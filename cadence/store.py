"""
Cadence store — a per-session in-memory budget, seeded with realistic data.

For the proof-of-concept this holds state in memory (which is exactly how a
single-user NiceGUI session naturally works). Swapping in Supabase later means
implementing the same handful of read/write methods against the DB — the UI
never changes.
"""

from datetime import date

from . import money as M


def _today() -> str:
    return date.today().isoformat()


def _effective_days(own_days, split, items):
    """A split bucket's urgency timing comes from its soonest *unpaid* item, so the
    whole bucket surfaces when its next bill lands (not just its own due day)."""
    if not split:
        return own_days
    unpaid = [it["days_until_due"] for it in items
              if not it.get("paid") and it["days_until_due"] is not None]
    if not unpaid:
        return own_days
    return min(unpaid) if own_days is None else min(own_days, min(unpaid))


def _dsort(x):
    return (x["days_until_due"] is None, x["days_until_due"] if x["days_until_due"] is not None else 9999)


def _build_steps(rows: list[dict], rules: list[dict], unallocated: float,
                 paycheck_amount=None) -> dict:
    """The shared distribution plan behind both the Buckets 'Distribute' and the
    paycheck flow, so they read the same. Percentages are of the paycheck when
    distributing one, otherwise of what's unallocated.

    • external  — rule-driven transfers out (checking → savings)
    • internal  — rule-driven funding suggestions (fund a bucket)
    • obligations — underfunded bills, soonest-due first; anything already funded
      OR already paid this cycle drops off the list
    • next      — the same bills, offered again to pre-fund next month (get ahead)
    """
    base = round(paycheck_amount if paycheck_amount else unallocated, 2)
    by_id = {r["id"]: r for r in rows}
    external, internal = [], []
    for r in rules:
        if not r.get("active"):
            continue
        pct = r["value_type"] == "pct"
        if r["kind"] == "external":
            amt = round(base * r["value"] / 100, 2) if pct else (round(r["value"], 2) if r["value_type"] == "fixed" else 0.0)
            if amt > 0.005:
                external.append({"id": r["id"], "name": r["name"], "amount": amt,
                                 "detail": f'{r["value"]:g}% of paycheck' if pct else "fixed transfer"})
        else:
            bid = r.get("bucket_id")
            if not bid or bid not in by_id:
                continue
            if r["value_type"] == "fund":
                amt, detail = by_id[bid]["gap"], "fill to target"
            else:
                amt = round(base * r["value"] / 100, 2) if pct else round(r["value"], 2)
                detail = f'{r["value"]:g}% of paycheck' if pct else "fixed"
            if amt > 0.005:
                internal.append({"id": r["id"], "name": r["name"], "bucket_id": bid,
                                 "bucket_name": by_id[bid]["name"], "amount": round(amt, 2), "detail": detail})

    obligations, nexts = [], []
    for r in rows:
        if r["type"] != "spend" or r["flex"] or r["handled"]:   # bills only (goals/vaults aren't "due")
            continue
        dated = r["due_day"] is not None or r["frequency"] in ("weekly", "biweekly", "triweekly", "monthly")
        if r["split"] and r["items"]:
            # each unpaid, still-underfunded bill is its own obligation, soonest first
            for it in r["items"]:
                if not it.get("paid") and it.get("item_gap", 0.0) > 0.005:
                    obligations.append({"key": f'{r["id"]}#{it["id"]}', "id": r["id"], "split_item": True,
                                        "name": f'{r["name"]} · {it["name"]}', "gap": it["item_gap"],
                                        "days_until_due": it["days_until_due"]})
        elif r["gap"] > 0.005:                                  # non-split, underfunded & not paid
            paid = r["target"] > 0 and r["spent"] >= r["target"] - 0.005
            if not paid:
                obligations.append({"key": r["id"], "id": r["id"], "name": r["name"],
                                    "gap": r["gap"], "days_until_due": r["days_until_due"]})
        if dated and r["target"] > 0:                           # any dated bill → can pre-fund
            nexts.append({"id": r["id"], "name": r["name"], "amount": round(r["target"], 2),
                          "days_until_due": r["days_until_due"]})
    obligations.sort(key=_dsort)
    nexts.sort(key=_dsort)
    return {"unallocated": round(unallocated, 2), "base": base, "external": external,
            "internal": internal, "obligations": obligations, "next": nexts}


