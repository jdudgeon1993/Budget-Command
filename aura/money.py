"""
Aura money domain — pure functions, no I/O, no framework.

This is the heart of Aura and the thing that must be provably correct: every
operation preserves the single invariant that ties the whole app to one real
cash account —

    Available Balance  ==  Unallocated + Σ over ALL envelopes (funded − spent)

`funded` is authoritative (fund/defund move it; spending never does). `spent` is
DERIVED from the ledger, so editing a transaction recomputes live. Available
Balance is also transaction-driven (opening + income/refund − expense), so it
self-corrects when any past transaction changes.

The in-memory `state` dict here maps 1:1 to aura/schema.sql, so the Supabase data
layer built in the next phase can hand back this exact shape and reuse every
function below unchanged. Run `python -m aura.money` to execute the self-check.
"""

from __future__ import annotations
import uuid
from datetime import date


# ── State shape ───────────────────────────────────────────────────────────────
# state = {
#   "budget":       {"account_name","opening_balance","unallocated","cycle_start"},
#   "envelopes":    [{"id","name","type","target","funded",...}],
#   "transactions": [{"id","envelope_id","kind","amount","tx_date","cycle_start","note"}],
# }

VAULT, SINKING, SPEND = "vault", "sinking", "spend"
EXPENSE, INCOME, REFUND = "expense", "income", "refund"


def genesis(opening_balance: float, cycle_start: str) -> dict:
    """A fresh budget: all cash starts Unallocated (no job yet)."""
    return {
        "budget": {
            "account_name": "Checking",
            "opening_balance": round(float(opening_balance), 2),
            "unallocated": round(float(opening_balance), 2),
            "cycle_start": cycle_start,
        },
        "envelopes": [],
        "transactions": [],
    }


def _new_id() -> str:
    return str(uuid.uuid4())


def _env(state: dict, env_id: str) -> dict:
    e = next((e for e in state["envelopes"] if e["id"] == env_id), None)
    if e is None:
        raise ValueError(f"no such envelope: {env_id}")
    return e


# ── Structure ─────────────────────────────────────────────────────────────────

def add_envelope(state: dict, name: str, type: str,
                 target: float | None = None, target_date: str | None = None,
                 due_day: int | None = None) -> dict:
    if type not in (SPEND, SINKING, VAULT):
        raise ValueError(f"bad envelope type: {type}")
    e = {"id": _new_id(), "name": name, "type": type,
         "target": None if target is None else round(float(target), 2),
         "target_date": target_date, "due_day": due_day,
         "funded": 0.0, "archived": False}
    state["envelopes"].append(e)
    return e


# ── Placement (silent — no ledger row) ────────────────────────────────────────

def fund(state: dict, env_id: str, amount: float) -> None:
    """Move money Unallocated → envelope. Silent; the envelope state is the record."""
    amount = round(float(amount), 2)
    if amount <= 0:
        raise ValueError("fund amount must be positive")
    _env(state, env_id)["funded"] = round(_env(state, env_id)["funded"] + amount, 2)
    state["budget"]["unallocated"] = round(state["budget"]["unallocated"] - amount, 2)


def defund(state: dict, env_id: str, amount: float) -> None:
    """Move money envelope → Unallocated. Silent."""
    amount = round(float(amount), 2)
    if amount <= 0:
        raise ValueError("defund amount must be positive")
    _env(state, env_id)["funded"] = round(_env(state, env_id)["funded"] - amount, 2)
    state["budget"]["unallocated"] = round(state["budget"]["unallocated"] + amount, 2)


def vault_transfer(state: dict, from_id: str | None, to_id: str | None,
                   amount: float, reason: str = "") -> None:
    """The only way money moves in/out of a vault. NULL side = Unallocated."""
    amount = round(float(amount), 2)
    if amount <= 0:
        raise ValueError("transfer amount must be positive")
    if from_id == to_id:
        raise ValueError("transfer needs two distinct sides")
    if from_id is None:
        state["budget"]["unallocated"] = round(state["budget"]["unallocated"] - amount, 2)
    else:
        _env(state, from_id)["funded"] = round(_env(state, from_id)["funded"] - amount, 2)
    if to_id is None:
        state["budget"]["unallocated"] = round(state["budget"]["unallocated"] + amount, 2)
    else:
        _env(state, to_id)["funded"] = round(_env(state, to_id)["funded"] + amount, 2)


