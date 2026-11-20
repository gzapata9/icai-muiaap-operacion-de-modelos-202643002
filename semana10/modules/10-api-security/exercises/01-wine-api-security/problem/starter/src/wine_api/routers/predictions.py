from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.rate_limit import enforce_rate_limit
from wine_api.schemas import (
    VALID_FEATURES_EXAMPLE,
    ErrorResponse,
    Prediction,
    PredictionRequest,
    PredictionResponse,
)
from wine_api.security import require_scope

PREDICTION_EXAMPLES = {
    "valid": {
        "summary": "Vino válido",
        "description": "Devuelve `200` con la predicción.",
        "value": {"features": VALID_FEATURES_EXAMPLE},
    },
    "wrong_type": {
        "summary": "Tipo incorrecto",
        "description": "`alcohol` es un texto: devuelve `422`.",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": "mucho"}},
    },
    "out_of_range": {
        "summary": "Fuera de rango",
        "description": "`ph` supera 4.5: devuelve `422`.",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "ph": 7.0}},
    },
}

# TODO S10.2f: protege TODAS las operaciones de este router declarando la
# autenticación en `dependencies=[...]` del `APIRouter` (no en cada ruta ni en
# `include_router()`). ¿Qué ventaja tiene declararla una sola vez aquí?
# TODO S10.3c: sustituye la autenticación a secas por `require_scope("predict")`.
# TODO S10.4d: añade `enforce_rate_limit` DESPUÉS del scope: FastAPI resuelve
# las dependencias en el orden en que las declaras.
# TODO S10.6a: documenta en `responses=` los 401, 403 y 429 con `ErrorResponse`
# (y la cabecera `Retry-After` del 429; investiga el campo `headers` de una
# respuesta en OpenAPI). Comprobación: tests/test_s10_6_openapi.py
router = APIRouter(
    prefix="/v1/predictions",
    tags=["predictions"],
    # Orden: autenticar + autorizar y, solo después, contar la cuota.
    dependencies=[Depends(require_scope("predict")), Depends(enforce_rate_limit)],
    responses={
        400: {"model": ErrorResponse, "description": "El cuerpo no es JSON válido."},
        422: {
            "model": ErrorResponse,
            "description": "JSON válido que incumple campos, tipos o rangos.",
        },
        401: {
            "model": ErrorResponse,
            "description": "Falta `X-API-Key` o no es válida (`unauthorized`).",
        },
        403: {
            "model": ErrorResponse,
            "description": "La clave no tiene el scope `predict` (`forbidden`).",
        },
        429: {
            "model": ErrorResponse,
            "description": "Cuota por minuto agotada (`rate_limited`).",
            "headers": {
                "Retry-After": {
                    "description": "Segundos que hay que esperar antes de reintentar.",
                    "schema": {"type": "integer"},
                }
            },
        },
        503: {"model": ErrorResponse, "description": "El modelo no está cargado."},
    },
)


@router.post(
    "",
    summary="Predecir la banda de calidad de un vino",
    response_description="Predicción con versión del modelo y `request_id`.",
)
def create_prediction(
    payload: Annotated[PredictionRequest, Body(openapi_examples=PREDICTION_EXAMPLES)],
    predictor: PredictorDep,
    request_id: RequestIdDep,
) -> PredictionResponse:
    """Estima la banda de calidad a partir de once variables fisicoquímicas.

    - Todos los campos son obligatorios y numéricos; no se aceptan booleanos,
      textos ni campos extra.
    - Los rangos son inclusivos y están en el esquema `WineFeatures`.
    - `confidence` se devuelve con dos decimales.
    - Guarda `request_id` si necesitas reportar una incidencia.
    - Requiere `X-API-Key` con scope `predict`; cada respuesta indica la cuota
      restante en `X-RateLimit-Remaining`.
    """

    output = predictor.predict(payload.features)
    return PredictionResponse(
        prediction=Prediction.model_validate(output, from_attributes=True),
        request_id=request_id,
        served_at=datetime.now(UTC),
    )
