"""Forecast panel — paycheck-by-paycheck cash flow projection."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3, GREEN, AMBER, ACCENT, RED, MONO, SANS


# ── Helpers ───────────────────────────────────────────────────────────────────

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


# ── Bill line renderer ────────────────────────────────────────────────────────

def _funded_line(line: dict) -> rx.Component:
    """Renders a date header, bill row, or balance row (green) from a structured dict."""
    return rx.cond(
        line["row_type"] == "date",
        rx.text(
            line["text"],
            style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.08em",
                   "text_transform": "uppercase", "font_family": MONO,
                   "padding": "6px 0 2px"},
        ),
        rx.cond(
            line["row_type"] == "bal",
            rx.hstack(
                rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
                rx.text(line["text"], style={"font_size": "11px", "font_family": MONO, "color": TEXT2}),
                width="100%", justify="between",
                style={"padding": "2px 0 4px", "border_top": f"1px solid {BORDER}",
                       "margin_top": "3px"},
            ),
            rx.hstack(
                rx.text("✓", style={"color": GREEN, "font_size": "12px", "flex_shrink": "0"}),
                rx.text(line["text"],
                        style={"font_size": "12px", "color": TEXT, "flex": "1"}),
                rx.text(line["amount_fmt"],
                        style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
                width="100%", justify="between", align_items="center",
            ),
        ),
    )


def _unfunded_line(line: dict) -> rx.Component:
    """Renders a date header, bill row, or balance row (red) from a structured dict."""
    return rx.cond(
        line["row_type"] == "date",
        rx.text(
            line["text"],
            style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.08em",
                   "text_transform": "uppercase", "font_family": MONO,
                   "padding": "6px 0 2px"},
        ),
        rx.cond(
            line["row_type"] == "bal",
            rx.hstack(
                rx.text("Balance", style={"font_size": "10px", "color": TEXT3, "flex": "1"}),
                rx.text(line["text"], style={"font_size": "11px", "font_family": MONO,
                                              "color": rx.cond(line["text"].startswith("-"), RED, TEXT2)}),
                width="100%", justify="between",
                style={"padding": "2px 0 4px", "border_top": f"1px solid {BORDER}",
                       "margin_top": "3px"},
            ),
            rx.hstack(
                rx.text("⚠", style={"color": AMBER, "font_size": "12px", "flex_shrink": "0"}),
                rx.text(line["text"],
                        style={"font_size": "12px", "color": TEXT, "flex": "1"}),
                rx.text(line["amount_fmt"],
                        style={"font_size": "12px", "font_family": MONO, "color": RED}),
                width="100%", justify="between", align_items="center",
            ),
        ),
    )


def _income_line(line: dict) -> rx.Component:
    return rx.hstack(
        rx.text("💰", style={"font_size": "12px", "flex_shrink": "0"}),
        rx.text(line["label"], style={"font_size": "12px", "color": TEXT, "flex": "1"}),
        rx.text(line["amount_fmt"], style={"font_size": "12px", "font_family": MONO, "color": GREEN}),
        width="100%", justify="between", align_items="center",
    )


def _transfer_line(line: dict) -> rx.Component:
    return rx.hstack(
        rx.text("→", style={"font_size": "12px", "color": TEXT3, "flex_shrink": "0"}),
        rx.text(line["label"], style={"font_size": "12px", "color": TEXT2, "flex": "1"}),
        rx.text(line["amount_fmt"], style={"font_size": "12px", "font_family": MONO, "color": AMBER}),
        width="100%", justify="between", align_items="center",
    )


# ── Period card ───────────────────────────────────────────────────────────────

def _period_card(p: dict) -> rx.Component:
    is_expanded = AppState.fc_expanded.contains(p["id"])  # type: ignore[attr-defined]
    shortfall_border = rx.cond(
        p["shortfall"],
        f"2px solid {RED}",
        rx.cond(p["type"] == "gap", f"1px solid {BORDER}", f"1px solid {BORDER2}"),
    )

    header = rx.hstack(
        # Type badge
        rx.box(
            rx.cond(p["type"] == "gap", "GAP", "PAY"),
            style={
                "font_size": "8px", "font_family": MONO, "letter_spacing": "0.1em",
                "padding": "2px 6px", "border_radius": "4px",
                "background": rx.cond(p["type"] == "gap", BG3, f"{ACCENT}22"),
                "color": rx.cond(p["type"] == "gap", TEXT3, ACCENT),
                "border": rx.cond(p["type"] == "gap", f"1px solid {BORDER}", f"1px solid {ACCENT}44"),
                "flex_shrink": "0",
            },
        ),
        # Label + date range
        rx.vstack(
            rx.text(p["label"],
                    style={"font_size": "13px", "font_weight": "600", "color": TEXT}),
            rx.text(p["date_range"],
                    style={"font_size": "10px", "color": TEXT3}),
            gap="1px", align_items="flex-start", flex="1",
        ),
        rx.spacer(),
        # Net change
        rx.vstack(
            rx.hstack(
                rx.text(p["net_sign"],
                        style={"font_size": "12px", "font_family": MONO,
                               "color": rx.cond(p["net_negative"], RED, GREEN)}),
                rx.text(p["net_fmt"],
                        style={"font_size": "12px", "font_family": MONO,
                               "color": rx.cond(p["net_negative"], RED, GREEN)}),
                gap="0px",
            ),
            rx.text(p["end_bal_fmt"],
                    style={"font_size": "14px", "font_weight": "700", "font_family": MONO,
                           "color": rx.cond(p["end_bal_negative"], RED, TEXT)}),
            gap="0px", align_items="flex-end",
        ),
        # Expand chevron
        rx.box(
            rx.cond(is_expanded, "▲", "▼"),
            style={"font_size": "10px", "color": TEXT3, "padding": "0 4px", "flex_shrink": "0"},
        ),
        align_items="center", width="100%",
        on_click=AppState.toggle_fc_period(p["id"]),
        style={"cursor": "pointer"},
    )

    body = rx.cond(
        is_expanded,
        rx.vstack(
            rx.box(style={"height": "1px", "background": BORDER, "width": "100%",
                          "margin": "8px 0"}),

            # Start balance
            rx.hstack(
                rx.text("START", style={"font_size": "9px", "color": TEXT3,
                                        "font_family": MONO, "letter_spacing": "0.1em"}),
                rx.spacer(),
                rx.text(p["start_bal_fmt"],
                        style={"font_size": "12px", "font_family": MONO, "color": TEXT2}),
                width="100%",
            ),

            # Income section
            rx.cond(
                p["has_income"],
                rx.vstack(
                    rx.foreach(
                        p["income_lines"].to(list[dict[str, Any]]),
                        _income_line,
                    ),
                    width="100%", gap="4px",
                    style={"background": f"{GREEN}0a", "border_radius": "6px",
                           "padding": "8px", "margin_top": "4px"},
                ),
                rx.box(),
            ),

            # Transfers section
            rx.cond(
                p["has_transfers"],
                rx.vstack(
                    rx.foreach(
                        p["transfer_lines"].to(list[dict[str, Any]]),
                        _transfer_line,
                    ),
                    width="100%", gap="4px",
                    style={"background": f"{AMBER}0a", "border_radius": "6px",
                           "padding": "8px", "margin_top": "4px"},
                ),
                rx.box(),
            ),

            # Funded bills (green)
            rx.cond(
                p["has_funded"],
                rx.vstack(
                    rx.text("✓ Pre-Funded",
                            style={"font_size": "9px", "color": GREEN, "letter_spacing": "0.08em",
                                   "text_transform": "uppercase", "font_family": MONO,
                                   "margin_bottom": "4px"}),
                    rx.foreach(
                        p["funded_lines"].to(list[dict[str, Any]]),
                        _funded_line,
                    ),
                    width="100%", gap="3px",
                    style={"background": f"{GREEN}08", "border": f"1px solid {GREEN}22",
                           "border_radius": "6px", "padding": "8px", "margin_top": "4px"},
                ),
                rx.box(),
            ),

            # Unfunded bills (red)
            rx.cond(
                p["has_unfunded"],
                rx.vstack(
                    rx.text("⚠ Needs Funding",
                            style={"font_size": "9px", "color": AMBER, "letter_spacing": "0.08em",
                                   "text_transform": "uppercase", "font_family": MONO,
                                   "margin_bottom": "4px"}),
                    rx.foreach(
                        p["unfunded_lines"].to(list[dict[str, Any]]),
                        _unfunded_line,
                    ),
                    width="100%", gap="3px",
                    style={"background": f"{RED}08", "border": f"1px solid {RED}22",
                           "border_radius": "6px", "padding": "8px", "margin_top": "4px"},
                ),
                rx.box(),
            ),

            # End balance
            rx.hstack(
                rx.text("END", style={"font_size": "9px", "color": TEXT3,
                                      "font_family": MONO, "letter_spacing": "0.1em"}),
                rx.spacer(),
                rx.text(p["end_bal_fmt"],
                        style={"font_size": "14px", "font_weight": "700", "font_family": MONO,
                               "color": rx.cond(p["end_bal_negative"], RED, TEXT)}),
                width="100%",
                style={"border_top": f"1px solid {BORDER}", "padding_top": "8px",
                       "margin_top": "4px"},
            ),

            # Safe to spend
            rx.hstack(
                rx.text("Safe to spend from here",
                        style={"font_size": "10px", "color": TEXT3}),
                rx.spacer(),
                rx.text(p["safe_to_spend_fmt"],
                        style={"font_size": "12px", "font_family": MONO,
                               "color": p["sts_color"], "font_weight": "600"}),
                width="100%",
            ),

            width="100%", gap="4px",
        ),
        rx.box(),
    )

    return rx.box(
        header,
        body,
        style={
            "background": rx.cond(p["type"] == "gap", BG3, BG2),
            "border": shortfall_border,
            "border_radius": "10px",
            "padding": "12px 14px",
            "margin_bottom": "6px",
        },
    )


# ── Main panel ────────────────────────────────────────────────────────────────

def forecast_panel() -> rx.Component:
    return rx.box(
        # Controls bar
        rx.vstack(
            # Range selector
            rx.hstack(
                _range_btn("2 Mo", 2),
                _range_btn("3 Mo", 3),
                _range_btn("6 Mo", 6),
                _range_btn("12 Mo", 12),
                gap="6px",
            ),

            # Account chips
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

        # Summary bar
        rx.cond(
            AppState.forecast_loading,
            rx.box(
                rx.text("Computing forecast…",
                        style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
                style={"text_align": "center", "padding": "40px 0"},
            ),
            rx.box(
                # KPI row
                rx.hstack(
                    _kpi("Start Balance", AppState.fc_start_bal),
                    rx.box(style={"width": "1px", "background": BORDER,
                                  "align_self": "stretch"}),
                    _kpi("Total Income", AppState.fc_total_income, GREEN),
                    rx.box(style={"width": "1px", "background": BORDER,
                                  "align_self": "stretch"}),
                    _kpi("Unfunded", AppState.fc_total_unfunded, RED),
                    rx.box(style={"width": "1px", "background": BORDER,
                                  "align_self": "stretch"}),
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

        # Period cards
        rx.cond(
            ~AppState.forecast_loading,
            rx.foreach(
                AppState.forecast_periods.to(list[dict[str, Any]]),
                _period_card,
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
