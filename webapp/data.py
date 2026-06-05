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

def load_data(full_history: bool = False) -> dict:
    """Canonical data dict for this request (cached on g).

    Normal loads window transactions to the last 13 months.
    Pass full_history=True for reports that need all-time data.
    """
    cache_key = "data_full" if full_history else "data"
    if cache_key in g:
        return g[cache_key]
    if current_app.config["DEV_SEED"]:
        g[cache_key] = sample_data()
    else:
        tx_months = 0 if full_history else 13
        g[cache_key] = DB.load_all(
            session.get("user_id", ""), session.get("access_token", ""),
            tx_months=tx_months,
        )
    return g[cache_key]


def active_mid() -> str:
    return session.get("active_mid") or F.current_month_id()


def active_month(data: dict, mid: str = None) -> dict:
    target = mid or active_mid()
    for m in data.get("months", []):
        if m["id"] == target:
            return m
    return {"id": target, "allocations": {}, "budgets": {}}


def month_label(mid: str) -> str:
    y, m0 = F.parse_month_id(mid)
    return f"{calendar.month_name[m0 + 1]} {y}"


# ── Shell view-model (sidebar RTS, header, month) ─────────────────────────────

def shell_ctx(active_panel: str = "") -> dict:
    from datetime import date as _date
    data = load_data()
    mid = active_mid()
    month = active_month(data)
    accounts = data.get("accounts", [])
    months = data.get("months", [])
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    txs = data.get("txs", [])

    rts = F.ready_to_spend(month, months, accounts, buckets, txs)
    total_cash = F.total_cash(accounts, txs)
    aom = F.age_of_money(accounts, txs)
    income = F.month_income(mid, txs, accounts)
    allocated = F.total_allocated(month, buckets)
    spent = sum(F.b_spent(mid, b["id"], txs) for b in buckets)
    pct = min(100, round((allocated / income) * 100)) if income else 0

    # Pre-render context for add-transaction modal (so it can be instant, no round-trip)
    tx_accounts = [{"id": a["id"], "name": a["name"]}
                   for a in accounts if not a.get("archived")]
    cats_sorted = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    tx_buckets_by_cat = []
    for c in cats_sorted:
        bkts = [{"id": b["id"], "name": b["name"]} for b in buckets
                if b.get("catId") == c["id"] and b.get("type") != "vault"]
        if bkts:
            tx_buckets_by_cat.append({"cat": c["name"], "buckets": bkts})

    month_closed = active_month(data).get("closed", False)
    return {
        "active_panel": active_panel,
        "user_email": session.get("email", ""),
        "month_label": month_label(mid),
        "month_closed": month_closed,
        "rts": rts,
        "total_cash": total_cash,
        "age_of_money": aom,
        "income": income,
        "allocated": allocated,
        "spent": spent,
        "pct": pct,
        "unhomed": max(rts, 0),
        "tx_accounts": tx_accounts,
        "tx_buckets_by_cat": tx_buckets_by_cat,
        "tx_today": _date.today().isoformat(),
    }


# ── Buckets panel view-model ──────────────────────────────────────────────────

