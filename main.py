import concurrent.futures
from typing import List, Dict, Optional
import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Charger les variables d'environnement depuis .env si le fichier existe (développement local)
def load_env_file():
    """Charge le fichier .env en développement local"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key not in os.environ:  # Ne pas écraser les variables système
                        os.environ[key] = value
        print("Variables d'environnement chargées depuis .env (développement)")
    except FileNotFoundError:
        print("Aucun fichier .env trouvé (probablement en production)")
    except Exception as e:
        print(f"Erreur lors du chargement de .env: {e}")

# Charger la configuration
load_env_file()

from stores.u import get_price_u
from stores.carrefour import get_price_carrefour
from stores.aldi import get_price_aldi
from stores.monoprix import get_price_monoprix

from geolocation.find_supermarches import find_supermarkets, find_supermarkets_gcp

app = FastAPI(
    title="Comparateur de Prix API",
    description="API pour comparer les prix d'articles dans différents supermarchés",
    version="1.0.0"
)


WORKERS = {
    "u": 3,
    "carrefour": 6,
    "aldi": 10,
    "monoprix": 10
}

class Item(BaseModel):
    name: str
    brand: Optional[str] = ""
    quantity: Optional[str] = ""

class PriceEstimationRequest(BaseModel):
    item: Item
    store: str
    city: Optional[str] = "Le port-marly"

class ListPriceEstimationRequest(BaseModel):
    items: List[Item]
    store: str
    city: Optional[str] = "Le port-marly"

class ClosestStoreRequest(BaseModel):
    adress:str
    max_distance_km: Optional[float] = 5.0

class ClosestStoreGroceries(BaseModel):
    adress: str
    max_distance_km: Optional[float] = 5.0
    items: List[Item]


def search_single_item(store: str, city: str, item: Dict) -> Dict:
    """Recherche le prix d'un seul article dans un magasin donné"""
    try:
        if store.lower() == "u":
            #highest_price, lowest_price, success = get_price_u(city, item)
            highest_price, lowest_price, success = 0, 0, False
        elif store.lower() == "carrefour":
            highest_price, lowest_price, success = get_price_carrefour(city, item)
        elif store.lower() == "aldi":
            highest_price, lowest_price, success = get_price_aldi(city, item)
        elif store.lower() == "monoprix":
            highest_price, lowest_price, success = get_price_monoprix(city, item)
        else:
            return {"item": item, "store": store, "success": False, "error": f"Magasin non supporté: {store}"}
        
        if success:
            return {"item": item, "store": store, "success": True, "highest_price": highest_price, "lowest_price": lowest_price}
        else:
            return {"item": item, "store": store, "success": False, "error": "Aucun produit trouvé"}
    
    except Exception as e:
        return {"item": item, "store": store, "success": False, "error": str(e)}


### ENDPOINTS DE L'API ###

@app.get("/health")
async def health():
    """Endpoint de santé avec diagnostic des configurations"""
    google_api_configured = bool(os.getenv('GOOGLE_MAPS_API_KEY'))
    environment = os.getenv('ENVIRONMENT', 'development')
    
    return {
        "status": "healthy",
        "environment": environment,
        "google_maps_api_configured": google_api_configured,
        "supported_stores": list(WORKERS.keys()),
        "workers_configuration": WORKERS
    }


@app.get("/")
async def root():
    """Endpoint racine avec informations sur l'API"""
    return {
        "message": "Bienvenue sur l'API Comparateur de Prix",
        "endpoints": {
            "/price_estimation": "Estimation de prix pour un seul article",
            "/list_price_estimation": "Estimation de prix pour une liste d'articles"
        },
        "supported_stores": list(WORKERS.keys()),
        "workers_configuration": WORKERS
    }


### RECUPERER LE PRIX D'UN SEUL ARTICLE ###

@app.post("/price_estimation")
async def price_estimation(request: PriceEstimationRequest):
    """
    Endpoint pour obtenir l'estimation de prix d'un seul article
    
    Args:
        request: Contient l'article, le magasin et la ville
    
    Returns:
        Résultat de la recherche de prix
    """
    try:
        # Vérifier que le magasin est supporté
        if request.store.lower() not in WORKERS:
            raise HTTPException(status_code=400, detail=f"Magasin non supporté: {request.store}")
        
        # Convertir l'item Pydantic en dictionnaire
        item_dict = {
            "name": request.item.name,
            "brand": request.item.brand or "",
            "quantity": request.item.quantity or ""
        }
        
        # Exécuter la recherche dans un thread séparé pour éviter les conflits asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            search_single_item, 
            request.store, 
            request.city, 
            item_dict
        )
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Article non trouvé"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


### RECUPERER LE PRIX D'UNE LISTE D'ARTICLES ###

