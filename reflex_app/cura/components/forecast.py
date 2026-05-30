"""Forecast panel — paycheck-by-paycheck cash flow projection."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3, GREEN, AMBER, ACCENT, RED, MONO, SANS


# ── Range / account controls ──────────────────────────────────────────────────

def _range_btn(label: str, n: int) -> rx.Component:
    active = AppState.forecast_range == n
    return rx.box(
        label,
        on_click=AppState.set_forecast_range(n),
        style=rx.cond(
            active,
            {"padding": "5px 14px", "border_radius": "20px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
             "background": ACCENT, "color": "#fff", "border": f"1px solid {ACCENT}"},
            {"padding": "5px 14px", "border_radius": "20px", "cursor": "pointer",
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
            rx.text(a["balance_fmt"],
                    style={"font_size": "10px", "font_family": MONO,
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


def _kpi(label: str, value: str, color: str = TEXT) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={"font_size": "9px", "letter_spacing": "0.1em",
                               "text_transform": "uppercase", "color": TEXT3, "font_family": MONO}),
        rx.text(value, style={"font_size": "16px", "font_weight": "700",
                               "font_family": MONO, "color": color}),
        gap="2px", align_items="flex-start",
    )


# ── Flat row renderer ─────────────────────────────────────────────────────────
# Each row dict has: rt, lbl, sub, amt, c1, c2, neg, shf, pid, pt, ebf, ebn, sgn

def _forecast_row(r: dict) -> rx.Component:
    return rx.match(
        r["rt"],

        # ── Period header ─────────────────────────────────────────────────────
        ("ph", rx.box(
            rx.hstack(
                # Type badge
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
                # Label + date range
                rx.vstack(
                    rx.text(r["lbl"], style={"font_size": "13px", "font_weight": "600",
                                              "color": TEXT}),
                    rx.text(r["sub"], style={"font_size": "10px", "color": TEXT3}),
                    gap="1px", align_items="flex-start", flex="1",
                ),
                rx.spacer(),
                # Net + end balance
                rx.vstack(
                    rx.hstack(
                        rx.text(r["sgn"], style={"font_size": "12px", "font_family": MONO,
                                                  "color": r["c1"]}),
                        rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO,
                                                  "color": r["c1"]}),
                        gap="0px",
                    ),
                    rx.text(r["ebf"],
                            style={"font_size": "14px", "font_weight": "700",
                                   "font_family": MONO,
                                   "color": rx.cond(r["ebn"] == "1", RED, TEXT)}),
                    gap="0px", align_items="flex-end",
                ),
                align_items="center", width="100%",
            ),
            style={
                "background": rx.cond(r["pt"] == "gap", BG3, BG2),
                "border": rx.cond(r["shf"] == "1",
                                  f"2px solid {RED}",
                                  rx.cond(r["pt"] == "gap",
                                          f"1px solid {BORDER}",
                                          f"1px solid {BORDER2}")),
                "border_radius": "10px 10px 0 0",
                "padding": "12px 14px 8px",
                "margin_top": "8px",
            },
        )),

        # ── Income line ───────────────────────────────────────────────────────
        ("inc", rx.hstack(
            rx.text("💰", style={"font_size": "12px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
            width="100%", justify="between", align_items="center",
            style={"background": f"{GREEN}0a", "padding": "6px 14px",
                   "border_left": f"2px solid {GREEN}33",
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # ── Transfer line ─────────────────────────────────────────────────────
        ("xfr", rx.hstack(
            rx.text("→", style={"font_size": "12px", "color": TEXT3, "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT2, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": AMBER}),
            width="100%", justify="between", align_items="center",
            style={"background": f"{AMBER}0a", "padding": "6px 14px",
                   "border_left": f"2px solid {AMBER}33",
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # ── Section header (funded / unfunded) ────────────────────────────────
        ("sbh", rx.box(
            rx.text(r["lbl"],
                    style={"font_size": "9px", "color": r["c1"], "letter_spacing": "0.1em",
                           "text_transform": "uppercase", "font_family": MONO}),
            style={"padding": "6px 14px 2px",
                   "background": rx.cond(r["c1"] == "#34d399", f"{GREEN}08", f"{RED}08"),
                   "border_left": rx.cond(r["c1"] == "#34d399",
                                          f"2px solid {GREEN}44", f"2px solid {RED}44"),
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # ── Funded date ───────────────────────────────────────────────────────
        ("fdt", rx.text(
            r["lbl"],
            style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.08em",
                   "text_transform": "uppercase", "font_family": MONO,
                   "padding": "4px 14px 0",
                   "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33",
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # ── Funded bill ───────────────────────────────────────────────────────
        ("fbl", rx.hstack(
            rx.text("✓", style={"color": GREEN, "font_size": "11px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
            width="100%", justify="between", align_items="center",
            style={"padding": "4px 14px",
                   "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33",
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # ── Funded running balance ────────────────────────────────────────────
        ("fba", rx.hstack(
            rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
            rx.text(r["lbl"], style={"font_size": "11px", "font_family": MONO, "color": TEXT2}),
            width="100%", justify="between",
            style={"padding": "3px 14px 5px",
                   "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33",
                   "border_right": f"1px solid {BORDER2}",
                   "border_top": f"1px solid {GREEN}22"},
        )),

        # ── Unfunded date ─────────────────────────────────────────────────────
        ("udt", rx.text(
            r["lbl"],
            style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.08em",
                   "text_transform": "uppercase", "font_family": MONO,
                   "padding": "4px 14px 0",
                   "background": f"{RED}08",
                   "border_left": f"2px solid {RED}33",
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # ── Unfunded bill ─────────────────────────────────────────────────────
        ("ubl", rx.hstack(
            rx.text("⚠", style={"color": AMBER, "font_size": "11px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": RED}),
            width="100%", justify="between", align_items="center",
            style={"padding": "4px 14px",
                   "background": f"{RED}08",
                   "border_left": f"2px solid {RED}33",
                   "border_right": f"1px solid {BORDER2}"},
        )),

        # ── Unfunded running balance ──────────────────────────────────────────
        ("uba", rx.hstack(
            rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
            rx.text(r["lbl"],
                    style={"font_size": "11px", "font_family": MONO,
                           "color": rx.cond(r["neg"] == "1", RED, TEXT2)}),
            width="100%", justify="between",
            style={"padding": "3px 14px 5px",
                   "background": f"{RED}08",
                   "border_left": f"2px solid {RED}33",
                   "border_right": f"1px solid {BORDER2}",
                   "border_top": f"1px solid {RED}22"},
        )),

        # ── Period footer ─────────────────────────────────────────────────────
        ("pf", rx.vstack(
            rx.hstack(
                rx.text("End Balance",
                        style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
                rx.text(r["ebf"],
                        style={"font_size": "14px", "font_weight": "700", "font_family": MONO,
                               "color": rx.cond(r["ebn"] == "1", RED, TEXT)}),
                width="100%", justify="between",
            ),
            rx.hstack(
                rx.text("Safe to spend from here",
                        style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
                rx.text(r["amt"],
                        style={"font_size": "12px", "font_family": MONO,
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
            style={
                "background": BG2,
                "border": rx.cond(r["shf"] == "1",
                                  f"2px solid {RED}", f"1px solid {BORDER2}"),
                "border_top": f"1px solid {BORDER}",
                "border_radius": "0 0 10px 10px",
                "padding": "10px 14px 12px",
                "margin_bottom": "2px",
            },
        )),

        rx.box(),  # default: unknown rt
    )


# ── Main panel ────────────────────────────────────────────────────────────────

def forecast_panel() -> rx.Component:
    return rx.box(
        # Controls bar
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
                    rx.foreach(
                        AppState.forecast_accounts.to(list[dict[str, Any]]),
                        _acct_chip,
                    ),
                    gap="6px", flex_wrap="wrap",
                ),
                rx.box(),
            ),
            gap="10px", width="100%",
            style={"margin_bottom": "12px"},
        ),

        # Summary KPI bar
        rx.cond(
            AppState.forecast_loading,
            rx.box(
                rx.text("Computing forecast…",
                        style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
                style={"text_align": "center", "padding": "40px 0"},
            ),
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
                        rx.text(
                            AppState.forecast_shortfall_label,
                            style={"font_size": "11px", "color": RED, "font_family": MONO},
                        ),
                        style={"background": f"{RED}12", "padding": "6px 16px",
                               "border_top": f"1px solid {RED}33"},
                    ),
                    rx.box(),
                ),
                style={"background": BG2, "border": f"1px solid {BORDER}",
                       "border_radius": "10px", "margin_bottom": "12px",
                       "overflow": "hidden"},
            ),
        ),

        # Flat forecast rows
        rx.cond(
            ~AppState.forecast_loading,
            rx.vstack(
                rx.foreach(
                    AppState.forecast_rows.to(list[dict[str, Any]]),
                    _forecast_row,
                ),
                width="100%", gap="0px",
            ),
            rx.box(),
        ),

        # Empty state
        rx.cond(
            AppState.forecast_rows.length() == 0,
            rx.box(
                rx.text("No paychecks configured",
                        style={"color": TEXT3, "font_size": "12px"}),
                rx.text("Add a paycheck in Setup to see your forecast",
                        style={"color": TEXT3, "font_size": "11px", "margin_top": "4px"}),
                style={"text_align": "center", "padding": "60px 0"},
            ),
            rx.box(),
        ),
    )
