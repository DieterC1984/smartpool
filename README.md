# smartpool

Smartpool integration for EPS Nexus system



smartpool is a custom component for Home Assistant that allows you to monitor your pool based onthe NEXUS system of EPS (Europe Pool Supplies), including water temperature, outside temperature, pH level, Rx level, deck status, pump status and light status. The devices and API's are made and maintained by EPS. This custom HA integration is totally independent and I have no connection with EPS.

This integration makes use of username and password that is also used to track the same information on the web application. This integration makes it possible to read the devices values into Home Assistant and convert into multiple sensors.
Switches and lights cannot be controlled as this integration is using the webportal without API access.





#### **Installation**

Requirements:



Username and password used on https://owner.smartpoolcontrol.eu/login/?next=/


Steps:



1\. Ensure you have HACS installed in your Home Assistant setup.

2\. Go to the HACS store and search for smartpool

3\. Click on the smartpool integration and select "Install".

#### configuration.yaml changes
4\. Add following lines to configuration.yaml

- sensor:
  - platform: smartpool

&#x20;   username: !secret smartpool\_user

&#x20;   password: !secret smartpool\_pass


#### secrets.yaml creation

5\. Create secrets.yaml into the same folder as your configuration.yaml if not already existing, and add your personal username and password to it.

smartpool\_user: "YOUR\_USERNAME"

smartpool\_pass: "YOUR\_PASSWORD"


