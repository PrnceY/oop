"""Personal Expense Tracker: Flask app factory that wires every layer together."""
import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask

from app.ai.categorizer import ExpenseCategorizer
from app.ai.recommender import (
    CompositeRecommender,
    ForecastRecommender,
    RuleBasedRecommender,
)
from app.database.db import Database
from app.database.repositories import TransactionRepository, UserRepository
from app.security import csrf_token, verify_csrf
from app.services.auth_service import AuthService
from app.services.tracker_service import TrackerService


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.update(
        # Set SECRET_KEY in the environment for a stable key between restarts.
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / "expense_tracker.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    )
    if config:
        app.config.update(config)

    # Build the object graph: Database -> Repositories -> Services.
    db = Database(app.config["DATABASE"])
    db.init_schema()
    users = UserRepository(db)
    transactions = TransactionRepository(db)
    categorizer = ExpenseCategorizer().train()
    recommender = CompositeRecommender([RuleBasedRecommender(), ForecastRecommender()])

    app.extensions["auth"] = AuthService(users)
    app.extensions["tracker"] = TrackerService(transactions, users, categorizer, recommender)

    app.jinja_env.globals["csrf_token"] = csrf_token
    app.jinja_env.filters["peso"] = lambda value: f"₱{value:,.2f}"
    app.before_request(verify_csrf)

    from app.routes import auth, main

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    return app
