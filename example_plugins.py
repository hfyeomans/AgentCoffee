"""
Example Action Plugins for the Modern Agent System
Includes enhanced versions of the coffee-related actions plus new capabilities
"""

import os
import asyncio
import aiohttp
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import logging

from modern_agent_system import ActionPlugin, ActionResult

logger = logging.getLogger(__name__)

# Get API keys from environment
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


class CoffeeLocationPlugin(ActionPlugin):
    """Enhanced coffee location finder with caching and detailed information"""
    
    def __init__(self):
        super().__init__(
            name="coffee_location",
            description="Find coffee shops in a specific location with detailed information"
        )
        self.cache = {}
        self.cache_duration = 3600  # 1 hour
    
    def validate_inputs(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """Validate input parameters"""
        if "city" not in kwargs:
            return False, "Missing required parameter: city"
        
        if not isinstance(kwargs["city"], str) or not kwargs["city"].strip():
            return False, "City must be a non-empty string"
        
        if "radius" in kwargs:
            try:
                radius = int(kwargs["radius"])
                if radius < 100 or radius > 50000:
                    return False, "Radius must be between 100 and 50000 meters"
            except (ValueError, TypeError):
                return False, "Radius must be a valid integer"
        
        return True, None
    
    async def execute(self, **kwargs) -> ActionResult:
        """Execute the coffee location search"""
        city = kwargs["city"]
        radius = kwargs.get("radius", 1500)
        
        # Check cache
        cache_key = f"{city}_{radius}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_duration:
                logger.info(f"Returning cached results for {city}")
                return ActionResult(
                    success=True,
                    data=cached_data,
                    metadata={"cached": True, "cache_age": (datetime.now() - timestamp).seconds}
                )
        
        try:
            # Get coordinates for the city
            geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json'
            geocode_params = {
                'address': city,
                'key': GOOGLE_MAPS_API_KEY
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(geocode_url, params=geocode_params) as response:
                    geocode_data = await response.json()
            
            if not geocode_data.get('results'):
                return ActionResult(
                    success=False,
                    error=f"Could not find location: {city}"
                )
            
            location = geocode_data['results'][0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
            formatted_address = geocode_data['results'][0]['formatted_address']
            
            # Search for coffee shops
            places_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
            places_params = {
                'key': GOOGLE_MAPS_API_KEY,
                'location': f'{latitude},{longitude}',
                'radius': radius,
                'keyword': 'coffee shop cafe',
                'type': 'cafe'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(places_url, params=places_params) as response:
                    places_data = await response.json()
            
            coffee_shops = []
            for place in places_data.get('results', [])[:10]:  # Limit to top 10
                shop_info = {
                    'name': place.get('name'),
                    'address': place.get('vicinity'),
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total'),
                    'price_level': place.get('price_level'),
                    'open_now': place.get('opening_hours', {}).get('open_now'),
                    'types': place.get('types', []),
                    'place_id': place.get('place_id'),
                    'location': {
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng']
                    }
                }
                
                # Calculate distance
                shop_info['distance_meters'] = self._calculate_distance(
                    latitude, longitude,
                    shop_info['location']['lat'], shop_info['location']['lng']
                )
                
                coffee_shops.append(shop_info)
            
            # Sort by rating and distance
            coffee_shops.sort(key=lambda x: (-(x.get('rating', 0)), x['distance_meters']))
            
            result_data = {
                'city': city,
                'formatted_address': formatted_address,
                'coordinates': {'lat': latitude, 'lng': longitude},
                'coffee_shops': coffee_shops,
                'total_found': len(coffee_shops),
                'search_radius': radius
            }
            
            # Cache the results
            self.cache[cache_key] = (result_data, datetime.now())
            
            return ActionResult(
                success=True,
                data=result_data,
                metadata={
                    "cached": False,
                    "api_calls": 2,
                    "processing_time": "fast"
                }
            )
            
        except Exception as e:
            logger.error(f"Error finding coffee shops: {e}")
            return ActionResult(
                success=False,
                error=f"Failed to find coffee shops: {str(e)}"
            )
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> int:
        """Calculate distance between two points in meters (simplified)"""
        # Haversine formula (simplified for small distances)
        import math
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return int(R * c)


class CoffeeTastePlugin(ActionPlugin):
    """Enhanced coffee taste recommendation with detailed profiles"""
    
    def __init__(self):
        super().__init__(
            name="coffee_taste",
            description="Recommend coffee types based on taste preferences with detailed information"
        )
        self.coffee_profiles = self._load_coffee_profiles()
    
    def _load_coffee_profiles(self) -> List[Dict[str, Any]]:
        """Load comprehensive coffee profiles"""
        return [
            {
                'name': 'Espresso',
                'notes': ['strong', 'bold', 'intense', 'concentrated'],
                'description': 'A concentrated coffee beverage brewed by forcing hot water under pressure through finely-ground coffee beans.',
                'caffeine_mg': 63,
                'serving_size': '1 oz',
                'brewing_method': 'Espresso machine',
                'origin': 'Italy',
                'best_time': 'Morning or after meals'
            },
            {
                'name': 'Latte',
                'notes': ['mild', 'creamy', 'smooth', 'milky'],
                'description': 'Espresso mixed with steamed milk, creating a creamy and mild coffee drink.',
                'caffeine_mg': 63,
                'serving_size': '8-12 oz',
                'brewing_method': 'Espresso machine + steamed milk',
                'origin': 'Italy',
                'best_time': 'Morning or afternoon'
            },
            {
                'name': 'Cappuccino',
                'notes': ['frothy', 'balanced', 'rich', 'foamy'],
                'description': 'Equal parts espresso, steamed milk, and milk foam, creating a balanced coffee experience.',
                'caffeine_mg': 63,
                'serving_size': '6 oz',
                'brewing_method': 'Espresso machine + steamed milk + foam',
                'origin': 'Italy',
                'best_time': 'Morning'
            },
            {
                'name': 'Americano',
                'notes': ['smooth', 'diluted', 'bold', 'clean'],
                'description': 'Espresso diluted with hot water, similar strength to drip coffee but different flavor.',
                'caffeine_mg': 63,
                'serving_size': '8-12 oz',
                'brewing_method': 'Espresso + hot water',
                'origin': 'World War II era',
                'best_time': 'Any time'
            },
            {
                'name': 'Cold Brew',
                'notes': ['smooth', 'chocolatey', 'less acidic', 'sweet'],
                'description': 'Coffee steeped in cold water for 12-24 hours, resulting in a smooth, less acidic brew.',
                'caffeine_mg': 200,
                'serving_size': '16 oz',
                'brewing_method': 'Cold water immersion for 12-24 hours',
                'origin': 'Japan (Kyoto-style)',
                'best_time': 'Hot weather, afternoon'
            },
            {
                'name': 'French Press',
                'notes': ['rich', 'full-bodied', 'robust', 'oily'],
                'description': 'Coarsely ground coffee steeped in hot water, then filtered by pressing down a metal mesh.',
                'caffeine_mg': 107,
                'serving_size': '8 oz',
                'brewing_method': 'Immersion brewing with metal filter',
                'origin': 'France',
                'best_time': 'Morning, leisurely breakfast'
            },
            {
                'name': 'Pour Over',
                'notes': ['clean', 'bright', 'aromatic', 'nuanced'],
                'description': 'Hot water poured over coffee grounds in a filter, allowing precise control over brewing.',
                'caffeine_mg': 95,
                'serving_size': '8 oz',
                'brewing_method': 'Manual pour over dripper (V60, Chemex)',
                'origin': 'Germany (Melitta Bentz, 1908)',
                'best_time': 'Morning, when you have time to enjoy'
            },
            {
                'name': 'Turkish Coffee',
                'notes': ['strong', 'thick', 'intense', 'sweet'],
                'description': 'Finely ground coffee boiled with sugar and served unfiltered in small cups.',
                'caffeine_mg': 50,
                'serving_size': '2 oz',
                'brewing_method': 'Boiled in cezve/ibrik',
                'origin': 'Ottoman Empire',
                'best_time': 'After meals, social occasions'
            },
            {
                'name': 'Flat White',
                'notes': ['velvety', 'strong', 'smooth', 'microfoam'],
                'description': 'Double shot of espresso with microfoam milk, stronger than a latte.',
                'caffeine_mg': 130,
                'serving_size': '6 oz',
                'brewing_method': 'Espresso + microfoam milk',
                'origin': 'Australia/New Zealand',
                'best_time': 'Morning or afternoon'
            },
            {
                'name': 'Macchiato',
                'notes': ['strong', 'marked', 'bold', 'slight milk'],
                'description': 'Espresso "marked" with a small amount of steamed milk.',
                'caffeine_mg': 63,
                'serving_size': '2-3 oz',
                'brewing_method': 'Espresso + dash of milk',
                'origin': 'Italy',
                'best_time': 'Morning or after lunch'
            }
        ]
    
    def validate_inputs(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """Validate input parameters"""
        if "preferences" not in kwargs:
            return False, "Missing required parameter: preferences"
        
        if not isinstance(kwargs["preferences"], str) or not kwargs["preferences"].strip():
            return False, "Preferences must be a non-empty string"
        
        return True, None
    
    async def execute(self, **kwargs) -> ActionResult:
        """Execute coffee taste recommendation"""
        preferences = kwargs["preferences"].lower()
        include_details = kwargs.get("include_details", True)
        
        try:
            # Extract taste keywords
            taste_keywords = [
                'strong', 'bold', 'intense', 'mild', 'creamy', 'smooth',
                'frothy', 'balanced', 'rich', 'diluted', 'chocolatey',
                'less acidic', 'full-bodied', 'robust', 'clean', 'bright',
                'aromatic', 'thick', 'sweet', 'velvety', 'microfoam', 'marked'
            ]
            
            # Extract keywords from preferences
            words = preferences.split()
            found_preferences = [word for word in words if word in taste_keywords]
            
            # Score each coffee based on matching preferences
            recommendations = []
            for coffee in self.coffee_profiles:
                score = sum(1 for pref in found_preferences if pref in coffee['notes'])
                if score > 0:
                    coffee_rec = {
                        'name': coffee['name'],
                        'match_score': score,
                        'matched_notes': [note for note in coffee['notes'] if note in found_preferences]
                    }
                    
                    if include_details:
                        coffee_rec.update({
                            'description': coffee['description'],
                            'caffeine_mg': coffee['caffeine_mg'],
                            'serving_size': coffee['serving_size'],
                            'brewing_method': coffee['brewing_method'],
                            'origin': coffee['origin'],
                            'best_time': coffee['best_time'],
                            'all_notes': coffee['notes']
                        })
                    
                    recommendations.append(coffee_rec)
            
            # Sort by match score
            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            
            # If no matches, suggest based on general preferences
            if not recommendations:
                # Analyze for general preferences
                if any(word in preferences for word in ['strong', 'wake', 'energy', 'bold']):
                    default_recs = ['Espresso', 'Cold Brew', 'French Press']
                elif any(word in preferences for word in ['mild', 'smooth', 'light', 'gentle']):
                    default_recs = ['Latte', 'Flat White', 'Pour Over']
                elif any(word in preferences for word in ['sweet', 'dessert', 'treat']):
                    default_recs = ['Latte', 'Cappuccino', 'Turkish Coffee']
                else:
                    default_recs = ['Americano', 'Pour Over', 'Latte']
                
                recommendations = [
                    {
                        'name': coffee['name'],
                        'match_score': 0,
                        'matched_notes': [],
                        'reason': 'General recommendation based on your preferences',
                        **({k: v for k, v in coffee.items() if k != 'name' and k != 'notes'} if include_details else {})
                    }
                    for coffee in self.coffee_profiles if coffee['name'] in default_recs
                ]
            
            result_data = {
                'preferences': preferences,
                'found_keywords': found_preferences,
                'recommendations': recommendations[:5],  # Top 5 recommendations
                'total_matches': len([r for r in recommendations if r['match_score'] > 0])
            }
            
            return ActionResult(
                success=True,
                data=result_data,
                metadata={
                    "processing_type": "keyword_matching",
                    "coffee_database_size": len(self.coffee_profiles)
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating coffee recommendations: {e}")
            return ActionResult(
                success=False,
                error=f"Failed to generate recommendations: {str(e)}"
            )


class WeatherPlugin(ActionPlugin):
    """Weather information plugin for planning coffee runs"""
    
    def __init__(self):
        super().__init__(
            name="weather",
            description="Get current weather information for a location"
        )
    
    def validate_inputs(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """Validate input parameters"""
        if "location" not in kwargs:
            return False, "Missing required parameter: location"
        
        if not isinstance(kwargs["location"], str) or not kwargs["location"].strip():
            return False, "Location must be a non-empty string"
        
        return True, None
    
    async def execute(self, **kwargs) -> ActionResult:
        """Execute weather check"""
        location = kwargs["location"]
        
        if not OPENWEATHER_API_KEY:
            # Return mock data if no API key
            return ActionResult(
                success=True,
                data={
                    'location': location,
                    'temperature': 72,
                    'feels_like': 70,
                    'condition': 'Clear',
                    'humidity': 45,
                    'wind_speed': 5,
                    'is_good_for_walking': True,
                    'recommendation': 'Perfect weather for a coffee walk!',
                    'mock_data': True
                },
                metadata={"mock": True}
            )
        
        try:
            # Get weather data
            weather_url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': location,
                'appid': OPENWEATHER_API_KEY,
                'units': 'imperial'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(weather_url, params=params) as response:
                    weather_data = await response.json()
            
            if weather_data.get('cod') != 200:
                return ActionResult(
                    success=False,
                    error=f"Weather API error: {weather_data.get('message', 'Unknown error')}"
                )
            
            # Extract relevant information
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            condition = weather_data['weather'][0]['main']
            description = weather_data['weather'][0]['description']
            humidity = weather_data['main']['humidity']
            wind_speed = weather_data['wind']['speed']
            
            # Determine if good for walking
            is_good_for_walking = (
                50 <= temp <= 85 and
                condition not in ['Rain', 'Snow', 'Thunderstorm'] and
                wind_speed < 25
            )
            
            # Generate recommendation
            if is_good_for_walking:
                recommendation = f"Great weather for a coffee walk! {description.capitalize()} with comfortable temperatures."
            elif condition in ['Rain', 'Snow']:
                recommendation = f"Consider driving or getting delivery - {description}."
            elif temp < 50:
                recommendation = "Bundle up! It's quite cold for a coffee walk."
            elif temp > 85:
                recommendation = "It's hot outside! Consider iced coffee and a short walk."
            else:
                recommendation = f"Weather is {description}. Plan accordingly!"
            
            result_data = {
                'location': location,
                'temperature': temp,
                'feels_like': feels_like,
                'condition': condition,
                'description': description,
                'humidity': humidity,
                'wind_speed': wind_speed,
                'is_good_for_walking': is_good_for_walking,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }
            
            return ActionResult(
                success=True,
                data=result_data,
                metadata={
                    "api": "openweathermap",
                    "units": "imperial"
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return ActionResult(
                success=False,
                error=f"Failed to get weather information: {str(e)}"
            )


class RoutePlugin(ActionPlugin):
    """Calculate routes and travel times between locations"""
    
    def __init__(self):
        super().__init__(
            name="route",
            description="Calculate route and travel time between locations"
        )
    
    def validate_inputs(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """Validate input parameters"""
        required = ["origin", "destination"]
        for param in required:
            if param not in kwargs:
                return False, f"Missing required parameter: {param}"
        
        if "mode" in kwargs:
            valid_modes = ["driving", "walking", "bicycling", "transit"]
            if kwargs["mode"] not in valid_modes:
                return False, f"Invalid mode. Must be one of: {', '.join(valid_modes)}"
        
        return True, None
    
    async def execute(self, **kwargs) -> ActionResult:
        """Execute route calculation"""
        origin = kwargs["origin"]
        destination = kwargs["destination"]
        mode = kwargs.get("mode", "walking")
        
        try:
            # Use Google Directions API
            directions_url = 'https://maps.googleapis.com/maps/api/directions/json'
            params = {
                'origin': origin,
                'destination': destination,
                'mode': mode,
                'key': GOOGLE_MAPS_API_KEY
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(directions_url, params=params) as response:
                    route_data = await response.json()
            
            if route_data['status'] != 'OK':
                return ActionResult(
                    success=False,
                    error=f"Route calculation failed: {route_data.get('status')}"
                )
            
            route = route_data['routes'][0]
            leg = route['legs'][0]
            
            result_data = {
                'origin': leg['start_address'],
                'destination': leg['end_address'],
                'distance': leg['distance']['text'],
                'distance_meters': leg['distance']['value'],
                'duration': leg['duration']['text'],
                'duration_seconds': leg['duration']['value'],
                'mode': mode,
                'steps': [
                    {
                        'instruction': step['html_instructions'],
                        'distance': step['distance']['text'],
                        'duration': step['duration']['text']
                    }
                    for step in leg['steps'][:5]  # First 5 steps
                ]
            }
            
            return ActionResult(
                success=True,
                data=result_data,
                metadata={
                    "total_steps": len(leg['steps']),
                    "api": "google_directions"
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating route: {e}")
            return ActionResult(
                success=False,
                error=f"Failed to calculate route: {str(e)}"
            )


# Additional utility plugins can be added here...