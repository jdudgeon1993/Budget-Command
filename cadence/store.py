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
        ("Groceries",     "Food",      M.SPEND,  400,  400),
        ("Dining Out",    "Food",      M.SPEND,  150,  150),
        ("Gas",           "Transport", M.SPEND,  120,  120),
        ("Car Insurance", "Transport", M.SPEND,  140,  140),
        ("Subscriptions", "Lifestyle", M.SPEND,   60,   60),
        ("Fun Money",     "Lifestyle", M.SPEND,  200,  200),
        ("Vacation Fund", "Future",    M.GOAL,  3000,  850),
        ("Emergency",     "Future",    M.VAULT, 10000, 2000),
    ]
    # Bank cash = everything funded into envelopes + a buffer left Unallocated.
    total_funded = sum(r[4] for r in rows)
    s = M.genesis(opening=total_funded + 650.00)

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
        return {
            "ready_to_spend": M.ready_to_spend(self.s),
            "unallocated": M.unallocated(self.s),
            "available_balance": M.available_balance(self.s),
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

    # ── live operations ───────────────────────────────────────────────────────
    def fund(self, eid: str, amount: float):
        M.fund(self.s, eid, amount)

    def defund(self, eid: str, amount: float):
        M.defund(self.s, eid, min(amount, M.env(self.s, eid)["funded"]))

    def add_envelope(self, name: str, cat_id: str, type: str, target: float):
        return M.add_envelope(self.s, name, cat_id, type, target)

    def categories(self) -> list[dict]:
        return self.s["categories"]
