"""Custom exceptions so the layers can report problems without leaking details."""


class ExpenseTrackerError(Exception):
    """Base class for all application errors."""


class ValidationError(ExpenseTrackerError):
    """Raised when user-supplied data is invalid."""


class AuthError(ExpenseTrackerError):
    """Raised when authentication fails."""
