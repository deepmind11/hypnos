import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Agent:
    def __init__(
        self,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: dict | None = None,
        model: str = "gpt-3.5-turbo",
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.response_format = response_format

    def run(self, messages: list[dict]) -> str:
        kwargs = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}, *messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.response_format:
            kwargs["response_format"] = self.response_format
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
