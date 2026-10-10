"""统一的 AI 客户端封装"""

from config import ZHIPU_MODEL
from data_manager import get_active_ai_provider


class AIClient:
    def __init__(self, provider: dict):
        self.provider = provider or {}
        self.api_key = self.provider.get("api_key") or ""
        self.model = self.provider.get("model") or ""
        self.base_url = self.provider.get("base_url") or ""
        self.sdk = (self.provider.get("sdk") or self._infer_sdk()).lower()
        self._client = self._build_client()

    def _infer_sdk(self) -> str:
        ptype = (self.provider.get("provider") or "zhipu").lower()
        if ptype == "zhipu":
            return "zhipu"
        if ptype == "anthropic":
            return "anthropic"
        return "openai"

    def _build_client(self):
        if not self.api_key:
            raise RuntimeError("缺少 API Key")

        if self.sdk == "zhipu":
            from zai import ZhipuAiClient

            return ZhipuAiClient(api_key=self.api_key)

        if self.sdk == "openai":
            try:
                from openai import OpenAI
            except ImportError:
                raise RuntimeError("请先安装依赖：pip install openai")
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            return OpenAI(**kwargs)

        if self.sdk == "anthropic":
            try:
                from anthropic import Anthropic
            except ImportError:
                raise RuntimeError("请先安装依赖：pip install anthropic")
            return Anthropic(api_key=self.api_key)

        raise ValueError(f"不支持的 SDK 类型：{self.sdk}")

    def chat(self, messages, max_tokens=4096, temperature=0.7) -> str:
        if self.sdk == "anthropic":
            system_parts = []
            chat_msgs = []
            for m in messages:
                if m.get("role") == "system":
                    system_parts.append(m.get("content", ""))
                else:
                    chat_msgs.append(m)
            resp = self._client.messages.create(
                model=self.model,
                system="\n".join(system_parts).strip() or None,
                messages=chat_msgs,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if not resp.content:
                return ""
            return getattr(resp.content[0], "text", "") or ""

        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""


def get_active_ai_client() -> AIClient:
    provider = get_active_ai_provider()
    if not provider:
        raise RuntimeError("尚未配置任何 AI Provider，请前往设置页添加")
    return AIClient(provider)
