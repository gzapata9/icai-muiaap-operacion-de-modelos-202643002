# Este archivo se hizo en clase para probar que es lo que devuelve un joblib

import joblib
objeto = joblib.load("wine_quality_classifier.joblib")
print(f"Tipo de objeto: {type(objeto)}")
print(objeto)