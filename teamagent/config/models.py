from pydantic import BaseModel


class ModelConfig(BaseModel):
    id: str
    name: str


class ProviderConfig(BaseModel):
    baseUrl: str
    apiKey: str | None = None
    apiFormat: str
    models: list[ModelConfig]


# TODO: 后续用于配置外部 harness 引擎（bin 路径、server 端口等）
# 内置引擎（claude-agent-sdk 等）通过 registry 自动注册，不需要在此配置。
# class EngineConfig(BaseModel):
#     engine: str
#     name: str | None = None
#     description: str | None = None
#     apiFormats: list[str]
#     bin: str | None = None
#     serverUrl: str | None = None
#
# class HarnessesConfig(BaseModel):
#     default: str | None = None
#     engines: dict[str, EngineConfig]


class MemberConfig(BaseModel):
    id: str
    type: str
    name: str
    email: str | None = None
    role: str | None = None
    serviceUrl: str | None = None


class AppConfig(BaseModel):
    providers: dict[str, ProviderConfig] = {}
    # harnesses: HarnessesConfig = HarnessesConfig(engines={})
    members: list[MemberConfig] = []
