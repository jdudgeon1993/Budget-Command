"""Reports panel — Budget vs Actual, Monthly Summary, Trends, Top Payees, Debt Tracker."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _section(title: str, *children) -> rx.Component:
    return rx.vstack(
        rx.text(title, style={
            "font_size": "11px", "letter_spacing": "0.14em",
            "text_transform": "uppercase", "color": TEXT3,
            "font_family": MONO, "padding_bottom": "8px",
            "border_bottom": f"1px solid {BORDER}", "width": "100%",
        }),
        *children,
        gap="10px", align_items="stretch", width="100%",
    )


def _cell_color(status: str) -> str:
    return {"over": "#f87171", "close": "#fbbf24", "ok": "#34d399"}.get(status, TEXT3)


def _var_color(var_str: str) -> str:
    if var_str.startswith("+") or var_str == "✓":
        return "#34d399"
    if var_str.startswith("-"):
        return "#f87171"
    return TEXT3


# ── Sub-tab switcher ──────────────────────────────────────────────────────────

def _tab(label: str, key: str) -> rx.Component:
    is_active = AppState.reports_tab == key
    return rx.box(
        label,
        on_click=AppState.set_reports_tab(key),
        style=rx.cond(
            is_active,
            {
                "padding": "7px 14px", "border_radius": "8px",
                "background": f"{ACCENT}20", "color": ACCENT,
                "font_size": "12px", "font_family": MONO,
                "letter_spacing": "0.06em", "cursor": "pointer",
                "white_space": "nowrap",
                "border": f"1px solid {ACCENT}44",
            },
            {
                "padding": "7px 14px", "border_radius": "8px",
                "background": "transparent", "color": TEXT3,
                "font_size": "12px", "font_family": MONO,
                "letter_spacing": "0.06em", "cursor": "pointer",
                "white_space": "nowrap",
                "_hover": {"color": TEXT2, "background": BG3},
            },
        ),
    )


def _tab_bar() -> rx.Component:
    return rx.hstack(
        _tab("Snapshot",         "snapshot"),
        _tab("Budget vs Actual", "bva"),
        _tab("Monthly Summary",  "summary"),
        _tab("Trends",           "trends"),
        _tab("Top Payees",       "payees"),
        _tab("Debt Tracker",     "debt"),
        gap="4px",
        style={
            "overflow_x": "auto", "padding_bottom": "2px",
            "flex_wrap": "nowrap", "width": "100%",
        },
    )


# ── Budget vs Actual ──────────────────────────────────────────────────────────

def _bva_month_cell(bar_w, spent, budget, var_str, var_color, status, show) -> rx.Component:
    c = rx.cond(
        status == "over",  "#f87171",
        rx.cond(status == "close", "#fbbf24", "#34d399"),
    )
    return rx.cond(
        show == "1",
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text(spent, style={
                        "font_size": "13px", "font_weight": "700",
                        "font_family": MONO, "color": c,
                    }),
                    rx.text(budget, style={
                        "font_size": "11px", "color": TEXT3,
                        "font_family": MONO,
                    }),
                    gap="4px", align_items="baseline",
                ),
                rx.box(
                    rx.box(style={
                        "height": "3px", "border_radius": "2px",
                        "background": c, "width": bar_w,
                        "transition": "width 0.3s ease",
                    }),
                    style={
                        "height": "3px", "border_radius": "2px",
                        "background": BG3, "width": "100%", "overflow": "hidden",
                    },
                ),
                rx.text(var_str, style={
                    "font_size": "10px", "font_family": MONO,
                    "color": var_color,
                }),
                gap="3px", align_items="flex-start", width="100%",
            ),
            style={"min_width": "130px", "flex": "1", "padding": "4px 8px"},
        ),
        rx.box(style={"min_width": "130px", "flex": "1"}),
    )


def _bva_row(row: dict) -> rx.Component:
    is_cat = row["row_type"] == "cat"
    return rx.cond(
        is_cat,
        # Category header
        rx.hstack(
            rx.box(style={
                "width": "8px", "height": "8px", "border_radius": "50%",
                "background": row["color"], "flex_shrink": "0",
                "margin_top": "4px",
            }),
            rx.text(row["name"], style={
                "font_size": "11px", "font_weight": "700", "color": TEXT3,
                "letter_spacing": "0.1em", "text_transform": "uppercase",
                "font_family": MONO,
            }),
            width="100%", padding="10px 8px 4px",
            style={"border_top": f"1px solid {BORDER}"},
        ),
        # Bucket row
        rx.hstack(
            # Bucket name
            rx.text(row["name"], style={
                "font_size": "13px", "color": TEXT, "font_weight": "500",
                "min_width": "140px", "flex": "2", "padding_left": "16px",
            }),
            # Month cells
            _bva_month_cell(row["m0_bar_w"], row["m0_spent"], row["m0_budget"],
                            row["m0_var"], row["m0_var_color"], row["m0_status"], row["show_m0"]),
            _bva_month_cell(row["m1_bar_w"], row["m1_spent"], row["m1_budget"],
                            row["m1_var"], row["m1_var_color"], row["m1_status"], row["show_m1"]),
            _bva_month_cell(row["m2_bar_w"], row["m2_spent"], row["m2_budget"],
                            row["m2_var"], row["m2_var_color"], row["m2_status"], row["show_m2"]),
            # Avg
            rx.vstack(
                rx.text(row["avg_spent"], style={
                    "font_size": "12px", "font_family": MONO,
                    "color": rx.cond(row["avg_status"] == "over", "#f87171",
                             rx.cond(row["avg_status"] == "close", "#fbbf24",
                                     TEXT2)),
                    "font_weight": "600",
                }),
                rx.text(row["avg_var"], style={
                    "font_size": "10px", "font_family": MONO,
                    "color": row["avg_var_color"],
                }),
                gap="2px", align_items="flex-start",
                style={"min_width": "90px", "flex": "1", "padding": "4px 8px"},
            ),
            align_items="center", width="100%",
            style={
                "padding": "6px 8px",
                "_hover": {"background": BG3},
                "border_radius": "4px",
            },
        ),
    )


def _bva_tab() -> rx.Component:
    return rx.vstack(
        # Column headers
        rx.hstack(
            rx.text("Bucket", style={
                "font_size": "11px", "color": TEXT3, "font_family": MONO,
                "letter_spacing": "0.1em", "min_width": "140px", "flex": "2",
                "padding_left": "16px",
            }),
            rx.foreach(
                AppState.bva_month_hdrs.to(list[dict[str, Any]]),
                lambda h: rx.cond(
                    h["label"] != "",
                    rx.text(h["label"], style={
                        "font_size": "11px", "color": TEXT3, "font_family": MONO,
                        "letter_spacing": "0.08em", "min_width": "130px", "flex": "1",
                        "padding": "0 8px",
                    }),
                    rx.box(style={"min_width": "130px", "flex": "1"}),
                ),
            ),
            rx.text("Avg", style={
                "font_size": "11px", "color": TEXT3, "font_family": MONO,
                "letter_spacing": "0.1em", "min_width": "90px", "flex": "1",
                "padding": "0 8px",
            }),
            width="100%", padding="8px 8px 6px",
            style={"border_bottom": f"1px solid {BORDER}"},
        ),
        rx.cond(
            AppState.bva_rows.length() == 0,
            rx.text("No data yet — add transactions across a few months.",
                    style={"color": TEXT3, "font_size": "12px", "font_family": MONO,
                           "padding": "20px 0"}),
            rx.foreach(AppState.bva_rows.to(list[dict[str, Any]]), _bva_row),
        ),
        gap="0px", align_items="stretch", width="100%",
        style={"overflow_x": "auto"},
    )


# ── Monthly Summary ───────────────────────────────────────────────────────────

def _summary_cat_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.box(style={
            "width": "7px", "height": "7px", "border_radius": "50%",
            "background": row["color"], "flex_shrink": "0",
        }),
        rx.text(row["name"], style={
            "font_size": "12px", "color": TEXT2, "flex": "1",
        }),
        rx.text(row["spent_fmt"], style={
            "font_size": "12px", "font_family": MONO,
            "color": rx.cond(row["is_over"] == "1", "#f87171", TEXT),
        }),
        rx.box(
            rx.box(style={
                "height": "3px", "border_radius": "2px",
                "background": rx.cond(row["is_over"] == "1", "#f87171", row["color"]),
                "width": row["bar_w"],
            }),
            style={
                "height": "3px", "border_radius": "2px",
                "background": BG3, "width": "60px", "overflow": "hidden",
                "flex_shrink": "0",
            },
        ),
        align_items="center", width="100%", gap="8px",
        style={"padding": "4px 0"},
    )


def _summary_card(card: dict) -> rx.Component:
    return rx.vstack(
        # Header
        rx.text(card["label"], style={
            "font_size": "13px", "font_weight": "700", "color": TEXT,
            "letter_spacing": "0.06em",
        }),
        rx.divider(style={"border_color": BORDER}),
        # KPIs
        rx.hstack(
            rx.vstack(
                rx.text("Income", style={"font_size": "10px", "color": TEXT3,
                                          "letter_spacing": "0.08em",
                                          "text_transform": "uppercase",
                                          "font_family": MONO}),
                rx.text(card["income_fmt"], style={
                    "font_size": "15px", "font_weight": "700",
                    "font_family": MONO, "color": GREEN,
                }),
                gap="2px",
            ),
            rx.vstack(
                rx.text("Spent", style={"font_size": "10px", "color": TEXT3,
                                         "letter_spacing": "0.08em",
                                         "text_transform": "uppercase",
                                         "font_family": MONO}),
                rx.text(card["spent_fmt"], style={
                    "font_size": "15px", "font_weight": "700",
                    "font_family": MONO, "color": AMBER,
                }),
                gap="2px",
            ),
            rx.vstack(
                rx.text("Net", style={"font_size": "10px", "color": TEXT3,
                                       "letter_spacing": "0.08em",
                                       "text_transform": "uppercase",
                                       "font_family": MONO}),
                rx.text(card["net_fmt"], style={
                    "font_size": "15px", "font_weight": "700",
                    "font_family": MONO, "color": card["net_color"],
                }),
                gap="2px",
            ),
            rx.vstack(
                rx.text("Saved", style={"font_size": "10px", "color": TEXT3,
                                         "letter_spacing": "0.08em",
                                         "text_transform": "uppercase",
                                         "font_family": MONO}),
                rx.text(card["savings_rate"], style={
                    "font_size": "15px", "font_weight": "700",
                    "font_family": MONO, "color": ACCENT,
                }),
                gap="2px",
            ),
            justify="between", width="100%",
        ),
        rx.divider(style={"border_color": BORDER}),
        # Category breakdown
        rx.text("By Category", style={
            "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
            "text_transform": "uppercase", "font_family": MONO,
        }),
        rx.foreach(
            card["cat_rows"].to(list[dict[str, Any]]),
            _summary_cat_row,
        ),
        gap="8px", align_items="stretch",
        style={
            "background": BG2, "border": f"1px solid {BORDER}",
            "border_radius": "12px", "padding": "16px",
            "flex": "1", "min_width": "240px",
        },
    )


def _summary_tab() -> rx.Component:
    return rx.cond(
        AppState.summary_cards.length() == 0,
        rx.text("No data yet.",
                style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
        rx.hstack(
            rx.foreach(AppState.summary_cards, _summary_card),
            gap="16px", align_items="flex-start", width="100%",
            style={"flex_wrap": "wrap"},
        ),
    )


# ── Trends ────────────────────────────────────────────────────────────────────

def _trend_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.text(row["label"], style={
            "font_size": "13px", "color": TEXT, "font_weight": "600",
            "min_width": "100px", "font_family": MONO,
        }),
        rx.text(row["income_fmt"], style={
            "font_size": "13px", "font_family": MONO, "color": GREEN,
            "min_width": "100px",
        }),
        rx.text(row["spent_fmt"], style={
            "font_size": "13px", "font_family": MONO, "color": AMBER,
            "min_width": "100px",
        }),
        rx.text(row["net_fmt"], style={
            "font_size": "13px", "font_family": MONO,
            "color": row["net_color"], "font_weight": "600",
            "min_width": "100px",
        }),
        rx.text(row["savings_rate"], style={
            "font_size": "13px", "font_family": MONO,
            "color": row["rate_color"],
        }),
        align_items="center", width="100%", gap="8px",
        style={
            "padding": "10px 12px", "border_radius": "8px",
            "_hover": {"background": BG3},
        },
    )


def _trends_tab() -> rx.Component:
    return rx.vstack(
        # SVG chart
        rx.cond(
            AppState.trend_svg != "",
            rx.box(
                rx.html(AppState.trend_svg),
                style={
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "12px", "padding": "16px 20px",
                    "overflow_x": "auto",
                },
            ),
            rx.box(),
        ),
        # Data table
        rx.cond(
            AppState.trend_rows.length() == 0,
            rx.text("No data yet.",
                    style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
            rx.vstack(
                # Headers
                rx.hstack(
                    rx.text("Month",       style={"font_size": "11px", "color": TEXT3, "font_family": MONO, "min_width": "100px"}),
                    rx.text("Income",      style={"font_size": "11px", "color": TEXT3, "font_family": MONO, "min_width": "100px"}),
                    rx.text("Spending",    style={"font_size": "11px", "color": TEXT3, "font_family": MONO, "min_width": "100px"}),
                    rx.text("Net",         style={"font_size": "11px", "color": TEXT3, "font_family": MONO, "min_width": "100px"}),
                    rx.text("Savings %",   style={"font_size": "11px", "color": TEXT3, "font_family": MONO}),
                    width="100%", padding="6px 12px",
                    style={"border_bottom": f"1px solid {BORDER}"},
                ),
                rx.foreach(AppState.trend_rows.to(list[dict[str, Any]]), _trend_row),
                gap="0px", align_items="stretch", width="100%",
                style={
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "12px", "overflow": "hidden",
                },
            ),
        ),
        gap="16px", align_items="stretch", width="100%",
    )


# ── Top Payees ────────────────────────────────────────────────────────────────

def _payee_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(row["payee"], style={
                    "font_size": "13px", "color": TEXT, "font_weight": "500",
                }),
                rx.cond(
                    row["cat_name"] != "",
                    rx.text(row["cat_name"], style={
                        "font_size": "11px", "color": TEXT3,
                        "background": BG3, "padding": "1px 6px",
                        "border_radius": "4px", "font_family": MONO,
                    }),
                    rx.box(),
                ),
                gap="6px", align_items="center", flex_wrap="wrap",
            ),
            rx.hstack(
                rx.text(row["count"], " transactions",
                        style={"font_size": "11px", "color": TEXT3, "font_family": MONO}),
                rx.text("·", style={"color": TEXT3}),
                rx.text(row["pct_str"], " of total",
                        style={"font_size": "11px", "color": TEXT3, "font_family": MONO}),
                gap="4px",
            ),
            # Bar
            rx.box(
                rx.box(style={
                    "height": "3px", "border_radius": "2px",
                    "background": ACCENT, "width": row["bar_w"],
                    "transition": "width 0.3s ease",
                }),
                style={
                    "height": "3px", "border_radius": "2px",
                    "background": BG3, "width": "100%", "overflow": "hidden",
                },
            ),
            gap="3px", align_items="stretch", flex="1",
        ),
        rx.text(row["total_fmt"], style={
            "font_size": "14px", "font_weight": "700",
            "font_family": MONO, "color": AMBER, "white_space": "nowrap",
        }),
        align_items="flex-start", width="100%", gap="12px",
        style={
            "padding": "10px 14px", "border_radius": "8px",
            "_hover": {"background": BG3},
        },
    )


def _payees_tab() -> rx.Component:
    return rx.cond(
        AppState.payee_spend_rows.length() == 0,
        rx.text("No spending data yet.",
                style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
        rx.vstack(
            rx.hstack(
                rx.text("Payee / Description", style={
                    "font_size": "11px", "color": TEXT3, "font_family": MONO,
                    "flex": "1",
                }),
                rx.text("Total", style={
                    "font_size": "11px", "color": TEXT3, "font_family": MONO,
                }),
                width="100%", padding="6px 14px",
                style={"border_bottom": f"1px solid {BORDER}"},
            ),
            rx.foreach(AppState.payee_spend_rows.to(list[dict[str, Any]]), _payee_row),
            gap="0px", align_items="stretch", width="100%",
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "12px", "overflow": "hidden",
            },
        ),
    )


# ── Debt Tracker ──────────────────────────────────────────────────────────────

def _debt_month_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.text(row["label"], style={
            "font_size": "12px", "color": TEXT2, "font_family": MONO, "flex": "1",
        }),
        rx.text(row["paid_fmt"], style={
            "font_size": "12px", "font_family": MONO,
            "color": rx.cond(row["paid_fmt"] == "—", TEXT3, GREEN),
            "font_weight": "600",
        }),
        align_items="center", width="100%",
        style={"padding": "4px 0"},
    )


def _debt_card(row: dict) -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.box(style={
                "width": "10px", "height": "10px", "border_radius": "50%",
                "background": row["color"], "flex_shrink": "0",
            }),
            rx.text(row["name"], style={
                "font_size": "14px", "font_weight": "700", "color": TEXT,
            }),
            align_items="center", gap="8px",
        ),
        rx.divider(style={"border_color": BORDER}),
        # Stats grid
        rx.hstack(
            rx.vstack(
                rx.text("Balance", style={"font_size": "10px", "color": TEXT3,
                                           "text_transform": "uppercase",
                                           "font_family": MONO, "letter_spacing": "0.08em"}),
                rx.text(row["balance_fmt"], style={
                    "font_size": "16px", "font_weight": "700",
                    "font_family": MONO, "color": RED,
                }),
                gap="2px",
            ),
            rx.vstack(
                rx.text("Lifetime Paid", style={"font_size": "10px", "color": TEXT3,
                                                 "text_transform": "uppercase",
                                                 "font_family": MONO, "letter_spacing": "0.08em"}),
                rx.text(row["total_paid_fmt"], style={
                    "font_size": "16px", "font_weight": "700",
                    "font_family": MONO, "color": GREEN,
                }),
                gap="2px",
            ),
            rx.vstack(
                rx.text("Avg payment", style={"font_size": "10px", "color": TEXT3,
                                               "text_transform": "uppercase",
                                               "font_family": MONO, "letter_spacing": "0.08em"}),
                rx.text(row["avg_payment_fmt"], style={
                    "font_size": "16px", "font_weight": "700",
                    "font_family": MONO, "color": TEXT2,
                }),
                gap="2px",
            ),
            justify="between", width="100%",
        ),
        rx.divider(style={"border_color": BORDER}),
        rx.text("Payments by Month", style={
            "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
            "text_transform": "uppercase", "font_family": MONO,
        }),
        rx.foreach(
            row["months"].to(list[dict[str, Any]]),
            _debt_month_row,
        ),
        gap="10px", align_items="stretch",
        style={
            "background": BG2, "border": f"1px solid {BORDER}",
            "border_radius": "12px", "padding": "16px",
            "min_width": "260px", "flex": "1",
        },
    )


def _debt_tab() -> rx.Component:
    return rx.cond(
        AppState.debt_tracker_rows.length() == 0,
        rx.text("No debt accounts. Add one in Accounts.",
                style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
        rx.hstack(
            rx.foreach(AppState.debt_tracker_rows, _debt_card),
            gap="16px", align_items="flex-start", width="100%",
            style={"flex_wrap": "wrap"},
        ),
    )


# ── Snapshot tab (monthly KPIs + account balances + spend by bucket) ─────────

def _snapshot_account_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.box(style={
            "width": "9px", "height": "9px", "border_radius": "50%",
            "background": row["color"], "flex_shrink": "0",
        }),
        rx.text(row["name"], style={
            "font_size": "13px", "color": TEXT, "flex": "1",
            "min_width": "0", "overflow": "hidden",
            "text_overflow": "ellipsis", "white_space": "nowrap",
        }),
        rx.text(row["balance_fmt"], style={
            "font_size": "13px", "font_family": MONO, "font_weight": "700",
            "color": row["bal_color"], "white_space": "nowrap", "flex_shrink": "0",
        }),
        align_items="center", gap="9px", width="100%",
        style={"margin_bottom": "6px"},
    )


def _snapshot_spend_bar(row: dict) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(row["name"], style={
                "font_size": "13px", "color": TEXT, "flex": "1",
                "min_width": "0", "overflow": "hidden",
                "text_overflow": "ellipsis", "white_space": "nowrap",
                "font_weight": "600",
            }),
            rx.hstack(
                rx.text(row["spent_fmt"], style={
                    "font_size": "13px", "font_family": MONO,
                    "color": rx.cond(row["is_over"] == "1", RED, TEXT2),
                    "white_space": "nowrap",
                }),
                rx.cond(
                    row["pct_str"] != "0%",
                    rx.text(row["pct_str"], style={
                        "font_size": "11px", "font_family": MONO,
                        "color": rx.cond(row["is_over"] == "1", RED, TEXT3),
                        "white_space": "nowrap",
                    }),
                    rx.box(),
                ),
                gap="5px", align_items="center", flex_shrink="0",
            ),
            align_items="center", gap="8px", width="100%",
        ),
        rx.box(
            rx.box(style={
                "height": "100%", "border_radius": "3px",
                "background": rx.cond(row["is_over"] == "1", RED, ACCENT),
                "width": row["pct_str"],
                "transition": "width 0.35s ease",
            }),
            style={
                "height": "5px", "border_radius": "3px",
                "background": BG3, "overflow": "hidden", "width": "100%",
            },
        ),
        gap="5px", width="100%",
        style={"margin_bottom": "10px"},
    )


def _snapshot_tab() -> rx.Component:
    _CARD = {
        "background": BG2, "border": f"1px solid {BORDER}",
        "border_radius": "12px", "padding": "16px 18px",
        "margin_bottom": "14px", "width": "100%",
    }
    _LABEL = {
        "font_size": "11px", "letter_spacing": "0.14em",
        "text_transform": "uppercase", "color": TEXT3,
        "font_family": MONO, "font_weight": "600",
        "display": "block", "margin_bottom": "12px",
    }
    return rx.box(
        rx.box(
            # Left: KPIs + spend breakdown
            rx.vstack(
                # This Month
                rx.box(
                    rx.text("THIS MONTH", style=_LABEL),
                    rx.hstack(
                        rx.hstack(
                            rx.box(style={
                                "width": "7px", "height": "7px", "border_radius": "50%",
                                "background": GREEN, "flex_shrink": "0",
                            }),
                            rx.text("Income", style={"font_size": "12px", "color": TEXT3}),
                            rx.text(AppState.income_fmt, style={
                                "font_size": "14px", "color": GREEN,
                                "font_family": MONO, "font_weight": "700",
                            }),
                            align_items="center", gap="6px",
                        ),
                        rx.hstack(
                            rx.box(style={
                                "width": "7px", "height": "7px", "border_radius": "50%",
                                "background": RED, "flex_shrink": "0",
                            }),
                            rx.text("Spent", style={"font_size": "12px", "color": TEXT3}),
                            rx.text(AppState.spent_fmt, style={
                                "font_size": "14px", "color": RED,
                                "font_family": MONO, "font_weight": "700",
                            }),
                            align_items="center", gap="6px",
                        ),
                        gap="16px", flex_wrap="wrap",
                    ),
                    rx.divider(style={"border_color": BORDER, "margin": "10px 0"}),
                    rx.hstack(
                        rx.text("Net (Ready to Spend)", style={"font_size": "13px", "color": TEXT3}),
                        rx.spacer(),
                        rx.text(AppState.rts_fmt, style={
                            "font_size": "15px", "font_family": MONO, "font_weight": "800",
                            "color": AppState.rts_color,
                        }),
                        align_items="center", width="100%",
                    ),
                    style=_CARD,
                ),

                # VS Last Month
                rx.box(
                    rx.text("VS LAST MONTH", style=_LABEL),
                    rx.hstack(
                        rx.vstack(
                            rx.text("", style={"font_size": "12px", "color": "transparent"}),
                            rx.text("Income", style={"font_size": "13px", "color": TEXT3}),
                            rx.text("Spent",  style={"font_size": "13px", "color": TEXT3}),
                            gap="8px", align_items="flex-start",
                        ),
                        rx.spacer(),
                        rx.vstack(
                            rx.text("This", style={
                                "font_size": "12px", "color": TEXT3,
                                "letter_spacing": "0.08em", "font_family": MONO,
                            }),
                            rx.text(AppState.income_fmt, style={
                                "font_size": "13px", "color": GREEN,
                                "font_family": MONO, "font_weight": "600",
                            }),
                            rx.text(AppState.spent_fmt, style={
                                "font_size": "13px", "color": RED,
                                "font_family": MONO, "font_weight": "600",
                            }),
                            gap="8px", align_items="flex-end",
                        ),
                        rx.vstack(
                            rx.text("Last", style={
                                "font_size": "12px", "color": TEXT3,
                                "letter_spacing": "0.08em", "font_family": MONO,
                            }),
                            rx.text(AppState.last_month_income_fmt, style={
                                "font_size": "13px", "color": TEXT2,
                                "font_family": MONO,
                            }),
                            rx.text(AppState.last_month_spent_fmt, style={
                                "font_size": "13px", "color": TEXT2,
                                "font_family": MONO,
                            }),
                            gap="8px", align_items="flex-end",
                        ),
                        align_items="flex-start", width="100%",
                    ),
                    rx.divider(style={"border_color": BORDER, "margin": "10px 0"}),
                    rx.text(AppState.mom_verdict, style={
                        "font_size": "13px", "font_family": MONO, "font_weight": "700",
                        "color": rx.cond(AppState.mom_better, GREEN, RED),
                    }),
                    style=_CARD,
                ),

                # Spending by Bucket
                rx.cond(
                    AppState.ledger_bucket_spend.length() > 0,
                    rx.box(
                        rx.text("SPENDING BY BUCKET", style=_LABEL),
                        rx.foreach(
                            AppState.ledger_bucket_spend.to(list[dict[str, Any]]),
                            _snapshot_spend_bar,
                        ),
                        style=_CARD,
                    ),
                    rx.box(),
                ),

                gap="0", align_items="stretch", width="100%",
            ),

            # Right: Account balances
            rx.box(
                rx.box(
                    rx.text("ACCOUNTS", style=_LABEL),
                    rx.foreach(
                        AppState.accounts_rows.to(list[dict[str, Any]]),
                        _snapshot_account_row,
                    ),
                    rx.divider(style={"border_color": BORDER, "margin": "8px 0 10px"}),
                    rx.hstack(
                        rx.text("Cash", style={"font_size": "13px", "color": TEXT3}),
                        rx.spacer(),
                        rx.text(AppState.total_cash_fmt, style={
                            "font_size": "14px", "font_family": MONO,
                            "font_weight": "700", "color": GREEN,
                        }),
                        align_items="center", width="100%",
                        style={"margin_bottom": "5px"},
                    ),
                    rx.cond(
                        AppState.total_debt > 0,
                        rx.hstack(
                            rx.text("Debt", style={"font_size": "13px", "color": TEXT3}),
                            rx.spacer(),
                            rx.text(AppState.total_debt_fmt, style={
                                "font_size": "14px", "font_family": MONO,
                                "font_weight": "700", "color": RED,
                            }),
                            align_items="center", width="100%",
                        ),
                        rx.box(),
                    ),
                    style=_CARD,
                ),
                style={"position": "sticky", "top": "72px"},
            ),

            class_name="split-grid",
            style={
                "display": "grid",
                "grid_template_columns": "1fr 340px",
                "gap": "24px",
                "align_items": "start",
                "width": "100%",
            },
        ),
    )


# ── Main panel ────────────────────────────────────────────────────────────────

def reports_panel() -> rx.Component:
    return rx.vstack(
        _tab_bar(),
        rx.match(
            AppState.reports_tab,
            ("snapshot", _snapshot_tab()),
            ("bva",     _bva_tab()),
            ("summary", _summary_tab()),
            ("trends",  _trends_tab()),
            ("payees",  _payees_tab()),
            ("debt",    _debt_tab()),
            _snapshot_tab(),
        ),
        gap="20px", align_items="stretch", width="100%",
    )