def bucket_rows(view_mid: str = None):
    """Category-grouped bucket rows with alloc/budget/spent/left + status."""
    data = load_data()
    current_mid = active_mid()
    mid = view_mid or current_mid
    month = active_month(data, mid)
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
            bid = b["id"]
            alloc = F.b_alloc(month, bid)
            budget = F.b_budget(month, bid)
            spent = F.b_spent(mid, bid, txs)
            left = F.bucket_available(b, month, months, txs)
            roll_bal = F.rollover_bal(b, month, months, txs)
            roll_bal_raw = F.rollover_bal_raw(b, month["id"], months, txs)
            rollover_released = float((month.get("rolloverReleased") or {}).get(bid) or 0)
            vault_total = F.vault_accumulated(bid, months) if b.get("type") == "vault" else 0.0
            over = max(spent - budget, 0) if budget else max(spent - alloc, 0)
            needed = max(budget - alloc, 0)
            handled = bool((month.get("handledBuckets") or {}).get(bid))
            if over > 0:
                status, pill = "over", f"Over ${over:,.2f}"
            elif needed > 0:
                status, pill = "partial", f"−${needed:,.2f}"
            elif budget and spent >= budget:
                status, pill = "funded", "Paid"
            else:
                status, pill = "funded", "Funded"
            if handled:
                status, pill = "funded", "✓ Handled"
            cat_alloc += alloc
            cat_budget += budget
            # Current month transactions for inline expand
            bkt_txs = sorted([
                {"date": t.get("date", "")[:10],
                 "desc": t.get("desc") or t.get("description") or "Transaction",
                 "amount": float(t.get("amount") or 0)}
                for t in txs
                if t.get("monthId") == mid and t.get("bucketId") == bid
                and t.get("type") == "out" and not F.is_scheduled(t)
            ], key=lambda x: x["date"], reverse=True)
            target_amount = float(b.get("targetAmount") or 0)
            target_date = b.get("targetDate") or ""
            contrib_freq = b.get("contribFreq") or ""
            progress_pct = 0
            goal_reached = False
            if target_amount > 0 and b.get("type") in ("sinking", "goal"):
                progress_pct = min(100, max(0, round((left / target_amount) * 100)))
                goal_reached = left >= target_amount
            monthly_needed = None
            if b.get("type") in ("sinking", "goal") and target_amount > 0 and target_date:
                try:
                    from datetime import date as _date_cls
                    ty = int(target_date[:4])
                    tm = int(target_date[5:7])
                    today = _date_cls.today()
                    months_left = (ty - today.year) * 12 + (tm - today.month)
                    if months_left > 0 and left < target_amount:
                        monthly_needed = round((target_amount - left) / months_left, 2)
                except Exception:
                    pass
            row = {
                "id": bid, "name": b["name"], "btype": b.get("type", "expense"),
                "alloc": alloc, "budget": budget, "spent": spent, "left": left,
                "status": status, "pill": pill, "needed": needed,
                "vault_total": vault_total,
                "due_day": b.get("dueDay"),
                "pay_freq": b.get("payFreq") or "",
                "target_amount": target_amount,
                "target_date": target_date,
                "contrib_freq": contrib_freq,
                "progress_pct": progress_pct,
                "goal_reached": goal_reached,
                "monthly_needed": monthly_needed,
                "rollover": b.get("rollover", False),
                "roll_bal_raw": roll_bal_raw,
                "rollover_released": rollover_released,
                "handled": handled,
                "txs": bkt_txs,
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
    # Month tabs for the future-planning toggle
    month_tabs = [
        {"mid": F.month_offset(current_mid, n),
         "label": month_label(F.month_offset(current_mid, n)),
         "offset": n}
        for n in (0, 1, 2)
    ]
    return {"groups": groups, "attention": attention, "cats": cats,
            "view_mid": mid, "current_mid": current_mid, "month_tabs": month_tabs,
            "all_buckets": [{"id": b["id"], "name": b["name"], "btype": b.get("type","expense")}
                            for b in buckets if not b.get("archived")]}


# ── Accounts panel view-model ─────────────────────────────────────────────────

def accounts_view():
    """Account cards (with live balances) + month summary + a grouped ledger."""
    data = load_data()
    mid = active_mid()
    txs = data.get("txs", [])
    accounts = [a for a in data.get("accounts", []) if not a.get("archived")]
    bkt_name = {b["id"]: b["name"] for b in data.get("buckets", [])}
    acct_map = {a["id"]: a for a in accounts}

    cards = [{
        "id": a["id"], "name": a["name"], "type": a.get("type", "budget"),
        "color": a.get("color", "#818cf8"),
        "balance": F.acct_balance(a, txs),
        "debtAPR": a.get("debtAPR"),
        "debtMinPayment": a.get("debtMinPayment"),
        "creditLimit": a.get("creditLimit"),
    } for a in accounts]

    month_txs = [t for t in txs if t.get("monthId") == mid]
    posted_txs = [t for t in month_txs if not F.is_scheduled(t)]
    sched_txs  = [t for t in month_txs if F.is_scheduled(t)]

    summary = {
        "income": F.month_income(mid, txs, accounts),
        "spent": sum(t["amount"] for t in posted_txs if t.get("type") == "out"),
        "scheduled": sum(t["amount"] for t in sched_txs if t.get("type") == "out"),
        "transferred": sum(t["amount"] for t in posted_txs if t.get("type") == "xfr"),
    }

    def _shape_row(t):
        ttype = t.get("type", "out")
        amt = float(t.get("amount") or 0)
        acct = acct_map.get(t.get("accountId", ""), {})
        if ttype == "in":
            signed, color, pill = amt, "green", "Income"
        elif ttype == "xfr":
            signed, color, pill = -amt, "text2", "Transfer"
        else:
            signed, color, pill = -amt, "red", "Expense"
        # Sub-label: bucket name for expenses, to-account for transfers
        to_acct = acct_map.get(t.get("toAccountId", ""), {})
        sub = bkt_name.get(t.get("bucketId", ""), "") or (to_acct.get("name", "") if ttype == "xfr" else "")
        return {
            "id": t.get("id", ""), "date": t.get("date", ""),
            "desc": t.get("desc") or "Transaction",
            "pill": pill, "color": color, "signed": signed,
            "sub": sub,
            "account_id": t.get("accountId", ""),
            "account_name": acct.get("name", ""),
            "account_color": acct.get("color", "#818cf8"),
            "reconciled": bool(t.get("reconciled")),
            "income_type": t.get("incomeType") or "",
            "scheduled": F.is_scheduled(t),
            "type": ttype, "amount": amt,
            "bucketId": t.get("bucketId", ""),
            "toAccountId": t.get("toAccountId", ""),
            "debtPaymentAccountId": t.get("debtPaymentAccountId", ""),
        }

    _TYPE_ORDER = {"in": 0, "xfr": 1, "out": 2}

    def _group(tx_list):
        # Sort newest-first; within same date: income → transfers → expenses
        rows = sorted(
            [_shape_row(t) for t in tx_list],
            key=lambda r: (r["date"], -_TYPE_ORDER.get(r["type"], 2)),
            reverse=True,
        )
        groups, cur = [], None
        for r in rows:
            if cur is None or cur["date"] != r["date"]:
                cur = {"date": r["date"], "label": _date_label(r["date"]), "net": 0.0, "rows": []}
                groups.append(cur)
            cur["net"] += r["signed"]
            cur["rows"].append(r)
        return groups

    # Payees for autocomplete
    payees = sorted(set(
        t.get("desc", "").strip()
        for t in txs if t.get("desc") and t.get("type") not in ("opening",)
    ), key=str.lower)

    acct_balances = {a["id"]: round(F.acct_balance(a, txs), 2) for a in accounts}
    acct_types = {a["id"]: a.get("type", "budget") for a in accounts}

    return {
        "cards": cards, "summary": summary,
        "ledger": _group(posted_txs),
        "scheduled": _group(sched_txs),
        "payees": payees,
        "acct_balances": acct_balances,
        "acct_types": acct_types,
    }


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
        "bucket": bkt_name.get(r.get("bucket_id") or r.get("bucketId"), "—"),
        "bucket_id": r.get("bucket_id") or r.get("bucketId") or "",
        "value": float(r.get("value") or 0),
        "is_pct": (r.get("value_type") == "pct" or r.get("type") == "pct"),
        "active": r.get("active", True),
        "rule_type": r.get("rule_type", "internal"),
    } for r in data.get("allocationRules", [])]
    buckets = [{"id": b["id"], "name": b["name"]}
               for b in data.get("buckets", []) if not b.get("archived")]
    active_internal = [r for r in rules if r["active"] and r["rule_type"] == "internal"]
    rules_total_pct   = sum(r["value"] for r in active_internal if r["is_pct"])
    rules_total_fixed = sum(r["value"] for r in active_internal if not r["is_pct"])
    paycheck_total = sum(p["amount"] for p in paychecks)
    return {"paychecks": paychecks, "cats": cats, "rules": rules, "buckets": buckets,
            "freq_label": {7: "Weekly", 14: "Bi-weekly", 15: "Semi-monthly", 30: "Monthly"},
            "rules_total_pct": rules_total_pct,
            "rules_total_fixed": rules_total_fixed,
            "paycheck_total": paycheck_total}


