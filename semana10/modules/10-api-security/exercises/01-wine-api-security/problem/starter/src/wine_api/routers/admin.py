from fastapi import APIRouter, Depends

from wine_api.dependencies import RequestIdDep, SettingsDep
from wine_api.rate_limit import RateLimiterDep
from wine_api.schemas import ClientUsage, ErrorResponse, UsageResponse
from wine_api.security import require_scope

# TODO S10.3d: protege este router con el scope `admin` (a nivel de
# `APIRouter`, como en predicciones) y crea `GET /v1/admin/usage`:
# - devuelve `UsageResponse` (tipo de retorno, no `dict`) con un `ClientUsage`
#   por cliente configurado, ordenados por nombre: nombre, peticiones en la
#   ventana actual (`limiter.usage(...)`) y límite por minuto;
# - nunca incluyas la clave: ¿qué campo de `ClientConfig` NO debe salir?
# - añade `summary`, `response_description` y un docstring para /docs (los
#   tests de S9.3 lo exigen a toda operación).
# Comprobación: uv run pytest -q tests/test_s10_3_authorization.py
# TODO S10.6a: documenta también aquí los 401 y 403 con `ErrorResponse`.
router = APIRouter(
    prefix="/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_scope("admin"))],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Falta `X-API-Key` o no es válida (`unauthorized`).",
        },
        403: {
            "model": ErrorResponse,
            "description": "La clave no tiene el scope `admin` (`forbidden`).",
        },
    },
)


@router.get(
    "/usage",
    summary="Consultar el consumo de cada cliente",
    response_description="Peticiones en la ventana actual y límite por cliente.",
)
def read_usage(
    settings: SettingsDep, limiter: RateLimiterDep, request_id: RequestIdDep
) -> UsageResponse:
    """Muestra, por cliente configurado, cuántas peticiones lleva en la ventana
    actual del rate limit y cuál es su límite por minuto.

    Requiere una API key con scope `admin`. Nunca devuelve claves: solo el
    nombre del cliente. Los clientes aparecen ordenados por nombre.
    """

    clients = [
        ClientUsage(
            client=name,
            requests_in_window=limiter.usage(name),
            limit=config.rate_limit_per_minute,
        )
        for name, config in sorted(settings.clients.items())
    ]
    return UsageResponse(clients=clients, request_id=request_id)
