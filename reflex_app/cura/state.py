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
    if budget > 0 and alloc > budget * 1.05: return "OVERFUNDED"
    if budget > 0 and alloc >= budget:
        return "PAID" if spent >= alloc else "FUNDED"
    if budget == 0 and alloc > 0 and spent >= alloc: return "PAID"
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

# Uniform shape for ledger "blocks" (section headers + per-day cards) so that
# rx.foreach / rx.match can access any key on any block without KeyErrors.
_BLOCK_DEFAULTS: dict = {
    "kind": "", "label": "", "meta": "",
    "balance_label": "", "balance_color": "",
    "date_label": "", "rb_label": "", "rb_color": "", "is_sched": "",
    "txs": [],
}


def _date_label(date_str: str) -> str:
    try:
        # Tolerate full timestamps ("2026-05-15T00:00:00+00:00") by taking the day.
        d = date.fromisoformat((date_str or "")[:10])
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

def _flatten_timeline(rows: list[dict]) -> list[dict]:
    """
    Pass-through for compute_simple_timeline() which already returns flat rows.
    Ensures all required keys exist with string values.
    """
    blank = {"rt": "", "lbl": "", "amt": "", "td": "", "pa": "", "pd": ""}
    out = []
    for r in rows:
        row = dict(blank)
        row.update({k: str(v) for k, v in r.items()})
        out.append(row)
    return out


def _build_forecast_periods(periods: list[dict], open_pids: set = None) -> list[dict]:
    """Convert compute_forecast() period list → list of per-period card dicts.

    Each dict has header fields (pid, lbl, sub, amt, …) + is_open flag +
    rows: list[dict] of body rows.

    Body row types (rt field):
      sb  – start balance
      inc – income line
      xfr – transfer line (cum=cumulative total)
      ae  – alloc event (sub2="vault" amber / sub2="info" grey)
      bat – balance after transfers divider
      sbh – section header (funded / unfunded)
      fdt – funded date label
      fbl – funded bill
      fba – funded running balance
      udt – unfunded date label
      ubl – unfunded bill
      uba – unfunded running balance
      pf  – period footer (end bal + safe-to-spend)

    open_pids: set of period IDs that are expanded; None = all expanded.
    All dict values are str. Boolean flags encoded as "1" or "".
    """
    _ROW_BLANK = {
        "rt": "", "lbl": "", "sub2": "", "amt": "", "cum": "",
        "c1": "", "neg": "", "shf": "", "ebf": "", "ebn": "",
    }

    def _r(**kw) -> dict:
        row = dict(_ROW_BLANK)
        row.update({k: str(v) for k, v in kw.items()})
        return row

    result: list[dict] = []

    for p in periods:
        pid     = p["id"]
        is_open = (open_pids is None) or (pid in open_pids)

        body_rows: list[dict] = []

        # Start balance
        body_rows.append(_r(rt="sb", lbl=p["start_bal_fmt"]))

        # Income lines
        for ln in p.get("income_lines", []):
            body_rows.append(_r(rt="inc", lbl=ln["label"], amt=ln["amount_fmt"]))

        # Transfer lines (with cumulative totals)
        for ln in p.get("transfer_lines", []):
            body_rows.append(_r(rt="xfr", lbl=ln["label"],
                                amt=ln["amount_fmt"], cum=ln.get("cum_fmt", "")))

        # Alloc events (vault deducts + informational allocs)
        for ae in p.get("alloc_events", []):
            body_rows.append(_r(rt="ae", lbl=ae["name"],
                                amt=_fmt(ae["amount"]), sub2=ae["ae_type"]))

        # Balance after transfers
        if p.get("has_income") or p.get("has_transfers") or p.get("has_alloc_events"):
            body_rows.append(_r(rt="bat", lbl=p["bal_after_xfr_fmt"]))

        # Funded section
        if p.get("has_funded"):
            body_rows.append(_r(rt="sbh", lbl="Pre-Funded", c1="#34d399"))
            for ln in p["funded_lines"]:
                rt = {"date": "fdt", "bill": "fbl", "bal": "fba"}.get(ln["row_type"], "fbl")
                body_rows.append(_r(rt=rt, lbl=ln["text"], amt=ln["amount_fmt"]))

        # Unfunded section
        if p.get("has_unfunded"):
            body_rows.append(_r(rt="sbh", lbl="Needs Funding", c1="#f87171"))
            for ln in p["unfunded_lines"]:
                rt  = {"date": "udt", "bill": "ubl", "bal": "uba"}.get(ln["row_type"], "ubl")
                neg = "1" if ln["text"].startswith("-") else ""
                body_rows.append(_r(rt=rt, lbl=ln["text"], amt=ln["amount_fmt"], neg=neg))

        # Period footer
        body_rows.append(_r(
            rt="pf",
            amt=p["safe_to_spend_fmt"],
            c1=p["sts_color"],
            shf="1" if p["shortfall"] else "",
            ebf=p["end_bal_fmt"],
            ebn="1" if p["end_bal_negative"] else "",
        ))

        result.append({
            "pid":     pid,
            "lbl":     p["label"],
            "sub":     p["date_range"],
            "amt":     p["net_fmt"],
            "c1":      "#34d399" if not p["net_negative"] else "#f87171",
            "c2":      p["sts_color"],
            "neg":     "1" if p["net_negative"] else "",
            "shf":     "1" if p["shortfall"] else "",
            "pt":      p["type"],
            "ebf":     p["end_bal_fmt"],
            "ebn":     "1" if p["end_bal_negative"] else "",
            "sgn":     p["net_sign"],
            "is_open": "1" if is_open else "",
            "pfc":     str(p.get("funded_count", 0)),
            "tbc":     str(p.get("total_count", 0)),
            "rows":    body_rows,
        })

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  AppState
# ─────────────────────────────────────────────────────────────────────────────

