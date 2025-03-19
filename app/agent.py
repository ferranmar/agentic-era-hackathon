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

import vertexai
from google import genai
from google.auth import default
from google.genai.types import (
    Content,
    FunctionDeclaration,
    LiveConnectConfig,
    Modality,
    Part,
    Tool,
)

from app.templates import SYSTEM_INSTRUCTION

# Constants
VERTEXAI = os.getenv("VERTEXAI", "true").lower() == "true"
LOCATION = "us-central1"
EMBEDDING_MODEL = "text-embedding-004"
MODEL_ID = "gemini-2.0-flash-001"

# Initialize Google Cloud clients
credentials, project_id = default()
vertexai.init(project=project_id, location=LOCATION)


if VERTEXAI:
    genai_client = genai.Client(
        project=project_id,
        location=LOCATION,
        vertexai=True,
    )
else:
    # API key should be set using GOOGLE_API_KEY environment variable
    genai_client = genai.Client(http_options={"api_version": "v1alpha"})


def hello_world():
    return {"output": "hello world!"}


hello_world_tool = Tool(
    function_declarations=[FunctionDeclaration(name="hello_world")]
)


tool_functions = {
    "hello_world": hello_world,
}

live_connect_config = LiveConnectConfig(
    response_modalities=[Modality.TEXT],
    tools=[hello_world_tool],
    system_instruction=Content(parts=[Part(text=SYSTEM_INSTRUCTION)]),
)
