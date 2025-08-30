import requests
import json
from django.conf import settings


class GeocodingService:
    """
    Geocoding service to get coordinates from location names.
    Uses OpenStreetMap Nominatim API (free and no API key required)
    """
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'EcoValidate/1.0 (Environmental Analysis App)'
        }
    
    def get_coordinates(self, location):
        """
        Get latitude and longitude for a given location string.
        
        Args:
            location (str): Location name (e.g., "Amazon Rainforest, Brazil")
            
        Returns:
            dict: {'latitude': float, 'longitude': float, 'display_name': str} or None if not found
        """
        try:
            params = {
                'q': location,
                'format': 'json',
                'addressdetails': 1,
                'limit': 1,
                'dedupe': 1
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    return {
                        'latitude': float(result['lat']),
                        'longitude': float(result['lon']),
                        'display_name': result.get('display_name', location),
                        'place_id': result.get('place_id'),
                        'osm_type': result.get('osm_type'),
                        'class': result.get('class'),
                        'type': result.get('type')
                    }
            
            return None
            
        except requests.RequestException as e:
            print(f"Geocoding request failed: {e}")
            return None
        except (ValueError, KeyError, IndexError) as e:
            print(f"Error parsing geocoding response: {e}")
            return None
    
    def reverse_geocode(self, latitude, longitude):
        """
        Get location name from coordinates (reverse geocoding).
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            dict: Location information or None if not found
        """
        try:
            reverse_url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1
            }
            
            response = requests.get(
                reverse_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        'display_name': data.get('display_name'),
                        'address': data.get('address', {}),
                        'place_id': data.get('place_id')
                    }
            
            return None
            
        except requests.RequestException as e:
            print(f"Reverse geocoding request failed: {e}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Error parsing reverse geocoding response: {e}")
            return None


# Global instance
geocoding_service = GeocodingService()
