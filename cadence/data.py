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
        try:
            due_day = int(b.get("dueDay"))
        except (ValueError, TypeError):
            due_day = None
        flex = bool(b.get("flex"))
        handled = bool((self._month.get("handledBuckets") or {}).get(b["id"]))
        gap = round(max(0.0, target - funded), 2)
        d = MZ.days_until(due_day)
        return {"id": b["id"], "name": b["name"], "type": typ, "cat_id": b.get("catId", ""),
                "target": round(target, 2), "funded": funded, "spent": sp, "available": av,
                "pct": pct, "gap": gap, "due_day": due_day, "frequency": b.get("payFreq"),
                "flex": flex, "handled": handled, "days_until_due": d,
                "status": MZ.status(av, gap, d, flex, handled),
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
