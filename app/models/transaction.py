"""Transaction hierarchy.

OOP concepts shown here:
- Abstraction:    Transaction is an abstract base class; it cannot be instantiated.
- Inheritance:    Income and Expense inherit shared state and behavior from Transaction.
- Polymorphism:   Each subclass implements kind, signed_amount, allowed_categories
                  and describe() in its own way; callers just use a Transaction.
- Encapsulation:  Fields are private (_amount, ...) and only changed through
                  validated properties.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

from app.exceptions import ValidationError
from app.models.categories import EXPENSE_CATEGORIES, INCOME_CATEGORIES

MAX_DESCRIPTION_LENGTH = 120
MAX_AMOUNT = 10_000_000


class Transaction(ABC):
    """Common data and operations for every kind of money movement."""

    def __init__(self, user_id, amount, description, category, tx_date=None, tx_id=None):
        self._id = tx_id
        self._user_id = user_id
        self._amount = 0.0
        self._description = ""
        self._category = ""
        self._tx_date = date.today()
        # Assigning through the properties runs validation.
        self.amount = amount
        self.description = description
        self.category = category
        self.tx_date = tx_date if tx_date else date.today()

    # ---- abstract operations: every subclass must provide these ----
    @property
    @abstractmethod
    def kind(self) -> str:
        """Short type name stored in the database ('income' or 'expense')."""

    @abstractmethod
    def signed_amount(self) -> float:
        """Amount with its effect on the balance (+ for income, - for expense)."""

    @classmethod
    @abstractmethod
    def allowed_categories(cls) -> tuple:
        """Categories that are valid for this type of transaction."""

    @abstractmethod
    def describe(self) -> str:
        """Human-readable one-line summary."""

    # ---- shared behavior inherited as-is ----
    def apply_to_balance(self, balance: float) -> float:
        return balance + self.signed_amount()

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "kind": self.kind,
            "amount": self._amount,
            "signed_amount": self.signed_amount(),
            "description": self._description,
            "category": self._category,
            "tx_date": self._tx_date.isoformat(),
        }

    # ---- encapsulated state ----
    @property
    def id(self):
        return self._id

    @property
    def user_id(self):
        return self._user_id

    @property
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, value):
        try:
            number = round(float(value), 2)
        except (TypeError, ValueError):
            raise ValidationError("Amount must be a number.")
        if number != number or number in (float("inf"), float("-inf")):
            raise ValidationError("Amount must be a real number.")
        if number <= 0:
            raise ValidationError("Amount must be greater than zero.")
        if number > MAX_AMOUNT:
            raise ValidationError("Amount is too large.")
        self._amount = number

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value):
        text = (value or "").strip()
        if not text:
            raise ValidationError("Description is required.")
        if len(text) > MAX_DESCRIPTION_LENGTH:
            raise ValidationError(f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.")
        self._description = text

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value):
        if value not in self.allowed_categories():
            raise ValidationError(f"'{value}' is not a valid {self.kind} category.")
        self._category = value

    @property
    def tx_date(self) -> date:
        return self._tx_date

    @tx_date.setter
    def tx_date(self, value):
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, str):
            try:
                value = date.fromisoformat(value)
            except ValueError:
                raise ValidationError("Date must be in YYYY-MM-DD format.")
        if not isinstance(value, date):
            raise ValidationError("Invalid date.")
        self._tx_date = value

    def __repr__(self):
        return f"<{type(self).__name__} {self._amount:.2f} {self._category} {self._tx_date}>"


class Income(Transaction):
    """Money coming in (allowance, part-time pay, gifts)."""

    @property
    def kind(self) -> str:
        return "income"

    def signed_amount(self) -> float:
        return self._amount

    @classmethod
    def allowed_categories(cls) -> tuple:
        return INCOME_CATEGORIES

    def describe(self) -> str:
        return f"Received ₱{self._amount:,.2f} ({self._category}): {self._description}"


class Expense(Transaction):
    """Money going out."""

    @property
    def kind(self) -> str:
        return "expense"

    def signed_amount(self) -> float:
        return -self._amount

    @classmethod
    def allowed_categories(cls) -> tuple:
        return EXPENSE_CATEGORIES

    def describe(self) -> str:
        return f"Spent ₱{self._amount:,.2f} on {self._category}: {self._description}"


class TransactionFactory:
    """Creates the right Transaction subclass from a type name (Factory pattern)."""

    _registry = {
        "income": Income,
        "expense": Expense,
    }

    @classmethod
    def create(cls, kind, **kwargs) -> Transaction:
        klass = cls._registry.get(kind)
        if klass is None:
            raise ValidationError("Unknown transaction type.")
        return klass(**kwargs)

    @classmethod
    def from_row(cls, row) -> Transaction:
        return cls.create(
            row["kind"],
            user_id=row["user_id"],
            amount=row["amount"],
            description=row["description"],
            category=row["category"],
            tx_date=row["tx_date"],
            tx_id=row["id"],
        )
