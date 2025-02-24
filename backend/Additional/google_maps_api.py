import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API key from environment variable
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

def find_nearby_bus(current_bus, buses, find_empty=True):
    if not GOOGLE_MAPS_API_KEY:
        print("Error: GOOGLE_MAPS_API_KEY not found in environment variables")
        return fallback_nearby_bus(current_bus, buses, find_empty)

    use_google_maps_api = False  # Set this to True when you want to use the Google Maps API

    if use_google_maps_api:
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
                    return fallback_nearby_bus(current_bus, buses, find_empty)

                distances = [element['distance']['value'] for element in elements]
                return process_excel_distances(current_bus, buses, distances, find_empty)
            else:
                print("Error: 'rows' not found in API response")
                return fallback_nearby_bus(current_bus, buses, find_empty)
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return fallback_nearby_bus(current_bus, buses, find_empty)
        except ValueError as e:
            print(f"Error processing API response: {e}")
            return fallback_nearby_bus(current_bus, buses, find_empty)
    else:
        print("Google Maps API is disabled. Using fallback method for Excel data...")
        return fallback_nearby_bus(current_bus, buses, find_empty)

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

def fallback_nearby_bus(current_bus, buses, find_empty):
    print("Using fallback method to find nearby bus from Excel data...")
    min_distance = float('inf')
    selected_bus = None

    for bus in buses:
        if bus['id'] != current_bus['id']:
            # Calculate Manhattan distance as a simple fallback
            distance = (abs(bus['latitude'] - current_bus['latitude']) + 
                        abs(bus['longitude'] - current_bus['longitude'])) * 111  # Approximate km per degree

            if find_empty:
                available_seats = bus['seatingCapacity'] - bus['currentAttendance']
                if available_seats > 0 and distance < min_distance:
                    min_distance = distance
                    selected_bus = bus
            else:
                combined_attendance = current_bus['currentAttendance'] + bus['currentAttendance']
                if combined_attendance <= max(current_bus['seatingCapacity'], bus['seatingCapacity']) and distance < min_distance:
                    min_distance = distance
                    selected_bus = bus

    return selected_bus, min_distance
