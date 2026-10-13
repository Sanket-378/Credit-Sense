from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_text_model: str = ""
    groq_vision_model: str = ""
    groq_reasoning_effort: str = Field(default="low", pattern="^(none|default|low|medium|high)$")
    max_completion_tokens: int = Field(default=4096, ge=1024, le=16384)
    enable_vision_crosscheck: bool = True
    max_file_mb: int = Field(default=10, ge=1, le=50)
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ocr_languages: str = "en"
    name_match_threshold: float = Field(default=0.82, ge=0, le=1)
    ela_ratio_threshold: float = Field(default=4.0, ge=1)

    @property
    def ocr_language_list(self) -> list[str]:
        return [language.strip() for language in self.ocr_languages.split(",") if language.strip()]

    @property
    def allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
