"""
AppState — single source of truth for the entire Cura app.

Compare to Flask: no Jinja2 context_dict, no JS refreshKpis(), no _live_state() JSON.
State vars update → React rerenders automatically via WebSocket.
"""

import asyncio
import reflex as rx
from typing import Any
from datetime import date, timedelta
import calendar

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


# ── ZBB helpers ───────────────────────────────────────────────────────────────

def _due_info(due_day: str, mid: str) -> tuple[str, str]:
    """Return (label, urgency) for a bucket's due day within month mid."""
    if not due_day:
        return "", ""
    try:
        year, m0 = parse_month_id(mid)
        month = m0 + 1
        today = date.today()
        raw = str(due_day).strip().lower()
        if raw in ("eom", "end", "last"):
            day = calendar.monthrange(year, month)[1]
        else:
            day = min(int(raw), calendar.monthrange(year, month)[1])
        due_date = date(year, month, day)
        days_away = (due_date - today).days
        if days_away < 0:
            return f"Due {abs(days_away)}d ago", "overdue"
        if days_away == 0:
            return "Due today", "urgent"
        if days_away <= 7:
            return f"Due in {days_away}d", "soon"
        return f"Due {due_date.strftime('%-d %b')}", ""
    except (ValueError, TypeError):
        return str(due_day), ""


def _months_left(target_date_str: str) -> int:
    """Return months remaining until target YYYY-MM string."""
    if not target_date_str:
        return 0
    try:
        parts = target_date_str.split("-")
        ty, tm = int(parts[0]), int(parts[1])
        today = date.today()
        return max(0, (ty - today.year) * 12 + (tm - today.month))
    except (ValueError, IndexError):
        return 0


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
#  Forecast helpers — flatten period dicts into a single display-row list
# ─────────────────────────────────────────────────────────────────────────────

