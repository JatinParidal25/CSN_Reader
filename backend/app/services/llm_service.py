import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Provides LLM access with OpenAI-compatible interface or graceful fallback."""

    def __init__(self):
        self._llm: Optional[ChatOpenAI] = None
        self._initialized: bool = False

    def is_configured(self) -> bool:
        return bool(settings.openai_api_key and settings.openai_api_key.strip() and settings.openai_api_key != "your_openai_api_key_here")

    def get_llm(self) -> Optional[ChatOpenAI]:
        if not self.is_configured():
            return None

        if not self._initialized:
            try:
                self._llm = ChatOpenAI(
                    model=settings.llm_model,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_api_base if settings.openai_api_base else None,
                    temperature=0.0,
                    max_tokens=600,
                )
                self._initialized = True
            except Exception as e:
                logger.warning(f"Could not initialize LLM: {e}")
                self._llm = None

        return self._llm


llm_service = LLMService()
