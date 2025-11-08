import concurrent.futures
from typing import List, Dict
from stores.u import get_price_u
from stores.carrefour import get_price_carrefour
from stores.aldi import get_price_aldi
from stores.monoprix import get_price_monoprix


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


def main(articles: List[Dict], store: str, city: str = "Le port-marly", max_workers: int = 2) -> List[Dict]:
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