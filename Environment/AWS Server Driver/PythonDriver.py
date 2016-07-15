import re
import tempfile

import json
import zipfile

import io
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.cp.vcenter.common.utilites.command_result import set_command_result
from cloudshell.cp.vcenter.models.DeployResultModel import DeployResult
import boto3
import drivercontext
from time import sleep
import requests
import os
import inspect

# noinspection PyMethodMayBeStatic
class AWSPythonConnectedDriver(ResourceDriverInterface):
    def cleanup(self):
        pass

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self._endpoint = ''
        self._session_arn = ''
        self._app_arn = ''
        self._project_arn = ''

    def initialize(self, context):
        pass

    def remote_refresh_ip(self, context, cancellation_context, ports):
        """
        :type context drivercontext.ResourceRemoteCommandContext
        """
        # df = self._connect_amazon(context)
        # instance = self._get_instance(context, self._get_connected_instance_id(context), ec2)
        # if instance is not None:
        #     address = instance.public_ip_address
        #     api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        #     api.UpdateResourceAddress(context.remote_endpoints[0].fullname.split('/')[0],address)
        #
        #     return address
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        # api.UpdateResourceAddress(context.remote_endpoints[0].fullname.split('/')[0],address)

        ep1 = self._endpoint[0:400]
        ep2 = self._endpoint[400:]

        api.SetAttributeValue(context.remote_endpoints[0].fullname.split('/')[0], 'AWSRemoteDeviceEndpoint', ep1)
        api.SetAttributeValue(context.remote_endpoints[0].fullname.split('/')[0], 'AWSRemoteDeviceEndpoint2', ep2)
        api.SetAttributeValue(context.remote_endpoints[0].fullname.split('/')[0], 'AWSDeviceFarmSessionARN', self._session_arn)

        return 'noaddr'

    def PowerOff(self, context, ports):
        """
        :param context:
        :param ports:
        :return:

        :type context drivercontext.ResourceRemoteCommandContext
        """
        # df = self._connect_amazon(context)
        # instance = self._get_instance(context, self._get_connected_instance_id(context), ec2)
        # if instance is not None:
        #     stop_response = instance.stop()
        #     instance.wait_until_stopped()
        #
        #     if stop_response["ResponseMetadata"]["HTTPStatusCode"] >= 200 and stop_response["ResponseMetadata"][
        #         "HTTPStatusCode"] < 300:
        #         api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        #         api.SetResourceLiveStatus(context.remote_endpoints[0].fullname.split('/')[0], 'Offline', 'Resource is powered off')
        #         return "success"
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        api.SetResourceLiveStatus(context.remote_endpoints[0].fullname.split('/')[0], 'Offline', 'Resource is powered off')
        return "success"

    # the name is by the Qualisystems conventions
    def PowerOn(self, context, ports):
        """
        :param context:
        :param ports:
        :return:

        :type context drivercontext.ResourceRemoteCommandContext
        """
        # df = self._connect_amazon(context)
        # instance = self._get_instance(context, self._get_connected_instance_id(context), ec2)
        # if instance is not None:
        #     start_response = instance.start()
        #     instance.wait_until_running()
        #
        #     if 200 <= start_response["ResponseMetadata"]["HTTPStatusCode"] < 300:
        #         api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        #         api.SetResourceLiveStatus(context.remote_endpoints[0].fullname.split('/')[0], 'Online', 'Resource is powered on')
        #         return "success"
        #     return "fail"
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        api.SetResourceLiveStatus(context.remote_endpoints[0].fullname.split('/')[0], 'Online', 'Resource is powered on')
        return "success"

    # the name is by the Qualisystems conventions
    def PowerCycle(self, context, ports, delay):
        self.PowerOff(context,ports)
        sleep(int(delay))
        self.PowerOn(context, ports)

    def _get_instance(self, context, instance_id, ec2_service):
        for instance in ec2_service.instances.all():
            if instance.id == instance_id:
                return instance

        return None

    def _connect_amazon(self, context):
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)

        access_key = context.resource.attributes["Access Key"]
        secret_access_key = api.DecryptPassword(context.resource.attributes["Secret Access Key"]).Value

        os.environ['AWS_DATA_PATH'] = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

        session = boto3.Session(aws_access_key_id=access_key,
                                aws_secret_access_key=secret_access_key,
                                region_name=context.resource.address)

        df = session.client('devicefarm')
        return df

    def deploy_from_device_farm(self, context, device_model, inbound_ports, instance_type, outbound_ports, app_name):
        # api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)

        # self._endpoint = 'fake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpoint'
        # self._session_arn = 'fake_session_arn'
        # self._app_arn = 'fake_app_arn'
        df_session = self._connect_amazon(context)

        device_arn = ''
        for d in df_session.list_devices()['devices']:
            s = d['name'] + ' - ' + d['platform'] + ' ' + d['os']
            s = s.replace('&amp;', '&')
            s = s.replace('&quot;', '"')
            device_model = device_model.replace('&amp;', '&')
            device_model = device_model.replace('&quot;', '"')
            s = s.replace('&', '')
            s = s.replace('"', '')
            device_model = device_model.replace('&', '')
            device_model = device_model.replace('"', '')
            if s == device_model:
                device_arn = d['arn']
                break

        if not device_arn:
            raise Exception('Device not found matching model selection <' + device_model + '>')

        self._project_arn = df_session.list_projects()['projects'][0]['arn']

        o = df_session.create_remote_access_session(
            deviceArn=device_arn,
            projectArn=self._project_arn,
            configuration={
                'billingMethod': 'METERED'
            },
            name=app_name.replace(' ', '_')
        )

        self._session_arn = o['remoteAccessSession']['arn']

        status = ''
        for _ in range(0, 30):
            o = df_session.get_remote_access_session(arn=self._session_arn)
            status = o['remoteAccessSession']['status']
            if status == 'RUNNING':
                self._endpoint = o['remoteAccessSession']['endpoint']
                break
            sleep(10)

        if status != 'RUNNING':
            raise Exception('Remote device session did not start within 5 minutes')

        result = DeployResult(app_name, 'no-uuid', context.resource.fullname, "", 60, True, True, True, True, False)
        rv = set_command_result(result, False)
        # # with open(r'c:\temp\a.txt', 'a') as f:
        # #     f.write(rv + '\n\n')
        #
        # # if apk_filename:
        # #     self.upload_app(context, None, apk_filename)
        return rv

    def get_inventory(self, context):
        return "Not Implemented"

    def create_ami(self, context, ports, snapshot_name, snapshot_description):
        return "Not Implemented"

    def ApplyConnectivityChanges(self, context, request):
        return "Not Implemented"

    def disconnect_all(self, context, ports):
        return "Not Implemented"

    def revert_to_snapshot(self, context, ports, snapshot_name):
        return "Not Implemented"

    def disconnect(self, context, ports, network_name):
        return "Not Implemented"

    def destroy_device(self, context, ports):
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        destroy_result = self.destroy_vm_only(context, ports)
        if destroy_result == "success":
            api.DeleteResource(context.remote_endpoints[0].fullname)
            return "Deleted instance {0} Successfully".format(context.remote_endpoints[0].fullname)
        else:
            return "Failed to delete instance"

    def upload_app(self, context, ports, apk_url, apk_asset_updates):
        r = requests.get(apk_url)
        # apkbuf = io.BytesIO(r.content)
        # z = zipfile.ZipFile(apkbuf, mode="a", compression=zipfile.ZIP_DEFLATED)
        # if apk_asset_updates:
        #     for fn, text in json.loads(apk_asset_updates).items():
        #         z.writestr(fn, text)
        # z.close()
        # apkbuf.seek(0)
        f = tempfile.NamedTemporaryFile(suffix='.apk', delete=False)

        # with open(r'c:\temp\patched2.apk', 'wb') as f:
        f.write(r.content)
        r.close()
        f.close()
        # f.write(apkbuf.read())
        # apkbuf.seek(0)

        # with open(f.name, 'rb') as g:
        #     apkdata = bytearray(g.read())


        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)

        res = api.GetReservationDetails(context.reservation.reservation_id).ReservationDescription

        z = zipfile.ZipFile(f.name, mode="a", compression=zipfile.ZIP_DEFLATED)

        if apk_asset_updates:
            for fn, text in json.loads(apk_asset_updates).items():
                while True:
                    m = re.search(r'([^{]*)\{([^}]*)\}(.*)', text)
                    if not m:
                        break
                    expr = m.group(2)
                    objref, attrname = expr.split('.')
                    objref = objref.replace('(', '').replace(')', '')
                    if '=' in objref:
                        familymodelname, objid = objref.split('=')
                    else:
                        familymodelname = 'name'
                        objid = objref
                    ans = 'EXPR_FAILED(' + expr + ')'
                    for resource in res.Resources:
                        if (familymodelname.lower() == 'family' and resource.ResourceFamilyName == objid) or \
                                (familymodelname.lower() == 'model' and resource.ResourceModelName == objid) or \
                                (familymodelname.lower() == 'name' and resource.Name == objid):
                            if attrname.lower() == 'address':
                                ans = resource.FullAddress
                            else:
                                for attr in api.GetResourceDetails(resource.Name).ResourceAttributes:
                                    if attr.Name == attrname:
                                        ans = attr.Value
                            break
                    text = m.group(1) + ans + m.group(3)
                z.writestr(fn, text)
        z.close()

        os.system(r'C:\ProgramData\Oracle\Java\javapath\java.exe -jar ' +
                  os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) +
                  '\\sign.jar ' + f.name)

        with open(f.name.replace('.apk', '.s.apk'), 'rb') as g:
            signed_apk_data = bytearray(g.read())


        api.WriteMessageToReservationOutput(context.reservation.reservation_id, 'upload_app called')

        api.WriteMessageToReservationOutput(context.reservation.reservation_id, f.name)

        df_session = self._connect_amazon(context)

        # apk_fullpath = "C:\\Users\\ericr\\Downloads\\HelloWorld_v1.0_apkpure.com.apk"
        # apk_basename = 'hello2.apk'

        # for apk_fullpath, apk_basename, t in [
        #     (apk_filename, apk_filename.replace('\\', '/').split('/')[-1], 'ANDROID_APP'),
        #     (r'c:\apk_repo\a.zip', 'a.zip', 'EXTERNAL_DATA')]:
        # apk_fullpath = apk_url
        apk_basename = apk_url.replace('\\', '/').split('/')[-1]

        r = df_session.create_upload(contentType='application/octet-stream',
                                     name=apk_basename,
                                     projectArn=self._project_arn,
                                     type='ANDROID_APP')
        upload_url = r['upload']['url']
        self._app_arn = r['upload']['arn']

        # with open(apk_fullpath, 'rb') as f:
        #     d = f.read()
        r2 = requests.put(upload_url,
                          headers={'Content-Type': 'application/octet-stream'},
                          data=signed_apk_data)
        if r2.status_code >= 300:
            raise Exception('Error ' + str(r2.status_code) + ' in PUT to ' + upload_url)

        status = ''
        for _ in range(0, 30):
            r = df_session.get_upload(arn=self._app_arn)
            status = r['upload']['status']
            if status in ['SUCCEEDED', 'FAILED', 'ERROR']:
                break
            sleep(10)
        if status != 'SUCCEEDED':
            raise Exception('App upload failed or did not complete within 5 minutes. Status=' + status)

        df_session.install_to_remote_access_session(appArn=self._app_arn, remoteAccessSessionArn=self._session_arn)
        return "success"

    def destroy_vm_only(self, context, ports):
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)

        session_arn = api.GetAttributeValue(context.remote_endpoints[0].fullname.split('/')[0], "AWSDeviceFarmSessionARN").Value

        df_session = self._connect_amazon(context)
        df_session.stop_remote_access_session(
            arn=session_arn
        )

        status = ''
        for _ in range(0, 30):
            o = df_session.get_remote_access_session(arn=session_arn)
            status = o['remoteAccessSession']['status']
            if status == 'COMPLETED':
                break
            sleep(10)

        if status != 'COMPLETED':
            return "fail"
            # raise Exception('session did not end within 5 minutes')
        return "success"
