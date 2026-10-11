from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from config import OLLAMA_BASE_URL, OLLAMA_MODEL_NAME, OLLAMA_API_KEY

# Initialize AsyncOpenAI client using configuration from config.py
client = AsyncOpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key=OLLAMA_API_KEY
)

# Configure OpenAIChatCompletionsModel with the model settings from config.py
ollama_model = OpenAIChatCompletionsModel(
    client=client,
    model=OLLAMA_MODEL_NAME
)