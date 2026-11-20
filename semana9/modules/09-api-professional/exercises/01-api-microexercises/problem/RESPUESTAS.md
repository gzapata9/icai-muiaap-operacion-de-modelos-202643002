# Respuestas — Microejercicios de la clase 1 (S9)

## M1 — Serialización

1. `/v1/scores/leaky` devuelve `band`, `confidence`, `raw_score` y
   `threshold_config`. `/v1/scores/public` devuelve `band`, `confidence`,
   `served_at`, `note` e `is_reliable`. Aparecen en la primera y no en la
   segunda: **`raw_score` y `threshold_config`** (detalles internos del modelo).
2. `/v1/scores/filtered` declara `response_model=PublicScore`: FastAPI valida el
   `dict` devuelto contra ese modelo y **descarta todos los campos que el modelo
   no declara**, así que `raw_score` y `threshold_config` nunca llegan al cliente.
3. Sí: `is_reliable` aparece en el esquema `PublicScore` de `/docs` porque es un
   `@computed_field`, que forma parte del esquema de serialización.

## M2 — Errores

| Petición | Status | `error.code` | `error.fields` |
| --- | ---: | --- | --- |
| `{"age": 30, "income": 1000}` | 200 | — | — (respuesta `{"score": 0.01}`) |
| `{"age": "treinta", "income": 1000}` | 422 | `validation_error` | `[{field: "age", message: "Input should be a valid integer…"}]` |
| `{"age": 30}` | 422 | `validation_error` | `[{field: "income", message: "Field required"}]` |
| `GET /v1/nada` | 404 | `not_found` | — |
| `GET /v1/boom` | 500 | `internal_error` | — |

Sin `handle_validation`, el segundo caso devolvería el 422 por defecto de
FastAPI: `{"detail": [{"type": "int_parsing", "loc": ["body", "age"], "msg": ...,
"input": "treinta"}]}`. Sin la clave `error` en la raíz y, además, repitiendo
el `input`.

## M3 — OpenAPI

1. En `/openapi.json` → `paths["/v1/scores"]["post"]`: `summary` está en
   `summary`; el docstring, en `description`; y `responses=` en `responses`, con
   las claves `200`, `422` y `503`.
2. El ejemplo `minor` (`{"age": 16, "income": 1}`) devuelve 422 porque `age`
   debe estar entre 18 y 100.
3. Ejemplo añadido en `openapi_examples` de `create_score`:

   ```python
   "no_income": {
       "summary": "Sin ingresos",
       "description": "Falta `income`: devuelve 422.",
       "value": {"age": 42},
   },
   ```

   Aparece como tercera opción en el desplegable. Se deshace después, como pide
   el enunciado, para que el test que cuenta ejemplos siga en verde.

## M4 — Tests

1. El test que usa `dependency_overrides` es
   `test_dependency_override_simulates_unavailable_model`: sustituye `get_model`
   por un modelo con `ready = False` y comprueba el 503.
2. Sin `raise_server_exceptions=False`, `TestClient` **relanza la excepción** del
   servidor (`RuntimeError`) dentro del test en lugar de devolver la respuesta
   500, y `test_unexpected_error_hides_secrets` falla. Con el flag, el test ve lo
   mismo que vería un cliente real: el 500 con el sobre de error.
3. Test nuevo en `tests/test_examples.py`:
   `test_zero_income_is_rejected_with_field_path` (`income: 0` → 422 con
   `fields[0].field == "income"`). Al ejecutar los tests pasan los 10 con éxito.
