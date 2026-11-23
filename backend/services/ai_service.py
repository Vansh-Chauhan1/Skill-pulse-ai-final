import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

if not API_KEY or not MODEL:
    raise RuntimeError(
        "LLM_API_KEY and LLM_MODEL must be configured."
    )

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL or None
)


SYSTEM_PROMPT = """
You are SkillPulse Intelligence Assistant.

SkillPulse AI is an Indian Labour Market Intelligence
platform.

Your responsibilities:

1. Explain state-wise skill gaps.
2. Analyse employment trends.
3. Explain sector-wise skill requirements.
4. Interpret employment forecasts.
5. Provide evidence-based recommendations.
6. Help policymakers understand labour market challenges.

IMPORTANT RULES:

- Use only the supplied analytical context for factual
  project-specific statistics.
- Never invent employment statistics.
- Never invent forecasting results.
- Clearly distinguish actual observations from predictions.
- Explain limitations when data is unavailable.
- Give practical and understandable recommendations.
- If information is insufficient, explicitly say so.

Your goal is to turn labour-market data into useful
decision-making insights.
"""


async def ask_ai(question: str, context: str = ""):

    response = await client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
                ANALYTICAL CONTEXT:

                {context}

                USER QUESTION:

                {question}
                """
            }
        ],

        temperature=0.3
    )

    return response.choices[0].message.content