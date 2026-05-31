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
                               "text_transform": "uppercase", "color": TEXT3,
                               "font_family": MONO}),
        rx.text(value, style={"font_size": "15px", "font_weight": "700",
                               "font_family": MONO, "color": color}),
        gap="2px", align_items="flex_start",
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
#  ── FORECAST sub-panel ───────────────────────────────────────────────────────
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


def _body_row(r: dict) -> rx.Component:
    """Render a single body row inside a period card."""
    return rx.match(
        r["rt"],

        # ── Start balance ────────────────────────────────────────────────────
        ("sb", rx.hstack(
            rx.text("START", style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                                     "letter_spacing": "0.1em", "flex_shrink": "0"}),
            rx.spacer(),
            rx.text(r["lbl"], style={"font_size": "11px", "font_family": MONO, "color": TEXT2}),
            width="100%", align_items="center",
            style={"padding": "5px 14px", "background": BG3,
                   "border_left": f"2px solid {BORDER2}"},
        )),

        # ── Income line ──────────────────────────────────────────────────────
        ("inc", rx.hstack(
            rx.text("💰", style={"font_size": "12px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
            width="100%", justify="between", align_items="center",
            style={"background": f"{GREEN}0a", "padding": "6px 14px",
                   "border_left": f"2px solid {GREEN}55"},
        )),

        # ── Transfer line ────────────────────────────────────────────────────
        ("xfr", rx.hstack(
            rx.text("→", style={"font_size": "12px", "color": TEXT3, "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT2, "flex": "1"}),
            rx.vstack(
                rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": AMBER}),
                rx.cond(
                    r["cum"] != "",
                    rx.text(r["cum"], style={"font_size": "9px", "color": TEXT3,
                                              "font_family": MONO}),
                    rx.box(),
                ),
                align_items="flex_end", gap="1px",
            ),
            width="100%", justify="between", align_items="center",
            style={"background": f"{AMBER}0a", "padding": "5px 14px",
                   "border_left": f"2px solid {AMBER}44"},
        )),

        # ── Alloc event ──────────────────────────────────────────────────────
        ("ae", rx.hstack(
            rx.cond(
                r["sub2"] == "vault",
                rx.text("→", style={"font_size": "11px", "color": AMBER, "flex_shrink": "0"}),
                rx.text("≈", style={"font_size": "11px", "color": TEXT3, "flex_shrink": "0"}),
            ),
            rx.text(r["lbl"], style={"font_size": "12px", "flex": "1",
                                      "color": rx.cond(r["sub2"] == "vault", TEXT2, TEXT3)}),
            rx.cond(
                r["sub2"] == "vault",
                rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO,
                                          "color": AMBER}),
                rx.text(r["amt"], style={"font_size": "11px", "font_family": MONO,
                                          "color": TEXT3, "font_style": "italic"}),
            ),
            width="100%", justify="between", align_items="center",
            style={
                "padding": "4px 14px",
                "background": rx.cond(r["sub2"] == "vault", f"{AMBER}07", "transparent"),
                "border_left": rx.cond(r["sub2"] == "vault",
                                        f"2px solid {AMBER}33",
                                        f"2px solid {BORDER}"),
            },
        )),

        # ── Balance after transfers divider ──────────────────────────────────
        ("bat", rx.hstack(
            rx.text("BAL AFTER TRANSFERS", style={
                "font_size": "8px", "color": TEXT3, "font_family": MONO,
                "letter_spacing": "0.1em", "flex_shrink": "0",
            }),
            rx.spacer(),
            rx.text(r["lbl"], style={"font_size": "12px", "font_weight": "600",
                                      "font_family": MONO, "color": TEXT2}),
            width="100%", align_items="center",
            style={"padding": "6px 14px",
                   "background": BG3,
                   "border_top": f"1px solid {BORDER}",
                   "border_bottom": f"1px solid {BORDER}",
                   "border_left": f"2px solid {BORDER2}"},
        )),

        # ── Section header (funded / unfunded) ───────────────────────────────
        ("sbh", rx.box(
            rx.text(r["lbl"], style={"font_size": "9px", "color": r["c1"],
                                      "letter_spacing": "0.1em",
                                      "text_transform": "uppercase", "font_family": MONO}),
            style={"padding": "6px 14px 2px",
                   "background": rx.cond(r["c1"] == "#34d399", f"{GREEN}08", f"{RED}08"),
                   "border_left": rx.cond(r["c1"] == "#34d399",
                                          f"2px solid {GREEN}44", f"2px solid {RED}44")},
        )),

        # ── Funded date label ────────────────────────────────────────────────
        ("fdt", rx.text(r["lbl"],
                        style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.08em",
                               "text_transform": "uppercase", "font_family": MONO,
                               "padding": "4px 14px 0",
                               "background": f"{GREEN}08",
                               "border_left": f"2px solid {GREEN}33"})),

        # ── Funded bill ──────────────────────────────────────────────────────
        ("fbl", rx.hstack(
            rx.text("✓", style={"color": GREEN, "font_size": "11px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
            width="100%", justify="between", align_items="center",
            style={"padding": "4px 14px", "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33"},
        )),

        # ── Funded running balance ───────────────────────────────────────────
        ("fba", rx.hstack(
            rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
            rx.text(r["lbl"], style={"font_size": "11px", "font_family": MONO, "color": TEXT2}),
            width="100%", justify="between",
            style={"padding": "3px 14px 6px", "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33",
                   "border_top": f"1px solid {GREEN}22"},
        )),

        # ── Unfunded date label ──────────────────────────────────────────────
        ("udt", rx.text(r["lbl"],
                        style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.08em",
                               "text_transform": "uppercase", "font_family": MONO,
                               "padding": "4px 14px 0",
                               "background": f"{RED}08",
                               "border_left": f"2px solid {RED}33"})),

        # ── Unfunded bill ────────────────────────────────────────────────────
        ("ubl", rx.hstack(
            rx.text("⚠", style={"color": AMBER, "font_size": "11px", "flex_shrink": "0"}),
            rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
            rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO, "color": RED}),
            width="100%", justify="between", align_items="center",
            style={"padding": "4px 14px", "background": f"{RED}08",
                   "border_left": f"2px solid {RED}55"},
        )),

        # ── Unfunded running balance ─────────────────────────────────────────
        ("uba", rx.hstack(
            rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
            rx.text(r["lbl"], style={"font_size": "11px", "font_family": MONO,
                                      "color": rx.cond(r["neg"] == "1", RED, TEXT2)}),
            width="100%", justify="between",
            style={"padding": "3px 14px 6px", "background": f"{RED}08",
                   "border_left": f"2px solid {RED}33",
                   "border_top": f"1px solid {RED}22"},
        )),

        # ── Period footer ────────────────────────────────────────────────────
        ("pf", rx.vstack(
            rx.hstack(
                rx.text("END", style={"font_size": "9px", "color": TEXT3,
                                       "font_family": MONO, "letter_spacing": "0.1em",
                                       "flex": "1"}),
                rx.text(r["ebf"], style={"font_size": "15px", "font_weight": "700",
                                          "font_family": MONO,
                                          "color": rx.cond(r["ebn"] == "1", RED, TEXT)}),
                width="100%", justify="between",
            ),
            rx.hstack(
                rx.text("Safe to Spend from here",
                        style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
                rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO,
                                          "color": r["c1"], "font_weight": "600"}),
                width="100%", justify="between",
            ),
            rx.cond(
                r["shf"] == "1",
                rx.text("⚠ Balance goes negative — shortfall",
                        style={"font_size": "10px", "color": RED, "font_family": MONO}),
                rx.box(),
            ),
            width="100%", gap="4px",
            style={"background": BG2,
                   "border_top": f"1px solid {BORDER}",
                   "padding": "10px 14px 12px"},
        )),

        rx.box(),
    )