# ── Ledger (cleared money) ────────────────────────────────────────────────────

def add_income(state: dict, amount: float, tx_date: str, note: str = "") -> dict:
    return _add_tx(state, None, INCOME, amount, tx_date, note)


def add_refund(state: dict, amount: float, tx_date: str, note: str = "") -> dict:
    """Refunds are income to Unallocated — never returned to an envelope."""
    return _add_tx(state, None, REFUND, amount, tx_date, note)


def add_expense(state: dict, env_id: str, amount: float, tx_date: str, note: str = "") -> dict:
    """An expense MUST name a non-vault envelope. Vault guard enforced here."""
    e = _env(state, env_id)
    if e["type"] == VAULT:
        raise ValueError("vault envelopes cannot be spent from — use a transfer")
    return _add_tx(state, env_id, EXPENSE, amount, tx_date, note)


def _add_tx(state: dict, env_id, kind: str, amount: float, tx_date: str, note: str) -> dict:
    amount = round(float(amount), 2)
    if amount < 0:
        raise ValueError("amount must be >= 0")
    tx = {"id": _new_id(), "envelope_id": env_id, "kind": kind, "amount": amount,
          "tx_date": tx_date, "cycle_start": _cycle_of(state, tx_date), "note": note}
    state["transactions"].append(tx)
    # Income/refund credit Unallocated (stored); expenses only affect derived spent.
    if kind in (INCOME, REFUND):
        state["budget"]["unallocated"] = round(state["budget"]["unallocated"] + amount, 2)
    return tx


def edit_tx(state: dict, tx_id: str, new_amount: float) -> None:
    """Edit an amount in place and ripple the correction to today (decision #4).

    - income/refund: adjust Unallocated by the delta.
    - expense in the CURRENT cycle: nothing stored changes (spent is derived).
    - expense in a CLOSED cycle: the delta lands in TODAY's Unallocated, so today
      stays accurate without reopening the closed cycle's books.
    """
    tx = next((t for t in state["transactions"] if t["id"] == tx_id), None)
    if tx is None:
        raise ValueError("no such transaction")
    new_amount = round(float(new_amount), 2)
    delta = round(new_amount - tx["amount"], 2)
    tx["amount"] = new_amount
    if tx["kind"] in (INCOME, REFUND):
        state["budget"]["unallocated"] = round(state["budget"]["unallocated"] + delta, 2)
    elif tx["kind"] == EXPENSE and tx["cycle_start"] != state["budget"]["cycle_start"]:
        # closed-cycle expense: more expense → less spendable today, and vice versa
        state["budget"]["unallocated"] = round(state["budget"]["unallocated"] - delta, 2)


# ── Rollover (cycle close) ────────────────────────────────────────────────────

def rollover(state: dict, new_cycle_start: str) -> dict:
    """Hard cutover: spend-envelope leftovers return to Unallocated and reset;
    sinking/vault carry forward untouched. Overspend is absorbed (Unallocated just
    ends up lower). Returns a snapshot of the just-closed cycle."""
    snap = {"cycle_start": state["budget"]["cycle_start"], "envelopes": []}
    for e in state["envelopes"]:
        if e["archived"]:
            continue
        sp = spent(state, e)
        snap["envelopes"].append({"id": e["id"], "name": e["name"], "type": e["type"],
                                  "funded": e["funded"], "spent": sp,
                                  "rolled": round(e["funded"] - sp, 2) if e["type"] == SPEND else 0.0})
        if e["type"] == SPEND:
            leftover = round(e["funded"] - sp, 2)          # positive OR negative (absorbed)
            state["budget"]["unallocated"] = round(state["budget"]["unallocated"] + leftover, 2)
            e["funded"] = 0.0
    snap["unallocated_close"] = state["budget"]["unallocated"]
    state["budget"]["cycle_start"] = new_cycle_start
    return snap


# ── Derived metrics (never stored — computed on demand) ───────────────────────

def _cycle_of(state: dict, d: str) -> str:
    """Cycle key = first-of-month of the tx date (cycles are calendar months)."""
    y, m, _ = (int(x) for x in d.split("-"))
    return f"{y:04d}-{m:02d}-01"


