import os
import json
import pytest
from requests_toolbelt.adapters.appengine import monkeypatch
from hubspotclient.client.hubspot.client import HubspotClient


@pytest.fixture()
def apikey(pytestconfig):
  return pytestconfig.getoption("hubspot_api_key")

@pytest.fixture()
def consortium_code(pytestconfig):
  return pytestconfig.getoption("consortium_code")

@pytest.fixture()
def contact_email(pytestconfig):
  return pytestconfig.getoption("contact_email")

@pytest.fixture()
def contact_id(pytestconfig):
  return pytestconfig.getoption("contact_id")


# ------------- TESTS ----------------

def test_get_contacts_by_committee(apikey, consortium_code, monkeypatch):
  monkeypatch.setenv('HUBSPOT_DEBUG', '1')
  assert apikey, "Missing Hubspot API key"
  assert consortium_code, "Missing consortium code"

  hubspot = HubspotClient(apikey)
  response = hubspot.get_contacts_by_committee(f"{consortium_code} Executive Committee Member")

  assert int(response['total']) == 2, "Hubspot failed to return expected data"


def test_get_contact_by_email(apikey, contact_email, contact_id, monkeypatch):
  monkeypatch.setenv('HUBSPOT_DEBUG', '1')
  assert apikey, "Missing Hubspot API key"
  assert contact_email, "Missing contact email"

  hubspot = HubspotClient(apikey)
  response = hubspot.get_contact_by_email(contact_email)

  assert (int(response['total']) == 1 and response['results'][0]['id'] == contact_id), "Hubspot failed to return expected data"


def test_update_contact(apikey, contact_id, monkeypatch):
  monkeypatch.setenv('HUBSPOT_DEBUG', '1')
  assert apikey, "Missing Hubspot API key"
  assert contact_id, "Missing contact id"

  hubspot = HubspotClient(apikey)
  response = hubspot.update_contact(contact_id, json.dumps({"firstname": "Fred"}))

  assert (int(response['total']) == 1 and response['results'][0]['id'] == contact_id), "Hubspot failed to return expected data"