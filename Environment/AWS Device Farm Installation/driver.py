import drivercontext
from cloudshell.api.cloudshell_api import CloudShellAPISession, InputNameValue
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

class DeployFromImage(ResourceDriverInterface):
    def cleanup(self):
        pass

    def __init__(self):
        pass

    def initialize(self, context):
        pass

    def install_device_farm_app(self, context, Name=None):
        """
        Installs app
        :type context: drivercontext.ResourceCommandContext
        """
        session = CloudShellAPISession(host=context.connectivity.server_address, token_id=context.connectivity.admin_auth_token, domain=context.reservation.domain)

        cp_resource = context.resource.attributes["AWS EC2"]
        deploy_inputs = [InputNameValue(attributeName.lower().replace(' ', '_'), attributeValue)
                         for attributeName, attributeValue
                         in context.resource.attributes.items()
                         if attributeName != "AWS EC2"]

        # with open(r'c:\temp\install_device_farm_app.log', 'a') as f:
        #     f.write('context:' + str(context) + '\n')
        #     f.write('name:' + str(context.resource.name) + '\n')
        #     f.write('aws ec2:' + str(context.resource.attributes["AWS EC2"]) + '\n')
        #     f.write('attributes:' + str(context.resource.attributes) + '\n')
        #     f.write('model:' + str(context.resource.model) + '\n')

        #session.WriteMessageToReservationOutput(context.reservation.reservation_id, str(context))
        # return 'success'
        result = session.ExecuteCommand(context.reservation.reservation_id, cp_resource, "Resource", "upload_app", deploy_inputs)
        return result.Output