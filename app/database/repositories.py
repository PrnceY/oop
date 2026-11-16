"""Repositories: the only place that talks SQL.

Every query uses parameters (no string-built SQL), and every transaction query
is filtered by user_id so one user can never read or delete another user's data.
"""
import sqlite3
from abc import ABC, abstractmethod

from app.exceptions import ValidationError
from app.models.transaction import Transaction, TransactionFactory
from app.models.user import User


class BaseRepository(ABC):
    def __init__(self, db):
        self._db = db

    @property
    @abstractmethod
    def table(self) -> str:
        """Name of the table this repository manages."""

    def count(self) -> int:
        with self._db.connection() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {self.table}").fetchone()[0]


class UserRepository(BaseRepository):
    @property
    def table(self) -> str:
        return "users"

    @staticmethod
    def _to_user(row) -> User:
        return User(row["username"], row["password_hash"], row["monthly_budget"], row["id"])

    def add(self, user: User) -> User:
        try:
            with self._db.connection() as conn:
                cur = conn.execute(
                    "INSERT INTO users (username, password_hash, monthly_budget) VALUES (?, ?, ?)",
                    (user.username, user.export_hash(), user.monthly_budget),
                )
                new_id = cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValidationError("That username is already taken.")
        return User(user.username, user.export_hash(), user.monthly_budget, new_id)

    def get_by_username(self, username):
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return self._to_user(row) if row else None

    def get_by_id(self, user_id):
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._to_user(row) if row else None

    def update_budget(self, user_id, monthly_budget):
        with self._db.connection() as conn:
            conn.execute("UPDATE users SET monthly_budget = ? WHERE id = ?", (monthly_budget, user_id))


class TransactionRepository(BaseRepository):
    @property
    def table(self) -> str:
        return "transactions"

    def add(self, tx: Transaction) -> Transaction:
        with self._db.connection() as conn:
            cur = conn.execute(
                "INSERT INTO transactions (user_id, kind, amount, description, category, tx_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (tx.user_id, tx.kind, tx.amount, tx.description, tx.category, tx.tx_date.isoformat()),
            )
            new_id = cur.lastrowid
        return TransactionFactory.create(
            tx.kind,
            user_id=tx.user_id,
            amount=tx.amount,
            description=tx.description,
            category=tx.category,
            tx_date=tx.tx_date,
            tx_id=new_id,
        )

    def list_for_user(self, user_id, month=None):
        """All of a user's transactions, newest first. month is 'YYYY-MM' or None."""
        sql = "SELECT * FROM transactions WHERE user_id = ?"
        params = [user_id]
        if month:
            sql += " AND substr(tx_date, 1, 7) = ?"
            params.append(month)
        sql += " ORDER BY tx_date DESC, id DESC"
        with self._db.connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [TransactionFactory.from_row(r) for r in rows]

    def delete(self, user_id, tx_id) -> bool:
        with self._db.connection() as conn:
            cur = conn.execute(
                "DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id)
            )
            return cur.rowcount > 0
