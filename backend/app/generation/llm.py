"""LLM client for Hugging Face Inference API.

Wraps InferenceClient.chat_completion for Qwen2.5-7B-Instruct.
Returns text + token usage for logging.
"""

from dataclasses import dataclass

from huggingface_hub import InferenceClient

from ..config import settings


MODEL = "meta-llama/Llama-3.1-8B-Instruct"


@dataclass
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def _client() -> InferenceClient:
    if not settings.hf_token:
        raise RuntimeError("HF_TOKEN is not set in .env")
    return InferenceClient(model=MODEL, token=settings.hf_token)


def generate(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 700,
) -> LLMResponse:
    """Call chat completion with a system + user prompt."""
    client = _client()
    response = client.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    text = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    return LLMResponse(
        text=text.strip(),
        model=MODEL,
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
    )
