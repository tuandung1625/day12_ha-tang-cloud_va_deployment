"""Production config — 12-Factor: tất cả từ environment variables."""
import os
import logging
from dataclasses import dataclass, field


@dataclass
class Settings:
    # Server
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # App
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    # LLM
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gemini-2.5-flash")
    )
    max_tool_rounds: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOOL_ROUNDS", "3"))
    )
    max_tool_output_chars: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOOL_OUTPUT_CHARS", "12000"))
    )

    # Security
    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me"))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-jwt-secret"))
    allowed_origins: list = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )

    # Rate limiting
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
    )

    # Budget
    daily_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("DAILY_BUDGET_USD", "5.0"))
    )
    input_cost_per_million_usd: float = field(
        default_factory=lambda: float(
            os.getenv("INPUT_COST_PER_MILLION_USD", "0.54")
        )
    )
    output_cost_per_million_usd: float = field(
        default_factory=lambda: float(
            os.getenv("OUTPUT_COST_PER_MILLION_USD", "4.50")
        )
    )

    # Storage
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))

    def validate(self):
        logger = logging.getLogger(__name__)
        if not 1 <= self.max_tool_rounds <= 6:
            raise ValueError("MAX_TOOL_ROUNDS must be between 1 and 6")
        if not 1000 <= self.max_tool_output_chars <= 50000:
            raise ValueError("MAX_TOOL_OUTPUT_CHARS must be between 1000 and 50000")
        if self.environment == "production":
            if self.agent_api_key.startswith("dev-"):
                raise ValueError("AGENT_API_KEY must be set in production!")
            if self.jwt_secret.startswith("dev-"):
                raise ValueError("JWT_SECRET must be set in production!")
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set - using mock LLM")
        return self


settings = Settings().validate()
