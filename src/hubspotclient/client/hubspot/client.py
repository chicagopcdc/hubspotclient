"""
Define the HubspotClient class for interfacing with the Hubspot service for
hubspot.
"""

import httpx
from os import environ
import json

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from .base import BaseHubspotClient


class SyncClient(httpx.Client):
    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)

    async def request(self, *args, **kwargs):
        return super().request(*args, **kwargs)


class HubspotClient(BaseHubspotClient):
    """
    A singleton class for interfacing with the hubspot engine, "Hubspot".
    """

    client_cls = SyncClient


    def get_contacts_by_committee(self, committee, **kwargs):
        """
        if DEBUG, return test data, otherwise, call the base method
        """
        if bool(environ.get('HUBSPOT_DEBUG')):
            data = {
                "total": "2",
                "results": [
                    {
                        "id": "9601",
                        "properties": {
                            "firstname": "Luca",
                            "lastname": "Graglia",
                            "email": "graglia01@gmail.com",
                            "disease_group_executive_committee": "FAKE Executive Committee Member"
                        },
                        "createdAt": "2019-12-18T03:30:17.883Z",
                        "updatedAt": "2021-07-08T16:50:06.678Z"
                    },
                    {
                        "id": "52551",
                        "properties": {
                            "firstname": "Debra",
                            "lastname": "Venckus",
                            "email": "dvenckus@uchicago.edu",
                            "disease_group_executive_committee": "FAKE Executive Committee Member"
                        },
                        "createdAt": "2021-04-09T03:30:17.883Z",
                        "updatedAt": "2021-07-07T16:50:06.678Z"
                    }
                ]
            }
            return data
        
        ### NORMAL HANDLING
        
        return super(HubspotClient, self).get_contacts_by_committee(committee, kwargs).json


    def get_contact_by_email(self, email, hubspot_id=None, **kwargs):
        """
        if DEBUG, return test data, otherwise, call the base method
        """
        if bool(environ.get('HUBSPOT_DEBUG')):
            data = {}

            if email == "graglia01@gmail.com":
                data = {
                    "total": "1",
                    "results": [{
                        "id": "9601",
                        "firstname": "Luca",
                        "lastname": "Graglia",
                        "institution": "University of Chicago"
                    }]
                }
            elif email == "dvenckus@uchicago.edu":
                data = {
                    "total": "1",
                    "results": [{
                        "id": "52551",
                        "firstname": "Debra",
                        "lastname": "Venckus",
                        "institution": "University of Chicago"
                    }]
                }
            else:
                data = {
                    "total": "0",
                    "results": []
                }
            
            return data

        ### Normal Handling

        return super(HubspotClient, self).get_contact_by_email(email, hubspot_id, kwargs)


    def update_contact(self, contact_id, property_json):
        """
        if DEBUG, return test data, otherwise, call the base method
        """
        if bool(environ.get('HUBSPOT_DEBUG')):
            data = {}

            if contact_id == "9601":
                data = {
                    "total": "1",
                    "results": [{
                        "id": "9601",
                        "firstname": "Luca",
                        "lastname": "Graglia",
                        "institution": "University of Chicago"
                    }]
                }

            elif contact_id == "52551":
                data = {
                    "total": "1",
                    "results": [{
                        "id": "52551",
                        "firstname": "Debra",
                        "lastname": "Venckus",
                        "institution": "University of Chicago"
                    }]
                }
            else:
                data = {
                    "total": "0",
                    "results": []
                }
        
            return data
        
        ### Normal Handling

        return super(HubspotClient, self).update_contact(contact_id, property_json)
        