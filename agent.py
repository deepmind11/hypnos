import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"


class Agent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: dict | None = None,
        model: str = "gpt-3.5-turbo",
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.response_format = response_format

    def run(self, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": self.system_prompt}, *messages]
        kwargs = {
            "model": self.model,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.response_format:
            kwargs["response_format"] = self.response_format
        start = time.perf_counter()
        resp = client.chat.completions.create(**kwargs)
        duration_ms = int((time.perf_counter() - start) * 1000)
        content = resp.choices[0].message.content
        with LOG_FILE.open("a") as f:
            f.write(json.dumps({
                "ts": datetime.now().isoformat(timespec="seconds"),
                "agent": self.name,
                "model": self.model,
                "duration_ms": duration_ms,
                "tokens": {
                    "prompt": resp.usage.prompt_tokens,
                    "completion": resp.usage.completion_tokens,
                    "total": resp.usage.total_tokens,
                },
                "messages": full_messages,
                "response": content,
            }) + "\n")
        return content
