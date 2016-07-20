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

# installation_result = api.InstallApp(reservationId=resid,
#                                      resourceName=service,
#                                      commandName='Install',
#                                      commandInputs=[],
#                                      printOutput=True)
cp_resource = [x['value']
               for x in resource['appData']['installationService']['attributes']
               if x['name'] == 'AWS EC2'][0]

deploy_inputs = [InputNameValue(x['name'].lower().replace(' ', '_'), x['value'])
                 for x in resource['appData']['installationService']['attributes']
                 if x['name'] != 'AWS EC2']


# with open(r'c:\temp\install_device_farm_app.log', 'a') as f:
#     f.write('context:' + str(context) + '\n')
#     f.write('name:' + str(context.resource.name) + '\n')
#     f.write('aws ec2:' + str(context.resource.attributes["AWS EC2"]) + '\n')
#     f.write('attributes:' + str(context.resource.attributes) + '\n')
#     f.write('model:' + str(context.resource.model) + '\n')

#session.WriteMessageToReservationOutput(context.reservation.reservation_id, str(context))
# return 'success'
result = api.ExecuteCommand(resid, cp_resource, "Resource", "upload_app", deploy_inputs)
