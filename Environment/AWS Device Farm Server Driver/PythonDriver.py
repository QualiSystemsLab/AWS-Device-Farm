import re
import tempfile

import json
import zipfile

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
        pass

    def initialize(self, context):
        pass

    def _set_endpoint_attributes(self, context):
        """
        :type context drivercontext.ResourceRemoteCommandContext
        """
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        # session_arn = json.loads(context.remote_endpoints[0].vmdata_json)['UID']
        # api.WriteMessageToReservationOutput(context.remote_reservation.reservation_id, 'vmdata_json = ' + context.remote_endpoints[0].vmdata_json)

        det = api.GetResourceDetails(context.remote_endpoints[0].fullname.split('/')[0])
        oldep1 = 'not_set'
        oldep2 = 'not_set'
        for attr in det.ResourceAttributes:
            if attr.Name == 'AWSRemoteDeviceEndpoint':
                oldep1 = attr.Value
            if attr.Name == 'AWSRemoteDeviceEndpoint2':
                oldep2 = attr.Value
        session_arn = det.VmDetails.UID

        df_session = self._connect_amazon(context)
        o = df_session.get_remote_access_session(arn=session_arn)
        status = o['remoteAccessSession']['status']
        if status != 'RUNNING':
            raise Exception('Cannot refresh endpoint when session is not RUNNING: ' + str(o))

        endpoint = o['remoteAccessSession']['endpoint']
        ep1 = endpoint[0:400]
        ep2 = endpoint[400:]

        api.SetAttributeValue(context.remote_endpoints[0].fullname.split('/')[0], 'AWSRemoteDeviceEndpoint', ep1)
        api.SetAttributeValue(context.remote_endpoints[0].fullname.split('/')[0], 'AWSRemoteDeviceEndpoint2', ep2)

        api.WriteMessageToReservationOutput(context.remote_reservation.reservation_id,
                                            'Set endpoint attributes:\nOld 1: %s\nOld 2: %s\nNew 1: %s\nNew 2: %s\n' % (oldep1, oldep2, ep1, ep2))


    def remote_refresh_ip(self, context, cancellation_context, ports):
        """
        :type context drivercontext.ResourceRemoteCommandContext
        """

        self._set_endpoint_attributes(context)

        return 'noaddr'

    def PowerOff(self, context, ports):
        """
        :param context:
        :param ports:
        :return:

        :type context drivercontext.ResourceRemoteCommandContext
        """
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

    def show_status(self, context, ports):
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        df_session = self._connect_amazon(context)
        session_arn = api.GetResourceDetails(context.remote_endpoints[0].fullname.split('/')[0]).VmDetails.UID
        o = df_session.get_remote_access_session(arn=session_arn)
        return 'Remote access session status: ' + str(o)

    def refresh_gui_link(self, context, ports):
        self._set_endpoint_attributes(context)

        # api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        # api.WriteMessageToReservationOutput(context.remote_reservation.reservation_id, 'ports:' + str(ports))
        # api.WriteMessageToReservationOutput(context.remote_reservation.reservation_id, 'resource:' + context.resource.fullname)
        # api.WriteMessageToReservationOutput(context.remote_reservation.reservation_id, 'remote resource:' + context.remote_endpoints[0].fullname)
        #
        # df_session = self._connect_amazon(context)
        # o = df_session.get_remote_access_session(arn=self._session_arn)
        # status = o['remoteAccessSession']['status']
        # if status == 'RUNNING':
        #     self._endpoint = o['remoteAccessSession']['endpoint']
        #     return str(ports)
        # else:
        #     raise Exception('Status is not RUNNING: ' + str(o))

    def deploy_from_device_farm(self, context, device_model, inbound_ports, instance_type, outbound_ports, app_name):
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)

        api.WriteMessageToReservationOutput(context.reservation.reservation_id, 'Deploying %s...' % device_model)
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

        project_arn = df_session.list_projects()['projects'][0]['arn']

        running = False
        retries = 0
        while not running:
            try:
                api.WriteMessageToReservationOutput(context.reservation.reservation_id, 'Creating remote access session...')

                o = df_session.create_remote_access_session(
                    deviceArn=device_arn,
                    projectArn=project_arn,
                    configuration={
                        'billingMethod': 'METERED'
                    },
                    name=app_name.replace(' ', '_')
                )

                session_arn = o['remoteAccessSession']['arn']

                status = ''
                for _ in range(0, 30):
                    o = df_session.get_remote_access_session(arn=session_arn)
                    status = o['remoteAccessSession']['status']
                    api.WriteMessageToReservationOutput(context.reservation.reservation_id, 'Status: %s' % status)
                    if status == 'RUNNING':
                        # endpoint = o['remoteAccessSession']['endpoint']
                        running = True
                        break
                    if 'ERROR' in status or 'FAIL' in status or 'COMPLETED' in status:
                        api.WriteMessageToReservationOutput(context.reservation.reservation_id, 'Remote device session ended with an error: %s' % str(o))
                        raise Exception('Remote device session ended with an error: ' + str(o))
                    sleep(10)

                if status != 'RUNNING':
                    raise Exception('Remote device session did not start within 5 minutes: ' + str(o))
                break
            except Exception as e:
                retries += 1
                if retries < 5:
                    api.WriteMessageToReservationOutput(context.reservation.reservation_id, 'Remote device failed, RETRYING...')
                else:
                    raise Exception('Could not start a remote session in 5 tries. Check the AWS Device Farm console or try another hardware selection')

        # self._endpoint = 'fake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpointfake_endpoint'
        # self._app_arn = 'fake_app_arn'
        # self._session_arn = 'fake_session_arn'

        result = DeployResult(app_name, session_arn, context.resource.fullname, "", 60, True, True, True, True, False)
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

    def destroy_vm(self, context, ports):
        # with open(r'c:\programdata\qualisystems\devicefarm.log', 'a') as f:
        #     f.write('destroy_vm called\n')
        return self.destroy_device(context, ports)

    def destroy_device(self, context, ports):
        # with open(r'c:\programdata\qualisystems\devicefarm.log', 'a') as f:
        #     f.write('destroy_device called\n')
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        destroy_result = self.destroy_vm_only(context, ports)
        if destroy_result == "success":
            api.DeleteResource(context.remote_endpoints[0].fullname)
            return "Deleted instance {0} Successfully".format(context.remote_endpoints[0].fullname)
        else:
            return "Failed to delete instance"

    def upload_app_connected(self, context, ports, apk_url, apk_asset_updates):
        # with open(r'c:\programdata\qualisystems\devicefarm.log', 'a') as f:
        #     f.write('upload_app_connected called\n')
        return self.upload_app(context, ports, apk_url, apk_asset_updates)

    def upload_app(self, context, ports, apk_url, apk_asset_updates):
        # with open(r'c:\programdata\qualisystems\devicefarm.log', 'a') as f:
        #     f.write('upload_app called\n')
        r = requests.get(apk_url)
        f = tempfile.NamedTemporaryFile(suffix='.apk', delete=False)

        f.write(r.content)
        r.close()
        f.close()

        try:
            resid = context.reservation.reservation_id
        except:
            resid = context.remote_reservation.reservation_id


        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        api.WriteMessageToReservationOutput(resid, 'upload_app called')
        api.WriteMessageToReservationOutput(resid, 'context=' + str(dir(context)))
        api.WriteMessageToReservationOutput(resid, 'remote_endpoints=' + ', '.join([x.fullname for x in context.remote_endpoints]))
        api.WriteMessageToReservationOutput(resid, 'resource=' + str(context.resource.fullname))


        res = api.GetReservationDetails(resid).ReservationDescription

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



        api.WriteMessageToReservationOutput(resid, f.name)

        df_session = self._connect_amazon(context)

        project_arn = df_session.list_projects()['projects'][0]['arn']

        apk_basename = apk_url.replace('\\', '/').split('/')[-1]

        r = df_session.create_upload(contentType='application/octet-stream',
                                     name=apk_basename,
                                     projectArn=project_arn,
                                     type='ANDROID_APP')
        upload_url = r['upload']['url']
        app_arn = r['upload']['arn']

        r2 = requests.put(upload_url,
                          headers={'Content-Type': 'application/octet-stream'},
                          data=signed_apk_data)
        if r2.status_code >= 300:
            raise Exception('Error ' + str(r2.status_code) + ' in PUT to ' + upload_url)

        status = ''
        for _ in range(0, 30):
            r = df_session.get_upload(arn=app_arn)
            status = r['upload']['status']
            if status in ['SUCCEEDED', 'FAILED', 'ERROR']:
                break
            sleep(10)
        if status != 'SUCCEEDED':
            raise Exception('App upload failed or did not complete within 5 minutes. Status=' + status)

        # with open(r'c:\temp\vmdet.txt', 'w') as f:
        #     f.write('context:' + str(context) + '\n')
        #     for name, o in inspect.getmembers(context):
        #         f.write('context member>' + name + '\n')
        #
        #     # vmdet = api.GetResourceDetails(context.connectivity.resource.fullname).VmDetails
        #     f.write('endpoint: ' + context.remote_endpoints[0].fullname.split('/')[0])
        #
        #     vmdet = api.GetResourceDetails(context.remote_endpoints[0].fullname.split('/')[0]).VmDetails
        #     f.write(str(vmdet) + '\n\n')
        #     for name, o in inspect.getmembers(vmdet):
        #         f.write('>' + name + '\n')
        #     uid = vmdet.UID
        #     f.write(str(uid) + '\n\n')

        # session_arn = json.loads(context.remote_endpoints[0].vmdata_json)['UID']

        session_arn = api.GetResourceDetails(context.remote_endpoints[0].fullname.split('/')[0]).VmDetails.UID
        df_session.install_to_remote_access_session(appArn=app_arn, remoteAccessSessionArn=session_arn)
        return "success"

    def destroy_vm_only(self, context, ports):
        # with open(r'c:\programdata\qualisystems\devicefarm.log', 'a') as f:
        #     f.write('destroy_vm_only called\n')
        api = CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)
        try:
            resid = context.remote_reservation.reservation_id
        except:
            resid = context.reservation.reservation_id
        api.WriteMessageToReservationOutput(resid, 'Stopping remote device session...')

        session_arn = api.GetResourceDetails(context.remote_endpoints[0].fullname.split('/')[0]).VmDetails.UID

        df_session = self._connect_amazon(context)
        try:
            df_session.stop_remote_access_session(
                arn=session_arn
            )

            status = 'none'
            o = 'no data'
            for _ in range(0, 30):
                o = df_session.get_remote_access_session(arn=session_arn)
                status = o['remoteAccessSession']['status']
                api.WriteMessageToReservationOutput(resid, 'Status: %s' % status)
                if status == 'COMPLETED':
                    break
                sleep(10)

            if status != 'COMPLETED':
                api.WriteMessageToReservationOutput(resid, 'Remote device session ended with an error: %s' % str(o))
                return "fail"
                # # raise Exception('session did not end within 5 minutes')
        except Exception as e:
            # api.WriteMessageToReservationOutput(context.remote_reservation.reservation_id, 'Failed to stop remote session: %s' % str(e))
            return "fail"
        return "success"
