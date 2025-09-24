# This script reads hotel and scenario data from local files and uploads it to Firestore.

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import re

# --- Firebase Initialization ---
# Ensure the path to your Firebase service account key is correct.
# Replace this with the correct path to your JSON key file.
# The path provided is an example based on a standard project structure.
cred_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'eco-pilot-realtime-firebase-adminsdk.json')

# Check if the credentials file exists
if not os.path.exists(cred_path):
    print(f"Error: Firebase credentials file not found at {cred_path}")
    print("Please ensure your 'eco-pilot-realtime-firebase-adminsdk.json' file is in the 'backend' folder.")
    exit()

try:
    cred = credentials.Certificate(cred_path)
    # Check if the app is already initialized to avoid errors in multiple runs
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit()

# --- Data Parsing and Upload Functions ---

def parse_markdown_scenarios(md_file_path):
    """
    Parses the Markdown file to extract and return a list of scenario dictionaries.
    """
    scenarios = []
    current_hotel = ''
    current_hotel_budget = ''
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Regular expression to match hotel headers
        hotel_header_pattern = re.compile(r'\*\*Hotel: (.+?) \((.+?)\)\*\*')
        # Regular expression to match each scenario line
        scenario_line_pattern = re.compile(r'^(\d+)\. \*\*Scenario #(\d+):(.+?)earning \*\*(.+?) tokens\*\*')

        lines = markdown_content.split('\n')
        for line in lines:
            # Check for a hotel header
            hotel_match = hotel_header_pattern.search(line)
            if hotel_match:
                current_hotel = hotel_match.group(1).strip()
                current_hotel_budget = hotel_match.group(2).replace('-End', '').strip()
                continue

            # Check for a scenario line
            scenario_match = scenario_line_pattern.search(line)
            if scenario_match:
                scenario_id = int(scenario_match.group(1))
                description = scenario_match.group(3).strip()
                token_value = int(scenario_match.group(4).replace(',', ''))
                
                # Extract client details from the description
                client_match = re.search(r'Client (.+?) \(Budget: (.+?)\)', description)
                client_name = client_match.group(1) if client_match else 'Unknown'
                client_budget = client_match.group(2) if client_match else 'Unknown'

                scenarios.append({
                    "id": scenario_id,
                    "hotel_name": current_hotel,
                    "hotel_budget": current_hotel_budget,
                    "client_name": client_name,
                    "client_budget": client_budget,
                    "description": description,
                    "tokens": token_value
                })

    except FileNotFoundError:
        print(f"Error: The file '{md_file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred during Markdown parsing: {e}")
        return None
    
    return scenarios

def upload_data(collection_name, data, doc_id_field):
    """
    Generic function to upload a list of dictionaries to a Firestore collection.
    """
    if not data:
        print(f"No data to upload for collection '{collection_name}'.")
        return

    print(f"\nFound {len(data)} items to upload to '{collection_name}'...")
    batch = db.batch()
    for item in data:
        doc_id = item.get(doc_id_field)
        if not doc_id:
            print(f"Skipping an entry with no '{doc_id_field}' for collection '{collection_name}'.")
            continue
        
        doc_ref = db.collection(collection_name).document(str(doc_id))
        batch.set(doc_ref, item)

    try:
        batch.commit()
        print(f"Successfully uploaded all data to '{collection_name}'.")
    except Exception as e:
        print(f"An error occurred during batch upload to '{collection_name}': {e}")

if __name__ == '__main__':
    # Define file paths
    hotels_json_path = os.path.join(os.path.dirname(__file__), 'hotels_data.json')
    scenarios_md_path = os.path.join(os.path.dirname(__file__), '..', 'Hotel_Eco_Scenarios.md')

    # Upload Hotels Data
    try:
        with open(hotels_json_path, 'r', encoding='utf-8') as f:
            hotels_data = json.load(f)
        upload_data('hotels', hotels_data, 'hotel_id')
    except Exception as e:
        print(f"Could not load or upload hotels data: {e}")

    # Upload Scenarios Data
    scenarios_data = parse_markdown_scenarios(scenarios_md_path)
    if scenarios_data:
        upload_data('scenarios', scenarios_data, 'id')
