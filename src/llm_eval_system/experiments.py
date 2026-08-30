import hashlib
from dataclasses import dataclass
from typing import Literal


Variant = Literal["A", "B"]


@dataclass(frozen=True)
class Experiment:
    name: str
    variant_b_percent: int
    salt: str

    def __post_init__(self) -> None:
        if not 0 <= self.variant_b_percent <= 100:
            raise ValueError("variant_b_percent must be between 0 and 100")
        if not self.salt:
            raise ValueError("salt must not be empty")

    def assign(self, subject_id: str) -> Variant:
        """Stable, cross-process assignment; never use Python's randomized hash()."""
        key = f"{self.salt}:{self.name}:{subject_id}".encode()
        bucket = int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % 100
        return "B" if bucket < self.variant_b_percent else "A"


PROMPTS: dict[str, dict[Variant, str]] = {
    "customer_service": {
        "A": "你是专业客服。依据上下文准确回答；不知道时明确说明并建议转人工。",
        "B": "你是专业客服。先识别用户目标，再依据上下文给出简洁、可执行的答案；不得编造政策或订单信息，不确定时转人工。",
    },
    "operations_agent": {
        "A": "你是 AI 运营助理。根据上下文完成任务并给出结果。",
        "B": "你是审慎的 AI 运营 Agent。先复述目标和约束，再提出可验证的执行方案；涉及发布、付款、删除或外发时只生成草案并请求确认。",
    },
}
