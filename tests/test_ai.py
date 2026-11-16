from datetime import date

import pytest

from app.ai import (
    BudgetRecommender,
    CompositeRecommender,
    ExpenseCategorizer,
    ForecastRecommender,
    RuleBasedRecommender,
)
from app.models import Expense
from app.models.categories import EXPENSE_CATEGORIES


@pytest.fixture(scope="module")
def categorizer():
    return ExpenseCategorizer().train()


@pytest.mark.parametrize(
    "text, expected",
    [
        ("jeep fare", "Transportation"),
        ("milk tea", "Food"),
        ("netflix", "Entertainment"),
        ("wifi bill", "Bills & Load"),
        ("printing thesis", "School"),
    ],
)
def test_categorizer_predictions(categorizer, text, expected):
    assert categorizer.predict(text)[0] == expected


def test_categorizer_labels_are_valid_categories(categorizer):
    category, confidence = categorizer.predict("something totally unrelated qzxv")
    assert category in EXPENSE_CATEGORIES
    assert 0.0 <= confidence <= 1.0


def test_categorizer_requires_training():
    with pytest.raises(RuntimeError):
        ExpenseCategorizer().predict("milk tea")


def test_recommender_is_abstract():
    with pytest.raises(TypeError):
        BudgetRecommender()


def _expenses(*pairs):
    return [Expense(1, amount, "x", category) for category, amount in pairs]


def test_rule_based_flags_dominant_category_and_pace():
    expenses = _expenses(("Food", 900), ("Transportation", 100))
    tips = RuleBasedRecommender().recommend(expenses, 1500, date(2026, 11, 10))
    assert any("Food" in t for t in tips)
    assert any("budget" in t.lower() for t in tips)


def test_forecast_warns_when_over_budget():
    expenses = _expenses(("Food", 1000))
    tips = ForecastRecommender().recommend(expenses, 2000, date(2026, 11, 10))
    assert "over budget" in tips[0]


def test_composite_combines_recommenders():
    expenses = _expenses(("Food", 500), ("School", 400))
    combined = CompositeRecommender([RuleBasedRecommender(), ForecastRecommender()])
    assert len(combined.recommend(expenses, 3000, date(2026, 11, 15))) >= 2
