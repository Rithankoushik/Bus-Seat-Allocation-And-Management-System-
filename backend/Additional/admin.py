def request_admin_approval(current_bus, nearby_bus, action):
    if action == "reallocate":
        print(f"Requesting admin approval to reallocate students from Bus {current_bus['id']} to Bus {nearby_bus['id']}.")  # Corrected key names
    elif action == "combine":
        print(f"Requesting admin approval to combine Bus {current_bus['id']} with Bus {nearby_bus['id']}.")  # Corrected key names
    
    admin_approval = input(f"Does the admin approve the {action} action? (yes/no): ").lower()
    return admin_approval == "yes"
