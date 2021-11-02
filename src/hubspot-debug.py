# 
# hubspotclient handy test script
# for easy live testing with the hubspot cloud account
# by: dvenckus@uchicago.edu
#

from hubspotclient.client.hubspot.client import HubspotClient
from os import environ

#--------------------------------------
# hapikey = '<insert hubspot key>'
# email = '<insert email address>'
# user_firstname = '<insert test firstname>'
# user_lastname = '<insert test lastname>'
# consortium_code = '<insert consortium_code>'
#--------------------------------------

# ----- Populate these fields !!! -----
hapikey = ''
email = ''
consortium_code = ''
user_firstname = ''
user_lastname = ''
#--------------------------------------

environ['HUBSPOT_DEBUG'] = "TRUE"

committee = f"{consortium_code} Executive Committee Member"

hubspot = HubspotClient(hubspot_auth_token=hapikey)

# Retrive EC Members for a consortium
print(f"Connect to hubspot to retrieve EC Members for consortium, {committee}")

hubspot_response = hubspot.get_contacts_by_committee(committee=committee)
print(f"hubspot response: {hubspot_response}")
if hubspot_response and int(hubspot_response["total"]):
  print('get_contacts_by_committee: Success!')
else:
  print("Hubspot request get_contacts_by_committee FAILED")

# Retrieve single user by email address
print(f"Connect to hubspot to retrieve info for user, {email}")
hubspot_contact = hubspot.get_contact_by_email(email=email)
print(f"hubspot contact: {hubspot_contact}")
if hubspot_contact and int(hubspot_contact.get('total')):
  print('get_contact_by_email: Success!')
else:
  print("Hubspot request get_contact_by_email FAILED")

# Update properties for a single user by hubspot_id from previous request

if hubspot_contact and int(hubspot_contact.get('total')) == 1 and \
   (user_firstname or user_lastname):
  print(f"Connect to hubspot to update user, {email}")
  properties_json = {}
  contact = hubspot_contact.get('results')[0]
  hubspot_id = contact.get('id')
  properties_json['firstname'] = user_firstname
  properties_json['lastname'] = user_lastname
  hubspot_update = hubspot.update_contact(hubspot_id, properties_json)
