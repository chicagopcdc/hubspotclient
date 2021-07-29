# hubspotclient

## Set up env
- `python -m venv env`
- `source env/bin/activate`
- `poetry install`


## Usage
Poetry dependency import (pyproject.toml)
`hubspotclient = {git = "https://github.com/chicagopcdc/hubspotclient.git", branch = "pcdc_dev"}`

You need to import the client
`from hubspotclient.client.hubspot.client import HubspotClient`

You need to instantiate the class
`hubspot = HubspotClient(hubspot_auth_token="HUBSPOT_TOKEN")`
The OAUTH implementation is on the way, but not supported yet.

Call the API with the main class functions:
`hubspot.get_commitees_info(committee="INSTRuCT")`
