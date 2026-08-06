"""
Cadence live data — the real Supabase budget, read through Cura's proven layer.

Uses Cadence's own copies of the proven Supabase queries (supabase_io) and money
math (formulas) — self-contained so this service deploys from cadence/ alone,
while still producing exactly the same numbers as Cura. Requires SUPABASE_URL /
SUPABASE_ANON_KEY in the env.
"""
from . import supabase_io as DB, formulas as F, money as MZ

# bcc bucket type → Cadence type
_TYPE = {"expense": "spend", "vault": "vault", "goal": "goal", "sinking": "goal"}
_FALLBACK = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6", "#f43f5e"]


def sign_in(email: str, password: str) -> dict:
    r = DB.sign_in(email, password)
    return {"token": r["access_token"], "uid": r["user_id"], "email": r.get("user_email", "")}


class LiveStore:
    """Same interface as the seed Store — metrics(), groups(), fund(), defund() —
    but backed by the user's real Supabase data."""

    def __init__(self, uid: str, token: str, email: str = ""):
        self.uid, self.token, self.email = uid, token, email
        self._load()

    def _load(self):
        self.data = DB.load_all(self.uid, self.token)
        self._mid = F.current_month_id()
        self._month = next((m for m in self.data["months"] if m["id"] == self._mid),
                           {"id": self._mid, "allocations": {}, "budgets": {}, "handledBuckets": {}})

    def _buckets(self):
        return [b for b in self.data["buckets"] if not b.get("archived")]

    # ── headline metrics (identical definitions to Cura) ──────────────────────
    def metrics(self) -> dict:
        acc, txs, months, bks = self.data["accounts"], self.data["txs"], self.data["months"], self._buckets()
        cash = F.budget_bal(acc, txs)              # CHECKING only — savings excluded
        unalloc = F.ready_to_spend(months, acc, bks, txs)          # money with no job yet
        return {
            "unallocated": round(unalloc, 2),
            "cash": round(cash, 2),                # the checking account total
            "in_buckets": round(cash - unalloc, 2),  # everything assigned to a bucket
        }

    # ── display row for one real bucket (shared by groups() + bucket()) ───────
    def _row(self, b: dict) -> dict:
        typ = _TYPE.get(b.get("type", "expense"), "spend")
        av = round(F.bucket_available(b, self._month, self.data["months"], self.data["txs"]), 2)
        sp = round(F.b_spent(self._mid, b["id"], self.data["txs"]), 2)
        if typ == "spend":
            funded = round(av + sp, 2)
            target = F.b_budget(self._month, b["id"]) or float(b.get("defaultBudget") or b.get("dueAmount") or 0)
            pct = min(1.0, max(0.0, sp / funded)) if funded > 0 else 0.0
        else:
            funded, sp = av, 0.0
            target = float(b.get("targetAmount") or 0)
            pct = min(1.0, max(0.0, funded / target)) if target > 0 else 0.0
        due_day = MZ._norm_due_day(b.get("dueDay"))   # keeps "eom" as-is; ints pass through
        flex = bool(b.get("flex"))
        handled = bool((self._month.get("handledBuckets") or {}).get(b["id"]))
        gap = round(max(0.0, target - funded), 2)
        d = MZ.days_until(due_day)
        # Goals carry their own cadence (contribFreq) + a target month; expenses use payFreq.
        frequency = (b.get("contribFreq") if typ == "goal" else b.get("payFreq")) or None
        return {"id": b["id"], "name": b["name"], "type": typ, "cat_id": b.get("catId", ""),
                "target": round(target, 2), "funded": funded, "spent": sp, "available": av,
                "pct": pct, "gap": gap, "due_day": due_day, "frequency": frequency,
                "flex": flex, "handled": handled,
                "target_date": b.get("targetDate") or None, "notes": b.get("notes") or "",
                **self._split_fields(b, target),
                "days_until_due": d, "status": MZ.status(av, gap, d, flex, handled),
                "urgency": MZ.urgency_score(av, gap, d, flex, handled, typ == "vault")}

    @staticmethod
    def _split_fields(b: dict, target: float) -> dict:
        its = [{"id": it["id"], "name": it["name"], "amount": round(it["amount"], 2),
                "due_day": MZ._norm_due_day(it["due_day"]), "paid": bool(it["paid"])}
               for it in b.get("items", [])]
        total = round(sum(i["amount"] for i in its), 2)
        return {"split": bool(b.get("split")), "items": its, "items_total": total,
                "unspoken": round(max(0.0, target - total), 2),
                "items_paid": sum(1 for i in its if i["paid"])}

    def groups(self) -> list[dict]:
        cats = sorted((c for c in self.data["cats"] if not c.get("archived")),
                      key=lambda c: c.get("order", 0))
        by_cat: dict[str, list] = {}
        for b in self._buckets():
            by_cat.setdefault(b.get("catId", ""), []).append(b)
        out = []
        for i, c in enumerate(cats):
            bks = by_cat.get(c["id"], [])
            if not bks:
                continue
            rows = sorted((self._row(b) for b in bks), key=lambda r: r["urgency"], reverse=True)
            out.append({"id": c["id"], "name": c["name"],
                        "color": c.get("color") or _FALLBACK[i % len(_FALLBACK)],
                        "funded": round(sum(r["funded"] for r in rows), 2),
                        "available": round(sum(r["available"] for r in rows), 2),
                        "rows": rows})
        return out

    def bucket(self, bid: str) -> dict:
        return self._row(next(b for b in self._buckets() if b["id"] == bid))

    def _all_rows(self) -> list[dict]:
        return [self._row(b) for b in self._buckets()]

    def distribute_plan(self) -> dict:
        from .store import _greedy_plan
        return _greedy_plan(self._all_rows(), self.metrics()["unallocated"])

    def fund_sources(self, exclude: str) -> list[dict]:
        out = [{"id": "unallocated", "name": "Unallocated", "avail": self.metrics()["unallocated"]}]
        for b in self._buckets():
            if b["id"] == exclude:
                continue
            av = round(F.bucket_available(b, self._month, self.data["months"], self.data["txs"]), 2)
            if av > 0.005:
                out.append({"id": b["id"], "name": b["name"], "avail": av})
        return out

    def assign(self, dst: str, source_id: str, amount: float):
        if source_id == "unallocated":
            self.fund(dst, amount)
        else:
            self.move(source_id, dst, amount)

    def categories(self) -> list[dict]:
        return [{"id": c["id"], "name": c["name"]}
                for c in self.data["cats"] if not c.get("archived")]

    # ── ledger (read real transactions; writes land with the rest) ────────────
    def _bucket_meta(self) -> dict:
        cc = {c["id"]: (c.get("color") or "#9aa0b5") for c in self.data["cats"]}
        return {b["id"]: (b["name"], cc.get(b.get("catId", ""), "#9aa0b5"))
                for b in self.data["buckets"]}

    def transactions(self, limit: int = 300) -> list[dict]:
        meta = self._bucket_meta()
        acct = {a["id"]: a["name"] for a in self.data["accounts"]}
        out = []
        for i, t in enumerate(self.data["txs"]):
            typ = t.get("type")
            bid = t.get("bucketId") or None
            amt = float(t.get("amount") or 0)
            if typ == "out" and amt < 0:              # negative out = a refund
                kind, (name, color) = "refund", meta.get(bid, ("", "#9aa0b5"))
                amt = -amt
            elif typ == "out" and bid:
                kind, (name, color) = "expense", meta.get(bid, ("", "#9aa0b5"))
            elif typ == "out":                        # no bucket = money left the budget
                kind, name, color, bid = "transfer", (t.get("desc") or "Transfer"), "#f59e0b", None
            elif typ == "in":
                kind, name, color, bid = "income", "Income", "#10b981", None
            elif typ == "xfr":                        # a real account-to-account move
                frm, to = acct.get(t.get("accountId"), "?"), acct.get(t.get("toAccountId"), "?")
                kind, name, color, bid = "transfer", f"{frm} → {to}", "#f59e0b", None
            else:
                continue
            out.append({"id": t["id"], "kind": kind, "amount": round(amt, 2),
                        "date": t.get("date") or "", "desc": t.get("desc") or "",
                        "bucket_id": bid, "bucket_name": name, "color": color,
                        "from_acct": t.get("accountId"), "to_acct": t.get("toAccountId"), "_seq": i})
        out.sort(key=lambda r: (r["date"], r["_seq"]), reverse=True)
        return out[:limit]

    def ledger_metrics(self) -> dict:
        txs = self.data["txs"]
        income = spent = 0.0
        for t in txs:
            if t.get("monthId") != self._mid:
                continue
            if t["type"] == "in":
                income += float(t.get("amount") or 0)
            elif t["type"] == "out":
                spent += float(t.get("amount") or 0)
        return {"balance": round(F.budget_bal(self.data["accounts"], txs), 2),
                "income": round(income, 2), "spent": round(spent, 2)}

    def payees(self) -> list[str]:
        seen = []
        for t in self.data["txs"]:
            d = (t.get("desc") or "").strip()
            if d and d not in seen:
                seen.append(d)
        return seen[:40]

    # ── settings: income + rules (read real data; writes land with the rest) ──
    def paychecks(self) -> list[dict]:
        fm = {7: "weekly", 14: "biweekly", 15: "semimonthly", 30: "monthly"}
        out = []
        for p in self.data["paychecks"]:
            try:
                freq = fm.get(int(p.get("freq", 14)), "biweekly")
            except (ValueError, TypeError):
                freq = "biweekly"
            anchor = p.get("anchor_date") or p.get("anchorDate") or ""
            out.append({"id": p.get("id", ""), "label": p.get("label", "Paycheck"),
                        "amount": round(float(p.get("amount") or 0), 2),
                        "freq": freq, "anchor": str(anchor)[:10]})
        return out

    def rules(self) -> list[dict]:
        names = {b["id"]: b["name"] for b in self._buckets()}
        out = []
        for r in self.data["allocationRules"]:
            kind = "external" if r.get("rule_type") == "external" else "internal"
            bid = r.get("bucket_id") or r.get("bucketId") or None
            vtype = r.get("value_type") or r.get("type") or "fixed"
            out.append({"id": r.get("id", ""), "name": r.get("name", "Rule"), "kind": kind,
                        "bucket_id": bid, "bucket_name": names.get(bid, ""),
                        "value": round(float(r.get("value") or 0), 2),
                        "value_type": vtype if vtype in ("fixed", "pct", "fund") else "fixed",
                        "active": bool(r.get("active", True))})
        return out

    def rules_summary(self) -> dict:
        pct = fixed = 0.0
        for r in self.rules():
            if not r["active"]:
                continue
            if r["value_type"] == "pct":
                pct += r["value"]
            elif r["value_type"] == "fixed" and r["kind"] == "internal":
                fixed += r["value"]
        return {"pct": round(pct, 2), "fixed": round(fixed, 2), "over": pct > 100}

    # ── assignment (writes the month allocation, like Cura's Distribute) ──────
    def fund(self, bid: str, amount: float):
        DB.ensure_month(self.uid, self.token, self._mid)
        new = max(0.0, round(F.b_alloc(self._month, bid) + amount, 2))
        DB.upsert_alloc(self.uid, self.token, self._mid, bid, new)
        self._load()

    def defund(self, bid: str, amount: float):
        self.fund(bid, -amount)

    def set_funded(self, bid: str, value: float):
        cur = F.bucket_available(next(b for b in self._buckets() if b["id"] == bid),
                                 self._month, self.data["months"], self.data["txs"])
        self.fund(bid, round(value - cur, 2))

    def fund_to_target(self, bid: str):
        gap = self.bucket(bid)["gap"]
        if gap > 0:
            self.fund(bid, gap)

    def move(self, src: str, dst: str, amount: float):
        self.defund(src, amount)
        self.fund(dst, amount)

    # ── live writes ───────────────────────────────────────────────────────────
    # Cadence type → bcc bucket type. Money columns split by type: expense uses
    # default_budget/pay_freq; goal & vault use target_amount/contrib_freq.
    _DB_TYPE = {"spend": "expense", "goal": "goal", "vault": "vault"}
    _FREQ_TO_INT = {"weekly": 7, "biweekly": 14, "semimonthly": 15, "monthly": 30}

    def _raw_bucket(self, bid: str) -> dict:
        return next(b for b in self.data["buckets"] if b["id"] == bid)

    def _budget_account_id(self) -> str:
        for a in self.data["accounts"]:
            if a.get("type") == "budget" and not a.get("archived"):
                return a["id"]
        return self.data["accounts"][0]["id"] if self.data["accounts"] else ""

    @staticmethod
    def _mid_for(iso: str) -> str:
        from datetime import date as _d
        try:
            d = _d.fromisoformat(str(iso)[:10])
        except (ValueError, TypeError):
            d = _d.today()
        return F.month_id(d.year, d.month - 1)

    def _bucket_update(self, bid: str, fields: dict):
        DB.update(self.token, "bcc_buckets", self.uid, "id", bid, fields)
        self._load()

    # bucket structure
    def rename(self, bid: str, name: str):
        self._bucket_update(bid, {"name": (name or "").strip() or "Bucket"})

    def set_target(self, bid: str, value: float):
        col = "default_budget" if self._raw_bucket(bid)["type"] == "expense" else "target_amount"
        self._bucket_update(bid, {col: round(max(0.0, value), 2)})

    def set_due_day(self, bid: str, day):
        self._bucket_update(bid, {"due_day": MZ._norm_due_day(day)})

    def set_frequency(self, bid: str, freq):
        col = "contrib_freq" if self._raw_bucket(bid)["type"] in ("goal", "sinking") else "pay_freq"
        self._bucket_update(bid, {col: freq or None})

    def set_flex(self, bid: str, flex: bool):
        self._bucket_update(bid, {"flex": bool(flex)})

    def set_target_date(self, bid: str, target_date):
        self._bucket_update(bid, {"target_date": (str(target_date).strip() or None) if target_date else None})

    def set_notes(self, bid: str, notes):
        self._bucket_update(bid, {"notes": (notes or "").strip()})

    def toggle_handled(self, bid: str):
        cur = bool((self._month.get("handledBuckets") or {}).get(bid))
        DB.set_handled(self.token, self.uid, self._mid, bid, not cur)
        self._load()

    def delete(self, bid: str):
        # Archive (money it held stops being claimed → returns to Ready to Spend).
        self._bucket_update(bid, {"archived": True})

    def add_bucket(self, name: str, cat_id: str, type: str, target: float,
                   due_day=None, frequency=None, flex: bool = False,
                   target_date=None, notes: str = ""):
        dbtype = self._DB_TYPE.get(type, "expense")
        row = {"id": DB.new_id(), "user_id": self.uid, "cat_id": cat_id or None,
               "name": (name or "New bucket").strip(), "type": dbtype,
               "flex": bool(flex), "notes": notes or "", "archived": False,
               "sort_order": len(self.data["buckets"]) + 1}
        if dbtype == "expense":
            row.update({"default_budget": round(target or 0, 2),
                        "due_day": MZ._norm_due_day(due_day), "pay_freq": frequency or None})
        else:
            row.update({"target_amount": round(target or 0, 2),
                        "target_date": target_date or None, "contrib_freq": frequency or None})
        DB.insert(self.token, "bcc_buckets", row)
        self._load()
        return {"id": row["id"]}

    # ledger transactions
    def _insert_tx(self, typ: str, amount: float, bid, desc: str, when: str, income_type=None):
        row = {"id": DB.new_id(), "user_id": self.uid, "account_id": self._budget_account_id(),
               "month_id": self._mid_for(when), "type": typ, "amount": round(float(amount), 2),
               "date": (when or "")[:10], "description": desc or "", "bucket_id": bid or None}
        if income_type:
            row["income_type"] = income_type
        DB.insert(self.token, "bcc_transactions", row)
        self._load()

    def record_spend(self, bid: str, amount: float, desc: str = ""):
        from datetime import date as _d
        self._insert_tx("out", amount, bid, desc, _d.today().isoformat())

    def add_transaction(self, kind: str, amount: float, bucket_id, desc: str, date: str):
        if kind == "income":
            self._insert_tx("in", amount, None, desc, date, income_type="other")
        elif kind == "refund":                       # money back to a bucket = negative spend
            self._insert_tx("out", -abs(float(amount)), bucket_id, desc, date)
        else:
            self._insert_tx("out", amount, bucket_id, desc, date)

    def edit_transaction(self, tid: str, amount=None, desc=None, date=None, envelope_id=None):
        fields = {}
        raw = next((t for t in self.data["txs"] if t["id"] == tid), None)
        if amount is not None:
            amt = round(float(amount), 2)
            # keep the sign a refund (negative out) already carries
            if raw and raw.get("type") == "out" and raw.get("amount", 0) < 0:
                amt = -abs(amt)
            fields["amount"] = amt
        if desc is not None:
            fields["description"] = desc
        if date is not None:
            fields["date"] = str(date)[:10]
            fields["month_id"] = self._mid_for(date)
        if envelope_id:
            fields["bucket_id"] = envelope_id
        if fields:
            DB.update(self.token, "bcc_transactions", self.uid, "id", tid, fields)
            self._load()

    def delete_transaction(self, tid: str):
        DB.delete(self.token, "bcc_transactions", self.uid, "id", tid)
        self._load()

    def accounts(self) -> list[dict]:
        return [{"id": a["id"], "name": a["name"], "type": a.get("type", "budget"),
                 "balance": round(F.acct_balance(a, self.data["txs"]), 2)}
                for a in self.data["accounts"] if not a.get("archived")]

    def add_transfer(self, from_id: str, to_id: str, amount: float, desc: str = "", date: str = ""):
        from datetime import date as _d
        when = (date or _d.today().isoformat())[:10]
        DB.insert(self.token, "bcc_transactions", {
            "id": DB.new_id(), "user_id": self.uid, "account_id": from_id,
            "to_account_id": to_id, "month_id": self._mid_for(when), "type": "xfr",
            "amount": round(float(amount), 2), "date": when,
            "description": desc or "", "bucket_id": None})
        self._load()

    def distribute_income(self, amount: float) -> list[dict]:
        """Auto-apply allocation rules to a paycheck: external → an out that debits
        the budget, internal → a bucket allocation."""
        from datetime import date as _d
        amount = round(float(amount), 2)
        DB.ensure_month(self.uid, self.token, self._mid)
        today, acct, applied = _d.today().isoformat(), self._budget_account_id(), []
        rules = self.rules()
        for r in rules:
            if not (r["active"] and r["kind"] == "external"):
                continue
            amt = round(amount * r["value"] / 100 if r["value_type"] == "pct"
                        else (r["value"] if r["value_type"] == "fixed" else 0), 2)
            if amt > 0.005:
                DB.insert(self.token, "bcc_transactions", {
                    "id": DB.new_id(), "user_id": self.uid, "account_id": acct,
                    "month_id": self._mid, "type": "out", "amount": amt,
                    "date": today, "description": r["name"], "bucket_id": None})
                applied.append({"name": r["name"], "kind": "external", "amount": amt})
        for r in rules:
            if not (r["active"] and r["kind"] == "internal" and r["bucket_id"]):
                continue
            bid = r["bucket_id"]
            if r["value_type"] == "fund":
                amt = round(max(0.0, self.bucket(bid)["gap"]), 2)
            else:
                amt = round(amount * r["value"] / 100 if r["value_type"] == "pct" else r["value"], 2)
            if amt > 0.005:
                new = round(F.b_alloc(self._month, bid) + amt, 2)
                DB.upsert_alloc(self.uid, self.token, self._mid, bid, new)
                applied.append({"name": r["name"], "kind": "internal",
                                "bucket": r["bucket_name"], "amount": amt})
        self._load()
        return applied

    # settings: paychecks
    def add_paycheck(self, label, amount, freq, anchor):
        DB.insert(self.token, "bcc_paychecks", {
            "id": DB.new_id(), "user_id": self.uid, "label": (label or "Paycheck").strip(),
            "amount": round(float(amount or 0), 2), "freq": self._FREQ_TO_INT.get(freq, 14),
            "anchor_date": (anchor or "")[:10] or None})
        self._load()

    def edit_paycheck(self, pid, label=None, amount=None, freq=None, anchor=None):
        fields = {}
        if label is not None:
            fields["label"] = label.strip() or "Paycheck"
        if amount is not None:
            fields["amount"] = round(float(amount or 0), 2)
        if freq is not None:
            fields["freq"] = self._FREQ_TO_INT.get(freq, 14)
        if anchor is not None:
            fields["anchor_date"] = (anchor or "")[:10] or None
        if fields:
            DB.update(self.token, "bcc_paychecks", self.uid, "id", pid, fields)
            self._load()

    def delete_paycheck(self, pid):
        DB.delete(self.token, "bcc_paychecks", self.uid, "id", pid)
        self._load()

    # settings: allocation rules
    def add_rule(self, name, kind, bucket_id, value, value_type, active=True):
        DB.insert(self.token, "bcc_allocation_rules", {
            "id": DB.new_id(), "user_id": self.uid, "name": (name or "Rule").strip(),
            "rule_type": kind if kind in ("internal", "external") else "internal",
            "bucket_id": bucket_id or None, "value": round(float(value or 0), 2),
            "value_type": value_type if value_type in ("fixed", "pct", "fund") else "fixed",
            "active": bool(active)})
        self._load()

    def edit_rule(self, rid, name=None, kind=None, bucket_id=..., value=None, value_type=None, active=None):
        fields = {}
        if name is not None:
            fields["name"] = name.strip() or "Rule"
        if kind is not None:
            fields["rule_type"] = kind if kind in ("internal", "external") else "internal"
        if bucket_id is not ...:
            fields["bucket_id"] = bucket_id or None
        if value is not None:
            fields["value"] = round(float(value or 0), 2)
        if value_type is not None:
            fields["value_type"] = value_type if value_type in ("fixed", "pct", "fund") else "fixed"
        if active is not None:
            fields["active"] = bool(active)
        if fields:
            DB.update(self.token, "bcc_allocation_rules", self.uid, "id", rid, fields)
            self._load()

    def delete_rule(self, rid):
        DB.delete(self.token, "bcc_allocation_rules", self.uid, "id", rid)
        self._load()

    def toggle_rule(self, rid):
        cur = next((r for r in self.rules() if r["id"] == rid), None)
        DB.update(self.token, "bcc_allocation_rules", self.uid, "id", rid,
                  {"active": not (cur["active"] if cur else True)})
        self._load()

    # split buckets (bill schedule) — bcc_buckets.split + bcc_bucket_items
    def set_split(self, bid: str, on: bool):
        self._bucket_update(bid, {"split": bool(on)})

    def add_item(self, bid: str, name: str, amount: float, due_day=None):
        DB.insert(self.token, "bcc_bucket_items", {
            "id": DB.new_id(), "user_id": self.uid, "bucket_id": bid,
            "name": (name or "Item").strip(), "amount": round(float(amount or 0), 2),
            "due_day": MZ._norm_due_day(due_day), "paid": False,
            "sort_order": sum(len(b.get("items", [])) for b in self._buckets())})
        self._load()

    def edit_item(self, bid: str, iid: str, name=None, amount=None, due_day=None):
        fields = {}
        if name is not None:
            fields["name"] = name.strip() or "Item"
        if amount is not None:
            fields["amount"] = round(float(amount or 0), 2)
        if due_day is not None:
            fields["due_day"] = MZ._norm_due_day(due_day)
        if fields:
            DB.update(self.token, "bcc_bucket_items", self.uid, "id", iid, fields)
            self._load()

    def remove_item(self, bid: str, iid: str):
        DB.delete(self.token, "bcc_bucket_items", self.uid, "id", iid)
        self._load()

    def toggle_item_paid(self, bid: str, iid: str):
        it = next((x for b in self._buckets() for x in b.get("items", []) if x["id"] == iid), None)
        DB.update(self.token, "bcc_bucket_items", self.uid, "id", iid,
                  {"paid": not (it["paid"] if it else False)})
        self._load()
