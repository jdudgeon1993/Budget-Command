"""Request-scoped data loading + view-model builders.

Pulls the canonical data dict (real Supabase via db.load_all, or dev seed),
then shapes it into the small dicts the templates render. All money math goes
through formulas.py — never reimplemented in templates or JS.
"""

import calendar
from flask import g, session, current_app

from . import db as DB
from . import formulas as F
from .seed import sample_data


# ── Loading ───────────────────────────────────────────────────────────────────

def load_data() -> dict:
    """Canonical data dict for this request (cached on g)."""
    if "data" in g:
        return g.data
    if current_app.config["DEV_SEED"]:
        g.data = sample_data()
    else:
        g.data = DB.load_all(session.get("user_id", ""), session.get("access_token", ""))
    return g.data


def active_mid() -> str:
    return session.get("active_mid") or F.current_month_id()


def active_month(data: dict) -> dict:
    mid = active_mid()
    for m in data.get("months", []):
        if m["id"] == mid:
            return m
    return {"id": mid, "allocations": {}, "budgets": {}}


def month_label(mid: str) -> str:
    y, m0 = F.parse_month_id(mid)
    return f"{calendar.month_name[m0 + 1]} {y}"


# ── Shell view-model (sidebar RTS, header, month) ─────────────────────────────

def shell_ctx(active_panel: str = "") -> dict:
    data = load_data()
    mid = active_mid()
    month = active_month(data)
    accounts = data.get("accounts", [])
    months = data.get("months", [])
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    txs = data.get("txs", [])

    rts = F.ready_to_spend(month, months, accounts, buckets, txs)
    income = F.month_income(mid, txs, accounts)
    allocated = F.total_allocated(month, buckets)
    spent = sum(F.b_spent(mid, b["id"], txs) for b in buckets)
    pct = min(100, round((allocated / income) * 100)) if income else 0

    return {
        "active_panel": active_panel,
        "user_email": session.get("email", ""),
        "month_label": month_label(mid),
        "rts": rts,
        "income": income,
        "allocated": allocated,
        "spent": spent,
        "pct": pct,
        "unhomed": max(rts, 0),
    }


# ── Buckets panel view-model ──────────────────────────────────────────────────

def bucket_rows():
    """Category-grouped bucket rows with alloc/budget/spent/left + status."""
    data = load_data()
    mid = active_mid()
    month = active_month(data)
    months = data.get("months", [])
    txs = data.get("txs", [])
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))

    groups = []
    attention = []
    for cat in cats:
        rows = []
        cat_alloc = cat_budget = 0.0
        cat_bkts = sorted(
            [b for b in buckets if b.get("catId") == cat["id"]],
            key=lambda b: b.get("order", 0),
        )
        for b in cat_bkts:
            alloc = F.b_alloc(month, b["id"])
            budget = F.b_budget(month, b["id"])
            spent = F.b_spent(mid, b["id"], txs)
            left = F.bucket_available(b, month, months, txs)
            over = max(spent - budget, 0) if budget else max(spent - alloc, 0)
            needed = max(budget - alloc, 0)
            if over > 0:
                status, pill = "over", f"Over ${over:,.0f}"
            elif needed > 0:
                status, pill = "partial", f"−${needed:,.0f}"
            elif budget and spent >= budget:
                status, pill = "funded", "Paid"
            else:
                status, pill = "funded", "Funded"
            cat_alloc += alloc
            cat_budget += budget
            row = {
                "id": b["id"], "name": b["name"], "type": b.get("type", "expense"),
                "alloc": alloc, "budget": budget, "spent": spent, "left": left,
                "status": status, "pill": pill, "needed": needed,
            }
            rows.append(row)
            if status in ("partial", "over"):
                attention.append({**row, "cat_color": cat.get("color", "#888")})
        groups.append({
            "id": cat["id"], "name": cat["name"], "color": cat.get("color", "#888"),
            "alloc": cat_alloc, "budget": cat_budget,
            "pct": min(100, round((cat_alloc / cat_budget) * 100)) if cat_budget else 0,
            "buckets": rows,
        })
    return {"groups": groups, "attention": attention, "cats": cats}
