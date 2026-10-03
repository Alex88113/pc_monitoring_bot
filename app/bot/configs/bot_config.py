from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class BOTApi(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    BOT_TOKEN: SecretStr

    def get_token_bot(self) -> str:
        return self.BOT_TOKEN.get_secret_value()

@lru_cache(maxsize=1)
def get_settings() -> BOTApi:
    return BOTApi()

settings = get_settings()
