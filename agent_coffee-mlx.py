from mlx_lm import load, generate
import re
import httpx
import os
import requests

google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY")

class Agent:
    def __init__(self, system=""):
        self.model, self.tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})
            
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result}) 
        return result

    
    def execute(self):
        if self.system:
            prompt = f"System: {self.system}\n\n"
        else:
            prompt = ""
        for msg in self.messages:
            if msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n"

        prompt += "Assistant: " 
        
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            verbose=False  
        )
        
        return response.strip()
    
prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

coffee_location:
e.g. Coffee shops near Boston, MA
run an API call to Google to find coffee shops in and near a city - Uses Python and Google nearby search API

coffee_taste:
e.g. I like my coffee strong and creamy
Returns a list of coffee types that match the taste preferences


Example session:

Question: Where can I find a coffee shop in Boston, MA? 
Thought: I should use the coffee_location action to find a coffee shop
Action: coffee_location: Boston, MA
PAUSE

You will be called again with this:

Observation: Coffee shops in Boston, MA:

You then output:

Answer: A list of coffee shops in Boston, MA
""".strip()


def coffee_taste(taste_preferences):
    # List of possible taste preference keywords
    taste_keywords = [
        'strong', 'bold', 'intense', 'mild', 'creamy', 'smooth',
        'frothy', 'balanced', 'rich', 'diluted', 'chocolatey',
        'less acidic', 'full-bodied', 'robust', 'clean', 'bright',
        'aromatic', 'thick'
    ]
    # Normalize the sentence to lower case and split into words
    words = taste_preferences.lower().split()
    # Extract keywords present in the sentence
    taste_preferences = [word for word in words if word in taste_keywords]
    
    coffee_profiles = [
        {'name': 'Espresso', 'notes': ['strong', 'bold', 'intense']},
        {'name': 'Latte', 'notes': ['mild', 'creamy', 'smooth']},
        {'name': 'Cappuccino', 'notes': ['frothy', 'balanced', 'rich']},
        {'name': 'Americano', 'notes': ['smooth', 'diluted', 'bold']},
        {'name': 'Cold Brew', 'notes': ['smooth', 'chocolatey', 'less acidic']},
        {'name': 'French Press', 'notes': ['rich', 'full-bodied', 'robust']},
        {'name': 'Pour Over', 'notes': ['clean', 'bright', 'aromatic']},
        {'name': 'Turkish Coffee', 'notes': ['strong', 'thick', 'intense']},
    ]
    recommendations = []
    for coffee in coffee_profiles:
        if any(pref.lower() in coffee['notes'] for pref in taste_preferences):
            recommendations.append(coffee['name'])
    return recommendations

def find_nearby_coffee_shops(city, radius=1000):
    geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    geocode_params = {
        'address': city,
        'key': google_maps_key
    }
    geocode_response = requests.get(geocode_url, params=geocode_params)
    geocode_data = geocode_response.json()
    
    if not geocode_data['results']:
        print(f"Could not geocode city: {city}")
        return []
    
    location = geocode_data['results'][0]['geometry']['location']
    latitude = location['lat']
    longitude = location['lng']


    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'key': google_maps_key,
        'location': f'{latitude},{longitude}',
        'radius': radius,
        'keyword': 'coffee shop',
        'type': 'cafe'
    }
    response = requests.get(url, params=params)
    data = response.json()
    coffee_shops = []
    for place in data.get('results', []):
        name = place.get('name')
        address = place.get('vicinity')
        location = place['geometry']['location']
        shop_lat = location['lat']
        shop_lng = location['lng']
        coffee_shops.append({
            'name': name,
            'address': address,
         #   'latitude': shop_lat,
         #   'longitude': shop_lng
        })
    
    return coffee_shops

def query(question, max_turns=10):
    action_re = re.compile(r'^Action: (\w+): (.*)$')
    i = 0
    bot = Agent(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        print(result)
        actions = [
            action_re.match(a) 
            for a in result.split('\n') 
            if action_re.match(a)
        ]
        if actions:
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception("Unknown action: {}: {}".format(action, action_input))
            print(" -- running {} {}".format(action, action_input))
            observation = known_actions[action](action_input)
            print("Observation:", observation)
            next_prompt = "Observation: {}".format(observation)
        else:
            return


known_actions = {
    "coffee_location": find_nearby_coffee_shops,
    "coffee_taste": coffee_taste
}


if __name__ == "__main__":
    
    continue_asking = True
    while continue_asking:
        question = input("Enter your question: ")
        if question.lower() in ['exit', 'quit']:
            print("Goodbye!")
            continue_asking = False
        else:
            query(question)






