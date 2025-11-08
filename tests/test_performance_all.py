import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import concurrent.futures
from typing import List, Dict
from main import search_single_item


def test_store_performance(store: str, city: str, articles: List[Dict], max_workers: int) -> Dict:
    """
    Teste les performances d'un magasin avec un nombre donné de workers
    """
    print(f"🧪 Test {store.upper()} avec {max_workers} worker(s)")
    
    start_time = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(search_single_item, store, city, item): item 
            for item in articles
        }
        
        for future in concurrent.futures.as_completed(future_to_item):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                item = future_to_item[future]
                results.append({
                    "item": item, 
                    "store": store, 
                    "success": False, 
                    "error": str(exc)
                })
    
    end_time = time.time()
    duration = end_time - start_time
    successful = sum(1 for r in results if r.get("success", False))
    
    print(f"   ⏱️  Temps: {duration:.2f}s")
    print(f"   ✅ Succès: {successful}/{len(articles)}")
    print(f"   📊 Taux: {(successful/len(articles)*100):.1f}%")
    print()
    
    return {
        "store": store,
        "workers": max_workers,
        "duration": duration,
        "successful": successful,
        "total": len(articles),
        "success_rate": successful/len(articles)*100
    }


def run_performance_tests():
    """Lance tous les tests de performance"""
    
    # Liste d'articles pour les tests (assez longue)
    test_articles = [
        {"name": "Spaghetti", "brand": "Barilla", "quantity": "500g"},
        {"name": "Yaourt", "brand": "Danone", "quantity": "4x125g"},
        {"name": "Pain de mie", "brand": "", "quantity": ""},
        {"name": "Lait", "brand": "", "quantity": "1L"},
        {"name": "Oeufs", "brand": "", "quantity": "x6"},
        {"name": "Riz", "brand": "Uncle Ben's", "quantity": "1kg"},
        {"name": "Huile d'olive", "brand": "", "quantity": "750ml"},
        {"name": "Fromage", "brand": "Président", "quantity": ""},
        {"name": "Biscuits", "brand": "LU", "quantity": ""},
        {"name": "Céréales", "brand": "Kellogg's", "quantity": ""},
        {"name": "Chocolat", "brand": "Milka", "quantity": "100g"},
        {"name": "Café", "brand": "Nescafé", "quantity": ""},
        {"name": "Thé", "brand": "Lipton", "quantity": ""},
        {"name": "Sucre", "brand": "", "quantity": "1kg"},
        {"name": "Farine", "brand": "", "quantity": "1kg"},
        {"name": "Pommes", "brand": "", "quantity": "1kg"},
        {"name": "Bananes", "brand": "", "quantity": "1kg"},
        {"name": "Tomates", "brand": "", "quantity": "1kg"},
        {"name": "Salade", "brand": "", "quantity": ""},
        {"name": "Carottes", "brand": "", "quantity": "1kg"}
    ]
    
    # Configuration des tests
    stores = [
        
        {"name": "carrefour", "city": "Marly-le-roi"},
    ]
    
    worker_counts = [4]
    
    print("🚀 TESTS DE PERFORMANCE - COMPARATEUR DE PRIX")
    print("=" * 60)
    print(f"📋 {len(test_articles)} articles à tester")
    print(f"🏪 {len(stores)} magasins")
    print(f"🔧 {len(worker_counts)} configurations de workers")
    print("=" * 60)
    print()
    
    all_results = []
    
    # Tests pour chaque magasin et configuration
    for store_config in stores:
        store_name = store_config["name"]
        city = store_config["city"]
        
        print(f"🏪 TESTS POUR {store_name.upper()}")
        print("-" * 40)
        
        store_results = []
        
        for workers in worker_counts:
            try:
                result = test_store_performance(store_name, city, test_articles, workers)
                store_results.append(result)
                all_results.append(result)
            except Exception as e:
                print(f"   ❌ Erreur avec {workers} worker(s): {e}")
                print()
        
        # Résumé pour ce magasin
        if store_results:
            print(f"📊 RÉSUMÉ {store_name.upper()}:")
            print("   Workers | Temps  | Succès | Taux")
            print("   --------|--------|--------|------")
            for r in store_results:
                print(f"   {r['workers']:7} | {r['duration']:6.1f}s | {r['successful']:2}/{r['total']:2}    | {r['success_rate']:5.1f}%")
            
            # Meilleure performance
            best_time = min(store_results, key=lambda x: x['duration'])
            best_success = max(store_results, key=lambda x: x['success_rate'])
            
            print(f"   🏆 Temps optimal: {best_time['workers']} worker(s) ({best_time['duration']:.1f}s)")
            print(f"   🎯 Meilleur taux: {best_success['workers']} worker(s) ({best_success['success_rate']:.1f}%)")
            print()
        
        print("=" * 60)
        print()
    
    # Comparaison globale
    print("🏆 COMPARAISON GLOBALE")
    print("=" * 60)
    
    # Grouper par magasin
    stores_summary = {}
    for result in all_results:
        store = result['store']
        if store not in stores_summary:
            stores_summary[store] = []
        stores_summary[store].append(result)
    
    print("Magasin    | Meilleur temps | Meilleur taux | Workers optimaux")
    print("-----------|----------------|---------------|------------------")
    
    for store, results in stores_summary.items():
        if results:
            best_time = min(results, key=lambda x: x['duration'])
            best_success = max(results, key=lambda x: x['success_rate'])
            
            print(f"{store:10} | {best_time['duration']:13.1f}s | {best_success['success_rate']:12.1f}% | {best_time['workers']} workers (temps), {best_success['workers']} workers (taux)")
    
    print()
    
    # Champion absolu
    if all_results:
        fastest = min(all_results, key=lambda x: x['duration'])
        most_successful = max(all_results, key=lambda x: x['success_rate'])
        
        print("🥇 CHAMPIONS:")
        print(f"   ⚡ Plus rapide: {fastest['store'].upper()} avec {fastest['workers']} worker(s) ({fastest['duration']:.1f}s)")
        print(f"   🎯 Plus fiable: {most_successful['store'].upper()} avec {most_successful['workers']} worker(s) ({most_successful['success_rate']:.1f}%)")


if __name__ == "__main__":
    # Ajouter l'import de monoprix au main.py
    try:
        from stores.monoprix import get_price_monoprix
        
        # Modifier temporairement la fonction search_single_item pour inclure monoprix
        def search_single_item_extended(store: str, city: str, item: Dict) -> Dict:
            """Version étendue avec support Monoprix"""
            try:
                if store.lower() == "u":
                    from stores.u import get_price_u
                    highest_price, lowest_price, success = get_price_u(city, item)
                elif store.lower() == "carrefour":
                    from stores.carrefour import get_price_carrefour
                    highest_price, lowest_price, success = get_price_carrefour(city, item)
                elif store.lower() == "aldi":
                    from stores.aldi import get_price_aldi
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
        
        # Remplacer la fonction pour ce test
        import __main__
        __main__.search_single_item = search_single_item_extended
        
        run_performance_tests()
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Assurez-vous que tous les modules (monoprix.py, aldi.py, etc.) sont présents")