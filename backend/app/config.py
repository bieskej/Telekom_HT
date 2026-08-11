from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg2://postgres:admin@localhost:5432/ht_eronet"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    rezervacija_minuta: int = 5
    karantena_dana_default: int = 60
    jwt_secret: str = "ht-eronet-dev-secret-promijeni-u-produkciji"
    jwt_expire_hours: int = 8
    smtp_host: str = ""  # npr. smtp.gmail.com, smtp.office365.com, localhost (smtp4dev)
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@eronet.ba"
    smtp_use_tls: bool = True

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_host.strip())
    iskoristivost_upozorenje_postotak: float = 90.0
    admin_alert_email: str = "admin@eronet.ba"


settings = Settings()
