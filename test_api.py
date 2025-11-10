"""
Script de test pour l'API FastAPI du comparateur de prix
"""
import requests
import json

# BASE_URL = "https://pricecomparing-1062149715485.europe-west9.run.app"
BASE_URL = "http://localhost:8080"

def test_root():
    """Test de l'endpoint racine"""
    response = requests.get(f"{BASE_URL}/")
    print("=== Test endpoint racine ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_single_item():
    """Test de l'endpoint /price_estimation"""
    data = {
        "item": {
            "name": "lait",
            "brand": "lactel",
            "quantity": "1L"
        },
        "store": "monoprix",
        "city": "Le port-marly"
    }
    
    print("=== Test /price_estimation ===")
    print(f"Données envoyées: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{BASE_URL}/price_estimation", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_multiple_items():
    """Test de l'endpoint /list_price_estimation"""
    data = {
        "items": [
            {
                "name": "lait",
                "brand": "lactel",
                "quantity": "1L"
            },
            {
                "name": "pain",
                "brand": "",
                "quantity": "400g"
            },
            {
                "name": "miel pops",
                "brand": "",
                "quantity": "500g"
            }
        ],
        "store": "carrefour",
        "city": "Le port-marly"
    }
    
    print("=== Test /list_price_estimation ===")
    print(f"Données envoyées: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{BASE_URL}/list_price_estimation", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()



def test_closest_stores():
    """Test de l'endpoint /closest_stores"""
    data = {
        "adress": "Marly le roi",
        "max_distance_km": 2.0
    }
    
    print("=== Test /closest_stores ===")
    print(f"Données envoyées: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{BASE_URL}/closest_stores", json=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_closest_store_groceries():
    """Test de l'endpoint /closest_store_groceries"""
    data = {
        "adress": "Marly le Roi",
        "max_distance_km": 2.0,
        "items": [
            {
                "name": "lait",
                "brand": "lactel",
                "quantity": "1L"
            },
            {
                "name": "pain",
                "brand": "",
                "quantity": "400g"
            }
        ]
    }
    
    print("=== Test /closest_store_groceries ===")
    print(f"Données envoyées: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{BASE_URL}/closest_store_groceries", json=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

if __name__ == "__main__":
    print("Démarrage des tests de l'API...")
    print("Assurez-vous que l'API est lancée avec: python main.py")
    print()
    
    try:
        test_root()
        test_single_item()
        test_multiple_items()
        #test_closest_stores()
        #test_closest_store_groceries()
    except requests.exceptions.ConnectionError:
        print("Erreur: Impossible de se connecter à l'API. Assurez-vous qu'elle est lancée.")
    except Exception as e:
        print(f"Erreur: {e}")