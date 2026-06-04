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


# ── Accounts panel view-model ─────────────────────────────────────────────────

def accounts_view():
    """Account cards (with live balances) + month summary + a grouped ledger."""
    data = load_data()
    mid = active_mid()
    txs = data.get("txs", [])
    accounts = [a for a in data.get("accounts", []) if not a.get("archived")]
    bkt_name = {b["id"]: b["name"] for b in data.get("buckets", [])}

    cards = [{
        "id": a["id"], "name": a["name"], "type": a.get("type", "budget"),
        "color": a.get("color", "#818cf8"),
        "balance": F.acct_balance(a, txs),
    } for a in accounts]

    month_txs = [t for t in txs if t.get("monthId") == mid]
    summary = {
        "income": F.month_income(mid, txs, accounts),
        "spent": sum(t["amount"] for t in month_txs if t.get("type") == "out" and not F.is_scheduled(t)),
        "scheduled": sum(t["amount"] for t in month_txs if t.get("type") == "out" and F.is_scheduled(t)),
        "transferred": sum(t["amount"] for t in month_txs if t.get("type") == "xfr"),
    }

    # Ledger: rows shaped for display, grouped by date (most recent first).
    rows = []
    for t in month_txs:
        ttype = t.get("type", "out")
        amt = float(t.get("amount") or 0)
        if ttype == "in":
            signed, color, pill = amt, "green", "Income"
        elif ttype == "xfr":
            signed, color, pill = -amt, "text2", "Transfer"
        else:
            signed, color, pill = -amt, "red", "Expense"
        rows.append({
            "id": t.get("id", ""), "date": t.get("date", ""),
            "desc": t.get("desc") or "Transaction",
            "pill": pill, "color": color, "signed": signed,
            "category": bkt_name.get(t.get("bucketId"), ""),
            "scheduled": F.is_scheduled(t),
            "type": ttype, "amount": amt,
            "accountId": t.get("accountId", ""),
            "bucketId": t.get("bucketId", ""),
            "toAccountId": t.get("toAccountId", ""),
        })
    rows.sort(key=lambda r: r["date"], reverse=True)

    groups, cur = [], None
    for r in rows:
        if cur is None or cur["date"] != r["date"]:
            cur = {"date": r["date"], "label": _date_label(r["date"]), "net": 0.0, "rows": []}
            groups.append(cur)
        cur["net"] += r["signed"]
        cur["rows"].append(r)

    return {"cards": cards, "summary": summary, "ledger": groups}


def setup_view():
    """Paychecks, categories, and allocation rules for the Setup panel."""
    data = load_data()
    bkt_name = {b["id"]: b["name"] for b in data.get("buckets", [])}
    paychecks = [{
        "id": p["id"], "label": p.get("label", "Paycheck"),
        "amount": float(p.get("amount") or 0),
        "freq": int(p.get("freq") or 14),
        "anchor": p.get("anchorDate") or p.get("anchor_date") or "",
    } for p in data.get("paychecks", [])]
    cats = [{
        "id": c["id"], "name": c["name"], "color": c.get("color", "#888"),
        "count": sum(1 for b in data.get("buckets", []) if b.get("catId") == c["id"]),
    } for c in sorted(data.get("cats", []), key=lambda c: c.get("order", 0))]
    rules = [{
        "id": r["id"], "name": r.get("name", "Rule"),
        "bucket": bkt_name.get(r.get("bucketId"), "—"),
        "value": float(r.get("value") or 0),
        "is_pct": (r.get("value_type") == "pct" or r.get("type") == "pct"),
        "active": r.get("active", True),
    } for r in data.get("allocationRules", [])]
    buckets = [{"id": b["id"], "name": b["name"]}
               for b in data.get("buckets", []) if not b.get("archived")]
    return {"paychecks": paychecks, "cats": cats, "rules": rules, "buckets": buckets,
            "freq_label": {7: "Weekly", 14: "Bi-weekly", 15: "Semi-monthly", 30: "Monthly"}}


