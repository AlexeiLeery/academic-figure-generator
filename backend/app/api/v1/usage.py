"""Usage tracking and analytics endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.usage import UsageLog
from app.models.user import User
from app.schemas.usage import (
    UsageBreakdown,
    UsageHistoryPoint,
    UsageHistoryResponse,
    UsageSummary,
)

router = APIRouter(prefix="/usage", tags=["Usage"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _current_billing_period() -> str:
    """Return the current billing period as YYYY-MM."""
    return datetime.utcnow().strftime("%Y-%m")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=UsageSummary)
async def get_usage_summary(
    billing_period: str = Query(default=None, description="Billing period YYYY-MM"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage summary for the given billing period.

    Aggregates Claude token usage, NanoBanana image count, and cost.
    Compares against the user's quota to report remaining allowance.
    """
    period = billing_period or _current_billing_period()

    # Claude usage
    claude_result = await db.execute(
        select(
            func.coalesce(func.sum(UsageLog.input_tokens + UsageLog.output_tokens), 0).label("tokens"),
            func.count().label("calls"),
        )
        .where(
            UsageLog.user_id == user.id,
            UsageLog.billing_period == period,
            UsageLog.api_name == "claude",
        )
    )
    claude_row = claude_result.one()
    claude_tokens_used: int = int(claude_row.tokens)
    claude_calls: int = int(claude_row.calls)

    # NanoBanana usage
    nano_result = await db.execute(
        select(func.count().label("images"))
        .where(
            UsageLog.user_id == user.id,
            UsageLog.billing_period == period,
            UsageLog.api_name == "nanobanana",
            UsageLog.is_success.is_(True),
        )
    )
    nanobanana_images: int = int(nano_result.scalar_one())

    # Total cost
    cost_result = await db.execute(
        select(func.coalesce(func.sum(UsageLog.estimated_cost_usd), 0))
        .where(
            UsageLog.user_id == user.id,
            UsageLog.billing_period == period,
        )
    )
    total_cost: float = float(cost_result.scalar_one())

    return UsageSummary(
        billing_period=period,
        claude_tokens_used=claude_tokens_used,
        claude_calls=claude_calls,
        nanobanana_images=nanobanana_images,
        estimated_cost_usd=round(total_cost, 6),
        quota_claude_remaining=max(0, user.claude_tokens_quota - claude_tokens_used),
        quota_images_remaining=max(0, user.nanobanana_images_quota - nanobanana_images),
    )


@router.get("/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    period: str = Query("daily", description="Aggregation period: daily/weekly/monthly"),
    limit: int = Query(30, ge=1, le=365, description="Number of data points"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage trend data aggregated by day, week, or month."""
    if period == "daily":
        date_trunc = func.date_trunc("day", UsageLog.created_at)
    elif period == "weekly":
        date_trunc = func.date_trunc("week", UsageLog.created_at)
    elif period == "monthly":
        date_trunc = func.date_trunc("month", UsageLog.created_at)
    else:
        date_trunc = func.date_trunc("day", UsageLog.created_at)

    result = await db.execute(
        select(
            date_trunc.label("period_start"),
            func.coalesce(
                func.sum(
                    case(
                        (UsageLog.api_name == "claude", UsageLog.input_tokens + UsageLog.output_tokens),
                        else_=0,
                    )
                ),
                0,
            ).label("claude_tokens"),
            func.count(
                case(
                    (UsageLog.api_name == "nanobanana", UsageLog.id),
                )
            ).label("nanobanana_images"),
            func.coalesce(func.sum(UsageLog.estimated_cost_usd), 0).label("cost"),
        )
        .where(UsageLog.user_id == user.id)
        .group_by("period_start")
        .order_by(func.max(date_trunc).desc())
        .limit(limit)
    )
    rows = result.all()

    data = [
        UsageHistoryPoint(
            date=row.period_start.strftime("%Y-%m-%d") if row.period_start else "",
            claude_tokens=int(row.claude_tokens),
            nanobanana_images=int(row.nanobanana_images),
            cost_usd=round(float(row.cost), 6),
        )
        for row in reversed(rows)  # chronological order
    ]

    return UsageHistoryResponse(period=period, data=data)


@router.get("/breakdown", response_model=list[UsageBreakdown])
async def get_usage_breakdown(
    billing_period: str = Query(default=None, description="Billing period YYYY-MM"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get per-API usage breakdown for the given billing period."""
    period = billing_period or _current_billing_period()

    result = await db.execute(
        select(
            UsageLog.api_name,
            func.count().label("total_calls"),
            func.count(case((UsageLog.is_success.is_(True), 1))).label("success_count"),
            func.count(case((UsageLog.is_success.is_(False), 1))).label("failure_count"),
            func.coalesce(
                func.sum(UsageLog.input_tokens + UsageLog.output_tokens), 0
            ).label("total_tokens"),
            func.coalesce(func.sum(UsageLog.estimated_cost_usd), 0).label("total_cost"),
            func.coalesce(func.avg(UsageLog.request_duration_ms), 0).label("avg_duration"),
        )
        .where(
            UsageLog.user_id == user.id,
            UsageLog.billing_period == period,
        )
        .group_by(UsageLog.api_name)
    )
    rows = result.all()

    return [
        UsageBreakdown(
            api_name=row.api_name,
            total_calls=int(row.total_calls),
            success_count=int(row.success_count),
            failure_count=int(row.failure_count),
            total_tokens=int(row.total_tokens) if row.total_tokens else None,
            total_cost_usd=round(float(row.total_cost), 6),
            avg_duration_ms=round(float(row.avg_duration), 1),
        )
        for row in rows
    ]
