import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client
import json
import re
import time

# Initialize Firebase (replace with your service account key file)
cred = credentials.Certificate(r"C:\Users\user\OneDrive\Documents\Hackathon_project\Eco-Pilot-Platform\backend\eco-pilot-realtime-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db: Client = firestore.client()

class Pilot:
    def __init__(self):
        # Cache hotel data to reduce Firestore reads.
        self.hotels = self._fetch_hotel_data()
        self.staff_roles = ['Housekeeping', 'Front Desk', 'Maintenance', 'Concierge', 'IT Support', 'Manager', 'Accountant', 'Procurement Office', 'Kitchen Staff', 'Guide/Concierge', 'Owner/Manager', 'Personal Butler', 'Wellness Coordinator']
        self.reward_values = {
            'eco-action-light': 100,
            'eco-action-water': 200,
            'eco-action-transport': 250,
            'eco-action-food': 180,
            'eco-action-zero-waste': 150,
            'eco-action-major': 500,
            'positive-review': 10,
            'politeness': 2
        }
        self.request_categories = {
            'service_request': ['wi-fi', 'internet', 'clean', 'housekeeping', 'laundry', 'maintenance', 'broken', 'leak', 'booking', 'check-in', 'check-out', 'room service', 'dining', 'meal', 'buzzer', 'towels', 'menu'],
            'eco_request': ['opt out', 'reuse towels', 'no linen', 'turn off lights', 'ac down', 'natural light', 'bike rental', 'bus pass', 'car-sharing', 'vegan', 'local food', 'no-meat', 'digital receipt', 'no paper', 'zero-waste', 'park clean-up', 'coral reef planting', 'tree planting', 'sustainable'],
            'review': ['review', 'feedback', 'happy', 'unhappy', 'disappointed', 'excellent', 'great', 'poor'],
            'medical_alert': ['diabetic', 'asthmatic', 'medical condition', 'therapeutic nutrition']
        }
        self.entity_keywords = {
            'staff': ['front desk staff', 'housekeeping', 'chef', 'concierge', 'attendant'],
            'amenity': ['wi-fi', 'internet', 'pool', 'gym'],
            'room': ['room', 'bed', 'bathroom'],
            'food': ['meal', 'food', 'breakfast', 'dinner']
        }

    def _fetch_hotel_data(self):
        """Fetches and caches all hotel data from Firestore."""
        try:
            hotels_ref = db.collection('hotels')
            hotels_data = {doc.id: doc.to_dict() for doc in hotels_ref.stream()}
            return hotels_data
        except Exception as e:
            print(f"Error fetching hotel data: {e}")
            return {}

    def process_request(self, customer_id, request_details):
        """
        Main function to process a customer's request and trigger task allocation.
        This is the core entry point for the pilot.
        """
        print(f"Processing request for customer {customer_id}")
        
        customer_profile = self._get_customer_profile(customer_id)
        current_hotel_id = request_details.get('hotel_id')
        current_hotel = self.hotels.get(current_hotel_id)

        if not current_hotel:
            print(f"Error: Hotel ID {current_hotel_id} not found.")
            return

        # Tier 1: Triage and Sentiment Analysis
        request_category, sentiment = self._triage_request(request_details)
        print(f"Request categorized as: {request_category} with sentiment: {sentiment}")

        # Tier 2: Intent Recognition
        intent, entities = self._recognize_intent(request_details.get('query', ''), request_category)
        print(f"Recognized intent: {intent}, Entities: {entities}")

        # Tier 3: Automated Task Generation
        tasks = self._generate_tasks(request_category, intent, entities, customer_profile, current_hotel, sentiment)
        
        # Allocate rewards and personalization
        self._allocate_rewards(customer_profile, request_details, tasks, sentiment)
        self._personalize_customer_profile(customer_profile, request_details, sentiment)

        # Send tasks to Firestore for staff app to retrieve
        self._send_tasks_to_staff(tasks, current_hotel_id)
        
        print(f"Tasks generated and sent for customer {customer_id}")

    def _triage_request(self, request_details):
        """Categorizes request type and analyzes sentiment."""
        query = request_details.get('query', '').lower()
        request_type = 'unknown'
        sentiment = 'neutral'

        # Sentiment Analysis
        negative_keywords = ['poor', 'slow', 'bad', 'unhappy', 'dirty', 'broken', 'disappointing', 'rude', 'unresolved']
        positive_keywords = ['excellent', 'great', 'fast', 'happy', 'clean', 'wonderful', 'professional', 'helpful']
        
        if any(keyword in query for keyword in negative_keywords):
            sentiment = 'negative'
        elif any(keyword in query for keyword in positive_keywords):
            sentiment = 'positive'

        # Category Triage
        for category, keywords in self.request_categories.items():
            if any(keyword in query for keyword in keywords):
                request_type = category
                break
        
        return request_type, sentiment

    def _recognize_intent(self, query, category):
        """Extracts specific intent and entities from the query."""
        intent = 'general_inquiry'
        entities = []

        if category == 'service_request':
            if 'wi-fi' in query or 'internet' in query:
                intent = 'tech_support'
                entities.append('Wi-Fi')
            elif 'clean' in query or 'housekeeping' in query:
                intent = 'housekeeping_request'
                entities.append('cleaning')
            elif 'maintenance' in query or 'broken' in query:
                intent = 'maintenance_issue'
                entities.append('maintenance')
            elif 'meal' in query or 'dining' in query or 'menu' in query:
                intent = 'food_order'
                entities.append('food')
            elif 'buzzer' in query or 'towels' in query:
                intent = 'realtime_service'

        elif category == 'eco_request':
            if 'opt out' in query or 'reuse' in query:
                intent = 'eco_housekeeping'
            elif 'transport' in query or 'bike' in query:
                intent = 'eco_transport'
            elif 'vegan' in query or 'local food' in query or 'sustainable' in query:
                intent = 'eco_food'
            elif 'donation' in query:
                intent = 'eco_donation'
        
        elif category == 'medical_alert':
            if 'diabetic' in query or 'therapeutic nutrition' in query:
                intent = 'diabetic_care'
            elif 'asthmatic' in query:
                intent = 'asthma_care'
        
        # Entity extraction
        for entity_type, keywords in self.entity_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    entities.append(keyword)
        
        return intent, entities

    def _generate_tasks(self, category, intent, entities, customer_profile, hotel_data, sentiment):
        """Generates contextual tasks for staff based on recognized intent."""
        tasks_list = []
        customer_name = customer_profile.get('name', 'Guest')
        room_number = customer_profile.get('room_number', 'unknown')

        # Proactive Alerts
        if customer_profile.get('negative_reviews_count', 0) > 3:
            tasks_list.append({
                'role': 'Manager',
                'description': f'Proactive Alert: {customer_name} has a history of negative reviews. Ensure high-quality service.',
                'priority': 'Critical'
            })

        if category == 'medical_alert':
            if intent == 'diabetic_care':
                tasks_list.append({
                    'role': 'Kitchen Staff',
                    'description': f'URGENT: {customer_name} in room {room_number} requires therapeutic nutrition for diabetic condition. Coordinate with chef on duty on suggested meal changes.',
                    'priority': 'Critical'
                })
                tasks_list.append({
                    'role': 'Chef',
                    'description': f'URGENT: {customer_name} in room {room_number} requires diabetic-friendly meal. Suggested changes: avoid added sugars, reduce carbs, and focus on fresh vegetables and lean proteins.',
                    'priority': 'Critical'
                })
            elif intent == 'asthma_care':
                tasks_list.append({
                    'role': 'Front Desk',
                    'description': f'URGENT: {customer_name} in room {room_number} has asthma. Re-allocate room to a lower floor away from potential triggers. Ensure air purifier is installed.',
                    'priority': 'Critical'
                })
        
        elif category == 'review':
            if 'positive' in sentiment:
                tasks_list.append({'role': 'Manager', 'description': f'Acknowledge and praise staff member mentioned in positive review from {customer_name}.', 'priority': 'Low'})
            else:
                tasks_list.append({
                    'role': 'Manager',
                    'description': f'Investigate and resolve negative review from {customer_name} in room {room_number}: {entities}.',
                    'priority': 'Critical'
                })
                tasks_list.append({'role': 'Front Desk', 'description': f'Offer a remedy to {customer_name} for their negative review.', 'priority': 'High'})

        elif category == 'service_request':
            if intent == 'tech_support':
                tasks_list.append({'role': 'IT Support', 'description': f'Troubleshoot Wi-Fi for {customer_name} in room {room_number}.', 'priority': 'Critical'})
            elif intent == 'housekeeping_request':
                tasks_list.append({'role': 'Housekeeping', 'description': f'Attend to a cleaning or laundry request for {customer_name} in room {room_number}.', 'priority': 'High'})
            elif intent == 'realtime_service':
                tasks_list.append({'role': 'Front Desk', 'description': f'URGENT: Buzzer request from {customer_name} in room {room_number}. Respond immediately.', 'priority': 'Critical'})
            elif intent == 'food_order':
                tasks_list.append({'role': 'Kitchen Staff', 'description': f'New meal order for {customer_name} in room {room_number}. Check for eco-friendly suggestions: use locally sourced ingredients and minimal packaging.', 'priority': 'High'})
        
        elif category == 'eco_request':
            tasks_list.append({'role': 'Housekeeping', 'description': f'Guest {customer_name} opted for eco-friendly housekeeping. Update schedule.', 'priority': 'Low'})
        
        return tasks_list

    def _get_customer_profile(self, customer_id):
        """Retrieves or creates a customer profile from Firestore."""
        doc_ref = db.collection('customers').document(customer_id)
        doc = doc_ref.get()
        if doc.exists:
            profile = doc.to_dict()
            if 'tokens' not in profile: profile['tokens'] = 0
            if 'negative_reviews_count' not in profile: profile['negative_reviews_count'] = 0
            if 'positive_reviews_count' not in profile: profile['positive_reviews_count'] = 0
            if 'staff_feedback' not in profile: profile['staff_feedback'] = {}
            if 'is_diabetic' not in profile: profile['is_diabetic'] = False
            if 'is_asthmatic' not in profile: profile['is_asthmatic'] = False
            return profile
        else:
            new_profile = {'id': customer_id, 'history': [], 'preferences': {}, 'tokens': 0, 'negative_reviews_count': 0, 'positive_reviews_count': 0, 'staff_feedback': {}, 'is_diabetic': False, 'is_asthmatic': False}
            doc_ref.set(new_profile)
            return new_profile

    def _personalize_customer_profile(self, customer_profile, request_details, sentiment):
        """Updates the customer's profile based on their behavior."""
        customer_doc_ref = db.collection('customers').document(customer_profile['id'])
        updates = {}
        query = request_details.get('query', '').lower()
        
        if 'please' in query or 'thank you' in query:
            updates['tokens'] = firestore.Increment(self.reward_values['politeness'])
            
        if sentiment == 'positive':
            updates['positive_reviews_count'] = firestore.Increment(1)
            updates['tokens'] = firestore.Increment(self.reward_values['positive-review'])
        elif sentiment == 'negative':
            updates['negative_reviews_count'] = firestore.Increment(1)
            updates['tokens'] = firestore.Increment(-5) # Punishment for negative feedback
        
        if updates:
            customer_doc_ref.update(updates)

    def _calculate_dynamic_reward(self, eco_action, duration_days=1):
        """Calculates a dynamic reward based on action and duration."""
        base_value = self.reward_values.get(eco_action, 0)
        multiplier = 1 + (duration_days - 1) * 0.25 # 25% bonus for each additional day
        return int(base_value * multiplier)

    def _allocate_rewards(self, customer_profile, request_details, tasks, sentiment):
        """Determines and allocates rewards based on customer behavior and eco-friendliness."""
        query = request_details.get('query', '').lower()
        reward_type = None
        duration_days = request_details.get('duration_days', 1)
        
        if any(keyword in query for keyword in ['opt out of', 'no linen', 'reuse towels']):
            reward_type = 'eco-action-water'
        elif any(keyword in query for keyword in ['turn off lights', 'ac down', 'natural light']):
            reward_type = 'eco-action-light'
        elif any(keyword in query for keyword in ['bike rental', 'bus pass', 'car-sharing']):
            reward_type = 'eco-action-transport'
        elif any(keyword in query for keyword in ['vegan', 'local food', 'no-meat', 'sustainable']):
            reward_type = 'eco-action-food'
        elif any(keyword in query for keyword in ['digital receipt', 'no paper', 'zero-waste']):
            reward_type = 'eco-action-zero-waste'
        elif any(keyword in query for keyword in ['park clean-up', 'coral reef planting', 'tree planting']):
            reward_type = 'eco-action-major'

        if reward_type:
            reward_amount = self._calculate_dynamic_reward(reward_type, duration_days)
            reward_details = f'{reward_amount} tokens for a sustainable action.'
            db.collection('customers').document(customer_profile['id']).update({'rewards': firestore.ArrayUnion([{'type': 'Green & Sustainable Reward', 'details': reward_details}]), 'tokens': firestore.Increment(reward_amount)})
            print(f"Reward assigned for sustainable behavior: {reward_details}")

    def _send_tasks_to_staff(self, tasks, hotel_id):
        """Publishes the generated tasks to the 'tasks' collection in Firestore."""
        for task in tasks:
            task['timestamp'] = firestore.SERVER_TIMESTAMP
            task['hotel_id'] = hotel_id
            db.collection('tasks').add(task)

if __name__ == '__main__':
    pilot_engine = Pilot()
    
    # Mock data demonstrating the new desired experience feature
    mock_request = {
        'hotel_id': 'hotel_17', # A Game Park Lodge
        'type': 'query',
        'query': 'What are the romantic activities available?',
        'perfect_solution': 'I want a perfect romantic getaway experience with my partner.'
    }
    mock_customer_id = 'customer_123'
    
    pilot_engine.process_request(mock_customer_id, mock_request)

    # Mock data for a negative review
    negative_review_request = {
        'hotel_id': 'hotel_5',
        'type': 'review',
        'query': 'The service was slow and the amenities were poor. Very disappointed.'
    }
    pilot_engine.process_request('customer_124', negative_review_request)
