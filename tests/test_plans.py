from app.core.plans import PlanCode, get_plan


def test_free_plan_limit() -> None:
    plan = get_plan(PlanCode.FREE)
    assert plan.daily_limit == 2
    assert plan.price_rub == 0
    assert plan.price_stars is None


def test_paid_plan_prices() -> None:
    assert get_plan("pro").price_rub == 499
    assert get_plan("pro").price_stars == 199
    assert get_plan("business").price_rub == 999
    assert get_plan("business").price_stars == 499
