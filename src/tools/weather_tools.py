"""
Weather Tools for ReAct Agent
These are mock tools for demonstration
"""

import json
from datetime import datetime, timedelta

# Mock weather database
WEATHER_DATA = {
    "Hanoi": {
        "current": {"temp": 25, "condition": "cloudy", "humidity": 70, "wind": 12},
        "forecast": [
            {"date": "2026-06-02", "temp": 26, "condition": "sunny", "rain_chance": 10},
            {"date": "2026-06-03", "temp": 24, "condition": "rainy", "rain_chance": 80},
            {"date": "2026-06-04", "temp": 23, "condition": "cloudy", "rain_chance": 30},
        ]
    },
    "Ho Chi Minh City": {
        "current": {"temp": 32, "condition": "sunny", "humidity": 65, "wind": 8},
        "forecast": [
            {"date": "2026-06-02", "temp": 33, "condition": "sunny", "rain_chance": 5},
            {"date": "2026-06-03", "temp": 32, "condition": "sunny", "rain_chance": 10},
            {"date": "2026-06-04", "temp": 31, "condition": "cloudy", "rain_chance": 20},
        ]
    },
    "Da Nang": {
        "current": {"temp": 28, "condition": "rainy", "humidity": 85, "wind": 15},
        "forecast": [
            {"date": "2026-06-02", "temp": 27, "condition": "rainy", "rain_chance": 90},
            {"date": "2026-06-03", "temp": 28, "condition": "cloudy", "rain_chance": 40},
            {"date": "2026-06-04", "temp": 29, "condition": "sunny", "rain_chance": 5},
        ]
    }
}

def get_current_weather(city: str) -> str:
    """
    Get current weather for a city.
    
    Args:
        city: Name of the city (Hanoi, Ho Chi Minh City, Da Nang)
    
    Returns:
        JSON string with temperature, condition, humidity, wind speed
    """
    # Normalize city name
    city_map = {
        "hanoi": "Hanoi",
        "ha noi": "Hanoi",
        "ho chi minh": "Ho Chi Minh City",
        "ho chi minh city": "Ho Chi Minh City",
        "hcm": "Ho Chi Minh City",
        "da nang": "Da Nang",
        "danang": "Da Nang"
    }
    
    normalized = city_map.get(city.lower(), city)
    
    if normalized not in WEATHER_DATA:
        return json.dumps({"error": f"No weather data available for {city}"})
    
    weather = WEATHER_DATA[normalized]["current"]
    
    # Trả về JSON string an toàn
    return json.dumps({
        "city": normalized,
        "temperature_c": weather["temp"],
        "condition": weather["condition"],
        "humidity_percent": weather["humidity"],
        "wind_speed_kph": weather["wind"]
    })

def get_weather_forecast(city: str, days: int = 1) -> str:
    """
    Get weather forecast for a city.
    
    Args:
        city: Name of the city (Hanoi, Ho Chi Minh City, Da Nang)
        days: Number of days to forecast (1-3)
    
    Returns:
        JSON string with forecast data
    """
    # Normalize city name
    city_map = {
        "hanoi": "Hanoi",
        "ha noi": "Hanoi",
        "ho chi minh": "Ho Chi Minh City",
        "ho chi minh city": "Ho Chi Minh City",
        "hcm": "Ho Chi Minh City",
        "da nang": "Da Nang",
        "danang": "Da Nang"
    }
    
    normalized = city_map.get(city.lower(), city)
    
    if normalized not in WEATHER_DATA:
        return json.dumps({"error": f"No weather data available for {city}"})
    
    days = min(days, 3)  # Limit to 3 days
    forecast = WEATHER_DATA[normalized]["forecast"][:days]
    
    return json.dumps({
        "city": normalized,
        "forecast": forecast
    })

def compare_weather(city1: str, city2: str) -> str:
    """
    Compare weather between two cities.
    
    Args:
        city1: First city name
        city2: Second city name
    
    Returns:
        Comparison string
    """
    weather1 = get_current_weather(city1)
    weather2 = get_current_weather(city2)
    
    data1 = json.loads(weather1)
    data2 = json.loads(weather2)
    
    if "error" in data1 or "error" in data2:
        return "Could not compare: one or both cities not found"
    
    temp1 = data1["temperature_c"]
    temp2 = data2["temperature_c"]
    
    diff = abs(temp1 - temp2)
    warmer = city1 if temp1 > temp2 else city2
    
    # Trả về string thường, không dùng f-string với JSON
    result = f"{city1}: {temp1}°C, {data1['condition']}. {city2}: {temp2}°C, {data2['condition']}. {warmer} is warmer by {diff}°C."
    return result

def get_clothing_advice(temperature: int, condition: str) -> str:
    """
    Get clothing advice based on weather.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition (sunny, rainy, cloudy, etc.)
    
    Returns:
        Clothing advice string
    """
    advice = ""
    
    if temperature >= 30:
        advice = "It's hot! Wear light clothing like shorts and t-shirt."
    elif temperature >= 20:
        advice = "Pleasant weather. Jeans and a t-shirt would work."
    else:
        advice = "It's cool. Bring a jacket or sweater."
    
    if condition == "rainy":
        advice += " Don't forget an umbrella and raincoat!"
    elif condition == "sunny":
        advice += " Use sunscreen and wear a hat."
    
    return advice

# Tool definitions for the agent
WEATHER_TOOLS = [
    {
        "name": "get_current_weather",
        "description": "Get current weather for a city. Returns temperature, condition, humidity, wind speed.",
        "function": get_current_weather,
        "input_schema": {
            "city": "string - City name (Hanoi, Ho Chi Minh City, Da Nang)"
        }
    },
    {
        "name": "get_weather_forecast",
        "description": "Get weather forecast for a city for the next few days.",
        "function": get_weather_forecast,
        "input_schema": {
            "city": "string - City name",
            "days": "integer - Number of days (1-3)"
        }
    },
    {
        "name": "compare_weather",
        "description": "Compare weather between two cities.",
        "function": compare_weather,
        "input_schema": {
            "city1": "string - First city name",
            "city2": "string - Second city name"
        }
    },
    {
        "name": "get_clothing_advice",
        "description": "Get clothing advice based on temperature and weather condition.",
        "function": get_clothing_advice,
        "input_schema": {
            "temperature": "integer - Temperature in Celsius",
            "condition": "string - Weather condition"
        }
    }
]