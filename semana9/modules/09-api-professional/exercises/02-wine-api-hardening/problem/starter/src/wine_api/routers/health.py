from fastapi import APIRouter, HTTPException

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.errors import ModelUnavailableError
from wine_api.schemas import ErrorResponse, HealthResponse  # noqa: F401 - pista para S9.1d

SERVICE_NAME = "wine-quality-prediction"

# TODO S9.3a: declara `tags=["health"]` en el router, no en include_router().
router = APIRouter(
    prefix="/v1/scores",
    tags=["health"],
    responses={422: {"model": HealthResponse}},
)


# TODO S9.3b: añade `summary=`, `response_description=` y un docstring que diga
# cuándo usar el endpoint y qué significa un 503. Documenta el 503 con
# `responses={503: {"model": ErrorResponse, "description": ...}}`.
@router.get("/health",
            summary="Comprobar el estado del servicio",
            response_description="El servicio está funcionando y el modelo listo para predecir.",
            responses={503: {
                "model": ErrorResponse,
                "description": "El modelo no está cargado: el servicio no puede predecir."
                }}
            )
def read_health(predictor: PredictorDep, request_id: RequestIdDep):
    # TODO S9.2f: sustituye el HTTPException por `ModelUnavailableError`: el
    # dominio no debería saber de HTTP y el manejador produce el sobre común.
    if not predictor.is_ready():
        raise ModelUnavailableError(status_code=503, detail="Model not ready")
    
    # TODO S9.1d: declara `-> HealthResponse` y devuelve una instancia.
    return HealthResponse({
        "status": "ok",
        "service": SERVICE_NAME,
        "model_status": "ready",
        "model_version": predictor.model_version,
        "request_id": request_id,
    })
