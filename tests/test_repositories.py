import pytest

from app.database.repositories import TransactionRepository, UserRepository
from app.exceptions import ValidationError
from app.models import Expense, Income, User


def make_user(users, name):
    return users.add(User.register(name, "password123"))


def test_user_roundtrip_and_duplicate(db):
    users = UserRepository(db)
    saved = make_user(users, "alice")
    assert saved.id is not None
    assert users.get_by_username("alice").check_password("password123")
    with pytest.raises(ValidationError):
        make_user(users, "alice")


def test_transactions_are_scoped_per_user(db):
    users, txs = UserRepository(db), TransactionRepository(db)
    alice, bob = make_user(users, "alice"), make_user(users, "bobby")
    saved = txs.add(Expense(alice.id, 50, "milk tea", "Food", tx_date="2026-11-03"))
    txs.add(Income(alice.id, 1000, "allowance", "Allowance", tx_date="2026-11-01"))

    assert len(txs.list_for_user(alice.id)) == 2
    assert txs.list_for_user(bob.id) == []
    assert txs.delete(bob.id, saved.id) is False  # cannot delete someone else's record
    assert txs.delete(alice.id, saved.id) is True


def test_month_filter(db):
    users, txs = UserRepository(db), TransactionRepository(db)
    alice = make_user(users, "alice")
    txs.add(Expense(alice.id, 10, "a", "Food", tx_date="2026-10-30"))
    txs.add(Expense(alice.id, 20, "b", "Food", tx_date="2026-11-02"))
    assert [t.amount for t in txs.list_for_user(alice.id, "2026-11")] == [20.0]


def test_sql_injection_text_is_stored_as_plain_text(db):
    users, txs = UserRepository(db), TransactionRepository(db)
    alice = make_user(users, "alice")
    txs.add(Expense(alice.id, 10, "x'); DROP TABLE transactions;--", "Other"))
    assert txs.count() == 1
