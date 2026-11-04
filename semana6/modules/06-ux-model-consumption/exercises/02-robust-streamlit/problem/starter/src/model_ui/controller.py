"""Controlador de estados independiente de Streamlit."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError

from model_ui.contracts import PredictionPayload, UiState
from model_ui.errors import BackendInferenceError
from model_ui.gateway import InferenceGateway
from model_ui.presentation import build_prediction_view, to_user_facing_error
from model_ui.telemetry import Telemetry

StateEmitter = Callable[[UiState], None]
Clock = Callable[[], float]
RequestIdFactory = Callable[[], str]


class PredictionController:
    """Orquesta loading, gateway, errores y telemetría."""

    def __init__(
        self,
        gateway: InferenceGateway,
        *,
        telemetry: Telemetry | None = None,
        clock: Clock = perf_counter,
        request_id_factory: RequestIdFactory | None = None,
    ) -> None:
        self.gateway = gateway
        self.telemetry = telemetry or Telemetry()
        self._clock = clock
        self._request_id_factory = request_id_factory or (lambda: uuid4().hex[:10])

    def submit(
        self,
        values: Mapping[str, object],
        *,
        emit: StateEmitter | None = None,
    ) -> UiState:
        """TODO: emite loading, mide, valida la salida y devuelve success/error.
        """

        request_id = self._request_id_factory()
        self._emit(emit, UiState(phase="loading", request_id=request_id))

        started = self._clock()
        try:
            prediction = _validate_output(self.gateway.predict(values))
        except Exception as error:  # noqa: BLE001 - se traduce a estado visible
            latency_ms = self._elapsed_ms(started)
            user_error = to_user_facing_error(error, request_id)
            self.telemetry.record_error(user_error.code, latency_ms)
            state = UiState(phase="error", request_id=request_id, error=user_error)
        else:
            latency_ms = self._elapsed_ms(started)
            view = build_prediction_view(prediction, latency_ms)
            self.telemetry.record_success(
                latency_ms,
                model_version=prediction.model_version,
                preprocessing_version=prediction.preprocessing_version,
            )
            state = UiState(phase="success", request_id=request_id, view=view)

        self._emit(emit, state)
        return state

    def _elapsed_ms(self, started: float) -> float:
        return round((self._clock() - started) * 1000, 3)

    @staticmethod
    def _emit(emit: StateEmitter | None, state: UiState) -> None:
        if emit is not None:
            emit(state)


def _validate_output(raw: object) -> PredictionPayload:
    """Vuelve a validar la salida del gateway antes de enseñarla."""

    try:
        if isinstance(raw, PredictionPayload):
            return PredictionPayload.model_validate(raw.model_dump())
        return PredictionPayload.model_validate(raw)
    except ValidationError as error:
        raise BackendInferenceError("La salida no cumple el contrato.") from error
