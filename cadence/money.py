"""
Cadence money domain — pure functions, no framework.

The single invariant that keeps every screen honest:

    Available Balance  ==  Unallocated + Σ over ALL envelopes (funded − spent)

`funded` is authoritative (fund/defund move it; spending never does).
`spent` is DERIVED from the ledger, so editing a transaction recomputes live.
Ready to Spend excludes vaults (locked savings). Nothing is cached.
"""

from __future__ import annotations
import uuid
import calendar
from datetime import date

SPEND, GOAL, VAULT = "spend", "goal", "vault"
EXPENSE, INCOME, REFUND = "expense", "income", "refund"


def genesis(opening: float) -> dict:
    return {"opening": round(opening, 2), "unallocated": round(opening, 2),
            "categories": [], "envelopes": [], "transactions": []}


def _id() -> str:
    return uuid.uuid4().hex[:12]


def add_category(s: dict, name: str, color: str) -> dict:
    c = {"id": _id(), "name": name, "color": color}
    s["categories"].append(c)
    return c


def add_envelope(s: dict, name: str, cat_id: str, type: str = SPEND,
                 target: float = 0.0, funded: float = 0.0,
                 due_day: int | None = None, frequency: str | None = None,
                 flex: bool = False) -> dict:
    e = {"id": _id(), "name": name, "cat_id": cat_id, "type": type,
         "target": round(target, 2), "funded": round(funded, 2),
         "due_day": due_day, "frequency": frequency,
         "flex": bool(flex), "handled": False}
    s["envelopes"].append(e)
    return e


def env(s: dict, eid: str) -> dict:
    return next(e for e in s["envelopes"] if e["id"] == eid)


# ── Due dates + urgency (drives sort order and Forecast) ──────────────────────

def days_until(due_day, today: date | None = None) -> int | None:
    """Days until the next occurrence of a day-of-month, or None."""
    if not due_day:
        return None
    today = today or date.today()
    y, m = today.year, today.month
    cand = date(y, m, min(int(due_day), calendar.monthrange(y, m)[1]))
    if cand < today:                                   # already passed → next month
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        cand = date(y, m, min(int(due_day), calendar.monthrange(y, m)[1]))
    return (cand - today).days


def days_until_due(e: dict, today: date | None = None) -> int | None:
    return days_until(e.get("due_day"), today)


def urgency_score(available: float, gap: float, days, flex: bool = False,
                  handled: bool = False, is_vault: bool = False) -> float:
    """Pure scoring — reused for both the demo and live data. Higher floats up."""
    if handled:
        return -100.0
    if is_vault:
        return -50.0
    over = max(0.0, -available)
    score = 500.0 + over if over > 0 else 0.0          # overspent needs attention now
    if flex:
        return score                                    # flex isn't "due"; only urgent if overspent
    if gap > 0.005:
        if days is None:
            score += 10.0 + gap * 0.02                  # no date, mild nudge by size
        elif days < 0:
            score += 400.0 + gap                        # past due + unfunded → top
        else:
            score += max(0.0, 200.0 - days * 5.0) + gap * 0.03   # sooner/bigger = higher
    return score


def urgency(s: dict, e: dict) -> float:
    gap = round(max(0.0, e.get("target", 0.0) - e["funded"]), 2)
    return urgency_score(available(s, e), gap, days_until_due(e),
                         e.get("flex"), e.get("handled"), e["type"] == VAULT)


def status(available: float, gap: float, days, flex: bool = False, handled: bool = False) -> str:
    """A one-word state used for the badge on each card."""
    if handled:
        return "handled"
    if available < -0.005:
        return "over"
    if flex:
        return "flex"
    if gap > 0.005 and days is not None and days < 0:
        return "pastdue"
    if gap > 0.005 and days is not None and days <= 10:
        return "soon"
    if gap > 0.005:
        return "under"
    return "ok"


# ── Placement (silent — no ledger row) ────────────────────────────────────────

def fund(s: dict, eid: str, amount: float) -> float:
    """Move money Unallocated → envelope. RULE: you can never assign more than
    you have, so Unallocated never goes negative — a positive request is capped
    at whatever's Unallocated. Returns the amount actually moved."""
    amount = round(amount, 2)
    if amount > 0:
        amount = min(amount, round(s["unallocated"], 2))
    if amount == 0:
        return 0.0
    env(s, eid)["funded"] = round(env(s, eid)["funded"] + amount, 2)
    s["unallocated"] = round(s["unallocated"] - amount, 2)
    return amount


