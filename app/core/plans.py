from dataclasses import dataclass
from enum import StrEnum


class PlanCode(StrEnum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    UNLIMIT = "unlimit"


@dataclass(frozen=True)
class Plan:
    code: PlanCode
    title: str
    price_rub: int
    price_stars: int | None
    daily_limit: int


PLANS: dict[PlanCode, Plan] = {
    PlanCode.FREE: Plan(PlanCode.FREE, "FREE", 0, None, 2),
    PlanCode.PRO: Plan(PlanCode.PRO, "PRO", 499, 199, 5),
    PlanCode.BUSINESS: Plan(PlanCode.BUSINESS, "BUSINESS", 999, 499, 10),
    PlanCode.UNLIMIT: Plan(PlanCode.UNLIMIT, "UNLIMIT", 1999, 999, 0),
}


def get_plan(code: str | PlanCode | None) -> Plan:
    if not code:
        return PLANS[PlanCode.FREE]
    try:
        return PLANS[PlanCode(str(code))]
    except ValueError:
        return PLANS[PlanCode.FREE]
