"""TODO: carga del .joblib e inferencia sobre características preparadas."""

# Declara DEFAULT_MODEL_PATH, load_wine_quality_model() e infer_wine_quality().
# Comprueba las características del artefacto antes de llamar al clasificador.
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import joblib

from model_inference.contracts import WineQualityPrediction
from model_inference.preprocess import (
    FEATURE_NAMES,
    PREPROCESSING_VERSION,
    WineFeatures,
)


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[2] / "model" / "wine_quality_classifier.joblib"
)


def load_wine_quality_model(
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """Comprueba el contrato de características y la interfaz del estimador."""
    model = joblib.load(model_path)
    if not isinstance(model, dict):
        raise ValueError("El artefacto debe contener metadatos y un estimador.")
    feature_names = model.get("feature_names")
    if not isinstance(feature_names, (list, tuple)) or (
        tuple(feature_names) != FEATURE_NAMES
    ):
        raise ValueError(
            "Los feature_names del artefacto no coinciden con el contrato."
        )
    estimator = model.get("estimator")
    if not all(
        callable(getattr(estimator, method, None))
        for method in ("predict", "predict_proba")
    ) or not hasattr(estimator, "classes_"):
        raise ValueError("El artefacto no contiene un clasificador compatible.")
    version = model.get("model_version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("El artefacto no declara un model_version válido.")
    return model


def infer_wine_quality(model: Mapping[str, Any] | None, features: WineFeatures,):
    """Predice y valida la categoría y su probabilidad para una muestra."""
    if model is None:
        model = load_wine_quality_model()
    vector = [features.as_vector()]
    estimator = model["estimator"]
    output_class = estimator.predict(vector)[0]
    probabilities = estimator.predict_proba(vector)[0]
    class_index = list(estimator.classes_).index(output_class)
    confidence = float(probabilities[class_index])
    return WineQualityPrediction(
        quality_band=str(output_class),
        confidence=confidence,
        model_version=model["model_version"],
        preprocessing_version=PREPROCESSING_VERSION,
    )