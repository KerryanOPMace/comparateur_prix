import concurrent.futures
from typing import List, Dict, Optional
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from stores.u import get_price_u
from stores.carrefour import get_price_carrefour
from stores.aldi import get_price_aldi
from stores.monoprix import get_price_monoprix

app = FastAPI(
    title="Comparateur de Prix API",
    description="API pour comparer les prix d'articles dans différents supermarchés",
    version="1.0.0"
)


WORKERS = {
    "u": 2,
    "carrefour": 4,
    "aldi": 8,
    "monoprix": 8
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


def search_single_item(store: str, city: str, item: Dict) -> Dict:
    """Recherche le prix d'un seul article dans un magasin donné"""
    try:
        if store.lower() == "u":
            highest_price, lowest_price, success = get_price_u(city, item)
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
            "successful_searches": len([r for r in results if r["success"]]),
            "failed_searches": len([r for r in results if not r["success"]]),
            "max_workers_used": max_workers,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)