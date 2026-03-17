"""
LLM service — Generate answers using OpenAI or Ollama.
"""

import os
from typing import AsyncGenerator
from openai import OpenAI, AsyncOpenAI


SYSTEM_PROMPT = """You are a helpful document assistant. Answer questions based ONLY on the provided context.

Rules:
1. Only use information from the provided context to answer
2. If the context doesn't contain the answer, say "I don't have enough information in the documents to answer this"
3. Cite which document and page the information comes from
4. Be concise but thorough
5. If multiple documents contain relevant info, synthesize them
6. Never make up information that isn't in the context"""


class LLMService:
    """Handles LLM interactions for answer generation."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.model = os.getenv("LLM_MODEL", "gpt-4o")

        if self.provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
            self.async_client = AsyncOpenAI(base_url=f"{base_url}/v1", api_key="ollama")

    def _build_messages(
        self,
        question: str,
        context: str,
        chat_history: list[dict] = None,
    ) -> list[dict]:
        """Build the message list for the LLM."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 exchanges
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add context + question
        user_message = f"""Context from documents:
{context}

---

Question: {question}

Provide a clear, well-structured answer based on the context above. Cite your sources."""

        messages.append({"role": "user", "content": user_message})
        return messages

    async def generate(
        self,
        question: str,
        context: str,
        chat_history: list[dict] = None,
    ) -> dict:
        """Generate a complete answer (non-streaming)."""
        messages = self._build_messages(question, context, chat_history)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,  # Low temperature for factual answers
            max_tokens=1500,
        )

        answer = response.choices[0].message.content or ""

        # Estimate confidence based on response characteristics
        confidence = self._estimate_confidence(answer, context)

        return {"answer": answer, "confidence": confidence}

    async def stream(
        self,
        question: str,
        context: str,
        chat_history: list[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream answer tokens as they're generated."""
        messages = self._build_messages(question, context, chat_history)

        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
            stream=True,
        )

        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def _estimate_confidence(self, answer: str, context: str) -> float:
        """
        Heuristic confidence score based on answer characteristics.
        Returns 0.0 - 1.0.
        """
        low_confidence_phrases = [
            "i don't have enough information",
            "the documents don't contain",
            "not mentioned in the context",
            "i cannot find",
            "no information available",
        ]

        answer_lower = answer.lower()
        for phrase in low_confidence_phrases:
            if phrase in answer_lower:
                return 0.2

        # Higher confidence if answer is substantial and references context
        if len(answer) > 100:
            return 0.85
        elif len(answer) > 50:
            return 0.7
        return 0.5
