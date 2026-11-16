"""Budget recommendations.

These are AI (rule-based + statistical projection), not machine learning:
nothing here learns from data. They sit behind one abstract interface so a
trained model can be added later as another BudgetRecommender subclass.

OOP: abstraction (BudgetRecommender), inheritance, polymorphism
(each subclass implements recommend()), composition (CompositeRecommender).
"""
import calendar
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date


class BudgetRecommender(ABC):
    @abstractmethod
    def recommend(self, expenses, monthly_budget: float, today: date) -> list:
        """Return a list of advice strings for this month's expenses."""


class RuleBasedRecommender(BudgetRecommender):
    """Fixed rules about category share and budget usage."""

    CATEGORY_SHARE_LIMIT = 0.40
    PACE_TOLERANCE = 0.15

    def recommend(self, expenses, monthly_budget, today):
        tips = []
        if monthly_budget <= 0:
            tips.append("Set a monthly budget so the tracker can give you budget advice.")

        total = sum(e.amount for e in expenses)
        if total == 0:
            return tips or ["No expenses recorded yet this month."]

        by_category = defaultdict(float)
        for e in expenses:
            by_category[e.category] += e.amount
        top_category, top_amount = max(by_category.items(), key=lambda kv: kv[1])
        share = top_amount / total
        if share > self.CATEGORY_SHARE_LIMIT and len(by_category) > 1:
            tips.append(
                f"{top_category} is {share:.0%} of your spending. "
                f"Try to keep any single category under {self.CATEGORY_SHARE_LIMIT:.0%}."
            )

        if monthly_budget > 0:
            used = total / monthly_budget
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            month_progress = today.day / days_in_month
            if used >= 1:
                tips.append("You have already used your whole monthly budget.")
            elif used > month_progress + self.PACE_TOLERANCE:
                tips.append(
                    f"You used {used:.0%} of your budget but only {month_progress:.0%} "
                    "of the month has passed. Slow down on non-essentials."
                )

        return tips or ["Your spending looks balanced so far. Keep it up!"]


class ForecastRecommender(BudgetRecommender):
    """Projects month-end spending from the average daily spend so far."""

    def recommend(self, expenses, monthly_budget, today):
        if monthly_budget <= 0 or not expenses:
            return []
        spent = sum(e.amount for e in expenses)
        daily = spent / max(today.day, 1)
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        projected = daily * days_in_month
        if projected > monthly_budget:
            runout_day = min(int(monthly_budget / daily) if daily else days_in_month, days_in_month)
            return [
                f"At about ₱{daily:,.0f} per day you are on track to spend ₱{projected:,.0f} "
                f"this month, ₱{projected - monthly_budget:,.0f} over budget. "
                f"Your budget may run out around day {runout_day}."
            ]
        return [
            f"On track: projected month-end spending is ₱{projected:,.0f} "
            f"of your ₱{monthly_budget:,.0f} budget."
        ]


class CompositeRecommender(BudgetRecommender):
    """Runs several recommenders and combines their advice."""

    def __init__(self, recommenders):
        self._recommenders = list(recommenders)

    def recommend(self, expenses, monthly_budget, today):
        tips = []
        for recommender in self._recommenders:
            tips.extend(recommender.recommend(expenses, monthly_budget, today))
        return tips
