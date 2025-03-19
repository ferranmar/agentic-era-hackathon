# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google
import vertexai
from google import genai
from google.genai.types import (
    Content,
    FunctionDeclaration,
    LiveConnectConfig,
    Tool,
    Schema
)
from langchain_google_vertexai import VertexAIEmbeddings

from app.templates import FORMAT_DOCS, SYSTEM_INSTRUCTION
from app.vector_store import get_vector_store
from app.interview_agent import InterviewAgent

# Constants
VERTEXAI = os.getenv("VERTEXAI", "true").lower() == "true"
LOCATION = "us-central1"
EMBEDDING_MODEL = "text-embedding-004"
MODEL_ID = "gemini-2.0-flash-001"
URLS = [
    "https://cloud.google.com/architecture/deploy-operate-generative-ai-applications"
]

# Initialize Google Cloud clients
credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=LOCATION)


if VERTEXAI:
    genai_client = genai.Client(project=project_id, location=LOCATION, vertexai=True)
else:
    # API key should be set using GOOGLE_API_KEY environment variable
    genai_client = genai.Client(http_options={"api_version": "v1alpha"})

# Initialize vector store and retriever
embedding = VertexAIEmbeddings(model_name=EMBEDDING_MODEL)
vector_store = get_vector_store(embedding=embedding, urls=URLS)
retriever = vector_store.as_retriever()

# Crear una instancia global del agente entrevistador
interview_agent = InterviewAgent()

def retrieve_docs(query: str) -> dict[str, str]:
    """
    Retrieves pre-formatted documents about MLOps (Machine Learning Operations),
      Gen AI lifecycle, and production deployment best practices.

    Args:
        query: Search query string related to MLOps, Gen AI, or production deployment.

    Returns:
        A set of relevant, pre-formatted documents.
    """
    docs = retriever.invoke(query)
    formatted_docs = FORMAT_DOCS.format(docs=docs)
    return {"output": formatted_docs}


# Configure tools and live connection
retrieve_docs_tool = Tool(
    function_declarations=[
        FunctionDeclaration.from_callable(client=genai_client, callable=retrieve_docs)
    ]
)


def developer_interview_python(anwser: str) -> dict[str, str]:
    """
    Asistente .

    Args:
        anwser: user answer.

    Returns:
        response to the user
    """
    print("SE LLAMA !!!!!!!!!!!!!!!!!!")
    print(anwser)
    return {"question": "¿Cual es tu experiencia en FastAPI?, ¿Cual es tu experiencia en SQLAlchemy?"}


# Add the developer interview tool
developer_interview_tool_python = Tool(
    function_declarations=[
        FunctionDeclaration.from_callable(client=genai_client, callable=developer_interview_python)
    ]
)

def developer_interview_company(anwser: str) -> dict[str, str]:
    """
    Asistente .

    Args:
        anwser: user answer.

    Returns:
        response to the user
    """
    print("SE LLAMA !!!!!!!!!!!!!!!!!!")
    print(anwser)
    return {"question": "El horario de trabajo es de 9 a 18, con un horario de almuerzo de 1 hora. El salario es de 40.000€ brutos anuales. Hay tickets restaurante y de transporte."}

nervous_data = []

def developer_interview_nervous(anwser: str) -> dict[str, str]:
    """
    Asistente .

    Args:
        anwser: user answer.

    Returns:
        response to the user
    """
    print("SE LLAMA !!!!!!!!!!!!!!!!!!")
    print(anwser)   
    nervous_data.append(anwser)
    print(nervous_data)
    return {"question": "OK"}

def developer_interview(anwser: str) -> dict[str, str]:
    """
    Asistente que maneja la entrevista de desarrollo.

    Args:
        anwser: Respuesta del usuario.

    Returns:
        Siguiente pregunta o informe final de la entrevista.
    """


    response = interview_agent.process_response(anwser)
    print(f"response: {response}")
    return response


# Add the developer interview tool
# developer_interview_tool = Tool(
#     function_declarations=[
#         FunctionDeclaration.from_callable(client=genai_client, callable=developer_interview_company),
#         FunctionDeclaration.from_callable(client=genai_client, callable=developer_interview_python)
#     ]
# )

developer_interview_tool = Tool(
    function_declarations=[
        # FunctionDeclaration(
        #     name="developer_interview",
        #     description="Herramienta para obtener la siguiente pregunta de la entrevista. Tienes que indicar siempre que es lo que ha dicho el usuario",
        #     parameters=Schema(
        #         type="object",
        #         properties={"anwser": {"type": "string", "description": "Respuesta del usuario"}}
        #     ),
        #     response=Schema(
        #         type="object",
        #         properties={"question": {"type": "string", "description": "Pregunta para la entrevista"}}
        #     )
        # ), 
        FunctionDeclaration(
            name="developer_interview_nervous",
            description="Herramienta para obtener la siguiente pregunta de la entrevista. Tienes que indicar siempre que es lo que ha dicho el usuario",
            parameters=Schema(
                type="object",
                properties={"anwser": {"type": "string", "description": "Respuesta del usuario"}}
            ),
            response=Schema(
                type="object",
                properties={"question": {"type": "string", "description": "Pregunta para la entrevista"}}
            )
        ), 
        FunctionDeclaration(
            name="developer_interview_company",
            description="Herramienta para obtener la siguiente pregunta de la entrevista. Tienes que indicar siempre que es lo que ha dicho el usuario",
            parameters=Schema(
                type="object",
                properties={"anwser": {"type": "string", "description": "Respuesta del usuario"}}
            ),
            response=Schema(
                type="object",
                properties={"question": {"type": "string", "description": "Pregunta para la entrevista"}}
            )
        ),
        FunctionDeclaration(
            name="developer_interview_python",
            description="Herramienta para obtener la siguiente pregunta de la entrevista. Tienes que indicar siempre que es lo que ha dicho el usuario",
            parameters=Schema(
                type="object",
                properties={"anwser": {"type": "string", "description": "Respuesta del usuario"}}
            ),
            response=Schema(
                type="object",
                properties={"question": {"type": "string", "description": "Pregunta para la entrevista"}}
            )
        )
    ]
)



def retrieve_docs(query: str) -> dict[str, str]:
    """
    Retrieves pre-formatted documents about MLOps (Machine Learning Operations),
      Gen AI lifecycle, and production deployment best practices.

    Args:
        query: Search query string related to MLOps, Gen AI, or production deployment.

    Returns:
        A set of relevant, pre-formatted documents.
    """
    docs = retriever.invoke(query)
    formatted_docs = FORMAT_DOCS.format(docs=docs)
    return {"output": formatted_docs}



tool_functions = {
    # "retrieve_docs": retrieve_docs,
    "developer_interview_python": developer_interview_python,
    "developer_interview_company": developer_interview_company,
    "developer_interview_nervous": developer_interview_nervous,
    # "developer_interview": developer_interview
}

live_connect_config = LiveConnectConfig(
    response_modalities=["AUDIO"],
    tools=[developer_interview_tool],
    system_instruction=Content(parts=[{"text": SYSTEM_INSTRUCTION}]),
)
