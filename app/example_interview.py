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

"""
Example of using the DeveloperInterviewNode for a simulated technical interview.

This script demonstrates how to use the dummy agent for a developer interview 
in two different ways:
1. Direct usage of the DeveloperInterviewNode class
2. Usage via the tool function for integration with the main agent
"""

import json
from app.dummy_agent import DeveloperInterviewNode, developer_interview, create_interview_workflow

# Example data
EXAMPLE_JOB_OFFER = """
Puesto: Desarrollador Full Stack Senior

Descripción:
Buscamos un desarrollador Full Stack con experiencia en React, Node.js y bases de datos SQL/NoSQL.
El candidato ideal tendrá 5+ años de experiencia en desarrollo web, conocimiento de prácticas DevOps,
y experiencia con arquitecturas serverless y microservicios.

Requisitos:
- Sólida experiencia en JavaScript/TypeScript, React y Node.js
- Experiencia con bases de datos SQL y NoSQL
- Conocimiento de AWS, Docker y Kubernetes
- Experiencia en CI/CD y metodologías ágiles
- Capacidad para diseñar APIs RESTful y GraphQL
"""

EXAMPLE_CV = """
Juan Pérez
Desarrollador Full Stack

Experiencia:
- ABC Tech (2019-2023): Desarrollador Full Stack
  * Implementé aplicaciones web con React, Node.js y MongoDB
  * Diseñé e implementé APIs RESTful
  * Colaboré en la migración a microservicios con Docker

- XYZ Solutions (2016-2019): Desarrollador Front-end
  * Desarrollé interfaces de usuario con React y Angular
  * Implementé sistemas de autenticación OAuth y JWT
  * Trabajé en un equipo ágil con Scrum

Habilidades:
- Lenguajes: JavaScript, TypeScript, Python, HTML, CSS
- Frameworks: React, Node.js, Express, Next.js
- Bases de datos: MongoDB, PostgreSQL, Redis
- DevOps: Docker, AWS (Lambda, S3, EC2), CI/CD (GitHub Actions)
"""

EXAMPLE_RESPONSE = """
Respecto a mi experiencia con React, he trabajado extensivamente con esta biblioteca durante los últimos 5 años. 
En ABC Tech, implementé una aplicación de panel de administración completa utilizando React con TypeScript, 
implementando patrones como arquitectura basada en componentes, uso de hooks personalizados para lógica 
reutilizable, y Redux para gestión de estado. 

Para optimizar el rendimiento, utilicé React.memo, useCallback y useMemo para prevenir renderizados innecesarios, 
implementé lazy loading para componentes grandes, y configuré code splitting para reducir el tamaño del bundle inicial.

En cuanto a las bases de datos, he trabajado principalmente con MongoDB y PostgreSQL. Con MongoDB diseñé esquemas 
flexibles para datos que cambiaban frecuentemente, mientras que PostgreSQL lo utilizaba para datos relacionales 
complejos donde la integridad referencial era crucial.
"""


def example_direct_use():
    """Example of direct use of the DeveloperInterviewNode"""
    print("\n==== EJEMPLO DE USO DIRECTO DEL NODO ====\n")
    
    # Initialize the node
    interview_node = DeveloperInterviewNode()
    
    # Generate initial questions
    print("Generando preguntas iniciales...")
    questions_result = interview_node.generate_questions(EXAMPLE_JOB_OFFER, EXAMPLE_CV)
    print("\nPreguntas generadas:")
    print(questions_result["questions"])
    
    # Evaluate a candidate response
    print("\nEvaluando respuesta del candidato...")
    evaluation_result = interview_node.evaluate_response(EXAMPLE_RESPONSE)
    print("\nEvaluación:")
    print(evaluation_result["evaluation"])
    
    # Generate final report
    print("\nGenerando informe final...")
    report_result = interview_node.generate_report()
    print("\nInforme técnico:")
    print(report_result["report"])


def example_tool_use():
    """Example of using the developer_interview function as a tool"""
    print("\n==== EJEMPLO DE USO COMO HERRAMIENTA ====\n")
    
    # Generate questions
    print("Generando preguntas como herramienta...")
    questions_input = {
        "action": "generate_questions",
        "job_offer": EXAMPLE_JOB_OFFER,
        "cv": EXAMPLE_CV
    }
    questions_result = developer_interview(questions_input)
    print(questions_result["output"])
    
    # Evaluate response
    print("\nEvaluando respuesta como herramienta...")
    evaluation_input = {
        "action": "evaluate_response",
        "candidate_response": EXAMPLE_RESPONSE
    }
    evaluation_result = developer_interview(evaluation_input)
    print(evaluation_result["output"])
    
    # Generate report
    print("\nGenerando informe como herramienta...")
    report_input = {
        "action": "generate_report"
    }
    report_result = developer_interview(report_input)
    print(report_result["output"])


def example_workflow():
    """Example of using the LangGraph workflow"""
    print("\n==== EJEMPLO DE USO DEL WORKFLOW DE LANGGRAPH ====\n")
    
    # Create the workflow
    workflow = create_interview_workflow()
    
    # Run the workflow with initial input
    print("Ejecutando flujo de trabajo de entrevista...")
    workflow_input = {
        "job_offer": EXAMPLE_JOB_OFFER,
        "cv": EXAMPLE_CV
    }
    
    # Get the first result - questions
    result = workflow.invoke(workflow_input)
    print("\nPreguntas generadas:")
    print(result["questions"])
    
    # Update the state with a candidate response
    workflow_input = {
        "candidate_response": EXAMPLE_RESPONSE
    }
    result = workflow.invoke(workflow_input)
    print("\nEvaluación y preguntas de seguimiento:")
    print(result["evaluation"])
    
    # Finish the interview and get the report
    workflow_input = {
        "candidate_response": "Mi experiencia con CI/CD incluye configuración de pipelines en GitHub Actions y Jenkins. He trabajado con Docker para containerizar aplicaciones y facilitar el despliegue consistente.",
        "final_response": True
    }
    result = workflow.invoke(workflow_input)
    print("\nInforme final:")
    print(result["report"])


if __name__ == "__main__":
    print("Ejemplos de uso del DeveloperInterviewNode")
    print("==========================================")
    
    try:
        example_direct_use()
        example_tool_use()
        example_workflow()
    except Exception as e:
        print(f"Error durante la ejecución del ejemplo: {e}") 