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
                "days_until_due": d, "status": MZ.status(av, gap, d, flex, handled),
                "urgency": MZ.urgency_score(av, gap, d, flex, handled, typ == "vault")}

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
        out = []
        for i, t in enumerate(self.data["txs"]):
            typ = t.get("type")
            if typ == "out":
                kind, (name, color) = "expense", meta.get(t.get("bucketId"), ("", "#9aa0b5"))
            elif typ == "in":
                kind, name, color = "income", "Income", "#10b981"
            else:
                continue                              # account transfers aren't ledger rows here
            out.append({"id": t["id"], "kind": kind, "amount": round(float(t.get("amount") or 0), 2),
                        "date": t.get("date") or "", "desc": t.get("desc") or "",
                        "bucket_id": t.get("bucketId") or None, "bucket_name": name,
                        "color": color, "_seq": i})
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

    # Structure edits land next once you pick the flow — safe no-ops in live for now.
    def _soon(self, *a, **k):
        raise NotImplementedError("Editing buckets (rename/target/due/delete/spend) is coming "
                                  "to the live app next — it's fully working in the demo.")
    rename = set_target = delete = add_bucket = _soon
    set_due_day = set_frequency = set_flex = toggle_handled = record_spend = _soon
    set_target_date = set_notes = _soon
    add_transaction = edit_transaction = delete_transaction = _soon
    add_paycheck = edit_paycheck = delete_paycheck = _soon
    add_rule = edit_rule = delete_rule = toggle_rule = _soon
