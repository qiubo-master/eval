from openai import AsyncOpenAI

from .config import Settings


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    async def answer(self, system_prompt: str, message: str, contexts: list[str]) -> str:
        context = "\n\n".join(contexts) if contexts else "（无检索上下文）"
        response = await self.client.chat.completions.create(
            model=self.settings.llm_model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"上下文：\n{context}\n\n用户请求：\n{message}"},
            ],
        )
        return response.choices[0].message.content or ""

