# Importaciones necesarias
import logging
from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

# Definir el estado del agente
class EstadoEntrevista(TypedDict):
    estado_actual: str
    informacion_recopilada: dict
    messages: Annotated[list, add_messages]

class InterviewAgent:
    def __init__(self):
        print("\n[INIT] Inicializando InterviewAgent")
        self.memory = MemorySaver()
        self.model = ChatVertexAI(model="gemini-2.0-flash-001", temperature=0)
        self.estados = {
            "presentacion": {
                "completado": False,
                "preguntas": [
                    "¿Qué te motiva a trabajar en este sector?",
                    "¿Qué te motiva a trabajar en este sector?",
                    "¿Cuál ha sido tu mayor logro profesional?"
                ]
            },
            "experiencia": {
                "completado": False,
                "preguntas": [
                    "¿Cuál es tu experiencia laboral más relevante?",
                    "¿Cuántos años de experiencia tienes en el sector?",
                    "¿Cuál ha sido tu mayor logro profesional?"
                ]
            },
            "tecnico": {
                "completado": False,
                "preguntas": [
                    "¿Qué lenguajes de programación dominas?",
                    "¿Qué frameworks has utilizado?",
                    "¿Cuál es tu experiencia con metodologías ágiles?"
                ]
            },
            "informe": {
                "completado": False,
                "preguntas": []
            },
            "siguiente": {
                "completado": False,
                "preguntas": []
            }
        }
        self.graph = self._setup_graph()
        self.current_state = self._initialize_state()
        self.interview_completed = False
        self.final_report = None
        self.current_question_index = 0
        self.thread_id = "interview_thread_1"  # Añadimos un thread_id fijo
        print("[INIT] InterviewAgent inicializado correctamente")

    def entrevistador_node(self, state: EstadoEntrevista):
        """Nodo principal que maneja las preguntas de la entrevista"""
        print(f"\n3. [ENTREVISTADOR] Estado actual: {state['estado_actual']}")
        print(f"3. [ENTREVISTADOR] Índice pregunta actual: {self.current_question_index}")
        print(f"3. [ENTREVISTADOR] Información recopilada: {state['informacion_recopilada'].keys()}")
        
        estado_actual = state["estado_actual"]
        messages = state["messages"]
        
        # Si el estado actual es "siguiente", necesitamos determinar el próximo estado
        if estado_actual == "siguiente":
            # Obtenemos el estado actual real de la información recopilada
            estados_completados = list(state["informacion_recopilada"].keys())
            print(f"3. [ENTREVISTADOR] Estados completados: {estados_completados}")
            
            if "presentacion" not in estados_completados:
                siguiente = "presentacion"
            elif "experiencia" not in estados_completados:
                siguiente = "experiencia"
            elif "tecnico" not in estados_completados:
                siguiente = "tecnico"
            else:
                siguiente = "informe"
            
            print(f"3. [ENTREVISTADOR] Cambiando de 'siguiente' a estado: {siguiente}")
            estado_actual = siguiente
        
        if not self.estados[estado_actual]["completado"]:
            preguntas = self.estados[estado_actual]["preguntas"]
            if self.current_question_index < len(preguntas):
                pregunta = preguntas[self.current_question_index]
                print(f"3. [ENTREVISTADOR] Haciendo pregunta: {pregunta}")
                return {
                    "messages": messages + [HumanMessage(content=pregunta)],
                    "estado_actual": estado_actual,
                    "informacion_recopilada": state["informacion_recopilada"]
                }
            self.current_question_index = 0
            print("3. [ENTREVISTADOR] Reiniciando índice de preguntas")
        
        print("3. [ENTREVISTADOR] Estado completado, pasando al siguiente")
        return {
            "messages": messages,
            "estado_actual": "siguiente",
            "informacion_recopilada": state["informacion_recopilada"]
        }

    def evaluador_node(self, state: EstadoEntrevista):
        """Nodo que evalúa las respuestas y determina si se puede avanzar"""
        print(f"\n2. [EVALUADOR] Evaluando respuesta para estado: {state['estado_actual']}")
        messages = state["messages"]
        estado_actual = state["estado_actual"]
        
        # Buscamos la última respuesta del usuario
        ultima_respuesta = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                ultima_respuesta = msg.content
                break
        
        if not ultima_respuesta:
            print("2. [EVALUADOR] No se encontró respuesta válida")
            return state
        
        print(f"2. [EVALUADOR] Última respuesta del usuario: {ultima_respuesta[:50]}...")
        
        # Creamos un nuevo estado para devolver
        nuevo_estado = {
            "messages": messages,
            "estado_actual": estado_actual,
            "informacion_recopilada": state["informacion_recopilada"]
        }
        
        # Siempre avanzamos (removemos la evaluación del modelo)
        print(f"[EVALUADOR] Avanzando automáticamente")
        self.current_question_index += 1
        print(f"[EVALUADOR] Incrementando índice de pregunta a: {self.current_question_index}")
        
        # Verificamos si hemos completado todas las preguntas del estado actual
        if self.current_question_index >= len(self.estados[estado_actual]["preguntas"]):
            print(f"[EVALUADOR] Completando estado: {estado_actual}")
            self.estados[estado_actual]["completado"] = True
            self.current_question_index = 0
            
            # Guardamos todas las respuestas del estado actual
            respuestas_estado = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    respuestas_estado.append(msg.content)
            
            nuevo_estado["informacion_recopilada"] = {
                **state["informacion_recopilada"],
                estado_actual: " | ".join(respuestas_estado)
            }
            
            print(f"[EVALUADOR] Marcando estado {estado_actual} como completado")
            nuevo_estado["estado_actual"] = "siguiente"
        
        print(f"[EVALUADOR] Devolviendo estado: {nuevo_estado['estado_actual']}")
        return nuevo_estado

    def _get_siguiente_estado(self, estado_actual: str) -> str:
        """Determina el siguiente estado de la entrevista"""
        estados_orden = {
            "presentacion": "experiencia",
            "experiencia": "tecnico",
            "tecnico": "informe"
        }
        return estados_orden.get(estado_actual, "informe")

    def informe_node(self, state: EstadoEntrevista):
        """Nodo que genera el informe final de la entrevista"""
        print("\n[INFORME] Generando informe final")
        info = state["informacion_recopilada"]
        print("[INFORME] Información recopilada:", info.keys())
        
        prompt = f"""
        Genera un informe detallado de la entrevista con la siguiente información:
        
        Presentación: {info.get('presentacion', 'No proporcionada')}
        Experiencia: {info.get('experiencia', 'No proporcionada')}
        Conocimientos Técnicos: {info.get('tecnico', 'No proporcionados')}
        
        El informe debe incluir:
        1. Resumen del perfil
        2. Puntos fuertes
        3. Áreas de mejora
        4. Recomendación final
        """
        
        informe = self.model.invoke([HumanMessage(content=prompt)])
        print("[INFORME] Informe generado correctamente")
        return {"messages": [informe]}

    def _setup_graph(self):
        """Configura el grafo de la entrevista"""
        workflow = StateGraph(EstadoEntrevista)
        
        # Añadimos los nodos
        workflow.add_node("entrevistador", self.entrevistador_node)
        workflow.add_node("evaluador", self.evaluador_node)
        workflow.add_node("informe", self.informe_node)
        
        # Configuramos el flujo
        workflow.add_edge(START, "entrevistador")
        workflow.add_edge("entrevistador", "evaluador")
        
        # El evaluador decide el siguiente paso basado en el estado actual
        workflow.add_conditional_edges(
            "evaluador",
            lambda x: "informe" if x["estado_actual"] == "informe" 
                     else "entrevistador" if x["estado_actual"] in ["presentacion", "experiencia", "tecnico", "siguiente"]
                     else END,
            ["informe", "entrevistador", END]
        )
        
        workflow.add_edge("informe", END)
        
        print("[SETUP] Grafo configurado con flujo: START -> entrevistador -> evaluador -> (informe|entrevistador)")
        return workflow.compile(checkpointer=self.memory)

    def _initialize_state(self):
        """Inicializa el estado de la entrevista"""
        return {
            "estado_actual": "presentacion",
            "informacion_recopilada": {},
            "messages": [
                SystemMessage(content="¿Podrías hacer una breve presentación sobre ti?")
            ]
        }

    def process_response(self, user_response: str) -> dict:
        """Procesa la respuesta del usuario y devuelve la siguiente acción"""
        print(f"\n1. [PROCESS] Procesando respuesta: {user_response[:50]}...")
        print(f"1. [PROCESS] Estado actual: {self.current_state}")
        print(f"1. [PROCESS] Estado actual antes de procesar: {self.current_state['estado_actual']}")
        
        if self.interview_completed:
            print("1. [PROCESS] Entrevista ya completada, devolviendo informe final")
            return {"anwser": self.final_report}

        # Añadimos la respuesta del usuario al estado actual
        self.current_state["messages"].append(HumanMessage(content=user_response))
        
        try:
            thread_config = {"configurable": {"thread_id": self.thread_id}}
            
            # Mantenemos solo una llamada al stream
            next_state = next(self.graph.stream(
                self.current_state,
                config=thread_config
            ))
            
            print(f"1. [PROCESS] Estado recibido: {next_state}")
            
            # Si tenemos un informe, lo procesamos
            if "informe" in next_state:
                self.interview_completed = True
                self.final_report = next_state["informe"]["messages"][-1].content
                return {"question": self.final_report}
            
            # Si tenemos un nuevo estado del entrevistador, actualizamos y devolvemos la pregunta
            if "entrevistador" in next_state:
                nuevo_estado = next_state["entrevistador"]
                if "messages" in nuevo_estado and nuevo_estado["messages"]:
                    self.current_state = nuevo_estado
                    return {"question": nuevo_estado["messages"][-1].content}
            
            # Si no hay nueva pregunta, mantenemos la última
            return {"question": "Por favor, proporciona más detalles en tu respuesta."}
            
        except Exception as e:
            print(f"[ERROR] Error en process_response: {str(e)}")
            logging.error(f"Error procesando la respuesta: {str(e)}")
            return {"question": "Lo siento, ha ocurrido un error en la entrevista."}

    def get_current_state(self):
        """Devuelve el estado actual de la entrevista"""
        return self.current_state["estado_actual"]

    def is_completed(self):
        """Indica si la entrevista ha sido completada"""
        return self.interview_completed

    def reset_interview(self):
        """Reinicia la entrevista al estado inicial"""
        print("\n[RESET] Reiniciando entrevista")
        self.current_state = self._initialize_state()
        self.interview_completed = False
        self.final_report = None
        self.current_question_index = 0
        self.thread_id = f"interview_thread_{id(self)}"
        for estado in self.estados.values():
            estado["completado"] = False
        print("[RESET] Entrevista reiniciada correctamente")