import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


# TODO: definir_tool() -> dict con la definicion de la tool, sacando "parameters" de PrestamoEntrada
def definir_tool():
    esquema = PrestamoEntrada.model_json_schema()
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": "Calcula la probabilidad de impago de un prestamo y la decision.",
            "parameters": esquema,
        },
    }


# TODO: ejecutar_tool(nombre, argumentos_json) -> dict con "ok" True/False
#       (tool desconocida, JSON roto, datos invalidos o campos inventados -> ok False con el error)
def ejecutar_tool(nombre, argumentos_json):
    if nombre != NOMBRE_TOOL:
        return {"ok": False, "error": f"Herramienta desconocida: {nombre}"}
 
    argumentos = leer_argumentos(argumentos_json)
    try:
        entrada = PrestamoEntrada.model_validate(argumentos)
    except ValidationError as e:
        return {"ok": False, "error": str(e)}
 
    try:
        resultado = predecir(entrada)
    except Exception as e:
        return {"ok": False, "error": f"Error del modelo: {e}"}
 
    return {"ok": True, **resultado.model_dump()}

# TODO: responder(mensajes, llm) -> ChatSalida, con el bucle LLM -> tool -> LLM (maximo MAX_VUELTAS)
def _a_dict(mensaje):
    """Acepta tanto objetos Mensaje (Pydantic) como dicts."""
    if isinstance(mensaje, dict):
        return {"role": mensaje["role"], "content": mensaje["content"]}
    return {"role": mensaje.role, "content": mensaje.content}
 
 
def responder(mensajes, llm):
    historial = [{"role": "system", "content": SISTEMA}]
    historial += [_a_dict(m) for m in mensajes]
    herramientas = [definir_tool()]
    herramienta_usada = None
 
    for _ in range(MAX_VUELTAS):
        respuesta = llm.completar(historial, herramientas)
        llamadas = respuesta.get("tool_calls")
 
        # Sin tool -> el LLM ya ha contestado con texto: hemos terminado
        if not llamadas:
            return ChatSalida(respuesta=respuesta.get("content") or "", herramienta=herramienta_usada)
 
        # El mensaje del asistente con las tool_calls tiene que ir al historial antes que los "tool"
        historial.append(respuesta)
        for llamada in llamadas:
            nombre = llamada["function"]["name"]
            argumentos_json = llamada["function"]["arguments"]
            resultado = ejecutar_tool(nombre, argumentos_json)
            historial.append(
                {
                    "role": "tool",
                    "tool_call_id": llamada["id"],
                    "content": json.dumps(resultado),
                }
            )
            herramienta_usada = HerramientaUsada(
                nombre=nombre, argumentos=leer_argumentos(argumentos_json), resultado=resultado
            )
 
    return ChatSalida(
        respuesta="No he podido completar la solicitud. Prueba a reformularla.",
        herramienta=herramienta_usada,
    )
