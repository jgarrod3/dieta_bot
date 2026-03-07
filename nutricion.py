import requests
from config import USDA_API_KEY

TRADUCCIONES = {
    "arroz": "rice white long grain cooked",
    "pollo": "chicken breast cooked",
    "huevo": "egg whole cooked",
    "avena": "oats rolled",
    "atun": "tuna canned water",
    "leche": "milk whole",
    "pasta": "pasta cooked",
    "pan": "bread white",
    "salmon": "salmon cooked",
    "ternera": "beef ground cooked",
    "platano": "banana raw",
    "manzana": "apple raw",
}

def buscar_alimento(nombre: str, gramos: float):
    nombre_busqueda = TRADUCCIONES.get(nombre.lower(), nombre)
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": nombre_busqueda,
        "api_key": USDA_API_KEY,
        "pageSize": 1,
        "dataType": "SR Legacy"
    }
    
    response = requests.get(url, params=params)
    data = response.json()

    if not data.get("foods"):
        return None

    food = data["foods"][0]
    nutrientes = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}

    factor = gramos / 100
    return {
        "nombre": food["description"],
        "gramos": gramos,
        "kcal": round(nutrientes.get("Energy", 0) * factor, 1),
        "proteinas": round(nutrientes.get("Protein", 0) * factor, 1),
        "carbos": round(nutrientes.get("Carbohydrate, by difference", 0) * factor, 1),
        "grasas": round(nutrientes.get("Total lipid (fat)", 0) * factor, 1),
    }

