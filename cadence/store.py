"""
Cadence store — a per-session in-memory budget, seeded with realistic data.

For the proof-of-concept this holds state in memory (which is exactly how a
single-user NiceGUI session naturally works). Swapping in Supabase later means
implementing the same handful of read/write methods against the DB — the UI
never changes.
"""

from . import money as M


def seed() -> dict:
    """A believable month-in-progress so every screen has something to show."""
    # (name, category, type, target, funded)
    rows = [
        ("Rent",          "Housing",   M.SPEND, 1500, 1500),
        ("Utilities",     "Housing",   M.SPEND,  300,  300),
        ("Groceries",     "Food",      M.SPEND,  400,  300),
        ("Dining Out",    "Food",      M.SPEND,  150,  100),
        ("Gas",           "Transport", M.SPEND,  120,   80),
        ("Car Insurance", "Transport", M.SPEND,  140,  140),
        ("Subscriptions", "Lifestyle", M.SPEND,   60,   60),
        ("Fun Money",     "Lifestyle", M.SPEND,  200,  200),
        ("Vacation Fund", "Future",    M.GOAL,  3000,  850),
        ("Emergency",     "Future",    M.VAULT, 10000, 2000),
    ]
    # Bank cash = everything funded into envelopes + a buffer left Unallocated.
    total_funded = sum(r[4] for r in rows)
    s = M.genesis(opening=total_funded + 800.00)

    cat_color = {"Housing": "#6366f1", "Food": "#10b981", "Transport": "#f59e0b",
                 "Lifestyle": "#ec4899", "Future": "#8b5cf6"}
    cats = {name: M.add_category(s, name, color)["id"] for name, color in cat_color.items()}

    ids = {}
    for name, cat, typ, target, funded in rows:
        eid = M.add_envelope(s, name, cats[cat], typ, target, 0.0)["id"]
        M.fund(s, eid, funded)          # moves money FROM Unallocated (keeps the invariant true)
        ids[name] = eid

    # Some real spending so envelopes show progress, not just full bars.
    for name, amt, desc in [
        ("Rent", 1500, "August rent"),
        ("Utilities", 142, "Power + water"),
        ("Groceries", 286, "Trader Joe's"),
        ("Groceries", 63, "Corner market"),
        ("Dining Out", 88, "Dinner w/ friends"),
        ("Gas", 52, "Shell"),
        ("Subscriptions", 46, "Streaming"),
        ("Fun Money", 120, "Concert tickets"),
    ]:
        M.add_expense(s, ids[name], amt, desc, "2026-08-14")

    return s


class Store:
    """Session-scoped budget state + the view-models the UI renders."""

    def __init__(self):
        self.s = seed()

    # ── headline metrics ──────────────────────────────────────────────────────
    def metrics(self) -> dict:
        un = M.unallocated(self.s)
        rts = M.ready_to_spend(self.s)
        bal = M.available_balance(self.s)
        return {
            "unallocated": un,
            "available_balance": bal,
            "in_buckets": round(rts - un, 2),      # non-vault available (assigned, unspent)
            "in_vaults": round(bal - rts, 2),      # locked savings
            "ready_to_spend": rts,
        }

    # ── buckets grouped by category ───────────────────────────────────────────
    def groups(self) -> list[dict]:
        out = []
        for c in self.s["categories"]:
            envs = [e for e in self.s["envelopes"] if e["cat_id"] == c["id"]]
            if not envs:
                continue
            rows = []
            for e in envs:
                sp = M.spent(self.s, e["id"])
                av = M.available(self.s, e)
                tgt = e["target"] or e["funded"] or 1
                rows.append({
                    "id": e["id"], "name": e["name"], "type": e["type"],
                    "target": e["target"], "funded": e["funded"],
                    "spent": sp, "available": av,
                    "pct": max(0.0, min(1.0, sp / tgt)) if e["type"] == M.SPEND
                           else max(0.0, min(1.0, e["funded"] / (e["target"] or 1))),
                })
            out.append({
                "id": c["id"], "name": c["name"], "color": c["color"],
                "funded": round(sum(r["funded"] for r in rows), 2),
                "available": round(sum(r["available"] for r in rows), 2),
                "rows": rows,
            })
        return out

    # ── single-bucket view (for the assign/manage modal) ──────────────────────
    def bucket(self, eid: str) -> dict:
        e = M.env(self.s, eid)
        sp, av = M.spent(self.s, eid), M.available(self.s, e)
        if e["type"] == M.SPEND:
            funded = e["funded"]
            pct = min(1.0, max(0.0, sp / funded)) if funded > 0 else 0.0
        else:
            funded, sp = e["funded"], 0.0
            pct = min(1.0, max(0.0, funded / e["target"])) if e["target"] else 0.0
        return {"id": eid, "name": e["name"], "type": e["type"], "cat_id": e["cat_id"],
                "target": round(e["target"], 2), "funded": round(funded, 2),
                "spent": round(sp, 2), "available": round(av, 2), "pct": pct,
                "gap": round(max(0.0, e["target"] - e["funded"]), 2)}

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

    def set_funded(self, eid: str, value: float):
        M.set_funded(self.s, eid, value)

    def fund_to_target(self, eid: str):
        e = M.env(self.s, eid)
        gap = round(max(0.0, e["target"] - e["funded"]), 2)
        if gap > 0:
            M.fund(self.s, eid, gap)

    def move(self, src: str, dst: str, amount: float):
        M.move(self.s, src, dst, min(amount, M.env(self.s, src)["funded"]))

    def rename(self, eid: str, name: str):
        M.rename(self.s, eid, name)

    def set_target(self, eid: str, value: float):
        M.set_target(self.s, eid, value)

    def delete(self, eid: str):
        M.delete_envelope(self.s, eid)

    def add_bucket(self, name: str, cat_id: str, type: str, target: float):
        return M.add_envelope(self.s, name, cat_id, type, target)
