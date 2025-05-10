import requests
import json
import logging

logger = logging.getLogger(__name__)

# API key for OpenWeatherMap (this is a placeholder - user should replace with their own key)
API_KEY = "YOUR_API_KEY_HERE"

def get_weather(location: str) -> str:
    """
    Fetches current weather information for a specified location.
    
    Args:
        location: City name or city,country code (e.g., "London" or "London,UK")
        
    Returns:
        str: Formatted weather information or error message
    """
    try:
        # Check if API key has been set
        if API_KEY == "YOUR_API_KEY_HERE":
            return "Please set your OpenWeatherMap API key in the Weather_Info.py file."
        
        # Build the API URL
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"
        
        # Make the API request
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Extract relevant information
            city_name = data['name']
            country = data['sys']['country']
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            
            # Format the response
            weather_info = f"""
Weather for {city_name}, {country}:
- Condition: {weather_desc.capitalize()}
- Temperature: {temp}°C (feels like {feels_like}°C)
- Humidity: {humidity}%
- Wind Speed: {wind_speed} m/s
            """
            
            return weather_info.strip()
        elif response.status_code == 401:
            return "Invalid API key. Please check your OpenWeatherMap API key."
        elif response.status_code == 404:
            return f"Location '{location}' not found. Please check the spelling or try a different location."
        else:
            return f"Error fetching weather data: HTTP {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return "Connection error. Please check your internet connection."
    except Exception as e:
        logger.error(f"Error in get_weather: {str(e)}")
        return f"Error fetching weather data: {str(e)}"

if __name__ == "__main__":
    # Test the function
    print(get_weather("London,UK"))