@app.post("/list_price_estimation")
async def list_price_estimation(request: ListPriceEstimationRequest):
    """
    Endpoint pour obtenir l'estimation de prix d'une liste d'articles
    
    Args:
        request: Contient la liste d'articles, le magasin et la ville
    
    Returns:
        Liste des résultats de recherche de prix
    """
    try:
        # Vérifier que le magasin est supporté
        if request.store.lower() not in WORKERS:
            raise HTTPException(status_code=400, detail=f"Magasin non supporté: {request.store}")
        
        # Obtenir le nombre de workers pour ce magasin
        max_workers = WORKERS[request.store.lower()]
        
        # Convertir les items Pydantic en dictionnaires
        items_dict = [
            {
                "name": item.name,
                "brand": item.brand or "",
                "quantity": item.quantity or ""
            }
            for item in request.items
        ]
        
        # Exécuter la recherche dans un thread séparé pour éviter les conflits asyncio
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            process_items_list,
            items_dict,
            request.store,
            request.city,
            max_workers
        )
        
        return {
            "total_items": len(results),
            "rate_success": (len([r for r in results if r["success"]]) / len(results)) * 100,
            "min_price": sum(r["lowest_price"] for r in results if r["success"]),
            "max_price": sum(r["highest_price"] for r in results if r["success"]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


def process_items_list(articles: List[Dict], store: str, city: str = "Le port-marly", max_workers: int = 2) -> List[Dict]:
    """
    Traite une liste d'articles avec multithreading
    
    Args:
        articles: Liste d'articles [{"name": "...", "brand": "...", "quantity": "..."}]
        store: "carrefour", "u", "aldi" ou "monoprix"
        city: Nom de la ville
        max_workers: Nombre maximum de threads
    
    Returns:
        Liste des résultats
    """
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(search_single_item, store, city, item): item for item in articles}
        
        for future in concurrent.futures.as_completed(future_to_item):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                item = future_to_item[future]
                results.append({"item": item, "store": store, "success": False, "error": str(exc)})
    
    return results



### RECUPERER TOUS LES SUPERMARCHES PROCHES ###

@app.post("/closest_stores")
async def closest_stores(request: ClosestStoreRequest):
    """
    Endpoint pour obtenir les supermarchés proches d'une adresse donnée
    
    Args:
        request: Contient l'adresse et la distance maximale en km
    
    Returns:
        Liste des supermarchés proches
    """
    try:
        # Essayer d'abord Google Maps, fallback sur Overpass si erreur
        try:
            stores = find_supermarkets_gcp(request.adress, request.max_distance_km)
            api_used = "Google Maps"
        except Exception as gcp_error:
            print(f"Google Maps API indisponible: {gcp_error}")
            stores = find_supermarkets(request.adress, request.max_distance_km)
            api_used = "Overpass"
            
        stores = stores.to_dict(orient="records")
        return {
            "address": request.adress,
            "max_distance_km": request.max_distance_km,
            "found_stores": len(stores),
            "api_used": api_used,
            "stores": stores
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


def process_single_store(store, items_list):
    """
    Traite un seul magasin et retourne ses résultats
    """
    store_name = store.get("name", "").lower()
    
    # Chercher si l'un des mots du nom du magasin correspond à une clé dans WORKERS
    matched_store = None
    for word in store_name.split():
        if word in WORKERS:
            matched_store = word
            break
    
    if not matched_store:
        return {
            "store": store,
            "success_rate": 0,
            "min_price": 0,
            "max_price": 0,
            "error": "Magasin non supporté"
        }
    
    try:
        max_workers = WORKERS[matched_store]
        store_results = process_items_list(items_list, matched_store, store.get("address", ""), max_workers)
        
        successful = sum(1 for r in store_results if r.get("success", False))
        total = len(store_results)
        
        return {
            "store": store,
            "success_rate": (successful / total) * 100 if total > 0 else 0,
            "min_price": sum(r["lowest_price"] for r in store_results if r["success"]),
            "max_price": sum(r["highest_price"] for r in store_results if r["success"]),
        }
    except Exception as e:
        return {
            "store": store,
            "success_rate": 0,
            "min_price": 0,
            "max_price": 0,
            "error": str(e)
        }


### ENDPOINT QUI PREND UNE LISTE, UNE ADRESSE, UN RAYON EN KM ET RETOURNE CHAQUE SUPERMARCHÉ PROCHE AVEC LE HIGHEST PRICE, LOWEST PRICE ET SUCCESS RATE
@app.post("/closest_store_groceries")
async def closest_store_groceries(request: ClosestStoreGroceries):
    """
    Endpoint pour obtenir les supermarchés proches d'une adresse donnée avec les prix des articles
    
    Args:
        request: Contient l'adresse, la distance maximale en km et la liste d'articles
    
    Returns:
        Liste des supermarchés proches avec les prix des articles
    """
    try:
        # Essayer d'abord Google Maps, fallback sur Overpass si erreur
        try:
            stores = find_supermarkets_gcp(request.adress, request.max_distance_km)
            api_used = "Google Maps"
        except Exception as gcp_error:
            print(f"Google Maps API indisponible: {gcp_error}")
            stores = find_supermarkets(request.adress, request.max_distance_km)
            api_used = "Overpass"
        
            
        stores = stores.to_dict(orient="records")
        
        # Convertir les items une seule fois
        items_dict = [
            {
                "name": item.name,
                "brand": item.brand or "",
                "quantity": item.quantity or ""
            }
            for item in request.items
        ]
        
        # PARALLÉLISATION : Traiter tous les magasins en parallèle
        loop = asyncio.get_event_loop()
        
        # Exécuter en parallèle
        tasks = [
            loop.run_in_executor(None, process_single_store, store, items_dict)
            for store in stores
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            "address": request.adress,
            "max_distance_km": request.max_distance_km,
            "stores_processed": len(results),
            "api_used": api_used,
            "stores_with_prices": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)