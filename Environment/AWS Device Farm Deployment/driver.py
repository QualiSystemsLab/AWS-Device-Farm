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

    def Deploy(self, context, Name=None):
        """
        Deploys app from image
        :type context: drivercontext.ResourceCommandContext
        """
        session = CloudShellAPISession(host=context.connectivity.server_address, token_id=context.connectivity.admin_auth_token, domain=context.reservation.domain)

        cp_resource = context.resource.attributes["AWS EC2"]
        deploy_inputs = [InputNameValue(attributeName.lower().replace(' ', '_'), attributeValue)
                         for attributeName, attributeValue
                         in context.resource.attributes.items()
                         if attributeName != "AWS EC2"]
        deploy_inputs.append(InputNameValue('app_name', Name))

        result = session.ExecuteCommand(context.reservation.reservation_id, cp_resource, "Resource", "deploy_from_device_farm", deploy_inputs)
        return result.Output

