# Garmin > Tanda Marathon Prediction > Home Assistant
Simplify your running metrics, track your performance, automate all the things. The only running metrics you need to estimate marathon race time is Avg Pace and Avg Miles/wk over the trailing 56days.  This script will fetch running data from your garminconnect account, apply the [tanda algorithm](https://rua.ua.es/dspace/bitstream/10045/18930/1/jhse_Vol_VI_N_III_511-520.pdf), push a sensor update to Home Assistant, then Home Assistant will automatically run the script after every activity, use our new sensor values as a display on our dashboards or as part of automtaions and notifications.

![image](https://github.com/seanap/HA-Garmin-Tanda/assets/17012946/4aa165a7-5559-44b2-abf2-3da5d4d0cf7e)

## PC Setup

### Script setup

* Save the `garmin_connect_data.py` script. In my example the script is saved at `C:\scripts\garmin_connect_data.py`  
* Edit the script with Notepad++, provide your garmin username and password as well as your Home Assistant IP address and a Long-lived Access Token:  
  * Profile Pic > Security > Long-lived access token > Create New > Copy/paste into garmin_connect_data.py  
* Install python if not already installed  
* Install pip if not already installed  
* Install required python module  
  * `pip install garminconnect`  

### Install Home Assistant PC Helper App
* Install [HASS.agent](https://github.com/LAB02-Research/HASS.Agent)
* Configure a new custom command:  
![image](https://github.com/seanap/HA-Garmin-Tanda/assets/17012946/248881e5-be1a-4e64-a154-6d7d201518ad)

## Home Assistant Setup

The goal is to bring the avg GAP pace, avg mi/wk, and estimated marathon time over to Home Assistant as sensor entities.  This allows us to set up custom notifications, chart performance over time, and any fun automation you can imagine. We will set up a template sensor that grabs the `last_activities` attribute of the Last Activities sensor in the Garmin Connect integration and outputs the date and time of the last activity logged in Garmin.  This new sensor is now used in an automation that is triggered when the last_activities changes state, this in turn will call the `garmin_connect_data.py` script, updating the pace/distance/est automatically whenever a new activity is posted.

### Set up Template Sensor

* Enable the Last Activities entity in the Garmin Connect integration
* Make note of the sensor name and make sure to update the value_template if needed.

```yaml
sensor:
  - platform: template
    sensors:
      garmin_last_activity_time:
        unique_id: "garmin_last_activity_time"
        friendly_name: "Garmin Last Activity Time"
        value_template: >
          {% set activities = state_attr('sensor.last_activities', 'last_Activities') %}
          {% if activities and activities | length > 0 %}
            {% set first_activity = activities[0] %}
            {{ first_activity.startTimeLocal }}
          {% else %}
            None
          {% endif %}
```

### Set up Automation

Review the sensor and button `entity_id`

```jinja
alias: Run Garmin Tanda Script on New Garmin Activity
description: >-
  Press the button to update Garmin Tanda python script when a new garmin
  activity is logged
trigger:
  - platform: state
    entity_id:
      - sensor.garmin_last_activity_time
condition: []
action:
  - service: button.press
    metadata: {}
    data: {}
    target:
      entity_id: button.update_garmin_tanda_python_script
mode: single
```

## Special Thanks
* ChatGPT 4o
* Josh Sambrook
* Giovanni Tanda
