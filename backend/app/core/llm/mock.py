"""离线演示用的 Mock LLM：无需 API Key，返回可预测的模板文本，保证框架开箱可跑。"""
import re

from .base import BaseLLM, LLMResult

# 简易多语言占位翻译（仅用于演示，非真实翻译）
_MOCK_TRANSLATIONS = {
    "en": "This is a sample English rendering of your content for international trade.",
    "fr": "Ceci est un exemple de traduction française de votre contenu.",
    "es": "Esta es una traducción de ejemplo en español de su contenido.",
    "ar": "هذه ترجمة عربية نموذجية لمحتواك التجاري.",
    "ja": "これは貴社コンテンツの日本語サンプル翻訳です。",
    "ko": "이것은 귀사 콘텐츠의 한국어 샘플 번역입니다.",
    "de": "Dies ist eine deutsche Beispielübersetzung Ihres Inhalts.",
    "ru": "Это примерный русский перевод вашего контента.",
    "pt": "Esta é uma tradução de exemplo em português do seu conteúdo.",
    "it": "Questa è una traduzione di esempio in italiano del tuo contenuto.",
}


def _extract_lang(prompt: str) -> str:
    m = re.search(r"目标语言[:：]\s*([A-Za-z]{2,3})", prompt)
    return m.group(1).lower() if m else "en"


def _render_copy(task: str, prompt: str) -> str:
    m = re.search(r"商品名称[:：]\s*(.+)", prompt)
    product = m.group(1).strip() if m else "商品"
    sp = re.search(r"卖点关键词[:：]\s*(.+)", prompt)
    selling = sp.group(1).strip() if sp else "高品质、工厂直供"
    mk = re.search(r"目标市场[:：]\s*(.+)", prompt)
    market = mk.group(1).strip() if mk else "欧美"

    if task == "copywriting_title":
        return f"Premium {product} — 跨境热销爆款 · 工厂直供"
    if task == "copywriting_ad":
        return (
            f"🔥 全球热卖中！{product}\n"
            f"核心卖点：{selling}\n"
            f"🚚 全球直邮 · 极速发货 · 无忧售后，立即抢购！"
        )
    if task == "copywriting_keywords":
        return "cross-border, wholesale, best seller, factory direct, hot sale, free shipping"
    # 默认商品描述
    return (
        f"【Mock 商品描述 · {market}】\n\n"
        f"{product} —— 精选优质材料，匠心工艺，通过国际质检认证。\n\n"
        f"✨ 核心卖点：{selling}\n"
        f"📦 支持批发定制、全球直邮、快速发货\n"
        f"🛡️ 售后无忧，7×24 客服响应\n\n"
        f"适用于 {market} 市场的专业之选。"
    )


class MockLLM(BaseLLM):
    name = "mock"

    def generate(self, prompt, system=None, task=None, **kwargs):
        task = task or "chat"

        if task == "translation":
            content = _MOCK_TRANSLATIONS.get(_extract_lang(prompt), _MOCK_TRANSLATIONS["en"])
        elif task and task.startswith("copywriting"):
            content = _render_copy(task, prompt)
        else:
            content = (
                "【Mock 客服回复】\n"
                "当前为离线演示模式，已模拟完成意图识别与知识检索流程。\n"
                "配置 LLM_PROVIDER / LLM_API_KEY 后，将基于企业知识库返回真实生成答案。"
            )

        return LLMResult(
            content=content,
            usage={
                "prompt_tokens": max(1, len(prompt) // 4),
                "completion_tokens": max(1, len(content) // 4),
            },
        )

    def generate_stream(self, prompt, system=None, task=None, **kwargs):
        """按句子切分模拟流式输出，便于前端联调打字机效果。"""
        content = self.generate(prompt, system=system, task=task, **kwargs).content
        for piece in re.split(r"(?<=[。！？\n])", content):
            if piece:
                yield piece

    def stream_events(self, prompt, system=None, task=None, **kwargs):
        """Mock 无推理过程，全部作为 content 事件逐步产出。"""
        content = self.generate(prompt, system=system, task=task, **kwargs).content
        for piece in re.split(r"(?<=[。！？\n])", content):
            if piece:
                yield ("content", piece)
