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
from typing import Dict, Any, List

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt.tool_node import ToolInvocation
from langchain_core.prompts import PromptTemplate

# For integration with the main agent
from google import genai
from google.genai.types import FunctionDeclaration, Tool

# Constants
DEVELOPER_INTERVIEW_PROMPT = """
Eres un entrevistador técnico experto en desarrollo de software. Con base en la siguiente oferta de trabajo y el CV del candidato, 
formula preguntas que permitan evaluar las competencias técnicas y la experiencia en las áreas relevantes.
Evalúa específicamente:

1. Conocimientos técnicos fundamentales para el puesto
2. Experiencia previa relevante para el rol
3. Capacidad para resolver problemas complejos
4. Conocimiento de mejores prácticas en desarrollo
5. Habilidades de comunicación técnica

Genera preguntas específicas y detalladas que permitan evaluar en profundidad al candidato.
"""

FOLLOW_UP_PROMPT = """
Basado en la respuesta del candidato a la pregunta anterior:

1. Evalúa la calidad técnica de su respuesta
2. Identifica fortalezas y debilidades
3. Formula una pregunta de seguimiento que profundice en áreas donde el candidato mostró conocimiento y otra en áreas donde podrías necesitar más información.
"""

INTERVIEW_REPORT_PROMPT = """
Genera un informe técnico detallado sobre la entrevista con el candidato. Incluye:

1. Resumen de las competencias técnicas demostradas
2. Evaluación de la experiencia relevante para el puesto
3. Fortalezas y debilidades técnicas identificadas
4. Recomendación sobre la idoneidad técnica del candidato para el puesto
5. Sugerencias de áreas para desarrollo profesional

Sé objetivo y detallado, basándote únicamente en las respuestas técnicas proporcionadas durante la entrevista.
"""

