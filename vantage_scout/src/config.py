"""Environment and path configuration for VANTAGE Scout."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT: Path = Path(__file__).resolve().parent.parent
PROMPTS_DIR: Path = PACKAGE_ROOT / "prompts"
OUTPUT_DIR: Path = PACKAGE_ROOT / "output"

load_dotenv(PACKAGE_ROOT / ".env")

WRAPPER_ALIASES: dict[str, str] = {
    "career_sites": "Prompt_Career_Sites.md",
    "careersites": "Prompt_Career_Sites.md",
    "prompt_career_sites": "Prompt_Career_Sites.md",
    "linkedin": "Prompt_LinkedIn.md",
    "prompt_linkedin": "Prompt_LinkedIn.md",
    "aggregators": "Prompt_Aggregators.md",
    "prompt_aggregators": "Prompt_Aggregators.md",
}

PROMPT_VERSION_BY_WRAPPER: dict[str, str] = {
    "Prompt_Career_Sites": "PromptA-v1.0+careersites",
    "Prompt_LinkedIn": "PromptA-v1.0+linkedin",
    "Prompt_Aggregators": "PromptA-v1.0+aggregators",
}

PROMPT_VARIANT_BY_WRAPPER: dict[str, str] = {
    "Prompt_Career_Sites": "A-weekly-unified-careersites",
    "Prompt_LinkedIn": "A-weekly-unified-linkedin",
    "Prompt_Aggregators": "A-weekly-unified-aggregators",
}


class Settings(BaseSettings):
    """Runtime settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=str(PACKAGE_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-5", alias="ANTHROPIC_MODEL")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5vl:7b", alias="OLLAMA_MODEL")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="qwen/qwen-2.5-vl-7b-instruct",
        alias="OPENROUTER_MODEL",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    chrome_user_data_dir: str = Field(default="", alias="CHROME_USER_DATA_DIR")
    browser_headless: bool = Field(default=False, alias="BROWSER_HEADLESS")
    browser_max_steps: int = Field(default=40, alias="BROWSER_MAX_STEPS")

    def provider(self) -> str:
        return self.llm_provider.strip().lower()


def get_settings() -> Settings:
    return Settings()


def resolve_wrapper_filename(wrapper: str) -> str:
    key = wrapper.strip().lower().replace("-", "_").replace(".md", "")
    if key in WRAPPER_ALIASES:
        return WRAPPER_ALIASES[key]
    candidate = f"{wrapper}.md" if not wrapper.endswith(".md") else wrapper
    path = PROMPTS_DIR / candidate
    if path.is_file():
        return path.name
    raise ValueError(
        f"Unknown wrapper '{wrapper}'. Expected one of: "
        f"{sorted(set(WRAPPER_ALIASES.keys()))}"
    )


def wrapper_stem(filename: str) -> str:
    return Path(filename).stem


def getenv_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