class AppState(rx.State):

    # ── Auth ─────────────────────────────────────────────────────────────────
    # Stored as cookies so sessions survive page refresh / new tabs.
    access_token: str = rx.Cookie(name="cura_at",  secure=True, max_age=86400 * 7, same_site="strict")
    user_id:      str = rx.Cookie(name="cura_uid", secure=True, max_age=86400 * 7, same_site="strict")
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
    ledger_rows:     list[dict[str, Any]] = []
    ledger_tx_count: int                  = 0   # tx rows only; excludes month_totals header

    # ── KPIs ─────────────────────────────────────────────────────────────────
    rts:          float = 0.0
    income_total: float = 0.0
    spent_total:  float = 0.0
    total_alloc_val: float = 0.0

    # ── Accounts panel ───────────────────────────────────────────────────────
    accounts_rows: list[dict[str, Any]] = []   # for accounts panel
    total_cash:    float = 0.0
    total_debt:    float = 0.0
    acct_expanded_id:  str = ""
    acct_ledger_rows:  list[dict[str, Any]] = []

    # Account settings drawer
    acct_settings_open:    bool = False
    acct_settings_aid:     str  = ""
    acct_settings_name:    str  = ""
    acct_settings_type:    str  = "budget"
    acct_settings_color:   str  = "#3a7fc1"
    acct_settings_opening: str  = "0"
    acct_settings_apr:     str  = ""
    acct_settings_min_pay: str  = ""
    acct_settings_credit:  str  = ""
    acct_settings_is_promo: bool = False
    acct_settings_promo_end: str = ""
    acct_settings_saving:  bool = False
    acct_settings_error:   str  = ""

    # Add account
    add_acct_open:    bool = False
    add_acct_name:    str  = ""
    add_acct_type:    str  = "budget"
    add_acct_color:   str  = "#3a7fc1"
    add_acct_opening: str  = "0"
    add_acct_saving:  bool = False
    add_acct_error:   str  = ""

    # Debt payment
    debt_pay_open:         bool = False
    debt_pay_aid:          str  = ""
    debt_pay_acct_name:    str  = ""
    debt_pay_amount:       str  = ""
    debt_pay_date:         str  = ""
    debt_pay_from_account: str  = ""
    debt_pay_bucket:       str  = ""
    debt_pay_saving:       bool = False
    debt_pay_error:        str  = ""

    # ── Category management ───────────────────────────────────────────────────
    cat_rows:          list[dict[str, Any]] = []   # [{id, name, color, order, bucket_count}]
    archived_cat_rows: list[dict[str, Any]] = []   # same shape, archived only
    cat_edit_id:    str  = ""
    cat_edit_name:  str  = ""
    cat_edit_color: str  = ""
    cat_saving:     bool = False

    # ── Month workflow ────────────────────────────────────────────────────────
    copy_allocs_saving:  bool = False
    close_month_saving:  bool = False

    # ── Payee autocomplete ────────────────────────────────────────────────────
    payee_options: list[str] = []

    # ── Form selects ──────────────────────────────────────────────────────────
    expense_buckets: list[dict[str, Any]] = []   # [{id, name}]
    account_options: list[dict[str, Any]] = []   # [{id, name}]

    # ── Reports panel ────────────────────────────────────────────────────────
    reports_tab:       str = "snapshot"  # "snapshot" | "bva" | "summary" | "trends" | "payees" | "debt"
    bva_rows:          list[dict[str, Any]] = []   # flat: row_type "cat"|"bucket", m0/m1/m2 cols
    bva_month_hdrs:    list[dict[str, Any]] = []   # [{label, mid}] × 3 (some may be empty)
    summary_cards:     list[dict] = []             # [{label, income_fmt, spent_fmt, net_fmt, net_positive, savings_rate, cat_rows:[...]}]
    trend_svg:         str = ""
    trend_rows:        list[dict[str, Any]] = []   # [{label, income_fmt, spent_fmt, net_fmt, net_positive, savings_rate}]
    payee_spend_rows:  list[dict[str, Any]] = []   # [{payee, total_fmt, count, pct_str, bar_w, cat_name}]
    debt_tracker_rows: list[dict] = []             # [{name, color, balance_fmt, total_paid_fmt, payment_count, avg_payment_fmt, months:[{label,paid_fmt}]}]

    # ── UI state ─────────────────────────────────────────────────────────────
    active_panel:  str  = "buckets"
    is_loading:    bool = False
    panel_error:   str  = ""
    _polling:      bool = False  # background poll running
    _busy:         bool = False  # a mutating write is in flight (poll backs off)

    # Inline budget editing
    editing_budget_bid: str = ""
    edit_budget_val:    str = ""

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
    ledger_acct_filter: str = ""           # "" = All; acct_id = single account view
    acct_balance_map: dict[str, float] = {}  # acct_id → real current balance (anchors running bal)

    # ── Category select options ───────────────────────────────────────────────
    cat_options: list[dict[str, Any]] = []

    # ── Scoreboard: needs-attention + category rollup ─────────────────────────
    attention_rows:  list[dict[str, Any]] = []
    cat_rollup_rows: list[dict[str, Any]] = []

    # ── Ledger scoreboard ─────────────────────────────────────────────────────
    last_month_income:   float             = 0.0
    last_month_spent:    float             = 0.0
    mom_verdict:         str               = ""
    mom_better:          bool              = False
    ledger_bucket_spend: list[dict[str, Any]] = []

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
    paycheck_rows:    list[dict[str, Any]] = []
    setup_pc_label:   str  = ""
    setup_pc_amount:  str  = ""
    setup_pc_freq:    str  = "14"    # 7 | 14 | 15
    setup_pc_anchor:  str  = ""
    setup_pc_saving:  bool = False
    setup_pc_error:   str  = ""
    # Edit-paycheck form
    edit_pc_open:     bool = False
    edit_pc_id:       str  = ""
    edit_pc_label:    str  = ""
    edit_pc_amount:   str  = ""
    edit_pc_freq:     str  = "14"
    edit_pc_anchor:   str  = ""
    edit_pc_saving:   bool = False
    edit_pc_error:    str  = ""

    # ── Setup panel — categories ──────────────────────────────────────
    show_archived_cats: bool = False

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
    edit_tx_reconciled:       bool = False
    _edit_tx_was_reconciled:  bool = False   # snapshot at open time
    edit_tx_saving:           bool = False
    edit_tx_error:            str  = ""

    # ── Reconciliation ───────────────────────────────────────────────────────
    recon_open:               bool        = False
    recon_account_id:         str         = ""
    recon_statement_balance:  str         = ""
    recon_unchecked_ids:      list[str]   = []   # explicitly unchecked tx IDs (rest = checked)
    recon_saving:             bool        = False
    recon_error:              str         = ""

    # ── Payday modal ──────────────────────────────────────────────────
    payday_open:       bool = False
    payday_amount_fmt: str  = ""
    payday_rows:       list[dict[str, Any]] = []
    payday_saving:     bool = False

    # ── Forecast ──────────────────────────────────────────────────────────────
    forecast_range:    int              = 3
    forecast_account:  str              = ""
    forecast_periods:  list[dict]       = []   # per-period card dicts (nested rows)
    forecast_accounts: list[dict]       = []   # [{id,name,color,balance_fmt}]
    forecast_loading:  bool             = False
    fc_start_bal:      str              = "—"
    fc_total_income:   str              = "—"
    fc_total_unfunded: str              = "—"
    fc_safe_to_spend:  str              = "—"
    fc_sts_color:      str              = "#818cf8"
    fc_shortfall_count: int             = 0
    fc_open_pids:       list[str]       = []   # open (expanded) period IDs

    # ── Insights sub-tab ──────────────────────────────────────────────────────
    insights_tab: str = "forecast"   # "forecast" | "timeline" | "whatif"

    # ── Timeline ──────────────────────────────────────────────────────────────
    tl_rows:         list[dict] = []   # flat 60-day event feed

    # ── What-If ───────────────────────────────────────────────────────────────
    wi_income_str:        str        = ""    # monthly income override input
    wi_bucket_overrides:  dict       = {}    # bid -> expr string ("+50", "200", etc.)
    wi_rule_overrides:    dict       = {}    # rule_id -> value string
    wi_off_buckets:       list[str]  = []    # bucket IDs turned off in what-if
    wi_schedule:          dict       = {}    # f"{bid}_{mid}" -> "off" (default "on")
    wi_due_day_overrides: dict       = {}    # bid -> int day override
    wi_periods:           list[dict] = []    # per-period card dicts for what-if result
    wi_start_bal:         str        = "—"
    wi_total_income:      str        = "—"
    wi_total_unfunded:    str        = "—"
    wi_safe_to_spend:     str        = "—"
    wi_sts_color:         str        = "#818cf8"
    wi_shortfall_count:   int        = 0
    wi_active:            bool       = False
    wi_bucket_rows:       list[dict] = []    # category-grouped bucket editor rows
    wi_rules_rows:        list[dict] = []    # rules editor rows
    wi_chart_svg:         str        = ""    # pre-computed 6-month SVG bar chart
    wi_scenarios:         list[dict] = []    # [{id, name, allocs}] loaded from DB
    wi_active_scenario_id: str       = ""
    wi_scenario_name:     str        = ""

    # ── Forecast scenario overlay ─────────────────────────────────────────────
    fc_active_scenario_id:   str  = ""
    fc_active_scenario_name: str  = ""

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
    def total_cash_fmt(self) -> str:
        return _fmt(self.total_cash)

    @rx.var
    def total_debt_fmt(self) -> str:
        return _fmt(self.total_debt)

    @rx.var
    def last_month_income_fmt(self) -> str:
        return _fmt(self.last_month_income)

    @rx.var
    def last_month_spent_fmt(self) -> str:
        return _fmt(self.last_month_spent)

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

    # ── Reconciliation computed vars ─────────────────────────────────────────

    @rx.var
    def recon_account_name(self) -> str:
        for a in self.accounts_rows:
            if a.get("id") == self.recon_account_id:
                return a.get("name", "")
        return ""

    @rx.var
    def recon_txs(self) -> list[dict[str, Any]]:
        """All unreconciled, non-scheduled transactions for the reconcile account,
        newest-first.  These are pre-checked (shown in the modal as cleared)."""
        acct = self.recon_account_id
        if not acct:
            return []
        out = []
        for row in self.ledger_rows:
            if row.get("row_type") != "tx":
                continue
            if row.get("acct_id", "") != acct and row.get("to_acct_id", "") != acct:
                continue
            if row.get("scheduled", False):
                continue
            if row.get("reconciled", False):
                continue
            out.append(dict(row))
        return out  # ledger_rows is already newest-first

    @rx.var
    def recon_cleared_balance(self) -> float:
        """cleared_balance = real account balance minus the signed effect of
        every unchecked transaction.  Anchoring to the real balance automatically
        includes the opening balance, so the math is correct regardless of how
        many prior reconciliations have been done."""
        acct = self.recon_account_id
        if not acct:
            return 0.0
        current = self.acct_balance_map.get(acct, 0.0)
        unchecked = set(self.recon_unchecked_ids)
        uncleared_effect = 0.0
        for row in self.recon_txs:
            tx_id = str(row.get("id", ""))
            if tx_id not in unchecked:   # checked → already in current balance, keep it
                continue
            # This tx is unchecked (hasn't posted) — subtract its effect
            t = row.get("type", "")
            a = float(row.get("amount") or 0)
            if row.get("acct_id") == acct:
                if t == "in":            uncleared_effect += a
                elif t in ("out","xfr"): uncleared_effect -= a
            elif t == "xfr" and row.get("to_acct_id") == acct:
                uncleared_effect += a
        return current - uncleared_effect

    @rx.var
    def recon_difference(self) -> float:
        try:
            stmt = float(self.recon_statement_balance.replace("$","").replace(",","") or "0")
        except ValueError:
            return 0.0
        return round(stmt - self.recon_cleared_balance, 2)

    @rx.var
    def recon_difference_fmt(self) -> str:
        d = self.recon_difference
        return f"${abs(d):,.2f}" if d >= 0 else f"-${abs(d):,.2f}"

    @rx.var
    def recon_cleared_fmt(self) -> str:
        b = self.recon_cleared_balance
        return f"${b:,.2f}" if b >= 0 else f"-${abs(b):,.2f}"

    @rx.var
    def recon_can_finish(self) -> bool:
        if not self.recon_statement_balance:
            return False
        return abs(self.recon_difference) < 0.015   # ±1 cent tolerance

    @rx.var
    def ledger_view(self) -> dict[str, Any]:
        """Bank-statement view: Scheduled + Current Statement sections, each
        grouped into per-day cards with a running balance, plus KPI totals.
        Reacts to ledger_acct_filter and ledger_query."""
        acct = self.ledger_acct_filter
        q = self.ledger_query.lower() if self.ledger_query else ""
        show_rb = bool(acct)   # running balance only meaningful for one account

        # ── 1. Split filtered tx rows into posted vs scheduled + KPI sums ──
        posted: list[dict] = []
        scheduled: list[dict] = []
        inc = sched_total = spent = xfer = 0.0
        for row in self.ledger_rows:
            if row.get("row_type") != "tx":
                continue
            if acct and row.get("acct_id", "") != acct and row.get("to_acct_id", "") != acct:
                continue
            if q and q not in row.get("desc", "").lower() and q not in row.get("bucket", "").lower():
                continue
            amt   = float(row.get("amount") or 0)
            ttype = row.get("type", "")
            if row.get("scheduled", False):
                scheduled.append(dict(row))
                sched_total += amt
            else:
                posted.append(dict(row))
                if   ttype == "in":  inc   += amt
                elif ttype == "out": spent += amt
                elif ttype == "xfr": xfer  += amt

        # ── 2. Running balance, anchored to the account's real balance ────
        # Day key = calendar day (strip any time component); "" = undated.
        def _day_key(d: str) -> str:
            return (d or "")[:10]

        def _effect(r: dict) -> float:
            """Signed change this tx made to the selected account's balance."""
            t = r.get("type", "")
            a = float(r.get("amount") or 0)
            if r.get("acct_id") == acct:
                if t == "in":            return a
                if t in ("out", "xfr"):  return -a
            elif t == "xfr" and r.get("to_acct_id") == acct:
                return a
            return 0.0

        current_bal = self.acct_balance_map.get(acct, 0.0) if acct else 0.0

        # Posted: walk newest→oldest from the real current balance so each
        # day's RB is the true end-of-day balance and the latest = account total.
        day_bal: dict[str, float] = {}
        if show_rb:
            running = current_bal
            for r in posted:  # already newest-first
                dk = _day_key(r.get("date", ""))
                if dk not in day_bal:
                    day_bal[dk] = running        # end-of-day balance
                running -= _effect(r)            # step back before this tx

        # Scheduled: project forward from the real current balance.
        sday_bal: dict[str, float] = {}
        if show_rb:
            pbal = current_bal
            for r in sorted(scheduled, key=lambda r: (_day_key(r.get("date", "")), r.get("id", ""))):
                pbal += _effect(r)
                sday_bal[_day_key(r.get("date", ""))] = pbal

        latest_posted_bal = current_bal

        # ── 3. Build per-day cards (newest-first; ledger_rows already is) ──
        def _plural(n: int, word: str) -> str:
            return f"{n} {word}" + ("s" if n != 1 else "")

        def _days(rows: list[dict], balmap: dict, is_sched: bool) -> list[dict]:
            order: list[str] = []
            buckets: dict[str, list[dict]] = {}
            for r in rows:
                dk = _day_key(r.get("date", ""))
                if dk not in buckets:
                    buckets[dk] = []
                    order.append(dk)
                buckets[dk].append(r)
            # Undated group (if any) sorts to the end.
            order.sort(key=lambda dk: (dk == "", ))
            out: list[dict] = []
            for dk in order:
                txs = buckets[dk]
                rb = balmap.get(dk, 0.0)
                # Undated rows still belong to the active month — label them
                # with the month rather than a vague "Undated".
                out.append({
                    **_BLOCK_DEFAULTS,
                    "kind":       "day",
                    "date_label": _date_label(dk) if dk else (self.month_display or "Undated"),
                    "meta":       _plural(len(txs), "transaction"),
                    "rb_label":   (("PRB " if is_sched else "RB ") + _fmt(rb)) if (show_rb and dk) else "",
                    "rb_color":   "#34d399" if rb >= 0 else "#f87171",
                    "is_sched":   "1" if is_sched else "",
                    "txs":        txs,
                })
            return out

        blocks: list[dict] = []
        if scheduled:
            blocks.append({
                **_BLOCK_DEFAULTS,
                "kind":  "section",
                "label": "Scheduled",
                "meta":  f"{len(scheduled)} pending",
            })
            blocks.extend(_days(scheduled, sday_bal, True))
        if posted:
            blocks.append({
                **_BLOCK_DEFAULTS,
                "kind":          "section",
                "label":         "Current Statement",
                "meta":          _plural(len(posted), "transaction"),
                "balance_label": (f"Balance {_fmt(latest_posted_bal)}") if show_rb else "",
                "balance_color": "#34d399" if latest_posted_bal >= 0 else "#f87171",
            })
            blocks.extend(_days(posted, day_bal, False))

        return {
            "blocks":          blocks,
            "income_fmt":      _fmt(inc),
            "scheduled_fmt":   _fmt(sched_total),
            "spent_fmt":       _fmt(spent),
            "transferred_fmt": _fmt(xfer),
            "has_scheduled":   "1" if scheduled else "",
            "empty":           "1" if not blocks else "",
        }

    @rx.var
    def forecast_shortfall_label(self) -> str:
        n = self.fc_shortfall_count
        return f"⚠ {n} period{'s' if n != 1 else ''} with negative balance"

    # ─────────────────────────────────────────────────────────────────────────
    #  Forecast events
    # ─────────────────────────────────────────────────────────────────────────

    def _run_forecast(self, preserve_open: bool = False):
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

        if not preserve_open:
            # Auto-open: first period + any shortfall periods
            auto_pids: list[str] = []
            periods = result["periods"]
            if periods:
                auto_pids.append(periods[0]["id"])
            for p in periods:
                if p["shortfall"] and p["id"] not in auto_pids:
                    auto_pids.append(p["id"])
            self.fc_open_pids = auto_pids

        self.forecast_periods = _build_forecast_periods(result["periods"], set(self.fc_open_pids))

    def set_forecast_range(self, n: int):
        self.forecast_range = n
        self._run_forecast()

    def set_forecast_account(self, aid: str):
        self.forecast_account = aid
        self._run_forecast()

    def toggle_period_collapse(self, pid: str):
        pids = list(self.fc_open_pids)
        if pid in pids:
            pids.remove(pid)
        else:
            pids.append(pid)
        self.fc_open_pids = pids
        self._run_forecast(preserve_open=True)

    # ── Insights sub-tab events ───────────────────────────────────────────────

    def set_insights_tab(self, tab: str):
        self.insights_tab = tab
        if tab == "timeline":
            self._run_timeline()
        elif tab == "whatif":
            self._build_wi_bucket_rows()
            self._build_wi_rules_rows()
            self._run_whatif()
            self._load_wi_scenarios()

    # ── Timeline events ───────────────────────────────────────────────────────

    def _run_timeline(self):
        from .forecast_calc import compute_simple_timeline
        if not self._raw:
            return
        rows      = compute_simple_timeline(self._raw, n_days=60)
        self.tl_rows = _flatten_timeline(rows)

    # ── What-If events ────────────────────────────────────────────────────────

    def set_wi_income(self, val: str):
        self.wi_income_str = val
        self._update_wi_active()
        self._run_whatif()
        self._build_wi_chart_svg()

    def set_wi_bucket_override(self, bid: str, val: str):
        overrides = dict(self.wi_bucket_overrides)
        if val.strip():
            overrides[bid] = val.strip()
        elif bid in overrides:
            del overrides[bid]
        self.wi_bucket_overrides = overrides
        self._update_wi_active()
        self._run_whatif()
        self._build_wi_bucket_rows()
        self._build_wi_chart_svg()

    def toggle_wi_bucket_off(self, bid: str):
        offs = list(self.wi_off_buckets)
        if bid in offs:
            offs.remove(bid)
        else:
            offs.append(bid)
        self.wi_off_buckets = offs
        self._update_wi_active()
        self._run_whatif()
        self._build_wi_bucket_rows()
        self._build_wi_chart_svg()

    def set_wi_rule_override(self, rule_id: str, val: str):
        overrides = dict(self.wi_rule_overrides)
        if val.strip():
            overrides[rule_id] = val.strip()
        elif rule_id in overrides:
            del overrides[rule_id]
        self.wi_rule_overrides = overrides
        self._update_wi_active()
        self._run_whatif()
        self._build_wi_rules_rows()
        self._build_wi_chart_svg()

    def reset_whatif(self):
        self.wi_income_str        = ""
        self.wi_bucket_overrides  = {}
        self.wi_rule_overrides    = {}
        self.wi_off_buckets       = []
        self.wi_schedule          = {}
        self.wi_due_day_overrides = {}
        self.wi_active            = False
        self.wi_active_scenario_id = ""
        self.wi_periods           = []
        self.wi_start_bal         = "—"
        self.wi_total_income      = "—"
        self.wi_total_unfunded    = "—"
        self.wi_safe_to_spend     = "—"
        self.wi_sts_color         = "#818cf8"
        self.wi_shortfall_count   = 0
        self.wi_chart_svg         = ""
        self._build_wi_bucket_rows()
        self._build_wi_rules_rows()

    def toggle_wi_month_schedule(self, key: str):
        """key = '{bid}_{mid}' — toggle on/off for that bucket+month."""
        sched = dict(self.wi_schedule)
        if sched.get(key, "on") == "off":
            del sched[key]
        else:
            sched[key] = "off"
        self.wi_schedule = sched
        self._update_wi_active()
        self._run_whatif()
        self._build_wi_bucket_rows()
        self._build_wi_chart_svg()

    def set_wi_due_day_override(self, bid: str, val: str):
        overrides = dict(self.wi_due_day_overrides)
        v = val.strip()
        if v and v.isdigit() and 1 <= int(v) <= 31:
            overrides[bid] = v
        elif bid in overrides:
            del overrides[bid]
        self.wi_due_day_overrides = overrides
        self._update_wi_active()
        self._run_whatif()
        self._build_wi_bucket_rows()
        self._build_wi_chart_svg()

    def apply_fc_scenario(self, sid: str):
        """Apply a saved What-If scenario to the Forecast tab."""
        try:
            rows = DB.list_scenarios(self.user_id, self.access_token)
            sc   = next((r for r in rows if r["id"] == sid), None)
            if not sc:
                return
            allocs = sc.get("allocations", {})
            self.fc_active_scenario_id   = sid
            self.fc_active_scenario_name = sc["name"]
            self._run_forecast_with_scenario(allocs)
        except Exception:
            pass

    def clear_fc_scenario(self):
        self.fc_active_scenario_id   = ""
        self.fc_active_scenario_name = ""
        self._run_forecast()

    def _run_forecast_with_scenario(self, allocs: dict):
        from .forecast_calc import compute_forecast
        if not self._raw:
            return
        income_ov = 0.0
        try:
            income_ov = float(allocs.get("_income", "").replace(",", "").replace("$", ""))
        except Exception:
            pass
        result = compute_forecast(
            self._raw, self.forecast_range, self.forecast_account,
            income_override=income_ov,
            bucket_overrides=allocs.get("_overrides", {}),
            rule_overrides=allocs.get("_rule_overrides", {}),
            off_buckets=allocs.get("_off_buckets", []),
            schedule=allocs.get("_schedule", {}),
            due_day_overrides={k: int(v) for k, v in allocs.get("_due_day_overrides", {}).items() if v},
        )
        self.fc_start_bal       = result["start_balance"]
        self.fc_total_income    = result["total_income"]
        self.fc_total_unfunded  = result["total_unfunded"]
        self.fc_safe_to_spend   = result["safe_to_spend"]
        self.fc_sts_color       = result["sts_color"]
        self.fc_shortfall_count = result["shortfall_count"]
        auto_pids = []
        periods = result["periods"]
        if periods:
            auto_pids.append(periods[0]["id"])
        for p in periods:
            if p["shortfall"] and p["id"] not in auto_pids:
                auto_pids.append(p["id"])
        self.fc_open_pids = auto_pids
        self.forecast_periods = _build_forecast_periods(result["periods"], set(self.fc_open_pids))

    def _update_wi_active(self):
        self.wi_active = bool(
            self.wi_income_str.strip() or
            self.wi_bucket_overrides or
            self.wi_rule_overrides or
            self.wi_off_buckets or
            self.wi_schedule or
            self.wi_due_day_overrides
        )

    def _run_whatif(self):
        from .forecast_calc import compute_forecast
        if not self._raw:
            return
        income_ov = 0.0
        try:
            income_ov = float(self.wi_income_str.replace(",", "").replace("$", ""))
        except Exception:
            pass
        result = compute_forecast(
            self._raw, self.forecast_range, self.forecast_account,
            income_override=income_ov,
            bucket_overrides=dict(self.wi_bucket_overrides),
            rule_overrides=dict(self.wi_rule_overrides),
            off_buckets=list(self.wi_off_buckets),
            schedule=dict(self.wi_schedule),
            due_day_overrides={k: int(v) for k, v in self.wi_due_day_overrides.items() if v},
        )
        self.wi_start_bal       = result["start_balance"]
        self.wi_total_income    = result["total_income"]
        self.wi_total_unfunded  = result["total_unfunded"]
        self.wi_safe_to_spend   = result["safe_to_spend"]
        self.wi_sts_color       = result["sts_color"]
        self.wi_shortfall_count = result["shortfall_count"]
        self.wi_periods         = _build_forecast_periods(result["periods"])

    def _build_wi_bucket_rows(self):
        """Build category-grouped bucket list for the What-If editor."""
        if not self._raw:
            return
        import calendar as _cal_mod
        from datetime import date as _date_cls
        from .forecast_calc import _apply_expr, _mid as _fc_mid
        raw       = self._raw
        cats      = sorted(raw.get("cats", []), key=lambda c: c.get("order", 0))
        buckets   = [b for b in raw.get("buckets", []) if not b.get("archived")]
        overrides = dict(self.wi_bucket_overrides)
        off_set   = set(self.wi_off_buckets)
        schedule  = dict(self.wi_schedule)
        due_ovs   = dict(self.wi_due_day_overrides)
        today     = _date_cls.today()

        # Compute 6 upcoming months: (mid_str, short_label)
        months_6: list[tuple[str, str]] = []
        for i in range(6):
            m_idx = (today.month - 1 + i) % 12
            yr    = today.year + (today.month - 1 + i) // 12
            d     = _date_cls(yr, m_idx + 1, 1)
            months_6.append((_fc_mid(d), d.strftime("%b")))

        rows: list[dict] = []
        for cat in cats:
            cid = cat["id"]
            cat_bkts = sorted(
                [b for b in buckets if b.get("catId") == cid
                 and (b.get("dueDay") is not None or b.get("payFreq") or float(b.get("defaultBudget") or 0) > 0)],
                key=lambda b: b.get("order", 0),
            )
            if not cat_bkts:
                continue
            rows.append({
                "rt": "cat", "id": cid, "name": cat.get("name", ""),
                "color": cat.get("color", "#818cf8"),
                "is_off": "", "bid": "", "base_fmt": "", "override_val": "",
                "eff_fmt": "", "due_info": "", "due_day_override": "",
                "mi0": "", "mi1": "", "mi2": "", "mi3": "", "mi4": "", "mi5": "",
                "ml0": "", "ml1": "", "ml2": "", "ml3": "", "ml4": "", "ml5": "",
                "ms0": "", "ms1": "", "ms2": "", "ms3": "", "ms4": "", "ms5": "",
            })
            for b in cat_bkts:
                bid   = b["id"]
                base  = float(b.get("dueAmount") or b.get("defaultBudget") or 0)
                expr  = overrides.get(bid, "")
                eff   = _apply_expr(base, expr) if expr else base
                is_off = "1" if bid in off_set else ""
                due_info = ""
                if b.get("dueDay"):
                    due_info = f"due {b['dueDay']}"
                elif b.get("payFreq"):
                    due_info = b["payFreq"]
                # Month schedule pills
                mi = [months_6[i][0] for i in range(6)]  # mid strings
                ml = [months_6[i][1] for i in range(6)]  # labels
                ms = [schedule.get(f"{bid}_{mi[i]}", "on") for i in range(6)]  # on/off
                rows.append({
                    "rt":              "bkt",
                    "id":              bid,
                    "bid":             bid,
                    "name":            b.get("name", ""),
                    "color":           cat.get("color", "#818cf8"),
                    "base_fmt":        _fmt(base),
                    "override_val":    expr,
                    "eff_fmt":         _fmt(eff),
                    "is_off":          is_off,
                    "due_info":        due_info,
                    "due_day_override": due_ovs.get(bid, ""),
                    "mi0": f"{bid}_{mi[0]}", "mi1": f"{bid}_{mi[1]}",
                    "mi2": f"{bid}_{mi[2]}", "mi3": f"{bid}_{mi[3]}",
                    "mi4": f"{bid}_{mi[4]}", "mi5": f"{bid}_{mi[5]}",
                    "ml0": ml[0], "ml1": ml[1], "ml2": ml[2],
                    "ml3": ml[3], "ml4": ml[4], "ml5": ml[5],
                    "ms0": ms[0], "ms1": ms[1], "ms2": ms[2],
                    "ms3": ms[3], "ms4": ms[4], "ms5": ms[5],
                })
        self.wi_bucket_rows = rows

    def _build_wi_rules_rows(self):
        """Build rules editor rows for What-If."""
        if not self._raw:
            return
        rules     = self._raw.get("allocationRules", [])
        overrides = dict(self.wi_rule_overrides)
        rows: list[dict] = []
        for r in rules:
            if not r.get("active", True):
                continue
            rid      = r.get("id", "")
            base_val = float(r.get("value") or 0)
            val_type = r.get("value_type") or r.get("type", "fixed")
            base_str = f"{base_val}%" if val_type == "pct" else _fmt(base_val)
            override = overrides.get(rid, "")
            rows.append({
                "id":           rid,
                "name":         r.get("name", ""),
                "rule_type":    r.get("rule_type") or r.get("ruleType", "internal"),
                "base_str":     base_str,
                "override_val": override,
                "val_type":     val_type,
            })
        self.wi_rules_rows = rows

    def _build_wi_chart_svg(self):
        """Build a 6-month SVG bar chart for the What-If panel."""
        from .forecast_calc import compute_6month
        if not self._raw:
            self.wi_chart_svg = ""
            return
        income_ov = 0.0
        try:
            income_ov = float(self.wi_income_str.replace(",", "").replace("$", ""))
        except Exception:
            pass
        months = compute_6month(
            self._raw,
            bucket_overrides=dict(self.wi_bucket_overrides),
            rule_overrides=dict(self.wi_rule_overrides),
            off_buckets=list(self.wi_off_buckets),
            income_override=income_ov,
            schedule=dict(self.wi_schedule),
            due_day_overrides={k: int(v) for k, v in self.wi_due_day_overrides.items() if v},
        )
        if not months:
            self.wi_chart_svg = ""
            return

        W, H = 420, 140
        bar_area_h = 90
        bar_w = 44
        gap = (W - len(months) * bar_w) // (len(months) + 1)
        max_v = max(max(m["income"], m["bills"]) for m in months) or 1.0

        def _scale(v: float) -> float:
            return max(2, round(abs(v) / max_v * bar_area_h))

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'style="font-family:monospace;overflow:visible">'
        ]

        for i, m in enumerate(months):
            x = gap + i * (bar_w + gap)
            ih = _scale(m["income"])
            bh = _scale(m["bills"])

            # Income bar (accent blue)
            parts.append(
                f'<rect x="{x}" y="{bar_area_h - ih + 4}" width="{bar_w // 2 - 2}" height="{ih}" '
                f'rx="3" fill="#818cf8" opacity="0.85"/>'
            )
            # Bills bar (amber if surplus else red)
            bill_color = "#fbbf24" if m["surplus_positive"] else "#f87171"
            parts.append(
                f'<rect x="{x + bar_w // 2 + 2}" y="{bar_area_h - bh + 4}" '
                f'width="{bar_w // 2 - 2}" height="{bh}" '
                f'rx="3" fill="{bill_color}" opacity="0.85"/>'
            )
            # Month label
            parts.append(
                f'<text x="{x + bar_w // 2}" y="{bar_area_h + 18}" '
                f'text-anchor="middle" font-size="10" fill="#818cf8">{m["label"]}</text>'
            )
            # Surplus/shortfall indicator
            s_color = "#34d399" if m["surplus_positive"] else "#f87171"
            s_sign  = "+" if m["surplus_positive"] else ""
            s_val   = m["surplus"]
            s_abs   = abs(s_val)
            s_str   = f"{s_sign}${s_abs:,.0f}" if s_abs >= 100 else f"{s_sign}${s_abs:.0f}"
            parts.append(
                f'<text x="{x + bar_w // 2}" y="{bar_area_h + 32}" '
                f'text-anchor="middle" font-size="8" fill="{s_color}">{s_str}</text>'
            )

        # Legend
        parts.append(
            f'<rect x="8" y="{H - 16}" width="10" height="8" rx="2" fill="#818cf8" opacity="0.85"/>'
            f'<text x="22" y="{H - 9}" font-size="9" fill="#9090b0">Income</text>'
            f'<rect x="70" y="{H - 16}" width="10" height="8" rx="2" fill="#fbbf24" opacity="0.85"/>'
            f'<text x="84" y="{H - 9}" font-size="9" fill="#9090b0">Bills</text>'
        )
        parts.append("</svg>")
        self.wi_chart_svg = "".join(parts)

    def _load_wi_scenarios(self):
        """Load scenarios from DB into wi_scenarios."""
        if not self.user_id:
            return
        try:
            rows = DB.list_scenarios(self.user_id, self.access_token)
            self.wi_scenarios = [{"id": r["id"], "name": r["name"], "allocs": r.get("allocations", {})} for r in rows]
        except Exception:
            self.wi_scenarios = []

    def set_wi_scenario_name(self, val: str):
        self.wi_scenario_name = val

    async def save_wi_scenario(self):
        name = self.wi_scenario_name.strip() or "Untitled"
        allocs = {
            "_overrides":          dict(self.wi_bucket_overrides),
            "_rule_overrides":     dict(self.wi_rule_overrides),
            "_off_buckets":        list(self.wi_off_buckets),
            "_income":             self.wi_income_str,
            "_schedule":           dict(self.wi_schedule),
            "_due_day_overrides":  dict(self.wi_due_day_overrides),
        }
        try:
            if self.wi_active_scenario_id:
                DB.update_scenario(self.user_id, self.access_token,
                                   self.wi_active_scenario_id, name, allocs)
            else:
                sid = DB.save_scenario(self.user_id, self.access_token, name, allocs)
                self.wi_active_scenario_id = sid
            self._load_wi_scenarios()
            self.wi_scenario_name = ""
            yield rx.toast.success("Scenario saved")
        except Exception as e:
            yield rx.toast.error(f"Save failed: {e}")

    def load_wi_scenario(self, sid: str):
        try:
            rows = DB.list_scenarios(self.user_id, self.access_token)
            sc   = next((r for r in rows if r["id"] == sid), None)
            if not sc:
                return
            allocs = sc.get("allocations", {})
            self.wi_bucket_overrides   = allocs.get("_overrides", {})
            self.wi_rule_overrides     = allocs.get("_rule_overrides", {})
            self.wi_off_buckets        = allocs.get("_off_buckets", [])
            self.wi_income_str         = allocs.get("_income", "")
            self.wi_schedule           = allocs.get("_schedule", {})
            self.wi_due_day_overrides  = allocs.get("_due_day_overrides", {})
            self.wi_active_scenario_id = sid
            self.wi_scenario_name      = sc["name"]
            self._update_wi_active()
            self._run_whatif()
            self._build_wi_bucket_rows()
            self._build_wi_rules_rows()
            self._build_wi_chart_svg()
        except Exception:
            pass

    async def delete_wi_scenario(self, sid: str):
        try:
            DB.delete_scenario(self.user_id, self.access_token, sid)
            self._load_wi_scenarios()
            if self.wi_active_scenario_id == sid:
                self.wi_active_scenario_id = ""
            yield rx.toast.success("Scenario deleted")
        except Exception as e:
            yield rx.toast.error(f"Delete failed: {e}")

    def _refresh_forecast_accounts(self):
        from .formulas import acct_balance
        raw = self._raw
        if not raw:
            return
        accounts = raw.get("accounts", [])
        txs      = raw.get("txs", [])
        self.forecast_accounts = [
            {"id": a["id"], "name": a["name"],
             "color": a.get("color", "#818cf8"),
             "balance_fmt": _fmt(acct_balance(a, txs))}
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
        except Exception as e:
            msg = str(e).lower()
            if any(k in msg for k in ("invalid", "credentials", "password", "email", "not found", "no user")):
                self.auth_error = "Invalid email or password."
            else:
                self.auth_error = "Could not connect — please try again."
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

    # ── Shared write/error plumbing ───────────────────────────────────────────
    def _interaction_open(self) -> bool:
        """True when the user has an inline edit or modal open — the poll must
        not reload underneath them or their in-progress input is lost."""
        return bool(
            self.editing_bid or self.editing_budget_bid or self.cat_edit_id
            or self.sheet_open or self.bsettings_open or self.rule_sheet_open
            or self.edit_tx_open or self.payday_open or self.acct_settings_open
            or self.add_acct_open or self.debt_pay_open
        )

    def _on_db_error(self, e: Exception):
        """Standard recovery for a failed DB write. Performs the side-effect
        (logout-redirect or reload-from-truth) and returns the rx event the
        caller should yield. Centralises auth handling so every handler agrees."""
        if DB.is_auth_error(e):
            self.access_token = ""
            return rx.redirect("/login")
        try:
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
        except Exception:
            pass
        return rx.toast.error("Couldn't save — reloaded the latest data")

    def _reload(self):
        """Refetch from the DB and reprocess for the active month."""
        data = DB.load_all(self.user_id, self.access_token)
        self._raw = data
        self._process(data, self.active_mid)

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
        """Refresh data from the DB on an interval — but never clobber work in
        progress. Skips the reload while a write is in flight (`_busy`) or the
        user has an edit/modal open (`_interaction_open`)."""
        while True:
            await asyncio.sleep(30)
            async with self:
                if not self.is_logged_in:
                    self._polling = False
                    return
                # Back off: a mutation is mid-flight or the user is editing.
                if self._busy or self._interaction_open():
                    continue
                try:
                    data = DB.load_all(self.user_id, self.access_token)
                    self._raw = data
                    self._process(data, self.active_mid)
                except Exception as e:
                    # Auth death must surface, not vanish.
                    if DB.is_auth_error(e):
                        self.access_token = ""
                        self._polling = False
                        return

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
            if self.active_panel == "insights":
                if self.insights_tab == "timeline":
                    self._run_timeline()
                elif self.insights_tab == "whatif":
                    self._run_whatif()
                    self._build_wi_chart_svg()

    # ─────────────────────────────────────────────────────────────────────────
    #  Panel navigation
    # ─────────────────────────────────────────────────────────────────────────

    def set_panel(self, name: str):
        self.active_panel = name
        if name == "reports" and self._raw:
            self._build_reports()

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
        self.load_payees()

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
        if self.sheet_type == "xfr":
            if not self.sheet_to_account:
                self.sheet_error = "Select a destination account."
                return
            if self.sheet_to_account == self.sheet_account:
                self.sheet_error = "Source and destination accounts must differ."
                return

        self.sheet_saving = True
        self._busy = True
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
            if DB.is_auth_error(e):
                self.access_token = ""
                yield rx.redirect("/login")
            else:
                self.sheet_error = f"Failed: {e}"
        finally:
            self.sheet_saving = False
            self._busy = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Delete transaction
    # ─────────────────────────────────────────────────────────────────────────

    async def delete_tx(self, tx_id: str):
        self._busy = True
        try:
            DB.delete_transaction(self.user_id, self.access_token, tx_id)
            self._reload()
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

    def export_transactions_csv(self):
        import csv, io
        raw  = self._raw
        txs  = raw.get("txs", [])
        mid  = self.active_mid
        acct_map   = {a["id"]: a.get("name", "") for a in raw.get("accounts", [])}
        bucket_map = {b["id"]: b.get("name", "") for b in raw.get("buckets", [])}
        month_txs  = [t for t in txs if t.get("monthId") == mid]
        buf = io.StringIO()
        w   = csv.writer(buf)
        w.writerow(["date", "type", "description", "amount", "account", "to_account", "bucket"])
        for t in sorted(month_txs, key=lambda x: x.get("date") or ""):
            w.writerow([
                t.get("date", ""),
                t.get("type", ""),
                t.get("desc", ""),
                t.get("amount", ""),
                acct_map.get(t.get("accountId", ""), ""),
                acct_map.get(t.get("toAccountId", ""), ""),
                bucket_map.get(t.get("bucketId", ""), ""),
            ])
        yr, m0 = parse_month_id(mid)
        filename = f"transactions_{yr}_{m0+1:02d}.csv"
        return rx.download(data=buf.getvalue(), filename=filename, mime_type="text/csv")

    # ─────────────────────────────────────────────────────────────────────────
    #  Fill bucket
    # ─────────────────────────────────────────────────────────────────────────

    async def fill_bucket(self, bucket_id: str, budget: float):
        self._set_raw_alloc(bucket_id, budget)
        self._process(self._raw, self.active_mid)
        self._busy = True
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, self.active_mid)
            DB.upsert_alloc(self.user_id, self.access_token, self.active_mid, bucket_id, budget)
            yield rx.toast.success("Bucket filled", duration=1500)
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Inline allocation editing
    # ─────────────────────────────────────────────────────────────────────────

    def start_edit_budget(self, bid: str, budget_fmt: str):
        v = budget_fmt.replace(",", "").replace("$", "")
        self.editing_budget_bid = bid
        self.edit_budget_val    = v

    async def save_budget_edit(self):
        bid = self.editing_budget_bid
        if not bid:
            return
        try:
            amount = round(float(self.edit_budget_val or "0"), 2)
        except ValueError:
            amount = 0.0
        self.editing_budget_bid = ""
        self.edit_budget_val    = ""
        self._busy = True
        yield
        try:
            DB.upsert_budget(self.user_id, self.access_token, self.active_mid, bid, amount)
            self._reload()
            yield rx.toast.success("Saved", duration=1200)
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

    def cancel_budget_edit(self):
        self.editing_budget_bid = ""
        self.edit_budget_val    = ""

    def handle_budget_key(self, key: str):
        if key == "Enter":
            yield AppState.save_budget_edit()
        elif key == "Escape":
            self.cancel_budget_edit()

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
        self._busy = True
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, self.active_mid)
            DB.upsert_alloc(self.user_id, self.access_token, self.active_mid, bid, amount)
            yield rx.toast.success("Saved", duration=1200)
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

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
    #  Bucket reorder (▲ / ▼ buttons)
    # ─────────────────────────────────────────────────────────────────────────

    async def move_bucket_up(self, bid: str):
        yield
        try:
            buckets = list((self._raw or {}).get("buckets", []))
            target  = next((b for b in buckets if b["id"] == bid), None)
            if not target:
                return
            cat_id   = target.get("catId", "")
            siblings = sorted(
                [b for b in buckets if b.get("catId") == cat_id and not b.get("archived")],
                key=lambda b: b.get("order", 0),
            )
            idx = next((i for i, b in enumerate(siblings) if b["id"] == bid), None)
            if idx is None or idx == 0:
                return
            other   = siblings[idx - 1]
            a_order = int(target.get("order", 0))
            b_order = int(other.get("order", 0))
            if a_order == b_order:
                a_order, b_order = idx, idx - 1
            DB.update_bucket_order(self.user_id, self.access_token, bid,        b_order)
            DB.update_bucket_order(self.user_id, self.access_token, other["id"], a_order)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
        except Exception as e:
            yield rx.toast.error(f"Reorder failed: {e}", duration=6000)

    async def move_bucket_down(self, bid: str):
        yield
        try:
            buckets = list((self._raw or {}).get("buckets", []))
            target  = next((b for b in buckets if b["id"] == bid), None)
            if not target:
                return
            cat_id   = target.get("catId", "")
            siblings = sorted(
                [b for b in buckets if b.get("catId") == cat_id and not b.get("archived")],
                key=lambda b: b.get("order", 0),
            )
            idx = next((i for i, b in enumerate(siblings) if b["id"] == bid), None)
            if idx is None or idx >= len(siblings) - 1:
                return
            other   = siblings[idx + 1]
            a_order = int(target.get("order", 0))
            b_order = int(other.get("order", 0))
            if a_order == b_order:
                a_order, b_order = idx + 1, idx
            DB.update_bucket_order(self.user_id, self.access_token, bid,        b_order)
            DB.update_bucket_order(self.user_id, self.access_token, other["id"], a_order)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
        except Exception as e:
            yield rx.toast.error(f"Reorder failed: {e}", duration=6000)

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
        self._busy = True
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, mid)
            DB.upsert_alloc(self.user_id, self.access_token, mid, bid, new_vault)
            DB.upsert_alloc(self.user_id, self.access_token, mid, dest, new_dest)
            yield rx.toast.success("Vault transferred")
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

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
        self._busy = True
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
            yield self._on_db_error(e)
        finally:
            self._busy = False

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
            budget = b_budget(active_month, bid) or float(b.get("defaultBudget") or 0)
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
        self._busy = True
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, mid)
            for bid, new_val in new_allocs.items():
                DB.upsert_alloc(self.user_id, self.access_token, mid, bid, new_val)
            yield rx.toast.success("Distributed!")
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

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
        self._busy = True
        yield
        try:
            DB.insert_paycheck(
                self.user_id, self.access_token,
                self.setup_pc_label.strip(), amt, freq,
                self.setup_pc_anchor.strip(),
            )
            self._reload()
            self.setup_pc_label  = ""
            self.setup_pc_amount = ""
            self.setup_pc_anchor = ""
            self.setup_pc_saving = False
            yield rx.toast.success("Paycheck added")
        except Exception as e:
            self.setup_pc_saving = False
            self.setup_pc_error  = str(e)
            yield self._on_db_error(e)
        finally:
            self._busy = False

    async def delete_paycheck_item(self, pc_id: str):
        self._busy = True
        yield
        try:
            DB.delete_paycheck(self.user_id, self.access_token, pc_id)
            self._reload()
            yield rx.toast.success("Deleted")
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

    def open_edit_paycheck(self, pc_id: str):
        pc = next((p for p in (self._raw.get("paychecks") or []) if p.get("id") == pc_id), None)
        if not pc:
            return
        v = float(pc.get("amount") or 0)
        self.edit_pc_id     = pc_id
        self.edit_pc_label  = pc.get("label", "")
        self.edit_pc_amount = str(int(v)) if v == int(v) else f"{v:.2f}"
        self.edit_pc_freq   = str(pc.get("freq", 14))
        self.edit_pc_anchor = pc.get("anchor_date") or ""
        self.edit_pc_saving = False
        self.edit_pc_error  = ""
        self.edit_pc_open   = True

    def close_edit_paycheck(self):
        self.edit_pc_open  = False
        self.edit_pc_error = ""

    async def save_edit_paycheck(self):
        if not self.edit_pc_label.strip():
            self.edit_pc_error = "Label required"
            return
        try:
            amt  = round(float(self.edit_pc_amount or "0"), 2)
            freq = int(self.edit_pc_freq or "14")
        except ValueError:
            self.edit_pc_error = "Invalid number"
            return
        if amt <= 0:
            self.edit_pc_error = "Amount must be positive"
            return
        self.edit_pc_saving = True
        self.edit_pc_error  = ""
        self._busy = True
        yield
        try:
            DB.update_paycheck(
                self.user_id, self.access_token, self.edit_pc_id,
                self.edit_pc_label.strip(), amt, freq, self.edit_pc_anchor.strip(),
            )
            self._reload()
            self.edit_pc_open   = False
            self.edit_pc_saving = False
            yield rx.toast.success("Paycheck updated")
        except Exception as e:
            self.edit_pc_saving = False
            self.edit_pc_error  = str(e)
            yield self._on_db_error(e)
        finally:
            self._busy = False

    def toggle_show_archived_cats(self):
        self.show_archived_cats = not self.show_archived_cats

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
        self._busy = True
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
            self._reload()
            self.rule_sheet_open   = False
            self.rule_sheet_saving = False
            yield rx.toast.success("Rule added")
        except Exception as e:
            self.rule_sheet_saving = False
            self.rule_sheet_error  = str(e)
            yield self._on_db_error(e)
        finally:
            self._busy = False

    async def toggle_alloc_rule_item(self, rule_id: str):
        self._busy = True
        yield
        try:
            DB.toggle_alloc_rule(self.user_id, self.access_token, rule_id)
            self._reload()
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

    async def delete_alloc_rule_item(self, rule_id: str):
        self._busy = True
        yield
        try:
            DB.delete_alloc_rule(self.user_id, self.access_token, rule_id)
            self._reload()
            yield rx.toast.success("Rule deleted")
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

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
        self.edit_tx_reconciled        = bool(tx.get("reconciled"))
        self._edit_tx_was_reconciled   = bool(tx.get("reconciled"))
        self.edit_tx_error             = ""
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
        if not self.edit_tx_date:
            self.edit_tx_error = "Date is required."
            return
        if self.edit_tx_type == "xfr" and self.edit_tx_to_account == self.edit_tx_account:
            self.edit_tx_error = "Source and destination accounts must differ"
            return
        mid = _date_to_mid(self.edit_tx_date)
        self.edit_tx_saving = True
        self.edit_tx_error  = ""
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, mid)
            DB.update_transaction(self.user_id, self.access_token, self.edit_tx_id, {
                "description":        self.edit_tx_desc.strip(),
                "amount":             amount,
                "date":               self.edit_tx_date,
                "month_id":           mid,
                "account_id":         self.edit_tx_account,
                "bucket_id":          self.edit_tx_bucket or None,
                "to_account_id":      self.edit_tx_to_account or None,
                "income_type":        self.edit_tx_income_type if self.edit_tx_type == "in" else None,
                # If the tx was reconciled when opened, editing it removes the cleared status.
                "reconciled": False if self._edit_tx_was_reconciled else self.edit_tx_reconciled,
            })
            data = DB.load_all(self.user_id, self.access_token)
            self._raw                    = data
            self._process(data, self.active_mid)
            self.edit_tx_open            = False
            self.edit_tx_saving          = False
            self._edit_tx_was_reconciled = False
            yield rx.toast.success("Transaction updated")
        except Exception as e:
            self.edit_tx_saving = False
            self.edit_tx_error  = str(e)

    # ─────────────────────────────────────────────────────────────────────────
    #  Reconciliation
    # ─────────────────────────────────────────────────────────────────────────

    def open_reconcile(self, acct_id: str = ""):
        """Open the reconcile modal, optionally pre-selecting an account."""
        # If no account given, pick the first non-debt account
        if not acct_id:
            for a in self.accounts_rows:
                if a.get("type") != "debt":
                    acct_id = a.get("id", "")
                    break
        self.recon_account_id        = acct_id
        self.recon_statement_balance = ""
        self.recon_unchecked_ids     = []
        self.recon_saving            = False
        self.recon_error             = ""
        self.recon_open              = True

    def close_reconcile(self):
        self.recon_open = False

    def set_recon_account_id(self, v: str):
        self.recon_account_id        = v
        self.recon_statement_balance = ""
        self.recon_unchecked_ids     = []
        self.recon_error             = ""

    def set_recon_statement_balance(self, v: str):
        self.recon_statement_balance = v

    def toggle_recon_tx(self, tx_id: str):
        ids = list(self.recon_unchecked_ids)
        if tx_id in ids:
            ids.remove(tx_id)   # was unchecked → check it
        else:
            ids.append(tx_id)   # was checked  → uncheck it
        self.recon_unchecked_ids = ids

    async def finish_reconcile(self):
        if not self.recon_can_finish:
            self.recon_error = "Difference must be $0.00 before finishing."
            return
        unchecked = set(self.recon_unchecked_ids)
        ids_to_mark = [
            str(row.get("id", ""))
            for row in self.recon_txs
            if str(row.get("id", "")) not in unchecked
        ]
        if not ids_to_mark:
            self.recon_error = "No transactions selected."
            return
        self.recon_saving = True
        self.recon_error  = ""
        yield
        try:
            for tx_id in ids_to_mark:
                DB.update_transaction(
                    self.user_id, self.access_token, tx_id,
                    {"reconciled": True},
                )
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
            self.recon_open   = False
            self.recon_saving = False
            yield rx.toast.success(f"Reconciled {len(ids_to_mark)} transaction{'s' if len(ids_to_mark) != 1 else ''}")
        except Exception as e:
            self.recon_saving = False
            self.recon_error  = str(e)

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

        # Pre-index non-scheduled "out" transactions by (bucket_id, month_id)
        # so bucket rows avoid scanning all transactions per bucket per month.
        _spent_idx: dict[tuple, float] = {}
        for _t in txs:
            if _t.get("type") == "out" and not is_scheduled(_t):
                _k = (_t.get("bucketId") or "", _t.get("monthId") or "")
                _spent_idx[_k] = _spent_idx.get(_k, 0.0) + float(_t.get("amount") or 0)

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
        for t in txs:
            if t.get("monthId") != mid or is_scheduled(t):
                continue
            amt = float(t.get("amount") or 0)
            if t.get("type") == "in":
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
                b_budget(active_month, b["id"]) or float(b.get("defaultBudget") or 0)
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
                "is_over": "", "over_fmt": "",
                "status_label": "", "action_hint": "", "left_avail_fmt": "",
                "roll_fmt": "", "show_roll": "", "target_fmt": "",
                "sinking_pct_str": "0%", "months_left_str": "",
                "show_goal": "", "vault_fmt": "", "show_vault": "",
                "due_label": "", "due_urgency": "", "is_skipped": "",
            })

            for b in cat_buckets:
                bid   = b["id"]
                btype = b.get("type", "expense")
                alloc  = b_alloc(active_month, bid)
                budget = b_budget(active_month, bid) or float(b.get("defaultBudget") or 0)

                if btype == "vault":
                    vault_total      = vault_accumulated(bid, all_months)
                    vault_withdrawn  = sum(
                        float((m.get("vaultWithdrawals") or {}).get(bid) or 0)
                        for m in all_months
                    )
                    spent = vault_withdrawn  # actual withdrawals from the vault
                    avail = vault_total      # remaining accumulated balance
                else:
                    vault_total = 0.0
                    spent = _spent_idx.get((bid, mid), 0.0)
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
                    "is_over":        "1" if avail < -0.005 else "",
                    "over_fmt":       f"OVER −{_fmt(abs(avail))}" if avail < -0.005 else "",
                    "status_label": (
                        "Overspent"   if avail < -0.005 else
                        "Paid"        if budget > 0 and is_funded and spent >= alloc - 0.005 else
                        "Funded"      if is_funded else
                        "Underfunded" if budget > 0 else
                        ""
                    ),
                    "action_hint": (
                        f"Allocate {_fmt(abs(avail))} to cover overspend" if avail < -0.005 else
                        f"Allocate {_fmt(gap)} to fully fund"             if gap > 0.005 else
                        ""
                    ),
                    "left_avail_fmt": _fmt(max(0.0, avail)),
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

        # ── Scoreboard: needs-attention buckets ───────────────────────────────
        attention: list[dict] = []
        for b in active_buckets:
            bid   = b["id"]
            btype = b.get("type", "expense")
            if btype == "vault" or bool(skipped_map.get(bid)):
                continue
            alloc  = b_alloc(active_month, bid)
            budget = b_budget(active_month, bid) or float(b.get("defaultBudget") or 0)
            avail  = bucket_available(b, active_month, all_months, txs)
            if avail < -0.005:
                attention.append({
                    "id": bid, "name": b.get("name", ""),
                    "label": f"−{_fmt(abs(avail))} over",
                    "budget": budget,
                    "is_over": "1",
                })
            elif budget > 0 and alloc < budget - 0.005:
                gap = budget - alloc
                attention.append({
                    "id": bid, "name": b.get("name", ""),
                    "label": f"−{_fmt(gap)} gap",
                    "budget": budget,
                    "is_over": "",
                })
        attention.sort(key=lambda x: (x["is_over"] != "1", -float(x["budget"])))
        self.attention_rows = attention

        # ── Scoreboard: category rollup ───────────────────────────────────────
        cat_rollups: list[dict] = []
        for cat in cats_sorted:
            cid       = cat["id"]
            cat_color = cat.get("color", "#818cf8")
            cb = sorted(
                [b for b in active_buckets if b.get("catId") == cid],
                key=lambda b: b.get("order", 0),
            )
            if not cb:
                continue
            cb_alloc_sum  = sum(b_alloc(active_month, b["id"]) for b in cb)
            cb_budget_sum = sum(
                (b_budget(active_month, b["id"]) or float(b.get("defaultBudget") or 0))
                for b in cb if b.get("type") != "vault"
            )
            cb_pct    = min(100, round(cb_alloc_sum / cb_budget_sum * 100)) if cb_budget_sum > 0 else 100
            cat_rollups.append({
                "name":       cat.get("name", ""),
                "color":      cat_color,
                "alloc_fmt":  _fmt(cb_alloc_sum),
                "budget_fmt": _fmt(cb_budget_sum) if cb_budget_sum > 0 else "",
                "pct_str":    f"{cb_pct}%",
                "is_funded":  "1" if cb_pct >= 100 else "",
            })
        self.cat_rollup_rows = cat_rollups

        # ── Ledger scoreboard: last-month comparison ──────────────────────────
        prev_mid_str = _month_id(year - 1, 11) if m0 == 0 else _month_id(year, m0 - 1)
        last_inc = 0.0
        last_sp  = 0.0
        for t in txs:
            if t.get("monthId") != prev_mid_str or is_scheduled(t):
                continue
            amt = float(t.get("amount") or 0)
            if t.get("type") == "in":
                last_inc += amt
            elif t.get("type") == "out":
                last_sp += amt
        self.last_month_income = last_inc
        self.last_month_spent  = last_sp
        delta = sp_total - last_sp
        if abs(delta) < 0.005:
            self.mom_verdict = "Same spending as last month"
            self.mom_better  = True
        elif delta < 0:
            self.mom_verdict = f"↓ {_fmt(abs(delta))} less spent"
            self.mom_better  = True
        else:
            self.mom_verdict = f"↑ {_fmt(delta)} more spent"
            self.mom_better  = False

        # ── Ledger scoreboard: bucket spending breakdown ───────────────────────
        bucket_spend_map: dict[str, float] = {}
        for t in txs:
            if t.get("monthId") == mid and t.get("type") == "out":
                bid = t.get("bucketId") or ""
                if bid:
                    bucket_spend_map[bid] = bucket_spend_map.get(bid, 0.0) + float(t.get("amount") or 0)
        spend_rows_raw = []
        for bid, sa in bucket_spend_map.items():
            if sa <= 0:
                continue
            bname = next((b.get("name", "") for b in active_buckets if b["id"] == bid), "")
            if not bname:
                continue
            budget_val = b_budget(active_month, bid) or float(
                next((b for b in active_buckets if b["id"] == bid), {}).get("defaultBudget") or 0
            )
            pct = min(100, round(sa / budget_val * 100)) if budget_val > 0 else 0
            spend_rows_raw.append((sa, {
                "name":      bname,
                "spent_fmt": _fmt(sa),
                "pct_str":   f"{pct}%",
                "is_over":   "1" if budget_val > 0 and sa > budget_val else "",
            }))
        spend_rows_raw.sort(key=lambda x: -x[0])
        self.ledger_bucket_spend = [r for _, r in spend_rows_raw[:8]]

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
            "date_label": "", "acct_id": "", "to_acct_id": "", "running_balance": "",
        }
        # NOTE: no "date" key here — tx rows set their own real date, and a
        # "date" default would overwrite it via the trailing dict spread.
        _HDR_DEFAULTS = {"label": "", "net_fmt": "", "net_color": ""}

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
                "3px solid #34d399"   if ttype == "in" and not sched else
                "3px solid #fbbf24"   if sched else
                "3px solid #8282a244" if ttype == "xfr" else
                "3px solid #f8717155"   # expense — subtle red
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
                "acct_id":        t.get("accountId", "") or "",
                "to_acct_id":     t.get("toAccountId", "") or "",
                **_HDR_DEFAULTS,
            })

        self.ledger_rows     = ledger_flat
        self.ledger_tx_count = sum(1 for r in ledger_flat if r.get("row_type") == "tx")

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
        self.acct_balance_map = {r["id"]: r["balance"] for r in acc_rows}
        self.total_cash = sum(r["balance"] for r in acc_rows if r["type"] != "debt")
        self.total_debt = sum(r["balance"] for r in acc_rows if r["type"] == "debt")

        # ── Category rows (for category management in Setup panel) ─────────
        self.cat_rows = [
            {
                "id":           c["id"],
                "name":         c.get("name", ""),
                "color":        c.get("color", "#818cf8"),
                "order":        c.get("order", 0),
                "bucket_count": str(len([b for b in all_buckets
                                         if b.get("catId") == c["id"] and not b.get("archived")])),
            }
            for c in cats_sorted
            if not c.get("archived")
        ]
        self.archived_cat_rows = [
            {
                "id":    c["id"],
                "name":  c.get("name", ""),
                "color": c.get("color", "#818cf8"),
            }
            for c in cats_sorted
            if c.get("archived")
        ]

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
        # preserve_open=True keeps whatever cards the user has expanded;
        # auto-open only happens when fc_open_pids is still empty (first load)
        self._run_forecast(preserve_open=bool(self.fc_open_pids))

        if self.active_panel == "reports":
            self._build_reports()

    # ─────────────────────────────────────────────────────────────────────────
    #  Accounts panel
    # ─────────────────────────────────────────────────────────────────────────

    def open_add_account(self):
        self.add_acct_name    = ""
        self.add_acct_type    = "budget"
        self.add_acct_color   = "#3a7fc1"
        self.add_acct_opening = "0"
        self.add_acct_saving  = False
        self.add_acct_error   = ""
        self.add_acct_open    = True

    async def save_add_account(self):
        if not self.add_acct_name.strip():
            self.add_acct_error = "Name is required"
            return
        try:
            opening = round(float(self.add_acct_opening or "0"), 2)
        except ValueError:
            self.add_acct_error = "Invalid opening balance"
            return
        self.add_acct_saving = True
        self.add_acct_error  = ""
        yield
        try:
            DB.insert_account(
                self.user_id, self.access_token,
                self.add_acct_name.strip(), self.add_acct_type,
                self.add_acct_color, opening,
            )
            data = DB.load_all(self.user_id, self.access_token)
            self._raw            = data
            self._process(data, self.active_mid)
            self.add_acct_open   = False
            self.add_acct_saving = False
            yield rx.toast.success("Account added")
        except Exception as e:
            self.add_acct_saving = False
            self.add_acct_error  = str(e)

    def open_account_settings(self, aid: str):
        acct = next((a for a in (self._raw.get("accounts") or []) if a["id"] == aid), None)
        if not acct:
            return
        v = float(acct.get("openingBalance") or 0)
        self.acct_settings_aid       = aid
        self.acct_settings_name      = acct.get("name", "")
        self.acct_settings_type      = acct.get("type", "budget")
        self.acct_settings_color     = acct.get("color", "#3a7fc1")
        self.acct_settings_opening   = str(int(v)) if v == int(v) else f"{v:.2f}"
        self.acct_settings_apr       = str(acct.get("debtAPR") or "")
        self.acct_settings_min_pay   = str(acct.get("debtMinPayment") or "")
        self.acct_settings_credit    = str(acct.get("creditLimit") or "")
        self.acct_settings_is_promo  = bool(acct.get("isPromo"))
        self.acct_settings_promo_end = acct.get("promoEndDate") or ""
        self.acct_settings_saving    = False
        self.acct_settings_error     = ""
        self.acct_settings_open      = True

    async def save_account_settings(self):
        if not self.acct_settings_name.strip():
            self.acct_settings_error = "Name is required"
            return
        try:
            opening = round(float(self.acct_settings_opening or "0"), 2)
            apr     = float(self.acct_settings_apr) if self.acct_settings_apr.strip() else None
            min_pay = float(self.acct_settings_min_pay) if self.acct_settings_min_pay.strip() else None
            credit  = float(self.acct_settings_credit) if self.acct_settings_credit.strip() else None
        except ValueError:
            self.acct_settings_error = "Invalid number"
            return
        self.acct_settings_saving = True
        self.acct_settings_error  = ""
        yield
        try:
            fields: dict = {
                "name":            self.acct_settings_name.strip(),
                "type":            self.acct_settings_type,
                "color":           self.acct_settings_color,
                "opening_balance": opening,
            }
            if apr is not None:     fields["debt_apr"]          = apr
            if min_pay is not None: fields["debt_min_payment"]  = min_pay
            if credit is not None:  fields["credit_limit"]      = credit
            if self.acct_settings_type == "debt":
                fields["is_promo"]       = self.acct_settings_is_promo
                fields["promo_end_date"] = self.acct_settings_promo_end or None
            DB.update_account(self.user_id, self.access_token, self.acct_settings_aid, fields)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw                 = data
            self._process(data, self.active_mid)
            self.acct_settings_open   = False
            self.acct_settings_saving = False
            yield rx.toast.success("Account updated")
        except Exception as e:
            self.acct_settings_saving = False
            self.acct_settings_error  = str(e)

    async def archive_account(self, aid: str):
        try:
            DB.update_account(self.user_id, self.access_token, aid, {"archived": True})
            data = DB.load_all(self.user_id, self.access_token)
            self._raw               = data
            self._process(data, self.active_mid)
            self.acct_settings_open = False
            yield rx.toast.success("Account archived")
        except Exception as e:
            self.acct_settings_error = str(e)

    def toggle_acct_expand(self, aid: str):
        if self.acct_expanded_id == aid:
            self.acct_expanded_id = ""
            self.acct_ledger_rows = []
            return
        self.acct_expanded_id = aid
        raw_txs    = (self._raw or {}).get("txs", [])
        bucket_map = {b["id"]: b.get("name", "") for b in (self._raw or {}).get("buckets", [])}
        txs = sorted(
            [t for t in raw_txs if t.get("accountId") == aid],
            key=lambda t: t.get("date", ""),
            reverse=True,
        )[:20]
        self.acct_ledger_rows = [
            {
                "id":         t["id"],
                "date_label": _date_label(t.get("date", "")),
                "desc":       t.get("desc") or "—",
                "amount_fmt": (f"+{_fmt(float(t.get('amount') or 0))}" if t.get("type") == "in"
                               else f"−{_fmt(float(t.get('amount') or 0))}"),
                "amt_color":  ("#34d399" if t.get("type") == "in" else
                               "#f87171" if t.get("type") == "out" else "#8282a2"),
                "bucket":     bucket_map.get(t.get("bucketId") or "", ""),
            }
            for t in txs
        ]

    def open_debt_payment(self, aid: str):
        acct = next((a for a in (self._raw.get("accounts") or []) if a["id"] == aid), None)
        if not acct:
            return
        budget_accts = [a for a in (self._raw.get("accounts") or [])
                        if a.get("type") == "budget" and not a.get("archived")]
        self.debt_pay_aid          = aid
        self.debt_pay_acct_name    = acct.get("name", "")
        self.debt_pay_amount       = ""
        self.debt_pay_date         = date.today().isoformat()
        self.debt_pay_from_account = budget_accts[0]["id"] if budget_accts else ""
        self.debt_pay_bucket       = ""
        self.debt_pay_saving       = False
        self.debt_pay_error        = ""
        self.debt_pay_open         = True

    async def save_debt_payment(self):
        try:
            amount = round(float(self.debt_pay_amount or "0"), 2)
        except ValueError:
            self.debt_pay_error = "Invalid amount"
            return
        if amount <= 0:
            self.debt_pay_error = "Amount must be positive"
            return
        if not self.debt_pay_from_account:
            self.debt_pay_error = "Select a source account"
            return
        if self.debt_pay_from_account == self.debt_pay_aid:
            self.debt_pay_error = "Source cannot be the debt account itself"
            return
        self.debt_pay_saving = True
        self.debt_pay_error  = ""
        yield
        try:
            mid = _date_to_mid(self.debt_pay_date)
            DB.ensure_month(self.user_id, self.access_token, mid)
            DB.insert_debt_payment(
                self.user_id, self.access_token,
                self.debt_pay_aid, self.debt_pay_from_account,
                amount, self.debt_pay_date, mid,
                self.debt_pay_acct_name, self.debt_pay_bucket,
            )
            data = DB.load_all(self.user_id, self.access_token)
            self._raw            = data
            self._process(data, self.active_mid)
            self.debt_pay_open   = False
            self.debt_pay_saving = False
            yield rx.toast.success("Payment recorded")
        except Exception as e:
            self.debt_pay_saving = False
            self.debt_pay_error  = str(e)

    # ─────────────────────────────────────────────────────────────────────────
    #  Category management
    # ─────────────────────────────────────────────────────────────────────────

    def open_cat_edit(self, cid: str):
        cat = next((c for c in (self._raw.get("cats") or []) if c["id"] == cid), None)
        if not cat:
            return
        self.cat_edit_id    = cid
        self.cat_edit_name  = cat.get("name", "")
        self.cat_edit_color = cat.get("color", "#818cf8")
        self.cat_saving     = False

    def close_cat_edit(self):
        self.cat_edit_id = ""

    async def save_cat_edit(self):
        if not self.cat_edit_id or not self.cat_edit_name.strip():
            return
        self.cat_saving = True
        self._busy = True
        yield
        try:
            DB.update_category(self.user_id, self.access_token, self.cat_edit_id, {
                "name":  self.cat_edit_name.strip(),
                "color": self.cat_edit_color,
            })
            self._reload()
            self.cat_edit_id = ""
            self.cat_saving  = False
            yield rx.toast.success("Category updated")
        except Exception as e:
            self.cat_saving = False
            yield self._on_db_error(e)
        finally:
            self._busy = False

    async def archive_category(self, cid: str):
        self._busy = True
        yield
        try:
            DB.update_category(self.user_id, self.access_token, cid, {"archived": True})
            self._reload()
            self.cat_edit_id = ""
            yield rx.toast.success("Category archived")
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

    async def unarchive_category(self, cid: str):
        self._busy = True
        yield
        try:
            DB.update_category(self.user_id, self.access_token, cid, {"archived": False})
            self._reload()
            yield rx.toast.success("Category restored")
        except Exception as e:
            yield self._on_db_error(e)
        finally:
            self._busy = False

    async def move_cat_up(self, cid: str):
        self._busy = True
        yield
        try:
            cats = sorted(
                [c for c in (self._raw or {}).get("cats", []) if not c.get("archived")],
                key=lambda c: c.get("order", 0),
            )
            idx = next((i for i, c in enumerate(cats) if c["id"] == cid), None)
            if idx is None or idx == 0:
                return
            other   = cats[idx - 1]
            a_order = int(cats[idx].get("order", 0))
            b_order = int(other.get("order", 0))
            if a_order == b_order:
                a_order, b_order = idx, idx - 1
            DB.update_category_order(self.user_id, self.access_token, cid, b_order)
            DB.update_category_order(self.user_id, self.access_token, other["id"], a_order)
            self._reload()
        except Exception as e:
            yield rx.toast.error(f"Reorder failed: {e}")
        finally:
            self._busy = False

    async def move_cat_down(self, cid: str):
        self._busy = True
        yield
        try:
            cats = sorted(
                [c for c in (self._raw or {}).get("cats", []) if not c.get("archived")],
                key=lambda c: c.get("order", 0),
            )
            idx = next((i for i, c in enumerate(cats) if c["id"] == cid), None)
            if idx is None or idx >= len(cats) - 1:
                return
            other   = cats[idx + 1]
            a_order = int(cats[idx].get("order", 0))
            b_order = int(other.get("order", 0))
            if a_order == b_order:
                a_order, b_order = idx + 1, idx
            DB.update_category_order(self.user_id, self.access_token, cid, b_order)
            DB.update_category_order(self.user_id, self.access_token, other["id"], a_order)
            self._reload()
        except Exception as e:
            yield rx.toast.error(f"Reorder failed: {e}")
        finally:
            self._busy = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Month workflow
    # ─────────────────────────────────────────────────────────────────────────

    async def do_copy_allocs(self):
        months      = self._raw.get("months") or []
        sorted_mids = sorted({m["id"] for m in months}, key=month_sort_key)
        if self.active_mid not in sorted_mids or sorted_mids.index(self.active_mid) == 0:
            yield rx.toast.info("No previous month to copy from")
            return
        src_mid = sorted_mids[sorted_mids.index(self.active_mid) - 1]
        self.copy_allocs_saving = True
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, self.active_mid)
            DB.copy_month_allocs(self.user_id, self.access_token, self.active_mid, src_mid)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw               = data
            self._process(data, self.active_mid)
            self.copy_allocs_saving = False
            yield rx.toast.success("Allocations copied from previous month")
        except Exception as e:
            self.copy_allocs_saving = False
            yield rx.toast.error(f"Copy failed: {e}")

    async def do_close_month(self):
        self.close_month_saving = True
        yield
        try:
            DB.ensure_month(self.user_id, self.access_token, self.active_mid)
            accounts = (self._raw or {}).get("accounts", [])
            txs      = (self._raw or {}).get("txs", [])
            DB.close_month(self.user_id, self.access_token, self.active_mid, accounts, txs)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw               = data
            self._process(data, self.active_mid)
            self.close_month_saving = False
            yield rx.toast.success("Month closed")
        except Exception as e:
            self.close_month_saving = False
            yield rx.toast.error(f"Close failed: {e}")

    async def do_reopen_month(self):
        yield
        try:
            DB.reopen_month(self.user_id, self.access_token, self.active_mid)
            data = DB.load_all(self.user_id, self.access_token)
            self._raw = data
            self._process(data, self.active_mid)
            yield rx.toast.success("Month reopened")
        except Exception as e:
            yield rx.toast.error(f"Reopen failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    #  Payees
    # ─────────────────────────────────────────────────────────────────────────

    def load_payees(self):
        # Read-only autocomplete fetch. Degrade gracefully to an empty list on
        # failure; any auth death surfaces on the next write via _on_db_error.
        try:
            self.payee_options = DB.get_payees(self.user_id, self.access_token)
        except Exception:
            self.payee_options = []

    # ─────────────────────────────────────────────────────────────────────────
    #  Signup
    # ─────────────────────────────────────────────────────────────────────────

    async def signup(self, form_data: dict):
        email    = (form_data.get("email") or "").strip()
        password = (form_data.get("password") or "").strip()
        confirm  = (form_data.get("confirm") or "").strip()
        self.auth_error = ""
        if password != confirm:
            self.auth_error = "Passwords do not match."
            return
        if len(password) < 6:
            self.auth_error = "Password must be at least 6 characters."
            return
        self.is_loading = True
        yield
        try:
            auth = DB.sign_up(email, password)
            self.access_token = auth["access_token"]
            self.user_id      = auth["user_id"]
            self.user_email   = auth["user_email"]
            self.is_loading   = False
            yield rx.redirect("/dashboard")
        except Exception as e:
            self.auth_error = str(e)
            self.is_loading = False

    # ─────────────────────────────────────────────────────────────────────────
    #  Reports builder
    # ─────────────────────────────────────────────────────────────────────────

    def set_reports_tab(self, tab: str):
        self.reports_tab = tab

    def _build_reports(self):
        raw = self._raw
        if not raw:
            return

        accounts    = raw.get("accounts", [])
        all_buckets = raw.get("buckets", [])
        cats        = raw.get("cats", [])
        txs         = raw.get("txs", [])
        all_months  = raw.get("months", [])

        budget_aid_set = {a["id"] for a in accounts if a.get("type") == "budget"}
        active_buckets = [b for b in all_buckets if not b.get("archived")]
        cat_map        = {c["id"]: c for c in cats}
        cats_sorted    = sorted(cats, key=lambda c: c.get("order", 0))

        # ── Determine report months (last ≤3 with any transactions) ──────
        tx_mids = sorted(
            {t["monthId"] for t in txs if t.get("monthId")},
            key=month_sort_key,
        )
        report_mids = tx_mids[-3:]
        n = len(report_mids)
        if not report_mids:
            return

        # ── Per-month aggregate objects ───────────────────────────────────
        monthly: list[dict] = []
        for mid in report_mids:
            yr, m0 = parse_month_id(mid)
            label  = f"{MONTH_NAMES[m0][:3]} {yr}"
            m_obj  = next(
                (m for m in all_months if m.get("id") == mid),
                {"id": mid, "allocations": {}, "budgets": {},
                 "rolloverReleased": {}, "skippedBuckets": {}, "vaultWithdrawals": {}},
            )
            income = sum(
                float(t.get("amount", 0)) for t in txs
                if t.get("monthId") == mid and t.get("type") == "in"
                and t.get("accountId") in budget_aid_set and not is_scheduled(t)
            )
            spent = sum(
                float(t.get("amount", 0)) for t in txs
                if t.get("monthId") == mid and t.get("type") == "out"
                and not is_scheduled(t)
            )
            alloc = total_allocated(m_obj, active_buckets)
            net   = income - spent
            savings_rate = round(net / income * 100) if income > 0 else 0
            monthly.append({
                "mid": mid, "label": label, "m_obj": m_obj,
                "income": income, "spent": spent, "alloc": alloc,
                "net": net, "savings_rate": savings_rate,
            })

        # ── Monthly Summary cards ─────────────────────────────────────────
        summary_cards: list[dict] = []
        for m in monthly:
            cat_rows: list[dict] = []
            for cat in cats_sorted:
                cid  = cat["id"]
                cb   = [b for b in active_buckets
                        if b.get("catId") == cid and b.get("type") != "vault"]
                if not cb:
                    continue
                cat_spent  = sum(b_spent(m["mid"], b["id"], txs) for b in cb)
                cat_budget = sum(
                    b_budget(m["m_obj"], b["id"]) or float(b.get("defaultBudget") or 0)
                    for b in cb
                )
                if cat_spent < 0.01 and cat_budget < 0.01:
                    continue
                pct = min(100, round(cat_spent / cat_budget * 100)) if cat_budget > 0 else 0
                cat_rows.append({
                    "name":       cat.get("name", ""),
                    "color":      cat.get("color", "#818cf8"),
                    "spent_fmt":  _fmt(cat_spent),
                    "budget_fmt": _fmt(cat_budget) if cat_budget > 0 else "",
                    "pct":        str(pct),
                    "bar_w":      f"{pct}%",
                    "is_over":    "1" if cat_spent > cat_budget + 0.005 else "",
                })
            net_positive = "1" if m["net"] >= 0 else ""
            summary_cards.append({
                "label":        m["label"],
                "income_fmt":   _fmt(m["income"]),
                "spent_fmt":    _fmt(m["spent"]),
                "net_fmt":      _fmt(m["net"]),
                "net_positive": net_positive,
                "net_color":    "#34d399" if net_positive else "#f87171",
                "savings_rate": f"{m['savings_rate']}%",
                "alloc_fmt":    _fmt(m["alloc"]),
                "cat_rows":     cat_rows,
            })
        self.summary_cards = summary_cards

        # ── Budget vs Actual ──────────────────────────────────────────────
        bva_rows: list[dict[str, Any]] = []

        def _empty_month_cols() -> dict:
            d: dict = {}
            for i in range(3):
                d[f"m{i}_budget"]    = ""
                d[f"m{i}_spent"]     = ""
                d[f"m{i}_pct"]       = "0"
                d[f"m{i}_bar_w"]     = "0%"
                d[f"m{i}_status"]    = ""
                d[f"m{i}_var"]       = ""
                d[f"m{i}_var_color"] = "#6868a2"
                d[f"show_m{i}"]      = ""
            return d

        for cat in cats_sorted:
            cid      = cat["id"]
            cb = sorted(
                [b for b in active_buckets
                 if b.get("catId") == cid and b.get("type") != "vault"],
                key=lambda b: b.get("order", 0),
            )
            if not cb:
                continue

            # Category header row
            cat_hdr: dict[str, Any] = {
                "row_type": "cat",
                "name":     cat.get("name", ""),
                "color":    cat.get("color", "#818cf8"),
                "bid":      "", "cat_name": "",
                **_empty_month_cols(),
                "avg_budget": "", "avg_spent": "", "avg_var": "", "avg_var_color": "#6868a2", "avg_status": "",
            }
            for i in range(n):
                cat_hdr[f"show_m{i}"] = "1"
            bva_rows.append(cat_hdr)

            for b in cb:
                bid   = b["id"]
                row: dict[str, Any] = {
                    "row_type": "bucket",
                    "bid":      bid,
                    "name":     b.get("name", ""),
                    "cat_name": cat.get("name", ""),
                    "color":    cat.get("color", "#818cf8"),
                    **_empty_month_cols(),
                    "avg_budget": "", "avg_spent": "", "avg_var": "", "avg_var_color": "#6868a2", "avg_status": "",
                }
                budgets: list[float] = []
                spents:  list[float] = []
                for i, m in enumerate(monthly):
                    budget = b_budget(m["m_obj"], bid) or float(b.get("defaultBudget") or 0)
                    spent  = b_spent(m["mid"], bid, txs)
                    pct    = min(150, round(spent / budget * 100)) if budget > 0 else 0
                    if spent > budget + 0.005:
                        status = "over"
                    elif budget > 0 and spent >= budget * 0.85:
                        status = "close"
                    elif spent > 0:
                        status = "ok"
                    else:
                        status = ""
                    var = budget - spent
                    var_str = (f"+{_fmt(var)}" if var > 0.005 else
                               _fmt(var) if var < -0.005 else "✓")
                    var_color = ("#34d399" if var_str.startswith("+") or var_str == "✓"
                                 else "#f87171")
                    row[f"m{i}_budget"]    = _fmt(budget) if budget > 0 else "—"
                    row[f"m{i}_spent"]     = _fmt(spent)  if spent  > 0 else "—"
                    row[f"m{i}_pct"]       = str(pct)
                    row[f"m{i}_bar_w"]     = f"{min(100, pct)}%"
                    row[f"m{i}_status"]    = status
                    row[f"m{i}_var"]       = var_str
                    row[f"m{i}_var_color"] = var_color
                    row[f"show_m{i}"]      = "1"
                    budgets.append(budget)
                    spents.append(spent)

                if budgets:
                    avg_b  = sum(budgets) / len(budgets)
                    avg_s  = sum(spents)  / len(spents)
                    avg_v  = avg_b - avg_s
                    avg_var_str = (f"+{_fmt(avg_v)}" if avg_v > 0.005 else
                                   _fmt(avg_v) if avg_v < -0.005 else "✓")
                    row["avg_budget"]    = _fmt(avg_b) if avg_b > 0 else "—"
                    row["avg_spent"]     = _fmt(avg_s) if avg_s > 0 else "—"
                    row["avg_var"]       = avg_var_str
                    row["avg_var_color"] = ("#34d399" if avg_var_str.startswith("+") or avg_var_str == "✓"
                                            else "#f87171")
                    row["avg_status"]    = ("over" if avg_s > avg_b + 0.005 else
                                            "close" if avg_b > 0 and avg_s >= avg_b * 0.85 else
                                            "ok" if avg_s > 0 else "")
                bva_rows.append(row)

        self.bva_rows = bva_rows

        hdrs = [{"label": m["label"], "mid": m["mid"]} for m in monthly]
        while len(hdrs) < 3:
            hdrs.append({"label": "", "mid": ""})
        self.bva_month_hdrs = hdrs

        # ── Trends ───────────────────────────────────────────────────────
        self.trend_svg  = self._build_trend_svg(monthly)
        self.trend_rows = [
            {
                "label":        m["label"],
                "income_fmt":   _fmt(m["income"]),
                "spent_fmt":    _fmt(m["spent"]),
                "net_fmt":      _fmt(m["net"]),
                "net_color":    "#34d399" if m["net"] >= 0 else "#f87171",
                "savings_rate": f"{m['savings_rate']}%",
                "rate_color":   "#34d399" if m["savings_rate"] >= 10 else
                                "#fbbf24" if m["savings_rate"] >= 0 else "#f87171",
            }
            for m in monthly
        ]

        # ── Top Payees ────────────────────────────────────────────────────
        bkt_cat: dict[str, str] = {
            b["id"]: cat_map.get(b.get("catId", ""), {}).get("name", "")
            for b in all_buckets
        }
        # Group by lowercase key; track total, count, most common casing, and cat
        payee_totals:  dict[str, float] = {}
        payee_counts:  dict[str, int]   = {}
        payee_cats:    dict[str, str]   = {}
        payee_casing:  dict[str, dict[str, int]] = {}  # key → {casing: count}
        report_mid_set = {m["mid"] for m in monthly}
        for t in txs:
            if t.get("type") != "out" or t.get("monthId") not in report_mid_set:
                continue
            if is_scheduled(t):
                continue
            raw_desc = (t.get("desc") or "").strip() or "(no description)"
            key = raw_desc.lower()
            amt = float(t.get("amount") or 0)
            payee_totals[key] = payee_totals.get(key, 0.0) + amt
            payee_counts[key] = payee_counts.get(key, 0) + 1
            payee_casing.setdefault(key, {})[raw_desc] = payee_casing.get(key, {}).get(raw_desc, 0) + 1
            if key not in payee_cats:
                payee_cats[key] = bkt_cat.get(t.get("bucketId") or "", "")
        total_spend = sum(payee_totals.values()) or 1
        sorted_payees = sorted(payee_totals.items(), key=lambda x: -x[1])[:15]
        max_v = sorted_payees[0][1] if sorted_payees else 1
        self.payee_spend_rows = [
            {
                "payee":     max(payee_casing.get(k, {k: 1}), key=lambda c: payee_casing[k][c]),
                "total_fmt": _fmt(v),
                "count":     str(payee_counts.get(k, 0)),
                "pct_str":   f"{round(v / total_spend * 100)}%",
                "bar_w":     f"{round(v / max_v * 100)}%",
                "cat_name":  payee_cats.get(k, ""),
            }
            for k, v in sorted_payees
        ]

        # ── Debt Tracker ──────────────────────────────────────────────────
        debt_accounts = [a for a in accounts
                         if a.get("type") == "debt" and not a.get("archived")]
        debt_rows: list[dict] = []
        for a in debt_accounts:
            aid      = a["id"]
            cur_bal  = acct_balance(a, txs)
            payments = [t for t in txs if t.get("debtPaymentAccountId") == aid]
            total_paid = sum(float(t.get("amount", 0)) for t in payments)
            m_rows: list[dict] = []
            for m in monthly:
                m_paid = sum(
                    float(t.get("amount", 0)) for t in payments
                    if t.get("monthId") == m["mid"]
                )
                m_rows.append({
                    "label":    m["label"],
                    "paid_fmt": _fmt(m_paid) if m_paid > 0 else "—",
                })
            debt_rows.append({
                "name":             a.get("name", ""),
                "color":            a.get("color", "#818cf8"),
                "balance_fmt":      _fmt(abs(cur_bal)),
                "total_paid_fmt":   _fmt(total_paid),
                "payment_count":    str(len(payments)),
                "avg_payment_fmt":  (_fmt(total_paid / len(payments))
                                     if payments else "—"),
                "months":           m_rows,
            })
        self.debt_tracker_rows = debt_rows

    def _build_trend_svg(self, monthly: list[dict]) -> str:
        if not monthly:
            return ""
        W, H      = 520, 180
        bar_h_max = 100
        n         = len(monthly)
        pair_w    = 54
        gap       = (W - n * pair_w) // (n + 1)
        max_v     = max(max(m["income"], m["spent"]) for m in monthly) or 1.0

        def _scale(v: float) -> int:
            return max(3, round(abs(v) / max_v * bar_h_max))

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'preserveAspectRatio="xMidYMid meet" '
            f'style="width:100%;height:auto;font-family:system-ui,sans-serif;overflow:visible">'
        ]
        # Subtle gridlines
        for frac in (0.25, 0.5, 0.75, 1.0):
            y  = bar_h_max - round(frac * bar_h_max) + 8
            lv = max_v * frac
            lbl = f"${lv:,.0f}"
            parts.append(
                f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" '
                f'stroke="#ffffff0d" stroke-width="1"/>'
                f'<text x="2" y="{y - 2}" font-size="8" fill="#ffffff25">{lbl}</text>'
            )
        # Bars
        for i, m in enumerate(monthly):
            x  = gap + i * (pair_w + gap)
            ih = _scale(m["income"])
            sh = _scale(m["spent"])
            # Income bar (green)
            parts.append(
                f'<rect x="{x}" y="{bar_h_max - ih + 8}" '
                f'width="{pair_w // 2 - 2}" height="{ih}" '
                f'rx="3" fill="#34d399" opacity="0.85"/>'
            )
            # Spend bar (amber if under income, red if over)
            sc = "#fbbf24" if m["spent"] <= m["income"] else "#f87171"
            parts.append(
                f'<rect x="{x + pair_w // 2 + 2}" y="{bar_h_max - sh + 8}" '
                f'width="{pair_w // 2 - 2}" height="{sh}" '
                f'rx="3" fill="{sc}" opacity="0.85"/>'
            )
            # Month label
            parts.append(
                f'<text x="{x + pair_w // 2}" y="{bar_h_max + 24}" '
                f'text-anchor="middle" font-size="10" fill="#9090b0">{m["label"]}</text>'
            )
            # Net label
            net     = m["income"] - m["spent"]
            nc      = "#34d399" if net >= 0 else "#f87171"
            ns      = f"+${abs(net):,.0f}" if net >= 0 else f"-${abs(net):,.0f}"
            parts.append(
                f'<text x="{x + pair_w // 2}" y="{bar_h_max + 38}" '
                f'text-anchor="middle" font-size="8" fill="{nc}">{ns}</text>'
            )
        # Legend
        ly = H - 12
        parts.append(
            f'<rect x="8" y="{ly - 8}" width="10" height="8" rx="2" fill="#34d399" opacity="0.85"/>'
            f'<text x="22" y="{ly}" font-size="9" fill="#9090b0">Income</text>'
            f'<rect x="76" y="{ly - 8}" width="10" height="8" rx="2" fill="#fbbf24" opacity="0.85"/>'
            f'<text x="90" y="{ly}" font-size="9" fill="#9090b0">Spending</text>'
        )
        parts.append("</svg>")
        return "".join(parts)