def seed() -> dict:
    """A believable month-in-progress so every screen has something to show."""
    # name, category, type, target, funded, due_day, flex
    rows = [
        {"name": "Rent",          "cat": "Housing",   "type": M.SPEND, "target": 1500, "funded": 1500, "due": 1},
        {"name": "Electric",      "cat": "Housing",   "type": M.SPEND, "target": 160,  "funded": 0,    "due": 9},
        {"name": "Utilities",     "cat": "Housing",   "type": M.SPEND, "target": 300,  "funded": 300,  "due": 15},
        {"name": "Groceries",     "cat": "Food",      "type": M.SPEND, "target": 400,  "funded": 300, "freq": "weekly"},
        {"name": "Dining Out",    "cat": "Food",      "type": M.SPEND, "funded": 100,  "flex": True},
        {"name": "Gas",           "cat": "Transport", "type": M.SPEND, "target": 120,  "funded": 80,  "freq": "biweekly"},
        {"name": "Car Insurance", "cat": "Transport", "type": M.SPEND, "target": 140,  "funded": 0,    "due": 20},
        {"name": "Subscriptions", "cat": "Lifestyle", "type": M.SPEND, "target": 60,   "funded": 60,   "due": 10},
        {"name": "Fun Money",     "cat": "Lifestyle", "type": M.SPEND, "funded": 200,  "flex": True},
        {"name": "Vacation Fund", "cat": "Future",    "type": M.GOAL,  "target": 3000, "funded": 850},
        {"name": "Emergency",     "cat": "Future",    "type": M.VAULT, "target": 10000, "funded": 2000},
    ]
    # This month's paychecks (income) and real spending, dated so the Ledger reads
    # like a live month-in-progress.
    income = [
        (1450.00, "Paycheck · Northwind Co", "2026-08-01"),
        (1350.00, "Paycheck · Northwind Co", "2026-07-18"),
    ]
    expenses = [
        ("Rent", 1500, "August rent", "2026-08-01"),
        ("Subscriptions", 46, "Streaming + music", "2026-08-01"),
        ("Utilities", 142, "Power + water", "2026-08-02"),
        ("Groceries", 286, "Trader Joe's", "2026-08-02"),
        ("Gas", 52, "Shell", "2026-08-03"),
        ("Groceries", 63, "Corner market", "2026-08-04"),
        ("Fun Money", 120, "Concert tickets", "2026-08-04"),
        ("Dining Out", 88, "Dinner w/ friends", "2026-08-05"),
    ]
    # Bank cash = funded envelopes + an $800 buffer left Unallocated. Splitting the
    # opening into (opening + income) keeps every headline number identical.
    total_funded = sum(r.get("funded", 0) for r in rows)
    total_income = sum(a for a, _, _ in income)
    xfer_out = 300.00                                # a checking→savings transfer, below
    s = M.genesis(opening=800.00 + total_funded - total_income + xfer_out,
                  savings_opening=6200.00)

    cat_color = {"Housing": "#6366f1", "Food": "#10b981", "Transport": "#f59e0b",
                 "Lifestyle": "#ec4899", "Future": "#8b5cf6"}
    cats = {name: M.add_category(s, name, color)["id"] for name, color in cat_color.items()}

    for amt, desc, when in income:               # income lifts Unallocated
        M.add_income(s, amt, desc, when)

    ids = {}
    for r in rows:
        eid = M.add_envelope(s, r["name"], cats[r["cat"]], r["type"], r.get("target", 0.0),
                             0.0, due_day=r.get("due"), frequency=r.get("freq"),
                             flex=r.get("flex", False))["id"]
        M.fund(s, eid, r.get("funded", 0.0))     # money moves FROM Unallocated (invariant stays true)
        ids[r["name"]] = eid

    for name, amt, desc, when in expenses:       # real spending → progress bars
        M.add_expense(s, ids[name], amt, desc, when)

    M.add_transfer(s, xfer_out, M.CHECKING, M.SAVINGS, "Move to savings", "2026-08-03")

    # Subscriptions is a split bucket: one pool, itemised into individual bills
    # that feed the Forecast on their own due dates. The target becomes the sum of
    # the items ($49.46); the pool funds the nearest unpaid bills first, so the
    # sheet shows some bills covered and the furthest-out ones still needing money.
    M.set_split(s, ids["Subscriptions"], True)
    for nm, amt, due, paid in [
        ("Netflix", 15.49, 3, True), ("Disney+", 13.99, 12, False),
        ("Spotify", 11.99, 8, False), ("Peacock", 7.99, 20, False),
    ]:
        it = M.add_item(s, ids["Subscriptions"], nm, amt, due)
        if paid:
            M.toggle_item_paid(s, ids["Subscriptions"], it["id"])

    # Settings: the recurring income + how each paycheck is split (feeds Forecast).
    M.add_paycheck(s, "Northwind Co", 1400.00, "biweekly", "2026-08-14")
    M.add_rule(s, "Fill Rent", "internal", ids["Rent"], 0, "fund", True)
    M.add_rule(s, "Emergency fund", "internal", ids["Emergency"], 10, "pct", True)
    M.add_rule(s, "401(k) contribution", "external", None, 6, "pct", True)

    return s


