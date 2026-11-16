from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.exceptions import AuthError, ValidationError

bp = Blueprint("auth", __name__)


def _start_session(user):
    session.clear()  # drop any old session data (prevents session fixation)
    session["user_id"] = user.id
    session["username"] = user.username
    session.permanent = True


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            user = current_app.extensions["auth"].register(
                request.form.get("username", ""), request.form.get("password", "")
            )
        except ValidationError as exc:
            flash(str(exc), "error")
        else:
            _start_session(user)
            return redirect(url_for("main.dashboard"))
    return render_template("auth.html", mode="register")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = current_app.extensions["auth"].login(
                request.form.get("username", ""), request.form.get("password", "")
            )
        except AuthError as exc:
            flash(str(exc), "error")
        else:
            _start_session(user)
            return redirect(url_for("main.dashboard"))
    return render_template("auth.html", mode="login")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
