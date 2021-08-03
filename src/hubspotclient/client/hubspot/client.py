"""
Define the HubspotClient class for interfacing with the Hubspot service for
hubspot.
"""

import httpx

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

