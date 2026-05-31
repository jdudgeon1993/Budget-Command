"""Insights panel — Forecast · Timeline · What-If."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS)

# ─────────────────────────────────────────────────────────────────────────────
#  Shared micro-components
# ─────────────────────────────────────────────────────────────────────────────

def _kpi(label: str, value: Any, color: str = TEXT) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={"font_size": "9px", "letter_spacing": "0.1em",
                               "text_transform": "uppercase", "color": TEXT3, "font_family": MONO}),
        rx.text(value, style={"font_size": "15px", "font_weight": "700",
                               "font_family": MONO, "color": color}),
        gap="2px", align_items="flex-start",
    )


def _kpi_card(*kpis) -> rx.Component:
    children = []
    for i, (label, value, color) in enumerate(kpis):
        if i > 0:
            children.append(rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}))
        children.append(_kpi(label, value, color))
    return rx.hstack(
        *children,
        gap="16px", width="100%", flex_wrap="wrap",
        style={"background": BG2, "border": f"1px solid {BORDER}",
               "border_radius": "10px", "padding": "14px 16px",
               "margin_bottom": "14px", "overflow": "hidden"},
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Sub-tab bar
# ─────────────────────────────────────────────────────────────────────────────

def _tab_btn(label: str, tab: str) -> rx.Component:
    active = AppState.insights_tab == tab
    return rx.box(
        label,
        on_click=AppState.set_insights_tab(tab),
        style=rx.cond(
            active,
            {"padding": "5px 16px", "border_radius": "20px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
             "background": ACCENT, "color": "#fff", "border": f"1px solid {ACCENT}"},
            {"padding": "5px 16px", "border_radius": "20px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
             "background": BG3, "color": TEXT3, "border": f"1px solid {BORDER}",
             "_hover": {"color": TEXT2, "border_color": BORDER2}},
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── FORECAST sub-panel ────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _range_btn(label: str, n: int) -> rx.Component:
    active = AppState.forecast_range == n
    return rx.box(
        label,
        on_click=AppState.set_forecast_range(n),
        style=rx.cond(
            active,
            {"padding": "4px 12px", "border_radius": "16px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
             "background": ACCENT, "color": "#fff", "border": f"1px solid {ACCENT}"},
            {"padding": "4px 12px", "border_radius": "16px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
             "background": BG3, "color": TEXT3, "border": f"1px solid {BORDER}",
             "_hover": {"color": TEXT2, "border_color": BORDER2}},
        ),
    )


def _acct_chip(a: dict) -> rx.Component:
    active = AppState.forecast_account == a["id"]
    return rx.box(
        rx.hstack(
            rx.box(style={"width": "8px", "height": "8px", "border_radius": "50%",
                          "background": a["color"], "flex_shrink": "0"}),
            rx.text(a["name"], style={"font_size": "11px"}),
            rx.text(a["balance_fmt"], style={"font_size": "10px", "font_family": MONO,
                                              "color": rx.cond(active, ACCENT, TEXT3)}),
            gap="6px", align_items="center",
        ),
        on_click=AppState.set_forecast_account(a["id"]),
        style=rx.cond(
            active,
            {"padding": "4px 10px", "border_radius": "20px", "cursor": "pointer",
             "border": f"1px solid {ACCENT}", "background": f"{ACCENT}18"},
            {"padding": "4px 10px", "border_radius": "20px", "cursor": "pointer",
             "border": f"1px solid {BORDER}", "background": BG3,
             "_hover": {"border_color": BORDER2}},
        ),
    )


def _forecast_row(r: dict) -> rx.Component:
    return rx.match(
        r["rt"],

        # Period header
        ("ph", rx.box(
            rx.hstack(
                rx.box(
                    rx.cond(r["pt"] == "gap", "GAP", "PAY"),
                    style={
                        "font_size": "8px", "font_family": MONO, "letter_spacing": "0.1em",
                        "padding": "2px 6px", "border_radius": "4px",
                        "background": rx.cond(r["pt"] == "gap", BG3, f"{ACCENT}22"),
                        "color": rx.cond(r["pt"] == "gap", TEXT3, ACCENT),
                        "border": rx.cond(r["pt"] == "gap",
                                          f"1px solid {BORDER}", f"1px solid {ACCENT}44"),
                        "flex_shrink": "0",
                    },
                ),
                rx.vstack(
                    rx.text(r["lbl"], style={"font_size": "13px", "font_weight": "600", "color": TEXT}),
                    rx.text(r["sub"], style={"font_size": "10px", "color": TEXT3}),
                    gap="1px", align_items="flex-start", flex="1",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.hstack(
                        rx.text(r["sgn"], style={"font_size": "12px", "font_family": MONO, "color": r["c1"]}),
                        rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": r["c1"]}),
                        gap="0px",
                    ),
                    rx.text(r["ebf"], style={"font_size": "14px", "font_weight": "700",
                                              "font_family": MONO,
                                              "color": rx.cond(r["ebn"] == "1", RED, TEXT)}),
                    gap="0px", align_items="flex-end",
                ),
                align_items="center", width="100%",
            ),
            style={
                "background": rx.cond(r["pt"] == "gap", BG3, BG2),
                "border": rx.cond(r["shf"] == "1", f"2px solid {RED}",
                                  rx.cond(r["pt"] == "gap", f"1px solid {BORDER}", f"1px solid {BORDER2}")),
                "border_radius": "10px 10px 0 0",
                "padding": "12px 14px 8px",
                "margin_top": "8px",
            },
        )),

        # Income line
        ("inc", rx.hstack(
            rx.text("💰", style={"font_size": "12px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
            width="100%", justify="between", align_items="center",
            style={"background": f"{GREEN}0a", "padding": "6px 14px",
                   "border_left": f"2px solid {GREEN}33", "border_right": f"1px solid {BORDER2}"},
        )),

        # Transfer line
        ("xfr", rx.hstack(
            rx.text("→", style={"font_size": "12px", "color": TEXT3, "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT2, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": AMBER}),
            width="100%", justify="between", align_items="center",
            style={"background": f"{AMBER}0a", "padding": "6px 14px",
                   "border_left": f"2px solid {AMBER}33", "border_right": f"1px solid {BORDER2}"},
        )),

        # Section header (funded / unfunded)
        ("sbh", rx.box(
            rx.text(r["lbl"], style={"font_size": "9px", "color": r["c1"], "letter_spacing": "0.1em",
                                      "text_transform": "uppercase", "font_family": MONO}),
            style={"padding": "6px 14px 2px",
                   "background": rx.cond(r["c1"] == "#34d399", f"{GREEN}08", f"{RED}08"),
                   "border_left": rx.cond(r["c1"] == "#34d399",
                                          f"2px solid {GREEN}44", f"2px solid {RED}44"),
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # Funded date
        ("fdt", rx.text(r["lbl"], style={"font_size": "9px", "color": TEXT3,
                                           "letter_spacing": "0.08em", "text_transform": "uppercase",
                                           "font_family": MONO, "padding": "4px 14px 0",
                                           "background": f"{GREEN}08",
                                           "border_left": f"2px solid {GREEN}33",
                                           "border_right": f"1px solid {BORDER2}"})),

        # Funded bill
        ("fbl", rx.hstack(
            rx.text("✓", style={"color": GREEN, "font_size": "11px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
            width="100%", justify="between", align_items="center",
            style={"padding": "4px 14px", "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33", "border_right": f"1px solid {BORDER2}"},
        )),

        # Funded balance
        ("fba", rx.hstack(
            rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
            rx.text(r["lbl"], style={"font_size": "11px", "font_family": MONO, "color": TEXT2}),
            width="100%", justify="between",
            style={"padding": "3px 14px 5px", "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33", "border_right": f"1px solid {BORDER2}",
                   "border_top": f"1px solid {GREEN}22"},
        )),

        # Unfunded date
        ("udt", rx.text(r["lbl"], style={"font_size": "9px", "color": TEXT3,
                                           "letter_spacing": "0.08em", "text_transform": "uppercase",
                                           "font_family": MONO, "padding": "4px 14px 0",
                                           "background": f"{RED}08",
                                           "border_left": f"2px solid {RED}33",
                                           "border_right": f"1px solid {BORDER2}"})),

        # Unfunded bill
        ("ubl", rx.hstack(
            rx.text("⚠", style={"color": AMBER, "font_size": "11px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": RED}),
            width="100%", justify="between", align_items="center",
            style={"padding": "4px 14px", "background": f"{RED}08",
                   "border_left": f"2px solid {RED}33", "border_right": f"1px solid {BORDER2}"},
        )),

        # Unfunded balance
        ("uba", rx.hstack(
            rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
            rx.text(r["lbl"], style={"font_size": "11px", "font_family": MONO,
                                      "color": rx.cond(r["neg"] == "1", RED, TEXT2)}),
            width="100%", justify="between",
            style={"padding": "3px 14px 5px", "background": f"{RED}08",
                   "border_left": f"2px solid {RED}33", "border_right": f"1px solid {BORDER2}",
                   "border_top": f"1px solid {RED}22"},
        )),

        # Period footer
        ("pf", rx.vstack(
            rx.hstack(
                rx.text("End Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
                rx.text(r["ebf"], style={"font_size": "14px", "font_weight": "700",
                                          "font_family": MONO,
                                          "color": rx.cond(r["ebn"] == "1", RED, TEXT)}),
                width="100%", justify="between",
            ),
            rx.hstack(
                rx.text("Safe to spend from here", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
                rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO,
                                          "color": r["c1"], "font_weight": "600"}),
                width="100%", justify="between",
            ),
            rx.cond(
                r["shf"] == "1",
                rx.text("⚠ Shortfall — balance goes negative",
                        style={"font_size": "10px", "color": RED, "font_family": MONO}),
                rx.box(),
            ),
            width="100%", gap="4px",
            style={"background": BG2,
                   "border": rx.cond(r["shf"] == "1", f"2px solid {RED}", f"1px solid {BORDER2}"),
                   "border_top": f"1px solid {BORDER}",
                   "border_radius": "0 0 10px 10px",
                   "padding": "10px 14px 12px", "margin_bottom": "2px"},
        )),

        rx.box(),
    )


def _forecast_subpanel() -> rx.Component:
    return rx.box(
        # Controls
        rx.vstack(
            rx.hstack(
                _range_btn("2 Mo", 2),
                _range_btn("3 Mo", 3),
                _range_btn("6 Mo", 6),
                _range_btn("12 Mo", 12),
                gap="6px",
            ),
            rx.cond(
                AppState.forecast_accounts.length() > 1,
                rx.hstack(
                    rx.box(
                        "All",
                        on_click=AppState.set_forecast_account(""),
                        style=rx.cond(
                            AppState.forecast_account == "",
                            {"padding": "4px 10px", "border_radius": "20px", "cursor": "pointer",
                             "border": f"1px solid {ACCENT}", "background": f"{ACCENT}18",
                             "font_size": "11px", "color": ACCENT},
                            {"padding": "4px 10px", "border_radius": "20px", "cursor": "pointer",
                             "border": f"1px solid {BORDER}", "background": BG3,
                             "font_size": "11px", "color": TEXT3,
                             "_hover": {"border_color": BORDER2}},
                        ),
                    ),
                    rx.foreach(AppState.forecast_accounts.to(list[dict[str, Any]]), _acct_chip),
                    gap="6px", flex_wrap="wrap",
                ),
                rx.box(),
            ),
            gap="10px", width="100%",
            style={"margin_bottom": "12px"},
        ),

        # KPI bar
        rx.cond(
            AppState.forecast_loading,
            rx.box(rx.text("Computing…", style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
                   style={"text_align": "center", "padding": "40px 0"}),
            rx.box(
                rx.hstack(
                    _kpi("Start Balance", AppState.fc_start_bal),
                    rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Total Income", AppState.fc_total_income, GREEN),
                    rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Unfunded", AppState.fc_total_unfunded, RED),
                    rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Safe to Spend", AppState.fc_safe_to_spend, AppState.fc_sts_color),
                    gap="16px", width="100%", flex_wrap="wrap",
                    style={"padding": "14px 16px"},
                ),
                rx.cond(
                    AppState.fc_shortfall_count > 0,
                    rx.box(
                        rx.text(AppState.forecast_shortfall_label,
                                style={"font_size": "11px", "color": RED, "font_family": MONO}),
                        style={"background": f"{RED}12", "padding": "6px 16px",
                               "border_top": f"1px solid {RED}33"},
                    ),
                    rx.box(),
                ),
                style={"background": BG2, "border": f"1px solid {BORDER}",
                       "border_radius": "10px", "margin_bottom": "12px", "overflow": "hidden"},
            ),
        ),

        # Forecast rows
        rx.cond(
            ~AppState.forecast_loading,
            rx.vstack(
                rx.foreach(AppState.forecast_rows.to(list[dict[str, Any]]), _forecast_row),
                width="100%", gap="0px",
            ),
            rx.box(),
        ),

        # Empty state
        rx.cond(
            AppState.forecast_rows.length() == 0,
            rx.box(
                rx.text("No paychecks configured", style={"color": TEXT3, "font_size": "12px"}),
                rx.text("Add a paycheck in Setup to see your forecast",
                        style={"color": TEXT3, "font_size": "11px", "margin_top": "4px"}),
                style={"text_align": "center", "padding": "60px 0"},
            ),
            rx.box(),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── TIMELINE sub-panel ───────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _tl_row(r: dict) -> rx.Component:
    return rx.match(
        r["rt"],

        # Week header
        ("wk", rx.hstack(
            rx.text(r["lbl"], style={"font_size": "11px", "font_weight": "600",
                                      "color": TEXT2, "flex": "1", "letter_spacing": "0.04em"}),
            rx.cond(
                r["wi"] != "",
                rx.hstack(
                    rx.text(r["wi"], style={"font_size": "11px", "font_family": MONO, "color": GREEN}),
                    rx.text("in", style={"font_size": "10px", "color": TEXT3}),
                    gap="4px", align_items="center",
                ),
                rx.box(),
            ),
            rx.cond(
                r["wb"] != "",
                rx.hstack(
                    rx.text(r["wb"], style={"font_size": "11px", "font_family": MONO, "color": AMBER}),
                    rx.text("bills", style={"font_size": "10px", "color": TEXT3}),
                    gap="4px", align_items="center",
                ),
                rx.box(),
            ),
            align_items="center", width="100%",
            style={"background": BG3, "border": f"1px solid {BORDER}",
                   "border_radius": "8px", "padding": "8px 12px",
                   "margin_top": "10px"},
        )),

        # Day header
        ("dh", rx.hstack(
            rx.box(
                rx.text(r["dn"], style={"font_size": "18px", "font_weight": "700",
                                         "font_family": MONO, "line_height": "1",
                                         "color": rx.cond(r["td"] == "1", ACCENT, TEXT)}),
                rx.text(r["wd"], style={"font_size": "9px", "color": TEXT3,
                                         "text_transform": "uppercase", "letter_spacing": "0.08em",
                                         "font_family": MONO}),
                style={"text_align": "center", "min_width": "36px"},
            ),
            rx.box(style={"width": "1px", "background": BORDER, "height": "32px", "flex_shrink": "0"}),
            rx.box(style={"flex": "1"}),
            rx.cond(
                r["td"] == "1",
                rx.box("Today", style={"font_size": "9px", "color": ACCENT, "font_family": MONO,
                                        "letter_spacing": "0.08em",
                                        "background": f"{ACCENT}18",
                                        "border": f"1px solid {ACCENT}44",
                                        "border_radius": "4px", "padding": "2px 6px"}),
                rx.box(),
            ),
            rx.cond(
                r["pa"] == "1",
                rx.box("Past", style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                                       "letter_spacing": "0.08em"}),
                rx.box(),
            ),
            align_items="center", gap="10px", width="100%",
            style={"padding": "6px 12px 2px"},
        )),

        # Paycheck event
        ("pc", rx.hstack(
            rx.box(style={"width": "36px", "flex_shrink": "0"}),
            rx.box(style={"width": "1px", "background": BORDER, "height": "100%", "flex_shrink": "0"}),
            rx.text("💰", style={"font_size": "11px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "13px", "font_family": MONO,
                                      "color": GREEN, "font_weight": "600"}),
            align_items="center", gap="8px", width="100%",
            style={"padding": "3px 12px",
                   "background": f"{GREEN}0a",
                   "border_left": f"3px solid {GREEN}44"},
        )),

        # Bill event
        ("bl", rx.hstack(
            rx.box(style={"width": "36px", "flex_shrink": "0"}),
            rx.box(style={"width": "1px", "background": BORDER, "height": "100%", "flex_shrink": "0"}),
            rx.cond(
                r["pd"] == "1",
                rx.text("✓", style={"color": GREEN, "font_size": "11px", "flex_shrink": "0"}),
                rx.text("·", style={"color": RED, "font_size": "18px", "flex_shrink": "0",
                                     "line_height": "1"}),
            ),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO,
                                      "color": rx.cond(r["pd"] == "1", TEXT3, RED)}),
            align_items="center", gap="8px", width="100%",
            style={"padding": "3px 12px",
                   "background": rx.cond(r["pd"] == "1", "transparent", f"{RED}07"),
                   "border_left": rx.cond(r["pd"] == "1",
                                          f"3px solid {GREEN}33",
                                          f"3px solid {RED}55")},
        )),

        rx.box(),
    )


def _hitter_row(h: dict) -> rx.Component:
    return rx.hstack(
        rx.cond(
            h["paid"] == "1",
            rx.text("✓", style={"color": GREEN, "font_size": "11px", "flex_shrink": "0", "width": "16px"}),
            rx.text("·", style={"color": RED, "font_size": "18px", "flex_shrink": "0",
                                  "line_height": "1", "width": "16px"}),
        ),
        rx.text(h["name"], style={"font_size": "13px", "color": TEXT, "flex": "1"}),
        rx.box(
            rx.box(style={"height": "4px", "border_radius": "2px", "width": h["pct"],
                           "background": rx.cond(h["paid"] == "1", GREEN, RED),
                           "max_width": "100%"}),
            style={"width": "80px", "background": BG3, "border_radius": "2px",
                   "overflow": "hidden", "flex_shrink": "0"},
        ),
        rx.text(h["amount_fmt"], style={"font_size": "12px", "font_family": MONO,
                                         "color": rx.cond(h["paid"] == "1", TEXT2, RED),
                                         "min_width": "60px", "text_align": "right"}),
        align_items="center", gap="10px", width="100%",
        style={"padding": "6px 0"},
    )


def _timeline_subpanel() -> rx.Component:
    return rx.box(
        # Summary KPI bar
        rx.hstack(
            _kpi("Income", AppState.tl_income_fmt, GREEN),
            rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
            _kpi("Total Bills", AppState.tl_bills_fmt, TEXT),
            rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
            _kpi("Paid", AppState.tl_paid_fmt, GREEN),
            rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
            _kpi("Remaining", AppState.tl_remaining_fmt, AMBER),
            rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
            _kpi("Daily Burn", AppState.tl_burn_fmt, TEXT3),
            gap="16px", width="100%", flex_wrap="wrap",
            style={"background": BG2, "border": f"1px solid {BORDER}",
                   "border_radius": "10px", "padding": "14px 16px",
                   "margin_bottom": "14px", "overflow": "hidden"},
        ),

        # Top hitters card
        rx.cond(
            AppState.tl_hitters.length() > 0,
            rx.box(
                rx.text("Top Bills", style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.1em",
                                             "text_transform": "uppercase", "font_family": MONO,
                                             "margin_bottom": "8px"}),
                rx.vstack(
                    rx.foreach(AppState.tl_hitters.to(list[dict[str, Any]]), _hitter_row),
                    width="100%", gap="0px",
                ),
                style={"background": BG2, "border": f"1px solid {BORDER}",
                       "border_radius": "10px", "padding": "14px 16px",
                       "margin_bottom": "14px"},
            ),
            rx.box(),
        ),

        # Week-by-week rows
        rx.cond(
            AppState.tl_rows.length() > 0,
            rx.vstack(
                rx.foreach(AppState.tl_rows.to(list[dict[str, Any]]), _tl_row),
                width="100%", gap="0px",
            ),
            rx.box(
                rx.text("No income or bills this month",
                        style={"color": TEXT3, "font_size": "12px"}),
                style={"text_align": "center", "padding": "60px 0"},
            ),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── WHAT-IF sub-panel ────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _wi_forecast_row(r: dict) -> rx.Component:
    return _forecast_row(r)


def _whatif_subpanel() -> rx.Component:
    return rx.box(
        # Controls
        rx.hstack(
            rx.vstack(
                rx.text("Monthly Income Override",
                        style={"font_size": "11px", "color": TEXT3, "font_family": MONO,
                               "letter_spacing": "0.06em", "text_transform": "uppercase"}),
                rx.hstack(
                    rx.input(
                        placeholder=f"e.g. 5000",
                        value=AppState.wi_income_str,
                        on_change=AppState.set_wi_income,
                        style={"background": BG3, "border": f"1px solid {BORDER}",
                               "border_radius": "8px", "padding": "8px 12px",
                               "color": TEXT, "font_family": MONO, "font_size": "13px",
                               "width": "180px",
                               "_focus": {"border_color": ACCENT, "outline": "none"}},
                    ),
                    rx.cond(
                        AppState.wi_active,
                        rx.box(
                            "Reset",
                            on_click=AppState.reset_whatif,
                            style={"padding": "8px 14px", "border_radius": "8px",
                                   "cursor": "pointer", "font_size": "12px",
                                   "background": f"{RED}18", "color": RED,
                                   "border": f"1px solid {RED}44",
                                   "_hover": {"background": f"{RED}28"}},
                        ),
                        rx.box(),
                    ),
                    gap="8px", align_items="center",
                ),
                gap="6px", align_items="flex-start",
            ),
            rx.spacer(),
            rx.cond(
                AppState.wi_active,
                rx.box(
                    "SCENARIO ACTIVE",
                    style={"font_size": "9px", "font_family": MONO, "letter_spacing": "0.12em",
                           "color": AMBER, "background": f"{AMBER}18",
                           "border": f"1px solid {AMBER}44",
                           "border_radius": "6px", "padding": "4px 10px"},
                ),
                rx.box(),
            ),
            align_items="flex-start", width="100%",
            style={"background": BG2, "border": f"1px solid {BORDER}",
                   "border_radius": "10px", "padding": "14px 16px",
                   "margin_bottom": "14px"},
        ),

        # KPI bar — shows what-if results vs baseline
        rx.cond(
            AppState.wi_active,
            rx.box(
                rx.hstack(
                    _kpi("Start Balance", AppState.wi_start_bal),
                    rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Total Income", AppState.wi_total_income, GREEN),
                    rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Unfunded", AppState.wi_total_unfunded, RED),
                    rx.box(style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Safe to Spend", AppState.wi_safe_to_spend, AppState.wi_sts_color),
                    gap="16px", width="100%", flex_wrap="wrap",
                    style={"padding": "14px 16px"},
                ),
                style={"background": BG2, "border": f"1px solid {AMBER}44",
                       "border_radius": "10px", "margin_bottom": "14px", "overflow": "hidden"},
            ),
            rx.box(
                rx.text("Enter a monthly income override above to run a What-If scenario.",
                        style={"color": TEXT3, "font_size": "12px"}),
                rx.text("The full forecast will recompute instantly with your adjusted numbers.",
                        style={"color": TEXT3, "font_size": "11px", "margin_top": "4px"}),
                style={"text_align": "center", "padding": "40px 0"},
            ),
        ),

        # What-if forecast rows
        rx.cond(
            AppState.wi_active,
            rx.vstack(
                rx.foreach(AppState.wi_rows.to(list[dict[str, Any]]), _wi_forecast_row),
                width="100%", gap="0px",
            ),
            rx.box(),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── Main insights panel ──────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def forecast_panel() -> rx.Component:
    return rx.box(
        # Sub-tab bar
        rx.hstack(
            _tab_btn("Forecast", "forecast"),
            _tab_btn("Timeline", "timeline"),
            _tab_btn("What-If", "whatif"),
            gap="6px",
            style={"margin_bottom": "16px"},
        ),

        # Active sub-panel
        rx.cond(
            AppState.insights_tab == "timeline",
            _timeline_subpanel(),
            rx.cond(
                AppState.insights_tab == "whatif",
                _whatif_subpanel(),
                _forecast_subpanel(),
            ),
        ),
    )
