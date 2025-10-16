import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "AutoValidate.AI"
    DB_URL: str = os.getenv("DB_URL", "sqlite:///./providers.db")
    NPI_BASE_URL: str = "https://npiregistry.cms.hhs.gov/api/"
    USE_MOCKS: bool = os.getenv("USE_MOCKS", "true").lower() == "true"
    GOOGLE_MAPS_API_KEY: str | None = os.getenv("GOOGLE_MAPS_API_KEY")
    OCR_ENABLED: bool = os.getenv("OCR_ENABLED", "false").lower() == "true"

settings = Settings()
