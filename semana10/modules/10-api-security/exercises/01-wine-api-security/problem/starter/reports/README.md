# S10.7 — Informe de carga

> **TODO S10.7c:** ejecuta Locust con `--csv reports/s10`, versiona los CSV
> generados y completa las tablas y el análisis de este archivo.

## Cómo se ha medido

| Dato | Valor |
| --- | --- |
| Comando de la API | `uv run fastapi dev` (1 proceso) |
| Comando de Locust | `uv run --group load locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10` |
| Cliente usado | `front` (scope `predict`) |
| `rate_limit_per_minute` del cliente | 60 |
| Máquina | _CPU_, Windows (Git Bash) |

Archivos generados por Locust y versionados junto a este informe:
`s10_stats.csv`, `s10_failures.csv` y `s10_stats_history.csv`.

## Resultados

Valores de `s10_stats.csv` (60 s de prueba, 20 usuarios).

| Endpoint | Peticiones | RPS | p50 (ms) | p95 (ms) | Fallos | % 429 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `POST /v1/predictions` | 732 | 12.36 | 4 | 7 | 632 | 86.3 % |
| `/v1/predictions [422]` | 104 | 1.76 | 4 | 7 | 85 | — |
| `GET /health` | 95 | 1.60 | 3 | 5 | 0 | — |
| Aggregated | 931 | 15.72 | 4 | 7 | 717 | 77.0 % |

`% 429` = fallos `429` de `s10_failures.csv` / peticiones de
`POST /v1/predictions` × 100 = 632 / 732 × 100 = 86.3 %. En `Aggregated`,
todos los fallos son `429` (717 / 931). Los 85 fallos de la fila `[422]` también
son `429` (`Esperaba 422 y llegó 429` en `s10_failures.csv`).

## Análisis

- **¿Cuántas predicciones por minuto deja pasar el límite y cuántas ha pedido
  Locust? ¿Cuadra el `% 429` con esa cuenta?**
  El límite deja pasar 60 por minuto y Locust pidió 836. Pasaron 119 (dos
  ventanas de 60) y el resto, 717, fueron `429`. Sí cuadra.

- **¿Qué latencia (p50, p95) tiene `GET /health`, que no pasa por autenticación
  ni rate limit, frente a `POST /v1/predictions`?**
  `/health`: 3 ms y 5 ms. `/v1/predictions`: 4 ms y 7 ms. La seguridad y el
  modelo solo añaden 1–2 ms.

- **¿Qué cambiaría con dos workers (`fastapi run --workers 2`) y un contador en
  memoria por proceso?**
  Cada proceso contaría por separado, así que el cliente podría hacer hasta 120
  peticiones por minuto en vez de 60. Para evitarlo, el contador tendría que
  estar compartido (por ejemplo, en Redis).

- **Si quisieras medir la capacidad del servicio y no la política de cuotas,
  ¿qué cliente y qué límite usarías?**
  Un cliente solo para pruebas con un límite muy alto (por ejemplo, 100 000 por
  minuto), para que no aparezcan `429` y se mida solo lo que aguanta la API.
