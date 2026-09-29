"""TODO: carga del .joblib e inferencia sobre características preparadas."""

# Declara DEFAULT_MODEL_PATH, load_wine_quality_model() e infer_wine_quality().
# Comprueba las características del artefacto antes de llamar al clasificador.
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast
import joblib
from model_inference.preprocess import FEATURE_NAMES, WineFeatures


DEFAULT_MODEL_PATH = Path("models/wine_quality_classifier.joblib")

class WineQualityEstimator(Protocol):
    def predict(self, features: list[list[float]]) -> Sequence[str]:
        ''''''
    def predict_proba(self, features: list[list[float]]) -> Sequence[Sequence[float]]:
        ''''''
        


@dataclass(frozen=True)
class LoadedWineModel:
    estimator: WineQualityEstimator
    model_version: str


def load_wine_quality_model(model_path: Path) -> LoadedWineModel:
    if not model_path.is_file():
        raise FileNotFoundError(
            f"No se encontró el modelo en {model_path}. "
            "Solicita el artefacto wine_quality_classifier.joblib al profesorado."
        )

    payload = joblib.load(model_path)
    if not isinstance(payload, Mapping):
        raise ValueError("El artefacto debe contener metadatos y un estimador.")

    artifact_features = tuple(payload.get("feature_names", []))
    if artifact_features != FEATURE_NAMES:
        raise ValueError(
            "Los feature_names del artefacto no coinciden con el contrato."
        )

    estimator = payload.get("estimator")
    model_version = payload.get("model_version")
    if not isinstance(model_version, str):
        raise ValueError("El artefacto no declara una versión de modelo válida.")
    if not hasattr(estimator, "predict") or not hasattr(estimator, "predict_proba"):
        raise ValueError("El artefacto no contiene un clasificador compatible.")

    return LoadedWineModel(
        estimator=cast(WineQualityEstimator, estimator),
        model_version=model_version,
    )


def infer_wine_quality(
    model: LoadedWineModel,
    features: WineFeatures,
) -> tuple[str, float]:
    """Predice la categoría y confianza de una fila ya preprocesada."""

    feature_vector = [features.as_vector()]
    quality_band = model.estimator.predict(feature_vector)[0]
    confidence = max(model.estimator.predict_proba(feature_vector)[0])
    return str(quality_band), round(float(confidence), 2)


def artifact_payload(
    estimator: WineQualityEstimator,
    model_version: str,
) -> dict[str, Any]:
    """Crea el formato que serializa el script de preparación del profesorado."""

    return {
        "estimator": estimator,
        "feature_names": list(FEATURE_NAMES),
        "model_version": model_version,
    }