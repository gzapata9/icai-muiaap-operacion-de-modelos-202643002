"""Punto de entrada de la API: `fastapi dev` usa `wine_api.main:app`."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.request_id import request_id_middleware
from wine_api.routers import health, predictions

# 1.1.0: añadir `served_at` es un cambio compatible, así que sube la versión menor.
API_VERSION = "1.1.0"

API_SUMMARY = "Predicción de la banda de calidad de vinos tintos."

API_DESCRIPTION = """
Servicio de inferencia que estima la banda de calidad de un vino tinto a partir
de once variables fisicoquímicas.

## request_id

Cada respuesta incluye un `request_id` que coincide con la cabecera
`X-Request-Id`. Cítalo al reportar una incidencia: permite localizar la
petición en los logs.

## Errores

Todos los errores comparten el mismo sobre:

```json
{
  "error": {"code": "validation_error", "message": "...", "fields": [...]},
  "request_id": "req_..."
}
```

Programa contra `error.code`, que es estable; `message` es orientativo y
`fields` solo aparece en errores de validación.
"""

OPENAPI_TAGS = [
    {"name": "health", "description": "Estado del servicio y del modelo cargado."},
    {
        "name": "predictions",
        "description": "Predicción de la banda de calidad de un vino tinto.",
    },
]


def create_app(predictor: Predictor | None = None) -> FastAPI:
    """Crea la aplicación; los tests inyectan su propio predictor."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(
            os.environ.get("WINE_API_MODE", "ready")
        )
        yield

    app = FastAPI(
        title="Wine Quality API",
        version=API_VERSION,
        summary=API_SUMMARY,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.middleware("http")(request_id_middleware)
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    return app


app = create_app()
