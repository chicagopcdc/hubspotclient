import pytest

def pytest_addoption(parser):
  parser.addoption("--hubspot-api-key", action="store", default=None, help="Hubspot api key")
  parser.addoption("--consortium-code", action="store", default="FAKE", help="Consortium Code")
  parser.addoption("--contact-email", action="store", default="dvenckus@uchicago.edu", help="Contact Email")
  parser.addoption("--contact-id", action="store", default="52551", help="Contact ID")

