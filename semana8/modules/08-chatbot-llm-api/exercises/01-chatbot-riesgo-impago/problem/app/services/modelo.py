import joblib

from app.config import MODEL_PATH
from app.schemas.prestamo import PrediccionSalida

# Orden en el que el modelo espera las variables
VARIABLES = [
    "edad",
    "ingresos_mensuales",
    "importe_prestamo",
    "plazo_meses",
    "antiguedad_laboral_anios",
    "impagos_previos",
]


# TODO: cargar el modelo joblib una sola vez, al importar el modulo
def cargar_modelo():
    modelo = joblib.load(MODEL_PATH)
    return modelo


# TODO: funcion decidir(probabilidad) -> "aprobar", "revisar" o "rechazar" (umbrales en el enunciado)
def decidir(probabilidad):
    if probabilidad<0.2:
        return "aprobar"
    elif probabilidad<0.5:
        return "revisar"
    else:
        return "rechazar"


# TODO: funcion predecir(entrada) -> PrediccionSalida, usando VARIABLES para ordenar los valores
def predecir(entrada):
    modelo = cargar_modelo()
    
    valores_ordenados = [entrada[var] for var in VARIABLES]
    probabilidad = modelo.predict_proba([valores_ordenados])[0][1]
    decision = decidir(probabilidad)

    return PrediccionSalida(probabilidad=probabilidad, decision=decision)
