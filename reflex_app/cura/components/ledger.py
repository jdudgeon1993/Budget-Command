"""Ledger panel — transaction list with search, month scoreboard, and add sheet."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, VIOLET, MONO, SANS)


# ── Shared form helpers (mirrors buckets.py) ──────────────────────────────────

def _input_style() -> dict:
    return {
        "background": BG3, "border": f"1px solid {BORDER}",
        "border_radius": "8px", "color": TEXT, "font_family": MONO,
        "font_size": "13px", "padding": "8px 12px", "outline": "none", "width": "100%",
        "_focus": {"border_color": ACCENT, "outline": "none"},
    }


def _select_style() -> dict:
    return {
        "background": BG3, "border": f"1px solid {BORDER}",
        "border_radius": "8px", "color": TEXT,
        "font_size": "13px", "padding": "8px 10px", "width": "100%",
    }


def _field(label: str, child: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={
            "font_size": "12px", "color": TEXT3, "letter_spacing": "0.1em",
            "text_transform": "uppercase", "font_family": MONO,
        }),
        child,
        gap="4px", align_items="stretch", width="100%",
    )


# ── Scoreboard card style (shared with buckets.py pattern) ───────────────────

_CARD = {
    "background": BG2,
    "border": f"1px solid {BORDER}",
    "border_radius": "12px",
    "padding": "16px 18px",
    "margin_bottom": "14px",
    "width": "100%",
}

_SECTION_LABEL = {
    "font_size": "11px", "letter_spacing": "0.14em",
    "text_transform": "uppercase", "color": TEXT3,
    "font_family": MONO, "font_weight": "600",
    "display": "block", "margin_bottom": "12px",
}


# ── Scoreboard sub-components ─────────────────────────────────────────────────

def _account_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.box(style={
            "width": "9px", "height": "9px", "border_radius": "50%",
            "background": row["color"], "flex_shrink": "0",
        }),
        rx.text(row["name"], style={
            "font_size": "14px", "color": TEXT, "flex": "1",
            "min_width": "0", "overflow": "hidden",
            "text_overflow": "ellipsis", "white_space": "nowrap",
        }),
        rx.text(row["balance_fmt"], style={
            "font_size": "14px", "font_family": MONO, "font_weight": "700",
            "color": row["bal_color"], "white_space": "nowrap", "flex_shrink": "0",
        }),
        align_items="center", gap="9px", width="100%",
        style={"margin_bottom": "7px"},
    )


def _spend_bar(row: dict) -> rx.Component:
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
            role="progressbar",
            aria_label=row["name"],
        ),
        gap="5px", width="100%",
        style={"margin_bottom": "10px"},
    )


# ── Ledger scoreboard (right column) ─────────────────────────────────────────

def _ledger_scoreboard() -> rx.Component:
    return rx.vstack(

        # 1. Accounts
        rx.box(
            rx.text("ACCOUNTS", style=_SECTION_LABEL),
            rx.foreach(
                AppState.accounts_rows.to(list[dict[str, Any]]),
                _account_row,
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

        # 2. This Month
        rx.box(
            rx.text("THIS MONTH", style=_SECTION_LABEL),
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
                rx.text("Net", style={"font_size": "13px", "color": TEXT3}),
                rx.spacer(),
                rx.text(AppState.rts_fmt, style={
                    "font_size": "15px", "font_family": MONO, "font_weight": "800",
                    "color": AppState.rts_color,
                }),
                align_items="center", width="100%",
            ),
            style=_CARD,
        ),

        # 3. VS Last Month
        rx.box(
            rx.text("VS LAST MONTH", style=_SECTION_LABEL),
            # Comparison table
            rx.hstack(
                # Row labels
                rx.vstack(
                    rx.text("", style={"font_size": "12px", "color": "transparent"}),
                    rx.text("Income", style={"font_size": "13px", "color": TEXT3}),
                    rx.text("Spent", style={"font_size": "13px", "color": TEXT3}),
                    gap="8px", align_items="flex-start",
                ),
                rx.spacer(),
                # This month column
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
                # Last month column
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
            # Verdict
            rx.text(AppState.mom_verdict, style={
                "font_size": "13px", "font_family": MONO, "font_weight": "700",
                "color": rx.cond(AppState.mom_better, GREEN, RED),
            }),
            style=_CARD,
        ),

        # 4. Spending by Bucket
        rx.cond(
            AppState.ledger_bucket_spend.length() > 0,
            rx.box(
                rx.text("SPENDING BY BUCKET", style=_SECTION_LABEL),
                rx.foreach(
                    AppState.ledger_bucket_spend.to(list[dict[str, Any]]),
                    _spend_bar,
                ),
                style=_CARD,
            ),
            rx.box(),
        ),

        gap="0", width="100%", align_items="stretch",
    )


# ── Month totals — compact one-liner at top of transaction list ───────────────

def _month_totals_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.text(row["inc_fmt"], style={
            "font_size": "13px", "color": GREEN, "font_family": MONO, "font_weight": "700",
        }),
        rx.text("income", style={"font_size": "12px", "color": TEXT3}),
        rx.text("·", style={"color": TEXT3, "font_size": "12px"}),
        rx.text(row["spent_fmt"], style={
            "font_size": "13px", "color": RED, "font_family": MONO, "font_weight": "700",
        }),
        rx.text("spent", style={"font_size": "12px", "color": TEXT3}),
        rx.text("·", style={"color": TEXT3, "font_size": "12px"}),
        rx.text("net", style={"font_size": "12px", "color": TEXT3}),
        rx.text(row["net_fmt"], style={
            "font_size": "14px", "font_family": MONO, "font_weight": "800",
            "color": row["net_color"],
        }),
        align_items="center", gap="6px", flex_wrap="wrap",
        style={
            "padding": "0 2px 16px",
            "border_bottom": f"1px solid {BORDER}",
            "margin_bottom": "16px",
        },
    )


# ── Transaction row ───────────────────────────────────────────────────────────

def _tx_row(row: dict) -> rx.Component:
    return rx.cond(
        row["row_type"] == "month_totals",
        _month_totals_row(row),

        # ── Transaction card (with optional date separator above) ────────────
        rx.vstack(
            # Date separator — shown when first tx of a new date
            rx.cond(
                row["date_label"] != "",
                rx.hstack(
                    rx.text(row["date_label"], style={
                        "font_size": "12px", "letter_spacing": "0.08em",
                        "text_transform": "uppercase", "color": TEXT2,
                        "font_family": MONO, "white_space": "nowrap",
                        "flex_shrink": "0", "font_weight": "600",
                    }),
                    rx.box(style={
                        "flex": "1", "height": "1px",
                        "background": BORDER2, "margin_left": "8px",
                    }),
                    align_items="center",
                    style={"padding": "18px 0 7px", "width": "100%"},
                ),
                rx.box(),
            ),

            # Transaction card
            rx.box(
                rx.hstack(
                    # Left: description + sub-label + chips
                    rx.vstack(
                        rx.text(
                            rx.cond(row["desc"] != "", row["desc"], "—"),
                            style={
                                "font_size": "15px", "font_weight": "600",
                                "line_height": "1.2",
                                "color": rx.cond(row["desc"] != "", TEXT, TEXT3),
                            },
                        ),
                        rx.hstack(
                            rx.text(
                                rx.cond(
                                    row["to_account"] != "",
                                    row["account"],
                                    rx.cond(row["bucket"] != "", row["bucket"], row["account"]),
                                ),
                                style={
                                    "font_size": "12px", "color": TEXT3,
                                    "font_family": MONO,
                                },
                            ),
                            rx.cond(
                                row["type_chip"] != "",
                                rx.text(row["type_chip"], style={
                                    "font_size": "11px", "font_family": MONO,
                                    "letter_spacing": "0.06em",
                                    "padding": "1px 7px", "border_radius": "6px",
                                    "color": row["chip_color"],
                                    "background": row["chip_bg"],
                                    "border": row["chip_border"],
                                    "white_space": "nowrap", "flex_shrink": "0",
                                }),
                                rx.box(),
                            ),
                            rx.cond(
                                row["reconciled_str"] != "",
                                rx.text("✓", style={
                                    "font_size": "11px", "color": GREEN,
                                    "font_family": MONO, "flex_shrink": "0",
                                }),
                                rx.box(),
                            ),
                            gap="6px", align_items="center",
                        ),
                        gap="4px", align_items="flex-start", flex="1", min_width="0",
                    ),

                    # Right: amount + edit
                    rx.hstack(
                        rx.text(row["amount_fmt"], style={
                            "font_size": "15px", "font_family": MONO, "font_weight": "700",
                            "color": row["amt_color"], "white_space": "nowrap",
                        }),
                        rx.box(
                            "⋯",
                            on_click=AppState.open_edit_tx(row["id"]),
                            role="button",
                            tab_index=0,
                            aria_label="Edit transaction",
                            style={
                                "font_size": "18px", "color": TEXT3, "cursor": "pointer",
                                "padding": "6px 10px", "border_radius": "6px",
                                "line_height": "1.2", "min_height": "36px",
                                "display": "flex", "align_items": "center",
                                "_hover": {"color": TEXT, "background": BG3},
                                "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
                            },
                        ),
                        align_items="center", gap="8px", flex_shrink="0",
                    ),

                    align_items="center", width="100%", gap="12px",
                ),
                style={
                    "background": BG2,
                    "border": f"1px solid {BORDER}",
                    "border_left": row["left_border"],
                    "border_radius": "8px",
                    "padding": rx.cond(
                        row["left_border"] != "none",
                        "11px 14px 11px 11px",
                        "11px 14px",
                    ),
                    "margin_bottom": "5px",
                    "_hover": {"border_color": BORDER2},
                },
            ),
            gap="0", width="100%",
        ),
    )


# ── Edit transaction dialog ───────────────────────────────────────────────────

def _type_pill(label: str, value: str, color: str) -> rx.Component:
    is_active = AppState.edit_tx_type == value
    return rx.text(label, style=rx.cond(
        is_active,
        {
            "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
            "padding": "4px 12px", "border_radius": "20px",
            "color": color, "background": color + "1a",
            "border": f"1px solid {color}55", "cursor": "pointer",
        },
        {
            "font_size": "11px", "font_family": MONO, "letter_spacing": "0.06em",
            "padding": "4px 12px", "border_radius": "20px",
            "color": TEXT3, "background": "transparent",
            "border": f"1px solid {BORDER}", "cursor": "pointer",
            "_hover": {"color": TEXT2, "border_color": BORDER2},
        },
    ),
    on_click=AppState.set_edit_tx_type(value),
    )


def edit_tx_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.text("TRANSACTION", style={
                            "font_size": "12px", "letter_spacing": "0.18em",
                            "color": TEXT3, "font_family": MONO,
                        }),
                        rx.hstack(
                            _type_pill("Expense",  "out", RED),
                            _type_pill("Income",   "in",  GREEN),
                            _type_pill("Transfer", "xfr", TEXT2),
                            gap="6px", align_items="center",
                        ),
                        gap="6px", align_items="flex-start",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box("×", style={
                            "font_size": "22px", "color": TEXT3, "cursor": "pointer",
                            "line_height": "1", "_hover": {"color": TEXT},
                        }),
                    ),
                    align_items="flex-start", width="100%",
                ),

                rx.divider(style={"border_color": BORDER}),

                # Amount
                _field("Amount ($)",
                    rx.input(
                        value=AppState.edit_tx_amount,
                        on_change=AppState.set_edit_tx_amount,
                        type="number", input_mode="decimal",
                        style={
                            **_input_style(),
                            "text_align": "center",
                            "color": rx.cond(
                                AppState.edit_tx_type == "in", GREEN,
                                rx.cond(AppState.edit_tx_type == "out", RED, TEXT2),
                            ),
                        },
                    )
                ),

                # Description
                _field("Description",
                    rx.input(
                        value=AppState.edit_tx_desc,
                        on_change=AppState.set_edit_tx_desc,
                        placeholder="What was this for?",
                        style=_input_style(),
                    )
                ),

                # Date + Account
                rx.hstack(
                    _field("Date",
                        rx.input(
                            type="date",
                            value=AppState.edit_tx_date,
                            on_change=AppState.set_edit_tx_date,
                            style=_input_style(),
                        )
                    ),
                    _field("Account",
                        rx.el.select(
                            AppState.account_options.to(list[dict[str, Any]]).foreach(
                                lambda a: rx.el.option(a["name"], value=a["id"])
                            ),
                            value=AppState.edit_tx_account,
                            on_change=AppState.set_edit_tx_account,
                            style=_select_style(),
                        )
                    ),
                    gap="10px", width="100%",
                ),

                # To Account — transfer only
                rx.cond(
                    AppState.edit_tx_type == "xfr",
                    _field("To Account",
                        rx.el.select(
                            AppState.account_options.to(list[dict[str, Any]]).foreach(
                                lambda a: rx.el.option(a["name"], value=a["id"])
                            ),
                            value=AppState.edit_tx_to_account,
                            on_change=AppState.set_edit_tx_to_account,
                            style=_select_style(),
                        )
                    ),
                    rx.box(),
                ),

                # Bucket — expense only
                rx.cond(
                    AppState.edit_tx_type == "out",
                    _field("Bucket",
                        rx.el.select(
                            rx.el.option("— No bucket —", value=""),
                            AppState.expense_buckets.to(list[dict[str, Any]]).foreach(
                                lambda b: rx.el.option(b["name"], value=b["id"])
                            ),
                            value=AppState.edit_tx_bucket,
                            on_change=AppState.set_edit_tx_bucket,
                            style=_select_style(),
                        )
                    ),
                    rx.box(),
                ),

                # Income type — income only
                rx.cond(
                    AppState.edit_tx_type == "in",
                    _field("Income Type",
                        rx.el.select(
                            rx.el.option("Paycheck", value="paycheck"),
                            rx.el.option("Other Income", value="other"),
                            value=AppState.edit_tx_income_type,
                            on_change=AppState.set_edit_tx_income_type,
                            style=_select_style(),
                        )
                    ),
                    rx.box(),
                ),

                # Reconciled toggle
                rx.hstack(
                    rx.text("Reconciled", style={
                        "font_size": "13px", "color": TEXT2, "font_family": MONO,
                    }),
                    rx.spacer(),
                    rx.box(
                        rx.cond(
                            AppState.edit_tx_reconciled,
                            rx.text("✓  Yes", style={
                                "font_size": "13px", "color": GREEN, "font_family": MONO,
                                "padding": "6px 14px", "border_radius": "6px",
                                "background": f"{GREEN}18", "border": f"1px solid {GREEN}44",
                                "cursor": "pointer",
                            }),
                            rx.text("○  No", style={
                                "font_size": "13px", "color": TEXT3, "font_family": MONO,
                                "padding": "6px 14px", "border_radius": "6px",
                                "background": BG3, "border": f"1px solid {BORDER}",
                                "cursor": "pointer",
                            }),
                        ),
                        on_click=AppState.set_edit_tx_reconciled(~AppState.edit_tx_reconciled),
                        role="button",
                        tab_index=0,
                        aria_label="Toggle reconciled status",
                        aria_pressed=rx.cond(AppState.edit_tx_reconciled, "true", "false"),
                        style={"_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px",
                                                   "border_radius": "6px"}},
                    ),
                    width="100%", align_items="center",
                ),

                # Error
                rx.cond(
                    AppState.edit_tx_error != "",
                    rx.text(AppState.edit_tx_error, style={
                        "color": RED, "font_size": "12px", "font_family": MONO,
                    }),
                    rx.box(),
                ),

                rx.divider(style={"border_color": BORDER}),

                # Footer: Delete | Save
                rx.hstack(
                    rx.box(
                        "Delete",
                        on_click=AppState.delete_from_edit_tx,
                        style={
                            "flex": "1", "padding": "10px", "border_radius": "8px",
                            "border": f"1px solid {RED}44", "color": RED,
                            "font_size": "12px", "text_align": "center",
                            "cursor": "pointer", "font_family": MONO,
                            "letter_spacing": "0.06em",
                            "_hover": {"background": f"{RED}11"},
                        },
                    ),
                    rx.box(
                        rx.cond(AppState.edit_tx_saving, "Saving…", "Save"),
                        on_click=AppState.save_edit_tx,
                        style={
                            "flex": "2", "padding": "10px", "border_radius": "8px",
                            "background": rx.cond(AppState.edit_tx_saving, BORDER, ACCENT),
                            "color": "#fff", "font_size": "12px",
                            "text_align": "center", "cursor": "pointer",
                            "font_family": MONO, "letter_spacing": "0.08em",
                            "text_transform": "uppercase", "font_weight": "700",
                            "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", width="100%",
                ),

                gap="14px", width="100%",
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "14px", "padding": "24px",
                "max_width": "460px", "width": "95vw",
            },
        ),
        open=AppState.edit_tx_open,
        on_open_change=AppState.set_edit_tx_open,
    )


# ── Add-transaction sheet ─────────────────────────────────────────────────────

def _add_type_btn(label: str, value: str, color: str) -> rx.Component:
    is_active = AppState.sheet_type == value
    return rx.box(
        label,
        on_click=AppState.set_sheet_type(value),
        style=rx.cond(
            is_active,
            {
                "flex": "1", "padding": "9px", "border_radius": "8px",
                "cursor": "pointer", "text_align": "center",
                "font_size": "12px", "letter_spacing": "0.06em", "font_family": MONO,
                "border": f"1px solid {color}", "color": color,
                "background": color + "1a",
            },
            {
                "flex": "1", "padding": "9px", "border_radius": "8px",
                "cursor": "pointer", "text_align": "center",
                "font_size": "12px", "letter_spacing": "0.06em", "font_family": MONO,
                "border": f"1px solid {BORDER}", "color": TEXT3, "background": BG3,
                "_hover": {"color": TEXT2, "border_color": BORDER2},
            },
        ),
    )


def add_tx_sheet() -> rx.Component:
    return rx.cond(
        AppState.sheet_open,
        rx.box(
            # Invisible close layer
            rx.box(
                on_click=AppState.close_sheet,
                style={"position": "absolute", "inset": "0", "cursor": "pointer"},
            ),

            # Sheet card
            rx.box(
                rx.vstack(
                    # Drag handle
                    rx.box(style={
                        "width": "36px", "height": "4px", "border_radius": "2px",
                        "background": BORDER2, "margin": "0 auto 12px",
                    }),

                    # Header
                    rx.hstack(
                        rx.text("ADD TRANSACTION", style={
                            "font_size": "12px", "letter_spacing": "0.14em",
                            "color": TEXT2, "flex": "1", "font_family": MONO,
                        }),
                        rx.box("×", on_click=AppState.close_sheet, style={
                            "font_size": "20px", "color": TEXT3, "cursor": "pointer",
                            "_hover": {"color": TEXT},
                        }),
                        align_items="center", width="100%",
                    ),

                    # Type buttons
                    rx.hstack(
                        _add_type_btn("Expense",  "out", RED),
                        _add_type_btn("Income",   "in",  GREEN),
                        _add_type_btn("Transfer", "xfr", TEXT2),
                        gap="6px",
                    ),

                    # Amount
                    rx.input(
                        placeholder="0.00",
                        value=AppState.sheet_amount,
                        on_change=AppState.set_sheet_amount,
                        type="text", input_mode="decimal",
                        style={
                            **_input_style(),
                            "text_align": "center",
                            "border_color": rx.cond(
                                AppState.sheet_type == "in", GREEN,
                                rx.cond(AppState.sheet_type == "out", f"{RED}88", BORDER),
                            ),
                        },
                    ),

                    # Description with payee autocomplete
                    rx.box(
                        rx.input(
                            placeholder="Description",
                            value=AppState.sheet_desc,
                            on_change=AppState.set_sheet_desc,
                            list="payee-list",
                            style=_input_style(),
                        ),
                        rx.el.datalist(
                            rx.foreach(
                                AppState.payee_options,
                                lambda p: rx.el.option(value=p),
                            ),
                            id="payee-list",
                        ),
                        style={"position": "relative", "width": "100%"},
                    ),

                    # Date + Account
                    rx.hstack(
                        _field("Date",
                            rx.input(
                                type="date",
                                value=AppState.sheet_date,
                                on_change=AppState.set_sheet_date,
                                style=_input_style(),
                            ),
                        ),
                        _field("Account",
                            rx.el.select(
                                AppState.account_options.to(list[dict[str, Any]]).foreach(
                                    lambda a: rx.el.option(a["name"], value=a["id"])
                                ),
                                value=AppState.sheet_account,
                                on_change=AppState.set_sheet_account,
                                style=_select_style(),
                            ),
                        ),
                        gap="10px",
                    ),

                    # To Account — transfer only
                    rx.cond(
                        AppState.sheet_type == "xfr",
                        _field("To Account",
                            rx.el.select(
                                AppState.account_options.to(list[dict[str, Any]]).foreach(
                                    lambda a: rx.el.option(a["name"], value=a["id"])
                                ),
                                value=AppState.sheet_to_account,
                                on_change=AppState.set_sheet_to_account,
                                style=_select_style(),
                            ),
                        ),
                        rx.box(),
                    ),

                    # Bucket — expense only
                    rx.cond(
                        AppState.sheet_type == "out",
                        _field("Bucket",
                            rx.el.select(
                                rx.el.option("— No bucket —", value=""),
                                AppState.expense_buckets.to(list[dict[str, Any]]).foreach(
                                    lambda b: rx.el.option(b["name"], value=b["id"])
                                ),
                                value=AppState.sheet_bucket,
                                on_change=AppState.set_sheet_bucket,
                                style=_select_style(),
                            ),
                        ),
                        rx.box(),
                    ),

                    # Income type — income only
                    rx.cond(
                        AppState.sheet_type == "in",
                        _field("Income Type",
                            rx.el.select(
                                rx.el.option("Paycheck", value="paycheck"),
                                rx.el.option("Other Income", value="other"),
                                value=AppState.sheet_income_type,
                                on_change=AppState.set_sheet_income_type,
                                style=_select_style(),
                            ),
                        ),
                        rx.box(),
                    ),

                    # Error
                    rx.cond(
                        AppState.sheet_error != "",
                        rx.text(AppState.sheet_error, style={
                            "color": RED, "font_size": "12px", "font_family": MONO,
                        }),
                        rx.box(),
                    ),

                    # Submit
                    rx.box(
                        rx.cond(AppState.sheet_saving, "Saving…", "Add Transaction"),
                        on_click=AppState.submit_transaction,
                        style={
                            "width": "100%", "padding": "13px",
                            "background": rx.cond(
                                AppState.sheet_saving, BORDER,
                                rx.cond(AppState.sheet_type == "in", GREEN,
                                rx.cond(AppState.sheet_type == "out", RED, ACCENT)),
                            ),
                            "color": "#fff", "border": "none",
                            "border_radius": "8px", "font_size": "13px",
                            "letter_spacing": "0.1em", "text_transform": "uppercase",
                            "cursor": "pointer", "text_align": "center",
                            "font_family": MONO, "font_weight": "700",
                            "_hover": {"opacity": "0.9"},
                            "_active": {"transform": "scale(0.99)"},
                        },
                    ),

                    gap="12px", width="100%",
                ),
                style={
                    "position": "relative", "z_index": "1",
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "14px 14px 0 0",
                    "padding": "20px 20px 36px",
                    "width": "100%", "max_width": "500px",
                },
            ),

            style={
                "position": "fixed", "inset": "0",
                "background": "rgba(0,0,0,0.6)",
                "backdrop_filter": "blur(4px)",
                "z_index": "200",
                "display": "flex",
                "align_items": "flex-end",
                "justify_content": "center",
            },
        ),
        rx.box(),
    )


# ── Ledger panel (2-column: left=transactions, right=scoreboard) ─────────────

def ledger_panel() -> rx.Component:
    return rx.box(
        rx.box(
            # ── Left column: search + transaction list ────────────────────
            rx.vstack(
                # Search bar
                rx.hstack(
                    rx.html(
                        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
                        'stroke="currentColor" stroke-width="2" style="color:#4e4e6a;flex-shrink:0">'
                        '<circle cx="11" cy="11" r="8"/>'
                        '<line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
                    ),
                    rx.input(
                        placeholder="Search transactions…",
                        value=AppState.ledger_query,
                        on_change=AppState.set_ledger_query,
                        style={
                            "background": "transparent", "border": "none", "outline": "none",
                            "color": TEXT, "font_family": MONO, "font_size": "13px",
                            "flex": "1", "width": "100%",
                        },
                    ),
                    rx.cond(
                        AppState.ledger_query != "",
                        rx.box("×", on_click=AppState.set_ledger_query(""),
                               style={"color": TEXT3, "cursor": "pointer", "font_size": "18px",
                                      "_hover": {"color": TEXT}}),
                        rx.box(),
                    ),
                    style={
                        "background": BG2, "border": f"1px solid {BORDER}",
                        "border_radius": "8px", "padding": "9px 14px",
                        "margin_bottom": "16px", "align_items": "center", "gap": "8px",
                    },
                ),

                # Transaction list
                rx.foreach(AppState.filtered_ledger.to(list[dict[str, Any]]), _tx_row),

                # Empty state
                rx.cond(
                    AppState.filtered_ledger.length() == 0,
                    rx.box(
                        rx.text("No transactions this month",
                                style={"color": TEXT3, "font_size": "13px", "font_family": MONO}),
                        style={"text_align": "center", "padding": "48px 0"},
                    ),
                    rx.box(),
                ),

                gap="0", align_items="stretch", width="100%",
            ),

            # ── Right column: scoreboard ──────────────────────────────────
            rx.box(
                _ledger_scoreboard(),
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

        edit_tx_dialog(),
        add_tx_sheet(),
    )