def income_rules_ctx(amount: float, mid: str) -> dict:
    """Compute what active allocation rules would do for a given income amount."""
    data = load_data()
    rules_raw = data.get("allocationRules", [])
    bkt_name = {b["id"]: b["name"] for b in data.get("buckets", [])}
    month = active_month(data)

    internal, external = [], []
    for r in rules_raw:
        if not r.get("active", True):
            continue
        v = float(r.get("value") or 0)
        vtype = r.get("value_type", "fixed")
        computed = round(amount * v / 100, 2) if vtype == "pct" else v
        rtype = r.get("rule_type", "internal")

        if rtype == "external":
            external.append({
                "id": r["id"], "name": r.get("name", "Transfer"),
                "computed": computed, "value": v, "is_pct": vtype == "pct",
            })
        else:
            bid = r.get("bucket_id") or r.get("bucketId") or ""
            if not bid:
                continue
            internal.append({
                "id": r["id"], "name": r.get("name", "Rule"),
                "bucket_id": bid, "bucket_name": bkt_name.get(bid, "—"),
                "computed": computed, "value": v, "is_pct": vtype == "pct",
                "current_alloc": F.b_alloc(month, bid),
            })

    total_in = sum(r["computed"] for r in internal)
    total_ex = sum(r["computed"] for r in external)
    return {
        "income_amount": amount, "mid": mid,
        "internal_rules": internal, "external_rules": external,
        "total_internal": total_in, "total_external": total_ex,
        "remaining": round(amount - total_in - total_ex, 2),
    }