class Store:
    """Session-scoped budget state + the view-models the UI renders."""

    def __init__(self):
        self.s = seed()

    # ── headline metrics ──────────────────────────────────────────────────────
    # The header decomposes your CHECKING (cash-flow) account into two slices that
    # sum to it: Unallocated + In buckets. Vault buckets are still buckets, so
    # their money is in "In buckets". (No separate savings account in the demo.)
    def metrics(self) -> dict:
        un = M.unallocated(self.s)
        cash = M.available_balance(self.s)
        return {
            "unallocated": un,
            "cash": cash,                          # the checking account total
            "in_buckets": round(cash - un, 2),     # everything assigned to a bucket
            "age_of_money": M.age_of_money(self.s),
        }

    # ── buckets grouped by category ───────────────────────────────────────────
    def groups(self) -> list[dict]:
        out = []
        for c in self.s["categories"]:
            envs = [e for e in self.s["envelopes"] if e["cat_id"] == c["id"]]
            if not envs:
                continue
            # urgency-first: due-soon/past-due/overspent float up; funded + handled sink
            rows = sorted((self._row(e) for e in envs), key=lambda r: r["urgency"], reverse=True)
            out.append({
                "id": c["id"], "name": c["name"], "color": c["color"],
                "funded": round(sum(r["funded"] for r in rows), 2),
                "available": round(sum(r["available"] for r in rows), 2),
                "rows": rows,
            })
        return out

    # ── display row for one envelope (shared by groups() + bucket()) ──────────
    def _row(self, e: dict) -> dict:
        sp, av = M.spent(self.s, e["id"]), M.available(self.s, e)
        typ = e["type"]
        if typ == M.SPEND:
            funded = e["funded"]
            pct = min(1.0, max(0.0, sp / funded)) if funded > 0 else 0.0
        else:
            funded, sp = e["funded"], 0.0
            pct = min(1.0, max(0.0, funded / e["target"])) if e["target"] else 0.0
        # split buckets show each bill's own funded state (pool poured over items,
        # soonest-due first); plain buckets just carry their raw item list.
        items = (M.item_funding(e.get("items", []), av) if e.get("split")
                 else M.item_rows(e.get("items", [])))
        gap = round(max(0.0, e.get("target", 0.0) - e["funded"]), 2)
        flex, handled = e.get("flex"), e.get("handled")
        d = _effective_days(M.days_until_due(e), e.get("split"), items)
        status = M.status(av, gap, d, flex, handled)
        return {"id": e["id"], "name": e["name"], "type": typ, "cat_id": e["cat_id"],
                "target": round(e.get("target", 0.0), 2), "funded": round(funded, 2),
                "spent": round(sp, 2), "available": round(av, 2), "pct": pct,
                "gap": gap, "due_day": e.get("due_day"), "frequency": e.get("frequency"),
                "flex": bool(flex), "handled": bool(handled),
                "target_date": e.get("target_date"), "notes": e.get("notes", ""),
                "split": bool(e.get("split")), "items": items,
                "items_total": M.items_total(e),
                "items_paid": sum(1 for it in e.get("items", []) if it.get("paid")),
                "days_until_due": d, "status": status,
                "urgency": M.urgency_score(av, gap, d, flex, handled, typ == M.VAULT)}

    def bucket(self, eid: str) -> dict:
        return self._row(M.env(self.s, eid))

    def _all_rows(self) -> list[dict]:
        return [self._row(e) for e in self.s["envelopes"]]

    def distribute_steps(self, paycheck_amount=None) -> dict:
        return _build_steps(self._all_rows(), self.rules(), self.metrics()["unallocated"], paycheck_amount)

    def default_transfer_accounts(self):
        return (M.CHECKING, M.SAVINGS)

    def fund_sources(self, exclude: str) -> list[dict]:
        """Where money can come from: Unallocated first, then other buckets with
        a positive available balance (you can only move out what's actually there)."""
        out = [{"id": "unallocated", "name": "Unallocated", "avail": round(self.s["unallocated"], 2)}]
        for e in self.s["envelopes"]:
            if e["id"] == exclude:
                continue
            av = M.available(self.s, e)
            if av > 0.005:
                out.append({"id": e["id"], "name": e["name"], "avail": round(av, 2)})
        return out

    def assign(self, dst: str, source_id: str, amount: float):
        """The one funding action: move `amount` from a source into this bucket."""
        amount = round(amount, 2)
        if source_id == "unallocated":
            M.fund(self.s, dst, amount)
        else:
            M.move(self.s, source_id, dst, min(amount, M.available(self.s, M.env(self.s, source_id))))

    def categories(self) -> list[dict]:
        return [{"id": c["id"], "name": c["name"]} for c in self.s["categories"]]

    # ── live operations ───────────────────────────────────────────────────────
    def fund(self, eid: str, amount: float):
        M.fund(self.s, eid, amount)

    def defund(self, eid: str, amount: float):
        M.defund(self.s, eid, min(amount, M.env(self.s, eid)["funded"]))

    def move(self, src: str, dst: str, amount: float):
        M.move(self.s, src, dst, min(amount, M.env(self.s, src)["funded"]))

    def rename(self, eid: str, name: str):
        M.rename(self.s, eid, name)

    def set_target(self, eid: str, value: float):
        M.set_target(self.s, eid, value)

    def set_due_day(self, eid: str, day):
        M.set_due_day(self.s, eid, day)

    def set_frequency(self, eid: str, freq):
        M.set_frequency(self.s, eid, freq)

    def set_target_date(self, eid: str, target_date):
        M.set_target_date(self.s, eid, target_date)

    def set_notes(self, eid: str, notes):
        M.set_notes(self.s, eid, notes)

    # ── split / bill-schedule ─────────────────────────────────────────────────
    def set_split(self, eid: str, on: bool):
        M.set_split(self.s, eid, on)

    def add_item(self, eid: str, name: str, amount: float, due_day=None):
        return M.add_item(self.s, eid, name, amount, due_day)

    def edit_item(self, eid: str, iid: str, **ch):
        M.edit_item(self.s, eid, iid, **ch)

    def remove_item(self, eid: str, iid: str):
        M.remove_item(self.s, eid, iid)

    def toggle_item_paid(self, eid: str, iid: str):
        M.toggle_item_paid(self.s, eid, iid)

    def set_flex(self, eid: str, flex: bool):
        M.set_flex(self.s, eid, flex)

    def toggle_handled(self, eid: str):
        M.toggle_handled(self.s, eid)

    def record_spend(self, eid: str, amount: float, desc: str = ""):
        """Log a real expense against the bucket — spending, not funding."""
        M.add_expense(self.s, eid, round(float(amount), 2), desc, _today())

    # ── ledger (the cleared-money timeline) ───────────────────────────────────
    def _env_meta(self) -> dict:
        colors = {c["id"]: c["color"] for c in self.s["categories"]}
        return {e["id"]: (e["name"], colors.get(e["cat_id"], "#9aa0b5"))
                for e in self.s["envelopes"]}

    def transactions(self) -> list[dict]:
        """Every ledger row, newest first — the shape the Ledger UI renders."""
        meta = self._env_meta()
        acct = {a["id"]: a["name"] for a in self.s["accounts"]}
        out = []
        for i, t in enumerate(self.s["transactions"]):
            eid = t.get("envelope_id")
            if eid:
                name, color = meta.get(eid, ("", "#9aa0b5"))
            elif t["kind"] == M.TRANSFER:
                frm, to = acct.get(t.get("account_id"), "?"), acct.get(t.get("to_account_id"), "?")
                name, color = f"{frm} → {to}", "#f59e0b"
            else:
                name, color = "Income", "#10b981"
            out.append({"id": t["id"], "kind": t["kind"], "amount": round(t["amount"], 2),
                        "date": t.get("date") or "", "desc": t.get("desc") or "",
                        "bucket_id": eid, "bucket_name": name, "color": color,
                        "from_acct": t.get("account_id"), "to_acct": t.get("to_account_id"), "_seq": i})
        out.sort(key=lambda r: (r["date"], r["_seq"]), reverse=True)
        return out

    def ledger_metrics(self) -> dict:
        mid = _today()[:7]                        # 'YYYY-MM'
        income = spent = 0.0
        for t in self.s["transactions"]:
            if not (t.get("date") or "").startswith(mid):
                continue
            if t["kind"] == M.INCOME:
                income += t["amount"]
            elif t["kind"] == M.EXPENSE:
                spent += t["amount"]
            elif t["kind"] == M.REFUND:
                spent -= t["amount"]
        return {"balance": M.available_balance(self.s),
                "income": round(income, 2), "spent": round(spent, 2)}

    def payees(self) -> list[str]:
        seen = []
        for t in self.s["transactions"]:
            d = (t.get("desc") or "").strip()
            if d and d not in seen:
                seen.append(d)
        return seen

    def add_transaction(self, kind: str, amount: float, bucket_id, desc: str, date: str):
        amount = round(float(amount), 2)
        date = date or _today()
        if kind == M.INCOME:
            M.add_income(self.s, amount, desc, date)
        elif kind == M.REFUND:
            M.add_refund(self.s, bucket_id, amount, desc, date)
        else:
            M.add_expense(self.s, bucket_id, amount, desc, date)

    def accounts(self) -> list[dict]:
        return M.accounts(self.s)

    def add_transfer(self, from_id: str, to_id: str, amount: float, desc: str = "", date: str = ""):
        M.add_transfer(self.s, round(float(amount), 2), from_id, to_id, desc, date or _today())

    def edit_transaction(self, tid: str, **changes):
        M.edit_transaction(self.s, tid, **changes)

    def delete_transaction(self, tid: str):
        M.delete_transaction(self.s, tid)

    # ── settings: income + allocation rules (feed the Forecast) ───────────────
    def paychecks(self) -> list[dict]:
        return [dict(p) for p in self.s["paychecks"]]

    def add_paycheck(self, label, amount, freq, anchor):
        return M.add_paycheck(self.s, label, amount, freq, anchor)

    def edit_paycheck(self, pid, **ch):
        M.edit_paycheck(self.s, pid, **ch)

    def delete_paycheck(self, pid):
        M.delete_paycheck(self.s, pid)

    def rules(self) -> list[dict]:
        names = {e["id"]: e["name"] for e in self.s["envelopes"]}
        return [{**r, "bucket_name": names.get(r["bucket_id"], "")} for r in self.s["rules"]]

    def rules_summary(self) -> dict:
        pct = fixed = ext = 0.0
        for r in self.s["rules"]:
            if not r["active"]:
                continue
            if r["kind"] == "external":
                ext += r["value"] if r["value_type"] == "fixed" else 0.0
                if r["value_type"] == "pct":
                    pct += r["value"]
            elif r["value_type"] == "pct":
                pct += r["value"]
            elif r["value_type"] == "fixed":
                fixed += r["value"]
        return {"pct": round(pct, 2), "fixed": round(fixed, 2), "over": pct > 100}

    def add_rule(self, name, kind, bucket_id, value, value_type, active=True):
        return M.add_rule(self.s, name, kind, bucket_id, value, value_type, active)

    def edit_rule(self, rid, **ch):
        M.edit_rule(self.s, rid, **ch)

    def delete_rule(self, rid):
        M.delete_rule(self.s, rid)

    def toggle_rule(self, rid):
        M.toggle_rule(self.s, rid)

    def delete(self, eid: str):
        M.delete_envelope(self.s, eid)

    def add_bucket(self, name: str, cat_id: str, type: str, target: float,
                   due_day=None, frequency=None, flex: bool = False,
                   target_date=None, notes: str = ""):
        return M.add_envelope(self.s, name, cat_id, type, target,
                              due_day=due_day, frequency=frequency, flex=flex,
                              target_date=target_date, notes=notes)
