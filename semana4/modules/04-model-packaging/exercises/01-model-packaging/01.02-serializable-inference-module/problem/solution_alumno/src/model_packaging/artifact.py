"""Puntos de extensión del taller de serialización."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import json
from preprocess import PREPROCESSING_VERSION, FEATURE_NAMES
from pydantic import BaseModel, ConfigDict, Field

from model_packaging.contracts import (
    QualityBand,
    WineQualityPrediction,
    WineQualityRequest,
)

ARTIFACT_SCHEMA_VERSION = "wine-quality-bundle-v1"
DEFAULT_BUNDLE_PATH = Path("models/wine_quality_bundle")
MANIFEST_FILENAME = "manifest.json"
MODEL_FILENAME = "model.joblib"
OUTPUT_LABELS: tuple[QualityBand, ...] = (
    "needs_review",
    "acceptable",
    "excellent",
)

@overload
def test_validator(fiel:str):
    print("test")

@test_validator()
def continuacion_de_test_validator(field:str):
    print(field)

class WineQualityEstimator(Protocol):
    """Interfaz mínima que debe cumplir el estimador cargado."""

    def predict(self, features: list[list[float]]) -> Sequence[str]:
        """Devuelve una etiqueta por fila."""

    def predict_proba(self, features: list[list[float]]) -> Sequence[Sequence[float]]:
        """Devuelve probabilidades por fila."""


class ArtifactManifest(BaseModel):
    """TODO: declara y valida los metadatos del bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str # Field(ARTIFACT_SCHEMA_VERSION)
    model_version: str = Field(min_length=1)
    preprocessing_version: str 
    feature_names: tuple[str, ...]
    output_labels: tuple[QualityBand, ...]
    estimator_type: str = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Impide crear el manifest si la version es invalida"""
        if value != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {ARTIFACT_SCHEMA_VERSION}, got {value}"
            )
        return value


@dataclass(frozen=True)
class LoadedModelBundle:
    """Bundle cargado; no modificar esta interfaz pública."""

    estimator: WineQualityEstimator
    manifest: ArtifactManifest


def create_manifest(
    estimator: WineQualityEstimator, model_version: str
) -> ArtifactManifest:
    """TODO: devuelve un manifiesto compatible con el contrato."""
    return ArtifactManifest(
        model_version=model_version,
        schema_version=ARTIFACT_SCHEMA_VERSION,
        preprocessing_version=PREPROCESSING_VERSION,
        feature_names=FEATURE_NAMES,
        output_labels=OUTPUT_LABELS,
        estimator_type=type(estimator).__name__,
    )



def save_model_bundle(
    bundle_path: Path,
    estimator: WineQualityEstimator,
    manifest: ArtifactManifest | None = None,
) -> ArtifactManifest:
    """TODO: escribe manifest.json y model.joblib de forma segura."""
    manifest_path: str = Path(bundle_path) / MANIFEST_FILENAME
    if manifest is None:
        
        with open(manifest_path, "w") as m:
            json.dump(manifest, m, indent=4, ensure_ascii=False)
    else: 
        raise NotImplementedError("Implementa save_model_bundle().")
    
    


def load_model_bundle(bundle_path: Path) -> LoadedModelBundle:
    """TODO: valida el manifiesto antes de cargar el estimador."""

    raise NotImplementedError("Implementa load_model_bundle().")


def infer_wine_quality(
    bundle: LoadedModelBundle,
    request: WineQualityRequest,
) -> WineQualityPrediction:
    """TODO: preprocesa, invoca el estimador y valida la respuesta."""

    raise NotImplementedError("Implementa infer_wine_quality().")
