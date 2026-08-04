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
                 target: float = 0.0, funded: float = 0.0) -> dict:
    e = {"id": _id(), "name": name, "cat_id": cat_id, "type": type,
         "target": round(target, 2), "funded": round(funded, 2)}
    s["envelopes"].append(e)
    return e


def env(s: dict, eid: str) -> dict:
    return next(e for e in s["envelopes"] if e["id"] == eid)


# ── Placement (silent — no ledger row) ────────────────────────────────────────

def fund(s: dict, eid: str, amount: float) -> None:
    amount = round(amount, 2)
    env(s, eid)["funded"] = round(env(s, eid)["funded"] + amount, 2)
    s["unallocated"] = round(s["unallocated"] - amount, 2)


def defund(s: dict, eid: str, amount: float) -> None:
    fund(s, eid, -amount)


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
