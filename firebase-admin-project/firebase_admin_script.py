import firebase_admin
from firebase_admin import credentials, firestore, auth
import random
import time

# Global variables provided by the environment
# The __app_id variable is essential for setting the correct Firestore collection path.
app_id = 'default-app-id' # Replace with a test ID if running outside the canvas environment

# Initialize Firebase Admin SDK
try:
    # Use a dummy credential for environments where a service account key is not available
    # In a real server environment, the serviceAccountKey.json file is used automatically.
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Failed to initialize Firebase with service account key: {e}")
    print("This script will not be able to write data to Firestore.")
    exit()

db = firestore.client()

def generate_hotel_data(num_hotels=50):
    """Generates a list of mock hotel data for training."""
    locations = ["New York, USA", "London, UK", "Paris, France", "Tokyo, Japan", "Sydney, Australia", "Rome, Italy", "Dubai, UAE", "Rio de Janeiro, Brazil"]
    amenities_options = ["Wi-Fi", "Pool", "Gym", "Restaurant", "Bar", "Spa", "Lounge", "Conference Room", "Room Service", "Laundry"]
    
    hotels = []
    for i in range(1, num_hotels + 1):
        name = f"Hotel Excellence #{i}"
        location = random.choice(locations)
        rating = round(random.uniform(3.0, 5.0), 1)
        rooms = random.randint(50, 500)
        num_amenities = random.randint(2, 6)
        amenities = random.sample(amenities_options, num_amenities)
        
        hotels.append({
            "name": name,
            "location": location,
            "rating": rating,
            "rooms": rooms,
            "amenities": amenities
        })
    return hotels

def add_mock_hotel_data():
    """Adds a collection of mock hotel data to Firestore."""
    
    # Use the correct public path for the collection
    collection_path = f"artifacts/{app_id}/public/data/hotels"
    
    # Delete existing documents to avoid duplicates
    print("Clearing existing hotel data...")
    docs = db.collection(collection_path).stream()
    for doc in docs:
        doc.reference.delete()
    time.sleep(1) # Wait for a second for deletions to propagate

    hotels_ref = db.collection(collection_path)
    hotels_data = generate_hotel_data()
    
    print(f"Adding {len(hotels_data)} hotel data entries to Firestore...")
    for hotel in hotels_data:
        hotels_ref.add(hotel)

    print("Hotel data added successfully.")
    
def get_hotel_data():
    """Retrieves and prints all documents from the hotels collection."""
    
    # Use the correct public path to retrieve the data
    collection_path = f"artifacts/{app_id}/public/data/hotels"

    print("\nGetting hotel data from Firestore...")
    hotels_ref = db.collection(collection_path)
    docs = hotels_ref.stream()
    
    count = 0
    for doc in docs:
        print(f"Document ID: {doc.id}")
        print(f"Data: {doc.to_dict()}\n")
        count += 1
    
    print(f"Retrieved {count} documents.")

def set_user_role(email, role):
    """Sets a user's role in the Firestore database."""
    try:
        user = auth.get_user_by_email(email)
        user_doc_ref = db.collection(f"artifacts/{app_id}/public/data/users").document(user.uid)
        user_doc_ref.set({"role": role})
        print(f"Successfully set role '{role}' for user: {email}")
    except Exception as e:
        print(f"Error setting role for user {email}: {e}")

def clear_user_profiles():
    """Clears all documents from the user_profiles collection."""
    collection_path = f"artifacts/{app_id}/public/data/user_profiles"
    print("Clearing existing user profiles...")
    docs = db.collection(collection_path).stream()
    for doc in docs:
        doc.reference.delete()
    print("User profiles cleared.")

# Run the functions
if __name__ == "__main__":
    add_mock_hotel_data()
    get_hotel_data()

    # To set a user's role, you must first create them by signing up on the website.
    # Then, uncomment and run this function with the user's email and desired role.
    # Example:
    # set_user_role("example-staff@example.com", "staff")
    
    # Uncomment to clear user profiles for testing
    # clear_user_profiles()
