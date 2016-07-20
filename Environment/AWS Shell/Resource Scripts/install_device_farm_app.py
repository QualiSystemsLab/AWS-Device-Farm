import json
import os

from cloudshell.api.cloudshell_api import CloudShellAPISession, InputNameValue

# print 'install_device_farm_app called: ' + str(os.environ)

resource = json.loads(os.environ['RESOURCECONTEXT'])
reservation = json.loads(os.environ['RESERVATIONCONTEXT'])
connectivity = json.loads(os.environ['QUALICONNECTIVITYCONTEXT'])

resid = reservation['id']


service = resource['appData']['name']


api = CloudShellAPISession(host=connectivity['serverAddress'],
                           token_id=connectivity['adminAuthToken'],
                           domain=reservation['domain'])

# Temporary implementation bypassing the installation service:
cp_resource = [x['value']
               for x in resource['appData']['installationService']['attributes']
               if x['name'] == 'AWS EC2'][0]

deploy_inputs = [InputNameValue(x['name'].lower().replace(' ', '_'), x['value'])
                 for x in resource['appData']['installationService']['attributes']
                 if x['name'] != 'AWS EC2']

result = api.ExecuteCommand(resid, cp_resource, "Resource", "upload_app", deploy_inputs)

# Version that calls the installation service from this script
# For this to work, update datamodel.xml on model "AWS Mobile Device Installation":
# Change to SupportsConcurrentCommands="true"

# installation_result = api.InstallApp(reservationId=resid,
#                                      resourceName=service,
#                                      commandName='Install',
#                                      commandInputs=[],
#                                      printOutput=True)
