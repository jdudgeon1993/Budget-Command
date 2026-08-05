"""
Cadence live data — the real Supabase budget, read through Cura's proven layer.

We deliberately reuse webapp.db (the tested Supabase queries) and webapp.formulas
(the tested money math) so Cadence shows exactly the same numbers as the current
app — this is a new UI on a proven brain, not a reimplementation. Only the
presentation is new. Requires SUPABASE_URL / SUPABASE_ANON_KEY in the env.
"""
from webapp import db as DB, formulas as F

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
        unalloc = F.ready_to_spend(months, acc, bks, txs)          # money with no job yet
        nonvault = sum(F.bucket_available(b, self._month, months, txs)
                       for b in bks if b.get("type") != "vault")
        return {
            "available_balance": round(F.total_cash(acc, txs), 2),
            "unallocated": round(unalloc, 2),
            "ready_to_spend": round(unalloc + nonvault, 2),
        }

    # ── envelopes grouped by category ─────────────────────────────────────────
    def groups(self) -> list[dict]:
        txs, months = self.data["txs"], self.data["months"]
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
            rows = []
            for b in sorted(bks, key=lambda x: x.get("order", 0)):
                typ = _TYPE.get(b.get("type", "expense"), "spend")
                avail = round(F.bucket_available(b, self._month, months, txs), 2)
                sp = round(F.b_spent(self._mid, b["id"], txs), 2)
                if typ == "spend":
                    funded = round(avail + sp, 2)
                    target = F.b_budget(self._month, b["id"]) or float(b.get("defaultBudget") or b.get("dueAmount") or 0)
                    pct = min(1.0, max(0.0, sp / funded)) if funded > 0 else 0.0
                else:
                    funded, sp = avail, 0.0
                    target = float(b.get("targetAmount") or 0)
                    pct = min(1.0, max(0.0, funded / target)) if target > 0 else 0.0
                rows.append({"id": b["id"], "name": b["name"], "type": typ,
                             "target": round(target, 2), "funded": funded,
                             "spent": sp, "available": avail, "pct": pct})
            out.append({"id": c["id"], "name": c["name"],
                        "color": c.get("color") or _FALLBACK[i % len(_FALLBACK)],
                        "funded": round(sum(r["funded"] for r in rows), 2),
                        "available": round(sum(r["available"] for r in rows), 2),
                        "rows": rows})
        return out

    # ── live funding (writes the month allocation, like Cura's Distribute) ────
    def fund(self, bid: str, amount: float):
        DB.ensure_month(self.uid, self.token, self._mid)
        new = max(0.0, round(F.b_alloc(self._month, bid) + amount, 2))
        DB.upsert_alloc(self.uid, self.token, self._mid, bid, new)
        self._load()

    def defund(self, bid: str, amount: float):
        self.fund(bid, -amount)
