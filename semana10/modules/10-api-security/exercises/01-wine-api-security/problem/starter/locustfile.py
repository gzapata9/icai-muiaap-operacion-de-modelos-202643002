"""S10.7 — Prueba de carga de la Wine Quality API con Locust.

Con la API arrancada en otra terminal (`uv run fastapi dev`), desde este
directorio:

    LOCUST_API_KEY=<clave-del-cliente> uv run --group load locust \\
      -f locustfile.py --headless -u 20 -r 5 -t 1m \\
      --host http://127.0.0.1:8000 --csv reports/s10

Locust cuenta los `429` como fallos: en `reports/s10_stats.csv`, el porcentaje
de fallos de `POST /v1/predictions` es el porcentaje que ha frenado el límite.
"""

import os

from locust import HttpUser, between, task

# Payload propio del cliente de carga: no importa código del servidor.
VALID_FEATURES = {
    "fixed_acidity": 7.4,
    "volatile_acidity": 0.7,
    "citric_acid": 0.0,
    "residual_sugar": 1.9,
    "chlorides": 0.076,
    "free_sulfur_dioxide": 11.0,
    "total_sulfur_dioxide": 34.0,
    "density": 0.9978,
    "ph": 3.51,
    "sulphates": 0.56,
    "alcohol": 9.4,
}
INVALID_FEATURES = {**VALID_FEATURES, "ph": 7.0}


class WineApiUser(HttpUser):
    wait_time = between(0.5, 2)

    # TODO S10.7a: añade `on_start` para que cada usuario simulado envíe la
    # cabecera `X-API-Key` en todas sus peticiones. La clave se lee de la
    # variable de entorno `LOCUST_API_KEY`: nunca la escribas en este archivo.
    # Investiga `self.client.headers` en la documentación de Locust
    # («HttpSession»). Comprobación: sin este paso, todas las predicciones
    # fallan con 401.
    def on_start(self) -> None:
        # La clave llega por entorno: nunca se escribe en este archivo.
        self.client.headers["X-API-Key"] = os.environ["LOCUST_API_KEY"]

    @task(8)
    def predict(self) -> None:
        self.client.post("/v1/predictions", json={"features": VALID_FEATURES})

    # TODO S10.7b: añade una tarea de peso 1 que envíe `INVALID_FEATURES` y
    # trate el `422` como ÉXITO (es la respuesta correcta a un payload inválido)
    # y cualquier otro status como fallo. Investiga `catch_response=True` y
    # dale un `name=` distinto para que salga en otra fila del informe.
    @task(1)
    def predict_invalid(self) -> None:
        # Un 422 es la respuesta correcta a un payload inválido: cuenta como éxito.
        with self.client.post(
            "/v1/predictions",
            json={"features": INVALID_FEATURES},
            name="/v1/predictions [422]",
            catch_response=True,
        ) as response:
            if response.status_code == 422:
                response.success()
            else:
                response.failure(f"Esperaba 422 y llegó {response.status_code}")

    @task(1)
    def health(self) -> None:
        self.client.get("/health")
