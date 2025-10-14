from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_port: int = 20213
    cors_allowed_origins: list = ["*"]  # Edit the list to restrict access.
    root: str = "."
    data: str = "./output"
    community_level: int = 2
    dynamic_community_selection: bool = False
    response_type: str = "Multiple Paragraphs"

    @property
    def website_address(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"


settings = Settings()
