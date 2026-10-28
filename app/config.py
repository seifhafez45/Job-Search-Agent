"""
Single source of truth for all environment/config values.
Every other module imports `settings` from here instead of reading os.environ directly.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "change-me"

    database_url: str
    access_token_expire_minutes: int = 60

    anthropic_api_key: str
    llm_model: str = "claude-sonnet-4-6"

    # Optional: used only by app/llm/groq_client.py (interview_agent + career_rag's
    # own scoped alternative to the shared Anthropic client). Empty by default so
    # teammates who never set these are unaffected.
    groq_api_key: str = ""
    groq_model: str = ""

    job_api_base_url: str = ""
    job_api_key: str = ""

    vector_db_path: str = "./data/vector_store"
    embedding_model: str = "all-MiniLM-L6-v2"

    resume_storage_path: str = "./data/resumes"

    class Config:
        env_file = ".env"


settings = Settings()