def reports_view():
    """Budget-vs-Actual + category spending + month totals + account snapshot."""
    data = load_data()
    mid = active_mid()
    month = active_month(data)
    txs = data.get("txs", [])
    accounts = [a for a in data.get("accounts", []) if not a.get("archived")]
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))

    bva, cat_spend = [], []
    grand_budget = grand_spent = 0.0
    for cat in cats:
        rows, c_budget, c_spent = [], 0.0, 0.0
        for b in sorted([b for b in buckets if b.get("catId") == cat["id"]],
                        key=lambda b: b.get("order", 0)):
            budget = F.b_budget(month, b["id"])
            spent = F.b_spent(mid, b["id"], txs)
            c_budget += budget
            c_spent += spent
            rows.append({"name": b["name"], "budget": budget, "spent": spent,
                         "variance": budget - spent,
                         "pct": min(100, round((spent / budget) * 100)) if budget else 0})
        if rows:
            grand_budget += c_budget
            grand_spent += c_spent
            bva.append({"name": cat["name"], "color": cat.get("color", "#888"),
                        "budget": c_budget, "spent": c_spent,
                        "variance": c_budget - c_spent, "buckets": rows})
            if c_spent > 0:
                cat_spend.append({"name": cat["name"], "color": cat.get("color", "#888"),
                                  "spent": c_spent})

    total_spend = sum(c["spent"] for c in cat_spend) or 1
    for c in cat_spend:
        c["pct"] = round((c["spent"] / total_spend) * 100)
    cat_spend.sort(key=lambda c: c["spent"], reverse=True)

    income = F.month_income(mid, txs, accounts)
    totals = {"income": income, "spent": grand_spent, "budget": grand_budget,
              "net": income - grand_spent}
    snapshot = [{"name": a["name"], "balance": F.acct_balance(a, txs)} for a in accounts]
    net_worth = sum(s["balance"] for s in snapshot)

    return {"bva": bva, "cat_spend": cat_spend, "totals": totals,
            "snapshot": snapshot, "net_worth": net_worth}


def tx_form_ctx():
    """Selects + defaults for the Add/Edit Transaction form."""
    from datetime import date as _date
    data = load_data()
    accounts = [{"id": a["id"], "name": a["name"]}
                for a in data.get("accounts", []) if not a.get("archived")]
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    buckets_by_cat = []
    for c in cats:
        bkts = [{"id": b["id"], "name": b["name"]}
                for b in data.get("buckets", [])
                if b.get("catId") == c["id"] and not b.get("archived")]
        if bkts:
            buckets_by_cat.append({"cat": c["name"], "buckets": bkts})
    return {"accounts": accounts, "buckets_by_cat": buckets_by_cat,
            "today": _date.today().isoformat(), "mid": active_mid()}


def tx_by_id(tid: str) -> dict | None:
    """Find a single transaction by ID from the loaded data."""
    for t in load_data().get("txs", []):
        if t.get("id") == tid:
            return t
    return None


def forecast_data_ctx() -> dict:
    """Real-data seed for the forecast builder (buckets, balances, income)."""
    data = load_data()
    mid = active_mid()
    month = active_month(data)
    accounts = [a for a in data.get("accounts", []) if not a.get("archived")]
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    txs = data.get("txs", [])
    paychecks = data.get("paychecks", [])

    # Cash balance: non-debt accounts
    start_bal = round(sum(
        F.acct_balance(a, txs)
        for a in accounts
        if a.get("type") not in ("debt",)
    ), 2)

    # Monthly income: normalize each paycheck to per-month
    freq_factor = {7: 52/12, 14: 26/12, 15: 2.0, 30: 1.0}
    start_inc = round(sum(
        float(p.get("amount", 0)) * freq_factor.get(int(p.get("freq") or 14), 26/12)
        for p in paychecks
    ), 2)

    pay_freq = "biweekly"
    if paychecks:
        freq = int(paychecks[0].get("freq") or 14)
        pay_freq = {7: "weekly", 14: "biweekly", 15: "semimonthly", 30: "monthly"}.get(freq, "biweekly")

    bkt_rows = []
    for b in buckets:
        target = F.b_budget(month, b["id"])
        if not target:
            target = float(b.get("defaultBudget") or b.get("default_budget") or 0)
        bkt_rows.append({
            "id": b["id"], "name": b["name"], "target": round(target, 2),
            "due": b.get("dueDay") or b.get("due_day"),
            "freq": b.get("payFreq") or b.get("pay_freq") or "monthly",
        })

    return {"startBal": start_bal, "startInc": start_inc,
            "payFreq": pay_freq, "buckets": bkt_rows}


def _date_label(iso: str) -> str:
    from datetime import date as _date
    try:
        dt = _date.fromisoformat(iso[:10])
        return dt.strftime("%a, %b ") + str(dt.day)
    except (ValueError, TypeError):
        return iso
