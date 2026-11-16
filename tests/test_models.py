from datetime import date

import pytest

from app.exceptions import ValidationError
from app.models import Expense, Income, Transaction, TransactionFactory, User


def test_abstraction_transaction_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Transaction(1, 10, "x", "Other")


def test_inheritance():
    assert issubclass(Income, Transaction)
    assert issubclass(Expense, Transaction)


def test_polymorphism_signed_amount_and_balance():
    items = [Income(1, 500, "allowance", "Allowance"), Expense(1, 120, "jeep fare", "Transportation")]
    balance = 0.0
    for tx in items:  # same call, different behavior per subclass
        balance = tx.apply_to_balance(balance)
    assert balance == 380.0
    assert items[0].describe().startswith("Received")
    assert items[1].describe().startswith("Spent")


def test_encapsulation_validates_amount_and_category():
    tx = Expense(1, 50, "milk tea", "Food")
    with pytest.raises(ValidationError):
        tx.amount = -5
    with pytest.raises(ValidationError):
        tx.amount = "abc"
    with pytest.raises(ValidationError):
        tx.category = "Salary"  # income-only category
    with pytest.raises(AttributeError):
        tx.id = 99  # read-only property
    assert tx.amount == 50.0


def test_description_required_and_date_parsing():
    with pytest.raises(ValidationError):
        Expense(1, 10, "   ", "Food")
    tx = Expense(1, 10, "snack", "Food", tx_date="2026-11-01")
    assert tx.tx_date == date(2026, 11, 1)
    with pytest.raises(ValidationError):
        Expense(1, 10, "snack", "Food", tx_date="not-a-date")


def test_factory():
    assert isinstance(TransactionFactory.create("income", user_id=1, amount=1, description="a", category="Gift"), Income)
    with pytest.raises(ValidationError):
        TransactionFactory.create("transfer", user_id=1, amount=1, description="a", category="Gift")


def test_user_hashes_password_and_validates():
    user = User.register("prnce_01", "supersecret1")
    assert user.check_password("supersecret1")
    assert not user.check_password("wrong")
    assert "supersecret1" not in user.export_hash()
    with pytest.raises(ValidationError):
        User.register("ab", "supersecret1")
    with pytest.raises(ValidationError):
        User.register("validname", "short")
