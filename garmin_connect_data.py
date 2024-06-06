import datetime
import json
import math
from garminconnect import Garmin, GarminConnectConnectionError, GarminConnectTooManyRequestsError, GarminConnectAuthenticationError
import requests

def main():
# User Input
    email = "un"
    password = "pw"
    home_assistant_url = "http://<ha-IP>:8123/api/states"
    home_assistant_token = "longrandomstringofcharacters"

# Begin script
    headers = {
        "Authorization": f"Bearer {home_assistant_token}",
        "content-type": "application/json"
    }

    try:
        client = Garmin(email, password)
        client.login()

        # Get activities for the last 56 days
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=56)
        activities = client.get_activities(start=0, limit=100)

        # Filter activities within the date range and only include running activities
        filtered_activities = []
        longest_run_duration = 0
        for activity in activities:
            try:
                activity_date = datetime.datetime.strptime(activity['startTimeLocal'], "%Y-%m-%d %H:%M:%S").date()
                if start_date <= activity_date <= end_date and activity['activityType']['typeKey'] == 'running':
                    filtered_activities.append(activity)
                    if activity['duration'] > longest_run_duration:
                        longest_run_duration = activity['duration']
            except ValueError:
                continue

        # Calculate total mileage and average GAP pace
        total_miles = sum(activity['distance'] for activity in filtered_activities) / 1609.34  # Convert meters to miles
        total_gap_speed = sum(activity.get('avgGradeAdjustedSpeed', 0) for activity in filtered_activities)  # Total GAP speed in meters per second
        if not filtered_activities or total_gap_speed == 0:
            raise ValueError("No valid GAP speed data found")

        average_gap_speed = total_gap_speed / len(filtered_activities)  # Average GAP speed in meters per second

        # Convert average GAP speed (m/s) to pace (min/mile)
        average_gap_pace_minutes_per_mile = (1609.34 / average_gap_speed) / 60  # Convert speed to pace in minutes per mile
        average_gap_pace_seconds_per_mile = round(average_gap_pace_minutes_per_mile * 60, 1)

        # Average miles per week
        average_miles_per_week = round(total_miles / 8, 2)

        # Format the average GAP pace
        def format_pace(seconds_per_mile):
            minutes = int(seconds_per_mile // 60)
            seconds = int(seconds_per_mile % 60)
            return f"{minutes}:{seconds:02d}"

        formatted_average_gap_pace = format_pace(average_gap_pace_seconds_per_mile)

        # Tanda race predictor constants
        C1 = 17.1
        C2 = 140.0
        C3 = 0.0053
        C4 = 0.55

        # Convert average weekly mileage from miles to kilometers
        K_km_per_week = average_miles_per_week * 1.60934

        # Convert average GAP pace from seconds per mile to seconds per kilometer
        P_sec_per_km = average_gap_pace_seconds_per_mile / 1.60934

        # Tanda race predictor formula
        P_m_sec_per_km = C1 + C2 * math.exp(-C3 * K_km_per_week) + C4 * P_sec_per_km

        # Convert P_m (sec/km) to total marathon time in seconds
        T_marathon_sec = round(P_m_sec_per_km * 42.195, 1)

        # Convert total marathon time to hours, minutes, and seconds
        marathon_hours = int(T_marathon_sec // 3600)
        marathon_minutes = int((T_marathon_sec % 3600) // 60)
        marathon_seconds = int(T_marathon_sec % 60)
        formatted_marathon_time = f"{marathon_hours}:{marathon_minutes:02d}:{marathon_seconds:02d}"

        # Prepare data to send to Home Assistant
        data = {
            "average_miles_per_week": average_miles_per_week,
            "average_gap_pace": average_gap_pace_seconds_per_mile,
            "marathon_prediction": T_marathon_sec
        }

        # Send data to Home Assistant
        requests.post(f"{home_assistant_url}/sensor.average_miles_per_week", headers=headers, json={"state": average_miles_per_week, "attributes": {"unit_of_measurement": "miles"}})
        requests.post(f"{home_assistant_url}/sensor.average_gap_pace", headers=headers, json={"state": average_gap_pace_seconds_per_mile, "attributes": {"unit_of_measurement": "s/mile", "human_readable": formatted_average_gap_pace}})
        requests.post(f"{home_assistant_url}/sensor.marathon_prediction", headers=headers, json={"state": T_marathon_sec, "attributes": {"unit_of_measurement": "s", "human_readable": formatted_marathon_time}})

    except (GarminConnectConnectionError, GarminConnectTooManyRequestsError, GarminConnectAuthenticationError) as e:
        requests.post(f"{home_assistant_url}/sensor.garmin_connect_error", headers=headers, json={"state": str(e)})
    except ValueError as e:
        requests.post(f"{home_assistant_url}/sensor.garmin_connect_error", headers=headers, json={"state": str(e)})

if __name__ == "__main__":
    main()
