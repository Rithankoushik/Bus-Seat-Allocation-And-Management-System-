from flask import Flask, jsonify, request, render_template, send_from_directory
import pandas as pd
import os
import requests
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Google Maps API key
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Center coordinates (e.g., college campus)
CENTER_COORDINATES = {'lat': 13.0382, 'lng': 80.0454}

# Global variable to store actions
pending_actions = []

def load_bus_data():
    
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'buses.xlsx')
    df = pd.read_excel(file_path)
    return df.to_dict(orient='records')

def call_driver(driver_phone, message):
    try:
        call = twilio_client.calls.create(
            to=driver_phone,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f'<Response><Say>{message}</Say></Response>'
        )
        print(f"Call initiated to {driver_phone}. Call SID: {call.sid}")
    except Exception as e:
        print(f"Error making call to {driver_phone}: {e}")

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
        pending_actions.append({
            'current_bus_id': current_bus['id'],
            'nearby_bus_id': nearby_bus['id'],
            'action': 'Reallocation',
            'message': f"Reallocate students from Bus {current_bus['id']} to Bus {nearby_bus['id']}.",
            'current_bus_details': current_bus,
            'nearby_bus_details': nearby_bus
        })
    else:
        print("No nearby bus with available seats found or unable to fetch nearby bus information.")

def handle_low_attendance_bus(current_bus, buses):
    print(f"Bus {current_bus['id']} has low attendance. Looking for nearby bus to combine...")
    nearby_bus, distance = find_nearby_bus(current_bus, buses, find_empty=False)
    if nearby_bus:
        pending_actions.append({
            'current_bus_id': current_bus['id'],
            'nearby_bus_id': nearby_bus['id'],
            'action': 'Combination',
            'message': f"Combine Bus {current_bus['id']} with Bus {nearby_bus['id']}.",
            'current_bus_details': current_bus,
            'nearby_bus_details': nearby_bus
        })
    else:
        print("No suitable nearby bus found for combining or unable to fetch nearby bus information.")

@app.route('/')
def serve_index():
    return send_from_directory('templates', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/bus-locations')
def bus_locations():
    bus_data = load_bus_data()
    locations = [{'id': bus['id'], 'latitude': bus['latitude'], 'longitude': bus['longitude']} for bus in bus_data]
    return jsonify(locations)

@app.route('/api/bus-details')
def bus_details():
    bus_data = load_bus_data()
    return jsonify(bus_data)

@app.route('/api/google-maps-key')
def google_maps_key():
    return jsonify({'apiKey': GOOGLE_MAPS_API_KEY})

@app.route('/api/pending-actions')
def get_pending_actions():
    return jsonify(pending_actions)

@app.route('/api/admin-action', methods=['POST'])
def admin_action():
    data = request.json
    current_bus_id = data.get('current_bus_id')
    nearby_bus_id = data.get('nearby_bus_id')
    action = data.get('action')
    approved = data.get('approved')

    buses = load_bus_data()
    print(f"Received admin action: current_bus_id={current_bus_id}, nearby_bus_id={nearby_bus_id}, action={action}, approved={approved}")
    print(f"Loaded bus IDs: {[bus['id'] for bus in buses]}")

    current_bus = next((bus for bus in buses if str(bus['id']) == str(current_bus_id)), None)
    nearby_bus = next((bus for bus in buses if str(bus['id']) == str(nearby_bus_id)), None)

    if current_bus is None:
        return jsonify({'success': False, 'message': f'Current bus with ID {current_bus_id} not found.'}), 404
    if nearby_bus is None:
        return jsonify({'success': False, 'message': f'Nearby bus with ID {nearby_bus_id} not found.'}), 404

    if approved:
        if action == "Reallocation":
            notify_driver(current_bus['driver'], current_bus['phone'], f"Your bus is full. Students will be allocated to Bus {nearby_bus['id']}.")
            notify_driver(nearby_bus['driver'], nearby_bus['phone'], f"Please pick up additional students from Bus {current_bus['id']}.")
        elif action == "Combination":
            notify_driver(current_bus['driver'], current_bus['phone'], f"Your bus will be combined with Bus {nearby_bus['id']}. Please proceed to the designated meeting point.")
            notify_driver(nearby_bus['driver'], nearby_bus['phone'], f"Your bus will be combined with Bus {current_bus['id']}. Please proceed to the designated meeting point.")
        return jsonify({'success': True, 'message': 'Action approved and notifications sent.'})
    else:
        return jsonify({'success': False, 'message': 'Action denied by admin.'})

def notify_driver(driver, driver_phone, message):
    """
    This function sends a notification to the driver via phone call.
    """
    print(f"Initiating call to {driver}: {message}")
    call_driver(driver_phone, f"Notification for {driver}. {message}")

def process_buses():
    buses = load_bus_data()
    for bus in buses:
        check_attendance_and_notify(bus, buses)

if __name__ == '__main__':
    process_buses()  
    app.run(debug=True)
