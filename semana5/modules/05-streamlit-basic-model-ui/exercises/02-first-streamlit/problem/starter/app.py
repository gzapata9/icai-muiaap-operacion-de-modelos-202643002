"""Starter de la primera interfaz Streamlit para Wine Quality."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from model_ui.contracts import PredictionPayload
from model_ui.errors import ArtifactUnavailableError, InputContractError
from model_ui.gateway import InferenceGateway, PackagedBundleGateway
from model_ui.ui_schema import FIELD_SPECS
from model_ui.presentation import confidence_caption, quality_label


def build_gateway() -> InferenceGateway:
    """Carga obligatoriamente el bundle de S4 configurado."""

    bundle_value = os.getenv("MODEL_UI_BUNDLE")
    if not bundle_value:
        raise ArtifactUnavailableError("MODEL_UI_BUNDLE no está configurado.")
    try:
        return PackagedBundleGateway.from_bundle_path(Path(bundle_value))
    except Exception as error:  # noqa: BLE001
        raise ArtifactUnavailableError("No se pudo cargar el bundle de S4.") from error


def render_bundle_error(st: Any) -> None:
    """Presenta una recuperación segura sin revelar detalles internos."""

    st.error("No se pudo cargar el bundle de S4.")
    st.info("Configura MODEL_UI_BUNDLE y vuelve a ejecutar la aplicación.")


def render_inference_error(st: Any) -> None:
    """Presenta un fallo de validación o inferencia sin detalles sensibles."""

    st.error("No se pudo ejecutar la inferencia.")
    st.info("Revisa los datos y la compatibilidad del bundle de S4.")


def _number_format(step: float) -> str:
    """Muestra tantos decimales como indica el step (p. ej. densidad 0.0001)."""

    text = f"{step:g}"
    decimals = len(text.split(".")[1]) if "." in text else 0
    return f"%.{decimals}f"


def collect_values(st: Any) -> tuple[bool, dict[str, float]]:
    """TODO: renderiza ``FIELD_SPECS`` dentro de un único ``st.form``.

    Cada ``number_input`` debe recibir label, rango, default, step y una key
    estable. Devuelve ``(submitted, values)`` sin llamar al gateway.
    """
    """Renderiza ``FIELD_SPECS`` dentro de un único ``st.form``.

    Cada ``number_input`` recibe label, rango, default, step y una key
    estable. Devuelve ``(submitted, values)`` sin llamar al gateway.
    """

    values: dict[str, float] = {}
    with st.form("wine_quality_form"):
        for field in FIELD_SPECS:
            values[field.name] = st.number_input(
                field.label,
                min_value=field.min_value,
                max_value=field.max_value,
                value=field.default,
                step=field.step,
                format=_number_format(field.step),
                key=f"input_{field.name}",
            )
        submitted = bool(st.form_submit_button("Ejecutar inferencia"))
    return submitted, values
    #raise NotImplementedError(
    #    f"TODO: renderiza los {len(FIELD_SPECS)} campos de FIELD_SPECS"
    #)


def render_prediction(st: Any, prediction: PredictionPayload) -> None:
    """TODO: presenta los cuatro campos de ``PredictionPayload``."""
    st.success(quality_label(prediction))
    band_column, confidence_column = st.columns(2)
    band_column.metric("quality_band", prediction.quality_band)
    confidence_column.metric("confidence", prediction.confidence)
    st.caption(
        confidence_caption(prediction)
        + " Es la salida del modelo, no una probabilidad calibrada ni una garantía."
    )
    st.write(f"model_version: {prediction.model_version}")
    st.write(f"preprocessing_version: {prediction.preprocessing_version}")

    #raise NotImplementedError(
    #    "TODO: presenta quality_band, confidence y las dos versiones"
    #)


def run_app(st: Any, gateway: InferenceGateway) -> None:
    """Conecta submit, gateway y salida sin añadir estado avanzado."""

    submitted, values = collect_values(st)
    if not submitted:
        st.info("Completa el formulario y pulsa «Ejecutar inferencia».")
        return

    try:
        prediction = gateway.predict(values)
    except ArtifactUnavailableError:
        render_bundle_error(st)
        return
    except InputContractError:
        render_inference_error(st)
        return
    except ValueError:
        render_inference_error(st)
        return

    render_prediction(st, prediction)


def run_configured_app(
    st: Any,
    gateway_factory: Callable[[], InferenceGateway] = build_gateway,
) -> None:
    """Carga la configuración y contiene cualquier fallo del bundle."""

    try:
        gateway = gateway_factory()
    except ArtifactUnavailableError:
        render_bundle_error(st)
        return
    run_app(st, gateway)


def main() -> None:
    """Ejecuta la pantalla básica; S6 añadirá estado explícito."""

    try:
        import streamlit as st
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Instala Streamlit con `uv run --with streamlit streamlit run app.py`."
        ) from error

    st.set_page_config(page_title="Wine Quality · S5", page_icon="🍷")
    st.title("Primera interfaz de inferencia")
    st.caption("S5: formulario, gateway y resultado; el estado avanzado llega en S6.")

    run_configured_app(st)


if __name__ == "__main__":
    main()
