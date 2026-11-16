import re
from datetime import date

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for

from app.exceptions import ValidationError
from app.models.categories import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from app.security import login_required

bp = Blueprint("main", __name__)

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _tracker():
    return current_app.extensions["tracker"]


@bp.get("/")
@login_required
def dashboard():
    user_id = session["user_id"]
    month = request.args.get("month", "")
    if not MONTH_PATTERN.match(month):
        month = date.today().strftime("%Y-%m")
    tracker = _tracker()
    return render_template(
        "dashboard.html",
        month=month,
        today=date.today().isoformat(),
        summary=tracker.summary(user_id, month),
        transactions=tracker.list_transactions(user_id, month),
        recommendations=tracker.recommendations(user_id),
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
    )


@bp.post("/transactions")
@login_required
def add_transaction():
    form = request.form
    try:
        _tracker().add_transaction(
            session["user_id"],
            kind=form.get("kind", ""),
            amount=form.get("amount", ""),
            description=form.get("description", ""),
            category=form.get("category") or None,
            tx_date=form.get("tx_date") or None,
        )
        flash("Transaction added.", "ok")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.dashboard"))


@bp.post("/transactions/<int:tx_id>/delete")
@login_required
def delete_transaction(tx_id):
    if _tracker().delete_transaction(session["user_id"], tx_id):
        flash("Transaction deleted.", "ok")
    else:
        flash("Transaction not found.", "error")
    return redirect(url_for("main.dashboard"))


@bp.post("/budget")
@login_required
def set_budget():
    try:
        _tracker().set_budget(session["user_id"], request.form.get("monthly_budget", ""))
        flash("Monthly budget updated.", "ok")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.dashboard"))


@bp.get("/api/suggest-category")
@login_required
def suggest_category():
    category, confidence = _tracker().suggest_category(request.args.get("description", ""))
    return jsonify(category=category, confidence=round(confidence, 2))
