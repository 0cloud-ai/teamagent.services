from pydantic import BaseModel


class ModelConfig(BaseModel):
    id: str
    name: str


class ProviderConfig(BaseModel):
    baseUrl: str
    apiKey: str | None = None
    apiFormat: str
    models: list[ModelConfig]


class EngineConfig(BaseModel):
    engine: str
    name: str | None = None
    description: str | None = None
    apiFormats: list[str]


class HarnessesConfig(BaseModel):
    default: str | None = None
    engines: dict[str, EngineConfig]


class MemberConfig(BaseModel):
    id: str
    type: str
    name: str
    email: str | None = None
    role: str | None = None
    serviceUrl: str | None = None


class AppConfig(BaseModel):
    providers: dict[str, ProviderConfig] = {}
    harnesses: HarnessesConfig = HarnessesConfig(engines={})
    members: list[MemberConfig] = []
