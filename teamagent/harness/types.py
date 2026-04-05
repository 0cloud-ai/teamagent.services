from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class Record:
    type: str = "message"        # "message" | "event"
    # type=message
    role: str | None = None      # "assistant"
    content: str | None = None
    done: bool = False           # True 表示本轮执行结束，系统停止监听/消费
    # type=event
    actor: str | None = None     # "agent"
    action: str | None = None    # "read_file" | "edit_file" | "create_file" | "delete_file" | "run_command"
    target: str | None = None    # 文件路径或命令
    detail: str | None = None    # diff 摘要、执行结果等


@dataclass
class FileWatcher:
    """文件监听模式。系统用 watchdog 监听 file_path，变更时调 engine.watch()。"""
    session_id: str
    file_path: str


@dataclass
class AsyncWatcher:
    """异步迭代模式。系统消费 iterator 拿到原始事件，再调 engine.watch() 转换。"""
    session_id: str
    iterator: AsyncIterator


@dataclass
class FileChangeEvent:
    event_type: str            # "modified" | "created"
    file_path: str             # 变更的文件路径
    new_lines: list[dict]      # 本次新增的行（已 json.loads 解析）
    total_lines: int           # 文件当前总行数


@dataclass
class ProviderInfo:
    name: str                  # provider 配置名
    base_url: str              # API 地址
    api_key: str | None        # API 密钥
    api_format: str            # "anthropic" | "openai-completions" | "ollama"
    model_id: str              # 模型 ID
