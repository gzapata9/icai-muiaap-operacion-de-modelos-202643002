"""S9.4 — Tests que escribe el alumnado."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wine_api.dependencies import get_predictor
from wine_api.export_openapi import render_openapi
from wine_api.predictor import UnavailablePredictor

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "openapi.json"


def test_prediction_returns_503_when_model_is_unavailable(
    client: TestClient, valid_payload: dict
) -> None:
    app = client.app
    app.dependency_overrides[get_predictor] = UnavailablePredictor
    try:
        response = client.post("/v1/predictions", json=valid_payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "model_unavailable"
    assert response.headers["X-Request-Id"] == body["request_id"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("alcohol", 4.99, id="alcohol-below-min"),
        pytest.param("alcohol", 20.01, id="alcohol-above-max"),
        pytest.param("ph", 2.49, id="ph-below-min"),
        pytest.param("density", 1.02, id="density-above-max"),
        pytest.param("sulphates", -0.01, id="sulphates-negative"),
        pytest.param("chlorides", None, id="chlorides-null"),
        pytest.param("residual_sugar", "dulce", id="residual-sugar-text"),
    ],
)
def test_out_of_contract_values_are_rejected(
    client: TestClient, valid_payload: dict, field: str, value: object
) -> None:
    valid_payload["features"][field] = value

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert [f["field"] for f in body["error"]["fields"]] == [f"features.{field}"]


@pytest.mark.parametrize("alcohol", [5, 20, 5.0, 20.0])
def test_range_limits_are_inclusive(
    client: TestClient, valid_payload: dict, alcohol: float
) -> None:
    valid_payload["features"]["alcohol"] = alcohol

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 200


def test_openapi_matches_versioned_contract() -> None:
    assert CONTRACT_PATH.exists(), (
        "Genera el contrato con `uv run python -m wine_api.export_openapi`"
    )
    current = json.loads(render_openapi())
    versioned = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert current == versioned, (
        "El contrato OpenAPI ha cambiado: revisa el cambio y regenera "
        "contracts/openapi.json si es intencionado."
    )
