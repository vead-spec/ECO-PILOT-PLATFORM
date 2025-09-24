import random
import time
from backend.pilot_engine import Pilot

pilot_engine = Pilot()

clients = [
    {
        'id': f'client_{i:03d}',
        'name': f'Client {chr(65 + i)}',
        'hotel_id': f'hotel_{random.randint(1, 15)}',
        'is_diabetic': random.choice([True, False]),
        'is_asthmatic': random.choice([True, False]),
        'requests': [
            {'type': 'query', 'query': 'Could you please help with a wifi issue?'},
            {'type': 'review', 'query': 'The housekeeping service was excellent, thank you!'},
            {'type': 'query', 'query': 'I need a diabetic-friendly meal plan for my stay.'},
            {'type': 'query', 'query': 'I would like to opt out of daily linen changes for 3 days.', 'duration_days': 3},
            {'type': 'query', 'query': 'I am an asthmatic. I need a room away from allergens.'},
            {'type': 'buzzer_request', 'query': 'Can I get some fresh towels?'},
            {'type': 'review', 'query': 'The service was terribly slow.'}
        ]
    } for i in range(100)
]

def simulate_client_interactions():
    """Simulates each client making one or more requests to the pilot engine."""
    print("Starting client interaction simulation...")
    for client in clients:
        customer_id = client['id']
        hotel_id = client['hotel_id']
        requests_to_make = random.sample(client['requests'], random.randint(1, len(client['requests'])))

        for request in requests_to_make:
            request['hotel_id'] = hotel_id
            print(f"\n--- Simulating request from {client['name']} (ID: {customer_id}) at Hotel {hotel_id} ---")
            pilot_engine.process_request(customer_id, request)
            time.sleep(1) # Pause to simulate a real-world delay

    print("\nSimulation complete. All client requests have been processed.")

if __name__ == '__main__':
    simulate_client_interactions()
