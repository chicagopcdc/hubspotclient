"""
Base classes for interfacing with the Hubspot service for hubspot. Please use
:class:`~.client.HubspotClient` in blocking context like Flask, or
:class:`~.async_client.HubspotClient` in asynchronous context like FastAPI.
"""

import inspect
import json
from json import dumps
from collections import deque
from urllib.parse import quote

import backoff
import contextvars
import httpx
from cdislogging import get_logger

from ..hubspot.errors import HubspotError, HubspotUnhealthyError
from ..base import CrmClient
from ... import string_types
from ...utils import maybe_sync


def _escape_newlines(text):
    return text.replace("\n", "\\n")


class HubspotResponse(object):
    """
    Args:
        response (requests.Response)
    """

    def __init__(self, response, expect_json=True):
        self._response = response
        print(response.status_code)
        print(response.json())
        self.code = response.status_code

        if not expect_json:
            return

        try:
            self.json = response.json()
        except ValueError as e:
            if self.code != 500:
                raise HubspotError(
                    "got a confusing response from Hubspot, couldn't parse JSON from"
                    " response but got code {} for this response: {}".format(
                        self.code, _escape_newlines(response.text)
                    ),
                    self.code,
                )
            self.json = {"error": {"message": str(e), "code": 500}}

    @property
    def successful(self):
        try:
            return "error" not in self.json
        except AttributeError:
            return self.code < 400

    @property
    def error_msg(self):
        if self.successful:
            return None
        try:
            return self.json["error"]["message"]
        except (KeyError, AttributeError):
            return self._response.text


    # {
    #     "status": "error",
    #     "message": "Invalid input JSON on line 13, column 17: Cannot deserialize instance of `java.util.LinkedHashMap` out of START_ARRAY token",
    #     "correlationId": "e752f250-59a1-466f-9d63-7a78ab3f942e"
    # }