class DeveloperInterviewNode:
    """
    A LangGraph node that simulates a technical interviewer for software developers.
    """
    
    def __init__(self, llm=None):
        """
        Initialize the DeveloperInterviewNode with an optional language model.
        
        Args:
            llm: The language model to use for generating interview questions and evaluations.
                 If None, it will try to use a default model.
        """
        self.llm = llm
        self.interview_prompt = PromptTemplate.from_template(DEVELOPER_INTERVIEW_PROMPT)
        self.follow_up_prompt = PromptTemplate.from_template(FOLLOW_UP_PROMPT)
        self.report_prompt = PromptTemplate.from_template(INTERVIEW_REPORT_PROMPT)
        self.interview_state = {
            "questions_asked": [],
            "responses": [],
            "evaluations": []
        }
    
    def generate_questions(self, job_offer: str, cv: str) -> Dict[str, Any]:
        """
        Generate initial technical interview questions based on job offer and CV.
        
        Args:
            job_offer: The job description text
            cv: The candidate's CV/resume text
            
        Returns:
            A dictionary containing the generated questions
        """
        context = f"Oferta de trabajo:\n{job_offer}\n\nCV:\n{cv}"
        
        # Use LLM to generate questions
        if self.llm:
            prompt = self.interview_prompt.format(context=context)
            response = self.llm.generate_content(prompt).text
        else:
            # Fallback questions if no LLM is provided
            response = """
            1. ¿Podrías describir un proyecto técnicamente desafiante en el que hayas trabajado y cómo lo abordaste?
            2. ¿Cuál es tu experiencia con metodologías ágiles y prácticas DevOps?
            3. ¿Cómo manejas los problemas de rendimiento en tus aplicaciones?
            """
        
        # Update state
        self.interview_state["questions_asked"].append(response)
        
        return {"questions": response, "interview_state": self.interview_state}
    
    def evaluate_response(self, response: str) -> Dict[str, Any]:
        """
        Evaluate a candidate's response and generate follow-up questions.
        
        Args:
            response: The candidate's response to a previous question
            
        Returns:
            A dictionary containing the evaluation and follow-up questions
        """
        # Update state
        self.interview_state["responses"].append(response)
        
        # Use LLM to evaluate response
        if self.llm:
            prompt = self.follow_up_prompt.format(response=response)
            evaluation = self.llm.generate_content(prompt).text
        else:
            # Fallback evaluation if no LLM is provided
            evaluation = """
            La respuesta muestra conocimiento básico del tema, pero carece de detalles técnicos específicos.
            
            Preguntas de seguimiento:
            1. ¿Podrías profundizar en las tecnologías específicas que utilizaste?
            2. ¿Cómo mediste el éxito o la eficacia de tu solución?
            """
        
        # Update state
        self.interview_state["evaluations"].append(evaluation)
        
        return {
            "evaluation": evaluation, 
            "follow_up_questions": evaluation.split("Preguntas de seguimiento:")[1] if "Preguntas de seguimiento:" in evaluation else "",
            "interview_state": self.interview_state
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive technical interview report.
        
        Returns:
            A dictionary containing the final interview report
        """
        # Combine all interview data
        full_interview = "\n\n".join([
            f"Pregunta {i+1}: {q}\nRespuesta: {r}\nEvaluación: {e}"
            for i, (q, r, e) in enumerate(zip(
                self.interview_state["questions_asked"],
                self.interview_state["responses"],
                self.interview_state["evaluations"]
            ))
        ])
        
        # Use LLM to generate report
        if self.llm:
            prompt = self.report_prompt.format(interview_transcript=full_interview)
            report = self.llm.generate_content(prompt).text
        else:
            # Fallback report if no LLM is provided
            report = """
            Informe de Entrevista Técnica
            
            El candidato demuestra conocimientos básicos en desarrollo de software, pero carece de experiencia profunda
            en las tecnologías específicas requeridas para el puesto. Se recomienda considerar para posiciones junior
            con potencial de crecimiento.
            """
        
        return {"report": report, "interview_state": self.interview_state}
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the node.
        
        Args:
            state: The current state dictionary which should contain action and relevant data
            
        Returns:
            Updated state with results from the requested action
        """
        action = state.get("action", "generate_questions")
        
        if action == "generate_questions":
            job_offer = state.get("job_offer", "")
            cv = state.get("cv", "")
            return self.generate_questions(job_offer, cv)
        
        elif action == "evaluate_response":
            response = state.get("candidate_response", "")
            return self.evaluate_response(response)
        
        elif action == "generate_report":
            return self.generate_report()
        
        else:
            return {"error": f"Unknown action: {action}"}

# Function for integration with the main agent as a tool
def developer_interview(input_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Function to be used as a tool for the main agent.
    
    Args:
        input_data: Dictionary containing:
            - action: The interview action to perform ('generate_questions', 'evaluate_response', 'generate_report')
            - job_offer: (Optional) The job description
            - cv: (Optional) The candidate's CV
            - candidate_response: (Optional) The candidate's response to evaluate
            
    Returns:
        A dictionary with the result of the requested action
    """
    # Initialize the interview node with Gemini model if available
    try:
        from app.agent import genai_client, MODEL_ID
        
        model = genai_client.get_generative_model(MODEL_ID)
        interview_node = DeveloperInterviewNode(llm=model)
    except (ImportError, NameError):
        # Fall back to using the node without a specific LLM
        interview_node = DeveloperInterviewNode()
    
    # Run the node with the provided input
    result = interview_node.run(input_data)
    
    # Format the output as required by the tool interface
    if "error" in result:
        return {"output": f"Error: {result['error']}"}
    
    # Format differently based on action
    action = input_data.get("action", "generate_questions")
    if action == "generate_questions":
        return {"output": f"Preguntas de entrevista:\n\n{result['questions']}"}
    elif action == "evaluate_response":
        return {"output": f"Evaluación:\n\n{result['evaluation']}"}
    elif action == "generate_report":
        return {"output": f"Informe técnico:\n\n{result['report']}"}
    else:
        return {"output": str(result)}

# Example of creating a LangGraph workflow
def create_interview_workflow():
    """
    Creates a complete interview workflow using LangGraph components.
    
    Returns:
        A StateGraph object representing the interview workflow
    """
    # Create the workflow
    workflow = StateGraph(state_type=Dict)
    
    # Initialize the interview node
    interview_node = DeveloperInterviewNode()
    
    # Add nodes
    workflow.add_node("generate_questions", lambda state: interview_node.generate_questions(
        state.get("job_offer", ""), state.get("cv", "")
    ))
    workflow.add_node("evaluate_response", lambda state: interview_node.evaluate_response(
        state.get("candidate_response", "")
    ))
    workflow.add_node("generate_report", lambda state: interview_node.generate_report())
    
    # Add edges
    workflow.add_edge("generate_questions", "evaluate_response")
    workflow.add_edge("evaluate_response", "evaluate_response")  # Loop for multiple responses
    workflow.add_conditional_edges(
        "evaluate_response",
        lambda state: "generate_report" if state.get("final_response", False) else "evaluate_response"
    )
    workflow.add_edge("generate_report", END)
    
    # Set the entry point
    workflow.set_entry_point("generate_questions")
    
    return workflow
