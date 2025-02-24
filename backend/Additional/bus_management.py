from google_maps_api import find_nearby_bus  # Updated import statement
from admin import request_admin_approval
from utils import notify_driver

def check_attendance_and_notify(current_bus, buses):
    if current_bus['currentAttendance'] >= current_bus['seatingCapacity']:  # Corrected key names
        handle_full_bus(current_bus, buses)
    elif current_bus['currentAttendance'] < current_bus['seatingCapacity'] * 0.5:  # Less than 50% capacity
        handle_low_attendance_bus(current_bus, buses)

def handle_full_bus(current_bus, buses):
    print(f"Bus {current_bus['id']} is full. Looking for nearby bus...")
    nearby_bus, distance = find_nearby_bus(current_bus, buses, find_empty=True)
    if nearby_bus:
        approved = request_admin_approval(current_bus, nearby_bus, "reallocate")
        if approved:
            print(f"Request approved. Notifying drivers {current_bus['driver']} and {nearby_bus['driver']}.")
            notify_driver(current_bus['driver'], f"Your bus is full. Students will be allocated to Bus {nearby_bus['id']}.")
            notify_driver(nearby_bus['driver'], f"Please pick up additional students from Bus {current_bus['id']}.")
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
            notify_driver(current_bus['driver'], f"Your bus will be combined with Bus {nearby_bus['id']}. Please proceed to the designated meeting point.")
            notify_driver(nearby_bus['driver'], f"Your bus will be combined with Bus {current_bus['id']}. Please proceed to the designated meeting point.")
        else:
            print("Request denied by admin.")
    else:
        print("No suitable nearby bus found for combining or unable to fetch nearby bus information.")
