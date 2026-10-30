from dataclasses import asdict

from fastapi import APIRouter
from fastapi.openapi.models import Example

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.schemas import PredictionRequest, ErrorResponse, VALID_FEATURES_EXAMPLE, PredictionResponse, Prediction

from datetime import UTC, datetime

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
        "value": {"features": VALID_FEATURES_EXAMPLE}
        },
    "out_of_range": {
        "summary": "Inválido: alcohol fuera de rango",
        "description": "`alcohol` debe estar entre 5 y 20: responde 422.",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": 25.0}}
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
                "color": "red"
                }
            },
        },
    "wrong_type": {
        "summary": "Inválido: texto en lugar de número",
        "description": 'Los campos son numéricos y estrictos: `"9.4"` responde 422.',
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": "9.4"}}
        }
    }

@router.post(
   "/v1/predictions",
    summary="Predecir la banda de calidad de un vino tinto",
    response_description="Predicción pública con trazabilidad del modelo.",
)

def create_prediction(payload: PredictionRequest,predictor: PredictorDep,
                      request_id: RequestIdDep,)-> PredictionResponse:
    
    output = predictor.predict(payload.features)
    # TODO S9.1e: este dict expone `raw_score` y la confianza sin redondear.
    # Declara `-> PredictionResponse` y construye el modelo; para pasar de la
    # dataclass ModelOutput a Prediction investiga `from_attributes=True`.
    return PredictionResponse(
            prediction=Prediction.model_validate(output),
            request_id=request_id,
            served_at=datetime.now(UTC),
        )
