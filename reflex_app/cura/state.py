"""
AppState — single source of truth for the entire Cura app.

Compare to Flask: no Jinja2 context_dict, no JS refreshKpis(), no _live_state() JSON.
State vars update → React rerenders automatically via WebSocket.
"""

import reflex as rx
from typing import Any
from datetime import date, timedelta
from itertools import groupby

from .formulas import (
    current_month_id, parse_month_id, month_id as _month_id,
    b_alloc, b_budget, b_spent, rollover_bal, bucket_available,
    ready_to_spend, vault_accumulated, is_scheduled,
    acct_balance, total_allocated, month_status as _month_status,
    month_sort_key,
)
from . import db as DB

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ── Money formatter ───────────────────────────────────────────────────────────

def _fmt(v: float) -> str:
    if v < 0:
        return f"-${abs(v):,.2f}"
    return f"${v:,.2f}"


# ── Bucket status ─────────────────────────────────────────────────────────────

def _bucket_status(alloc: float, budget: float, spent: float, avail: float) -> str:
    if avail < 0: return "OVER"
    if alloc > 0 and spent >= alloc: return "PAID"
    if budget > 0 and alloc > budget * 1.05: return "OVERFUNDED"
    if budget > 0 and alloc >= budget: return "FUNDED"
    if alloc > 0: return "FUNDING"
    return ""

def _pill(status: str) -> str:
    return {
        "PAID": "paid", "OVER": "over", "OVERFUNDED": "overfunded",
        "FUNDED": "funded", "FUNDING": "funding",
    }.get(status, "empty")

def _avail_color(pill: str) -> str:
    return {
        "paid": "#34d399", "funded": "#34d399",
        "overfunded": "#a78bfa", "funding": "#fbbf24",
        "over": "#f87171",
    }.get(pill, "#4e4e6a")

def _bar_color(pill: str) -> str:
    return {
        "paid": "#34d399", "funded": "#34d399",
        "overfunded": "#a78bfa", "over": "#f87171",
    }.get(pill, "#818cf8")


# ── Date label ────────────────────────────────────────────────────────────────

def _date_label(date_str: str) -> str:
    try:
        d = date.fromisoformat(date_str)
        today = date.today()
        if d == today: return "Today"
        if d == today - timedelta(days=1): return "Yesterday"
        return d.strftime("%A, %B %-d")
    except ValueError:
        return date_str or "—"


# ── Date → month ID ───────────────────────────────────────────────────────────

def _date_to_mid(date_str: str) -> str:
    d = date.fromisoformat(date_str)
    return _month_id(d.year, d.month - 1)


# ─────────────────────────────────────────────────────────────────────────────
#  AppState
# ─────────────────────────────────────────────────────────────────────────────

