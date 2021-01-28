![](https://brands.home-assistant.io/_/vivint/logo.png)
# Vivint for Home Assistant
Home Assistant integration for a Vivint home security system.

# Installation
There are two main ways to install this custom component within your Home Assistant instance:

1. Using HACS (see https://hacs.xyz/ for installation instructions if you do not already have it installed):
    1. From within Home Assistant, click on the link to **HACS**
    2. Click on **Integrations**
    3. Click on the vertical ellipsis in the top right and select **Custom repositories**
    4. Enter the URL for this repository in the section that says *Add custom repository URL* and select **Integration** in the *Category* dropdown list
    5. Click the **ADD** button
    6. Close the *Custom repositories* window
    7. You should now be able to see the *Vivint* card on the HACS Integrations page. Click on **INSTALL** and proceed with the installation instructions.
    8. Restart your Home Assistant instance and then proceed to the *Configuration* section below.

2. Manual Installation:
    1. Download or clone this repository
    2. Copy the contents of the folder **custom_components/vivint** into the same file structure on your Home Assistant instance
        - An easy way to do this is using the [Samba add-on](https://www.home-assistant.io/getting-started/configuration/#editing-configuration-via-sambawindows-networking), but feel free to do so however you want
    3. Restart your Home Assistant instance and then proceed to the *Configuration* section below.

While the manual installation above seems like less steps, it's important to note that you will not be able to see updates to this custom component unless you are subscribed to the watch list. You will then have to repeat each step in the process. By using HACS, you'll be able to see that an update is available and easily update the custom component.

# Configuration

There is a config flow for this Vivint integration. After installing the custom component:
1. Go to **Configuration**->**Integrations**
2. Click **+ ADD INTEGRATION** to setup a new integration
3. Search for **Vivint** and click on it
4. You will be guided through the rest of the setup process via the config flow

# Options

After this integration is set up, you can configure a couple of options relating to the camera streams:
* **HD Stream** - indicates whether to stream the camera in high definition or not, defaults to `True`
* **RTSP Stream** -  which RTSP stream source to use, defaults to `Direct`. Can be one of:
  * *Direct* - falls back to the internal RTSP stream if direct access is unavailable
  * *Internal* - use this if, for some reason, you have a camera that doesn't seem to stream despite the Vivint API indicating direct access is available for it
  * *External* - use this option if your Vivint system and Home Assistant installation are on separate networks without access to each other

---

## TODO
* Add support for multi-level switches and thermostats**
* Add support for 2FA**

** These can't be done until the underlying library has been updated

---

## Support Me
I'm not employed by Vivint, and provide this custom component purely for your own enjoyment and home automation needs. 

If you don't already own a Vivint system, please consider using [my referal code (kaf164)](https://www.vivint.com/get?refCode=kaf164&exid=165211vivint.com/get?refCode=kaf164&exid=165211) to get $50 off your bill (as well as a tip to me in appreciation)!

If you already own a Vivint system and still want to donate, consider buying me a coffee ☕ (or beer 🍺) instead by using the link below:

<a href="https://www.buymeacoffee.com/natekspencer" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-blue.png" alt="Buy Me A Coffee" height="41" width="174"></a>