def _flatten_periods(periods: list[dict]) -> list[dict]:
    """Convert compute_forecast() period list → flat list[dict[str,str]] rows.

    Row types (rt field):
      ph  – period header
      inc – income line
      xfr – transfer line
      sbh – section header (funded / unfunded)
      fdt – funded date label
      fbl – funded bill
      fba – funded running balance
      udt – unfunded date label
      ubl – unfunded bill
      uba – unfunded running balance
      pf  – period footer (end bal + safe-to-spend)
    All dict values are str so Reflex can type the list as list[dict[str,str]].
    Boolean flags are encoded as "1" (true) or "" (false).
    """
    rows: list[dict] = []
    for p in periods:
        rows.append({
            "rt": "ph",
            "lbl": p["label"],
            "sub": p["date_range"],
            "amt": p["net_fmt"],
            "c1":  "#34d399" if not p["net_negative"] else "#f87171",
            "c2":  p["sts_color"],
            "neg": "1" if p["net_negative"] else "",
            "shf": "1" if p["shortfall"] else "",
            "pid": p["id"],
            "pt":  p["type"],
            "ebf": p["end_bal_fmt"],
            "ebn": "1" if p["end_bal_negative"] else "",
            "sgn": p["net_sign"],
        })
        if p.get("has_income"):
            for ln in p["income_lines"]:
                rows.append({"rt": "inc", "lbl": ln["label"], "amt": ln["amount_fmt"],
                             "c1": "", "c2": "", "neg": "", "shf": "", "pid": p["id"],
                             "pt": "", "ebf": "", "ebn": "", "sgn": ""})
        if p.get("has_transfers"):
            for ln in p["transfer_lines"]:
                rows.append({"rt": "xfr", "lbl": ln["label"], "amt": ln["amount_fmt"],
                             "c1": "", "c2": "", "neg": "", "shf": "", "pid": p["id"],
                             "pt": "", "ebf": "", "ebn": "", "sgn": ""})
        if p.get("has_funded"):
            rows.append({"rt": "sbh", "lbl": "Pre-Funded", "amt": "",
                         "c1": "#34d399", "c2": "", "neg": "", "shf": "", "pid": p["id"],
                         "pt": "", "ebf": "", "ebn": "", "sgn": ""})
            for ln in p["funded_lines"]:
                rt = {"date": "fdt", "bill": "fbl", "bal": "fba"}.get(ln["row_type"], "fbl")
                rows.append({"rt": rt, "lbl": ln["text"], "amt": ln["amount_fmt"],
                             "c1": "", "c2": "", "neg": "", "shf": "", "pid": p["id"],
                             "pt": "", "ebf": "", "ebn": "", "sgn": ""})
        if p.get("has_unfunded"):
            rows.append({"rt": "sbh", "lbl": "Needs Funding", "amt": "",
                         "c1": "#f87171", "c2": "", "neg": "", "shf": "", "pid": p["id"],
                         "pt": "", "ebf": "", "ebn": "", "sgn": ""})
            for ln in p["unfunded_lines"]:
                rt = {"date": "udt", "bill": "ubl", "bal": "uba"}.get(ln["row_type"], "ubl")
                neg = "1" if ln["text"].startswith("-") else ""
                rows.append({"rt": rt, "lbl": ln["text"], "amt": ln["amount_fmt"],
                             "c1": "", "c2": "", "neg": neg, "shf": "", "pid": p["id"],
                             "pt": "", "ebf": "", "ebn": "", "sgn": ""})
        rows.append({
            "rt": "pf",
            "lbl": p["start_bal_fmt"],
            "amt": p["safe_to_spend_fmt"],
            "c1":  p["sts_color"],
            "c2":  "",
            "neg": "1" if p["end_bal_negative"] else "",
            "shf": "1" if p["shortfall"] else "",
            "pid": p["id"],
            "pt":  "",
            "ebf": p["end_bal_fmt"],
            "ebn": "1" if p["end_bal_negative"] else "",
            "sgn": "",
        })
    return rows


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
    _polling:      bool = False  # background poll running

    # ── Add-transaction sheet ─────────────────────────────────────────────────
    sheet_open:        bool = False
    sheet_type:        str  = "out"      # "out" | "in" | "xfr"
    sheet_amount:      str  = ""
    sheet_desc:        str  = ""
    sheet_date:        str  = ""
    sheet_account:     str  = ""
    sheet_to_account:  str  = ""         # xfr destination
    sheet_bucket:      str  = ""
    sheet_income_type: str  = "paycheck" # "paycheck" | "other"
    sheet_error:       str  = ""
    sheet_saving:      bool = False

    # ── Bucket transaction expand ─────────────────────────────────────────────
    expanded_bucket_id:  str        = ""
    expanded_bucket_txs: list[dict] = []

    # ── Ledger search ─────────────────────────────────────────────────────────
    ledger_query: str = ""

    # ── Category select options ───────────────────────────────────────────────
    cat_options: list[dict[str, Any]] = []

    # ── Inline bucket allocation editing ─────────────────────────────────────
    editing_bid:    str  = ""
    edit_alloc_val: str  = ""

    # ── Bucket settings dialog ────────────────────────────────────────────────
    bsettings_open: bool = False
    bsettings_bid:  str  = ""
    bsf_name:       str  = ""
    bsf_type:       str  = "expense"
    bsf_cat_id:     str  = ""
    bsf_budget:     str  = ""
    bsf_rollover:   bool = False
    bsf_due_day:    str  = ""
    bsf_due_amount: str  = ""
    bsf_pay_freq:   str  = ""
    bsf_notes:      str  = ""
    bsf_saving:     bool = False
    bsf_error:      str  = ""

    # ── Add bucket strip ──────────────────────────────────────────────────────
    add_bkt_name:          str  = ""
    add_bkt_cat_id:        str  = ""
    add_bkt_type:          str  = "expense"
    add_bkt_saving:        bool = False
    add_bkt_creating_cat:  bool = False
    add_bkt_new_cat_name:  str  = ""
    add_bkt_new_cat_color: str  = "#818cf8"

    # ── Bucket settings — extended type-aware fields ──────────────────
    bsf_target_amount: str   = ""
    bsf_target_date:   str   = ""    # "YYYY-MM" for month picker
    bsf_contrib_freq:  str   = ""    # monthly | weekly | biweekly
    bsf_recurring:     bool  = False
    bsf_skip:          bool  = False
    bsf_vault_total:   float = 0.0
    bsf_vault_total_fmt: str = "$0.00"
    bsf_transfer_bid:  str   = ""
    bsf_transfer_amt:  str   = ""
    bsf_release_amt:   str   = ""

    # ── Setup panel — paychecks ───────────────────────────────────────
    paycheck_rows:  list[dict[str, Any]] = []
    setup_pc_label:  str  = ""
    setup_pc_amount: str  = ""
    setup_pc_freq:   str  = "14"    # 7 | 14 | 15
    setup_pc_anchor: str  = ""
    setup_pc_saving: bool = False
    setup_pc_error:  str  = ""

    # ── Setup panel — allocation rules ────────────────────────────────
    alloc_rule_rows:     list[dict[str, Any]] = []
    rule_sheet_open:     bool = False
    rule_sheet_itype:    str  = "internal"    # internal | external
    rule_sheet_name:     str  = ""
    rule_sheet_val_type: str  = "fixed"       # fixed | pct
    rule_sheet_value:    str  = ""
    rule_sheet_bid:      str  = ""
    rule_sheet_saving:   bool = False
    rule_sheet_error:    str  = ""

    # ── Edit transaction ──────────────────────────────────────────
    edit_tx_open:         bool = False
    edit_tx_id:           str  = ""
    edit_tx_type:         str  = "out"
    edit_tx_desc:         str  = ""
    edit_tx_amount:       str  = ""
    edit_tx_date:         str  = ""
    edit_tx_account:      str  = ""
    edit_tx_to_account:   str  = ""
    edit_tx_bucket:       str  = ""
    edit_tx_income_type:  str  = "paycheck"
    edit_tx_reconciled:   bool = False
    edit_tx_saving:       bool = False
    edit_tx_error:        str  = ""

    # ── Payday modal ──────────────────────────────────────────────────
    payday_open:       bool = False
    payday_amount_fmt: str  = ""
    payday_rows:       list[dict[str, Any]] = []
    payday_saving:     bool = False

    # ── Forecast ──────────────────────────────────────────────────────────────
    forecast_range:    int              = 3
    forecast_account:  str              = ""
    forecast_rows:     list[dict]       = []   # flat display rows (all-str values)
    forecast_accounts: list[dict]       = []   # [{id,name,color,balance_fmt}]
    forecast_loading:  bool             = False
    fc_start_bal:      str              = "—"
    fc_total_income:   str              = "—"
    fc_total_unfunded: str              = "—"
    fc_safe_to_spend:  str              = "—"
    fc_sts_color:      str              = "#818cf8"
    fc_shortfall_count: int             = 0

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
        # Keep month_totals row; filter tx rows by query
        matches: list[dict] = []
        for row in self.ledger_rows:
            if row["row_type"] == "month_totals":
                matches.append(row)
            elif row["row_type"] == "tx":
                if q in row.get("desc", "").lower() or q in row.get("bucket", "").lower():
                    matches.append(dict(row))
        # Re-stamp date_label on first tx of each date group
        prev = ""
        for row in matches:
            if row["row_type"] != "tx":
                continue
            d = row.get("date", "")
            row["date_label"] = _date_label(d) if d != prev else ""
            prev = d
        return matches

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
        self.forecast_rows      = _flatten_periods(result["periods"])

    def set_forecast_range(self, n: int):
        self.forecast_range = n
        self._run_forecast()

    def set_forecast_account(self, aid: str):
        self.forecast_account = aid
        self._run_forecast()

    def _refresh_forecast_accounts(self):
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
        # Start background poll (only one per session)
        if not self._polling:
            self._polling = True
            yield AppState.poll_data

    @rx.event(background=True)
    async def poll_data(self):
        """Refresh data from DB every 30 seconds silently."""
        while True:
            await asyncio.sleep(30)
            async with self:
                if not self.is_logged_in:
                    self._polling = False
                    return
                try:
                    data = DB.load_all(self.user_id, self.access_token)
                    self._raw = data
                    self._process(data, self.active_mid)
                except Exception:
                    pass

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
        self.sheet_open        = True
        self.sheet_type        = "out"
        self.sheet_amount      = ""
        self.sheet_desc        = ""
        self.sheet_date        = date.today().isoformat()
        self.sheet_account     = self.account_options[0]["id"] if self.account_options else ""
        self.sheet_to_account  = self.account_options[1]["id"] if len(self.account_options) > 1 else ""
        self.sheet_bucket      = self.expense_buckets[0]["id"] if self.expense_buckets else ""
        self.sheet_income_type = "paycheck"
        self.sheet_error       = ""

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
                "accountId":    self.sheet_account,
                "monthId":      mid,
                "type":         self.sheet_type,
                "amount":       amount,
                "date":         self.sheet_date,
                "desc":         self.sheet_desc,
                "bucketId":     self.sheet_bucket if self.sheet_type == "out" else "",
                "toAccountId":  self.sheet_to_account if self.sheet_type == "xfr" else "",
                "incomeType":   self.sheet_income_type if self.sheet_type == "in" else None,
            }
            tx_id = DB.insert_transaction(self.user_id, self.access_token, tx)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
            self.sheet_open  = False
            self.sheet_error = ""
            # Trigger payday modal for income transactions
            if self.sheet_type == "in":
                self._compute_payday_rows(amount)
                if self.payday_rows:
                    self.payday_amount_fmt = _fmt(amount)
                    self.payday_open = True
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
        self._set_raw_alloc(bucket_id, budget)
        self._process(self._raw, self.active_mid)
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, self.active_mid)
            DB.upsert_alloc(self.user_id, self.access_token, self.active_mid, bucket_id, budget)
            yield rx.toast.success("Bucket filled", duration=1500)
        except Exception as e:
            if DB.is_auth_error(e):
                yield rx.redirect("/login")
            else:
                data = DB.load_all(self.user_id, self.access_token)
                self._raw = data
                self._process(data, self.active_mid)
                yield rx.toast.error("Could not fill bucket")

    # ─────────────────────────────────────────────────────────────────────────
    #  Inline allocation editing
    # ─────────────────────────────────────────────────────────────────────────

    def start_edit_alloc(self, bid: str, alloc_fmt: str):
        v = alloc_fmt.replace(",", "").replace("$", "")
        try:
            f = float(v)
            v = str(int(f)) if f == int(f) else f"{f:.2f}"
        except ValueError:
            v = "0"
        self.editing_bid    = bid
        self.edit_alloc_val = v

    def cancel_alloc_edit(self):
        self.editing_bid    = ""
        self.edit_alloc_val = ""

    async def save_alloc_edit(self):
        bid = self.editing_bid
        val = self.edit_alloc_val
        if not bid:
            return
        self.editing_bid    = ""
        self.edit_alloc_val = ""
        try:
            amount = round(float(val or "0"), 2)
        except ValueError:
            return
        self._set_raw_alloc(bid, amount)
        self._process(self._raw, self.active_mid)
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, self.active_mid)
            DB.upsert_alloc(self.user_id, self.access_token, self.active_mid, bid, amount)
            yield rx.toast.success("Saved", duration=1200)
        except Exception as e:
            if DB.is_auth_error(e):
                yield rx.redirect("/login")
            else:
                data = DB.load_all(self.user_id, self.access_token)
                self._raw = data
                self._process(data, self.active_mid)
                yield rx.toast.error("Could not save allocation")

    def handle_alloc_key(self, key: str):
        if key == "Escape":
            self.editing_bid    = ""
            self.edit_alloc_val = ""
        elif key == "Enter":
            yield AppState.save_alloc_edit()

    def _set_raw_alloc(self, bid: str, amount: float):
        months = self._raw.get("months", [])
        mid    = self.active_mid
        for m in months:
            if m.get("id") == mid:
                m.setdefault("allocations", {})[bid] = amount
                return
        months.append({
            "id": mid, "closed": False,
            "allocations": {bid: amount}, "budgets": {},
            "rolloverReleased": {}, "skippedBuckets": {}, "vaultWithdrawals": {},
        })
        self._raw["months"] = months

    # ─────────────────────────────────────────────────────────────────────────
    #  Bucket inline transaction expand
    # ─────────────────────────────────────────────────────────────────────────

    def toggle_bucket_expand(self, bid: str):
        if self.expanded_bucket_id == bid:
            self.expanded_bucket_id = ""
            self.expanded_bucket_txs = []
            return
        self.expanded_bucket_id = bid
        raw_txs = (self._raw or {}).get("txs", [])
        txs = [
            t for t in raw_txs
            if t.get("bucketId") == bid and t.get("monthId") == self.active_mid
        ]
        txs.sort(key=lambda t: t.get("date", ""), reverse=True)
        self.expanded_bucket_txs = [
            {
                "desc":       t.get("desc") or "—",
                "amount_fmt": f"−{_fmt(float(t.get('amount') or 0))}",
                "date_label": _date_label(t.get("date", "")),
            }
            for t in txs
        ]

    # ─────────────────────────────────────────────────────────────────────────
    #  Bucket settings dialog
    # ─────────────────────────────────────────────────────────────────────────

    def open_bucket_settings(self, bid: str):
        bucket = next((b for b in (self._raw.get("buckets") or []) if b["id"] == bid), None)
        if not bucket:
            return
        all_months = self._raw.get("months") or []

        def _fnum(v):
            v = float(v or 0)
            return str(int(v)) if v == int(v) else f"{v:.2f}"

        self.bsettings_bid     = bid
        self.bsf_name          = bucket.get("name", "")
        self.bsf_type          = bucket.get("type", "expense")
        self.bsf_cat_id        = bucket.get("catId", "")
        self.bsf_budget        = _fnum(bucket.get("defaultBudget"))
        self.bsf_rollover      = bool(bucket.get("rollover"))
        self.bsf_due_day       = str(bucket.get("dueDay") or "")
        self.bsf_due_amount    = _fnum(bucket.get("dueAmount"))
        self.bsf_pay_freq      = bucket.get("payFreq") or ""
        self.bsf_notes         = bucket.get("notes") or ""
        self.bsf_target_amount = _fnum(bucket.get("targetAmount"))
        self.bsf_target_date   = bucket.get("targetDate") or ""
        self.bsf_contrib_freq  = bucket.get("contribFreq") or ""
        self.bsf_recurring     = bool(bucket.get("recurring"))
        # Skip for active month
        active_month = next((m for m in all_months if m.get("id") == self.active_mid), {})
        self.bsf_skip = bool(active_month.get("skippedBuckets", {}).get(bid))
        # Vault info
        if bucket.get("type") == "vault":
            vt = vault_accumulated(bid, all_months)
            self.bsf_vault_total     = vt
            self.bsf_vault_total_fmt = _fmt(vt)
        else:
            self.bsf_vault_total     = 0.0
            self.bsf_vault_total_fmt = "$0.00"
        self.bsf_transfer_bid = ""
        self.bsf_transfer_amt = ""
        self.bsf_release_amt  = ""
        self.bsf_error        = ""
        self.bsf_saving       = False
        self.bsettings_open   = True

    def set_bsettings_open(self, v: bool):
        self.bsettings_open = v
        if not v:
            self.bsf_error = ""

    async def save_bucket_settings(self):
        if not self.bsf_name.strip():
            self.bsf_error = "Name is required"
            return
        try:
            budget_val        = round(float(self.bsf_budget or "0"), 2)
            due_amount_val    = round(float(self.bsf_due_amount or "0"), 2)
            target_amount_val = round(float(self.bsf_target_amount or "0"), 2)
        except ValueError:
            self.bsf_error = "Invalid number"
            return
        self.bsf_saving = True
        self.bsf_error  = ""
        yield
        try:
            DB.upsert_bucket(self.user_id, self.access_token, self.bsettings_bid, {
                "name":           self.bsf_name.strip(),
                "type":           self.bsf_type,
                "cat_id":         self.bsf_cat_id,
                "rollover":       self.bsf_rollover,
                "default_budget": budget_val,
                "due_day":        self.bsf_due_day.strip() or None,
                "due_amount":     due_amount_val,
                "pay_freq":       self.bsf_pay_freq or None,
                "notes":          self.bsf_notes.strip(),
                "target_amount":  target_amount_val,
                "target_date":    self.bsf_target_date.strip() or None,
                "contrib_freq":   self.bsf_contrib_freq or None,
                "recurring":      self.bsf_recurring,
            })
            data = DB.load_all(self.user_id, self.access_token)
            self._raw           = data
            self._process(data, self.active_mid)
            self.bsettings_open = False
            self.bsf_saving     = False
            yield rx.toast.success("Bucket saved")
        except Exception as e:
            self.bsf_saving = False
            self.bsf_error  = str(e)

    async def archive_bucket_confirm(self, bid: str):
        try:
            DB.upsert_bucket(self.user_id, self.access_token, bid, {"archived": True})
            data = DB.load_all(self.user_id, self.access_token)
            self._raw           = data
            self._process(data, self.active_mid)
            self.bsettings_open = False
            yield rx.toast.success("Bucket archived")
        except Exception as e:
            self.bsf_error = str(e)

    async def vault_transfer(self):
        """Move allocation from vault to a destination bucket (net RTS = 0)."""
        bid  = self.bsettings_bid
        dest = self.bsf_transfer_bid
        try:
            amt = round(float(self.bsf_transfer_amt or "0"), 2)
        except ValueError:
            self.bsf_error = "Invalid amount"
            return
        if amt <= 0 or not dest:
            self.bsf_error = "Amount and destination required"
            return
        months = self._raw.get("months") or []
        mid = self.active_mid
        active_month = next((m for m in months if m.get("id") == mid), None)
        if not active_month:
            active_month = {"id": mid, "closed": False, "allocations": {}, "budgets": {},
                            "rolloverReleased": {}, "skippedBuckets": {}, "vaultWithdrawals": {}}
            months.append(active_month)
            self._raw["months"] = months
        allocs     = active_month.setdefault("allocations", {})
        new_vault  = max(0.0, float(allocs.get(bid) or 0) - amt)
        new_dest   = round(float(allocs.get(dest) or 0) + amt, 2)
        allocs[bid]  = new_vault
        allocs[dest] = new_dest
        self._process(self._raw, mid)
        self.bsf_transfer_amt = ""
        self.bsettings_open   = False
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, mid)
            DB.upsert_alloc(self.user_id, self.access_token, mid, bid, new_vault)
            DB.upsert_alloc(self.user_id, self.access_token, mid, dest, new_dest)
            yield rx.toast.success("Vault transferred")
        except Exception as e:
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, mid)
            yield rx.toast.error("Transfer failed")

    async def vault_release_pool(self):
        """Release vault savings back to RTS pool."""
        bid = self.bsettings_bid
        try:
            release = round(float(self.bsf_release_amt or "0"), 2)
        except ValueError:
            self.bsf_error = "Invalid amount"
            return
        if release <= 0:
            self.bsf_error = "Amount must be positive"
            return
        months = self._raw.get("months") or []
        mid = self.active_mid
        active_month = next((m for m in months if m.get("id") == mid), {})
        allocs       = active_month.get("allocations", {})
        cur_alloc    = float(allocs.get(bid) or 0)
        from_alloc   = min(cur_alloc, release)
        from_prior   = max(0.0, release - from_alloc)
        new_alloc    = round(cur_alloc - from_alloc, 2)
        allocs[bid]  = new_alloc
        self._process(self._raw, mid)
        self.bsf_release_amt = ""
        self.bsettings_open  = False
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, mid)
            DB.upsert_alloc(self.user_id, self.access_token, mid, bid, new_alloc)
            if from_prior > 0:
                existing_wd = float(active_month.get("vaultWithdrawals", {}).get(bid) or 0)
                DB.upsert_vault_withdrawal(
                    self.user_id, self.access_token, mid, bid,
                    round(existing_wd + from_prior, 2)
                )
            yield rx.toast.success("Released to pool")
        except Exception as e:
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, mid)
            yield rx.toast.error("Release failed")

    # ─────────────────────────────────────────────────────────────────────────
    #  Add bucket (with optional inline category creation)
    # ─────────────────────────────────────────────────────────────────────────

    def toggle_create_cat(self):
        self.add_bkt_creating_cat = not self.add_bkt_creating_cat
        if self.add_bkt_creating_cat:
            self.add_bkt_cat_id = "new"
        else:
            self.add_bkt_cat_id = ""
            self.add_bkt_new_cat_name = ""

    def select_add_bkt_cat(self, v: str):
        if v == "new":
            self.add_bkt_creating_cat = True
            self.add_bkt_cat_id = "new"
        else:
            self.add_bkt_cat_id = v
            self.add_bkt_creating_cat = False
            self.add_bkt_new_cat_name = ""

    async def add_bucket_submit(self):
        if not self.add_bkt_name.strip():
            return
        cat_id = self.add_bkt_cat_id
        self.add_bkt_saving = True
        yield
        try:
            # Create the category first if user entered a new one
            if cat_id == "new" or self.add_bkt_creating_cat:
                if not self.add_bkt_new_cat_name.strip():
                    self.add_bkt_saving = False
                    return
                cat_id = DB.insert_category(
                    self.user_id, self.access_token,
                    self.add_bkt_new_cat_name.strip(),
                    self.add_bkt_new_cat_color,
                )
            if not cat_id:
                self.add_bkt_saving = False
                return
            DB.insert_bucket(
                self.user_id, self.access_token,
                self.add_bkt_name.strip(), cat_id, self.add_bkt_type,
            )
            data = DB.load_all(self.user_id, self.access_token)
            self._raw                  = data
            self._process(data, self.active_mid)
            self.add_bkt_name          = ""
            self.add_bkt_cat_id        = ""
            self.add_bkt_type          = "expense"
            self.add_bkt_new_cat_name  = ""
            self.add_bkt_new_cat_color = "#818cf8"
            self.add_bkt_creating_cat  = False
            self.add_bkt_saving        = False
            yield rx.toast.success("Bucket added")
        except Exception:
            self.add_bkt_saving = False
            yield rx.toast.error("Could not add bucket")

    # ─────────────────────────────────────────────────────────────────────────
    #  Distribute RTS
    # ─────────────────────────────────────────────────────────────────────────

    async def distribute_rts(self):
        """Spread RTS proportionally across underfunded buckets."""
        rts = self.rts
        if rts <= 0.005:
            return
        months = self._raw.get("months") or []
        mid    = self.active_mid
        active_month = next((m for m in months if m.get("id") == mid), {})
        active_buckets = [b for b in (self._raw.get("buckets") or []) if not b.get("archived")]

        underfunded = []
        for b in active_buckets:
            bid   = b["id"]
            btype = b.get("type", "expense")
            if btype == "vault":
                continue
            alloc  = b_alloc(active_month, bid)
            budget = b_budget(active_month, bid)
            if budget > 0 and alloc < budget:
                underfunded.append((bid, budget, alloc, budget - alloc))

        if not underfunded:
            yield rx.toast.info("All buckets are funded!")
            return

        total_gap = sum(g for _, _, _, g in underfunded)
        allocs = active_month.setdefault("allocations", {})
        new_allocs: dict[str, float] = {}
        for bid, budget, alloc, gap in underfunded:
            if rts >= total_gap:
                new_allocs[bid] = budget
            else:
                new_allocs[bid] = round(alloc + rts * (gap / total_gap), 2)
            allocs[bid] = new_allocs[bid]

        if active_month not in months:
            months.append(active_month)
            self._raw["months"] = months

        self._process(self._raw, mid)
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, mid)
            for bid, new_val in new_allocs.items():
                DB.upsert_alloc(self.user_id, self.access_token, mid, bid, new_val)
            yield rx.toast.success("Distributed!")
        except Exception:
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, mid)
            yield rx.toast.error("Could not distribute")

    # ─────────────────────────────────────────────────────────────────────────
    #  Paychecks
    # ─────────────────────────────────────────────────────────────────────────

    async def add_paycheck_submit(self):
        if not self.setup_pc_label.strip():
            self.setup_pc_error = "Label required"
            return
        try:
            amt  = round(float(self.setup_pc_amount or "0"), 2)
            freq = int(self.setup_pc_freq or "14")
        except ValueError:
            self.setup_pc_error = "Invalid number"
            return
        if amt <= 0:
            self.setup_pc_error = "Amount must be positive"
            return
        self.setup_pc_saving = True
        self.setup_pc_error  = ""
        yield
        try:
            DB.insert_paycheck(
                self.user_id, self.access_token,
                self.setup_pc_label.strip(), amt, freq,
                self.setup_pc_anchor.strip(),
            )
            data = DB.load_all(self.user_id, self.access_token)
            self._raw            = data
            self._process(data, self.active_mid)
            self.setup_pc_label  = ""
            self.setup_pc_amount = ""
            self.setup_pc_anchor = ""
            self.setup_pc_saving = False
            yield rx.toast.success("Paycheck added")
        except Exception as e:
            self.setup_pc_saving = False
            self.setup_pc_error  = str(e)

    async def delete_paycheck_item(self, pc_id: str):
        try:
            DB.delete_paycheck(self.user_id, self.access_token, pc_id)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
            yield rx.toast.success("Deleted")
        except Exception:
            yield rx.toast.error("Could not delete paycheck")

    # ─────────────────────────────────────────────────────────────────────────
    #  Allocation rules
    # ─────────────────────────────────────────────────────────────────────────

    def open_rule_sheet(self, rule_type: str):
        self.rule_sheet_itype    = rule_type
        self.rule_sheet_name     = ""
        self.rule_sheet_val_type = "fixed"
        self.rule_sheet_value    = ""
        self.rule_sheet_bid      = ""
        self.rule_sheet_error    = ""
        self.rule_sheet_saving   = False
        self.rule_sheet_open     = True

    def close_rule_sheet(self):
        self.rule_sheet_open  = False
        self.rule_sheet_error = ""

    async def add_alloc_rule_submit(self):
        if not self.rule_sheet_name.strip():
            self.rule_sheet_error = "Name required"
            return
        try:
            value = round(float(self.rule_sheet_value or "0"), 4)
        except ValueError:
            self.rule_sheet_error = "Invalid value"
            return
        if value <= 0:
            self.rule_sheet_error = "Value must be positive"
            return
        if self.rule_sheet_itype == "internal" and not self.rule_sheet_bid:
            self.rule_sheet_error = "Select a bucket"
            return
        self.rule_sheet_saving = True
        self.rule_sheet_error  = ""
        yield
        try:
            DB.insert_alloc_rule(
                self.user_id, self.access_token,
                self.rule_sheet_name.strip(),
                self.rule_sheet_itype,
                self.rule_sheet_val_type,
                value,
                self.rule_sheet_bid,
            )
            data = DB.load_all(self.user_id, self.access_token)
            self._raw              = data
            self._process(data, self.active_mid)
            self.rule_sheet_open   = False
            self.rule_sheet_saving = False
            yield rx.toast.success("Rule added")
        except Exception as e:
            self.rule_sheet_saving = False
            self.rule_sheet_error  = str(e)

    async def toggle_alloc_rule_item(self, rule_id: str):
        try:
            DB.toggle_alloc_rule(self.user_id, self.access_token, rule_id)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
        except Exception:
            yield rx.toast.error("Could not toggle rule")

    async def delete_alloc_rule_item(self, rule_id: str):
        try:
            DB.delete_alloc_rule(self.user_id, self.access_token, rule_id)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
            yield rx.toast.success("Rule deleted")
        except Exception:
            yield rx.toast.error("Could not delete rule")

    # ─────────────────────────────────────────────────────────────────────────
    #  Edit transaction
    # ─────────────────────────────────────────────────────────────────────────

    def open_edit_tx(self, tx_id: str):
        tx = next((t for t in (self._raw.get("txs") or []) if t["id"] == tx_id), None)
        if not tx:
            return
        v = float(tx.get("amount") or 0)
        self.edit_tx_id           = tx_id
        self.edit_tx_type         = tx.get("type", "out")
        self.edit_tx_desc         = tx.get("desc") or ""
        self.edit_tx_amount       = str(int(v)) if v == int(v) else f"{v:.2f}"
        self.edit_tx_date         = tx.get("date", "")
        self.edit_tx_account      = tx.get("accountId", "")
        self.edit_tx_to_account   = tx.get("toAccountId", "")
        self.edit_tx_bucket       = tx.get("bucketId", "")
        self.edit_tx_income_type  = tx.get("incomeType", "paycheck") or "paycheck"
        self.edit_tx_reconciled   = bool(tx.get("reconciled"))
        self.edit_tx_error        = ""
        self.edit_tx_saving       = False
        self.edit_tx_open         = True

    def set_edit_tx_open(self, v: bool):
        self.edit_tx_open = v
        if not v:
            self.edit_tx_error = ""

    async def delete_from_edit_tx(self):
        tx_id = self.edit_tx_id
        if not tx_id:
            return
        self.edit_tx_open = False
        yield
        try:
            DB.delete_transaction(self.user_id, self.access_token, tx_id)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
            yield rx.toast.success("Transaction deleted")
        except Exception:
            yield rx.toast.error("Could not delete transaction")

    async def save_edit_tx(self):
        if not self.edit_tx_id:
            return
        try:
            amount = round(float(self.edit_tx_amount or "0"), 2)
        except ValueError:
            self.edit_tx_error = "Invalid amount"
            return
        if amount <= 0:
            self.edit_tx_error = "Amount must be positive"
            return
        self.edit_tx_saving = True
        self.edit_tx_error  = ""
        yield
        try:
            DB.update_transaction(self.user_id, self.access_token, self.edit_tx_id, {
                "description":        self.edit_tx_desc.strip(),
                "amount":             amount,
                "date":               self.edit_tx_date,
                "account_id":         self.edit_tx_account,
                "bucket_id":          self.edit_tx_bucket or None,
                "to_account_id":      self.edit_tx_to_account or None,
                "income_type":        self.edit_tx_income_type if self.edit_tx_type == "in" else None,
                "reconciled":         self.edit_tx_reconciled,
            })
            data = DB.load_all(self.user_id, self.access_token)
            self._raw           = data
            self._process(data, self.active_mid)
            self.edit_tx_open   = False
            self.edit_tx_saving = False
            yield rx.toast.success("Transaction updated")
        except Exception as e:
            self.edit_tx_saving = False
            self.edit_tx_error  = str(e)

    # ─────────────────────────────────────────────────────────────────────────
    #  Payday modal
    # ─────────────────────────────────────────────────────────────────────────

    def _compute_payday_rows(self, income_amount: float):
        rules      = self._raw.get("allocationRules") or []
        buckets    = self._raw.get("buckets") or []
        bucket_map = {b["id"]: b.get("name", "") for b in buckets}
        rows = []
        for r in rules:
            if not r.get("active", True):
                continue
            rule_type = r.get("rule_type", "internal")
            val_type  = r.get("value_type", "fixed")
            value     = float(r.get("value") or 0)
            if val_type == "pct":
                amt     = round(income_amount * value / 100, 2)
                val_str = f"{value}%"
            else:
                amt     = round(value, 2)
                val_str = _fmt(value)
            bid = r.get("bucket_id") or ""
            rows.append({
                "id":          r["id"],
                "name":        r.get("name", ""),
                "rule_type":   rule_type,
                "bucket_id":   bid,
                "bucket_name": bucket_map.get(bid, ""),
                "value_str":   val_str,
                "amount":      amt,
                "amount_fmt":  _fmt(amt),
                "included":    "1",
            })
        self.payday_rows = rows

    def toggle_payday_row(self, rule_id: str):
        self.payday_rows = [
            {**row, "included": "" if row["included"] else "1"}
            if row["id"] == rule_id else row
            for row in self.payday_rows
        ]

    def close_payday(self):
        self.payday_open = False

    async def apply_payday(self):
        mid = self.active_mid
        self.payday_saving = True
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, mid)
            all_months   = self._raw.get("months") or []
            active_month = next((m for m in all_months if m.get("id") == mid), {})
            cur_allocs   = active_month.get("allocations", {})
            for row in self.payday_rows:
                if row["included"] and row["rule_type"] == "internal" and row["bucket_id"]:
                    bid      = row["bucket_id"]
                    existing = float(cur_allocs.get(bid) or 0)
                    DB.upsert_alloc(
                        self.user_id, self.access_token, mid, bid,
                        round(existing + row["amount"], 2),
                    )
            data = DB.load_all(self.user_id, self.access_token)
            self._raw      = data
            self._process(data, mid)
            self.payday_open   = False
            self.payday_saving = False
            yield rx.toast.success("Allocations applied!")
        except Exception as e:
            self.payday_saving = False
            yield rx.toast.error("Could not apply allocations")

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

        # ── Category select options ────────────────────────────────────────
        self.cat_options = [
            {"id": c["id"], "name": c.get("name", ""), "color": c.get("color", "#818cf8")}
            for c in cats_sorted
        ]

        # ── Bucket rows (flat list with category headers) ──────────────────
        skipped_map = active_month.get("skippedBuckets", {})
        rows: list[dict] = []

        for cat in cats_sorted:
            cid       = cat["id"]
            cat_color = cat.get("color", "#818cf8")
            cat_buckets = sorted(
                [b for b in active_buckets if b.get("catId") == cid],
                key=lambda b: b.get("order", 0),
            )
            if not cat_buckets:
                continue

            # Category subtotals
            cat_alloc_sum  = sum(b_alloc(active_month, b["id"]) for b in cat_buckets)
            cat_budget_sum = sum(
                b_budget(active_month, b["id"])
                for b in cat_buckets if b.get("type") != "vault"
            )
            cat_pct      = min(100, round(cat_alloc_sum / cat_budget_sum * 100)) if cat_budget_sum > 0 else 100
            is_cat_funded = cat_pct >= 100

            rows.append({
                "row_type": "header", "name": cat.get("name", ""), "id": cid,
                "color": cat_color,
                "cat_alloc_fmt": _fmt(cat_alloc_sum),
                "budget_h_fmt":  _fmt(cat_budget_sum),
                "cat_pct_str":   f"{cat_pct}%",
                "is_cat_funded": "1" if is_cat_funded else "",
                # bucket-field defaults (keep flat-list uniform)
                "type": "", "alloc": 0.0, "budget": 0.0, "spent": 0.0, "avail": 0.0,
                "status": "", "pill": "", "avail_fmt": "", "alloc_fmt": "", "budget_fmt": "",
                "spent_fmt": "", "pct_str": "0%", "avail_color": "", "avail_bg": "",
                "avail_border": "", "bar_color": "", "prog_h": "0px", "show_fill": False,
                "funding_pct_str": "0%", "gap": 0.0, "gap_fmt": "", "is_funded": "",
                "roll_fmt": "", "show_roll": "", "target_fmt": "",
                "sinking_pct_str": "0%", "months_left_str": "",
                "show_goal": "", "vault_fmt": "", "show_vault": "",
                "due_label": "", "due_urgency": "", "is_skipped": "",
            })

            for b in cat_buckets:
                bid   = b["id"]
                btype = b.get("type", "expense")
                alloc  = b_alloc(active_month, bid)
                budget = b_budget(active_month, bid)

                if btype == "vault":
                    vault_total = vault_accumulated(bid, all_months)
                    spent       = vault_total
                    avail       = vault_total
                else:
                    vault_total = 0.0
                    spent = b_spent(mid, bid, txs)
                    avail = bucket_available(b, active_month, all_months, txs)

                status = _bucket_status(alloc, budget, spent, avail)
                pill   = _pill(status)

                # ZBB funding metrics
                gap         = max(0.0, round(budget - alloc, 2))
                funding_pct = min(100, round(alloc / budget * 100)) if budget > 0 else (100 if btype == "vault" else 0)
                is_funded   = funding_pct >= 100

                # Rollover chip
                roll_bal  = rollover_bal(b, active_month, all_months, txs) if b.get("rollover") else 0.0
                show_roll = bool(b.get("rollover") and abs(roll_bal) > 0.005)
                roll_fmt  = (f"+{_fmt(roll_bal)}" if roll_bal >= 0 else _fmt(roll_bal)) if show_roll else ""

                # Sinking / goal progress toward target
                target_amount = float(b.get("targetAmount") or 0)
                if btype in ("sinking", "goal") and target_amount > 0:
                    saved       = max(0.0, avail)
                    sinking_pct = min(100, round(saved / target_amount * 100))
                    target_fmt  = f"{_fmt(saved)} / {_fmt(target_amount)}"
                    show_goal   = True
                else:
                    sinking_pct = 0
                    target_fmt  = ""
                    show_goal   = False

                ml = _months_left(b.get("targetDate") or "")
                months_left_str = f"{ml}mo left" if ml > 0 else ""

                # Vault display
                show_vault = btype == "vault"
                vault_fmt  = _fmt(vault_total) if show_vault else ""

                # Due date badge
                due_label, due_urgency = _due_info(b.get("dueDay") or "", mid)

                # Skip flag
                is_skipped = bool(skipped_map.get(bid))

                rows.append({
                    "row_type":  "bucket",
                    "id":        bid,
                    "name":      b.get("name", ""),
                    "type":      btype,
                    "color":     cat_color,
                    "alloc":     alloc,
                    "budget":    budget,
                    "spent":     spent,
                    "avail":     avail,
                    "status":    status,
                    "pill":      pill,
                    "avail_fmt":    _fmt(avail),
                    "alloc_fmt":    _fmt(alloc),
                    "budget_fmt":   _fmt(budget) if budget > 0 else "",
                    "spent_fmt":    _fmt(spent),
                    "pct_str":      f"{min(100, round(spent/budget*100)) if budget > 0 else 0}%",
                    "avail_color":  _avail_color(pill),
                    "avail_bg":     _avail_color(pill) + "1f",
                    "avail_border": "1px solid " + _avail_color(pill) + "33",
                    "bar_color":    _bar_color(pill),
                    "prog_h":       "3px",
                    "show_fill":    bool(budget > 0 and alloc < budget and btype != "vault"),
                    # ZBB fields
                    "funding_pct_str": f"{funding_pct}%",
                    "gap":            gap,
                    "gap_fmt":        f"-{_fmt(gap)}" if gap > 0.005 else "",
                    "is_funded":      "1" if is_funded else "",
                    "roll_fmt":       roll_fmt,
                    "show_roll":      "1" if show_roll else "",
                    "target_fmt":     target_fmt,
                    "sinking_pct_str": f"{sinking_pct}%",
                    "months_left_str": months_left_str,
                    "show_goal":      "1" if show_goal else "",
                    "vault_fmt":      vault_fmt,
                    "show_vault":     "1" if show_vault else "",
                    "due_label":      due_label,
                    "due_urgency":    due_urgency,
                    "is_skipped":     "1" if is_skipped else "",
                    # header-field defaults
                    "cat_alloc_fmt": "", "budget_h_fmt": "",
                    "cat_pct_str": "0%", "is_cat_funded": "",
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

        # Uniform defaults for all row types
        _TX_DEFAULTS = {
            "id": "", "desc": "", "type": "", "amount": 0.0,
            "amount_fmt": "", "amt_color": "", "account": "", "to_account": "",
            "bucket": "", "income_type": "", "scheduled": False, "reconciled": False,
            "left_border": "none", "type_chip": "", "chip_color": "#8282a2",
            "chip_bg": "#8282a218", "chip_border": "1px solid #8282a233",
            "reconciled_str": "", "inc_fmt": "", "spent_fmt": "",
            "date_label": "",
        }
        _HDR_DEFAULTS = {"label": "", "date": "", "net_fmt": "", "net_color": ""}

        ledger_flat: list[dict] = []

        # Month totals summary row (income and spending for the month)
        month_net = inc_total - sp_total
        ledger_flat.append({
            "row_type":  "month_totals",
            **_TX_DEFAULTS,
            **_HDR_DEFAULTS,
            "net_fmt":    _fmt(month_net),
            "net_color":  "#34d399" if month_net >= 0 else "#f87171",
            "inc_fmt":    f"+{_fmt(inc_total)}",
            "spent_fmt":  f"−{_fmt(sp_total)}",
        })

        prev_date_str = None
        for t in ledger_txs:
            ttype = t.get("type", "out")
            amt   = float(t.get("amount") or 0)
            sched = is_scheduled(t)
            recon = bool(t.get("reconciled"))
            date_str = t.get("date", "")
            # Embed date label into first tx of each new date
            this_date_label = _date_label(date_str) if date_str != prev_date_str else ""
            prev_date_str = date_str
            if True:

                amt_color = (
                    "#34d399" if ttype == "in" else
                    "#fbbf24" if sched else
                    "#f87171" if ttype == "out" else
                    "#8282a2"   # xfr — neutral, money staying in system
                )
                amt_prefix = (
                    "+" if ttype == "in" else
                    ""  if ttype == "xfr" else
                    "−"
                )
                left_border = (
                    "3px solid #34d399" if ttype == "in" and not sched else
                    "3px solid #fbbf24" if sched else
                    "none"
                )
                type_chip = (
                    "Income"    if ttype == "in" and not sched else
                    "Scheduled" if sched else
                    "Transfer"  if ttype == "xfr" else
                    ""
                )
                chip_color = (
                    "#34d399" if ttype == "in" and not sched else
                    "#fbbf24" if sched else
                    "#8282a2"
                )

                from_name = acct_map.get(t.get("accountId", ""), "")
                to_name   = acct_map.get(t.get("toAccountId", ""), "")
                # Sub-label: for transfers show "From → To", else bucket or account
                if ttype == "xfr" and to_name:
                    sub_label = f"{from_name} → {to_name}"
                elif bucket_map.get(t.get("bucketId", "")):
                    sub_label = bucket_map[t["bucketId"]]
                else:
                    sub_label = from_name

                ledger_flat.append({
                    "row_type":       "tx",
                    "id":             t["id"],
                    "date":           date_str,
                    "date_label":     this_date_label,
                    "desc":           t.get("desc") or "",
                    "type":           ttype,
                    "amount":         amt,
                    "amount_fmt":     f"{amt_prefix}{_fmt(amt)}",
                    "amt_color":      amt_color,
                    "account":        sub_label,
                    "to_account":     to_name,
                    "bucket":         bucket_map.get(t.get("bucketId", ""), ""),
                    "income_type":    t.get("incomeType", "") or "",
                    "scheduled":      sched,
                    "reconciled":     recon,
                    "reconciled_str": "✓" if recon else "",
                    "left_border":    left_border,
                    "type_chip":      type_chip,
                    "chip_color":     chip_color,
                    "chip_bg":        chip_color + "18",
                    "chip_border":    "1px solid " + chip_color + "33",
                    **_HDR_DEFAULTS,
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

        # ── Paycheck rows ──────────────────────────────────────────────────
        FREQ_LABELS = {"7": "Weekly", "14": "Biweekly", "15": "Semi-monthly"}
        self.paycheck_rows = [
            {
                "id":         p.get("id", ""),
                "label":      p.get("label", ""),
                "amount_fmt": _fmt(float(p.get("amount") or 0)),
                "freq_label": FREQ_LABELS.get(str(p.get("freq", 14)), f"Every {p.get('freq', 14)}d"),
                "anchor":     p.get("anchor_date") or "",
            }
            for p in (data.get("paychecks") or [])
        ]

        # ── Allocation rule rows ───────────────────────────────────────────
        self.alloc_rule_rows = [
            {
                "id":          r.get("id", ""),
                "name":        r.get("name", ""),
                "rule_type":   r.get("rule_type", "internal"),
                "value_type":  r.get("value_type", "fixed"),
                "value_str":   (f"{r.get('value', 0)}%"
                                if r.get("value_type") == "pct"
                                else _fmt(float(r.get("value") or 0))),
                "bucket_id":   r.get("bucket_id") or "",
                "bucket_name": bucket_map.get(r.get("bucket_id") or "", ""),
                "active_str":  "1" if r.get("active", True) else "",
            }
            for r in (data.get("allocationRules") or [])
        ]

        # ── Forecast ───────────────────────────────────────────────────────
        self._refresh_forecast_accounts()
        self._run_forecast()
