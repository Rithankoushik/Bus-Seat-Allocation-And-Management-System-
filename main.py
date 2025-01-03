import os
import json
import requests
import pandas as pd
import pyttsx3
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

# Load API key from environment variable
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Set the voice (optional)
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)  # Use second voice if available
else:
    engine.setProperty('voice', voices[0].id)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def load_bus_data(filepath):
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filepath)
    
    with open(full_path, 'r') as file:
        buses = json.load(file)
    return buses

def speak(text):
    """
    This function converts text to speech using pyttsx3.
    """
    engine.say(text)
    engine.runAndWait()

def notify_driver(driver, driver_phone, message):
    """
    This function sends a notification to the driver via phone call.
    """
    print(f"Initiating call to {driver}: {message}")
    call_driver(driver_phone, f"Notification for {driver}. {message}")

def request_admin_approval(current_bus, nearby_bus, action):
    if action == "reallocate":
        print(f"Requesting admin approval to reallocate students from Bus {current_bus['id']} to Bus {nearby_bus['id']}.")
    elif action == "combine":
        print(f"Requesting admin approval to combine Bus {current_bus['id']} with Bus {nearby_bus['id']}.")
    
    admin_approval = input(f"Does the admin approve the {action} action? (yes/no): ").lower()
    return admin_approval == "yes"

def find_nearby_bus(current_bus, buses, find_empty=True):
    if not GOOGLE_MAPS_API_KEY:
        print("Error: GOOGLE_MAPS_API_KEY not found in environment variables")
        return None, float('inf')

    try:
        origins = f"{current_bus['latitude']},{current_bus['longitude']}"
        destinations = "|".join([f"{bus['latitude']},{bus['longitude']}" for bus in buses if bus['id'] != current_bus['id']])
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origins}&destinations={destinations}&key={GOOGLE_MAPS_API_KEY}"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'rows' in data and data['rows']:
            elements = data['rows'][0]['elements']
            if len(elements) != len(buses) - 1:
                print("Error: Mismatch between number of buses in Excel and distance elements")
                return None, float('inf')

            distances = [element['distance']['value'] for element in elements]
            return process_excel_distances(current_bus, buses, distances, find_empty)
        else:
            print("Error: 'rows' not found in API response")
            return None, float('inf')
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None, float('inf')
    except ValueError as e:
        print(f"Error processing API response: {e}")
        return None, float('inf')

def process_excel_distances(current_bus, buses, distances, find_empty):
    min_distance = float('inf')
    selected_bus = None

    # Create a list of buses excluding the current bus
    other_buses = [bus for bus in buses if bus['id'] != current_bus['id']]

    for idx, bus in enumerate(other_buses):
        if idx >= len(distances):
            print("Warning: Distance data is missing for some buses in Excel.")
            continue

        if find_empty:
            available_seats = bus['seatingCapacity'] - bus['currentAttendance']
            if available_seats > 0 and distances[idx] < min_distance:
                min_distance = distances[idx]
                selected_bus = bus
        else:
            combined_attendance = current_bus['currentAttendance'] + bus['currentAttendance']
            if combined_attendance <= max(current_bus['seatingCapacity'], bus['seatingCapacity']) and distances[idx] < min_distance:
                min_distance = distances[idx]
                selected_bus = bus

    return selected_bus, min_distance

def check_attendance_and_notify(current_bus, buses):
    if current_bus['currentAttendance'] >= current_bus['seatingCapacity']:
        handle_full_bus(current_bus, buses)
    elif current_bus['currentAttendance'] < current_bus['seatingCapacity'] * 0.5:
        handle_low_attendance_bus(current_bus, buses)

def handle_full_bus(current_bus, buses):
    print(f"Bus {current_bus['id']} is full. Looking for nearby bus...")
    nearby_bus, distance = find_nearby_bus(current_bus, buses, find_empty=True)
    if nearby_bus:
        approved = request_admin_approval(current_bus, nearby_bus, "reallocate")
        if approved:
            print(f"Request approved. Notifying drivers {current_bus['driver']} and {nearby_bus['driver']}.")
            notify_driver(current_bus['driver'], current_bus['phone'], f"Your bus is full. Students will be allocated to Bus {nearby_bus['id']}.")
            notify_driver(nearby_bus['driver'], nearby_bus['phone'], f"Please pick up additional students from Bus {current_bus['id']}.")
        else:
            print("Request denied by admin.")
    else:
        print("No nearby bus with available seats found or unable to fetch nearby bus information.")

def handle_low_attendance_bus(current_bus, buses):
    print(f"Bus {current_bus['id']} has low attendance. Looking for nearby bus to combine...")
    nearby_bus, distance = find_nearby_bus(current_bus, buses, find_empty=False)
    if nearby_bus:
        approved = request_admin_approval(current_bus, nearby_bus, "combine")
        if approved:
            print(f"Request approved. Notifying drivers {current_bus['driver']} and {nearby_bus['driver']}.")
            notify_driver(current_bus['driver'], current_bus['phone'], f"Your bus will be combined with Bus {nearby_bus['id']}. Please proceed to the designated meeting point.")
            notify_driver(nearby_bus['driver'], nearby_bus['phone'], f"Your bus will be combined with Bus {current_bus['id']}. Please proceed to the designated meeting point.")
        else:
            print("Request denied by admin.")
    else:
        print("No suitable nearby bus found for combining or unable to fetch nearby bus information.")

def call_driver(driver_phone, message):
    """
    This function makes a phone call to the driver and plays the message.
    """
    try:
        call = twilio_client.calls.create(
            to=driver_phone,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f'<Response><Say>{message}</Say></Response>'
        )
        print(f"Call initiated to {driver_phone}. Call SID: {call.sid}")
    except Exception as e:
        print(f"Error making call to {driver_phone}: {e}")

def main():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'buses.xlsx')  # Excel file path

    # Load bus data from the spreadsheet
    try:
        buses_df = pd.read_excel(file_path)  # Read Excel file
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return

    if buses_df.empty:
        print(f"Error: No bus data loaded. Check the {file_path} file.")
        return

    # Convert DataFrame to a list of dictionaries for easier processing
    buses = buses_df.to_dict(orient='records')

    # Process all buses
    for bus in buses:
        # Call the function to check attendance and send notifications based on the bus data
        check_attendance_and_notify(bus, buses)

if __name__ == "__main__":
    main()