def reports_view():
    """Budget-vs-Actual + category spending + month totals + account snapshot."""
    data = load_data(full_history=True)
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

    # Debt accounts are liabilities — negate for net worth
    snapshot = []
    for a in accounts:
        bal = F.acct_balance(a, txs)
        atype = a.get("type", "budget")
        snapshot.append({"name": a["name"], "type": atype,
                         "balance": bal,
                         "net_worth_bal": -bal if atype == "debt" else bal})
    net_worth = sum(s["net_worth_bal"] for s in snapshot)

    return {"bva": bva, "cat_spend": cat_spend, "totals": totals,
            "snapshot": snapshot, "net_worth": net_worth}


def tx_form_ctx():
    """Selects + defaults for the Add/Edit Transaction form."""
    from datetime import date as _date
    data = load_data()
    acct_name = {a["id"]: a["name"] for a in data.get("accounts", [])}
    accounts = [{"id": a["id"], "name": a["name"]}
                for a in data.get("accounts", []) if not a.get("archived")]
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    buckets_by_cat = []
    for c in cats:
        bkts = [{"id": b["id"], "name": b["name"],
                 "debtAccountId": b.get("debtAccountId", ""),
                 "debtAccountName": acct_name.get(b.get("debtAccountId", ""), "")}
                for b in data.get("buckets", [])
                if b.get("catId") == c["id"] and not b.get("archived")
                and b.get("type") != "vault"]
        if bkts:
            buckets_by_cat.append({"cat": c["name"], "buckets": bkts})
    payees = sorted(set(
        t.get("desc", "").strip()
        for t in data.get("txs", []) if t.get("desc") and t.get("type") not in ("opening",)
    ), key=str.lower)
    return {"accounts": accounts, "buckets_by_cat": buckets_by_cat,
            "today": _date.today().isoformat(), "mid": active_mid(),
            "payees": payees}


def tx_by_id(tid: str) -> dict | None:
    """Find a single transaction by ID from the loaded data."""
    for t in load_data().get("txs", []):
        if t.get("id") == tid:
            return t
    return None


