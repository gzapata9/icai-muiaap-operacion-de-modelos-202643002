"""Vista UX: copy de salida y traducción de errores."""

from __future__ import annotations

from model_ui.contracts import (
    ErrorCode,
    PredictionPayload,
    PredictionView,
    UserFacingError,
)
from model_ui.errors import (
    ArtifactUnavailableError,
    InferenceTimeoutError,
    InputContractError,
)
from model_ui.policies import (
    DEFAULT_CONFIDENCE_POLICY,
    DEFAULT_LATENCY_POLICY,
    ConfidencePolicy,
    LatencyPolicy,
    classify_confidence,
    classify_latency,
)

QUALITY_LABELS = {
    "needs_review": "Requiere revisión",
    "acceptable": "Resultado aceptable",
    "excellent": "Resultado excelente",
}

CONFIDENCE_COPY = {
    "low": (
        "Confianza baja",
        "El resultado es orientativo y requiere revisión; "
        "la confianza no es una garantía.",
    ),
    "medium": (
        "Confianza intermedia",
        "Usa el resultado como señal orientativa y revisa su contexto antes de actuar.",
    ),
    "high": (
        "Confianza alta",
        "La confianza es alta para este modelo, pero no garantiza "
        "que la decisión sea correcta.",
    ),
}

LATENCY_COPY = {
    "within_target": (
        "Dentro del objetivo",
        "La respuesta quedó dentro del objetivo de la demo.",
    ),
    "above_target": (
        "Por encima del objetivo",
        "La respuesta llegó, pero la latencia supera el objetivo técnico de la demo.",
    ),
}


def build_prediction_view(
    prediction: PredictionPayload,
    latency_ms: float,
    *,
    confidence_policy: ConfidencePolicy = DEFAULT_CONFIDENCE_POLICY,
    latency_policy: LatencyPolicy = DEFAULT_LATENCY_POLICY,
) -> PredictionView:
    """Construye la vista con etiquetas, confianza, latencia y versiones."""

    confidence_level = classify_confidence(prediction.confidence, confidence_policy)
    latency_status = classify_latency(latency_ms, latency_policy)
    confidence_label, confidence_message = CONFIDENCE_COPY[confidence_level]
    latency_label, latency_message = LATENCY_COPY[latency_status]
    return PredictionView(
        quality_band=prediction.quality_band,
        quality_label=QUALITY_LABELS[prediction.quality_band],
        confidence=prediction.confidence,
        confidence_level=confidence_level,
        confidence_label=confidence_label,
        confidence_message=confidence_message,
        latency_ms=float(latency_ms),
        latency_status=latency_status,
        latency_label=latency_label,
        latency_message=latency_message,
        model_version=prediction.model_version,
        preprocessing_version=prediction.preprocessing_version,
    )


ERROR_COPY: dict[ErrorCode, tuple[str, str, str]] = {
    "invalid_input": (
        "Datos no válidos",
        "Algún valor del formulario no cumple el contrato de entrada del modelo.",
        "Revisa los valores y sus rangos y vuelve a ejecutar la inferencia.",
    ),
    "artifact_unavailable": (
        "Modelo no disponible",
        "No se pudo cargar el bundle del modelo.",
        "Comprueba que MODEL_UI_BUNDLE apunta a un bundle válido, reinicia la "
        "app y pulsa «Reintentar».",
    ),
    "timeout": (
        "La inferencia tardó demasiado",
        "El modelo no respondió dentro del tiempo permitido.",
        "Pulsa «Reintentar»; si se repite, inténtalo de nuevo más tarde.",
    ),
    "prediction_error": (
        "No se pudo completar la predicción",
        "El modelo no devolvió una salida válida.",
        "Pulsa «Reintentar»; si se repite, comparte el request_id con el equipo.",
    ),
}


def _error_code(error: Exception) -> ErrorCode:
    """Clasifica la excepción por tipo, nunca por su texto."""

    if isinstance(error, InputContractError):
        return "invalid_input"
    if isinstance(error, ArtifactUnavailableError):
        return "artifact_unavailable"
    if isinstance(error, InferenceTimeoutError | TimeoutError):
        return "timeout"
    return "prediction_error"


def to_user_facing_error(error: Exception, request_id: str) -> UserFacingError:
    """Asigna código estable, mensaje accionable y recuperación.

    El texto de ``error`` no se copia nunca: puede contener rutas, valores o
    detalles internos.
    """

    code = _error_code(error)
    title, message, recovery = ERROR_COPY[code]
    return UserFacingError(
        code=code,
        title=title,
        message=message,
        recovery=recovery,
        request_id=request_id,
    )
