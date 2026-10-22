import os
import requests
from dotenv import load_dotenv
import json

# Ruta para guardar el json final en la misma carpeta
carpeta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_completa = os.path.join(carpeta_actual, "datos_primerdia_octubre_2019.json")

# API KEY guardada en el .env por seguridad
load_dotenv()
api_key = os.getenv("API_KEY")

url_inventario = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
key = {"api_key": api_key}

response = requests.get(url_inventario, params=key)

if response.status_code == 200:
    print("Conexion completada con el inventario.")
    url_inventario = response.json().get("datos")
    
    # Lista de estaciones disponibles
    estaciones = requests.get(url_inventario).json()

    # Crear variable idema vacia para rellenarla con el resultado de la busqueda
    idema = None

    # Bucle para recorrer los diccinoarios dentro de la lista de estaciones y comprobar el nombre
    for estacion in estaciones:
        # Si encuentra el nombre deja de recorrer el bucle (break)
        if estacion.get("nombre") == "MADRID, CIUDAD UNIVERSITARIA":
            idema = estacion.get("indicativo")
            break
            
    print(f"Idema para MADRID, CIUDAD UNIVERSITARIA: {idema}")
    
    # Comprobar que idema no sea None
    if idema:
        # Fechas con el formato indicado segun la documentacion de la api
        fechaIniStr = "2019-10-01T00:00:00UTC"
        fechaFinStr = "2019-10-31T23:59:59UTC"
        
        # Url con los parametros
        url_clima = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema}"
        
        response_clima = requests.get(url_clima, params={key})
        
        if response_clima.status_code == 200:
            url_datos_clima = response_clima.json().get("datos")
            datos_octubre_2019 = requests.get(url_datos_clima).json()
            
            print(f"\nResultados: {len(datos_octubre_2019)}.")
            print("Datos del primer día de octubre:")
            print(datos_octubre_2019[0])
        else:
            print(f"Error en la peticion con los parametros{response_clima.status_code}")
    else:
        print("No se encontro un idema que coincida con MADRID, CIUDAD UNIVERSITARIA.")
else:
    print("Error al acceder al inventario:", response.status_code)

if datos_octubre_2019:
    with open(ruta_completa, "w", encoding="utf-8") as archivo:
        json.dump(datos_octubre_2019[0], archivo, ensure_ascii=False, indent=4)