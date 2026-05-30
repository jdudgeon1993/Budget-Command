"""Ledger panel — transaction list with search and add sheet."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS)


# ── Transaction row ───────────────────────────────────────────────────────────

def _tx_row(row: dict) -> rx.Component:
    return rx.cond(
        row["row_type"] == "date_header",

        # ── Date section header ──────────────────────────────────────────────
        rx.hstack(
            rx.text(row["label"], style={
                "font_size": "9px", "letter_spacing": "0.12em",
                "text_transform": "uppercase", "color": TEXT3,
                "font_family": MONO, "white_space": "nowrap", "flex_shrink": "0",
            }),
            rx.box(style={
                "flex": "1", "height": "1px",
                "background": BORDER, "margin_left": "8px",
            }),
            align_items="center",
            style={"padding": "14px 0 6px", "width": "100%"},
        ),

        # ── Transaction row ──────────────────────────────────────────────────
        rx.hstack(
            # Left: description + meta
            rx.vstack(
                rx.text(row["desc"], style={
                    "font_size": "13px", "color": TEXT,
                    "font_weight": "500", "line_height": "1.2",
                    "white_space": "nowrap", "overflow": "hidden",
                    "text_overflow": "ellipsis",
                }),
                rx.hstack(
                    # Bucket or account
                    rx.text(
                        rx.cond(row["bucket"] != "", row["bucket"], row["account"]),
                        style={
                            "font_size": "10px", "color": TEXT3,
                            "font_family": MONO,
                        },
                    ),
                    # Type chip — shown only for non-expense
                    rx.cond(
                        row["type_chip"] != "",
                        rx.text(row["type_chip"], style={
                            "font_size": "8px", "font_family": MONO,
                            "letter_spacing": "0.08em",
                            "padding": "1px 5px", "border_radius": "6px",
                            "color": row["chip_color"],
                            "background": row["chip_color"] + "18",
                            "border": "1px solid " + row["chip_color"] + "33",
                            "white_space": "nowrap", "flex_shrink": "0",
                        }),
                        rx.box(),
                    ),
                    align_items="center", gap="6px",
                ),
                gap="3px", align_items="flex-start", flex="1", min_width="0",
            ),

            # Right: amount + delete
            rx.hstack(
                rx.text(row["amount_fmt"], style={
                    "font_size": "14px", "font_family": MONO, "font_weight": "700",
                    "color": row["amt_color"], "white_space": "nowrap",
                }),
                rx.box(
                    "×",
                    on_click=AppState.delete_tx(row["id"]),
                    style={
                        "width": "22px", "height": "22px", "border_radius": "4px",
                        "display": "flex", "align_items": "center",
                        "justify_content": "center",
                        "color": TEXT3, "cursor": "pointer",
                        "font_size": "16px", "flex_shrink": "0",
                        "opacity": "0",
                        "_hover": {"color": RED, "background": f"{RED}18", "opacity": "1"},
                    },
                ),
                align_items="center", gap="4px", flex_shrink="0",
            ),

            align_items="center", width="100%", gap="10px",
            style={
                "background": BG2,
                "border": f"1px solid {BORDER}",
                "border_left": row["left_border"],
                "border_radius": "8px",
                "padding": rx.cond(
                    row["left_border"] != "none",
                    "9px 12px 9px 10px",
                    "9px 12px",
                ),
                "margin_bottom": "4px",
                "_hover": {
                    "border_color": BORDER2,
                    "border_left": row["left_border"],
                },
            },
        ),
    )


# ── Add-transaction sheet ─────────────────────────────────────────────────────

def _type_btn(label: str, value: str, color: str) -> rx.Component:
    is_active = AppState.sheet_type == value
    return rx.box(
        label,
        on_click=AppState.set_sheet_type(value),
        style=rx.cond(
            is_active,
            {
                "flex": "1", "padding": "8px", "border_radius": "8px",
                "cursor": "pointer", "text_align": "center",
                "font_size": "11px", "letter_spacing": "0.06em",
                "font_family": MONO,
                "border": f"1px solid {color}",
                "color": color,
                "background": color + "1a",
            },
            {
                "flex": "1", "padding": "8px", "border_radius": "8px",
                "cursor": "pointer", "text_align": "center",
                "font_size": "11px", "letter_spacing": "0.06em",
                "font_family": MONO,
                "border": f"1px solid {BORDER}", "color": TEXT3, "background": BG3,
                "_hover": {"color": TEXT2, "border_color": BORDER2},
            },
        ),
    )


def _field(label: str, child: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={
            "font_size": "9px", "color": TEXT3,
            "letter_spacing": "0.1em", "text_transform": "uppercase",
            "font_family": MONO,
        }),
        child,
        gap="4px", align_items="stretch",
    )


def _input_style() -> dict:
    return {
        "width": "100%", "background": BG3, "border": f"1px solid {BORDER}",
        "border_radius": "8px", "color": TEXT, "font_family": MONO,
        "font_size": "13px", "padding": "10px 14px", "outline": "none",
        "_focus": {"border_color": ACCENT},
    }


def add_tx_sheet() -> rx.Component:
    return rx.cond(
        AppState.sheet_open,
        rx.box(
            rx.box(
                rx.vstack(
                    # Drag handle
                    rx.box(style={
                        "width": "36px", "height": "4px", "border_radius": "2px",
                        "background": BORDER2, "margin": "0 auto 12px",
                    }),

                    # Title row
                    rx.hstack(
                        rx.text("Add Transaction", style={
                            "font_size": "11px", "letter_spacing": "0.14em",
                            "text_transform": "uppercase", "color": TEXT2,
                            "flex": "1", "font_family": MONO,
                        }),
                        rx.box("×", on_click=AppState.close_sheet, style={
                            "font_size": "20px", "color": TEXT3, "cursor": "pointer",
                            "_hover": {"color": TEXT},
                        }),
                        align_items="center", width="100%",
                    ),

                    # Type selector — each button gets its semantic color
                    rx.hstack(
                        _type_btn("Expense",  "out", RED),
                        _type_btn("Income",   "in",  GREEN),
                        _type_btn("Transfer", "xfr", TEXT2),
                        gap="6px",
                    ),

                    # Amount — large, type-colored border when active
                    rx.input(
                        placeholder="$0.00",
                        value=AppState.sheet_amount,
                        on_change=AppState.set_sheet_amount,
                        type="text", input_mode="decimal",
                        style={
                            **_input_style(),
                            "font_size": "28px", "text_align": "center",
                            "letter_spacing": "0.02em", "padding": "12px 14px",
                            "border_color": rx.cond(
                                AppState.sheet_type == "in", GREEN,
                                rx.cond(AppState.sheet_type == "out", f"{RED}88", BORDER),
                            ),
                        },
                    ),

                    # Description
                    rx.input(
                        placeholder="Description",
                        value=AppState.sheet_desc,
                        on_change=AppState.set_sheet_desc,
                        style=_input_style(),
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
                                style=_input_style(),
                            ),
                        ),
                        gap="8px",
                    ),

                    # Bucket (expense only)
                    rx.cond(
                        AppState.sheet_type == "out",
                        _field("Bucket",
                            rx.el.select(
                                AppState.expense_buckets.to(list[dict[str, Any]]).foreach(
                                    lambda b: rx.el.option(b["name"], value=b["id"])
                                ),
                                value=AppState.sheet_bucket,
                                on_change=AppState.set_sheet_bucket,
                                style=_input_style(),
                            ),
                        ),
                        rx.box(),
                    ),

                    # Error
                    rx.cond(
                        AppState.sheet_error != "",
                        rx.text(AppState.sheet_error, style={
                            "color": RED, "font_size": "11px", "font_family": MONO,
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
                            "color": "#fff", "border": "none", "border_radius": "8px",
                            "font_size": "12px", "letter_spacing": "0.1em",
                            "text_transform": "uppercase", "cursor": "pointer",
                            "text_align": "center", "font_family": MONO, "font_weight": "700",
                            "_hover": {"opacity": "0.9"},
                            "_active": {"transform": "scale(0.99)"},
                        },
                    ),

                    gap="12px", width="100%",
                ),
                style={
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "14px 14px 0 0", "padding": "20px 20px 36px",
                    "width": "100%", "max_width": "500px",
                },
            ),
            on_click=AppState.close_sheet,
            class_name="sheet-backdrop",
        ),
        rx.box(),
    )


# ── Ledger panel ──────────────────────────────────────────────────────────────

def ledger_panel() -> rx.Component:
    return rx.box(
        # Search bar
        rx.hstack(
            rx.html(
                '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
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
                    "color": TEXT, "font_family": MONO, "font_size": "12px",
                    "flex": "1", "width": "100%",
                },
            ),
            rx.cond(
                AppState.ledger_query != "",
                rx.box("×", on_click=AppState.set_ledger_query(""),
                       style={"color": TEXT3, "cursor": "pointer", "font_size": "16px",
                              "_hover": {"color": TEXT}}),
                rx.box(),
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "padding": "8px 12px",
                "margin_bottom": "14px", "align_items": "center", "gap": "8px",
            },
        ),

        # Transaction list
        rx.foreach(AppState.filtered_ledger.to(list[dict[str, Any]]), _tx_row),

        # Empty state
        rx.cond(
            AppState.filtered_ledger.length() == 0,
            rx.box(
                rx.text("No transactions this month",
                        style={"color": TEXT3, "font_size": "12px", "font_family": MONO}),
                style={"text_align": "center", "padding": "48px 0"},
            ),
            rx.box(),
        ),

        add_tx_sheet(),
    )
