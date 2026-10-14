"""TODO: script CLI que encadena contratos, preprocesado e inferencia."""

# Implementa el comando:
# python -m model_inference.predict_file --input <csv> --output <csv>
# No dejes un archivo de salida parcial si alguna fila es inválida.

import argparse
import csv
from pathlib import Path

from model_inference.contracts import WineQualityRequest
from model_inference.inference import (
    DEFAULT_MODEL_PATH,
    infer_wine_quality,
    load_wine_quality_model,
)
from model_inference.preprocess import preprocess_wine_request

OUTPUT_FIELDS = (
    "sample_id",
    "quality_band",
    "confidence",
    "model_version",
    "preprocessing_version",
)


def predict_file(input_path: Path, output_path: Path, model_path: Path) -> int:
    """Valida y predice todas las filas antes de abrir el CSV de salida."""
    model = load_wine_quality_model(model_path)
    predictions = []

    with input_path.open(newline="", encoding="utf-8-sig") as source:
        rows = csv.DictReader(source)
        if not rows.fieldnames or "sample_id" not in rows.fieldnames:
            raise ValueError("El CSV debe incluir la columna sample_id.")

        for row_number, row in enumerate(rows, start=2):
            sample_id = row.pop("sample_id")
            if not sample_id or not sample_id.strip():
                raise ValueError(f"Fila {row_number}: sample_id vacío.")
            try:
                request = WineQualityRequest.model_validate(row)
                features = preprocess_wine_request(request)
                prediction = infer_wine_quality(model, features)
                predictions.append({"sample_id": sample_id, **prediction.model_dump()})
            except ValueError as error:
                raise ValueError(
                    f"Fila {row_number}, sample_id={sample_id}: {error}"
                ) from error

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(predictions)
    return len(predictions)


def main() -> int:
    """Procesa argumentos y comunica errores de datos con código de salida 2."""
    parser = argparse.ArgumentParser(description="Inferencia local de calidad de vino")
    parser.add_argument("--input", required=True, type=Path, help="CSV de muestras")
    parser.add_argument(
        "--output", required=True, type=Path, help="CSV de predicciones"
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    arguments = parser.parse_args()

    try:
        count = predict_file(arguments.input, arguments.output, arguments.model)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f"Predicciones escritas: {count} en {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())