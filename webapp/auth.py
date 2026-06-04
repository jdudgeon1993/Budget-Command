"""Authentication — Supabase JWT stored in Flask session.

Mirrors the Reflex app's behavior: sign_in -> store token/uid/email,
auth errors -> clear session -> redirect to login.
"""

from functools import wraps
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, current_app, flash)

from . import db as DB
from .seed import SAMPLE_SESSION

bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_app.config["DEV_SEED"]:
            session.update(SAMPLE_SESSION)
            return view(*args, **kwargs)
        if not session.get("access_token"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            res = DB.sign_in(request.form["email"], request.form["password"])
            session["access_token"] = res["access_token"]
            session["user_id"] = res["user_id"]
            session["email"] = res.get("user_email", request.form["email"])
            return redirect(url_for("panels.buckets"))
        except Exception as e:
            flash(str(e), "error")
    return render_template("login.html", mode="login")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            DB.sign_up(request.form["email"], request.form["password"])
            flash("Account created — please sign in.", "ok")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(str(e), "error")
    return render_template("login.html", mode="signup")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
