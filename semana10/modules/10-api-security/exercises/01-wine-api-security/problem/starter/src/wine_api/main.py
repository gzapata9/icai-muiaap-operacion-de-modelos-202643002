"""Punto de entrada de la API: `fastapi dev` usa `wine_api.main:app`."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.rate_limit import FixedWindowRateLimiter
from wine_api.request_id import request_id_middleware
from wine_api.routers import admin, health, predictions
from wine_api.settings import Settings

# TODO S10.6b: ¿qué versión semántica corresponde a una API que pasa a exigir
# `X-API-Key` a clientes que hasta ahora llamaban sin clave? Actualiza
# `API_VERSION`, explica la autenticación, los scopes y el `429` en
# `API_DESCRIPTION` y añade el tag `admin` con su descripción a `OPENAPI_TAGS`.
# Después regenera el contrato (S10.6c):
#   uv run python -m wine_api.export_openapi && git diff contracts/openapi.json
# Comprobación: tests/test_s10_6_openapi.py
# 2.0.0: exigir `X-API-Key` rompe a los clientes anónimos de 1.x (cambio mayor).
API_VERSION = "2.0.0"

API_DESCRIPTION = """
Servicio de inferencia del proyecto **Wine Quality** de Operación de Modelos.

- Todas las respuestas incluyen `request_id` y la cabecera `X-Request-Id`.
- Todos los errores comparten el sobre `ErrorResponse`; programa contra
  `error.code`, no contra `error.message`.
- La predicción es determinista y docente: no es una garantía de calidad.

## Autenticación y scopes

Las operaciones de `/v1/...` exigen la cabecera `X-API-Key` (botón
**Authorize** en `/docs`). Sin clave o con una clave incorrecta la API responde
`401 unauthorized`. Cada clave tiene scopes: `predict` permite predecir y
`admin` consultar el consumo en `GET /v1/admin/usage`; sin el scope necesario
la respuesta es `403 forbidden`. `GET /health` es público.

## Límite de peticiones

Cada cliente tiene una cuota por minuto. Las respuestas permitidas incluyen
`X-RateLimit-Limit` y `X-RateLimit-Remaining`; al superarla la API responde
`429 rate_limited` con la cabecera `Retry-After` (segundos enteros).
"""

OPENAPI_TAGS = [
    {"name": "health", "description": "Disponibilidad del servicio y del modelo."},
    {"name": "predictions", "description": "Inferencia de calidad de vino tinto."},
    {
        "name": "admin",
        "description": "Operación del servicio: consumo por cliente (scope `admin`).",
    },
]


def create_app(
    predictor: Predictor | None = None,
    settings: Settings | None = None,
    rate_limiter: FixedWindowRateLimiter | None = None,
) -> FastAPI:
    """Crea la aplicación; los tests inyectan predictor, configuración y reloj."""

    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(settings.mode)
        yield

    # TODO S10.5b: con `settings.docs_enabled` en `False`, `/docs`, `/redoc` y
    # `/openapi.json` deben responder 404. Investiga los parámetros `docs_url`,
    # `redoc_url` y `openapi_url` de `FastAPI(...)`. ¿Desactivar la
    # documentación protege la API o solo reduce lo que se anuncia?
    # Ocultar la documentación no protege nada: solo deja de anunciar el contrato.
    docs = settings.docs_enabled
    app = FastAPI(
        title="Wine Quality API",
        version=API_VERSION,
        summary="Predicción de la banda de calidad de vinos tintos.",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.rate_limiter = rate_limiter or FixedWindowRateLimiter()

    app.middleware("http")(request_id_middleware)
    # TODO S10.5a: añade `CORSMiddleware` con los orígenes de
    # `settings.cors_origins` (nunca "*"), solo los métodos y cabeceras que usa
    # el front (`Content-Type` y `X-API-Key`), sin credenciales, y expón
    # `X-Request-Id`, `Retry-After` y `X-RateLimit-Remaining` para que el
    # JavaScript del navegador pueda leerlas. ¿Por qué el preflight `OPTIONS`
    # no debe pasar por la autenticación? Pista: el último middleware que se
    # añade es el más externo.
    # Comprobación: uv run pytest -q tests/test_s10_5_cors.py
    # CORS se añade el último para ser el middleware más externo: el preflight
    # `OPTIONS` se responde aquí, sin pasar por la autenticación.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
        allow_credentials=False,
        expose_headers=["X-Request-Id", "Retry-After", "X-RateLimit-Remaining"],
    )
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    app.include_router(admin.router)
    return app


app = create_app()
