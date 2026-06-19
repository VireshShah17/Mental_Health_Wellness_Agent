# Import the required libraries
import json
import logging

# Configure logging to INFO level by default
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S')


def get_weather_for_date(target_date, json_file_path):
    """
        Reads the synthetic Open-Meteo JSON and returns the weather condition.
    """

    try:
        with open(json_file_path, "r") as file:
            weather_data = json.load(file)
            
        # Loop through the historical data to find a date match
        for record in weather_data.get('historical_weather', []):
            if record.get('date') == target_date:
                return record.get('condition')
        
        logging.warning(f"===== No weather data found for date: {target_date} =====")

        return "Unknown"
    
    except FileNotFoundError:
        logging.error(f"===== Weather data file '{json_file_path}' not found! =====")

        return "Error"
    except json.JSONDecodeError:
        logging.error(f"===== Failed to parse JSON in '{json_file_path}'. =====")

        return "Error"



