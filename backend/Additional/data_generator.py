import json
import random

def generate_chennai_bus_data(num_buses=10):
    buses = []
    for i in range(1, num_buses + 1):
        seating_capacity = random.randint(30, 50)
        current_attendance = random.randint(0, seating_capacity)
        # Chennai coordinates: approximately 13.0827° N, 80.2707° E
        lat = round(random.uniform(13.0, 13.2), 6)
        lng = round(random.uniform(80.1, 80.3), 6)
        buses.append({
            "id": i,
            "driver": f"Driver {i}",
            "seatingCapacity": seating_capacity,
            "currentAttendance": current_attendance,
            "location": f"{lat},{lng}",
            "latitude": lat,
            "longitude": lng
        })
    return buses

def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    bus_data = generate_chennai_bus_data(15)  # Generate data for 15 buses
    save_to_json(bus_data, 'buses.json')
    print("Chennai bus data has been saved to buses.json")