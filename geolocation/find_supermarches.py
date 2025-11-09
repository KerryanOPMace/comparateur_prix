import requests
from geopy.geocoders import Nominatim
import pandas as pd

def find_supermarkets(address, radius_km=5):
    """
    Trouve les supermarchés et drives autour d'une adresse donnée.
    """
    # 1. Géocoder l’adresse
    geolocator = Nominatim(user_agent="drive_finder")
    location = geolocator.geocode(address)
    if not location:
        raise ValueError(f"Adresse introuvable : {address}")

    lat, lon = location.latitude, location.longitude

    # 2. Construire la requête Overpass (OpenStreetMap)
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["shop"="supermarket"](around:{radius_km * 1000},{lat},{lon});
      node["shop"="convenience"](around:{radius_km * 1000},{lat},{lon});
      node["drive_through"="yes"](around:{radius_km * 1000},{lat},{lon});
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
    adresse = "Marly le roi"
    resultats = find_supermarkets(adresse, radius_km=2)
    print(resultats)
