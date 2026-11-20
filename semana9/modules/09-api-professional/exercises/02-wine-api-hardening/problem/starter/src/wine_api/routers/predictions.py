from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body
from fastapi.openapi.models import Example

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.schemas import (
    VALID_FEATURES_EXAMPLE,
    ErrorResponse,
    Prediction,
    PredictionRequest,
    PredictionResponse,
)

# TODO S9.3a: mueve aquí `prefix="/v1/predictions"` y `tags=["predictions"]`.
# TODO S9.3c: declara a nivel de router `responses=` para 400, 422 y 503 con
# `{"model": ErrorResponse, "description": ...}`. Así el 422 deja de
# documentarse como `HTTPValidationError`, que ya no es lo que devolvemos.
router = APIRouter(
    prefix="/v1/predictions",
    tags=["predictions"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "El cuerpo no es JSON válido (`invalid_json`).",
        },
        422: {
            "model": ErrorResponse,
            "description": (
                "El JSON no cumple el contrato (`validation_error`); "
                "`error.fields` indica qué campos fallan."
            ),
        },
        503: {
            "model": ErrorResponse,
            "description": "El modelo no está disponible (`model_unavailable`).",
        },
    },
)


# TODO S9.3e: añade summary, response_description y un docstring útil para
# quien consume la API (campos, rangos, decimales de confidence).
# TODO S9.3f: ofrece en Swagger al menos tres ejemplos de cuerpo (uno válido
# y dos inválidos). Investiga `Annotated[PredictionRequest, Body(...)]` con
# `openapi_examples=`; usa VALID_FEATURES_EXAMPLE como base.
PREDICTION_EXAMPLES: dict[str, Example] = {
    "valid": {
        "summary": "Vino tinto válido",
        "description": "Las once variables dentro de rango: responde 200.",
        "value": {"features": VALID_FEATURES_EXAMPLE},
    },
    "out_of_range": {
        "summary": "Inválido: alcohol fuera de rango",
        "description": "`alcohol` debe estar entre 5 y 20: responde 422.",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": 25.0}},
    },
    "missing_and_extra": {
        "summary": "Inválido: falta un campo y sobra otro",
        "description": (
            "Sin `ph` y con un campo desconocido `color`: responde 422 con "
            "un error por campo."
        ),
        "value": {
            "features": {
                **{k: v for k, v in VALID_FEATURES_EXAMPLE.items() if k != "ph"},
                "color": "red",
            }
        },
    },
    "wrong_type": {
        "summary": "Inválido: texto en lugar de número",
        "description": 'Los campos son numéricos y estrictos: `"9.4"` responde 422.',
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": "9.4"}},
    },
}


@router.post(
    "",
    summary="Predecir la banda de calidad de un vino tinto",
    response_description="Predicción pública con trazabilidad del modelo.",
)
def create_prediction(
    payload: Annotated[PredictionRequest, Body(openapi_examples=PREDICTION_EXAMPLES)],
    predictor: PredictorDep,
    request_id: RequestIdDep,
) -> PredictionResponse:
    """Estima la banda de calidad de un vino tinto a partir de once variables.

    - Todas las variables de `features` son obligatorias, numéricas y con rangos
      inclusivos; los campos desconocidos se rechazan con `422`.
    - `prediction.confidence` está entre 0 y 1 y se expone con dos decimales.
    - `served_at` es la hora de servicio en UTC (ISO 8601 con sufijo `Z`).
    - `request_id` coincide con la cabecera `X-Request-Id`: cítalo al reportar
      una incidencia.
    """

    output = predictor.predict(payload.features)
    return PredictionResponse(
        prediction=Prediction.model_validate(output),
        request_id=request_id,
        served_at=datetime.now(UTC),
    )
