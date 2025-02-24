import json
import pyttsx3
import os

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Set the voice (optional)
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)  # Use second voice if available
else:
    engine.setProperty('voice', voices[0].id)

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

def notify_driver(driver, message):
    """
    This function sends a notification to the driver and speaks the message aloud.
    """
    print(f"Notification to {driver}: {message}")
    speak(f"Notification for {driver}. {message}")