def defund(s: dict, eid: str, amount: float) -> None:
    fund(s, eid, -amount)


def set_funded(s: dict, eid: str, value: float) -> None:
    """Assign the envelope to an exact funded level (moves the delta to/from Unallocated)."""
    fund(s, eid, round(value - env(s, eid)["funded"], 2))


def move(s: dict, src_id: str, dst_id: str, amount: float) -> None:
    """Reallocate between two envelopes without touching Unallocated."""
    amount = round(amount, 2)
    env(s, src_id)["funded"] = round(env(s, src_id)["funded"] - amount, 2)
    env(s, dst_id)["funded"] = round(env(s, dst_id)["funded"] + amount, 2)


# ── Structure edits ───────────────────────────────────────────────────────────

def rename(s: dict, eid: str, name: str) -> None:
    name = (name or "").strip()
    if name:
        env(s, eid)["name"] = name


def set_target(s: dict, eid: str, value: float) -> None:
    env(s, eid)["target"] = round(max(0.0, value), 2)


def set_due_day(s: dict, eid: str, day) -> None:
    try:
        d = int(day)
        env(s, eid)["due_day"] = d if 1 <= d <= 31 else None
    except (ValueError, TypeError):
        env(s, eid)["due_day"] = None


def set_frequency(s: dict, eid: str, freq) -> None:
    env(s, eid)["frequency"] = freq or None


def set_flex(s: dict, eid: str, flex: bool) -> None:
    env(s, eid)["flex"] = bool(flex)


def toggle_handled(s: dict, eid: str) -> None:
    e = env(s, eid)
    e["handled"] = not e.get("handled")


def set_category(s: dict, eid: str, cat_id: str) -> None:
    env(s, eid)["cat_id"] = cat_id


def delete_envelope(s: dict, eid: str) -> None:
    """Remove an envelope. Its unspent balance returns to Unallocated (money is
    never vaporized); past spending stays on the books."""
    e = env(s, eid)
    s["unallocated"] = round(s["unallocated"] + available(s, e), 2)
    s["envelopes"] = [x for x in s["envelopes"] if x["id"] != eid]


# ── Ledger (cleared money) ────────────────────────────────────────────────────

def add_expense(s: dict, eid: str, amount: float, desc: str = "", date: str = "") -> dict:
    if env(s, eid)["type"] == VAULT:
        raise ValueError("a vault can't be spent from — move money out with a transfer first")
    return _tx(s, EXPENSE, round(amount, 2), eid, desc, date)


def add_income(s: dict, amount: float, desc: str = "", date: str = "") -> dict:
    tx = _tx(s, INCOME, round(amount, 2), None, desc, date)
    s["unallocated"] = round(s["unallocated"] + amount, 2)
    return tx


def _tx(s: dict, kind: str, amount: float, eid, desc: str, date: str) -> dict:
    tx = {"id": _id(), "kind": kind, "amount": amount, "envelope_id": eid,
          "desc": desc, "date": date}
    s["transactions"].append(tx)
    return tx


# ── Derived metrics (computed, never stored) ──────────────────────────────────

def spent(s: dict, eid: str) -> float:
    return round(sum(t["amount"] for t in s["transactions"]
                     if t["kind"] == EXPENSE and t["envelope_id"] == eid), 2)


def available(s: dict, e: dict) -> float:
    return round(e["funded"] - spent(s, e["id"]), 2)


def unallocated(s: dict) -> float:
    return round(s["unallocated"], 2)


def ready_to_spend(s: dict) -> float:
    return round(s["unallocated"] + sum(available(s, e) for e in s["envelopes"]
                                        if e["type"] != VAULT), 2)


def available_balance(s: dict) -> float:
    bal = s["opening"]
    for t in s["transactions"]:
        if t["kind"] in (INCOME, REFUND):
            bal += t["amount"]
        elif t["kind"] == EXPENSE:
            bal -= t["amount"]
    return round(bal, 2)