def _period_card(p: dict) -> rx.Component:
    """Render a single forecast period as a collapsible card."""
    header = rx.box(
        rx.hstack(
            # Left: type badge + title + date range + badges
            rx.hstack(
                rx.box(
                    rx.cond(p["pt"] == "gap", "GAP", "PAY"),
                    style={
                        "font_size": "8px", "font_family": MONO, "letter_spacing": "0.1em",
                        "padding": "2px 6px", "border_radius": "4px",
                        "background": rx.cond(p["pt"] == "gap", BG3, f"{ACCENT}22"),
                        "color": rx.cond(p["pt"] == "gap", TEXT3, ACCENT),
                        "border": rx.cond(p["pt"] == "gap",
                                          f"1px solid {BORDER}", f"1px solid {ACCENT}44"),
                        "flex_shrink": "0",
                    },
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(p["lbl"], style={"font_size": "13px", "font_weight": "600",
                                                  "color": TEXT, "line_height": "1.2"}),
                        # Pre-funded badge
                        rx.cond(
                            (p["tbc"] != "0") & (p["tbc"] != "") & (p["shf"] == ""),
                            rx.box(
                                rx.cond(
                                    p["pfc"] == p["tbc"],
                                    "✓ All Funded",
                                    rx.fragment(p["pfc"], "/", p["tbc"], " Funded"),
                                ),
                                style={
                                    "font_size": "8px", "font_family": MONO,
                                    "padding": "1px 5px", "border_radius": "4px",
                                    "color": rx.cond(p["pfc"] == p["tbc"], GREEN, AMBER),
                                    "border": rx.cond(p["pfc"] == p["tbc"],
                                                      f"1px solid {GREEN}55",
                                                      f"1px solid {AMBER}55"),
                                    "background": rx.cond(p["pfc"] == p["tbc"],
                                                          f"{GREEN}12", f"{AMBER}12"),
                                    "flex_shrink": "0",
                                },
                            ),
                            rx.box(),
                        ),
                        # Shortfall badge
                        rx.cond(
                            p["shf"] == "1",
                            rx.box(
                                "⚠ SHORTFALL",
                                style={"font_size": "8px", "font_family": MONO,
                                       "padding": "1px 5px", "border_radius": "4px",
                                       "color": RED, "background": f"{RED}18",
                                       "border": f"1px solid {RED}44", "flex_shrink": "0"},
                            ),
                            rx.box(),
                        ),
                        gap="6px", align_items="center", flex_wrap="wrap",
                    ),
                    rx.text(p["sub"], style={"font_size": "10px", "color": TEXT3,
                                              "line_height": "1.2"}),
                    gap="3px", align_items="flex_start", flex="1",
                ),
                gap="8px", align_items="flex_start", flex="1",
            ),
            # Right: net amount + end balance + chevron
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(p["sgn"], style={"font_size": "11px", "font_family": MONO,
                                                  "color": p["c1"]}),
                        rx.text(p["amt"], style={"font_size": "11px", "font_family": MONO,
                                                  "color": p["c1"]}),
                        gap="0px",
                    ),
                    rx.text(p["ebf"], style={"font_size": "14px", "font_weight": "700",
                                              "font_family": MONO,
                                              "color": rx.cond(p["ebn"] == "1", RED, TEXT)}),
                    gap="0px", align_items="flex_end",
                ),
                rx.text(
                    rx.cond(p["is_open"] == "1", "▾", "▸"),
                    style={"font_size": "14px", "color": TEXT3, "flex_shrink": "0",
                           "padding_left": "6px"},
                ),
                align_items="center", gap="4px",
            ),
            align_items="flex_start", width="100%",
        ),
        on_click=AppState.toggle_period_collapse(p["pid"]),
        style={
            "background": rx.cond(p["pt"] == "gap", BG3, BG2),
            "padding": "12px 14px 10px",
            "cursor": "pointer",
            "_hover": {"opacity": "0.92"},
        },
    )

    body = rx.cond(
        p["is_open"] == "1",
        rx.box(
            rx.foreach(p["rows"].to(list[dict[str, Any]]), _body_row),
            style={"border_top": f"1px solid {BORDER}"},
        ),
        rx.box(),
    )

    return rx.box(
        header,
        body,
        style={
            "border": rx.cond(p["shf"] == "1",
                              f"2px solid {RED}44", f"1px solid {BORDER2}"),
            "border_radius": "10px",
            "overflow": "hidden",
            "margin_bottom": "10px",
        },
    )


