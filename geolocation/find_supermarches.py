import requests
from geopy.geocoders import Nominatim
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def find_supermarkets_gcp(latitude, longitude, radius_km=5):
    """
    Trouve les supermarchés autour de coordonnées données en utilisant Google Places API.
    Beaucoup plus rapide et fiable qu'Overpass.
    
    Args:
        latitude: Latitude du point de recherche
        longitude: Longitude du point de recherche
        radius_km: Rayon de recherche en kilomètres
    
    Nécessite une clé API Google Maps avec Places API activée.
    Définir la variable d'environnement GOOGLE_MAPS_API_KEY.
    """
    # Vérifier la clé API
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY non définie. Obtenez une clé sur https://console.cloud.google.com/")
    
    # Validation des coordonnées
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Latitude invalide: {latitude}. Doit être entre -90 et 90.")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Longitude invalide: {longitude}. Doit être entre -180 et 180.")
    
    # Rechercher les supermarchés avec Places API Nearby Search
    places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    radius_m = radius_km * 1000
    
    supermarkets = []
    
    # Types de lieux à rechercher
    place_types = ['supermarket', 'grocery_or_supermarket']
    
    for place_type in place_types:
        places_params = {
            'location': f"{latitude},{longitude}",
            'radius': radius_m,
            'type': place_type,
            'key': api_key,
            'language': 'fr'
        }
        
        try:
            places_response = requests.get(places_url, params=places_params, timeout=10)
            places_response.raise_for_status()
            places_data = places_response.json()
            
            if places_data['status'] not in ['OK', 'ZERO_RESULTS']:
                continue
                
            # Traiter les résultats
            for place in places_data.get('results', []):
                name = place.get('name', 'Inconnu')
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                is_opened = place.get('opening_hours', {}).get('open_now', None)
                
                # Extraire l'adresse formatée
                vicinity = place.get('vicinity', '')
                
                # Identifier la marque/enseigne à partir du nom
                brand = ""
                name_lower = name.lower()
                
                # Mapping des enseignes courantes
                brand_mapping = {
                    'carrefour': 'carrefour',
                    'monoprix': 'monoprix', 
                    'aldi': 'aldi',
                    'super u': 'u',
                    'hyper u': 'u',
                    'marché u': 'u',
                    'leclerc': 'leclerc',
                    'intermarché': 'intermarché',
                    'casino': 'casino',
                    'franprix': 'franprix',
                    'picard': 'picard'
                }
                
                for key, value in brand_mapping.items():
                    if key in name_lower:
                        brand = value
                        break
                
                supermarkets.append({
                    "name": name,
                    "brand": brand,
                    "latitude": place_lat,
                    "longitude": place_lng,
                    "address": vicinity,
                    "is_opened": is_opened
                })
                
        except Exception as e:
            continue  # Continuer avec le type suivant si erreur
    
    # Supprimer les doublons basés sur le nom et la position
    df = pd.DataFrame(supermarkets)
    if not df.empty:
        df = df.drop_duplicates(subset=['name', 'latitude', 'longitude'])
        df = df.reset_index(drop=True)
    
    return df


def find_supermarkets(latitude, longitude, radius_km=5):
    """
    Trouve les supermarchés et drives autour de coordonnées données avec Overpass.
    
    Args:
        latitude: Latitude du point de recherche
        longitude: Longitude du point de recherche
        radius_km: Rayon de recherche en kilomètres
    """
    # 1. Validation des coordonnées
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Latitude invalide: {latitude}. Doit être entre -90 et 90.")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Longitude invalide: {longitude}. Doit être entre -180 et 180.")

    # 2. Construire la requête Overpass (OpenStreetMap)
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["shop"="supermarket"](around:{radius_km * 1000},{latitude},{longitude});
      node["shop"="convenience"](around:{radius_km * 1000},{latitude},{longitude});
      node["drive_through"="yes"](around:{radius_km * 1000},{latitude},{longitude});
    );
    out body;
    """
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = requests.get(overpass_url, params={'data': query}, timeout=30)
            
            if response.status_code == 200:
                if not response.text.strip():
                    raise ValueError("Réponse vide de l'API Overpass")
                data = response.json()
                break
                
            elif response.status_code == 504:  
                if attempt < max_retries - 1:
                    continue
                else:
                    raise ValueError(f"API Overpass indisponible après {max_retries} tentatives (504)")
            
            else:
                raise ValueError(f"Erreur API Overpass: status {response.status_code}")
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue
            else:
                raise ValueError(f"Timeout après {max_retries} tentatives")
                
        except requests.exceptions.JSONDecodeError as e:
            if attempt < max_retries - 1:
                continue
            else:
                raise ValueError(f"Réponse invalide après {max_retries} tentatives")
                
        except Exception as e:
            if attempt < max_retries - 1:
                continue
            else:
                raise

    # 4. Extraire les résultats
    supermarkets = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name", "Inconnu")
        brand = tags.get("brand", "")
        addr = ", ".join(
            filter(None, [
                tags.get("addr:street"),
                tags.get("addr:postcode"),
                tags.get("addr:city")
            ])
        )
        supermarkets.append({
            "name": name,
            "brand": brand,
            "latitude": element["lat"],
            "longitude": element["lon"],
            "address": addr
        })

    df = pd.DataFrame(supermarkets)
    return df

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    # Coordonnées de Marly le Roi
    lat, lon = 48.8671, 2.0935
    
    print("=== Test avec Google Maps API ===")
    try:
        resultats_gcp = find_supermarkets_gcp(lat, lon, radius_km=2)
        print("Résultats Google Maps :")
        print(resultats_gcp)
        print(f"Trouvé {len(resultats_gcp)} magasins")
    except Exception as e:
        print(f"Erreur Google Maps: {e}")
    
    print("\n=== Test avec Overpass API ===")
    try:
        resultats_overpass = find_supermarkets(lat, lon, radius_km=2)
        print("Résultats Overpass :")
        print(resultats_overpass)
        print(f"Trouvé {len(resultats_overpass)} magasins")
    except Exception as e:
        print(f"Erreur Overpass: {e}")
