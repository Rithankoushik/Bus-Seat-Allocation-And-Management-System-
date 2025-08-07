 Passenger Management and Reallocation System
 
📌 Project Overview
The Passenger Management and Reallocation System is an intelligent, real-time college transportation management platform that automates the monitoring of student bus attendance, dynamically reallocates students to nearby buses when overcapacity is detected, and combines underutilized buses based on live data and route proximity.

The system integrates Google Sheets as a live database (via BUSNET-X, a geo-fenced attendance logging hardware) to fetch attendance and location details, Google Maps API to calculate distances between buses, and Twilio API to notify drivers via automated phone calls once an admin approves any action.

🎯 Problem Statement
Managing student transportation is challenging when dealing with real-time crowd fluctuations. Some buses exceed their capacity, causing overcrowding and safety issues, while others operate with very few students, wasting fuel and increasing operational costs. There is a lack of a centralized, automated solution that handles capacity-based reallocation and route optimization based on live attendance and GPS data.

✅ Solution Proposed
This system provides a smart, automated approach to passenger monitoring and reallocation. Students mark their attendance using a biometric device (BUSNET-X), which logs the data into a Google Sheet in real-time. The reallocation engine processes this data continuously, detects capacity violations or underutilization, and triggers one of the two core actions:

Reallocation: If a bus exceeds its seating capacity, the system identifies the nearest bus with available seats and requests the admin's approval to reallocate students.

Combination: If two or more buses have significantly low attendance, they are proposed to be merged at a common point to conserve resources.

Once approved, both drivers are notified through phone calls using Twilio. The system also visually displays all bus locations and statuses on a web dashboard using Google Maps.

🧠 Key Features
Live Attendance Tracking via Google Sheets

Automatic Overcrowding Detection

Dynamic Student Reallocation

Bus Combination Based on Route Proximity

Admin Approval Workflow

Voice Notification to Drivers (Twilio)

Real-time Visualization of Bus Locations (Google Maps)

Separate Views for Admin and Students

🧰 Technologies Used
Frontend: HTML, CSS, JavaScript

Backend: Python (Flask)

Database: Google Sheets API

APIs: Google Maps Distance Matrix API, Twilio Voice API

Other Tools: Pyttsx3 for local TTS fallback, Pandas for data processing

📁 Project Structure
bash
Copy
Edit
project/
│
├── app.py               # Flask server for API and routing
├── main.py              # Logic for checking reallocation & combination
├── templates/
│   ├── index.html       # Login page
│   ├── admin.html       # Admin dashboard
│   ├── student.html     # Student view
│   └── bus_details.html # Detailed view of all buses
│
├── static/
│   ├── styles.css       # Stylesheet
│   └── script.js        # Frontend logic (map rendering, actions)
│
├── buses.xlsx           # Local fallback (now replaced by Google Sheets)
└── .env                 # Environment variables (API keys, phone numbers)
🛠 How It Works
Students board the bus and register their presence via BUSNET-X (biometric device).

This logs attendance and GPS location directly to a connected Google Sheet.

The backend reads this data in real-time and identifies:

If a bus is overcrowded → find the nearest bus with space.

If a bus is underloaded → find a nearby underloaded bus to combine.

A reallocation/combination request is sent to the admin.

Upon approval, drivers are notified via automated Twilio voice calls.

All updates are reflected live on the admin dashboard map.

🌍 Use Cases
Colleges/Universities with a large fleet of buses

Corporate Transport Services handling shift-based employees

School Bus Systems needing live monitoring and dynamic rerouting

🚀 Deployment Instructions
Clone the repository

bash
Copy
Edit
git clone https://github.com/your-repo/passenger-reallocation-system.git
cd passenger-reallocation-system
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Create a .env file with your credentials:

ini
Copy
Edit
GOOGLE_MAPS_API_KEY=your_api_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+your_twilio_number
Run the app

bash
Copy
Edit
python app.py
Visit the local server at

arduino
Copy
Edit
http://localhost:5000/
🔒 Admin Credentials (Sample for Demo)
Role	Username	Password
Admin	admin	admin123
Student	student	student123

💡 Future Enhancements
Mobile app for drivers and students

SMS-based OTP check-ins

AI-based route optimization

QR Code-based attendance integration

📜 License
This project is intended for educational and research purposes only. Feel free to modify and improve upon it for your use case.