def spent(state: dict, e: dict) -> float:
    """Σ expenses against this envelope in its active window: current cycle for
    spend envelopes, lifetime for non-resetting sinking/vault."""
    cur = state["budget"]["cycle_start"]
    total = 0.0
    for t in state["transactions"]:
        if t["kind"] != EXPENSE or t["envelope_id"] != e["id"]:
            continue
        if e["type"] == SPEND and t["cycle_start"] != cur:
            continue
        total += t["amount"]
    return round(total, 2)


def available(state: dict, e: dict) -> float:
    return round(e["funded"] - spent(state, e), 2)


def available_balance(state: dict) -> float:
    """The real cash number — transaction-driven, reconciles to the bank."""
    bal = state["budget"]["opening_balance"]
    for t in state["transactions"]:
        if t["kind"] in (INCOME, REFUND):
            bal += t["amount"]
        elif t["kind"] == EXPENSE:
            bal -= t["amount"]
    return round(bal, 2)


def unallocated(state: dict) -> float:
    return round(state["budget"]["unallocated"], 2)


def ready_to_spend(state: dict) -> float:
    """Unallocated + available across NON-VAULT envelopes."""
    total = state["budget"]["unallocated"]
    for e in state["envelopes"]:
        if e["type"] != VAULT and not e["archived"]:
            total += available(state, e)
    return round(total, 2)


# ── Self-check: the invariant must hold after every operation ─────────────────

def _assert_invariant(state: dict, where: str) -> None:
    lhs = available_balance(state)
    rhs = round(state["budget"]["unallocated"]
                + sum(available(state, e) for e in state["envelopes"] if not e["archived"]), 2)
    assert lhs == rhs, f"INVARIANT BROKEN @ {where}: available_balance {lhs} != unalloc+Σavail {rhs}"


def _selfcheck() -> None:
    s = genesis(1000.00, "2026-08-01")
    _assert_invariant(s, "genesis")
    assert unallocated(s) == 1000.00 and available_balance(s) == 1000.00

    groc = add_envelope(s, "Groceries", SPEND, target=400)
    vac  = add_envelope(s, "Vacation", SINKING, target=3000, target_date="2027-06-01")
    vault = add_envelope(s, "Emergency", VAULT)

    fund(s, groc["id"], 400);  _assert_invariant(s, "fund groceries")
    fund(s, vac["id"], 250);   _assert_invariant(s, "fund vacation")
    vault_transfer(s, None, vault["id"], 500, "seed emergency"); _assert_invariant(s, "vault seed")
    assert unallocated(s) == round(1000 - 400 - 250 - 500, 2)   # 150 -150? => -150

    add_income(s, 2000, "2026-08-15"); _assert_invariant(s, "payday")
    add_expense(s, groc["id"], 130, "2026-08-16"); _assert_invariant(s, "buy groceries")
    add_refund(s, 40, "2026-08-17"); _assert_invariant(s, "refund")

    assert round(available(s, groc), 2) == round(400 - 130, 2)          # 270 left in groceries
    # RTS excludes the $500 vault; Available includes it
    assert round(available_balance(s) - ready_to_spend(s), 2) == available(s, vault) == 500.00

    # Vault guard: no expense may target a vault
    try:
        add_expense(s, vault["id"], 10, "2026-08-18"); raise AssertionError("vault expense allowed!")
    except ValueError:
        pass

    # Rollover: groceries leftover (270) returns to Unallocated; vault/sinking persist
    u_before = unallocated(s); groc_left = available(s, groc)
    snap = rollover(s, "2026-09-01"); _assert_invariant(s, "after rollover")
    assert unallocated(s) == round(u_before + groc_left, 2)
    assert s["envelopes"][0]["funded"] == 0.0          # groceries reset
    assert available(s, vac) == 250.00                 # sinking carried forward

    # Cross-cycle edit (decision #4): amend the closed-cycle grocery expense
    # 130 -> 100; the $30 must reappear in TODAY's Unallocated, invariant intact.
    past_tx = next(t for t in s["transactions"] if t["envelope_id"] == groc["id"])
    u_pre = unallocated(s)
    edit_tx(s, past_tx["id"], 100); _assert_invariant(s, "after cross-cycle edit")
    assert unallocated(s) == round(u_pre + 30, 2)

    print("aura.money self-check: ALL INVARIANTS HELD ✓")


if __name__ == "__main__":
    _selfcheck()