def _forecast_subpanel() -> rx.Component:
    return rx.box(
        # Controls row: range buttons + account chips
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
            rx.box(rx.text("Computing…", style={"color": TEXT3, "font_size": "12px",
                                                  "font_family": MONO}),
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
                       "border_radius": "10px", "margin_bottom": "16px", "overflow": "hidden"},
            ),
        ),

        # Period cards
        rx.cond(
            ~AppState.forecast_loading,
            rx.box(
                rx.foreach(AppState.forecast_periods.to(list[dict[str, Any]]), _period_card),
                width="100%",
            ),
            rx.box(),
        ),

        # Empty state
        rx.cond(
            AppState.forecast_periods.length() == 0,
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


# ─────────────────────────────────────────────────────────────────────────────
#  ── TIMELINE sub-panel — 60-day event feed ───────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _tl_row(r: dict) -> rx.Component:
    return rx.match(
        r["rt"],

        # Day header
        ("day", rx.hstack(
            rx.text(r["lbl"], style={
                "font_size": "12px", "font_weight": "600",
                "color": rx.cond(r["td"] == "1", ACCENT, TEXT2),
                "letter_spacing": "0.04em",
                "flex": "1",
            }),
            rx.cond(
                r["td"] == "1",
                rx.box("Today", style={"font_size": "9px", "color": ACCENT, "font_family": MONO,
                                        "background": f"{ACCENT}18", "border": f"1px solid {ACCENT}44",
                                        "border_radius": "4px", "padding": "2px 6px"}),
                rx.box(),
            ),
            align_items="center", width="100%",
            style={"padding": "10px 0 4px",
                   "border_bottom": f"1px solid {BORDER}",
                   "margin_top": "8px"},
        )),

        # Paycheck event
        ("paycheck", rx.hstack(
            rx.box(style={"width": "10px", "height": "10px", "border_radius": "50%",
                          "background": GREEN, "flex_shrink": "0", "margin_top": "2px"}),
            rx.vstack(
                rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "font_weight": "500"}),
                rx.text("Paycheck", style={"font_size": "10px", "color": TEXT3,
                                            "font_family": MONO}),
                gap="1px", align_items="flex_start",
            ),
            rx.spacer(),
            rx.text(r["amt"], style={"font_size": "13px", "font_family": MONO,
                                      "color": GREEN, "font_weight": "600"}),
            align_items="flex_start", gap="10px", width="100%",
            style={"padding": "8px 0 6px", "border_bottom": f"1px solid {BORDER}33"},
        )),

        # Bill event
        ("bill", rx.hstack(
            rx.box(style={
                "width": "10px", "height": "10px", "border_radius": "50%",
                "background": rx.cond(r["pd"] == "1", TEXT3, rx.cond(r["pa"] == "1", TEXT3, RED)),
                "flex_shrink": "0", "margin_top": "2px",
                "opacity": rx.cond(r["pa"] == "1", "0.5", "1"),
            }),
            rx.vstack(
                rx.text(r["lbl"], style={
                    "font_size": "12px",
                    "color": rx.cond(r["pd"] == "1", TEXT3, TEXT),
                    "font_weight": "500",
                    "text_decoration": rx.cond(r["pd"] == "1", "line-through", "none"),
                }),
                rx.text("Bill due", style={"font_size": "10px", "color": TEXT3,
                                            "font_family": MONO}),
                gap="1px", align_items="flex_start",
            ),
            rx.spacer(),
            rx.text(r["amt"], style={
                "font_size": "12px", "font_family": MONO,
                "color": rx.cond(r["pd"] == "1", TEXT3, rx.cond(r["pa"] == "1", TEXT3, RED)),
                "text_decoration": rx.cond(r["pd"] == "1", "line-through", "none"),
            }),
            align_items="flex_start", gap="10px", width="100%",
            style={"padding": "8px 0 6px",
                   "border_bottom": f"1px solid {BORDER}33",
                   "opacity": rx.cond(r["pa"] == "1", "0.6", "1")},
        )),

        rx.box(),
    )


