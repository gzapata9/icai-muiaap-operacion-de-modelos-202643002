# Semana 2 — Proyectos reproducibles con uv y Git

- **Clase 1 — [Assignment 2.1](../assignments/semana02_clase01_assignment.pdf):** crear el proyecto local `env-demo`, ejecutar una misma base de código en DEV/PRE/PRO, comprobarla con tests y registrar tres commits locales.
- **Clase 2 — [Assignment 2.2](../assignments/semana02_clase02_assignment.pdf):** reorganizar el caso Wine de S1, comprobarlo y trabajar con una rama, `push` y pull request contra `main` del fork de la pareja.

| Fichero para la clase 2 | Uso |
| --- | --- |
| [`starter/WineQT.csv`](starter/WineQT.csv) | Dataset del caso Wine que se reorganiza como proyecto reproducible. |
| [`starter/train.py`](starter/train.py) | Punto de partida del entrenamiento que debe integrarse en la nueva estructura. |
| [`starter/test_train.py`](starter/test_train.py) | Test inicial para comprobar que el entrenamiento conserva su comportamiento. |

Los assignments contienen todo el recorrido; durante la práctica no hay otra documentación que consultar.

## Comentarios sobre la práctica 2
### Pasos seguidos:
- Creada la rama feature/s2-wine-project para trabajar fuera de la rama main
- Inicializado el paquete e instalado de las dependencias (pandas, scikitlearn, Pytest, Ruff)
- Ajuste de rutas para los imports
- Ejecutado el entrenamiento para comprobar el funcionamiento correcto
