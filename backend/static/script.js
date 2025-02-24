// Fetch the Google Maps API key from the server
fetch('/api/google-maps-key')
    .then(response => response.json())
    .then(data => {
        const apiKey = data.apiKey;
        loadGoogleMaps(apiKey);
    });

function loadGoogleMaps(apiKey) {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initMap`;
    script.async = true;
    document.head.appendChild(script);
}

// Initialize and add the map
function initMap() {
    const collegeIcon = {
        url: 'logo.png',
        scaledSize: new google.maps.Size(30, 30)
    };

    const busIcon = {
        url: 'https://maps.google.com/mapfiles/kml/shapes/bus.png',
        scaledSize: new google.maps.Size(32, 32),
        anchor: new google.maps.Point(16, 16) // Center the icon
    };

    const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 10,
        center: { lat: 13.0382, lng: 80.0454 },
    });

    // College marker
    const collegePosition = { lat: 13.0382, lng: 80.0454 };
    new google.maps.Marker({
        position: collegePosition,
        map: map,
        icon: collegeIcon,
        title: 'RIT Chennai'
    });

    // Create a DirectionsService object
    const directionsService = new google.maps.DirectionsService();
    
    fetch('/api/bus-locations')
        .then(response => response.json())
        .then(data => {
            data.forEach(bus => {
                const marker = new google.maps.Marker({
                    position: { lat: bus.latitude, lng: bus.longitude },
                    map: map,
                    icon: busIcon,
                    title: `Bus ID: ${bus.id}`
                });

                // Create a unique DirectionsRenderer for each bus
                const directionsRenderer = new google.maps.DirectionsRenderer({
                    map: map,
                    suppressMarkers: true, // Don't show default markers
                    polylineOptions: {
                        strokeColor: "#0000FF",
                        strokeOpacity: 0.8,
                        strokeWeight: 3
                    }
                });

                // Calculate and display route to college
                const request = {
                    origin: { lat: bus.latitude, lng: bus.longitude },
                    destination: collegePosition,
                    travelMode: google.maps.TravelMode.DRIVING
                };

                directionsService.route(request, (result, status) => {
                    if (status === google.maps.DirectionsStatus.OK) {
                        directionsRenderer.setDirections(result);
                    }
                });

                // Add click event to show detailed route
                marker.addListener('click', () => {
                    showRoute(bus.id, map);
                });
            });
        });
}

// Function to show route from bus to center
function showRoute(busId, map) {
    fetch(`/api/route?bus_id=${busId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Route data:', data); // Debugging line
            if (data.routes && data.routes.length > 0) {
                const directionsService = new google.maps.DirectionsService();
                const directionsRenderer = new google.maps.DirectionsRenderer();
                directionsRenderer.setMap(map);

                const route = data.routes[0];
                const start = route.legs[0].start_location;
                const end = route.legs[0].end_location;

                const request = {
                    origin: start,
                    destination: end,
                    travelMode: google.maps.TravelMode.DRIVING
                };

                directionsService.route(request, (result, status) => {
                    if (status === google.maps.DirectionsStatus.OK) {
                        directionsRenderer.setDirections(result);
                    } else {
                        console.error('Directions request failed due to:', status); // Debugging line
                        alert('Could not display directions due to: ' + status);
                    }
                });
            } else {
                console.error('No route found'); // Debugging line
                alert('No route found');
            }
        });
}

// Load bus details into the table
function loadBusDetails() {
    fetch('/api/bus-details')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('busTable').getElementsByTagName('tbody')[0];
            data.forEach(bus => {
                const row = tableBody.insertRow();
                row.insertCell(0).textContent = bus.id;
                row.insertCell(1).textContent = bus.driver;
                row.insertCell(2).textContent = bus.seatingCapacity;
                row.insertCell(3).textContent = bus.currentAttendance;
                row.insertCell(4).textContent = bus.location;
                const actionCell = row.insertCell(5);
                const acceptButton = document.createElement('button');
                acceptButton.textContent = 'Accept';
                acceptButton.onclick = () => handleAction(bus.id, 'accept');
                const denyButton = document.createElement('button');
                denyButton.textContent = 'Deny';
                denyButton.onclick = () => handleAction(bus.id, 'deny');
                actionCell.appendChild(acceptButton);
                actionCell.appendChild(denyButton);
            });
        });
}

// Handle accept/deny actions
function handleAction(busId, action) {
    fetch(`/api/bus-action/${busId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action }),
    })
    .then(response => response.json())
    .then(data => {
        alert(`Action ${action} for bus ${busId} was ${data.success ? 'successful' : 'unsuccessful'}`);
    });
}

// Load bus details on page load
window.onload = function() {
    loadBusDetails();
};

// Load pending actions into the table
function loadPendingActions() {
    fetch('/api/pending-actions')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('busTable').getElementsByTagName('tbody')[0];
            tableBody.innerHTML = ''; // Clear existing rows
            data.forEach(action => {
                const row = tableBody.insertRow();
                row.insertCell(0).textContent = action.current_bus_id;
                row.insertCell(1).textContent = action.current_bus_details.seatingCapacity;
                row.insertCell(2).textContent = action.current_bus_details.currentAttendance;
                row.insertCell(3).textContent = action.nearby_bus_id;
                row.insertCell(4).textContent = action.nearby_bus_details.seatingCapacity;
                row.insertCell(5).textContent = action.nearby_bus_details.currentAttendance;
                row.insertCell(6).textContent = action.action;
                row.insertCell(7).textContent = action.message;
                row.insertCell(8).textContent = `Current Bus: ${action.current_bus_details.location}, Nearby Bus: ${action.nearby_bus_details.location}`;
                const actionCell = row.insertCell(9);
                const acceptButton = document.createElement('button');
                acceptButton.textContent = 'Accept';
                acceptButton.onclick = () => handleAdminAction(action, true);
                const denyButton = document.createElement('button');
                denyButton.textContent = 'Deny';
                denyButton.onclick = () => handleAdminAction(action, false);
                actionCell.appendChild(acceptButton);
                actionCell.appendChild(denyButton);
            });
        });
}

// Handle admin action
function handleAdminAction(action, approved) {
    fetch('/api/admin-action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            current_bus_id: action.current_bus_id,
            nearby_bus_id: action.nearby_bus_id,
            action: action.action,
            approved: approved
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadPendingActions(); // Refresh the list of pending actions
    })
    .catch(error => console.error('Error:', error));
}

// Load pending actions on page load
window.onload = function() {
    loadPendingActions();
};