def _timeline_subpanel() -> rx.Component:
    return rx.box(
        rx.cond(
            AppState.tl_rows.length() > 0,
            rx.vstack(
                rx.foreach(AppState.tl_rows.to(list[dict[str, Any]]), _tl_row),
                width="100%", gap="0px",
            ),
            rx.box(
                rx.text("No income or bills in the next 60 days",
                        style={"color": TEXT3, "font_size": "12px"}),
                rx.text("Add paychecks and bills in Setup",
                        style={"color": TEXT3, "font_size": "11px", "margin_top": "4px"}),
                style={"text_align": "center", "padding": "60px 0"},
            ),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── WHAT-IF sub-panel ────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _wi_bucket_row(r: dict) -> rx.Component:
    return rx.match(
        r["rt"],

        # Category header
        ("cat", rx.hstack(
            rx.box(style={"width": "10px", "height": "10px", "border_radius": "50%",
                          "background": r["color"], "flex_shrink": "0"}),
            rx.text(r["name"], style={"font_size": "11px", "font_weight": "600",
                                       "color": TEXT2, "letter_spacing": "0.04em",
                                       "text_transform": "uppercase", "font_family": MONO}),
            gap="8px", align_items="center",
            style={"padding": "10px 0 4px"},
        )),

        # Bucket row
        ("bkt", rx.hstack(
            # On/Off toggle
            rx.box(
                rx.cond(
                    r["is_off"] == "1",
                    rx.text("◎", style={"color": TEXT3, "font_size": "14px"}),
                    rx.text("●", style={"color": r["color"], "font_size": "14px"}),
                ),
                on_click=AppState.toggle_wi_bucket_off(r["bid"]),
                style={"cursor": "pointer", "flex_shrink": "0", "_hover": {"opacity": "0.7"}},
            ),
            # Bucket name + due info
            rx.vstack(
                rx.text(r["name"], style={
                    "font_size": "13px", "color": rx.cond(r["is_off"] == "1", TEXT3, TEXT),
                    "text_decoration": rx.cond(r["is_off"] == "1", "line-through", "none"),
                }),
                rx.cond(
                    r["due_info"] != "",
                    rx.text(r["due_info"], style={"font_size": "9px", "color": TEXT3,
                                                   "font_family": MONO}),
                    rx.box(),
                ),
                gap="1px", align_items="flex_start", flex="1",
            ),
            # Base amount
            rx.text(r["base_fmt"], style={"font_size": "11px", "color": TEXT3,
                                           "font_family": MONO, "min_width": "60px",
                                           "text_align": "right"}),
            # Override input
            rx.input(
                placeholder="+50",
                value=r["override_val"],
                on_change=AppState.set_wi_bucket_override(r["bid"]),
                style={
                    "background": BG3, "border": f"1px solid {BORDER}",
                    "border_radius": "6px", "padding": "4px 8px",
                    "color": TEXT, "font_family": MONO, "font_size": "12px",
                    "width": "70px", "text_align": "right",
                    "_focus": {"border_color": ACCENT, "outline": "none"},
                },
            ),
            # Effective amount
            rx.text(r["eff_fmt"], style={
                "font_size": "12px", "font_family": MONO, "font_weight": "600",
                "color": rx.cond(r["is_off"] == "1", TEXT3,
                                  rx.cond(r["override_val"] != "", AMBER, TEXT2)),
                "min_width": "60px", "text_align": "right",
            }),
            align_items="center", gap="8px", width="100%",
            style={"padding": "6px 0", "border_bottom": f"1px solid {BORDER}33",
                   "opacity": rx.cond(r["is_off"] == "1", "0.5", "1")},
        )),

        rx.box(),
    )


def _wi_rule_row(r: dict) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(r["name"], style={"font_size": "13px", "color": TEXT}),
            rx.text(r["rule_type"], style={"font_size": "9px", "color": TEXT3,
                                            "font_family": MONO, "letter_spacing": "0.08em"}),
            gap="2px", align_items="flex_start", flex="1",
        ),
        rx.text(r["base_str"], style={"font_size": "11px", "color": TEXT3,
                                       "font_family": MONO, "min_width": "60px",
                                       "text_align": "right"}),
        rx.input(
            placeholder="new value",
            value=r["override_val"],
            on_change=AppState.set_wi_rule_override(r["id"]),
            style={
                "background": BG3, "border": f"1px solid {BORDER}",
                "border_radius": "6px", "padding": "4px 8px",
                "color": TEXT, "font_family": MONO, "font_size": "12px",
                "width": "80px", "text_align": "right",
                "_focus": {"border_color": ACCENT, "outline": "none"},
            },
        ),
        align_items="center", gap="8px", width="100%",
        style={"padding": "6px 0", "border_bottom": f"1px solid {BORDER}33"},
    )


