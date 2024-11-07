from mlx_lm import load, generate
import re
import httpx
import os
import requests
import streamlit as st

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


known_actions = {
    "coffee_location": find_nearby_coffee_shops,
    "coffee_taste": coffee_taste
}



'''
Web interface for the AgentCoffee project.

'''

# Initialize session state for conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Initialize session state for user input
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

action_re = re.compile(r'^Action: (\w+): (.*)$')

def process_query(user_input, max_turns=10):
    bot = Agent(prompt)
    next_prompt = user_input
    final_response = ""
    i = 0
    
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        
        actions = [
            action_re.match(a) 
            for a in result.split('\n') 
            if action_re.match(a)
        ]
        
        if actions:
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception(f"Unknown action: {action}: {action_input}")
            
            observation = known_actions[action](action_input)
            next_prompt = f"Observation: {observation}"
            final_response = result
        else:
            final_response = result
            break
            
    return final_response

def main():
    st.title('AgentCoffee, at your service! ☕')
    st.write("Ask me anything about your taste preferences and I'll recommend ways to enjoy coffee!")

    # Custom CSS for styling
    st.markdown("""
        <style>
            /* Container styling */
            .chat-message {
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                display: flex;
                flex-direction: column;
                white-space: pre-wrap;
            }
            
            .user-message {
                background-color: #f0f0f0;
            }
            
            .assistant-message {
                background-color: #e1f5fe;
            }
            
            /* Button styling */
            .stButton > button {
                background-color: #1E3D59 !important;
                color: white !important;
                border: none !important;
                padding: 0 16px !important;
                border-radius: 4px !important;
                height: 45px !important;
                margin-top: -10px !important;
            }
            
            .stButton > button:hover {
                background-color: #2E4D69 !important;
            }
            
            /* Input field styling */
            .stTextInput > div > div > input {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                height: 45px !important;
                min-width: 600px !important;
            }
            
            /* Coffee shop list styling */
            .coffee-shop-list {
                margin-top: 10px;
                line-height: 1.5;
            }
        </style>
    """, unsafe_allow_html=True)

    # Create a container for chat history with scrolling
    with st.expander("Chat History", expanded=True):
        # Display chat history
        for message in st.session_state.conversation_history:
            role = message["role"]
            content = message["content"]
            
            # Style based on role
            if role == "user":
                st.markdown(f"""
                    <div class="chat-message user-message">
                        <div><strong>You:</strong></div>
                        <div>{content}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <div><strong>Assistant:</strong></div>
                        <div>{content}</div>
                    </div>
                """, unsafe_allow_html=True)

    # Create input container
    with st.container():
        col1, col2 = st.columns([8, 1])
        
        # Input field
        with col1:
            user_input = st.text_input(
                "Ask me about coffee...",
                key="input_field",
                value=st.session_state.user_input,
                label_visibility="collapsed"
            )

        # Send button
        with col2:
            send_button = st.button("Send", key="send_button", use_container_width=True)

    # Process input when send button is clicked
    if send_button and user_input:
        # Add user message to history
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Show processing status
        status = st.empty()
        status.text("Processing...")
        
        try:
            # Get response from bot
            response = process_query(user_input)
            
            # Add bot response to history
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Clear status and input
            status.empty()
            st.session_state.user_input = ""
            st.rerun()
            
        except Exception as e:
            status.error(f"Error: {str(e)}")

    # Clear chat button
    if st.button('Clear Chat', key='clear_chat'):
        st.session_state.conversation_history = []
        st.session_state.user_input = ""
        st.rerun()

    # Sidebar information
    with st.sidebar:
        st.subheader("About AgentCoffee")
        st.write("""
        AgentCoffee can:
        - Find coffee shops near you
        - Recommend coffee based on your taste
        - Help you discover new coffee experiences
        """)

if __name__ == "__main__":
    main()


#TODO: Depending on the order of the questions asked the both tools may not run.

