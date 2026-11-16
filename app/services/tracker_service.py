"""Business logic that ties models, repositories and the AI components together."""
from collections import defaultdict
from datetime import date

from app.ai.categorizer import ExpenseCategorizer
from app.ai.recommender import BudgetRecommender
from app.database.repositories import TransactionRepository, UserRepository
from app.exceptions import ValidationError
from app.models.transaction import TransactionFactory

DEFAULT_INCOME_CATEGORY = "Allowance"


class TrackerService:
    def __init__(
        self,
        transactions: TransactionRepository,
        users: UserRepository,
        categorizer: ExpenseCategorizer,
        recommender: BudgetRecommender,
    ):
        self._transactions = transactions
        self._users = users
        self._categorizer = categorizer
        self._recommender = recommender

    def suggest_category(self, description):
        return self._categorizer.predict(description)

    def add_transaction(self, user_id, kind, amount, description, category=None, tx_date=None):
        if not category:
            if kind == "expense":
                category, _ = self._categorizer.predict(description)  # ML picks it
            else:
                category = DEFAULT_INCOME_CATEGORY
        tx = TransactionFactory.create(
            kind,
            user_id=user_id,
            amount=amount,
            description=description,
            category=category,
            tx_date=tx_date or date.today(),
        )
        return self._transactions.add(tx)

    def list_transactions(self, user_id, month=None):
        return self._transactions.list_for_user(user_id, month)

    def delete_transaction(self, user_id, tx_id) -> bool:
        return self._transactions.delete(user_id, tx_id)

    def set_budget(self, user_id, monthly_budget):
        user = self._users.get_by_id(user_id)
        if user is None:
            raise ValidationError("User not found.")
        user.monthly_budget = monthly_budget  # validated by the model
        self._users.update_budget(user_id, user.monthly_budget)

    def summary(self, user_id, month=None) -> dict:
        balance = income = expense = 0.0
        by_category = defaultdict(float)
        for tx in self._transactions.list_for_user(user_id, month):
            balance = tx.apply_to_balance(balance)
            if tx.kind == "income":
                income += tx.amount
            else:
                expense += tx.amount
                by_category[tx.category] += tx.amount
        user = self._users.get_by_id(user_id)
        budget = user.monthly_budget if user else 0.0
        return {
            "income": income,
            "expense": expense,
            "balance": balance,
            "budget": budget,
            "budget_remaining": (budget - expense) if budget > 0 else None,
            "by_category": sorted(by_category.items(), key=lambda kv: kv[1], reverse=True),
        }

    def recommendations(self, user_id, today=None) -> list:
        today = today or date.today()
        month = today.strftime("%Y-%m")
        expenses = [t for t in self._transactions.list_for_user(user_id, month) if t.kind == "expense"]
        user = self._users.get_by_id(user_id)
        budget = user.monthly_budget if user else 0.0
        return self._recommender.recommend(expenses, budget, today)
