# AWS-Device-Farm

Note: Every CloudShell server needs the following changes:

1.	Insert a line in ServerUniversalSettings.xml: key name="AWS Remote Phone" pattern="http://{QsPortalAddress}/Content/devicefarm/aws2.html?address={Address}&amp;endpoint={AWSRemoteDeviceEndpoint}{AWSRemoteDeviceEndpoint2}" icon-key="RDP" />

2.	Put aws2.html under C:\Program Files (x86)\QualiSystems\CloudShell\Portal\Content\devicefarm


## QualiDemo1
Basic Android app that displays a webpage from a URL passed in as a text file asset bundled in the APK. 

Generate APK in Android Studio.

Not complete until the APK has been extracted, assets/backend_url.txt has been added, and the APK has been rezipped. This is done programmatically by the Device Farm app driver.

## Environment

### AWS Server Driver

Connected command driver implementing Device Farm session start, session end, and APK customization+upload.


### AWS EC2 Instance

Deployment service driver for AWS Device Farm phone session

Not renamed yet in case something depends on it.

Just a wrapper that calls the connected command on the AWS Server Driver.


### AWS Device Farm Installation

Installation service driver

Just a wrapper that calls the connected command on the AWS Server Driver.

There also has to be a Python script (as opposed to driver) attached to the installation service with the same name as the main function of the driver.


### AWS Shell

Top-level environment. The latest versions of the three drivers (AWS Server Driver, AWS EC2 Instance, AWS Device Farm Installation) must be zipped and placed in Resource Drivers - Python. There is also a file Deployment Orchestrator.zip that must remain identical to the one on CloudShell Live. After updating the zips, zip this whole directory and drag into the portal.