def close_wizard_ctx() -> dict:
    """All data needed by the End-of-Month Close wizard modal.

    Always targets the previous calendar month — you close the month that ended,
    not the one you're currently budgeting.
    """
    import calendar as _cal
    from datetime import date as _date
    data = load_data()
    txs = data.get("txs", [])
    accounts = [a for a in data.get("accounts", []) if not a.get("archived")]
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]

    # Always close the previous calendar month
    target_mid = F.month_offset(F.current_month_id(), -1)
    month = active_month(data, target_mid)

    # Last calendar day of the target month — used for end-of-month balances
    y, m0 = F.parse_month_id(target_mid)
    cal_month = m0 + 1  # 0-indexed → 1-indexed
    eom_date = _date(y, cal_month, _cal.monthrange(y, cal_month)[1])

    # Transactions that belong to the target month (posted only)
    month_txs = [t for t in txs
                 if t.get("monthId") == target_mid and not F.is_scheduled(t)]

    # Step 1 — income
    income_txs = sorted(
        [{"date": t.get("date", "")[:10],
          "desc": t.get("desc") or "Income",
          "amount": float(t.get("amount") or 0),
          "acct": next((a["name"] for a in accounts if a["id"] == t.get("accountId")), "")}
         for t in month_txs if t.get("type") == "in"],
        key=lambda r: r["date"], reverse=True,
    )
    income_total = sum(r["amount"] for r in income_txs)

    # Step 2 — non-debt accounts, balance as of EOM
    budget_accounts = [
        {"id": a["id"], "name": a["name"], "type": a.get("type", "budget"),
         "balance": F.acct_balance_as_of(a, txs, eom_date)}
        for a in accounts if a.get("type") != "debt"
    ]

    # Step 3 — debt accounts, balance as of EOM
    debt_accounts = [
        {"id": a["id"], "name": a["name"],
         "balance": F.acct_balance_as_of(a, txs, eom_date),
         "apr": a.get("debtAPR"),
         "min_payment": a.get("debtMinPayment"),
         "interest_posted": sum(
             float(t.get("amount") or 0) for t in month_txs
             if t.get("accountId") == a["id"] and t.get("type") == "out"
             and "Interest" in (t.get("desc") or "")
         )}
        for a in accounts if a.get("type") == "debt"
    ]

    # Step 4 — bucket summary for the target month
    funded = partial = over = 0
    over_buckets = []
    partial_buckets = []
    for b in buckets:
        bid = b["id"]
        alloc = F.b_alloc(month, bid)
        budget = F.b_budget(month, bid)
        spent = F.b_spent(target_mid, bid, txs)
        if b.get("type") == "vault":
            funded += 1
            continue
        excess = spent - budget if budget else spent - alloc
        if excess > 0.005:
            over += 1
            over_buckets.append({"id": bid, "name": b["name"], "budget": budget,
                                  "spent": spent, "over": excess})
        elif alloc < (budget * 0.99 if budget else 0.01):
            partial += 1
            partial_buckets.append({"id": bid, "name": b["name"],
                                     "budget": budget, "alloc": alloc,
                                     "needed": round(budget - alloc, 2)})
        else:
            funded += 1

    # Step 5 — closing snapshot using EOM balances
    cash = sum(F.acct_balance_as_of(a, txs, eom_date)
               for a in accounts if a.get("type") != "debt")
    debt_total = sum(F.acct_balance_as_of(a, txs, eom_date)
                     for a in accounts if a.get("type") == "debt")
    spent_total = sum(float(t.get("amount") or 0)
                      for t in month_txs if t.get("type") == "out")

    return {
        "month_label": month_label(target_mid),
        "target_mid": target_mid,
        "eom_date": eom_date.isoformat(),
        "is_closed": month.get("closed", False),
        # Step 1
        "income_txs": income_txs, "income_total": income_total,
        # Step 2
        "budget_accounts": budget_accounts,
        # Step 3
        "debt_accounts": debt_accounts,
        # Step 4
        "bucket_counts": {"funded": funded, "partial": partial, "over": over},
        "over_buckets": over_buckets,
        "partial_buckets": partial_buckets,
        # Step 5
        "snapshot": {
            "cash": round(cash, 2), "debt_total": round(debt_total, 2),
            "net_worth": round(cash - debt_total, 2),
            "income": round(income_total, 2), "spent": round(spent_total, 2),
        },
    }


def forecast_view(n_months: int = 3, income_override: float = 0.0,
                  skipped_pay_dates: list = None,
                  no_accrue_dates: list = None) -> dict:
    """Full forecast panel data: 60-day timeline + pay-period what-if."""
    from . import forecast_calc as FC
    data = load_data()
    skip_list = skipped_pay_dates or []
    no_accrue_list = no_accrue_dates or []
    timeline_rows = FC.compute_simple_timeline(data, 60)
    fc = FC.compute_forecast(data, n_months=n_months, income_override=income_override,
                             skipped_pay_dates=skip_list,
                             no_accrue_dates=no_accrue_list)
    svg = FC.build_balance_svg(fc["periods"])
    return {
        "timeline_rows": timeline_rows,
        "forecast": fc,
        "balance_svg": svg,
        "n_months": n_months,
        "income_override": income_override,
        "skipped_pay_dates": skip_list,
        "skip_dates_str": ",".join(str(d) for d in skip_list),
        "no_accrue_dates": no_accrue_list,
        "no_accrue_dates_str": ",".join(str(d) for d in no_accrue_list),
    }


def _date_label(iso: str) -> str:
    from datetime import date as _date
    try:
        dt = _date.fromisoformat(iso[:10])
        return dt.strftime("%a, %b ") + str(dt.day)
    except (ValueError, TypeError):
        return iso
