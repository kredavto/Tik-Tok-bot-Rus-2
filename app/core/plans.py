from dataclasses import dataclass
from enum import StrEnum


class PlanCode(StrEnum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


@dataclass(frozen=True)
class Plan:
    code: PlanCode
    title: str
    price_rub: int
    daily_limit: int


PLANS: dict[PlanCode, Plan] = {
    PlanCode.FREE: Plan(PlanCode.FREE, "FREE", 0, 2),
    PlanCode.PRO: Plan(PlanCode.PRO, "PRO", 499, 5),
    PlanCode.BUSINESS: Plan(PlanCode.BUSINESS, "BUSINESS", 999, 10),
}


def get_plan(code: str | PlanCode | None) -> Plan:
    if not code:
        return PLANS[PlanCode.FREE]
    try:
        return PLANS[PlanCode(str(code))]
    except ValueError:
        return PLANS[PlanCode.FREE]
