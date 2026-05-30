"""Ledger panel — transaction list with search and add sheet."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3, GREEN, AMBER, ACCENT, RED, MONO, SANS


# ── Transaction row ───────────────────────────────────────────────────────────

def _tx_row(row: dict) -> rx.Component:
    return rx.cond(
        row["row_type"] == "date_header",

        # Date header
        rx.text(
            row["label"],
            style={"font_size": "9px", "letter_spacing": "0.1em", "text_transform": "uppercase",
                   "color": TEXT3, "padding": "10px 2px 5px", "font_family": MONO},
        ),

        # Transaction row
        rx.hstack(
            # Color dot
            rx.box(
                style={"width": "8px", "height": "8px", "border_radius": "50%",
                       "background": row["dot_color"], "flex_shrink": "0"},
            ),
            # Description + badge
            rx.vstack(
                rx.text(row["desc"],
                        style={"font_size": "13px", "color": TEXT, "font_weight": "500",
                               "white_space": "nowrap", "overflow": "hidden",
                               "text_overflow": "ellipsis"}),
                rx.text(
                    rx.cond(row["bucket"] != "", row["bucket"], row["account"]),
                    style={"font_size": "10px", "color": TEXT3, "letter_spacing": "0.03em"},
                ),
                gap="1px", align_items="flex-start", flex="1", min_width="0",
            ),
            rx.spacer(),
            # Amount
            rx.text(
                row["amount_fmt"],
                style={"font_size": "13px", "font_family": MONO,
                       "color": row["amt_color"], "white_space": "nowrap", "flex_shrink": "0"},
            ),
            # Delete button
            rx.box(
                "×",
                on_click=AppState.delete_tx(row["id"]),
                style={
                    "width": "22px", "height": "22px", "border_radius": "4px",
                    "display": "flex", "align_items": "center", "justify_content": "center",
                    "color": TEXT3, "cursor": "pointer", "font_size": "16px", "flex_shrink": "0",
                    "_hover": {"color": RED, "background": f"{RED}18"},
                },
            ),
            align_items="center", width="100%",
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "padding": "9px 12px",
                "margin_bottom": "5px",
                "_hover": {"border_color": BORDER2},
            },
        ),
    )


# ── Add-transaction sheet ─────────────────────────────────────────────────────

def _type_btn(label: str, value: str) -> rx.Component:
    is_active = AppState.sheet_type == value
    return rx.box(
        label,
        on_click=AppState.set_sheet_type(value),
        style=rx.cond(
            is_active,
            {
                "flex": "1", "padding": "8px", "border_radius": "8px", "cursor": "pointer",
                "border": f"1px solid {ACCENT}", "color": ACCENT,
                "background": f"{ACCENT}1a", "text_align": "center",
                "font_size": "11px", "letter_spacing": "0.06em",
            },
            {
                "flex": "1", "padding": "8px", "border_radius": "8px", "cursor": "pointer",
                "border": f"1px solid {BORDER}", "color": TEXT3, "background": BG3,
                "text_align": "center", "font_size": "11px", "letter_spacing": "0.06em",
                "_hover": {"color": TEXT2},
            },
        ),
    )


def _field(label: str, child: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={"font_size": "10px", "color": TEXT3, "letter_spacing": "0.07em",
                               "text_transform": "uppercase"}),
        child,
        gap="4px", align_items="stretch",
    )


def _input_style() -> dict:
    return {
        "width": "100%", "background": BG3, "border": f"1px solid {BORDER}",
        "border_radius": "8px", "color": TEXT, "font_family": MONO,
        "font_size": "13px", "padding": "10px 14px", "outline": "none",
    }


def add_tx_sheet() -> rx.Component:
    """Bottom-sheet / modal for adding a transaction."""
    return rx.cond(
        AppState.sheet_open,
        rx.box(
            rx.box(
                # Sheet card
                rx.vstack(
                    # Drag handle (mobile)
                    rx.box(
                        style={"width": "36px", "height": "4px", "border_radius": "2px",
                               "background": BORDER, "margin": "0 auto 16px"},
                    ),
                    # Title
                    rx.hstack(
                        rx.text("Add Transaction",
                                style={"font_size": "11px", "letter_spacing": "0.14em",
                                       "text_transform": "uppercase", "color": TEXT2, "flex": "1"}),
                        rx.box("×", on_click=AppState.close_sheet,
                               style={"font_size": "20px", "color": TEXT3, "cursor": "pointer",
                                      "_hover": {"color": TEXT}}),
                    ),

                    # Type selector
                    rx.hstack(
                        _type_btn("Expense", "out"),
                        _type_btn("Income", "in"),
                        _type_btn("Transfer", "xfr"),
                        gap="6px",
                    ),

                    # Amount (big)
                    rx.input(
                        placeholder="$0.00",
                        value=AppState.sheet_amount,
                        on_change=AppState.set_sheet_amount,
                        type="text", input_mode="decimal",
                        style={**_input_style(), "font_size": "24px", "text_align": "center",
                               "letter_spacing": "0.02em"},
                    ),

                    # Description
                    rx.input(
                        placeholder="Description",
                        value=AppState.sheet_desc,
                        on_change=AppState.set_sheet_desc,
                        style=_input_style(),
                    ),

                    # Date + Account row
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
                        rx.text(AppState.sheet_error,
                                style={"color": RED, "font_size": "11px", "font_family": MONO}),
                        rx.box(),
                    ),

                    # Submit
                    rx.box(
                        rx.cond(AppState.sheet_saving, "Saving…", "Add Transaction"),
                        on_click=AppState.submit_transaction,
                        style={
                            "width": "100%", "padding": "12px",
                            "background": rx.cond(AppState.sheet_saving, BORDER, ACCENT),
                            "color": "#fff", "border": "none", "border_radius": "8px",
                            "font_size": "12px", "letter_spacing": "0.1em",
                            "text_transform": "uppercase", "cursor": "pointer",
                            "text_align": "center",
                            "box_shadow": f"0 4px 12px {ACCENT}4d",
                            "_hover": {"opacity": "0.9"},
                        },
                    ),

                    gap="12px",
                    style={"width": "100%"},
                ),
                style={
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "14px 14px 0 0", "padding": "20px 20px 32px",
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
            rx.html('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
                    'stroke="currentColor" stroke-width="2" style="color:#4e4e6a;flex-shrink:0">'
                    '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'
                    '</svg>'),
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
                "margin_bottom": "12px", "align_items": "center", "gap": "8px",
            },
        ),

        # Transaction list
        rx.foreach(AppState.filtered_ledger.to(list[dict[str, Any]]), _tx_row),

        # Empty state
        rx.cond(
            AppState.filtered_ledger.length() == 0,
            rx.box(
                rx.text("No transactions yet", style={"color": TEXT3, "font_size": "12px"}),
                style={"text_align": "center", "padding": "40px 0"},
            ),
            rx.box(),
        ),

        add_tx_sheet(),
    )
