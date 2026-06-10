"""Authentication — Supabase JWT stored in Flask session.

Mirrors the Reflex app's behavior: sign_in -> store token/uid/email,
auth errors -> clear session -> redirect to login.

Token lifecycle:
  - Supabase access tokens expire in ~3600 s.
  - before_app_request checks expiry 5 min early and silently refreshes.
  - If refresh fails (or no token), session is cleared; HTMX requests get
    HX-Redirect so the full page navigates to /login rather than injecting
    the login page into a panel target.
"""

import time
from functools import wraps

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, current_app, make_response)

from . import db as DB
from .seed import SAMPLE_SESSION

bp = Blueprint("auth", __name__)

_REFRESH_BEFORE_SECS = 300   # refresh when < 5 min remain


def _htmx_or_redirect(location: str):
    """Full-page redirect for both HTMX and plain requests."""
    if request.headers.get("HX-Request") == "true":
        resp = make_response("", 200)
        resp.headers["HX-Redirect"] = location
        return resp
    return redirect(location)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_app.config["DEV_SEED"]:
            session.update(SAMPLE_SESSION)
            return view(*args, **kwargs)
        if not session.get("access_token"):
            return _htmx_or_redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


@bp.before_app_request
def _refresh_token_if_needed():
    """Proactively refresh the Supabase access token before it expires."""
    if current_app.config.get("DEV_SEED"):
        return
    # Skip auth/static endpoints — they don't need a valid token
    if request.endpoint in ("auth.login", "auth.signup", "auth.logout", None):
        return
    if request.path.startswith("/static/"):
        return

    access_token  = session.get("access_token")
    refresh_token = session.get("refresh_token")
    expires_at    = session.get("expires_at", 0)

    if not access_token:
        return  # login_required will handle the redirect

    # Token is still fresh — nothing to do
    if expires_at and time.time() < expires_at - _REFRESH_BEFORE_SECS:
        return

    # Token is expired or within the refresh window — try to refresh
    if refresh_token:
        try:
            result = DB.refresh_session(refresh_token)
            session["access_token"]  = result["access_token"]
            session["refresh_token"] = result["refresh_token"]
            session["expires_at"]    = result["expires_at"]
            return
        except Exception:
            pass

    # Could not refresh — force re-login
    session.clear()
    return _htmx_or_redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            res = DB.sign_in(request.form["email"], request.form["password"])
            session.permanent        = bool(request.form.get("remember_me"))
            session["access_token"]  = res["access_token"]
            session["refresh_token"] = res["refresh_token"]
            session["expires_at"]    = res["expires_at"]
            session["user_id"]       = res["user_id"]
            session["email"]         = res.get("user_email", request.form["email"])
            return redirect(url_for("panels.buckets"))
        except Exception as e:
            from flask import flash
            flash(str(e), "error")
    return render_template("login.html", mode="login")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        from flask import flash
        pw = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if pw != confirm:
            flash("Passwords don't match.", "error")
            return render_template("login.html", mode="signup")
        try:
            DB.sign_up(request.form["email"], pw)
            flash("Account created — please sign in.", "ok")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(str(e), "error")
    return render_template("login.html", mode="signup")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
