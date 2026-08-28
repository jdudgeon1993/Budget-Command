"""
Cadence live data — the real Supabase budget, read through Cura's proven layer.

Uses Cadence's own copies of the proven Supabase queries (supabase_io) and money
math (formulas) — self-contained so this service deploys from cadence/ alone,
while still producing exactly the same numbers as Cura. Requires SUPABASE_URL /
SUPABASE_ANON_KEY in the env.
"""
from . import supabase_io as DB, formulas as F, money as MZ, forecast as FC
from .store import _effective_days, _build_steps

# bcc bucket type → Cadence type
_TYPE = {"expense": "spend", "vault": "vault", "goal": "goal", "sinking": "goal"}
_FALLBACK = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6", "#f43f5e"]
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_label(mid: str) -> str:
    """m_2026_7 → 'Aug 2026' (month is 0-indexed)."""
    try:
        y, m = F.parse_month_id(mid)
        return f"{_MONTHS[m]} {y}"
    except (ValueError, IndexError):
        return mid


def sign_in(email: str, password: str) -> dict:
    r = DB.sign_in(email, password)
    return {"token": r["access_token"], "uid": r["user_id"], "email": r.get("user_email", "")}


class LiveStore:
    """Same interface as the seed Store — metrics(), groups(), fund(), defund() —
    but backed by the user's real Supabase data."""

    def __init__(self, uid: str, token: str, email: str = ""):
        self.uid, self.token, self.email = uid, token, email
        self._view_mid = None          # None = follow today; else a browsed month
        self._load()

    def _load(self):
        """Full load — every table. Caches the raw rows so later writes can refetch
        just what they touched (see _reload)."""
        self._raw = DB.fetch_raw(self.uid, self.token)
        self._assemble()

    def _reload(self, *keys):
        """Targeted reload after a write: refetch only the table(s) that changed,
        keeping Supabase the source of truth (the money invariant can't drift) while
        skipping the other eleven fetches. 'months_raw' is included wherever a write
        may have created the current month via ensure_month."""
        self._raw.update(DB.fetch_raw(self.uid, self.token, keys))
        self._assemble()

    def _assemble(self):
        self.data = DB.assemble(self._raw)
        # The browsed month drives Buckets display + where funding/spending lands;
        # RTS stays anchored to today inside ready_to_spend regardless.
        self._mid = self._view_mid or F.current_month_id()
        self._month = next((m for m in self.data["months"] if m["id"] == self._mid),
                           {"id": self._mid, "allocations": {}, "budgets": {}, "handledBuckets": {}})

    # ── month navigation ──────────────────────────────────────────────────────
    def set_view_month(self, mid):
        """Browse a different month (None returns to today). Re-derives from the
        already-cached rows — no network — since every month is loaded up front."""
        self._view_mid = None if (mid is None or mid == F.current_month_id()) else mid
        self._assemble()

    def view_month(self) -> dict:
        """Current browse state for the month bar: the viewed month, whether it's
        today, and the list of months you can jump to (past → a few for planning)."""
        today = F.current_month_id()
        known = {m["id"] for m in self.data["months"]}
        # every real month, today, and 3 months out for forward planning
        mids = set(known) | {today} | {F.month_offset(today, n) for n in range(1, 4)}
        ordered = sorted(mids, key=F.month_sort_key)
        opts = [{"mid": mid, "label": _month_label(mid),
                 "rel": ("future" if F.month_sort_key(mid) > F.month_sort_key(today)
                         else "past" if F.month_sort_key(mid) < F.month_sort_key(today) else "current")}
                for mid in ordered]
        return {"mid": self._mid, "today": today, "is_current": self._mid == today,
                "label": _month_label(self._mid), "options": opts}

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
            "age_of_money": F.age_of_money(acc, txs),
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
        # Goals carry their own cadence (contribFreq) + a target month; expenses use payFreq.
        frequency = (b.get("contribFreq") if typ == "goal" else b.get("payFreq")) or None
        sf = self._split_fields(b, av)
        if sf["split"]:                          # the schedule drives the number
            target = sf["items_total"]
            gap = round(max(0.0, target - funded), 2)
        d = _effective_days(MZ.days_until(due_day), sf["split"], sf["items"])
        return {"id": b["id"], "name": b["name"], "type": typ, "cat_id": b.get("catId", ""),
                "target": round(target, 2), "funded": funded, "spent": sp, "available": av,
                "pct": pct, "gap": gap, "due_day": due_day, "frequency": frequency,
                "flex": flex, "handled": handled,
                "target_date": b.get("targetDate") or None, "notes": b.get("notes") or "",
                **sf,
                "days_until_due": d, "status": MZ.status(av, gap, d, flex, handled),
                "urgency": MZ.urgency_score(av, gap, d, flex, handled, typ == "vault")}

    @staticmethod
    def _split_fields(b: dict, available: float) -> dict:
        raw = [{"id": it["id"], "name": it["name"], "amount": round(it["amount"], 2),
                "due_day": MZ._norm_due_day(it["due_day"]), "paid": bool(it["paid"])}
               for it in b.get("items", [])]
        total = round(sum(i["amount"] for i in raw), 2)
        split = bool(b.get("split"))
        # split → each bill learns its own funded state from the shared pool
        items = MZ.item_funding(raw, available) if split else MZ.item_rows(raw)
        return {"split": split, "items": items, "items_total": total,
                "items_paid": sum(1 for i in items if i.get("paid"))}

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
        b = next((x for x in self._buckets() if x["id"] == bid), None)
        if b is None:
            raise ValueError("That bucket isn't there anymore — it may have just been merged, archived, or removed. Refresh and try again.")
        return self._row(b)

    def _all_rows(self) -> list[dict]:
        return [self._row(b) for b in self._buckets()]

    def orphaned_buckets(self) -> list[dict]:
        """Buckets filed under a category that's missing or archived — groups()
        only shows buckets whose category still exists, so these are real, funded,
        and completely invisible on the Buckets screen until re-filed."""
        live_cats = {c["id"] for c in self.data["cats"] if not c.get("archived")}
        return [self._row(b) for b in self._buckets() if b.get("catId") not in live_cats]

    def recategorize_bucket(self, bid: str, cat_id: str):
        self._bucket_update(bid, {"cat_id": cat_id})

    def duplicate_buckets(self) -> list[list[dict]]:
        """Buckets sharing a name (case/space-insensitive) — most often two of the
        same subscription/bill after a split exploded one that already existed as
        its own bucket. Scans every non-archived bucket (orphaned-category ones
        included), since a duplicate is often exactly one visible + one hidden."""
        groups: dict[str, list[dict]] = {}
        for b in self._buckets():
            key = (b.get("name") or "").strip().lower()
            if key:
                groups.setdefault(key, []).append(self._row(b))
        return [rows for rows in groups.values() if len(rows) > 1]

    def merge_buckets(self, keep_id: str, drop_id: str):
        """Fold `drop` into `keep`: drop's funded money and every transaction that
        ever pointed at it move to keep, then drop is archived. keep's name/due
        date/category/type are untouched. Money is conserved exactly — this only
        relabels which bucket funded dollars and history belong to."""
        if keep_id == drop_id:
            return
        keep, drop = self.bucket(keep_id), self.bucket(drop_id)
        if drop["type"] == "vault" or keep["type"] == "vault":
            raise ValueError("Vaults are locked — release one to Ready to Assign and delete it instead of merging.")
        if drop.get("split") and drop.get("items"):
            raise ValueError(f'"{drop["name"]}" has its own bill schedule — clear or move its bills first.')
        amt = round(drop["funded"], 2)
        if amt > 0.005:
            self.move(drop_id, keep_id, amt)
        tids = [t["id"] for t in self.transactions(limit=10000) if t.get("bucket_id") == drop_id]
        if tids:
            for tid in tids:
                DB.update(self.token, "bcc_transactions", self.uid, "id", tid, {"bucket_id": keep_id})
            self._reload("txs_raw")
        self.delete(drop_id)

    def distribute_steps(self, paycheck_amount=None) -> dict:
        return _build_steps(self._all_rows(), self.rules(), self.metrics()["unallocated"], paycheck_amount)

    def default_transfer_accounts(self):
        frm = self._budget_account_id()
        to = next((a["id"] for a in self.data["accounts"]
                   if a.get("type") != "budget" and not a.get("archived")), frm)
        return (frm, to)

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
        live = [b.get("catId", "") for b in self._buckets()]
        cats = sorted((c for c in self.data["cats"] if not c.get("archived")),
                      key=lambda c: c.get("order", 0))
        return [{"id": c["id"], "name": c["name"], "color": c.get("color") or "#9aa0b5",
                 "bucket_count": sum(1 for cid in live if cid == c["id"])}
                for c in cats]

    def add_category(self, name, color=None):
        cats = [c for c in self.data["cats"] if not c.get("archived")]
        DB.insert(self.token, "bcc_categories", {
            "id": DB.new_id(), "user_id": self.uid, "name": (name or "Category").strip() or "Category",
            "color": color or MZ._CAT_COLORS[len(cats) % len(MZ._CAT_COLORS)],
            "sort_order": (max((c.get("order", 0) for c in cats), default=-1) + 1)})
        self._reload("cats_raw")

    def rename_category(self, cid, name):
        if (name or "").strip():
            DB.update(self.token, "bcc_categories", self.uid, "id", cid, {"name": name.strip()})
            self._reload("cats_raw")

    def move_category(self, cid, direction):
        cats = sorted((c for c in self.data["cats"] if not c.get("archived")),
                      key=lambda c: c.get("order", 0))
        i = next((k for k, c in enumerate(cats) if c["id"] == cid), None)
        if i is None:
            return
        j = i - 1 if direction == "up" else i + 1
        if not (0 <= j < len(cats)):
            return
        a, b = cats[i], cats[j]                                # swap their sort orders
        DB.update(self.token, "bcc_categories", self.uid, "id", a["id"], {"sort_order": b.get("order", 0)})
        DB.update(self.token, "bcc_categories", self.uid, "id", b["id"], {"sort_order": a.get("order", 0)})
        self._reload("cats_raw")

    def archive_category(self, cid):
        if any(b.get("catId") == cid for b in self._buckets()):
            raise ValueError("Move or remove its buckets first.")
        DB.update(self.token, "bcc_categories", self.uid, "id", cid, {"archived": True})
        self._reload("cats_raw")

    # ── ledger (read real transactions; writes land with the rest) ────────────
    def _bucket_meta(self) -> dict:
        cc = {c["id"]: (c.get("color") or "#9aa0b5") for c in self.data["cats"]}
        return {b["id"]: (b["name"], cc.get(b.get("catId", ""), "#9aa0b5"))
                for b in self.data["buckets"]}

    def transactions(self, limit: int = 300) -> list[dict]:
        meta = self._bucket_meta()
        live = {b["id"] for b in self._buckets()}     # active (non-archived) buckets
        acct = {a["id"]: a["name"] for a in self.data["accounts"]}
        out = []
        for i, t in enumerate(self.data["txs"]):
            if F.is_scheduled(t):                     # future-dated → belongs to the Forecast, not the Ledger
                continue
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
            # expense/refund whose bucket was archived/removed → needs re-homing
            orphaned = bool(bid) and bid not in live and kind in ("expense", "refund")
            out.append({"id": t["id"], "kind": kind, "amount": round(amt, 2),
                        "date": t.get("date") or "", "desc": t.get("desc") or "",
                        "bucket_id": bid, "bucket_name": name, "color": color, "orphaned": orphaned,
                        "from_acct": t.get("accountId"), "to_acct": t.get("toAccountId"), "_seq": i})
        out.sort(key=lambda r: (r["date"], r["_seq"]), reverse=True)
        return out[:limit]

    def scheduled(self) -> list[dict]:
        """Future-dated transactions — committed items the Forecast injects so every
        real outflow/inflow (a planned payment, a transfer, expected income) shows."""
        meta = self._bucket_meta()
        acct = {a["id"]: a["name"] for a in self.data["accounts"]}
        out = []
        for t in self.data["txs"]:
            if not F.is_scheduled(t):
                continue
            typ, bid, amt = t.get("type"), t.get("bucketId") or None, float(t.get("amount") or 0)
            if typ == "out" and amt < 0:
                kind, label, amt = "refund", (t.get("desc") or meta.get(bid, ("", ""))[0] or "Refund"), -amt
            elif typ == "out" and bid:
                kind, label = "expense", (t.get("desc") or meta.get(bid, ("", ""))[0])
            elif typ == "out":
                kind, label, bid = "transfer", (t.get("desc") or "Transfer"), None
            elif typ == "in":
                kind, label, bid = "income", (t.get("desc") or "Income"), None
            elif typ == "xfr":
                kind, bid = "transfer", None
                label = t.get("desc") or f'{acct.get(t.get("accountId"), "?")} → {acct.get(t.get("toAccountId"), "?")}'
            else:
                continue
            out.append({"kind": kind, "amount": round(amt, 2), "date": t.get("date") or "",
                        "bucket_id": bid, "name": label or kind.title()})
        return out

    def reassign_transactions(self, tids, bucket_id):
        """Re-home orphaned expenses/refunds onto a bucket, then fund it to cover the
        re-homed net so it reads as budgeted rather than overspent (the funding that
        backed these went away with their old bucket)."""
        net = 0.0
        for tid in tids:
            t = next((x for x in self.data["txs"] if x["id"] == tid), None)
            if t is not None:
                net += float(t.get("amount") or 0)        # 'out' amount: expense +, refund −
            DB.update(self.token, "bcc_transactions", self.uid, "id", tid, {"bucket_id": bucket_id})
        self._reload("txs_raw")
        if abs(net) > 0.005:
            self.fund(bucket_id, round(net, 2))

    def ledger_metrics(self) -> dict:
        txs = self.data["txs"]
        income = spent = 0.0
        for t in txs:
            if t.get("monthId") != self._mid:
                continue
            if t["type"] == "in":
                income += float(t.get("amount") or 0)
            elif t["type"] == "out" and t.get("bucketId"):   # real spending only — not transfers out
                spent += float(t.get("amount") or 0)          # negative amounts (refunds) net down
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
            rt = r.get("rule_type")
            kind = rt if rt in ("internal", "external", "roundup") else "internal"
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
        self._reload("allocs_raw", "months_raw")

    def defund(self, bid: str, amount: float):
        self.fund(bid, -amount)
        self._maybe_sweep_roundup()      # freeing up Unallocated may clear a queued pool

    def move(self, src: str, dst: str, amount: float):
        self.defund(src, amount)
        self.fund(dst, amount)

    def prefund(self, bid: str, amount: float):
        """Get ahead: put money into NEXT month's allocation for this bucket, so it
        actually carries forward instead of returning to Ready to Assign. RTS today
        drops by the amount (ready_to_spend subtracts future allocations)."""
        nxt = F.month_offset(F.current_month_id(), 1)
        DB.ensure_month(self.uid, self.token, nxt)
        nxt_month = next((m for m in self.data["months"] if m["id"] == nxt), {"id": nxt, "allocations": {}})
        new = max(0.0, round(F.b_alloc(nxt_month, bid) + amount, 2))
        DB.upsert_alloc(self.uid, self.token, nxt, bid, new)
        self._reload("allocs_raw", "months_raw")

    def prefunded(self, bid: str) -> float:
        """Sum of this bucket's allocations already sitting in months AFTER today's.
        bucket_available() only ever looks at the currently-VIEWED month, so money
        prefunded ahead via prefund()/"get ahead" is real and correctly subtracted
        from RTS, but is otherwise invisible until you browse forward to that month
        — including to the Forecast, which would otherwise show a bill as fully
        unfunded even though it's already been gotten-ahead-of."""
        today_mid = F.current_month_id()
        return round(sum(F.b_alloc(m, bid) for m in self.data["months"]
                         if F.month_sort_key(m["id"]) > F.month_sort_key(today_mid)), 2)

    def _is_vault(self, bid) -> bool:
        b = next((x for x in self.data["buckets"] if x["id"] == bid), None)
        return bool(b) and _TYPE.get(b.get("type", "expense")) == "vault"

    def release_vault(self, bid: str, amount: float):
        """Deliberately move money OUT of a vault, back to Ready to Assign — the
        only way a vault ever gives money up. Clamped to what it actually holds."""
        held = self.bucket(bid)["available"]
        amount = round(min(float(amount or 0), held), 2)
        if amount <= 0.005:
            return
        DB.ensure_month(self.uid, self.token, self._mid)
        DB.vault_release_to_pool(self.uid, self.token, self._mid, bid, amount,
                                 F.b_alloc(self._month, bid))
        self._reload("allocs_raw", "vaultwd_raw", "months_raw")

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
        self._reload("buckets_raw")

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
        self._reload("handled_raw", "months_raw")

    def delete(self, bid: str):
        # Archive (money it held stops being claimed → returns to Ready to Spend).
        self._bucket_update(bid, {"archived": True})

    def add_bucket(self, name: str, cat_id: str, type: str, target: float,
                   due_day=None, frequency=None, flex: bool = False,
                   target_date=None, notes: str = ""):
        # A bucket filed under a missing/archived category becomes invisible —
        # groups() only shows buckets whose category still exists. Never create
        # one silently orphaned; fall back to any live category.
        live_cats = {c["id"] for c in self.data["cats"] if not c.get("archived")}
        if cat_id not in live_cats:
            cat_id = next(iter(live_cats), None)
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
        self._reload("buckets_raw")
        return {"id": row["id"]}

    # ledger transactions
    def _insert_tx(self, typ: str, amount: float, bid, desc: str, when: str, income_type=None):
        row = {"id": DB.new_id(), "user_id": self.uid, "account_id": self._budget_account_id(),
               "month_id": self._mid_for(when), "type": typ, "amount": round(float(amount), 2),
               "date": (when or "")[:10], "description": desc or "", "bucket_id": bid or None}
        if income_type:
            row["income_type"] = income_type
        DB.insert(self.token, "bcc_transactions", row)
        self._reload("txs_raw")
        if not F.is_scheduled({"date": when}):
            if typ == "out" and amount > 0:      # a real, already-happened expense
                self._queue_roundup(amount)
            elif typ == "in":                    # fresh Unallocated may clear a queued pool
                self._maybe_sweep_roundup()

    # ── roundup savings (spare change queued, then swept into a bucket) ───────
    def roundup_status(self) -> dict:
        r = self.data["roundup"]
        month = F.current_month_id()
        swept = r["swept_this_month"] if r.get("swept_month") == month else 0.0
        return {"pending": round(r["pending"], 2), "threshold": round(r["threshold"], 2),
                "swept_this_month": round(swept, 2)}

    def set_roundup_threshold(self, amount):
        amount = round(max(0.01, float(amount or 0)), 2)
        DB.upsert_roundup_pool(self.uid, self.token, {"threshold": amount})
        self._reload("roundup_raw")

    def _queue_roundup(self, amount: float):
        cents = MZ.roundup_cents(amount)
        if cents <= 0:
            return
        pending = round(self.data["roundup"]["pending"] + cents, 2)
        DB.upsert_roundup_pool(self.uid, self.token, {"pending": pending})
        self._reload("roundup_raw")
        self._maybe_sweep_roundup()

    def _maybe_sweep_roundup(self) -> float:
        """Once the queued pool crosses its threshold AND Unallocated can cover
        it, sweep the whole pool in one move, split evenly (to the penny) across
        every active roundup rule. Never partial — either it all lands, or it
        keeps waiting. Mirrors money.py's demo-engine logic exactly."""
        pool = self.data["roundup"]
        pending = round(pool["pending"], 2)
        if pending < pool["threshold"] - 0.005:
            return 0.0
        targets = [r for r in self.rules() if r["kind"] == "roundup" and r["active"] and r.get("bucket_id")]
        if not targets or pending > round(self.metrics()["unallocated"], 2) + 0.005:
            return 0.0
        n = len(targets)
        total_cents = int(round(pending * 100))
        base = total_cents // n
        shares = [base] * n
        for i in range(total_cents - base * n):
            shares[i] += 1
        for r, cents in zip(targets, shares):
            if cents > 0:
                self.fund(r["bucket_id"], cents / 100.0)
        month = F.current_month_id()
        swept_this_month = pool["swept_this_month"] if pool.get("swept_month") == month else 0.0
        DB.upsert_roundup_pool(self.uid, self.token, {
            "pending": 0.0, "swept_month": month, "swept_this_month": round(swept_this_month + pending, 2)})
        self._reload("roundup_raw")
        return pending

    def _view_date(self) -> str:
        """A date inside the month you're browsing — today when that's the current
        month, otherwise the last day of the viewed month, so a spend logged while
        catching up on a past month lands where you expect."""
        from datetime import date as _d
        import calendar
        if not self._view_mid or self._view_mid == F.current_month_id():
            return _d.today().isoformat()
        y, m0 = F.parse_month_id(self._view_mid)          # m0 is 0-indexed
        return _d(y, m0 + 1, calendar.monthrange(y, m0 + 1)[1]).isoformat()

    def record_spend(self, bid: str, amount: float, desc: str = ""):
        if self._is_vault(bid):
            raise ValueError("A vault is locked — no transaction can touch it. Release money to Ready to Assign instead.")
        self._insert_tx("out", amount, bid, desc, self._view_date())

    def add_transaction(self, kind: str, amount: float, bucket_id, desc: str, date: str):
        if kind in ("expense", "refund") and self._is_vault(bucket_id):
            raise ValueError("A vault is locked — no transaction can touch it. Release money to Ready to Assign instead.")
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
            self._reload("txs_raw")

    def delete_transaction(self, tid: str):
        DB.delete(self.token, "bcc_transactions", self.uid, "id", tid)
        self._reload("txs_raw")

    def accounts(self) -> list[dict]:
        return [{"id": a["id"], "name": a["name"], "type": a.get("type", "budget"),
                 "opening": round(float(a.get("openingBalance") or 0), 2),
                 "balance": round(F.acct_balance(a, self.data["txs"]), 2),
                 "is_budget": a.get("type") == "budget"}
                for a in self.data["accounts"] if not a.get("archived")]

    # ── cash-flow accounts (no debt accounts — visibility + light management) ──
    def add_account(self, name, type="cash", opening=0.0):
        DB.insert(self.token, "bcc_accounts", {
            "id": DB.new_id(), "user_id": self.uid, "name": (name or "Account").strip(),
            "type": type if type in ("savings", "cash") else "cash",   # never a 2nd budget acct
            "opening_balance": round(float(opening or 0), 2),
            "sort_order": len(self.data["accounts"])})
        self._reload("accounts_raw")

    def edit_account(self, aid, name=None, type=None, opening=None):
        acct = next((a for a in self.data["accounts"] if a["id"] == aid), None)
        fields = {}
        if name is not None:
            fields["name"] = (name or "").strip() or "Account"
        # the single budget account keeps its type — it drives Ready to Assign
        if type is not None and not (acct and acct.get("type") == "budget"):
            fields["type"] = type if type in ("savings", "cash") else "cash"
        if opening is not None:
            fields["opening_balance"] = round(float(opening or 0), 2)
        if fields:
            DB.update(self.token, "bcc_accounts", self.uid, "id", aid, fields)
            self._reload("accounts_raw")

    def archive_account(self, aid):
        acct = next((a for a in self.data["accounts"] if a["id"] == aid), None)
        if acct and acct.get("type") == "budget":
            raise ValueError("The budget account can't be removed — it drives Ready to Assign.")
        DB.update(self.token, "bcc_accounts", self.uid, "id", aid, {"archived": True})
        self._reload("accounts_raw")

    def add_transfer(self, from_id: str, to_id: str, amount: float, desc: str = "", date: str = ""):
        from datetime import date as _d
        when = (date or _d.today().isoformat())[:10]
        DB.insert(self.token, "bcc_transactions", {
            "id": DB.new_id(), "user_id": self.uid, "account_id": from_id,
            "to_account_id": to_id, "month_id": self._mid_for(when), "type": "xfr",
            "amount": round(float(amount), 2), "date": when,
            "description": desc or "", "bucket_id": None})
        self._reload("txs_raw")

    # settings: paychecks
    def add_paycheck(self, label, amount, freq, anchor):
        DB.insert(self.token, "bcc_paychecks", {
            "id": DB.new_id(), "user_id": self.uid, "label": (label or "Paycheck").strip(),
            "amount": round(float(amount or 0), 2), "freq": self._FREQ_TO_INT.get(freq, 14),
            "anchor_date": (anchor or "")[:10] or None})
        self._reload("paychecks_raw")

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
            self._reload("paychecks_raw")

    def advance_paycheck(self, pid: str):
        """Already got this one — roll its anchor to the next occurrence so the
        Forecast stops projecting a payday that's already real, logged income."""
        from datetime import date as _d
        p = next((x for x in self.paychecks() if x["id"] == pid), None)
        if not p:
            return
        nxt = FC.next_payday(p["anchor"], p["freq"], _d.today())
        if nxt:
            self.edit_paycheck(pid, anchor=nxt)

    def delete_paycheck(self, pid):
        DB.delete(self.token, "bcc_paychecks", self.uid, "id", pid)
        self._reload("paychecks_raw")

    # settings: allocation rules
    def add_rule(self, name, kind, bucket_id, value, value_type, active=True):
        DB.insert(self.token, "bcc_allocation_rules", {
            "id": DB.new_id(), "user_id": self.uid, "name": (name or "Rule").strip(),
            "rule_type": kind if kind in ("internal", "external", "roundup") else "internal",
            "bucket_id": bucket_id or None, "value": round(float(value or 0), 2),
            "value_type": value_type if value_type in ("fixed", "pct", "fund") else "fixed",
            "active": bool(active)})
        self._reload("rules_raw")

    def edit_rule(self, rid, name=None, kind=None, bucket_id=..., value=None, value_type=None, active=None):
        fields = {}
        if name is not None:
            fields["name"] = name.strip() or "Rule"
        if kind is not None:
            fields["rule_type"] = kind if kind in ("internal", "external", "roundup") else "internal"
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
            self._reload("rules_raw")

    def delete_rule(self, rid):
        DB.delete(self.token, "bcc_allocation_rules", self.uid, "id", rid)
        self._reload("rules_raw")

    def toggle_rule(self, rid):
        cur = next((r for r in self.rules() if r["id"] == rid), None)
        DB.update(self.token, "bcc_allocation_rules", self.uid, "id", rid,
                  {"active": not (cur["active"] if cur else True)})
        self._reload("rules_raw")

    # split buckets (bill schedule) — bcc_buckets.split + bcc_bucket_items
    def set_split(self, bid: str, on: bool):
        self._bucket_update(bid, {"split": bool(on)})

    def convert_to_split(self, bid: str):
        """Plain bucket → bill split. Seed the first bill from the bucket's current
        target + due (captured before the flag flips, since a split bucket derives
        its target from the items). Reuse any dormant bills instead of duplicating."""
        b = self.bucket(bid)                          # split off → target = its own budget
        target, due, name = b["target"], b["due_day"], b["name"]
        self.set_split(bid, True)
        raw = next((x for x in self._buckets() if x["id"] == bid), None)
        if raw is not None and not raw.get("items"):
            self.add_item(bid, name, target, due)

    def convert_to_bucket(self, bid: str, due_day=None):
        """Bill split → one bucket: the bills' total becomes the single target and
        one due date is chosen. Bills are kept (dormant) for an easy re-split."""
        b = self.bucket(bid)
        total = b["items_total"] if b.get("split") else b["target"]
        self.set_target(bid, round(total, 2))         # preserve the money target
        if due_day is not None:
            self.set_due_day(bid, due_day)
        self.set_split(bid, False)

    def explode_to_buckets(self, bid: str):
        """Turn each bill into its own standalone bucket in the same category, then
        archive the split. The funded pool waterfalls into the new buckets
        soonest-first; the remainder returns to Ready to Assign when the archived
        bucket stops claiming it — money is conserved."""
        b = self.bucket(bid)
        cat = b["cat_id"]
        for it in b["items"]:                          # split rows are soonest-due first
            amt = round(it["amount"], 2)
            nid = self.add_bucket(it["name"], cat, "spend", amt, due_day=it.get("due_day"))["id"]
            give = round(min(amt, max(0.0, self.bucket(bid)["available"])), 2)
            if give > 0.005:
                self.move(bid, nid, give)
        self.delete(bid)
        # zero the now-archived bucket's leftover allocation so it can't ghost the
        # books (it's excluded from RTS either way, but no dead allocation should linger)
        DB.upsert_alloc(self.uid, self.token, self._mid, bid, 0.0)
        self._reload("allocs_raw")

    # ── reconciliation: expose where every allocated dollar lives ──────────────
    def reconcile(self) -> dict:
        m = self.metrics()
        active = self._buckets()
        active_ids = {b["id"] for b in active}
        names = {b["id"]: b["name"] for b in self.data["buckets"]}
        cur_alloc = (self._month.get("allocations") or {})     # {bucket_id: amount} this month
        ghosts = [{"id": bid, "name": names.get(bid, "removed bucket"), "amount": round(amt, 2)}
                  for bid, amt in cur_alloc.items() if bid not in active_ids and abs(amt) > 0.005]
        total_alloc = round(sum(a for b, a in cur_alloc.items() if b in active_ids), 2)
        resid = round(m["cash"] - (m["unallocated"] + m["in_buckets"]), 2)
        return {"cash": m["cash"], "rts": m["unallocated"], "in_buckets": m["in_buckets"],
                "total_alloc": total_alloc, "residual": resid,
                "ghosts": ghosts, "ghost_total": round(sum(g["amount"] for g in ghosts), 2)}

    def clear_ghost_allocations(self) -> float:
        """Zero out allocations still sitting on archived buckets this month."""
        rec = self.reconcile()
        for g in rec["ghosts"]:
            DB.upsert_alloc(self.uid, self.token, self._mid, g["id"], 0.0)
        if rec["ghosts"]:
            self._reload("allocs_raw")
        return rec["ghost_total"]

    def add_item(self, bid: str, name: str, amount: float, due_day=None):
        DB.insert(self.token, "bcc_bucket_items", {
            "id": DB.new_id(), "user_id": self.uid, "bucket_id": bid,
            "name": (name or "Item").strip(), "amount": round(float(amount or 0), 2),
            "due_day": MZ._norm_due_day(due_day), "paid": False,
            "sort_order": sum(len(b.get("items", [])) for b in self._buckets())})
        self._reload("items_raw")

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
            self._reload("items_raw")

    def remove_item(self, bid: str, iid: str):
        DB.delete(self.token, "bcc_bucket_items", self.uid, "id", iid)
        self._reload("items_raw")

    def toggle_item_paid(self, bid: str, iid: str):
        it = next((x for b in self._buckets() for x in b.get("items", []) if x["id"] == iid), None)
        DB.update(self.token, "bcc_bucket_items", self.uid, "id", iid,
                  {"paid": not (it["paid"] if it else False)})
        self._reload("items_raw")
