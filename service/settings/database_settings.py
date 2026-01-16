from pydantic import Field, SecretStr
from sqlalchemy.engine.url import URL
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='DB_PG_')

    host: str = '127.0.0.1'
    port: int = 5432
    name: str = 'postgres'
    user: str = 'postgres'
    password: SecretStr = Field(default=SecretStr('postgres'))
    pool_size: int = 20
    pool_max_overflow: int = 5
    connect_wait_timeout: float = 5.0
    debug: bool = False
    expire_on_commit: bool = False

    def build_url(self, driver_name) -> URL:
        return URL.create(
            drivername=driver_name,
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.name,
        )

    def build_async_engine_options(self) -> dict:
        return {
            'url': self.build_url('postgresql+asyncpg'),
            'pool_size': self.pool_size,
            'max_overflow': self.pool_max_overflow,
            'pool_timeout': self.connect_wait_timeout,
            'echo': self.debug,
            'echo_pool': self.debug,
        }
