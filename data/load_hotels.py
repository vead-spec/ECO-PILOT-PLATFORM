import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# Ensure the path to your Firebase service account key is correct.
# Replace this with the correct path to your JSON key file.
# The path provided is an example based on a standard project structure.
cred_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'eco-pilot-realtime-firebase-adminsdk.json')

# Check if the credentials file exists
if not os.path.exists(cred_path):
    print(f"Error: Firebase credentials file not found at {cred_path}")
    print("Please ensure your 'eco-pilot-realtime-firebase-adminsdk.json' file is in the 'backend' folder.")
    exit()

# Initialize Firebase App
try:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit()

def upload_hotels_data(json_file_path):
    """
    Reads a JSON file containing hotel data and uploads it to the 'hotels' collection
    in Firestore.
    """
    try:
        with open(json_file_path, 'r') as f:
            hotels = json.load(f)
        
        print(f"Found {len(hotels)} hotels to upload.")
        
        for hotel in hotels:
            hotel_id = hotel.get("hotel_id")
            if not hotel_id:
                print("Skipping a hotel entry with no 'hotel_id'.")
                continue

            doc_ref = db.collection('hotels').document(hotel_id)
            doc_ref.set(hotel)
            print(f"Successfully uploaded hotel: {hotel_id}")
            
        print("\nAll hotel data has been uploaded to Firestore.")
    
    except FileNotFoundError:
        print(f"Error: The file '{json_file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file '{json_file_path}' is not a valid JSON file.")
    except Exception as e:
        print(f"An error occurred during upload: {e}")

if __name__ == '__main__':
    # Adjust this path if your hotels_data.json file is in a different location
    json_path = os.path.join(os.path.dirname(__file__), 'hotels_data.json')
    upload_hotels_data(json_path)
