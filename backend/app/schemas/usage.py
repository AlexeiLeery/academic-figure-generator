from pydantic import BaseModel


class UsageSummary(BaseModel):
    billing_period: str
    claude_tokens_used: int
    claude_calls: int
    nanobanana_images: int
    estimated_cost_usd: float
    quota_claude_remaining: int
    quota_images_remaining: int


class UsageHistoryPoint(BaseModel):
    date: str
    claude_tokens: int
    nanobanana_images: int
    cost_usd: float


class UsageBreakdown(BaseModel):
    api_name: str
    total_calls: int
    success_count: int
    failure_count: int
    total_tokens: int | None
    total_cost_usd: float
    avg_duration_ms: float


class UsageHistoryResponse(BaseModel):
    period: str
    data: list[UsageHistoryPoint]