def _whatif_subpanel() -> rx.Component:
    return rx.box(
        # ── Scenario bar ─────────────────────────────────────────────────────
        rx.hstack(
            rx.text("What-If Sandbox",
                    style={"font_size": "13px", "font_weight": "600", "color": TEXT,
                           "flex": "1"}),
            rx.cond(
                AppState.wi_active,
                rx.hstack(
                    rx.box(
                        "SCENARIO ACTIVE",
                        style={"font_size": "9px", "font_family": MONO, "letter_spacing": "0.1em",
                               "color": AMBER, "background": f"{AMBER}18",
                               "border": f"1px solid {AMBER}44",
                               "border_radius": "6px", "padding": "3px 8px"},
                    ),
                    rx.box(
                        "Reset",
                        on_click=AppState.reset_whatif,
                        style={"font_size": "11px", "color": RED, "cursor": "pointer",
                               "padding": "3px 8px", "border_radius": "6px",
                               "border": f"1px solid {RED}44", "background": f"{RED}12",
                               "_hover": {"background": f"{RED}22"}},
                    ),
                    gap="8px", align_items="center",
                ),
                rx.box(),
            ),
            align_items="center", width="100%",
            style={"margin_bottom": "12px"},
        ),

        # ── Saved scenarios ───────────────────────────────────────────────────
        rx.cond(
            AppState.wi_scenarios.length() > 0,
            rx.box(
                rx.text("Saved Scenarios",
                        style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                               "letter_spacing": "0.1em", "text_transform": "uppercase",
                               "margin_bottom": "8px"}),
                rx.hstack(
                    rx.foreach(
                        AppState.wi_scenarios.to(list[dict[str, Any]]),
                        lambda sc: rx.hstack(
                            rx.box(
                                sc["name"],
                                on_click=AppState.load_wi_scenario(sc["id"]),
                                style=rx.cond(
                                    AppState.wi_active_scenario_id == sc["id"],
                                    {"padding": "4px 10px", "border_radius": "16px",
                                     "cursor": "pointer", "font_size": "11px",
                                     "font_family": MONO, "background": f"{ACCENT}18",
                                     "color": ACCENT, "border": f"1px solid {ACCENT}44"},
                                    {"padding": "4px 10px", "border_radius": "16px",
                                     "cursor": "pointer", "font_size": "11px",
                                     "font_family": MONO, "background": BG3,
                                     "color": TEXT2, "border": f"1px solid {BORDER}",
                                     "_hover": {"border_color": BORDER2}},
                                ),
                            ),
                            rx.box(
                                "×",
                                on_click=AppState.delete_wi_scenario(sc["id"]),
                                style={"font_size": "12px", "color": TEXT3, "cursor": "pointer",
                                       "padding": "2px 4px", "_hover": {"color": RED}},
                            ),
                            gap="2px", align_items="center",
                        ),
                    ),
                    gap="6px", flex_wrap="wrap",
                ),
                style={"margin_bottom": "14px"},
            ),
            rx.box(),
        ),

        # ── Save scenario input ───────────────────────────────────────────────
        rx.cond(
            AppState.wi_active,
            rx.hstack(
                rx.input(
                    placeholder="Name this scenario…",
                    value=AppState.wi_scenario_name,
                    on_change=AppState.set_wi_scenario_name,
                    style={"background": BG3, "border": f"1px solid {BORDER}",
                           "border_radius": "8px", "padding": "6px 12px",
                           "color": TEXT, "font_size": "12px", "flex": "1",
                           "_focus": {"border_color": ACCENT, "outline": "none"}},
                ),
                rx.box(
                    "Save",
                    on_click=AppState.save_wi_scenario,
                    style={"padding": "6px 14px", "border_radius": "8px",
                           "cursor": "pointer", "font_size": "12px",
                           "background": f"{ACCENT}18", "color": ACCENT,
                           "border": f"1px solid {ACCENT}44",
                           "_hover": {"background": f"{ACCENT}28"}},
                ),
                gap="8px", align_items="center", width="100%",
                style={"margin_bottom": "14px"},
            ),
            rx.box(),
        ),

        # ── KPI summary bar ───────────────────────────────────────────────────
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
            style={"background": BG2,
                   "border": rx.cond(AppState.wi_active,
                                     f"1px solid {AMBER}44", f"1px solid {BORDER}"),
                   "border_radius": "10px", "margin_bottom": "14px", "overflow": "hidden"},
        ),

        # ── 6-month chart ─────────────────────────────────────────────────────
        rx.cond(
            AppState.wi_chart_svg != "",
            rx.box(
                rx.text("6-Month Projection",
                        style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                               "letter_spacing": "0.1em", "text_transform": "uppercase",
                               "margin_bottom": "8px"}),
                rx.html(AppState.wi_chart_svg),
                style={"background": BG2, "border": f"1px solid {BORDER}",
                       "border_radius": "10px", "padding": "14px 16px",
                       "margin_bottom": "14px", "overflow": "hidden"},
            ),
            rx.box(),
        ),

        # ── Income override ───────────────────────────────────────────────────
        rx.box(
            rx.text("Income Override",
                    style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                           "letter_spacing": "0.1em", "text_transform": "uppercase",
                           "margin_bottom": "6px"}),
            rx.input(
                placeholder="Monthly income (e.g. 5000)",
                value=AppState.wi_income_str,
                on_change=AppState.set_wi_income,
                style={"background": BG3, "border": f"1px solid {BORDER}",
                       "border_radius": "8px", "padding": "8px 12px",
                       "color": TEXT, "font_family": MONO, "font_size": "13px",
                       "width": "200px",
                       "_focus": {"border_color": ACCENT, "outline": "none"}},
            ),
            style={"margin_bottom": "14px"},
        ),

        # ── Rules editor ──────────────────────────────────────────────────────
        rx.cond(
            AppState.wi_rules_rows.length() > 0,
            rx.box(
                rx.text("Allocation Rules",
                        style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                               "letter_spacing": "0.1em", "text_transform": "uppercase",
                               "margin_bottom": "8px"}),
                rx.vstack(
                    rx.foreach(AppState.wi_rules_rows.to(list[dict[str, Any]]), _wi_rule_row),
                    width="100%", gap="0px",
                ),
                rx.text("Enter new value to override (% rules: enter new %, $ rules: enter new $)",
                        style={"font_size": "9px", "color": TEXT3, "margin_top": "6px"}),
                style={"background": BG2, "border": f"1px solid {BORDER}",
                       "border_radius": "10px", "padding": "14px 16px",
                       "margin_bottom": "14px"},
            ),
            rx.box(),
        ),

        # ── Bucket overrides ──────────────────────────────────────────────────
        rx.cond(
            AppState.wi_bucket_rows.length() > 0,
            rx.box(
                rx.hstack(
                    rx.text("Budget Overrides",
                            style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                                   "letter_spacing": "0.1em", "text_transform": "uppercase",
                                   "flex": "1"}),
                    rx.text("Base", style={"font_size": "9px", "color": TEXT3,
                                            "font_family": MONO, "min_width": "60px",
                                            "text_align": "right"}),
                    rx.text("Override", style={"font_size": "9px", "color": TEXT3,
                                                "font_family": MONO, "width": "70px",
                                                "text_align": "right"}),
                    rx.text("Effective", style={"font_size": "9px", "color": TEXT3,
                                                 "font_family": MONO, "min_width": "60px",
                                                 "text_align": "right"}),
                    gap="8px", align_items="center", width="100%",
                    style={"margin_bottom": "6px"},
                ),
                rx.text("Override syntax: +50 (add), -20 (subtract), *1.1 (multiply), =200 (set)",
                        style={"font_size": "9px", "color": TEXT3, "margin_bottom": "8px"}),
                rx.vstack(
                    rx.foreach(AppState.wi_bucket_rows.to(list[dict[str, Any]]), _wi_bucket_row),
                    width="100%", gap="0px",
                ),
                style={"background": BG2, "border": f"1px solid {BORDER}",
                       "border_radius": "10px", "padding": "14px 16px",
                       "margin_bottom": "14px"},
            ),
            rx.box(
                rx.text("No bills configured",
                        style={"color": TEXT3, "font_size": "12px"}),
                rx.text("Add buckets with due days or payment frequencies",
                        style={"color": TEXT3, "font_size": "11px", "margin_top": "4px"}),
                style={"text_align": "center", "padding": "40px 0"},
            ),
        ),

        # ── What-if forecast period cards ─────────────────────────────────────
        rx.cond(
            AppState.wi_active & (AppState.wi_periods.length() > 0),
            rx.box(
                rx.text("What-If Forecast",
                        style={"font_size": "9px", "color": TEXT3, "font_family": MONO,
                               "letter_spacing": "0.1em", "text_transform": "uppercase",
                               "margin_bottom": "12px", "margin_top": "4px"}),
                rx.foreach(AppState.wi_periods.to(list[dict[str, Any]]), _period_card),
                width="100%",
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
