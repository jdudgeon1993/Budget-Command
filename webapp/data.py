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


def parse_amount(raw, default: float = 0.0) -> float:
    """Parse a user-entered dollar amount, stripping $ and , separators."""
    try:
        return round(float((raw or "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        return default


# ── Loading ───────────────────────────────────────────────────────────────────

def load_data(full_history: bool = False) -> dict:
    """Canonical data dict for this request (cached on g).

    Normal loads window transactions to the last 13 months.
    Pass full_history=True for reports that need all-time data.
    """
    cache_key = "data_full" if full_history else "data"
    cached = getattr(g, cache_key, None)
    if cached is not None:
        return cached
    if current_app.config["DEV_SEED"]:
        result = sample_data()
    else:
        tx_months = 0 if full_history else 13
        result = DB.load_all(
            session.get("user_id", ""), session.get("access_token", ""),
            tx_months=tx_months,
        )
    setattr(g, cache_key, result)
    return result


def invalidate_cache() -> None:
    """Drop the request-scoped data cache.

    Call this right after persisting a write to the database — any
    subsequent load_data() in the same request must re-fetch the
    canonical state rather than re-serve the pre-write snapshot, or the
    panel re-rendered for the response will show stale values until the
    user manually reloads the page.
    """
    for key in ("data", "data_full"):
        try:
            delattr(g, key)
        except AttributeError:
            pass


def active_mid() -> str:
    return session.get("active_mid") or F.current_month_id()


def active_month(data: dict, mid: str = None) -> dict:
    target = mid or active_mid()
    for m in data.get("months", []):
        if m["id"] == target:
            return m
    return {"id": target, "allocations": {}, "budgets": {}, "handledBuckets": {}, "vaultWithdrawals": {}}


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

    # RTS is always anchored to today's calendar month so it stays consistent
    # regardless of which month the user is browsing. Viewing July does not
    # suddenly inflate RTS by dropping June's claims from the calculation.
    today_mid = F.current_month_id()
    today_month = next((m for m in months if m["id"] == today_mid),
                       {"id": today_mid, "allocations": {}, "budgets": {}})
    rts = F.ready_to_spend(today_month, months, accounts, buckets, txs)

    total_cash = F.total_cash(accounts, txs)
    aom = F.age_of_money(accounts, txs)
    # Income/allocated/spent are scoped to the VIEWED month for context
    income = F.month_income(mid, txs, accounts)
    allocated = F.total_allocated(month, buckets)
    spent = sum(F.b_spent(mid, b["id"], txs) for b in buckets)
    # Denominator is total available to assign (allocated + unassigned), not
    # just income — in ZBB you also allocate from prior-month carry-forward.
    _available = allocated + max(rts, 0)
    pct = min(100, round((allocated / _available) * 100)) if _available > 0 else 0

    month_closed = bool(month.get("closed"))
    is_past_month = F.month_status(mid) == "past"
    today_month_label = month_label(today_mid)

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

    return {
        "active_panel": active_panel,
        "user_email": session.get("email", ""),
        "month_label": month_label(mid),
        "today_month_label": today_month_label,
        "is_past_month": is_past_month,
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

    # Future months always show today's budget targets. Today is the source of
    # truth for what each bucket costs — stale DB entries in future months are
    # ignored at render time so any target change is immediately visible across
    # all forward months without requiring a DB sweep.
    if F.month_status(mid) == "future":
        today_mid = F.current_month_id()
        today_month = next(
            (m for m in months if m["id"] == today_mid),
            {"id": today_mid, "allocations": {}, "budgets": {}},
        )
        merged_budgets = {
            **(month.get("budgets") or {}),    # future month base (new buckets only)
            **(today_month.get("budgets") or {}),  # today always overrides
        }
        month = {**month, "budgets": merged_budgets}

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
            vault_total = F.vault_accumulated(bid, months) if b.get("type") == "vault" else 0.0
            needed = max(budget - alloc, 0)
            handled = bool((month.get("handledBuckets") or {}).get(bid))

            is_flex = b.get("flex", False) and b.get("type", "expense") == "expense"

            if is_flex:
                uncovered = spent - alloc
                if uncovered > 0.005:
                    status, pill = "partial", f"Cover ${uncovered:,.2f}"
                elif spent > 0.005:
                    status, pill = "funded", f"${spent:,.2f} spent"
                else:
                    status, pill = "funded", "Open"
            elif budget > 0:
                over = spent - budget
                if over > 0.005:
                    status, pill = "over", f"Overspent ${over:,.2f}"
                elif alloc > budget + 0.005:
                    status, pill = "funded", "Overfunded"
                elif alloc >= budget - 0.005:
                    status, pill = "funded", ("Paid" if spent >= budget - 0.005 else "Funded")
                elif alloc <= 0.005:
                    status, pill = "partial", "Unfunded"
                else:
                    status, pill = "partial", f"Funding — ${needed:,.2f} short"
            else:
                # No budget target — envelope vs spending
                over = spent - alloc
                if over > 0.005:
                    status, pill = "partial", f"Cover ${over:,.2f}"
                elif alloc > 0.005:
                    status, pill = "funded", "Funded"
                else:
                    status, pill = "funded", "Open"

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
                "flex": is_flex, "uncovered": round(max(spent - alloc, 0), 2) if is_flex else 0.0,
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


# ── Distribute modal view-model ───────────────────────────────────────────────

def _due_reason(o: dict) -> str:
    """Human-readable explanation of why an obligation ranked where it did."""
    bits = []
    if o["due_in"] is not None:
        d = o["due_in"]
        bits.append(f"Due in {d} day{'' if d == 1 else 's'}" if d > 0 else "Due today")
    if o["freq"]:
        bits.append(o["freq"])
    bits.append(f"${o['gap']:,.2f} short")
    return " · ".join(bits)


def distribute_ctx(checked_ob: set | None = None, checked_rule: set | None = None) -> dict:
    """Ranked funding suggestions for the Distribute modal.

    Step 1 ranks underfunded buckets by urgency (gap weighted by how soon
    it's due). Step 2 previews what the active internal allocation rules
    would do with whatever's left over — percentage/fixed rules take their
    cut, "fund this bucket" rules cascade and catch the remainder, exactly
    like income_rules_ctx but against leftover RTS instead of a paycheck.

    `checked_ob`/`checked_rule` reflect the user's current checkbox state
    (None means "default to everything checked" — the initial suggestion).
    Unchecked items display with their suggested amount but contribute
    nothing to totals or to the cascade — skipping a rule leaves its share
    available to the rule below it, exactly like disabling it would.
    """
    data = load_data()
    mid = active_mid()
    month = active_month(data)
    months = data.get("months", [])
    accounts = data.get("accounts", [])
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    txs = data.get("txs", [])
    bkt_name = {b["id"]: b["name"] for b in buckets}

    rts = F.ready_to_spend(month, months, accounts, buckets, txs)

    obligations = F.distribute_obligations(buckets, month)
    for o in obligations:
        o["reason"] = _due_reason(o)
    all_ob_ids = {o["id"] for o in obligations}
    if checked_ob is None:
        # First open: greedily pre-check from top of urgency list until RTS
        # is exhausted. Skips items that don't fit but continues checking
        # smaller items below — gives a realistic, achievable suggestion.
        checked_ob = set()
        budget_remaining = rts
        for o in obligations:
            if o["gap"] <= budget_remaining + 0.005:
                checked_ob.add(o["id"])
                budget_remaining = round(budget_remaining - o["gap"], 2)
    else:
        checked_ob = checked_ob & all_ob_ids
    for o in obligations:
        o["checked"] = o["id"] in checked_ob

    total_gap = round(sum(o["gap"] for o in obligations if o["checked"]), 2)
    leftover = round(max(rts - total_gap, 0), 2)

    rules_raw = sorted(
        [r for r in data.get("allocationRules", [])
         if r.get("active", True) and r.get("rule_type", "internal") == "internal"
         and (r.get("bucket_id") or r.get("bucketId"))],
        key=lambda r: r.get("sort_order", 0),
    )
    all_rule_ids = {r["id"] for r in rules_raw}
    checked_rule = all_rule_ids if checked_rule is None else (checked_rule & all_rule_ids)

    rule_suggestions = []
    remaining = leftover
    for r in rules_raw:
        bid = r.get("bucket_id") or r.get("bucketId") or ""
        vtype = r.get("value_type", "fixed")
        v = float(r.get("value") or 0)
        is_fund = (vtype == "fund")
        is_checked = r["id"] in checked_rule
        if is_fund:
            computed = round(max(0.0, remaining), 2)
        elif vtype == "pct":
            computed = round(leftover * v / 100, 2)
        else:
            computed = round(min(v, max(0.0, remaining)), 2)
        if is_checked:
            remaining = round(remaining - computed, 2)
        rule_suggestions.append({
            "id": r["id"], "name": r.get("name", "Rule"),
            "bucket_id": bid, "bucket_name": bkt_name.get(bid, "—"),
            "computed": computed, "value": v, "is_pct": vtype == "pct", "is_fund": is_fund,
            "checked": is_checked,
        })

    total_applied = total_gap + sum(r["computed"] for r in rule_suggestions if r["checked"])
    remaining_rts = round(max(rts - total_applied, 0), 2)

    return {
        "rts": rts, "mid": mid,
        "obligations": obligations, "total_gap": total_gap, "leftover": leftover,
        "rule_suggestions": rule_suggestions,
        "total_applied": round(total_applied, 2), "remaining_rts": remaining_rts,
    }


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
        "value_type": r.get("value_type", "fixed"),
        "is_pct": (r.get("value_type") == "pct" or r.get("type") == "pct"),
        "is_fund": (r.get("value_type") == "fund"),
        "active": r.get("active", True),
        "rule_type": r.get("rule_type", "internal"),
    } for r in sorted(data.get("allocationRules", []), key=lambda r: r.get("sort_order", 0))]
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
    """Compute what active allocation rules would do for a given income amount.

    Rules fire in order (sort_order). Percentage and fixed-amount rules take
    their cut from the original paycheck; "fund this bucket" rules have no
    fixed cut of their own — each one simply claims whatever's left over after
    every rule before it, like a real envelope catching the remainder.
    """
    data = load_data()
    rules_raw = sorted(data.get("allocationRules", []), key=lambda r: r.get("sort_order", 0))
    bkt_name = {b["id"]: b["name"] for b in data.get("buckets", [])}
    month = active_month(data)

    internal, external = [], []
    remaining = amount
    for r in rules_raw:
        if not r.get("active", True):
            continue
        v = float(r.get("value") or 0)
        vtype = r.get("value_type", "fixed")
        is_fund = (vtype == "fund")
        if is_fund:
            computed = round(max(0.0, remaining), 2)
        else:
            computed = round(amount * v / 100, 2) if vtype == "pct" else v
        remaining = round(remaining - computed, 2)
        rtype = r.get("rule_type", "internal")

        if rtype == "external":
            external.append({
                "id": r["id"], "name": r.get("name", "Transfer"),
                "computed": computed, "value": v, "is_pct": vtype == "pct", "is_fund": is_fund,
            })
        else:
            bid = r.get("bucket_id") or r.get("bucketId") or ""
            if not bid:
                continue
            internal.append({
                "id": r["id"], "name": r.get("name", "Rule"),
                "bucket_id": bid, "bucket_name": bkt_name.get(bid, "—"),
                "computed": computed, "value": v, "is_pct": vtype == "pct", "is_fund": is_fund,
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


def paycheck_distribute_ctx(
    paycheck_amount: float,
    mid: str,
    checked_rule: set | None = None,
    checked_ob: set | None = None,
    checked_fund: set | None = None,
    checked_next: set | None = None,
) -> dict:
    """Combined paycheck distribution: rules → obligations → catch-alls → next month.

    None for any checked_* means "use smart defaults" (first open).
    An explicit set (even empty) means the user has made their choices.

    Step 4 (next month) inherits this month's budget targets for any bucket
    that doesn't yet have an explicit next-month budget set. This means pre-
    funding next month's bills always shows realistic gap amounts even before
    the user has manually configured a next-month budget.
    """
    data = load_data()
    month = active_month(data, mid)
    months = data.get("months", [])
    accounts = data.get("accounts", [])
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    txs = data.get("txs", [])
    bkt_name = {b["id"]: b["name"] for b in buckets}

    rts = F.ready_to_spend(month, months, accounts, buckets, txs)

    # Partition rules into three groups
    rules_raw = sorted(
        [r for r in data.get("allocationRules", []) if r.get("active", True)],
        key=lambda r: r.get("sort_order", 0),
    )
    external_rules, internal_rules, fund_rules = [], [], []
    for r in rules_raw:
        vtype = r.get("value_type", "fixed")
        v = float(r.get("value") or 0)
        is_fund = (vtype == "fund")
        rtype = r.get("rule_type", "internal")
        bid = r.get("bucket_id") or r.get("bucketId") or ""
        computed = round(paycheck_amount * v / 100, 2) if vtype == "pct" else (v if not is_fund else 0.0)
        entry = {
            "id": r["id"], "name": r.get("name", "Rule"),
            "bucket_id": bid, "bucket_name": bkt_name.get(bid, "—"),
            "computed": computed, "value": v,
            "is_pct": vtype == "pct", "is_fund": is_fund,
        }
        if rtype == "external":
            external_rules.append(entry)
        elif is_fund:
            fund_rules.append(entry)
        else:
            internal_rules.append(entry)

    # Step 1 — internal pct/fixed rules (computed against paycheck amount)
    all_rule_ids = {r["id"] for r in internal_rules}
    checked_rule = all_rule_ids if checked_rule is None else (checked_rule & all_rule_ids)
    for r in internal_rules:
        r["checked"] = r["id"] in checked_rule
    total_rules = round(sum(r["computed"] for r in internal_rules if r["checked"]), 2)

    # Step 2 — obligations fill from RTS remaining after rules are claimed
    rts_after_rules = round(rts - total_rules, 2)
    obligations = F.distribute_obligations(buckets, month)
    for o in obligations:
        o["reason"] = _due_reason(o)
    all_ob_ids = {o["id"] for o in obligations}
    if checked_ob is None:
        checked_ob = set()
        budget_remaining = max(rts_after_rules, 0)
        for o in obligations:
            if o["gap"] <= budget_remaining + 0.005:
                checked_ob.add(o["id"])
                budget_remaining = round(budget_remaining - o["gap"], 2)
    else:
        checked_ob = checked_ob & all_ob_ids
    for o in obligations:
        o["checked"] = o["id"] in checked_ob
    total_ob = round(sum(o["gap"] for o in obligations if o["checked"]), 2)

    # Step 3 — "fund this bucket" catch-alls absorb whatever's left
    rts_after_ob = round(max(rts_after_rules - total_ob, 0), 2)
    all_fund_ids = {r["id"] for r in fund_rules}
    checked_fund = all_fund_ids if checked_fund is None else (checked_fund & all_fund_ids)
    fund_remaining = rts_after_ob
    for r in fund_rules:
        if r["id"] in checked_fund:
            r["computed"] = round(fund_remaining, 2)
            fund_remaining = 0.0
        else:
            r["computed"] = 0.0
        r["checked"] = r["id"] in checked_fund
    total_fund = round(sum(r["computed"] for r in fund_rules if r["checked"]), 2)

    # Step 4 — pre-fund next month's obligations with whatever remains after Step 3.
    # Build next month: use existing DB record if it exists, otherwise synthesise.
    # Either way, fill in any missing budget targets from this month so the gap
    # calculation returns realistic amounts even before the user has manually
    # planned next month.
    rts_after_fund = round(max(rts_after_ob - total_fund, 0), 2)
    next_mid = F.month_offset(mid, 1)
    next_month_raw = next((m for m in months if m["id"] == next_mid), None)
    this_budgets = dict(month.get("budgets") or {})
    if next_month_raw:
        # Merge: prefer next month's explicit budgets, fall back to this month's
        merged_budgets = {**this_budgets, **(next_month_raw.get("budgets") or {})}
        next_month = {**next_month_raw, "budgets": merged_budgets}
    else:
        next_month = {
            "id": next_mid, "allocations": {}, "budgets": this_budgets,
            "handledBuckets": {}, "vaultWithdrawals": {},
        }
    next_obligations = F.distribute_obligations(buckets, next_month)
    for o in next_obligations:
        o["reason"] = _due_reason(o)
        o["next_mid"] = next_mid  # carry forward so apply route knows which month
    all_next_ids = {o["id"] for o in next_obligations}
    if checked_next is None:
        checked_next = set()
        budget_remaining = rts_after_fund
        for o in next_obligations:
            if o["gap"] <= budget_remaining + 0.005:
                checked_next.add(o["id"])
                budget_remaining = round(budget_remaining - o["gap"], 2)
    else:
        checked_next = checked_next & all_next_ids
    for o in next_obligations:
        o["checked"] = o["id"] in checked_next
    total_next = round(sum(o["gap"] for o in next_obligations if o["checked"]), 2)

    total_applied = round(total_rules + total_ob + total_fund + total_next, 2)

    return {
        "rts": rts, "mid": mid, "next_mid": next_mid,
        "next_month_label": month_label(next_mid),
        "paycheck_amount": paycheck_amount,
        "external_rules": external_rules,
        "internal_rules": internal_rules, "total_rules": total_rules,
        "obligations": obligations, "total_ob": total_ob,
        "fund_rules": fund_rules, "total_fund": total_fund,
        "next_obligations": next_obligations, "total_next": total_next,
        "total_applied": total_applied,
        "remaining_rts": round(max(rts - total_applied, 0), 2),
    }


def reports_view(view_mid: str = None):
    """Full reports data — BvA, trends, spending analysis, goals, discipline."""
    from collections import defaultdict
    from datetime import date as _date
    import calendar as _cal

    data = load_data(full_history=True)
    mid = view_mid or active_mid()
    month = active_month(data, mid)
    txs = data.get("txs", [])
    all_months = data.get("months", [])
    accounts = [a for a in data.get("accounts", []) if not a.get("archived")]
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))

    # ── Available months for dropdown ─────────────────────────────────────────
    seen = {m["id"] for m in all_months} | {F.current_month_id()}
    available_months = [{"mid": m, "label": month_label(m)}
                        for m in sorted(seen, reverse=True)[:13]]

    # ── BvA (current month) ───────────────────────────────────────────────────
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

    total_spend_cat = sum(c["spent"] for c in cat_spend) or 1
    for c in cat_spend:
        c["pct"] = round((c["spent"] / total_spend_cat) * 100)
    cat_spend.sort(key=lambda c: c["spent"], reverse=True)

    income = F.month_income(mid, txs, accounts)
    totals = {"income": income, "spent": grand_spent, "budget": grand_budget,
              "net": income - grand_spent}

    # ── Account snapshot / net worth ──────────────────────────────────────────
    snapshot = []
    for a in accounts:
        bal = F.acct_balance(a, txs)
        atype = a.get("type", "budget")
        snapshot.append({"name": a["name"], "type": atype, "balance": bal,
                         "net_worth_bal": -bal if atype == "debt" else bal})
    net_worth = sum(s["net_worth_bal"] for s in snapshot)

    # ── Funding rate ──────────────────────────────────────────────────────────
    expense_bkts = [b for b in buckets if b.get("type", "expense") != "vault"]
    funded_count = sum(
        1 for b in expense_bkts
        if F.b_alloc(month, b["id"]) >= max(F.b_budget(month, b["id"]) - 0.005, 0.005)
    )
    funding_rate = {"funded": funded_count, "total": max(len(expense_bkts), 1),
                    "pct": round(funded_count / max(len(expense_bkts), 1) * 100)}

    # ── Allocation rate + RTS ─────────────────────────────────────────────────
    total_alloc = sum(F.b_alloc(month, b["id"]) for b in buckets)
    rts_val = round(income - total_alloc, 2)
    alloc_pct = min(100, round(total_alloc / income * 100) if income > 0 else 0)
    allocation_rate = {"allocated": total_alloc, "income": income,
                       "pct": alloc_pct, "rts": rts_val}

    # ── Fixed vs variable ─────────────────────────────────────────────────────
    fixed_spent = sum(
        F.b_spent(mid, b["id"], txs)
        for b in buckets
        if not b.get("flex") and b.get("type", "expense") == "expense"
           and (b.get("recurring") or b.get("dueDay") or (b.get("defaultBudget") or 0) > 0)
    )
    variable_spent = max(0.0, grand_spent - fixed_spent)
    fv_denom = (fixed_spent + variable_spent) or 1
    fixed_pct = round(fixed_spent / fv_denom * 100)
    fixed_vs_variable = {"fixed": fixed_spent, "variable": variable_spent,
                         "fixed_pct": fixed_pct, "variable_pct": 100 - fixed_pct}

    # ── Top merchants ─────────────────────────────────────────────────────────
    merchant_totals: dict = defaultdict(float)
    for t in txs:
        if t.get("monthId") == mid and t.get("type") == "out" and not F.is_scheduled(t):
            name = (t.get("desc") or "Unknown").strip()
            merchant_totals[name] += float(t.get("amount") or 0)
    top_merchants = [{"name": k, "amount": round(v, 2)}
                     for k, v in sorted(merchant_totals.items(),
                                        key=lambda x: x[1], reverse=True)[:8]]

    # ── Top transactions ──────────────────────────────────────────────────────
    bkt_name = {b["id"]: b["name"] for b in buckets}
    out_txs = sorted(
        [t for t in txs if t.get("monthId") == mid and t.get("type") == "out"
         and not F.is_scheduled(t)],
        key=lambda t: float(t.get("amount") or 0), reverse=True
    )
    top_txs = [{"date": (t.get("date") or "")[:10][5:],
                "desc": t.get("desc") or "Transaction",
                "bucket": bkt_name.get(t.get("bucketId", ""), ""),
                "amount": float(t.get("amount") or 0)}
               for t in out_txs[:5]]

    # ── 12-month income/expense trend ─────────────────────────────────────────
    trend_12mo = []
    for i in range(11, -1, -1):
        m_id = F.month_offset(mid, -i)
        m_income = F.month_income(m_id, txs, accounts)
        m_spent = sum(F.b_spent(m_id, b["id"], txs) for b in buckets)
        trend_12mo.append({"mid": m_id, "label": month_label(m_id)[:3],
                           "income": m_income, "spent": m_spent,
                           "net": m_income - m_spent})
    max_val = max((max(t["income"], t["spent"]) for t in trend_12mo), default=1) or 1
    for t in trend_12mo:
        t["income_pct"] = round(t["income"] / max_val * 100)
        t["spent_pct"] = round(t["spent"] / max_val * 100)

    # ── Over-budget frequency by category (last 6 months) ────────────────────
    over_freq = []
    for cat in cats:
        cat_bkts = [b for b in buckets if b.get("catId") == cat["id"]]
        if not cat_bkts:
            continue
        dots, over_count = [], 0
        for i in range(5, -1, -1):
            m_id = F.month_offset(mid, -i)
            m_month = active_month(data, m_id)
            c_budget = sum(F.b_budget(m_month, b["id"]) for b in cat_bkts)
            c_spent = sum(F.b_spent(m_id, b["id"], txs) for b in cat_bkts)
            hit = c_budget > 0 and c_spent > c_budget + 0.005
            dots.append(hit)
            if hit:
                over_count += 1
        if over_count > 0:
            over_freq.append({"name": cat["name"], "count": over_count,
                              "total": 6, "dots": dots})
    over_freq.sort(key=lambda x: x["count"], reverse=True)
    over_freq = over_freq[:6]

    # ── Goals ─────────────────────────────────────────────────────────────────
    goals = []
    for b in buckets:
        btype = b.get("type", "expense")
        target = float(b.get("targetAmount") or 0)
        if btype in ("goal", "sinking") and target > 0:
            saved = F.bucket_available(b, month, all_months, txs)
            saved = max(0.0, saved)
            monthly_contrib = float(b.get("defaultBudget") or 0)
            remaining = max(0.0, target - saved)
            months_left = (round(remaining / monthly_contrib)
                          if monthly_contrib > 0 else None)
            pct = min(100, round(saved / target * 100))
            goals.append({"name": b["name"], "saved": saved, "target": target,
                          "pct": pct, "monthly_contrib": monthly_contrib,
                          "months_left": months_left,
                          "target_date": b.get("targetDate") or ""})

    # ── Net worth trend (6 months) ────────────────────────────────────────────
    nw_trend = []
    for i in range(5, -1, -1):
        m_id = F.month_offset(mid, -i)
        y, m0 = F.parse_month_id(m_id)
        last_day = _date(y, m0 + 1, _cal.monthrange(y, m0 + 1)[1])
        nw = sum(
            (-F.acct_balance_as_of(a, txs, last_day) if a.get("type") == "debt"
             else F.acct_balance_as_of(a, txs, last_day))
            for a in accounts
        )
        nw_trend.append({"mid": m_id, "label": month_label(m_id)[:3], "net_worth": round(nw, 2)})
    nw_min = min(t["net_worth"] for t in nw_trend) if nw_trend else 0
    nw_max = max(t["net_worth"] for t in nw_trend) if nw_trend else 1
    nw_range = (nw_max - nw_min) or 1
    for t in nw_trend:
        t["pct"] = round((t["net_worth"] - nw_min) / nw_range * 100)

    # ── Debt accounts with monthly delta ─────────────────────────────────────
    debt_accounts = []
    for a in accounts:
        if a.get("type") == "debt":
            cur_bal = F.acct_balance(a, txs)
            prev_mid = F.month_offset(mid, -1)
            prev_y, prev_m0 = F.parse_month_id(prev_mid)
            prev_last = _date(prev_y, prev_m0 + 1, _cal.monthrange(prev_y, prev_m0 + 1)[1])
            prev_bal = F.acct_balance_as_of(a, txs, prev_last)
            debt_accounts.append({"name": a["name"], "balance": cur_bal,
                                   "delta": round(prev_bal - cur_bal, 2)})

    # ── Multi-month BvA ───────────────────────────────────────────────────────
    def _bva_multi(n):
        m_ids = [F.month_offset(mid, -(n - 1 - i)) for i in range(n)]
        rows = []
        for cat in cats:
            cat_bkts = [b for b in buckets if b.get("catId") == cat["id"]]
            if not cat_bkts:
                continue
            months_data = []
            for m_id in m_ids:
                m_mo = active_month(data, m_id)
                c_bud = sum(F.b_budget(m_mo, b["id"]) for b in cat_bkts)
                c_sp = sum(F.b_spent(m_id, b["id"], txs) for b in cat_bkts)
                months_data.append({"label": month_label(m_id)[:3],
                                    "variance": c_bud - c_sp,
                                    "budget": c_bud, "spent": c_sp})
            rows.append({"name": cat["name"], "color": cat.get("color", "#888"),
                         "months": months_data})
        labels = [month_label(m)[:3] for m in m_ids]
        return {"rows": rows, "labels": labels}

    bva_3mo = _bva_multi(3)
    bva_6mo = _bva_multi(6)

    # ── Discipline heatmap (12 months) ────────────────────────────────────────
    heatmap, neg_rts_months = [], []
    for i in range(11, -1, -1):
        m_id = F.month_offset(mid, -i)
        m_mo = active_month(data, m_id)
        m_income = F.month_income(m_id, txs, accounts)
        m_alloc = sum(F.b_alloc(m_mo, b["id"]) for b in buckets)
        rts_m = m_income - m_alloc
        if m_income > 0:
            alloc_rate = min(m_alloc / m_income, 1.0)
            if rts_m < -0.005:
                status = "deficit"
                neg_rts_months.append(month_label(m_id))
            elif alloc_rate >= 0.90:
                status = "full"
            else:
                status = "partial"
        else:
            alloc_rate = 0.0
            status = "empty"
        heatmap.append({"mid": m_id, "label": month_label(m_id)[:3],
                        "status": status, "rts": round(rts_m, 2),
                        "alloc_rate": round(alloc_rate * 100)})

    active_hm = [h for h in heatmap if h["status"] != "empty"]
    disc_score = round(sum(h["alloc_rate"] for h in active_hm) / max(len(active_hm), 1))
    avg_surplus = round(
        sum(h["rts"] for h in heatmap if h["rts"] > 0) /
        max(sum(1 for h in heatmap if h["rts"] > 0), 1), 2
    )

    return {
        "view_mid": mid, "available_months": available_months,
        "bva": bva, "bva_3mo": bva_3mo, "bva_6mo": bva_6mo,
        "cat_spend": cat_spend, "totals": totals,
        "snapshot": snapshot, "net_worth": net_worth,
        "funding_rate": funding_rate, "allocation_rate": allocation_rate,
        "fixed_vs_variable": fixed_vs_variable,
        "top_merchants": top_merchants, "top_txs": top_txs,
        "trend_12mo": trend_12mo, "over_freq": over_freq,
        "goals": goals, "nw_trend": nw_trend,
        "debt_accounts": debt_accounts,
        "heatmap": heatmap, "disc_score": disc_score,
        "neg_rts_months": neg_rts_months, "avg_surplus": avg_surplus,
    }


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


def forecast_view(n_months: int = 3, income_override: float = 0.0,
                  skipped_pay_dates: list = None, no_accrue_dates: list = None,
                  active_scenario_id: str = "") -> dict:
    """Full forecast panel data: 60-day timeline + pay-period what-if."""
    from . import forecast_calc as FC
    from flask import session as _session
    data = load_data()
    skip_list = skipped_pay_dates or []
    no_accrue_list = no_accrue_dates or []

    scenarios = []
    if not current_app.config["DEV_SEED"]:
        scenarios = DB.list_scenarios(session.get("user_id", ""), session.get("access_token", ""))

    bucket_overrides, off_buckets = {}, []
    if active_scenario_id:
        sc = next((s for s in scenarios if s["id"] == active_scenario_id), None)
        if sc:
            allocs = sc.get("allocations") or {}
            bucket_overrides = allocs.get("bucket_overrides") or {}
            off_buckets = allocs.get("off_buckets") or []

    timeline_rows = FC.compute_simple_timeline(data, 60)
    # Load scenarios for the scenario bar (baseline view has no active scenario)
    scenarios = []
    try:
        uid = _session.get("user_id", "")
        token = _session.get("access_token", "")
        if uid and token:
            scenarios = DB.list_scenarios(uid, token)
    except Exception:
        pass
    fc = FC.compute_forecast(data, n_months=n_months, income_override=income_override,
                             skipped_pay_dates=skip_list, no_accrue_dates=no_accrue_list,
                             bucket_overrides=bucket_overrides or None,
                             off_buckets=off_buckets or None)
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
        "scenarios": scenarios,
        "active_scenario_id": "",
    }


def _date_label(iso: str) -> str:
    from datetime import date as _date
    try:
        dt = _date.fromisoformat(iso[:10])
        return dt.strftime("%a, %b ") + str(dt.day)
    except (ValueError, TypeError):
        return iso
