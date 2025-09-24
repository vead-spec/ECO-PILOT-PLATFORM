import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import os
import logging

# Enable detailed logging for the Firebase Admin SDK
logging.basicConfig(level=logging.DEBUG)

def initialize_firebase():
    """Initializes the Firebase Admin SDK using the downloaded credentials."""
    try:
        # Load credentials from the JSON file
        cred_path = os.path.join(os.path.dirname(__file__), 'eco-pilot-realtime-firebase-adminsdk.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return None

def save_data(db, collection_name, document_id, data):
    """Saves or updates a document in a specified Firestore collection."""
    try:
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.set(data)
        print(f"Success: Data saved to Firestore at {collection_name}/{document_id}")
    except Exception as e:
        print(f"Error saving data to Firestore: {e}")
        # The `logging.DEBUG` output will provide more details.

def get_data(db, collection_name, document_id):
    """Retrieves a document from a specified Firestore collection."""
    try:
        doc_ref = db.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            print("No such document!")
            return None
    except Exception as e:
        print(f"Error getting data from Firestore: {e}")
        # The `logging.DEBUG` output will provide more details.
        return None

if __name__ == '__main__':
    db = initialize_firebase()
    if db:
        # Example Usage: Save some sample data
        sample_data = {
            'hotel_id': 'fairmont_norfolk',
            'room_id': '101',
            'realtime_usage': {
                'water_liters': 15,
                'electricity_kwh': 2.3,
                'wifi_data_mb': 500
            }
        }
        save_data(db, 'realtime_data', 'fairmont_norfolk_101', sample_data)
        
        # Example Usage: Get the data back
        retrieved_data = get_data(db, 'realtime_data', 'fairmont_norfolk_101')
        print("Retrieved Data:")
        print(retrieved_data)