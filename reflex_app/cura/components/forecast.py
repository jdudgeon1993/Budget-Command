"""Insights panel — Forecast · Timeline · What-If (timeline grid)."""

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
        rx.text(label, style={"font_size": "11px", "letter_spacing": "0.1em",
                               "text_transform": "uppercase", "color": TEXT3,
                               "font_family": MONO}),
        rx.text(value, style={"font_size": "15px", "font_weight": "700",
                               "font_family": MONO, "color": color}),
        gap="2px", align_items="flex_start",
    )


def _kpi_chip(label: str, value: Any, color: str = TEXT2) -> rx.Component:
    """Compact KPI chip for collapsible panel header bars."""
    return rx.hstack(
        rx.text(label, style={"font_size": "10px", "color": TEXT3,
                               "font_family": MONO, "letter_spacing": "0.06em",
                               "white_space": "nowrap"}),
        rx.text(value, style={"font_size": "11px", "font_weight": "600",
                               "font_family": MONO, "color": color,
                               "white_space": "nowrap"}),
        gap="4px", align_items="center",
        style={"background": BG3, "border_radius": "5px", "padding": "2px 8px",
               "border": f"1px solid {BORDER}", "flex_shrink": "0"},
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
             "background": f"{ACCENT}20", "color": "#D8A4FF",
             "border": f"1px solid {ACCENT}44"},
            {"padding": "5px 16px", "border_radius": "20px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
             "background": "transparent", "color": TEXT3, "border": f"1px solid {BORDER}",
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
            rx.text(a["balance_fmt"], style={"font_size": "12px", "font_family": MONO,
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
            rx.text("START", style={"font_size": "11px", "color": TEXT3, "font_family": MONO,
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
                    rx.text(r["cum"], style={"font_size": "11px", "color": TEXT3,
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
                "font_size": "11px", "color": TEXT3, "font_family": MONO,
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
            rx.text(r["lbl"], style={"font_size": "11px", "color": r["c1"],
                                      "letter_spacing": "0.1em",
                                      "text_transform": "uppercase", "font_family": MONO}),
            style={"padding": "6px 14px 2px",
                   "background": rx.cond(r["c1"] == "#34d399", f"{GREEN}08", f"{RED}08"),
                   "border_left": rx.cond(r["c1"] == "#34d399",
                                          f"2px solid {GREEN}44", f"2px solid {RED}44")},
        )),

        # ── Funded date label ────────────────────────────────────────────────
        ("fdt", rx.text(r["lbl"],
                        style={"font_size": "11px", "color": TEXT3, "letter_spacing": "0.08em",
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
            rx.text("Balance", style={"font_size": "12px", "color": TEXT3, "flex": "1"}),
            rx.text(r["lbl"], style={"font_size": "11px", "font_family": MONO, "color": TEXT2}),
            width="100%", justify="between",
            style={"padding": "3px 14px 6px", "background": f"{GREEN}08",
                   "border_left": f"2px solid {GREEN}33",
                   "border_top": f"1px solid {GREEN}22"},
        )),

        # ── Unfunded date label ──────────────────────────────────────────────
        ("udt", rx.text(r["lbl"],
                        style={"font_size": "11px", "color": TEXT3, "letter_spacing": "0.08em",
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
            rx.text("Balance", style={"font_size": "12px", "color": TEXT3, "flex": "1"}),
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
                rx.text("END", style={"font_size": "11px", "color": TEXT3,
                                       "font_family": MONO, "letter_spacing": "0.1em",
                                       "flex": "1"}),
                rx.text(r["ebf"], style={"font_size": "15px", "font_weight": "700",
                                          "font_family": MONO,
                                          "color": rx.cond(r["ebn"] == "1", RED, TEXT)}),
                width="100%", justify="between",
            ),
            rx.hstack(
                rx.text("Safe to Spend from here",
                        style={"font_size": "12px", "color": TEXT3, "flex": "1"}),
                rx.text(r["amt"], style={"font_size": "12px", "font_family": MONO,
                                          "color": r["c1"], "font_weight": "600"}),
                width="100%", justify="between",
            ),
            rx.cond(
                r["shf"] == "1",
                rx.text("⚠ Balance goes negative — shortfall",
                        style={"font_size": "12px", "color": RED, "font_family": MONO}),
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
                # GAP/PAY badge
                rx.box(
                    rx.cond(p["pt"] == "gap", "– GAP", "▶ PAY"),
                    style={
                        "font_size": "11px", "font_family": MONO, "letter_spacing": "0.08em",
                        "padding": "3px 7px", "border_radius": "4px",
                        "background": rx.cond(p["pt"] == "gap", BG3, f"{ACCENT}22"),
                        "color": rx.cond(p["pt"] == "gap", TEXT3, ACCENT),
                        "border": rx.cond(p["pt"] == "gap",
                                          f"1px solid {BORDER}", f"1px solid {ACCENT}44"),
                        "flex_shrink": "0",
                    },
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(p["lbl"], style={"font_size": "14px", "font_weight": "600",
                                                  "color": TEXT, "line_height": "1.2"}),
                        rx.cond(
                            (p["tbc"] != "0") & (p["tbc"] != "") & (p["shf"] == ""),
                            rx.box(
                                rx.cond(
                                    p["pfc"] == p["tbc"],
                                    "✓ Funded",
                                    rx.fragment("◐ ", p["pfc"], "/", p["tbc"]),
                                ),
                                style={
                                    "font_size": "11px", "font_family": MONO,
                                    "padding": "2px 7px", "border_radius": "4px",
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
                        rx.cond(
                            p["shf"] == "1",
                            rx.box(
                                "▲ SHORTFALL",
                                style={"font_size": "11px", "font_family": MONO,
                                       "padding": "2px 7px", "border_radius": "4px",
                                       "color": RED, "background": f"{RED}18",
                                       "border": f"1px solid {RED}44", "flex_shrink": "0"},
                            ),
                            rx.box(),
                        ),
                        gap="6px", align_items="center", flex_wrap="wrap",
                    ),
                    rx.text(p["sub"], style={"font_size": "12px", "color": TEXT3,
                                              "line_height": "1.2"}),
                    gap="3px", align_items="flex_start", flex="1",
                ),
                gap="8px", align_items="flex_start", flex="1",
            ),
            # Right: net amount + end balance + chevron
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(p["sgn"], style={"font_size": "12px", "font_family": MONO,
                                                  "color": p["c1"]}),
                        rx.text(p["amt"], style={"font_size": "12px", "font_family": MONO,
                                                  "color": p["c1"]}),
                        gap="0px",
                    ),
                    rx.text(p["ebf"], style={"font_size": "15px", "font_weight": "700",
                                              "font_family": MONO,
                                              "color": rx.cond(p["ebn"] == "1", RED, TEXT)}),
                    gap="0px", align_items="flex_end",
                ),
                rx.text(
                    rx.cond(p["is_open"] == "1", "▾", "▸"),
                    style={"font_size": "16px", "color": TEXT3, "flex_shrink": "0",
                           "padding_left": "6px"},
                ),
                align_items="center", gap="4px",
            ),
            align_items="flex_start", width="100%",
        ),
        on_click=AppState.toggle_period_collapse(p["pid"]),
        role="button",
        tab_index=0,
        aria_label=p["lbl"],
        aria_expanded=rx.cond(p["is_open"] == "1", "true", "false"),
        style={
            "background": rx.cond(p["pt"] == "gap", BG3, BG2),
            "padding": "13px 14px 11px",
            "cursor": "pointer",
            "_hover": {"opacity": "0.92"},
            "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "-2px"},
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
                              f"2px solid {RED}", f"1px solid {BORDER2}"),
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

        # Saved scenario chips
        rx.cond(
            AppState.wi_scenarios.length() > 0,
            rx.box(
                rx.hstack(
                    rx.text("SCENARIOS",
                            style={"font_size": "11px", "color": TEXT3, "font_family": MONO,
                                   "letter_spacing": "0.1em", "flex_shrink": "0"}),
                    rx.hstack(
                        rx.foreach(
                            AppState.wi_scenarios.to(list[dict[str, Any]]),
                            lambda sc: rx.box(
                                sc["name"],
                                on_click=AppState.apply_fc_scenario(sc["id"]),
                                style=rx.cond(
                                    AppState.fc_active_scenario_id == sc["id"],
                                    {"padding": "3px 10px", "border_radius": "16px",
                                     "cursor": "pointer", "font_size": "11px",
                                     "font_family": MONO, "background": f"{AMBER}22",
                                     "color": AMBER, "border": f"1px solid {AMBER}55"},
                                    {"padding": "3px 10px", "border_radius": "16px",
                                     "cursor": "pointer", "font_size": "11px",
                                     "font_family": MONO, "background": BG3,
                                     "color": TEXT3, "border": f"1px solid {BORDER}",
                                     "_hover": {"color": TEXT2, "border_color": BORDER2}},
                                ),
                            ),
                        ),
                        gap="6px", flex_wrap="wrap",
                    ),
                    rx.cond(
                        AppState.fc_active_scenario_id != "",
                        rx.box(
                            "Clear",
                            on_click=AppState.clear_fc_scenario,
                            style={"font_size": "12px", "color": TEXT3, "cursor": "pointer",
                                   "padding": "2px 8px", "border_radius": "6px",
                                   "border": f"1px solid {BORDER}",
                                   "_hover": {"color": RED, "border_color": RED + "44"}},
                        ),
                        rx.box(),
                    ),
                    gap="8px", align_items="center", flex_wrap="wrap", width="100%",
                ),
                rx.cond(
                    AppState.fc_active_scenario_id != "",
                    rx.box(
                        rx.text("Scenario: ", style={"font_size": "12px", "color": AMBER,
                                                      "font_family": MONO}),
                        rx.text(AppState.fc_active_scenario_name,
                                style={"font_size": "12px", "color": AMBER, "font_weight": "600"}),
                        style={"display": "inline-flex", "gap": "4px", "align_items": "center",
                               "padding": "4px 10px", "background": f"{AMBER}12",
                               "border_radius": "6px", "margin_top": "8px"},
                    ),
                    rx.box(),
                ),
                style={"margin_bottom": "12px", "padding": "10px 12px",
                       "background": BG2, "border_radius": "8px",
                       "border": f"1px solid {BORDER}"},
            ),
            rx.box(),
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
                    rx.box(class_name="kpi-divider", style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Total Income", AppState.fc_total_income, GREEN),
                    rx.box(class_name="kpi-divider", style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
                    _kpi("Unfunded", AppState.fc_total_unfunded, RED),
                    rx.box(class_name="kpi-divider", style={"width": "1px", "background": BORDER, "align_self": "stretch"}),
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
            rx.vstack(
                rx.text("No paychecks configured",
                        style={"color": TEXT2, "font_size": "15px", "font_weight": "600"}),
                rx.text("Add a paycheck in Setup to see your forecast.",
                        style={"color": TEXT3, "font_size": "13px", "margin_top": "4px"}),
                rx.box(
                    "Go to Setup →",
                    on_click=AppState.set_panel("setup"),
                    role="button", tab_index=0,
                    style={
                        "margin_top": "12px", "padding": "8px 20px",
                        "border_radius": "8px", "cursor": "pointer",
                        "font_size": "13px", "font_family": MONO,
                        "background": f"{ACCENT}18", "color": ACCENT,
                        "border": f"1px solid {ACCENT}44",
                        "_hover": {"background": f"{ACCENT}28"},
                        "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
                    },
                ),
                align_items="center",
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

        ("day", rx.hstack(
            rx.text(r["lbl"], style={
                "font_size": "12px", "font_weight": "600",
                "color": rx.cond(r["td"] == "1", ACCENT, TEXT2),
                "letter_spacing": "0.04em", "flex": "1",
            }),
            rx.cond(
                r["td"] == "1",
                rx.box("Today", style={"font_size": "11px", "color": ACCENT, "font_family": MONO,
                                        "background": f"{ACCENT}18", "border": f"1px solid {ACCENT}44",
                                        "border_radius": "4px", "padding": "2px 6px"}),
                rx.box(),
            ),
            align_items="center", width="100%",
            style={"padding": "10px 0 4px",
                   "border_bottom": f"1px solid {BORDER}",
                   "margin_top": "8px"},
        )),

        ("paycheck", rx.hstack(
            rx.box(style={"width": "10px", "height": "10px", "border_radius": "50%",
                          "background": GREEN, "flex_shrink": "0", "margin_top": "2px"}),
            rx.vstack(
                rx.text(r["lbl"], style={"font_size": "12px", "color": TEXT, "font_weight": "500"}),
                rx.text("Paycheck", style={"font_size": "12px", "color": TEXT3, "font_family": MONO}),
                gap="1px", align_items="flex_start",
            ),
            rx.spacer(),
            rx.text(r["amt"], style={"font_size": "13px", "font_family": MONO,
                                      "color": GREEN, "font_weight": "600"}),
            align_items="flex_start", gap="10px", width="100%",
            style={"padding": "8px 0 6px", "border_bottom": f"1px solid {BORDER}33"},
        )),

        ("bill", rx.hstack(
            rx.box(style={
                "width": "10px", "height": "10px", "border_radius": "50%",
                "flex_shrink": "0", "margin_top": "2px",
                "background": rx.cond(
                    r["pd"] == "1", TEXT3,
                    rx.cond(r["sch"] == "1", AMBER,
                            rx.cond(r["pa"] == "1", TEXT3, RED))
                ),
                "opacity": rx.cond(r["pa"] == "1", "0.5", "1"),
            }),
            rx.vstack(
                rx.text(r["lbl"], style={
                    "font_size": "12px",
                    "color": rx.cond(r["pd"] == "1", TEXT3, TEXT),
                    "font_weight": "500",
                    "text_decoration": rx.cond(r["pd"] == "1", "line-through", "none"),
                }),
                rx.text(
                    rx.cond(r["sch"] == "1", "Scheduled",
                            rx.cond(r["pd"] == "1", "Paid", "Bill due")),
                    style={"font_size": "11px", "font_family": MONO,
                           "color": rx.cond(r["sch"] == "1", AMBER, TEXT3)},
                ),
                gap="1px", align_items="flex_start",
            ),
            rx.spacer(),
            rx.text(r["amt"], style={
                "font_size": "12px", "font_family": MONO, "font_weight": "600",
                "color": rx.cond(
                    r["pd"] == "1", TEXT3,
                    rx.cond(r["sch"] == "1", AMBER,
                            rx.cond(r["pa"] == "1", TEXT3, RED))
                ),
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
#  ── WHAT-IF helpers (legacy — kept for month-pill row in bucket editor) ──────
# ─────────────────────────────────────────────────────────────────────────────

def _month_pill(label: str, key: str, status: str) -> rx.Component:
    return rx.box(
        label,
        on_click=AppState.toggle_wi_month_schedule(key),
        role="button", tab_index=0,
        style={
            "font_size": "11px", "font_family": MONO, "cursor": "pointer",
            "padding": "5px 8px", "border_radius": "4px", "min_height": "28px",
            "display": "flex", "align_items": "center",
            "background": rx.cond(status == "off", BG3, f"{ACCENT}22"),
            "color": rx.cond(status == "off", TEXT3, ACCENT),
            "border": rx.cond(status == "off", f"1px solid {BORDER}", f"1px solid {ACCENT}44"),
            "text_decoration": rx.cond(status == "off", "line-through", "none"),
            "_hover": {"opacity": "0.8"},
        },
    )


def _wi_bucket_row(r: dict) -> rx.Component:
    return rx.match(
        r["rt"],
        ("cat", rx.hstack(
            rx.box(style={"width": "10px", "height": "10px", "border_radius": "50%",
                          "background": r["color"], "flex_shrink": "0"}),
            rx.text(r["name"], style={"font_size": "11px", "font_weight": "600",
                                       "color": TEXT2, "letter_spacing": "0.04em",
                                       "text_transform": "uppercase", "font_family": MONO}),
            gap="8px", align_items="center",
            style={"padding": "10px 0 4px"},
        )),
        ("bkt", rx.vstack(
            rx.hstack(
                rx.box(
                    rx.cond(
                        r["is_off"] == "1",
                        rx.text("◎", style={"color": TEXT3, "font_size": "14px"}),
                        rx.text("●", style={"color": r["color"], "font_size": "14px"}),
                    ),
                    on_click=AppState.toggle_wi_bucket_off(r["bid"]),
                    style={"cursor": "pointer", "flex_shrink": "0", "_hover": {"opacity": "0.7"}},
                ),
                rx.vstack(
                    rx.text(r["name"], style={
                        "font_size": "13px",
                        "color": rx.cond(r["is_off"] == "1", TEXT3, TEXT),
                        "text_decoration": rx.cond(r["is_off"] == "1", "line-through", "none"),
                    }),
                    rx.cond(
                        r["due_info"] != "",
                        rx.text(r["due_info"], style={"font_size": "11px", "color": TEXT3,
                                                       "font_family": MONO}),
                        rx.box(),
                    ),
                    gap="1px", align_items="flex_start", flex="1",
                ),
                rx.text(r["base_fmt"], style={"font_size": "11px", "color": TEXT3,
                                               "font_family": MONO, "min_width": "52px",
                                               "text_align": "right"}),
                rx.input(
                    placeholder="+50",
                    value=r["override_val"],
                    on_change=AppState.set_wi_bucket_override(r["bid"]),
                    class_name="wi-col-override",
                    style={
                        "background": BG3, "border": f"1px solid {BORDER}",
                        "border_radius": "6px", "padding": "4px 8px",
                        "color": TEXT, "font_family": MONO, "font_size": "12px",
                        "width": "66px", "text_align": "right",
                        "_focus": {"border_color": ACCENT, "outline": "none"},
                    },
                ),
                rx.text(r["eff_fmt"], class_name="wi-col-effective", style={
                    "font_size": "12px", "font_family": MONO, "font_weight": "600",
                    "color": rx.cond(r["is_off"] == "1", TEXT3,
                                      rx.cond(r["override_val"] != "", AMBER, TEXT2)),
                    "min_width": "52px", "text_align": "right",
                }),
                align_items="center", gap="8px", width="100%",
            ),
            rx.hstack(
                rx.text("MONTHS:", style={"font_size": "11px", "color": TEXT3,
                                           "font_family": MONO, "letter_spacing": "0.06em",
                                           "flex_shrink": "0"}),
                _month_pill(r["ml0"], r["mi0"], r["ms0"]),
                _month_pill(r["ml1"], r["mi1"], r["ms1"]),
                _month_pill(r["ml2"], r["mi2"], r["ms2"]),
                _month_pill(r["ml3"], r["mi3"], r["ms3"]),
                _month_pill(r["ml4"], r["mi4"], r["ms4"]),
                _month_pill(r["ml5"], r["mi5"], r["ms5"]),
                rx.spacer(),
                rx.text("Day:", style={"font_size": "11px", "color": TEXT3,
                                        "font_family": MONO, "flex_shrink": "0"}),
                rx.input(
                    placeholder=r["due_info"],
                    value=r["due_day_override"],
                    on_change=AppState.set_wi_due_day_override(r["bid"]),
                    style={
                        "background": BG3, "border": f"1px solid {BORDER}",
                        "border_radius": "4px", "padding": "2px 6px",
                        "color": TEXT, "font_family": MONO, "font_size": "11px",
                        "width": "44px", "text_align": "center",
                        "_focus": {"border_color": ACCENT, "outline": "none"},
                    },
                ),
                gap="4px", align_items="center", width="100%",
                style={"padding_left": "22px", "opacity": rx.cond(r["is_off"] == "1", "0.4", "1")},
            ),
            width="100%", gap="4px",
            style={"padding": "6px 0", "border_bottom": f"1px solid {BORDER}33",
                   "opacity": rx.cond(r["is_off"] == "1", "0.5", "1")},
        )),
        rx.box(),
    )


def _wi_rule_row(r: dict) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(r["name"], style={"font_size": "13px", "color": TEXT}),
            rx.text(r["rule_type"], style={"font_size": "11px", "color": TEXT3,
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


# ─────────────────────────────────────────────────────────────────────────────
#  ── NEW: Cell popover ────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _pop_month_chip(m: dict) -> rx.Component:
    """Month selector chip inside the cell popover."""
    is_sel = AppState.wi_pop_apply_from == m["mkey"]
    return rx.box(
        m["label"],
        on_click=AppState.set_pop_apply_from(m["mkey"]),
        role="button", tab_index=0,
        style=rx.cond(
            is_sel,
            {"padding": "5px 10px", "border_radius": "6px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO,
             "background": ACCENT, "color": "#fff",
             "border": f"1px solid {ACCENT}"},
            {"padding": "5px 10px", "border_radius": "6px", "cursor": "pointer",
             "font_size": "11px", "font_family": MONO,
             "background": BG3, "color": TEXT3,
             "border": f"1px solid {BORDER}",
             "_hover": {"color": TEXT2, "border_color": BORDER2}},
        ),
    )


def _pop_rule_row(r: dict) -> rx.Component:
    """Existing rule row inside the cell popover."""
    return rx.hstack(
        rx.vstack(
            rx.text(
                rx.cond(r["from_label"] == "Default", "Default", f"From {r['from_label']}"),
                style={"font_size": "12px", "color": TEXT2, "font_family": MONO},
            ),
            rx.hstack(
                rx.cond(
                    r["enabled"] == "1",
                    rx.box("ON", style={"font_size": "10px", "color": GREEN,
                                         "background": f"{GREEN}18", "border_radius": "4px",
                                         "padding": "1px 5px", "font_family": MONO}),
                    rx.box("OFF", style={"font_size": "10px", "color": TEXT3,
                                          "background": BG3, "border_radius": "4px",
                                          "padding": "1px 5px", "font_family": MONO}),
                ),
                rx.text(r["amount_fmt"],
                        style={"font_size": "12px", "color": TEXT3, "font_family": MONO}),
                gap="6px", align_items="center",
            ),
            gap="2px", align_items="flex_start", flex="1",
        ),
        rx.box(
            "×",
            on_click=AppState.del_wi_timeline_rule(AppState.wi_pop_bkt_id, r["idx"]),
            role="button", tab_index=0,
            style={"font_size": "16px", "color": TEXT3, "cursor": "pointer",
                   "padding": "4px 8px", "border_radius": "4px",
                   "_hover": {"color": RED, "background": f"{RED}12"}},
        ),
        align_items="center", gap="8px", width="100%",
        style={"padding": "6px 8px", "border_radius": "6px",
               "background": BG3, "margin_bottom": "4px"},
    )


def _cell_popover() -> rx.Component:
    """Fixed-overlay modal for editing a timeline cell rule."""
    return rx.cond(
        AppState.wi_pop_open,
        rx.box(
            # Backdrop (click to close)
            rx.box(
                style={
                    "position": "absolute", "inset": "0",
                    "cursor": "default",
                },
                on_click=AppState.close_cell_pop(False),
            ),
            # Modal card
            rx.box(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.text("Schedule Change", style={
                            "font_size": "14px", "font_weight": "700", "color": TEXT}),
                        rx.text(AppState.wi_pop_bkt_id, style={
                            "font_size": "11px", "color": TEXT3, "font_family": MONO}),
                        gap="2px", align_items="flex_start",
                    ),
                    rx.spacer(),
                    rx.box(
                        "×",
                        on_click=AppState.close_cell_pop(False),
                        role="button", tab_index=0, aria_label="Close",
                        style={"font_size": "20px", "color": TEXT3, "cursor": "pointer",
                               "padding": "2px 8px", "_hover": {"color": TEXT}},
                    ),
                    width="100%", align_items="flex_start",
                    style={"margin_bottom": "14px"},
                ),

                # Existing rules
                rx.cond(
                    AppState.wi_pop_rules.length() > 0,
                    rx.box(
                        rx.text("CURRENT RULES",
                                style={"font_size": "10px", "color": TEXT3, "font_family": MONO,
                                       "letter_spacing": "0.1em", "margin_bottom": "6px"}),
                        rx.foreach(AppState.wi_pop_rules.to(list[dict[str, Any]]), _pop_rule_row),
                        style={"margin_bottom": "14px"},
                    ),
                    rx.box(),
                ),

                rx.box(style={"height": "1px", "background": BORDER, "margin_bottom": "14px"}),

                # Apply-from month chips
                rx.text("APPLY FROM",
                        style={"font_size": "10px", "color": TEXT3, "font_family": MONO,
                               "letter_spacing": "0.1em", "margin_bottom": "8px"}),
                rx.hstack(
                    rx.box(
                        "Default",
                        on_click=AppState.set_pop_apply_from(""),
                        role="button", tab_index=0,
                        style=rx.cond(
                            AppState.wi_pop_apply_from == "",
                            {"padding": "5px 10px", "border_radius": "6px", "cursor": "pointer",
                             "font_size": "11px", "font_family": MONO,
                             "background": ACCENT, "color": "#fff",
                             "border": f"1px solid {ACCENT}"},
                            {"padding": "5px 10px", "border_radius": "6px", "cursor": "pointer",
                             "font_size": "11px", "font_family": MONO,
                             "background": BG3, "color": TEXT3,
                             "border": f"1px solid {BORDER}",
                             "_hover": {"color": TEXT2, "border_color": BORDER2}},
                        ),
                    ),
                    rx.foreach(AppState.wi_grid_months.to(list[dict[str, Any]]), _pop_month_chip),
                    gap="6px", flex_wrap="wrap",
                    style={"margin_bottom": "14px"},
                ),

                # Enable/disable toggle
                rx.text("STATE",
                        style={"font_size": "10px", "color": TEXT3, "font_family": MONO,
                               "letter_spacing": "0.1em", "margin_bottom": "8px"}),
                rx.hstack(
                    rx.box(
                        "Enabled",
                        on_click=AppState.set_pop_enabled(True),
                        role="button", tab_index=0,
                        style=rx.cond(
                            AppState.wi_pop_enabled,
                            {"padding": "6px 14px", "border_radius": "6px", "cursor": "pointer",
                             "font_size": "12px", "font_family": MONO,
                             "background": f"{GREEN}22", "color": GREEN,
                             "border": f"1px solid {GREEN}55"},
                            {"padding": "6px 14px", "border_radius": "6px", "cursor": "pointer",
                             "font_size": "12px", "font_family": MONO,
                             "background": BG3, "color": TEXT3,
                             "border": f"1px solid {BORDER}",
                             "_hover": {"border_color": BORDER2}},
                        ),
                    ),
                    rx.box(
                        "Disabled",
                        on_click=AppState.set_pop_enabled(False),
                        role="button", tab_index=0,
                        style=rx.cond(
                            ~AppState.wi_pop_enabled,
                            {"padding": "6px 14px", "border_radius": "6px", "cursor": "pointer",
                             "font_size": "12px", "font_family": MONO,
                             "background": f"{RED}18", "color": RED,
                             "border": f"1px solid {RED}44"},
                            {"padding": "6px 14px", "border_radius": "6px", "cursor": "pointer",
                             "font_size": "12px", "font_family": MONO,
                             "background": BG3, "color": TEXT3,
                             "border": f"1px solid {BORDER}",
                             "_hover": {"border_color": BORDER2}},
                        ),
                    ),
                    gap="8px",
                    style={"margin_bottom": "14px"},
                ),

                # Amount input
                rx.cond(
                    AppState.wi_pop_enabled,
                    rx.box(
                        rx.text("AMOUNT",
                                style={"font_size": "10px", "color": TEXT3, "font_family": MONO,
                                       "letter_spacing": "0.1em", "margin_bottom": "6px"}),
                        rx.input(
                            placeholder="e.g. 1800",
                            value=AppState.wi_pop_amount,
                            on_change=AppState.set_pop_amount,
                            style={
                                "background": BG3, "border": f"1px solid {BORDER}",
                                "border_radius": "8px", "padding": "10px 12px",
                                "color": TEXT, "font_family": MONO, "font_size": "14px",
                                "width": "100%",
                                "_focus": {"border_color": ACCENT, "outline": "none",
                                           "box_shadow": f"0 0 0 3px {ACCENT}22"},
                            },
                        ),
                        style={"margin_bottom": "14px"},
                    ),
                    rx.box(),
                ),

                # Apply button
                rx.box(
                    "Apply Change",
                    on_click=AppState.apply_pop_rule,
                    role="button", tab_index=0,
                    style={
                        "width": "100%", "padding": "12px",
                        "border_radius": "8px", "cursor": "pointer",
                        "font_size": "13px", "font_weight": "600",
                        "font_family": MONO, "text_align": "center",
                        "background": ACCENT, "color": "#fff",
                        "border": "none",
                        "box_shadow": f"0 4px 16px rgba(191,90,242,0.30)",
                        "_hover": {"opacity": "0.9"},
                        "_active": {"transform": "scale(0.98)"},
                    },
                ),

                # Card style
                style={
                    "position": "relative", "z_index": "1",
                    "width": "360px", "max_width": "calc(100vw - 32px)",
                    "max_height": "90vh", "overflow_y": "auto",
                    "background": BG2,
                    "border": f"1px solid {BORDER2}",
                    "border_radius": "14px",
                    "padding": "20px",
                    "box_shadow": "0 24px 64px rgba(0,0,0,0.60)",
                },
                on_click=rx.stop_propagation,
            ),
            # Backdrop overlay styles
            style={
                "position": "fixed", "inset": "0",
                "background": "rgba(0,0,0,0.68)",
                "backdrop_filter": "blur(6px)",
                "-webkit-backdrop_filter": "blur(6px)",
                "z_index": "400",
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
            },
        ),
        rx.box(),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── NEW: Timeline grid ───────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

_CELL_STATE_STYLES: dict = {
    "on":    {"background": "transparent", "border_left": f"3px solid transparent"},
    "off":   {"background": f"rgba(255,69,58,0.06)", "border_left": f"3px solid rgba(255,69,58,0.4)"},
    "start": {"background": f"rgba(48,209,88,0.08)", "border_left": f"3px solid rgba(48,209,88,0.5)"},
    "chg":   {"background": f"rgba(255,159,10,0.08)", "border_left": f"3px solid rgba(255,159,10,0.5)"},
}


def _grid_cell(cell: dict) -> rx.Component:
    """One cell in the timeline grid — clickable to open the rule popover."""
    return rx.el.td(
        rx.text(
            cell["amount_fmt"],
            style={
                "font_size": "12px", "font_family": MONO, "font_weight": "500",
                "color": rx.cond(
                    cell["tx_class"] == "off", TEXT3,
                    rx.cond(cell["tx_class"] == "start", GREEN,
                            rx.cond(cell["tx_class"] == "chg", AMBER, TEXT2)),
                ),
                "text_decoration": rx.cond(cell["tx_class"] == "off", "line-through", "none"),
            },
        ),
        on_click=AppState.open_cell_pop(cell["bid"], cell["mkey"]),
        style={
            "min_width": "100px",
            "max_width": "120px",
            "height": "38px",
            "padding": "0 10px",
            "cursor": "pointer",
            "text_align": "right",
            "vertical_align": "middle",
            "white_space": "nowrap",
            "border_right": f"1px solid {BORDER}",
            "background": rx.cond(
                cell["tx_class"] == "off", "rgba(255,69,58,0.06)",
                rx.cond(cell["tx_class"] == "start", "rgba(48,209,88,0.08)",
                        rx.cond(cell["tx_class"] == "chg", "rgba(255,159,10,0.06)",
                                "transparent")),
            ),
            "border_left": rx.cond(
                cell["tx_class"] == "off", "3px solid rgba(255,69,58,0.4)",
                rx.cond(cell["tx_class"] == "start", "3px solid rgba(48,209,88,0.5)",
                        rx.cond(cell["tx_class"] == "chg", "3px solid rgba(255,159,10,0.5)",
                                "3px solid transparent")),
            ),
            "_hover": {"background": "rgba(191,90,242,0.08)"},
        },
    )


def _grid_row_comp(row: dict) -> rx.Component:
    """One bucket row in the timeline grid."""
    return rx.el.tr(
        # Sticky name cell
        rx.el.td(
            rx.hstack(
                rx.box(style={
                    "width": "8px", "height": "8px", "border_radius": "50%",
                    "background": row["cat_color"], "flex_shrink": "0",
                }),
                rx.text(row["name"], style={
                    "font_size": "12px", "color": TEXT, "white_space": "nowrap",
                    "overflow": "hidden", "text_overflow": "ellipsis",
                }),
                gap="6px", align_items="center", width="100%",
            ),
            style={
                "position": "sticky", "left": "0", "z_index": "5",
                "background": BG, "border_right": f"1px solid {BORDER2}",
                "min_width": "160px", "max_width": "160px",
                "padding": "0 10px", "height": "38px",
                "white_space": "nowrap", "overflow": "hidden",
                "text_overflow": "ellipsis", "vertical_align": "middle",
            },
        ),
        # Month cells
        rx.foreach(row["cells"].to(list[dict[str, Any]]), _grid_cell),
        style={"border_bottom": f"1px solid {BORDER}33",
               "_hover": {"background": "rgba(255,255,255,0.015)"}},
    )


def _wi_grid_body() -> rx.Component:
    """Scrollable timeline matrix — buckets × months."""
    return rx.box(
        rx.cond(
            AppState.wi_grid_rows.length() > 0,
            rx.box(
                rx.el.table(
                    # Header
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th(
                                "Bucket",
                                style={
                                    "position": "sticky", "left": "0", "z_index": "10",
                                    "background": BG2,
                                    "font_size": "10px", "font_family": MONO,
                                    "letter_spacing": "0.1em", "text_transform": "uppercase",
                                    "color": TEXT3, "font_weight": "600",
                                    "padding": "8px 10px", "text_align": "left",
                                    "min_width": "160px", "border_right": f"1px solid {BORDER2}",
                                    "border_bottom": f"1px solid {BORDER}",
                                    "white_space": "nowrap",
                                },
                            ),
                            rx.foreach(
                                AppState.wi_grid_months.to(list[dict[str, Any]]),
                                lambda m: rx.el.th(
                                    m["label"],
                                    style={
                                        "font_size": "10px", "font_family": MONO,
                                        "letter_spacing": "0.08em", "text_transform": "uppercase",
                                        "color": ACCENT, "font_weight": "600",
                                        "padding": "8px 10px", "text_align": "right",
                                        "min_width": "100px",
                                        "border_right": f"1px solid {BORDER}",
                                        "border_bottom": f"1px solid {BORDER}",
                                        "white_space": "nowrap",
                                    },
                                ),
                            ),
                        ),
                    ),
                    # Body
                    rx.el.tbody(
                        rx.foreach(AppState.wi_grid_rows.to(list[dict[str, Any]]), _grid_row_comp),
                    ),
                    style={
                        "border_collapse": "collapse",
                        "width": "100%",
                        "table_layout": "fixed",
                    },
                ),
                style={
                    "overflow_x": "auto",
                    "overflow_y": "auto",
                    "max_height": "320px",
                    "border": f"1px solid {BORDER}",
                    "border_radius": "8px",
                },
            ),
            # Empty state
            rx.box(
                rx.text("No buckets with budgets configured.",
                        style={"color": TEXT3, "font_size": "13px"}),
                rx.box(
                    "Go to Setup →",
                    on_click=AppState.set_panel("setup"),
                    role="button",
                    style={"margin_top": "10px", "padding": "6px 16px",
                           "border_radius": "8px", "cursor": "pointer",
                           "font_size": "12px", "font_family": MONO,
                           "background": f"{ACCENT}18", "color": ACCENT,
                           "border": f"1px solid {ACCENT}44",
                           "_hover": {"background": f"{ACCENT}28"}},
                ),
                style={"text_align": "center", "padding": "32px 0"},
            ),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── NEW: Collapsible panel header ────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _panel_hdr(key: str, icon_paths: str, title: str, kpi_row: rx.Component,
               is_open: Any) -> rx.Component:
    """44px collapsible panel header bar."""
    return rx.hstack(
        # Collapse arrow
        rx.html(
            f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="2" stroke-linecap="round">'
            f'<polyline points="6 9 12 15 18 9"/></svg>',
            style=rx.cond(
                is_open,
                {"color": TEXT3, "flex_shrink": "0",
                 "transition": "transform 0.18s", "transform": "rotate(0deg)"},
                {"color": TEXT3, "flex_shrink": "0",
                 "transition": "transform 0.18s", "transform": "rotate(-90deg)"},
            ),
        ),
        # Icon
        rx.html(
            f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
            f'{icon_paths}</svg>',
            style={"color": ACCENT, "flex_shrink": "0"},
        ),
        # Title
        rx.text(
            title,
            style={"font_size": "12px", "font_weight": "600", "color": TEXT2,
                   "font_family": MONO, "letter_spacing": "0.06em",
                   "text_transform": "uppercase", "flex_shrink": "0"},
        ),
        # KPI chips
        kpi_row,
        rx.spacer(),
        on_click=AppState.toggle_wi_panel(key),
        role="button", tab_index=0, aria_expanded=rx.cond(is_open, "true", "false"),
        width="100%",
        style={
            "height": "44px", "min_height": "44px",
            "align_items": "center",
            "padding": "0 14px",
            "cursor": "pointer",
            "background": BG2,
            "border_bottom": rx.cond(is_open, f"1px solid {BORDER}", "none"),
            "gap": "10px",
            "user_select": "none",
            "_hover": {"background": BG3},
            "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "-2px"},
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── NEW: What-If scenario sidebar ───────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _wi_scenarios_sidebar() -> rx.Component:
    """Left sidebar — income override, scenario save/load, active state."""
    return rx.vstack(
        # Active badge + Reset
        rx.cond(
            AppState.wi_active,
            rx.hstack(
                rx.box(
                    "ACTIVE",
                    style={"font_size": "10px", "font_family": MONO, "letter_spacing": "0.1em",
                           "color": AMBER, "background": f"{AMBER}18",
                           "border": f"1px solid {AMBER}44",
                           "border_radius": "5px", "padding": "2px 7px"},
                ),
                rx.spacer(),
                rx.box(
                    "Reset",
                    on_click=AppState.reset_whatif,
                    role="button", tab_index=0,
                    style={"font_size": "11px", "color": TEXT3, "cursor": "pointer",
                           "padding": "3px 8px", "border_radius": "5px",
                           "border": f"1px solid {BORDER}",
                           "_hover": {"color": RED, "border_color": f"{RED}44"}},
                ),
                width="100%", align_items="center",
                style={"margin_bottom": "10px"},
            ),
            rx.box(),
        ),

        # Section: Income
        rx.text("INCOME", style={"font_size": "10px", "color": TEXT3, "font_family": MONO,
                                   "letter_spacing": "0.12em", "margin_bottom": "5px"}),
        rx.input(
            placeholder="Monthly (e.g. 5000)",
            value=AppState.wi_income_str,
            on_change=AppState.set_wi_income,
            style={"background": BG3, "border": f"1px solid {BORDER}",
                   "border_radius": "7px", "padding": "8px 10px",
                   "color": TEXT, "font_family": MONO, "font_size": "12px",
                   "width": "100%",
                   "_focus": {"border_color": ACCENT, "outline": "none"}},
        ),

        # Divider
        rx.box(style={"height": "1px", "background": BORDER, "margin": "12px 0"}),

        # Section: KPIs
        rx.text("SUMMARY", style={"font_size": "10px", "color": TEXT3, "font_family": MONO,
                                    "letter_spacing": "0.12em", "margin_bottom": "8px"}),
        rx.vstack(
            rx.hstack(
                rx.text("Balance", style={"font_size": "11px", "color": TEXT3,
                                          "font_family": MONO, "flex": "1"}),
                rx.text(AppState.wi_start_bal, style={"font_size": "12px", "font_weight": "600",
                                                        "font_family": MONO, "color": TEXT2}),
                width="100%", justify="between",
            ),
            rx.hstack(
                rx.text("Income", style={"font_size": "11px", "color": TEXT3,
                                          "font_family": MONO, "flex": "1"}),
                rx.text(AppState.wi_total_income, style={"font_size": "12px", "font_weight": "600",
                                                           "font_family": MONO, "color": GREEN}),
                width="100%", justify="between",
            ),
            rx.hstack(
                rx.text("Unfunded", style={"font_size": "11px", "color": TEXT3,
                                            "font_family": MONO, "flex": "1"}),
                rx.text(AppState.wi_total_unfunded, style={"font_size": "12px", "font_weight": "600",
                                                             "font_family": MONO, "color": RED}),
                width="100%", justify="between",
            ),
            rx.hstack(
                rx.text("Safe to Spend", style={"font_size": "11px", "color": TEXT3,
                                                 "font_family": MONO, "flex": "1"}),
                rx.text(AppState.wi_safe_to_spend, style={"font_size": "12px", "font_weight": "700",
                                                           "font_family": MONO,
                                                           "color": AppState.wi_sts_color}),
                width="100%", justify="between",
            ),
            gap="7px", width="100%",
            style={"background": BG3, "border_radius": "8px", "padding": "10px 12px",
                   "border": rx.cond(AppState.wi_active,
                                     f"1px solid {AMBER}33", f"1px solid {BORDER}")},
        ),

        # Divider
        rx.box(style={"height": "1px", "background": BORDER, "margin": "12px 0"}),

        # Section: Scenarios
        rx.text("SCENARIOS", style={"font_size": "10px", "color": TEXT3, "font_family": MONO,
                                     "letter_spacing": "0.12em", "margin_bottom": "8px"}),
        rx.cond(
            AppState.wi_scenarios.length() > 0,
            rx.vstack(
                rx.foreach(
                    AppState.wi_scenarios.to(list[dict[str, Any]]),
                    lambda sc: rx.hstack(
                        rx.box(
                            sc["name"],
                            on_click=AppState.load_wi_scenario(sc["id"]),
                            style=rx.cond(
                                AppState.wi_active_scenario_id == sc["id"],
                                {"flex": "1", "padding": "5px 8px", "border_radius": "6px",
                                 "cursor": "pointer", "font_size": "11px", "font_family": MONO,
                                 "background": f"{ACCENT}18", "color": ACCENT,
                                 "border": f"1px solid {ACCENT}44",
                                 "overflow": "hidden", "text_overflow": "ellipsis",
                                 "white_space": "nowrap"},
                                {"flex": "1", "padding": "5px 8px", "border_radius": "6px",
                                 "cursor": "pointer", "font_size": "11px", "font_family": MONO,
                                 "background": BG3, "color": TEXT2,
                                 "border": f"1px solid {BORDER}",
                                 "overflow": "hidden", "text_overflow": "ellipsis",
                                 "white_space": "nowrap",
                                 "_hover": {"border_color": BORDER2}},
                            ),
                        ),
                        rx.box(
                            "×",
                            on_click=AppState.delete_wi_scenario(sc["id"]),
                            style={"font_size": "14px", "color": TEXT3, "cursor": "pointer",
                                   "padding": "2px 5px", "border_radius": "4px",
                                   "flex_shrink": "0",
                                   "_hover": {"color": RED}},
                        ),
                        gap="4px", align_items="center", width="100%",
                    ),
                ),
                gap="5px", width="100%",
                style={"margin_bottom": "10px"},
            ),
            rx.box(),
        ),

        # Save input
        rx.cond(
            AppState.wi_active,
            rx.vstack(
                rx.input(
                    placeholder="Name this scenario…",
                    value=AppState.wi_scenario_name,
                    on_change=AppState.set_wi_scenario_name,
                    style={"background": BG3, "border": f"1px solid {BORDER}",
                           "border_radius": "7px", "padding": "8px 10px",
                           "color": TEXT, "font_family": MONO, "font_size": "12px",
                           "width": "100%",
                           "_focus": {"border_color": ACCENT, "outline": "none"}},
                ),
                rx.box(
                    "Save Scenario",
                    on_click=AppState.save_wi_scenario,
                    role="button", tab_index=0,
                    style={"width": "100%", "padding": "9px",
                           "border_radius": "7px", "cursor": "pointer",
                           "font_size": "12px", "font_weight": "600",
                           "font_family": MONO, "text_align": "center",
                           "background": f"{ACCENT}18", "color": ACCENT,
                           "border": f"1px solid {ACCENT}44",
                           "_hover": {"background": f"{ACCENT}28"},
                           "_active": {"transform": "scale(0.98)"}},
                ),
                gap="6px", width="100%",
            ),
            rx.box(),
        ),

        # RLS error warning
        rx.cond(
            AppState.wi_scenarios_rls_error,
            rx.box(
                rx.text("⚠ DB permissions error.",
                        style={"font_size": "11px", "color": AMBER, "font_family": MONO}),
                rx.text("Run schema_migrations.sql in Supabase.",
                        style={"font_size": "10px", "color": TEXT3}),
                style={"margin_top": "8px", "padding": "8px 10px",
                       "background": f"{AMBER}10", "border_radius": "7px",
                       "border": f"1px solid {AMBER}33"},
            ),
            rx.box(),
        ),

        gap="0px", width="100%",
        style={
            "width": "210px", "min_width": "210px", "flex_shrink": "0",
            "background": BG2,
            "border_right": f"1px solid {BORDER}",
            "padding": "14px 12px",
            "overflow_y": "auto",
            "max_height": "calc(100vh - 160px)",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── NEW: What-If three-panel layout ─────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def _whatif_subpanel() -> rx.Component:
    """New three-panel What-If layout: Chart · Timeline Grid · Periods/Intel."""
    return rx.box(
        # Main layout: sidebar + panels
        rx.hstack(
            # Left sidebar
            _wi_scenarios_sidebar(),

            # Right: three collapsible panels
            rx.vstack(

                # ── Panel 1: Balance Chart ───────────────────────────────────
                rx.box(
                    _panel_hdr(
                        "chart",
                        '<polyline points="3 17 9 11 13 15 21 7"/>',
                        "Balance Chart",
                        rx.hstack(
                            rx.cond(
                                AppState.wi_shortfall_count > 0,
                                _kpi_chip("shortfalls", AppState.wi_shortfall_count, RED),
                                _kpi_chip("safe", AppState.wi_safe_to_spend,
                                          AppState.wi_sts_color),
                            ),
                            gap="6px",
                        ),
                        AppState.wi_chart_open,
                    ),
                    rx.cond(
                        AppState.wi_chart_open,
                        rx.box(
                            rx.cond(
                                AppState.wi_balance_svg != "",
                                rx.box(
                                    rx.html(AppState.wi_balance_svg),
                                    style={"padding": "14px 16px", "overflow_x": "auto"},
                                ),
                                rx.box(
                                    rx.text("Run a What-If scenario to see the balance trajectory.",
                                            style={"color": TEXT3, "font_size": "12px"}),
                                    style={"padding": "24px", "text_align": "center"},
                                ),
                            ),
                        ),
                        rx.box(),
                    ),
                    style={
                        "background": BG2, "border": f"1px solid {BORDER}",
                        "border_radius": "10px", "overflow": "hidden",
                        "margin_bottom": "8px",
                    },
                ),

                # ── Panel 2: Budget Timeline Grid ────────────────────────────
                rx.box(
                    _panel_hdr(
                        "grid",
                        '<rect x="3" y="3" width="18" height="4" rx="1"/>'
                        '<rect x="3" y="10" width="12" height="4" rx="1"/>'
                        '<rect x="3" y="17" width="15" height="4" rx="1"/>',
                        "Budget Timeline",
                        rx.hstack(
                            _kpi_chip("buckets", AppState.wi_grid_rows.length(), TEXT2),
                            gap="6px",
                        ),
                        AppState.wi_grid_open,
                    ),
                    rx.cond(
                        AppState.wi_grid_open,
                        rx.box(
                            rx.box(
                                rx.hstack(
                                    rx.box(style={"width": "14px", "height": "14px",
                                                  "background": "rgba(48,209,88,0.2)",
                                                  "border_left": "3px solid rgba(48,209,88,0.6)",
                                                  "border_radius": "2px"}),
                                    rx.text("Start", style={"font_size": "10px", "color": GREEN,
                                                             "font_family": MONO}),
                                    rx.box(style={"width": "14px", "height": "14px",
                                                  "background": "rgba(255,69,58,0.1)",
                                                  "border_left": "3px solid rgba(255,69,58,0.5)",
                                                  "border_radius": "2px"}),
                                    rx.text("Off", style={"font_size": "10px", "color": RED,
                                                           "font_family": MONO}),
                                    rx.box(style={"width": "14px", "height": "14px",
                                                  "background": "rgba(255,159,10,0.1)",
                                                  "border_left": "3px solid rgba(255,159,10,0.5)",
                                                  "border_radius": "2px"}),
                                    rx.text("Changed", style={"font_size": "10px", "color": AMBER,
                                                               "font_family": MONO}),
                                    rx.text("Click a cell to schedule changes",
                                            style={"font_size": "10px", "color": TEXT3,
                                                   "margin_left": "8px"}),
                                    gap="5px", align_items="center",
                                ),
                                style={"padding": "8px 14px",
                                       "border_bottom": f"1px solid {BORDER}",
                                       "background": BG3},
                            ),
                            _wi_grid_body(),
                            style={"padding_bottom": "4px"},
                        ),
                        rx.box(),
                    ),
                    style={
                        "background": BG2, "border": f"1px solid {BORDER}",
                        "border_radius": "10px", "overflow": "hidden",
                        "margin_bottom": "8px",
                    },
                ),

                # ── Panel 3: Periods / Intelligence ──────────────────────────
                rx.box(
                    _panel_hdr(
                        "periods",
                        '<circle cx="12" cy="12" r="10"/>'
                        '<polyline points="12 6 12 12 16 14"/>',
                        "Pay Periods",
                        rx.hstack(
                            rx.cond(
                                AppState.wi_periods.length() > 0,
                                _kpi_chip("periods", AppState.wi_periods.length(), TEXT2),
                                rx.box(),
                            ),
                            rx.cond(
                                AppState.wi_shortfall_count > 0,
                                _kpi_chip("shortfalls", AppState.wi_shortfall_count, RED),
                                rx.box(),
                            ),
                            gap="6px",
                        ),
                        AppState.wi_periods_open,
                    ),
                    rx.cond(
                        AppState.wi_periods_open,
                        rx.box(
                            # Sub-tab: Periods | Intel
                            rx.hstack(
                                rx.box(
                                    "Periods",
                                    on_click=AppState.set_wi_rp_tab("periods"),
                                    role="button", tab_index=0,
                                    style=rx.cond(
                                        AppState.wi_rp_tab == "periods",
                                        {"font_size": "11px", "font_family": MONO,
                                         "padding": "4px 12px", "border_radius": "14px",
                                         "cursor": "pointer", "background": f"{ACCENT}20",
                                         "color": "#D8A4FF", "border": f"1px solid {ACCENT}44"},
                                        {"font_size": "11px", "font_family": MONO,
                                         "padding": "4px 12px", "border_radius": "14px",
                                         "cursor": "pointer", "background": "transparent",
                                         "color": TEXT3, "border": f"1px solid {BORDER}",
                                         "_hover": {"color": TEXT2}},
                                    ),
                                ),
                                rx.box(
                                    "Intelligence",
                                    on_click=AppState.set_wi_rp_tab("intel"),
                                    role="button", tab_index=0,
                                    style=rx.cond(
                                        AppState.wi_rp_tab == "intel",
                                        {"font_size": "11px", "font_family": MONO,
                                         "padding": "4px 12px", "border_radius": "14px",
                                         "cursor": "pointer", "background": f"{ACCENT}20",
                                         "color": "#D8A4FF", "border": f"1px solid {ACCENT}44"},
                                        {"font_size": "11px", "font_family": MONO,
                                         "padding": "4px 12px", "border_radius": "14px",
                                         "cursor": "pointer", "background": "transparent",
                                         "color": TEXT3, "border": f"1px solid {BORDER}",
                                         "_hover": {"color": TEXT2}},
                                    ),
                                ),
                                gap="6px",
                                style={"padding": "10px 14px 8px",
                                       "border_bottom": f"1px solid {BORDER}"},
                            ),
                            # Periods tab content
                            rx.cond(
                                AppState.wi_rp_tab == "periods",
                                rx.box(
                                    rx.cond(
                                        AppState.wi_periods.length() > 0,
                                        rx.box(
                                            rx.foreach(AppState.wi_periods.to(list[dict[str, Any]]),
                                                       _period_card),
                                            style={"padding": "12px 4px"},
                                        ),
                                        rx.box(
                                            rx.text("No forecast data. Switch to the What-If grid and "
                                                    "click Apply to run the forecast.",
                                                    style={"color": TEXT3, "font_size": "12px",
                                                           "text_align": "center"}),
                                            style={"padding": "32px 20px"},
                                        ),
                                    ),
                                ),
                                # Intelligence tab
                                rx.vstack(
                                    # Shortfall alert
                                    rx.cond(
                                        AppState.wi_shortfall_count > 0,
                                        rx.hstack(
                                            rx.text("⚠",
                                                    style={"font_size": "18px", "flex_shrink": "0"}),
                                            rx.vstack(
                                                rx.text("Balance Shortfall",
                                                        style={"font_size": "13px",
                                                               "font_weight": "700",
                                                               "color": RED}),
                                                rx.text(
                                                    AppState.forecast_shortfall_label,
                                                    style={"font_size": "12px", "color": TEXT3},
                                                ),
                                                gap="2px", align_items="flex_start",
                                            ),
                                            gap="12px", align_items="flex_start", width="100%",
                                            style={"background": f"{RED}10",
                                                   "border": f"1px solid {RED}33",
                                                   "border_radius": "8px", "padding": "12px 14px"},
                                        ),
                                        rx.box(),
                                    ),
                                    # Summary cards
                                    rx.hstack(
                                        rx.vstack(
                                            rx.text("Total Income",
                                                    style={"font_size": "11px", "color": TEXT3,
                                                           "font_family": MONO}),
                                            rx.text(AppState.wi_total_income,
                                                    style={"font_size": "16px", "font_weight": "700",
                                                           "font_family": MONO, "color": GREEN}),
                                            gap="3px", align_items="flex_start",
                                            style={"flex": "1", "background": f"{GREEN}08",
                                                   "border_radius": "8px", "padding": "12px 14px",
                                                   "border": f"1px solid {GREEN}22"},
                                        ),
                                        rx.vstack(
                                            rx.text("Total Unfunded",
                                                    style={"font_size": "11px", "color": TEXT3,
                                                           "font_family": MONO}),
                                            rx.text(AppState.wi_total_unfunded,
                                                    style={"font_size": "16px", "font_weight": "700",
                                                           "font_family": MONO, "color": RED}),
                                            gap="3px", align_items="flex_start",
                                            style={"flex": "1", "background": f"{RED}08",
                                                   "border_radius": "8px", "padding": "12px 14px",
                                                   "border": f"1px solid {RED}22"},
                                        ),
                                        gap="10px", width="100%",
                                    ),
                                    rx.vstack(
                                        rx.text("Safe to Spend",
                                                style={"font_size": "11px", "color": TEXT3,
                                                       "font_family": MONO}),
                                        rx.text(AppState.wi_safe_to_spend,
                                                style={"font_size": "22px", "font_weight": "700",
                                                       "font_family": MONO,
                                                       "color": AppState.wi_sts_color}),
                                        gap="4px", align_items="flex_start", width="100%",
                                        style={"background": BG3, "border_radius": "8px",
                                               "padding": "14px 16px",
                                               "border": f"1px solid {BORDER}"},
                                    ),
                                    gap="10px", width="100%",
                                    style={"padding": "14px"},
                                ),
                            ),
                        ),
                        rx.box(),
                    ),
                    style={
                        "background": BG2, "border": f"1px solid {BORDER}",
                        "border_radius": "10px", "overflow": "hidden",
                    },
                ),

                gap="0px", flex="1",
                style={"min_width": "0", "overflow_y": "auto"},
            ),

            gap="0px", align_items="flex_start", width="100%",
            style={"min_height": "0"},
        ),

        # Cell popover overlay (fixed, outside scroll container)
        _cell_popover(),

        style={"position": "relative", "min_height": "0"},
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ── Main entry point ─────────────────────────────────────────────────────────
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
