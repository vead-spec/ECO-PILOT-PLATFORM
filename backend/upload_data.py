# upload_data.py

import firebase_admin
from firebase_admin import credentials, firestore
import json

# Replace with the path to your service account key file
cred = credentials.Certificate(r"C:\Users\user\OneDrive\Documents\Hackathon_project\Eco-Pilot-Platform\backend\eco-pilot-realtime-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Path to the JSON file
file_path = 'hotels_data.json'

with open(file_path, 'r') as f:
    hotels_data = json.load(f)

# Upload each hotel as a new document to the 'hotels' collection
def upload_data():
    for hotel in hotels_data:
        doc_ref = db.collection('hotels').document(hotel['id'])
        doc_ref.set(hotel)
        print(f"Successfully uploaded hotel: {hotel['name']}")

if __name__ == '__main__':
    upload_data()