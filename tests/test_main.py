"""
Tests unitaires pour l'API FastAPI du comparateur de prix
Compatible avec pytest pour la CI/CD
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test de l'endpoint racine"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data
    assert "supported_stores" in data
    assert "workers_configuration" in data

def test_price_estimation_valid_store():
    """Test de l'endpoint /price_estimation avec un magasin valide"""
    data = {
        "item": {
            "name": "lait",
            "brand": "lactel",
            "quantity": "1L"
        },
        "store": "monoprix",
        "city": "Le port-marly"
    }
    
    response = client.post("/price_estimation", json=data)
    # Le test peut réussir (200) ou échouer (404) selon la disponibilité du scraping
    assert response.status_code in [200, 404, 500]

def test_price_estimation_invalid_store():
    """Test de l'endpoint /price_estimation avec un magasin invalide"""
    data = {
        "item": {
            "name": "lait",
            "brand": "lactel",
            "quantity": "1L"
        },
        "store": "magasin_inexistant",
        "city": "Le port-marly"
    }
    
    response = client.post("/price_estimation", json=data)
    assert response.status_code == 400
    assert "Magasin non supporté" in response.json()["detail"]

def test_price_estimation_missing_item_name():
    """Test de l'endpoint /price_estimation sans nom d'article"""
    data = {
        "item": {
            "brand": "lactel",
            "quantity": "1L"
        },
        "store": "monoprix",
        "city": "Le port-marly"
    }
    
    response = client.post("/price_estimation", json=data)
    assert response.status_code == 422  # Validation error

def test_list_price_estimation_valid_store():
    """Test de l'endpoint /list_price_estimation avec un magasin valide"""
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
            }
        ],
        "store": "carrefour",
        "city": "Le port-marly"
    }
    
    response = client.post("/list_price_estimation", json=data)
    # Le test peut réussir (200) ou échouer (500) selon la disponibilité du scraping
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "total_items" in data
        assert "successful_searches" in data
        assert "failed_searches" in data
        assert "results" in data

def test_list_price_estimation_invalid_store():
    """Test de l'endpoint /list_price_estimation avec un magasin invalide"""
    data = {
        "items": [
            {
                "name": "lait",
                "brand": "lactel",
                "quantity": "1L"
            }
        ],
        "store": "magasin_inexistant",
        "city": "Le port-marly"
    }
    
    response = client.post("/list_price_estimation", json=data)
    assert response.status_code == 400
    assert "Magasin non supporté" in response.json()["detail"]

def test_list_price_estimation_empty_items():
    """Test de l'endpoint /list_price_estimation avec une liste vide"""
    data = {
        "items": [],
        "store": "carrefour",
        "city": "Le port-marly"
    }
    
    response = client.post("/list_price_estimation", json=data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 0

def test_supported_stores():
    """Test que tous les magasins supportés sont accessibles"""
    supported_stores = ["u", "carrefour", "aldi", "monoprix"]
    
    for store in supported_stores:
        data = {
            "item": {
                "name": "test",
                "brand": "",
                "quantity": ""
            },
            "store": store,
            "city": "Le port-marly"
        }
        
        response = client.post("/price_estimation", json=data)
        # Le magasin doit être reconnu (pas d'erreur 400)
        assert response.status_code != 400

if __name__ == "__main__":
    pytest.main([__file__, "-v"])