class EnvContext(object):
    __slots__ = ("_stack", "_kwargs")

    def __init__(self, stack, kwargs):
        self._stack = stack
        self._kwargs = kwargs

    def __enter__(self):
        kwargs = {}
        if self._stack:
            kwargs.update(self._stack[-1])
        kwargs.update(self._kwargs)
        self._stack.append(kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stack.pop()


class _Env(object):
    __slots__ = ("_local",)

    def __init__(self):
        self._local = contextvars.ContextVar("stack")

    def _get_stack(self):
        stack = self._local.get(None)
        if stack is None:
            stack = deque()
            self._local.set(stack)
        return stack

    def get_current_with(self, kwargs):
        rv = {}
        stack = self._get_stack()
        if stack:
            rv.update(stack[-1])
        rv.update(kwargs)
        return rv

    def make_context(self, kwargs):
        return EnvContext(self._get_stack(), kwargs)


class BaseHubspotClient(CrmClient):
    """
    Abstract class to define behavior of an hubspot client implementation.
    """

    client_cls = NotImplemented

    def __init__(
        self,
        logger=None,
        hubspot_base_url="https://api.hubapi.com/crm/v3/objects/",
        hubspot_auth_token=None,
        timeout=10,
    ):
        self.logger = logger or get_logger("HubspotClient")
        self._auth_token = hubspot_auth_token
        self._base_url = hubspot_base_url.strip("/")
        self._companies_url = self._base_url + "/companies"
        self._associated_companies_url = self._base_url + "/associations/companies"
        self._contacts_url = self._base_url + "/contacts"
        self._timeout = timeout
        self._env = _Env()

    def context(self, **kwargs):
        return self._env.make_context(kwargs)


    async def request(self, method, url, **kwargs):
        """
        Wrapper method of ``requests.request`` adding retry, timeout and headers.

        If the actual request fails to connect or timed out, this client will retry the
        same request if ``retry`` is truthy after Hubspot becomes healthy.
        By default, it will retry health check up to 5 times, waiting for a maximum of
        10 seconds, before giving up and declaring Hubspot unavailable.

        Args:
            method:
            url:
            kwargs:
                expect_json:
                    True (default) if the response should be in JSON format
                retry:
                    True (default) if the request should be retried, or a dict as
                    keyword arguments for ``backoff.on_predicate``
                timeout:
                    overwrite timeout parameter for ``requests``
        """
        expect_json = kwargs.pop("expect_json", True)
        kwargs = self._env.get_current_with(kwargs)
        retry = kwargs.pop("retry", True)
        kwargs.setdefault("timeout", self._timeout)

    
        #TODO replace with OAuth
        params_old = kwargs.pop("params", None)
        params_new = {'hapikey': self._auth_token}
        if params_old:
            params = params_old.copy()
            params.update(params_new)
        else:
            params = params_new
        kwargs.setdefault("params",params)


        async with self.client_cls() as client:
            try:
                rv = await client.request(method, url, **kwargs)
            except httpx.TimeoutException:
                if retry:
                    if isinstance(retry, bool):
                        retry = {}
                    # set some defaults for when to give up: after 5 failures, or 10
                    # seconds (these can be overridden by keyword arguments)
                    retry.setdefault("max_tries", 5)
                    retry.setdefault("max_time", 10)

                    def giveup():
                        raise HubspotUnhealthyError()

                    def wait_gen():
                        # shorten the wait times between retries a little to fit our
                        # scale a little better (aim to give up within 10 s)
                        for n in backoff.fibo():
                            yield n / 2.0

                    await backoff.on_predicate(wait_gen, on_giveup=giveup, **retry)(
                        self.healthy
                    )()
                    rv = await client.request(method, url, **kwargs)
                else:
                    raise
        return HubspotResponse(rv, expect_json=expect_json)

    def get(self, url, params=None, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("get", url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request("post", url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request("put", url, data=data, **kwargs)

    def patch(self, url, data=None, json=None, **kwargs):
        return self.request("patch", url, data=data, json=json, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("delete", url, **kwargs)

    

    # @maybe_sync
    # async def healthy(self, timeout=1):
    #     """
    #     Indicate whether the Hubspot service is available and functioning.

    #     Return:
    #         bool: whether Hubspot service is available
    #     """
    #     try:
    #         response = await self.get(
    #             self._health_url, retry=False, timeout=timeout, expect_json=False
    #         )
    #     except httpx.HTTPError as e:
    #         self.logger.error(
    #             "Hubspot unavailable; got requests exception: {}".format(str(e))
    #         )
    #         return False
    #     if response.code != 200:
    #         self.logger.error(
    #             "Hubspot not healthy; {} returned code {}".format(
    #                 self._health_url, response.code
    #             )
    #         )
    #     return response.code == 200


    @maybe_sync
    async def get_contact_by_email(self, email, hubspot_id=None, **kwargs):
        """
        Returned response example
        {'total': 1, 'results': [{'id': '9601', 'properties': {'createdate': '2019-12-18T19:49:03.109Z', 'firstname': 'Luca', 'hs_object_id': '9601', 'institution': 'The University of Chicago', 'lastmodifieddate': '2021-07-08T17:28:39.152Z', 'lastname': 'Graglia'}, 'createdAt': '2019-12-18T19:49:03.109Z', 'updatedAt': '2021-07-08T17:28:39.152Z', 'archived': False}]}
        """
        data = {
            "filterGroups": [{
                "filters": [{
                    "value": email,
                    "propertyName": "email",
                    "operator": "EQ"
                }]
            }],
            "properties": ["firstname", "lastname", "institution"]
        }
        return await self.post(url=self._contacts_url + "/search", json=data, **kwargs)
        
    @maybe_sync
    async def get_contacts_by_committee(self, committee, **kwargs):
        """
        Returned response example
        {'total': 1, 'results': [{'id': '9601', 'properties': {'createdate': '2019-12-18T19:49:03.109Z', 'firstname': 'Luca', 'hs_object_id': '9601', 'institution': 'The University of Chicago', 'lastmodifieddate': '2021-07-08T17:28:39.152Z', 'lastname': 'Graglia'}, 'createdAt': '2019-12-18T19:49:03.109Z', 'updatedAt': '2021-07-08T17:28:39.152Z', 'archived': False}]}
        """
        data = {
            "filterGroups": [{
                "filters": [{
                    "value": committee,
                    "propertyName": "disease_group_executive_committee",
                    "operator": "EQ"
                }]
            }],
            "properties": ["email", "disease_group_executive_committee"]
        }
        return await self.post(url=self._contacts_url + "/search", json=data, **kwargs)

    @maybe_sync
    async def create_contact(self, property_json):
        """
        Create a new contact in Hubspot (does not affect fence database or
        otherwise have any interaction with userdatamodel).

        Example schema for resource JSON:

            {
                "email": "string",          #required
                "firstname": "string"       #optional
                "lastname": "string",       #optional
                "institution": "string"     #optional
            }

        Args:
            property_json (dict):
                dictionary of resource information (see the example above)

        Return:
            dict: response JSON from hubspot
            201
            {'id': '60901', 'properties': {'createdate': '2021-07-28T20:52:30.963Z', 'hs_is_unworked': 'true', 'hs_object_id': '60901', 'lastmodifieddate': '2021-07-28T20:52:30.963Z'}, 'createdAt': '2021-07-28T20:52:30.963Z', 'updatedAt': '2021-07-28T20:52:30.963Z', 'archived': False}

        Raises:
            - HubspotError: if the operation failed (couldn't create contact)
        """
        path = self._contacts_url

        data = {}
        data["properties"] = property_json

        response = await self.post(url=path, json=data)
        if response.code == 409:
            # already exists; this is ok, but leave warning
            # hubspot response {'status': 'error', 'message': 'Contact already exists. Existing ID: 9601', 'correlationId': '1823bec6-d3ad-4a3d-bfb6-e2251a9a4b42', 'category': 'CONFLICT'}
            self.logger.warning(
                "Contact `{}` already exists in Hubspot".format(property_json["email"])
            )
            return None
        if not response.successful:
            msg = "could not create resource `{}` in Hubspot: {}".format(
                path, response.error_msg
            )
            self.logger.error(msg)
            raise HubspotError(msg, response.code)
        self.logger.info("created resource {}".format(property_json["email"]))
        return response.json


    @maybe_sync
    async def update_contact(self, contact_id, property_json):
        """
        Response example:
        {'id': '61051', 'properties': {'firstname': 'test', 'lastmodifieddate': '2021-07-28T21:34:44.133Z', 'lastname': 'Test'}, 'createdAt': '2021-07-28T21:31:48.144Z', 'updatedAt': '2021-07-28T21:34:44.133Z', 'archived': False}
        """
        url = self._contacts_url + "/" + str(contact_id)

        data = {}
        data["properties"] = property_json
       
        response = await self.patch(url=url, json=data)
        if not response.successful:
            msg = "could not update contact `{}` in Hubspot: {}".format(
                path, response.error_msg
            )
            self.logger.error(msg)
            raise HubspotError(msg, response.code)
        self.logger.info("updated contact {}".format(contact_id))
        return response.json

    @maybe_sync
    async def get_commitees_info(self, committee, **kwargs):
        """
        Returned response example
        {'total': 1, 'results': [{'id': '6618904721', 'properties': {'approval_committees': 'INSTRuCT Executive Committee Member', 'createdate': '2021-07-22T18:30:31.713Z', 'hs_lastmodifieddate': '2021-07-22T20:56:05.763Z', 'hs_object_id': '6618904721'}, 'createdAt': '2021-07-22T18:30:31.713Z', 'updatedAt': '2021-07-22T20:56:05.763Z', 'archived': False}]}
        """
        data = {
            "filterGroups": [{
                "filters": [{
                    "value": committee,
                    "propertyName": "name",
                    "operator": "EQ"
                }]
            }],
            "properties": ["approval_committees"]
        }
        return await self.post(url=self._companies_url + "/search", json=data, **kwargs)
        # if response.code == 404:
        #     return None
        # if not response.successful:
        #     self.logger.error(response.error_msg)
        #     raise HubspotError(response.error_msg, response.code)
        # return response.json

    # # @maybe_sync
    # # async def delete_resource(self, path):
    # #     url = self._resource_url + quote(path)
    # #     response = await self.delete(url)
    # #     if response.code not in [204, 404]:
    # #         msg = "could not delete resource `{}` in Hubspot: {}".format(
    # #             path, response.error_msg
    # #         )
    # #         raise HubspotError(msg, response.code)
    # #     return True

    

