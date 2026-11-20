from fastapi import APIRouter

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.errors import ModelUnavailableError
from wine_api.schemas import ErrorResponse, HealthResponse

SERVICE_NAME = "wine-quality-prediction"

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Comprobar el estado del servicio",
    response_description="El servicio está activo y el modelo listo para predecir.",
    responses={
        503: {
            "model": ErrorResponse,
            "description": (
                "El modelo no está cargado (`model_unavailable`): el servicio "
                "está vivo pero no puede predecir."
            ),
        }
    },
)
def read_health(predictor: PredictorDep, request_id: RequestIdDep) -> HealthResponse:
    """Indica si el servicio puede atender predicciones.

    Úsalo como sonda de disponibilidad (readiness) antes de enviar tráfico.
    Un `200` significa que el modelo está cargado; un `503` significa que el
    proceso responde pero el modelo no está listo, así que conviene reintentar
    más tarde en lugar de llamar a `POST /v1/predictions`.
    """

    if not predictor.is_ready():
        raise ModelUnavailableError()
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        model_status="ready",
        model_version=predictor.model_version,
        request_id=request_id,
    )
