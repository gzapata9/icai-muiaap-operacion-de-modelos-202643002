import os
import requests
from dotenv import load_dotenv

# API KEY
load_dotenv()
api_key = os.getenv("API_KEY")

url_inventario = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
response_inv = requests.get(url_inventario, params={"api_key": api_key})

if response_inv.status_code == 200:
    # AEMET devuelve una URL temporal en la clave 'datos'
    url_datos_inventario = response_inv.json().get("datos")
    
    # 2. Descargar los datos reales del inventario y buscar la estación
    estaciones = requests.get(url_datos_inventario).json()
    idema = None
    
    for estacion in estaciones:
        if estacion.get("nombre") == "MADRID, CIUDAD UNIVERSITARIA":
            idema = estacion.get("indicativo") # Obtenemos el idema
            break
            
    print(f"Indicativo (idema) encontrado: {idema}")
    
    # 3. Llamar al endpoint de climatologías diarias
    if idema:
        # Fechas corregidas al formato API AEMET para octubre de 2019
        fechaIniStr = "2019-10-01T00:00:00UTC"
        fechaFinStr = "2019-10-31T23:59:59UTC"
        
        # Sustituimos las variables en la URL
        url_clima = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema}"
        
        # No olvides pasar tu API key como query string
        response_clima = requests.get(url_clima, params={"api_key": api_key})
        
        if response_clima.status_code == 200:
            url_datos_clima = response_clima.json().get("datos")
            # Descargamos los datos finales
            datos_octubre = requests.get(url_datos_clima).json()
            
            print(f"\n¡Éxito! Se han obtenido {len(datos_octubre)} registros.")
            print("Datos del primer día de octubre:")
            print(datos_octubre[0])
        else:
            print("Error al pedir la climatología:", response_clima.status_code)
else:
    print("Error al acceder al inventario:", response_inv.status_code)