class AppState(rx.State):

    # ── Auth ─────────────────────────────────────────────────────────────────
    access_token: str = ""
    user_id:      str = ""
    user_email:   str = ""
    auth_error:   str = ""

    # ── Month navigation ──────────────────────────────────────────────────────
    active_mid:       str = ""
    month_display:    str = ""
    month_status_str: str = "present"   # "past" | "present" | "future" | "closed"
    prev_mid:         str = ""
    next_mid:         str = ""

    # ── Processed display data ────────────────────────────────────────────────
    # Flat list: {"row_type": "header"|"bucket", ...}
    bucket_rows: list[dict[str, Any]] = []
    # Flat list: {"row_type": "date_header"|"tx", ...}
    ledger_rows: list[dict[str, Any]] = []

    # ── KPIs ─────────────────────────────────────────────────────────────────
    rts:          float = 0.0
    income_total: float = 0.0
    spent_total:  float = 0.0
    total_alloc_val: float = 0.0

    # ── Accounts ─────────────────────────────────────────────────────────────
    accounts_rows: list[dict[str, Any]] = []   # for accounts panel
    total_cash:    float = 0.0
    total_debt:    float = 0.0

    # ── Form selects ──────────────────────────────────────────────────────────
    expense_buckets: list[dict[str, Any]] = []   # [{id, name}]
    account_options: list[dict[str, Any]] = []   # [{id, name}]

    # ── UI state ─────────────────────────────────────────────────────────────
    active_panel:  str  = "buckets"
    is_loading:    bool = False
    panel_error:   str  = ""

    # ── Add-transaction sheet ─────────────────────────────────────────────────
    sheet_open:     bool = False
    sheet_type:     str  = "out"      # "out" | "in" | "xfr"
    sheet_amount:   str  = ""
    sheet_desc:     str  = ""
    sheet_date:     str  = ""
    sheet_account:  str  = ""
    sheet_bucket:   str  = ""
    sheet_error:    str  = ""
    sheet_saving:   bool = False

    # ── Ledger search ─────────────────────────────────────────────────────────
    ledger_query: str = ""

    # ── Forecast ──────────────────────────────────────────────────────────────
    forecast_range:       int        = 3
    forecast_account:     str        = ""
    forecast_periods:     list[dict[str, Any]] = []
    forecast_accounts:    list[dict[str, Any]] = []
    forecast_loading:     bool       = False
    fc_expanded:          list[str]  = []
    # Flat summary KPIs (avoids dict var access issues)
    fc_start_bal:         str        = "—"
    fc_total_income:      str        = "—"
    fc_total_unfunded:    str        = "—"
    fc_safe_to_spend:     str        = "—"
    fc_sts_color:         str        = "#818cf8"
    fc_shortfall_count:   int        = 0

    # ── Internal raw data (not sent to client — prefixed with _) ─────────────
    # Note: in Reflex 0.9 all state vars go to client; use _ prefix by convention
    _raw: dict = {}   # full data dict from DB.load_all()

    # ─────────────────────────────────────────────────────────────────────────
    #  Computed vars
    # ─────────────────────────────────────────────────────────────────────────

    @rx.var
    def is_logged_in(self) -> bool:
        return bool(self.access_token and self.user_id)

    @rx.var
    def rts_fmt(self) -> str:
        return _fmt(self.rts)

    @rx.var
    def income_fmt(self) -> str:
        return _fmt(self.income_total)

    @rx.var
    def spent_fmt(self) -> str:
        return _fmt(self.spent_total)

    @rx.var
    def alloc_fmt(self) -> str:
        return _fmt(self.total_alloc_val)

    @rx.var
    def alloc_pct(self) -> int:
        if self.income_total <= 0:
            return 0
        return min(100, max(0, round(self.total_alloc_val / self.income_total * 100)))

    @rx.var
    def rts_negative(self) -> bool:
        return self.rts < -0.005

    @rx.var
    def rts_zero(self) -> bool:
        return -0.005 <= self.rts < 0.01

    @rx.var
    def rts_sub(self) -> str:
        if self.rts < -0.005:
            return "Over-allocated — cut spending or move funds"
        if self.rts < 0.01:
            return "Every dollar has a job"
        return f"{_fmt(self.rts)} waiting to be assigned"

    @rx.var
    def rts_color(self) -> str:
        if self.rts < -0.005: return "#f87171"
        if self.rts < 0.01:   return "#34d399"
        return "#818cf8"

    @rx.var
    def distribute_visible(self) -> bool:
        return self.rts > 0.005 and self.month_status_str not in ("closed",)

    @rx.var
    def month_is_closed(self) -> bool:
        return self.month_status_str == "closed"

    @rx.var
    def filtered_ledger(self) -> list[dict[str, Any]]:
        if not self.ledger_query:
            return self.ledger_rows
        q = self.ledger_query.lower()
        out = []
        for row in self.ledger_rows:
            if row["row_type"] == "date_header":
                out.append(row)
            elif q in row.get("desc", "").lower() or q in row.get("bucket", "").lower():
                out.append(row)
        # Remove orphan date headers
        cleaned = []
        for i, row in enumerate(out):
            if row["row_type"] == "date_header":
                has_tx = any(r["row_type"] == "tx" for r in out[i+1:i+20]
                             if r["row_type"] != "date_header")
                if has_tx:
                    cleaned.append(row)
            else:
                cleaned.append(row)
        return cleaned

    @rx.var
    def forecast_shortfall_label(self) -> str:
        n = self.fc_shortfall_count
        return f"⚠ {n} period{'s' if n != 1 else ''} with negative balance"

    # ─────────────────────────────────────────────────────────────────────────
    #  Forecast events
    # ─────────────────────────────────────────────────────────────────────────

    def _run_forecast(self):
        from .forecast_calc import compute_forecast
        if not self._raw:
            return
        result = compute_forecast(self._raw, self.forecast_range, self.forecast_account)
        self.fc_start_bal       = result["start_balance"]
        self.fc_total_income    = result["total_income"]
        self.fc_total_unfunded  = result["total_unfunded"]
        self.fc_safe_to_spend   = result["safe_to_spend"]
        self.fc_sts_color       = result["sts_color"]
        self.fc_shortfall_count = result["shortfall_count"]
        self.forecast_periods   = result["periods"]
        expanded = [p["id"] for p in result["periods"] if p["shortfall"]]
        if result["periods"] and result["periods"][0]["id"] not in expanded:
            expanded.insert(0, result["periods"][0]["id"])
        self.fc_expanded = expanded

    def set_forecast_range(self, n: int):
        self.forecast_range = n
        self._run_forecast()

    def set_forecast_account(self, aid: str):
        self.forecast_account = aid
        self._run_forecast()

    def toggle_fc_period(self, pid: str):
        if pid in self.fc_expanded:
            self.fc_expanded = [x for x in self.fc_expanded if x != pid]
        else:
            self.fc_expanded = self.fc_expanded + [pid]

    def _refresh_forecast_accounts(self):
        """Rebuild the account chip list from raw data."""
        raw = self._raw
        if not raw:
            return
        accounts = raw.get("accounts", [])
        txs      = raw.get("txs", [])

        def _bal(a):
            bal = float(a.get("openingBalance") or 0)
            for t in txs:
                if t.get("accountId") == a["id"]:
                    bal += float(t.get("amount") or 0) if t.get("type") == "in" else -float(t.get("amount") or 0)
                if t.get("toAccountId") == a["id"] and t.get("type") == "xfr":
                    bal += float(t.get("amount") or 0)
            return bal

        self.forecast_accounts = [
            {"id": a["id"], "name": a["name"],
             "color": a.get("color", "#818cf8"),
             "balance_fmt": _fmt(_bal(a))}
            for a in accounts
            if a.get("type") == "budget" and not a.get("archived")
        ]

    # ─────────────────────────────────────────────────────────────────────────
    #  Auth events
    # ─────────────────────────────────────────────────────────────────────────

    async def login(self, form_data: dict):
        email    = (form_data.get("email") or "").strip()
        password = (form_data.get("password") or "").strip()
        self.auth_error = ""
        self.is_loading = True
        yield
        try:
            auth = DB.sign_in(email, password)
            self.access_token = auth["access_token"]
            self.user_id      = auth["user_id"]
            self.user_email   = auth["user_email"]
            self.is_loading   = False
            yield rx.redirect("/dashboard")
        except Exception:
            self.auth_error = "Invalid email or password."
            self.is_loading = False

    def logout(self):
        self.access_token = ""
        self.user_id      = ""
        self.user_email   = ""
        self._raw         = {}
        return rx.redirect("/login")

    # ─────────────────────────────────────────────────────────────────────────
    #  Dashboard load
    # ─────────────────────────────────────────────────────────────────────────

    async def on_dashboard_load(self):
        if not self.is_logged_in:
            yield rx.redirect("/login")
            return
        self.is_loading = True
        yield
        try:
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            if not self.active_mid:
                self.active_mid = current_month_id()
            self._process(data, self.active_mid)
        except Exception as e:
            if DB.is_auth_error(e):
                self.access_token = ""
                yield rx.redirect("/login")
                return
            self.panel_error = str(e)
        finally:
            self.is_loading = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Month navigation
    # ─────────────────────────────────────────────────────────────────────────

    def go_prev_month(self):
        if self.prev_mid:
            self._switch_month(self.prev_mid)

    def go_next_month(self):
        if self.next_mid:
            self._switch_month(self.next_mid)

    def _switch_month(self, mid: str):
        self.active_mid = mid
        if self._raw:
            self._process(self._raw, mid)

    # ─────────────────────────────────────────────────────────────────────────
    #  Panel navigation
    # ─────────────────────────────────────────────────────────────────────────

    def set_panel(self, name: str):
        self.active_panel = name

    # ─────────────────────────────────────────────────────────────────────────
    #  Add-transaction sheet
    # ─────────────────────────────────────────────────────────────────────────

    def open_sheet(self):
        self.sheet_open   = True
        self.sheet_type   = "out"
        self.sheet_amount = ""
        self.sheet_desc   = ""
        self.sheet_date   = date.today().isoformat()
        self.sheet_account = self.account_options[0]["id"] if self.account_options else ""
        self.sheet_bucket  = self.expense_buckets[0]["id"] if self.expense_buckets else ""
        self.sheet_error  = ""

    def close_sheet(self):
        self.sheet_open  = False
        self.sheet_error = ""

    def set_sheet_type(self, t: str):
        self.sheet_type = t

    def set_sheet_amount(self, v: str):
        self.sheet_amount = v

    def set_sheet_desc(self, v: str):
        self.sheet_desc = v

    def set_sheet_date(self, v: str):
        self.sheet_date = v

    def set_sheet_account(self, v: str):
        self.sheet_account = v

    def set_sheet_bucket(self, v: str):
        self.sheet_bucket = v

    async def submit_transaction(self):
        amount_str = self.sheet_amount.replace("$", "").replace(",", "").strip()
        try:
            amount = float(amount_str)
        except ValueError:
            self.sheet_error = "Enter a valid amount."
            return
        if amount <= 0:
            self.sheet_error = "Amount must be positive."
            return
        if not self.sheet_date:
            self.sheet_error = "Date is required."
            return
        if not self.sheet_account:
            self.sheet_error = "Account is required."
            return

        self.sheet_saving = True
        yield
        try:
            mid = _date_to_mid(self.sheet_date)
            DB.ensure_month(self.user_id, self.access_token, mid)
            tx = {
                "accountId": self.sheet_account,
                "monthId": mid,
                "type": self.sheet_type,
                "amount": amount,
                "date": self.sheet_date,
                "desc": self.sheet_desc,
                "bucketId": self.sheet_bucket if self.sheet_type == "out" else "",
                "incomeType": "paycheck" if self.sheet_type == "in" else None,
            }
            tx_id = DB.insert_transaction(self.user_id, self.access_token, tx)
            # Reload data
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
            self.sheet_open   = False
            self.sheet_error  = ""
        except Exception as e:
            self.sheet_error = f"Failed: {e}"
        finally:
            self.sheet_saving = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Delete transaction
    # ─────────────────────────────────────────────────────────────────────────

    async def delete_tx(self, tx_id: str):
        try:
            DB.delete_transaction(self.user_id, self.access_token, tx_id)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
        except Exception as e:
            self.panel_error = str(e)

    # ─────────────────────────────────────────────────────────────────────────
    #  Fill bucket
    # ─────────────────────────────────────────────────────────────────────────

    async def fill_bucket(self, bucket_id: str, budget: float):
        try:
            DB.ensure_month(self.user_id, self.access_token, self.active_mid)
            DB.upsert_alloc(self.user_id, self.access_token, self.active_mid, bucket_id, budget)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
        except Exception as e:
            self.panel_error = str(e)

    # ─────────────────────────────────────────────────────────────────────────
    #  Ledger search
    # ─────────────────────────────────────────────────────────────────────────

    def set_ledger_query(self, q: str):
        self.ledger_query = q

    # ─────────────────────────────────────────────────────────────────────────
    #  Core data processor  (replaces _dashboard_inner in Flask)
    # ─────────────────────────────────────────────────────────────────────────

    def _process(self, data: dict, mid: str):
        accounts    = data.get("accounts") or []
        all_buckets = data.get("buckets") or []
        cats        = data.get("cats") or []
        all_months  = data.get("months") or []
        txs         = data.get("txs") or []

        active_month = next(
            (m for m in all_months if m.get("id") == mid),
            {"id": mid, "allocations": {}, "budgets": {},
             "rolloverReleased": {}, "skippedBuckets": {}, "vaultWithdrawals": {}},
        )
        active_buckets = [b for b in all_buckets if not b.get("archived")]
        cats_sorted    = sorted(cats, key=lambda c: c.get("order", 0))

        # ── Month display ──────────────────────────────────────────────────
        year, m0 = parse_month_id(mid)
        self.active_mid    = mid
        self.month_display = f"{MONTH_NAMES[m0]} {year}"

        # Month status
        ms = active_month.get("closed") and "closed" or _month_status(mid)
        self.month_status_str = ms

        # Prev / next months for navigation
        sorted_mids = sorted(
            set(m["id"] for m in all_months) | {current_month_id()},
            key=month_sort_key,
        )
        if mid in sorted_mids:
            idx = sorted_mids.index(mid)
            self.prev_mid = sorted_mids[idx - 1] if idx > 0 else ""
            self.next_mid = sorted_mids[idx + 1] if idx < len(sorted_mids) - 1 else ""
        else:
            self.prev_mid = ""
            self.next_mid = ""

        # ── KPIs ──────────────────────────────────────────────────────────
        cur_mid_obj = next(
            (m for m in all_months if m.get("id") == current_month_id()),
            {"id": current_month_id(), "allocations": {}, "budgets": {},
             "rolloverReleased": {}, "skippedBuckets": {}, "vaultWithdrawals": {}},
        )
        self.rts = ready_to_spend(cur_mid_obj, all_months, accounts, active_buckets, txs)
        self.total_alloc_val = total_allocated(active_month, active_buckets)

        inc_total = 0.0
        sp_total  = 0.0
        budget_ids = {a["id"] for a in accounts if a["type"] == "budget"}
        for t in txs:
            if t.get("monthId") != mid or is_scheduled(t):
                continue
            amt = float(t.get("amount") or 0)
            if t.get("type") == "in" and t.get("accountId") in budget_ids:
                inc_total += amt
            elif t.get("type") == "out":
                sp_total += amt
        self.income_total = inc_total
        self.spent_total  = sp_total

        # ── Bucket rows (flat list with category headers) ──────────────────
        max_budget = max((b.get("defaultBudget") or 0 for b in active_buckets), default=1) or 1
        rows: list[dict] = []

        for cat in cats_sorted:
            cid = cat["id"]
            cat_buckets = sorted(
                [b for b in active_buckets if b.get("catId") == cid],
                key=lambda b: b.get("order", 0),
            )
            if not cat_buckets:
                continue

            rows.append({"row_type": "header", "name": cat.get("name", ""), "id": cid})

            for b in cat_buckets:
                bid    = b["id"]
                btype  = b.get("type", "expense")
                alloc  = b_alloc(active_month, bid)
                budget = b_budget(active_month, bid)

                if btype == "vault":
                    spent = vault_total = vault_accumulated(bid, all_months)
                    avail = vault_total
                else:
                    vault_total = 0.0
                    spent = b_spent(mid, bid, txs)
                    avail = bucket_available(b, active_month, all_months, txs)

                status = _bucket_status(alloc, budget, spent, avail)
                pill   = _pill(status)
                pct    = min(100, round(spent / budget * 100)) if budget > 0 else 0
                prog_h = max(2, min(7, round((budget or 0) / max_budget * 7)))

                rows.append({
                    "row_type":    "bucket",
                    "id":          bid,
                    "name":        b.get("name", ""),
                    "type":        btype,
                    "alloc":       alloc,
                    "budget":      budget,
                    "spent":       spent,
                    "avail":       avail,
                    "status":      status,
                    "pill":        pill,
                    "avail_fmt":   _fmt(avail),
                    "alloc_fmt":   _fmt(alloc),
                    "budget_fmt":  _fmt(budget),
                    "spent_fmt":   _fmt(spent),
                    "pct_str":     f"{pct}%",
                    "avail_color": _avail_color(pill),
                    "avail_bg":    _avail_color(pill) + "1f",
                    "avail_border": "1px solid " + _avail_color(pill) + "33",
                    "bar_color":   _bar_color(pill),
                    "prog_h":      f"{prog_h}px",
                    "show_fill":   bool(budget > 0 and alloc < budget and btype != "vault"),
                })

        self.bucket_rows = rows

        # ── Ledger rows (flat list with date headers) ──────────────────────
        acct_map   = {a["id"]: a.get("name", "") for a in accounts}
        bucket_map = {b["id"]: b.get("name", "") for b in all_buckets}

        ledger_txs = sorted(
            [t for t in txs if t.get("monthId") == mid],
            key=lambda t: (t.get("date") or "", t.get("id") or ""),
            reverse=True,
        )

        ledger_flat: list[dict] = []
        for date_str, group in groupby(ledger_txs, key=lambda t: t.get("date", "")):
            ledger_flat.append({
                "row_type": "date_header",
                "label": _date_label(date_str),
                "date": date_str,
            })
            for t in group:
                ttype = t.get("type", "out")
                amt   = float(t.get("amount") or 0)
                sched = is_scheduled(t)
                amt_color = (
                    "#34d399" if ttype == "in" else
                    "#fbbf24" if sched else
                    "#f87171" if ttype == "out" else
                    "#8282a2"
                )
                amt_prefix = "+" if ttype == "in" else "−"
                ledger_flat.append({
                    "row_type":    "tx",
                    "id":          t["id"],
                    "date":        t.get("date", ""),
                    "desc":        t.get("desc", "") or "(no description)",
                    "type":        ttype,
                    "amount":      amt,
                    "amount_fmt":  f"{amt_prefix}{_fmt(amt)}",
                    "amt_color":   amt_color,
                    "account":     acct_map.get(t.get("accountId", ""), ""),
                    "bucket":      bucket_map.get(t.get("bucketId", ""), ""),
                    "scheduled":   sched,
                    "reconciled":  bool(t.get("reconciled")),
                    "dot_color":   (
                        "#34d399" if ttype == "in" else
                        "#818cf8" if ttype == "out" else
                        "#8282a2"
                    ),
                })

        self.ledger_rows = ledger_flat

        # ── Accounts rows ──────────────────────────────────────────────────
        acc_rows = []
        for a in accounts:
            if a.get("archived"):
                continue
            bal = acct_balance(a, txs)
            atype = a.get("type", "budget")
            acc_rows.append({
                "id": a["id"], "name": a.get("name", ""),
                "type": atype,
                "type_upper": atype.upper(),
                "balance": bal,
                "balance_fmt": _fmt(bal),
                "color": a.get("color", "#818cf8"),
                "bal_color": "#34d399" if atype != "debt" else "#f87171",
            })

        self.accounts_rows = acc_rows
        self.total_cash = sum(r["balance"] for r in acc_rows if r["type"] != "debt")
        self.total_debt = sum(r["balance"] for r in acc_rows if r["type"] == "debt")

        # ── Form selects ───────────────────────────────────────────────────
        self.expense_buckets = [
            {"id": b["id"], "name": b.get("name", "")}
            for b in active_buckets if b.get("type") != "vault"
        ]
        self.account_options = [
            {"id": a["id"], "name": a.get("name", "")}
            for a in accounts if not a.get("archived")
        ]

        # ── Forecast ───────────────────────────────────────────────────────
        self._refresh_forecast_accounts()
        self._run_forecast()
