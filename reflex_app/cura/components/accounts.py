"""Accounts panel — bank-statement ledger with account filter + balance cards."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS)


# ── Shared form helpers ───────────────────────────────────────────────────────

def _input_style() -> dict:
    return {
        "background": BG3, "border": f"1px solid {BORDER}",
        "border_radius": "8px", "color": TEXT, "font_family": MONO,
        "font_size": "13px", "padding": "8px 12px", "outline": "none", "width": "100%",
        "_focus": {"border_color": ACCENT, "outline": "none"},
        "_placeholder": {"color": TEXT3},
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


def _inp(placeholder: str, value, on_change, type_: str = "text", **extra) -> rx.Component:
    return rx.input(
        placeholder=placeholder, value=value, on_change=on_change, type=type_,
        style={**_input_style(), **extra},
    )


def _err(msg) -> rx.Component:
    return rx.cond(
        msg != "",
        rx.text(msg, style={"color": RED, "font_size": "11px", "font_family": MONO}),
        rx.box(),
    )


def _sel(*opts, value, on_change, **extra) -> rx.Component:
    return rx.el.select(
        *opts, value=value, on_change=on_change,
        style={**_select_style(), **extra},
    )


# ── KPI summary boxes ─────────────────────────────────────────────────────────

def _kpi_box(label: str, value, color: str) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={
            "font_size": "11px", "letter_spacing": "0.1em",
            "text_transform": "uppercase", "color": TEXT3, "font_family": MONO,
        }),
        rx.text(value, style={
            "font_size": "16px", "font_weight": "700", "font_family": MONO,
            "color": color, "white_space": "nowrap",
        }),
        gap="3px", align_items="flex-start",
        style={
            "flex": "1", "min_width": "120px",
            "background": BG2, "border": f"1px solid {color}44",
            "border_radius": "10px", "padding": "10px 14px",
        },
    )


def _kpi_row() -> rx.Component:
    return rx.hstack(
        _kpi_box("Income",      AppState.ledger_view["income_fmt"],      GREEN),
        _kpi_box("Scheduled",   AppState.ledger_view["scheduled_fmt"],   AMBER),
        _kpi_box("Spent",       AppState.ledger_view["spent_fmt"],       RED),
        _kpi_box("Transferred", AppState.ledger_view["transferred_fmt"], TEXT2),
        gap="10px", width="100%", flex_wrap="wrap",
        style={"margin_bottom": "12px"},
    )


# ── Transaction line (Excel-style table row) ──────────────────────────────────

def _tx_line(row: dict) -> rx.Component:
    return rx.hstack(
        # Description + sub-label + chips
        rx.vstack(
            rx.text(
                rx.cond(row["desc"] != "", row["desc"], "—"),
                style={
                    "font_size": "13px", "font_weight": "600", "line_height": "1.2",
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
                    style={"font_size": "11px", "color": TEXT3, "font_family": MONO},
                ),
                rx.cond(
                    row["type_chip"] != "",
                    rx.text(row["type_chip"], style={
                        "font_size": "10px", "font_family": MONO,
                        "letter_spacing": "0.06em",
                        "padding": "1px 6px", "border_radius": "5px",
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
            gap="3px", align_items="flex-start", flex="1", min_width="0",
        ),

        # Amount (right-aligned column)
        rx.text(row["amount_fmt"], style={
            "font_size": "13px", "font_family": MONO, "font_weight": "700",
            "color": row["amt_color"], "white_space": "nowrap",
            "text_align": "right", "flex_shrink": "0",
        }),

        # Edit affordance
        rx.box(
            "⋯",
            on_click=AppState.open_edit_tx(row["id"]),
            role="button", tab_index=0, aria_label="Edit transaction",
            style={
                "font_size": "18px", "color": TEXT3, "cursor": "pointer",
                "padding": "4px 8px", "border_radius": "6px",
                "line_height": "1.2", "min_height": "32px", "flex_shrink": "0",
                "display": "flex", "align_items": "center",
                "_hover": {"color": TEXT, "background": BG3},
                "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
            },
        ),

        align_items="center", width="100%", gap="12px",
        style={
            "padding": "9px 12px 9px 11px",
            "border_left": row["left_border"],
            "border_bottom": f"1px solid {BORDER}",
            "_hover": {"background": BG3},
        },
    )


# ── Section header (Scheduled / Current Statement) ────────────────────────────

def _section_header(block: dict) -> rx.Component:
    return rx.hstack(
        rx.text(block["label"], style={
            "font_size": "15px", "font_weight": "700", "color": TEXT,
            "letter_spacing": "0.02em",
        }),
        rx.text(block["meta"], style={
            "font_size": "11px", "color": TEXT3, "font_family": MONO,
        }),
        rx.spacer(),
        rx.cond(
            block["balance_label"] != "",
            rx.text(block["balance_label"], style={
                "font_size": "14px", "font_family": MONO, "font_weight": "700",
                "color": block["balance_color"], "white_space": "nowrap",
            }),
            rx.box(),
        ),
        align_items="center", width="100%", gap="10px",
        style={"padding": "8px 4px 8px", "margin_top": "10px"},
    )


# ── Day card (date header + its transaction rows) ─────────────────────────────

def _day_card(block: dict) -> rx.Component:
    return rx.box(
        # Date header row
        rx.hstack(
            rx.text(block["date_label"], style={
                "font_size": "12px", "font_weight": "700", "color": TEXT2,
                "letter_spacing": "0.04em", "white_space": "nowrap",
                "text_transform": "uppercase", "font_family": MONO,
            }),
            rx.text(block["meta"], style={
                "font_size": "11px", "color": TEXT3, "font_family": MONO,
            }),
            rx.spacer(),
            rx.cond(
                block["rb_label"] != "",
                rx.text(block["rb_label"], style={
                    "font_size": "13px", "font_family": MONO, "font_weight": "700",
                    "color": block["rb_color"], "white_space": "nowrap",
                }),
                rx.box(),
            ),
            align_items="center", width="100%", gap="10px",
            style={
                "padding": "8px 12px",
                "background": BG3,
                "border_bottom": f"1px solid {BORDER}",
            },
        ),
        # Transaction rows
        rx.foreach(block["txs"].to(list[dict[str, Any]]), _tx_line),
        style={
            "background": BG2, "border": f"1px solid {BORDER}",
            "border_radius": "10px", "overflow": "hidden",
            "margin_bottom": "10px", "width": "100%",
        },
    )


# ── Block dispatcher ──────────────────────────────────────────────────────────

def _ledger_block(block: dict) -> rx.Component:
    return rx.match(
        block["kind"],
        ("section", _section_header(block)),
        ("day",     _day_card(block)),
        rx.box(),
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
                        role="button", tab_index=0, aria_label="Toggle reconciled status",
                        aria_pressed=rx.cond(AppState.edit_tx_reconciled, "true", "false"),
                        style={"_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px",
                                                   "border_radius": "6px"}},
                    ),
                    width="100%", align_items="center",
                ),

                # Reconciled warning
                rx.cond(
                    AppState.edit_tx_reconciled,
                    rx.hstack(
                        rx.html(
                            '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
                            f'stroke="{AMBER}" stroke-width="2" aria-hidden="true">'
                            '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 '
                            '1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
                            '<line x1="12" y1="9" x2="12" y2="13"/>'
                            '<line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
                        ),
                        rx.text(
                            "This transaction is reconciled. Saving will remove the cleared status.",
                            style={"font_size": "12px", "color": AMBER, "font_family": MONO,
                                   "flex": "1"},
                        ),
                        style={
                            "background": f"{AMBER}10", "border": f"1px solid {AMBER}33",
                            "border_radius": "8px", "padding": "8px 10px",
                            "align_items": "flex-start", "gap": "8px", "width": "100%",
                        },
                    ),
                    rx.box(),
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
                class_name="sheet-card",
                style={
                    "position": "relative", "z_index": "1",
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "14px 14px 0 0",
                    "padding": "20px 20px 36px",
                    "width": "100%", "max_width": "500px",
                },
            ),

            class_name="sheet-backdrop-fx",
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


# ── Account balance card (right column) ──────────────────────────────────────

def _acct_balance_card(row: dict) -> rx.Component:
    is_debt = row["type"] == "debt"
    is_active = AppState.ledger_acct_filter == row["id"]
    return rx.hstack(
        rx.box(style={
            "width": "9px", "height": "9px", "border_radius": "50%",
            "background": row["color"], "flex_shrink": "0", "margin_top": "2px",
        }),
        rx.vstack(
            rx.text(row["name"], style={
                "font_size": "13px", "font_weight": "600",
                "color": rx.cond(is_active, ACCENT, TEXT),
            }),
            rx.text(row["type_upper"], style={
                "font_size": "10px", "color": TEXT3, "letter_spacing": "0.1em",
                "font_family": MONO,
            }),
            gap="1px", align_items="flex-start", flex="1",
        ),
        rx.text(row["balance_fmt"], style={
            "font_family": MONO, "font_size": "14px", "font_weight": "700",
            "color": row["bal_color"], "white_space": "nowrap",
        }),
        # Settings gear
        rx.box(
            rx.html(
                '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="1.75" aria-hidden="true">'
                '<circle cx="12" cy="12" r="3"/>'
                '<path d="M19.1 12a7.1 7.1 0 0 0-.1-1l2.2-1.7-2.1-3.6-2.6 1'
                'a7 7 0 0 0-1.7-1l-.4-2.7h-4.2l-.4 2.7a7 7 0 0 0-1.7 1l-2.6-1'
                '-2.1 3.6 2.2 1.7a7.1 7.1 0 0 0 0 2l-2.2 1.7 2.1 3.6 2.6-1'
                'a7 7 0 0 0 1.7 1l.4 2.7h4.2l.4-2.7a7 7 0 0 0 1.7-1l2.6 1'
                ' 2.1-3.6-2.2-1.7a7.1 7.1 0 0 0 .1-1z"/></svg>'
            ),
            on_click=AppState.open_account_settings(row["id"]),
            style={
                "color": TEXT3, "cursor": "pointer", "padding": "4px 5px",
                "border_radius": "4px",
                "_hover": {"color": ACCENT, "background": f"{ACCENT}11"},
            },
        ),
        # Debt pay button
        rx.cond(
            is_debt,
            rx.box(
                "Pay",
                on_click=AppState.open_debt_payment(row["id"]),
                style={
                    "font_size": "10px", "color": AMBER, "cursor": "pointer",
                    "padding": "3px 7px", "border_radius": "4px",
                    "border": f"1px solid {AMBER}44",
                    "_hover": {"background": f"{AMBER}11"},
                    "font_family": MONO, "white_space": "nowrap",
                },
            ),
            rx.box(),
        ),
        align_items="center", width="100%", gap="8px",
        on_click=AppState.set_ledger_acct_filter(
            rx.cond(is_active, "", row["id"])
        ),
        role="button", tab_index=0,
        style={
            "padding": "9px 12px",
            "border_radius": "8px",
            "cursor": "pointer",
            "background": rx.cond(is_active, f"{ACCENT}10", "transparent"),
            "border": rx.cond(is_active, f"1px solid {ACCENT}33", f"1px solid transparent"),
            "_hover": {"background": rx.cond(is_active, f"{ACCENT}15", BG3)},
            "margin_bottom": "2px",
        },
    )


# ── Add account dialog ────────────────────────────────────────────────────────

def _add_account_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Add Account", style={
                        "font_size": "11px", "letter_spacing": "0.14em",
                        "text_transform": "uppercase", "color": TEXT2,
                        "flex": "1", "font_family": MONO,
                    }),
                    rx.dialog.close(
                        rx.box("×", style={
                            "font_size": "22px", "color": TEXT3, "cursor": "pointer",
                            "line_height": "1", "_hover": {"color": TEXT},
                        }),
                    ),
                    align_items="center", width="100%",
                ),
                rx.divider(style={"border_color": BORDER}),

                _field("Account Name",
                    _inp("e.g. Checking Account", AppState.add_acct_name,
                         AppState.set_add_acct_name),
                ),
                _field("Type",
                    _sel(
                        rx.el.option("Budget / Checking", value="budget"),
                        rx.el.option("Savings", value="savings"),
                        rx.el.option("Debt / Credit Card", value="debt"),
                        rx.el.option("Investment", value="investment"),
                        value=AppState.add_acct_type,
                        on_change=AppState.set_add_acct_type,
                    ),
                ),
                rx.hstack(
                    _field("Opening Balance",
                        _inp("0.00", AppState.add_acct_opening,
                             AppState.set_add_acct_opening, type_="number",
                             input_mode="decimal"),
                    ),
                    _field("Color",
                        rx.el.input(
                            type="color",
                            value=AppState.add_acct_color,
                            on_change=AppState.set_add_acct_color,
                            style={
                                "width": "100%", "height": "36px", "border_radius": "8px",
                                "border": f"1px solid {BORDER}", "cursor": "pointer",
                                "background": "transparent", "padding": "2px",
                            },
                        ),
                    ),
                    gap="10px", width="100%",
                ),

                _err(AppState.add_acct_error),

                rx.hstack(
                    rx.dialog.close(
                        rx.box("Cancel", style={
                            "flex": "1", "padding": "9px", "border_radius": "8px",
                            "border": f"1px solid {BORDER}", "color": TEXT3,
                            "font_size": "11px", "text_align": "center", "cursor": "pointer",
                            "font_family": MONO,
                        }),
                    ),
                    rx.box(
                        rx.cond(AppState.add_acct_saving, "Saving…", "Add Account"),
                        on_click=AppState.save_add_account,
                        style={
                            "flex": "2", "padding": "9px", "border_radius": "8px",
                            "background": rx.cond(AppState.add_acct_saving, BORDER, ACCENT),
                            "color": "#fff", "font_size": "11px", "text_align": "center",
                            "cursor": "pointer", "font_family": MONO,
                            "letter_spacing": "0.06em", "text_transform": "uppercase",
                            "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", width="100%",
                ),

                gap="12px", width="100%",
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "14px", "padding": "22px",
                "max_width": "420px", "width": "95vw",
            },
        ),
        open=AppState.add_acct_open,
        on_open_change=AppState.set_add_acct_open,
    )


# ── Account settings dialog ───────────────────────────────────────────────────

def _account_settings_dialog() -> rx.Component:
    is_debt = AppState.acct_settings_type == "debt"
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Account Settings", style={
                        "font_size": "11px", "letter_spacing": "0.14em",
                        "text_transform": "uppercase", "color": TEXT2,
                        "flex": "1", "font_family": MONO,
                    }),
                    rx.dialog.close(
                        rx.box("×", style={
                            "font_size": "22px", "color": TEXT3, "cursor": "pointer",
                            "line_height": "1", "_hover": {"color": TEXT},
                        }),
                    ),
                    align_items="center", width="100%",
                ),
                rx.divider(style={"border_color": BORDER}),

                _field("Account Name",
                    _inp("Account name", AppState.acct_settings_name,
                         AppState.set_acct_settings_name),
                ),
                _field("Type",
                    _sel(
                        rx.el.option("Budget / Checking", value="budget"),
                        rx.el.option("Savings", value="savings"),
                        rx.el.option("Debt / Credit Card", value="debt"),
                        rx.el.option("Investment", value="investment"),
                        value=AppState.acct_settings_type,
                        on_change=AppState.set_acct_settings_type,
                    ),
                ),
                rx.hstack(
                    _field("Opening Balance",
                        _inp("0.00", AppState.acct_settings_opening,
                             AppState.set_acct_settings_opening, type_="number",
                             input_mode="decimal"),
                    ),
                    _field("Color",
                        rx.el.input(
                            type="color",
                            value=AppState.acct_settings_color,
                            on_change=AppState.set_acct_settings_color,
                            style={
                                "width": "100%", "height": "36px", "border_radius": "8px",
                                "border": f"1px solid {BORDER}", "cursor": "pointer",
                                "background": "transparent", "padding": "2px",
                            },
                        ),
                    ),
                    gap="10px", width="100%",
                ),

                # Debt-specific fields
                rx.cond(
                    is_debt,
                    rx.vstack(
                        _field("APR (%)",
                            _inp("e.g. 24.99", AppState.acct_settings_apr,
                                 AppState.set_acct_settings_apr, type_="number",
                                 input_mode="decimal"),
                        ),
                        _field("Minimum Payment",
                            _inp("e.g. 25.00", AppState.acct_settings_min_pay,
                                 AppState.set_acct_settings_min_pay, type_="number",
                                 input_mode="decimal"),
                        ),
                        _field("Credit Limit",
                            _inp("e.g. 5000", AppState.acct_settings_credit,
                                 AppState.set_acct_settings_credit, type_="number",
                                 input_mode="decimal"),
                        ),
                        _field("Promotional rate",
                            rx.hstack(
                                rx.el.input(
                                    type="checkbox",
                                    checked=AppState.acct_settings_is_promo,
                                    on_change=AppState.set_acct_settings_is_promo,
                                    style={"cursor": "pointer", "width": "16px", "height": "16px"},
                                ),
                                rx.text("Promotional rate active", style={
                                    "font_size": "12px", "color": TEXT2, "font_family": MONO,
                                    "cursor": "pointer",
                                }),
                                align_items="center", gap="8px",
                            ),
                        ),
                        rx.cond(
                            AppState.acct_settings_is_promo,
                            _field("Promo ends (YYYY-MM-DD)",
                                _inp("YYYY-MM-DD", AppState.acct_settings_promo_end,
                                     AppState.set_acct_settings_promo_end, type_="date"),
                            ),
                            rx.box(),
                        ),
                        gap="12px", width="100%",
                    ),
                    rx.box(),
                ),

                _err(AppState.acct_settings_error),

                rx.hstack(
                    rx.box(
                        "Archive",
                        on_click=AppState.archive_account(AppState.acct_settings_aid),
                        style={
                            "flex": "1", "padding": "9px", "border_radius": "8px",
                            "border": f"1px solid {RED}44", "color": RED,
                            "font_size": "11px", "text_align": "center", "cursor": "pointer",
                            "font_family": MONO, "_hover": {"background": f"{RED}11"},
                        },
                    ),
                    rx.dialog.close(
                        rx.box("Cancel", style={
                            "flex": "1", "padding": "9px", "border_radius": "8px",
                            "border": f"1px solid {BORDER}", "color": TEXT3,
                            "font_size": "11px", "text_align": "center", "cursor": "pointer",
                            "font_family": MONO,
                        }),
                    ),
                    rx.box(
                        rx.cond(AppState.acct_settings_saving, "Saving…", "Save"),
                        on_click=AppState.save_account_settings,
                        style={
                            "flex": "2", "padding": "9px", "border_radius": "8px",
                            "background": rx.cond(AppState.acct_settings_saving, BORDER, ACCENT),
                            "color": "#fff", "font_size": "11px", "text_align": "center",
                            "cursor": "pointer", "font_family": MONO,
                            "letter_spacing": "0.06em", "text_transform": "uppercase",
                            "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", width="100%",
                ),

                gap="12px", width="100%",
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "14px", "padding": "22px",
                "max_width": "420px", "width": "95vw",
            },
        ),
        open=AppState.acct_settings_open,
        on_open_change=AppState.set_acct_settings_open,
    )


# ── Debt payment dialog ───────────────────────────────────────────────────────

def _debt_payment_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Record Debt Payment", style={
                            "font_size": "11px", "letter_spacing": "0.14em",
                            "text_transform": "uppercase", "color": TEXT2,
                            "font_family": MONO,
                        }),
                        rx.text(AppState.debt_pay_acct_name, style={
                            "font_size": "13px", "color": AMBER, "font_weight": "600",
                        }),
                        gap="1px", align_items="flex-start", flex="1",
                    ),
                    rx.dialog.close(
                        rx.box("×", style={
                            "font_size": "22px", "color": TEXT3, "cursor": "pointer",
                            "line_height": "1", "_hover": {"color": TEXT},
                        }),
                    ),
                    align_items="flex-start", width="100%",
                ),
                rx.divider(style={"border_color": BORDER}),

                rx.hstack(
                    _field("Amount",
                        _inp("0.00", AppState.debt_pay_amount,
                             AppState.set_debt_pay_amount, type_="number",
                             input_mode="decimal"),
                    ),
                    _field("Date",
                        _inp("", AppState.debt_pay_date,
                             AppState.set_debt_pay_date, type_="date"),
                    ),
                    gap="10px", width="100%",
                ),

                _field("Pay From Account",
                    rx.el.select(
                        AppState.account_options.to(list[dict[str, Any]]).foreach(
                            lambda a: rx.el.option(a["name"], value=a["id"])
                        ),
                        value=AppState.debt_pay_from_account,
                        on_change=AppState.set_debt_pay_from_account,
                        style=_select_style(),
                    ),
                ),

                _field("Bucket (optional)",
                    rx.el.select(
                        rx.el.option("— No bucket —", value=""),
                        AppState.expense_buckets.to(list[dict[str, Any]]).foreach(
                            lambda b: rx.el.option(b["name"], value=b["id"])
                        ),
                        value=AppState.debt_pay_bucket,
                        on_change=AppState.set_debt_pay_bucket,
                        style=_select_style(),
                    ),
                ),

                _err(AppState.debt_pay_error),

                rx.hstack(
                    rx.dialog.close(
                        rx.box("Cancel", style={
                            "flex": "1", "padding": "9px", "border_radius": "8px",
                            "border": f"1px solid {BORDER}", "color": TEXT3,
                            "font_size": "11px", "text_align": "center", "cursor": "pointer",
                            "font_family": MONO,
                        }),
                    ),
                    rx.box(
                        rx.cond(AppState.debt_pay_saving, "Saving…", "Record Payment"),
                        on_click=AppState.save_debt_payment,
                        style={
                            "flex": "2", "padding": "9px", "border_radius": "8px",
                            "background": rx.cond(AppState.debt_pay_saving, BORDER, AMBER),
                            "color": "#fff", "font_size": "11px", "text_align": "center",
                            "cursor": "pointer", "font_family": MONO,
                            "letter_spacing": "0.06em", "text_transform": "uppercase",
                            "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", width="100%",
                ),

                gap="12px", width="100%",
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "14px", "padding": "22px",
                "max_width": "420px", "width": "95vw",
            },
        ),
        open=AppState.debt_pay_open,
        on_open_change=AppState.set_debt_pay_open,
    )


# ── Right column: account balance summary ────────────────────────────────────

def _right_column() -> rx.Component:
    _CARD = {
        "background": BG2, "border": f"1px solid {BORDER}",
        "border_radius": "12px", "padding": "14px 16px",
        "margin_bottom": "12px", "width": "100%",
    }
    _LABEL = {
        "font_size": "10px", "letter_spacing": "0.14em",
        "text_transform": "uppercase", "color": TEXT3,
        "font_family": MONO, "font_weight": "600",
        "display": "block", "margin_bottom": "10px",
    }
    return rx.vstack(

        # Accounts card
        rx.box(
            rx.text("ACCOUNTS", style=_LABEL),
            rx.foreach(
                AppState.accounts_rows.to(list[dict[str, Any]]),
                _acct_balance_card,
            ),
            rx.divider(style={"border_color": BORDER, "margin": "8px 0 10px"}),
            # Cash total
            rx.hstack(
                rx.text("Cash Total", style={"font_size": "12px", "color": TEXT3}),
                rx.spacer(),
                rx.text(AppState.total_cash_fmt, style={
                    "font_size": "14px", "font_family": MONO,
                    "font_weight": "700", "color": GREEN,
                }),
                align_items="center", width="100%",
                style={"margin_bottom": "4px"},
            ),
            # Debt total
            rx.cond(
                AppState.total_debt > 0,
                rx.hstack(
                    rx.text("Debt Total", style={"font_size": "12px", "color": TEXT3}),
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

        # This month card
        rx.box(
            rx.text("THIS MONTH", style=_LABEL),
            rx.hstack(
                rx.hstack(
                    rx.box(style={
                        "width": "7px", "height": "7px", "border_radius": "50%",
                        "background": GREEN, "flex_shrink": "0",
                    }),
                    rx.text("Income", style={"font_size": "11px", "color": TEXT3}),
                    rx.text(AppState.income_fmt, style={
                        "font_size": "13px", "color": GREEN,
                        "font_family": MONO, "font_weight": "700",
                    }),
                    align_items="center", gap="5px",
                ),
                rx.hstack(
                    rx.box(style={
                        "width": "7px", "height": "7px", "border_radius": "50%",
                        "background": RED, "flex_shrink": "0",
                    }),
                    rx.text("Spent", style={"font_size": "11px", "color": TEXT3}),
                    rx.text(AppState.spent_fmt, style={
                        "font_size": "13px", "color": RED,
                        "font_family": MONO, "font_weight": "700",
                    }),
                    align_items="center", gap="5px",
                ),
                gap="14px", flex_wrap="wrap",
            ),
            rx.divider(style={"border_color": BORDER, "margin": "8px 0"}),
            rx.hstack(
                rx.text("Net", style={"font_size": "12px", "color": TEXT3}),
                rx.spacer(),
                rx.text(AppState.rts_fmt, style={
                    "font_size": "14px", "font_family": MONO, "font_weight": "800",
                    "color": AppState.rts_color,
                }),
                align_items="center", width="100%",
            ),
            style=_CARD,
        ),

        # Add account button
        rx.box(
            "+ Add Account",
            on_click=AppState.open_add_account,
            style={
                "font_size": "11px", "letter_spacing": "0.08em",
                "text_transform": "uppercase", "padding": "9px 14px",
                "border_radius": "8px", "border": f"1px dashed {ACCENT}55",
                "color": ACCENT, "cursor": "pointer", "font_family": MONO,
                "text_align": "center", "width": "100%",
                "_hover": {"background": f"{ACCENT}0d"},
            },
        ),

        gap="0px", align_items="stretch", width="100%",
    )


# ── Account filter chips ──────────────────────────────────────────────────────

def _filter_chip(row: dict) -> rx.Component:
    is_active = AppState.ledger_acct_filter == row["id"]
    return rx.box(
        rx.hstack(
            rx.box(style={
                "width": "7px", "height": "7px", "border_radius": "50%",
                "background": row["color"], "flex_shrink": "0",
            }),
            rx.text(row["name"], style={"white_space": "nowrap"}),
            align_items="center", gap="5px",
        ),
        on_click=AppState.set_ledger_acct_filter(
            rx.cond(is_active, "", row["id"])
        ),
        style=rx.cond(
            is_active,
            {
                "padding": "5px 12px", "border_radius": "20px",
                "font_size": "12px", "font_family": MONO, "cursor": "pointer",
                "color": ACCENT, "background": f"{ACCENT}18",
                "border": f"1px solid {ACCENT}44", "flex_shrink": "0",
            },
            {
                "padding": "5px 12px", "border_radius": "20px",
                "font_size": "12px", "font_family": MONO, "cursor": "pointer",
                "color": TEXT3, "background": BG3,
                "border": f"1px solid {BORDER}", "flex_shrink": "0",
                "_hover": {"color": TEXT2, "border_color": BORDER2},
            },
        ),
    )


def _all_chip() -> rx.Component:
    is_active = AppState.ledger_acct_filter == ""
    return rx.box(
        "All",
        on_click=AppState.set_ledger_acct_filter(""),
        style=rx.cond(
            is_active,
            {
                "padding": "5px 12px", "border_radius": "20px",
                "font_size": "12px", "font_family": MONO, "cursor": "pointer",
                "color": ACCENT, "background": f"{ACCENT}18",
                "border": f"1px solid {ACCENT}44", "flex_shrink": "0",
            },
            {
                "padding": "5px 12px", "border_radius": "20px",
                "font_size": "12px", "font_family": MONO, "cursor": "pointer",
                "color": TEXT3, "background": BG3,
                "border": f"1px solid {BORDER}", "flex_shrink": "0",
                "_hover": {"color": TEXT2, "border_color": BORDER2},
            },
        ),
    )


# ── Reconcile modal ──────────────────────────────────────────────────────────

def _recon_tx_row(row: dict) -> rx.Component:
    """Single transaction row inside the reconcile checklist."""
    tx_id      = row["id"].to(str)
    # Checked by default — only explicitly unchecked IDs are in recon_unchecked_ids
    is_checked = ~AppState.recon_unchecked_ids.contains(tx_id)
    return rx.hstack(
        # Checkbox-style indicator
        rx.box(
            rx.cond(
                is_checked,
                rx.html(
                    f'<svg width="14" height="14" viewBox="0 0 24 24" fill="{GREEN}" '
                    f'stroke="{GREEN}" stroke-width="2" aria-hidden="true">'
                    '<rect x="3" y="3" width="18" height="18" rx="3"/>'
                    '<polyline points="20 6 9 17 4 12" stroke="white" stroke-width="2.5" '
                    'fill="none"/></svg>'
                ),
                rx.html(
                    f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
                    f'stroke="{BORDER2}" stroke-width="1.5" aria-hidden="true">'
                    '<rect x="3" y="3" width="18" height="18" rx="3"/></svg>'
                ),
            ),
            style={"flex_shrink": "0"},
        ),
        # Description + date
        rx.vstack(
            rx.text(row["desc"], style={
                "font_size": "13px", "color": rx.cond(is_checked, TEXT, TEXT3),
                "font_weight": "500", "line_height": "1.2",
                "overflow": "hidden", "text_overflow": "ellipsis", "white_space": "nowrap",
                "max_width": "200px",
            }),
            rx.text(row["date_label"], style={
                "font_size": "11px", "color": TEXT3, "font_family": MONO,
            }),
            gap="1px", align_items="flex-start",
        ),
        rx.spacer(),
        # Amount
        rx.text(row["amount_fmt"], style={
            "font_size": "13px", "font_family": MONO, "font_weight": "700",
            "color": rx.cond(is_checked, row["amt_color"], TEXT3),
            "white_space": "nowrap",
        }),
        on_click=AppState.toggle_recon_tx(tx_id),
        role="checkbox",
        aria_checked=rx.cond(is_checked, "true", "false"),
        style={
            "padding": "10px 14px", "min_height": "52px",
            "border_bottom": f"1px solid {BORDER}",
            "cursor": "pointer", "width": "100%",
            "align_items": "center", "gap": "10px",
            "_hover": {"background": BG3},
            "_active": {"opacity": "0.8"},
        },
    )


def reconcile_modal() -> rx.Component:
    """Full-screen-style reconciliation overlay."""
    diff_color = rx.cond(AppState.recon_can_finish, GREEN, AMBER)

    return rx.cond(
        AppState.recon_open,
        rx.box(
            rx.box(
                rx.vstack(
                    # ── Header ───────────────────────────────────────────
                    rx.hstack(
                        rx.vstack(
                            rx.text("RECONCILE", style={
                                "font_size": "11px", "letter_spacing": "0.16em",
                                "color": TEXT3, "font_family": MONO,
                            }),
                            rx.text(AppState.recon_account_name, style={
                                "font_size": "17px", "font_weight": "700", "color": TEXT,
                                "line_height": "1.1",
                            }),
                            gap="2px", align_items="flex-start",
                        ),
                        rx.spacer(),
                        rx.box(
                            "×",
                            on_click=AppState.close_reconcile,
                            style={
                                "font_size": "24px", "color": TEXT3, "cursor": "pointer",
                                "line_height": "1", "_hover": {"color": TEXT},
                                "padding": "4px 6px",
                            },
                        ),
                        align_items="flex-start", width="100%",
                    ),

                    rx.divider(style={"border_color": BORDER}),

                    # ── Account selector (if multiple accounts) ───────────
                    rx.cond(
                        AppState.accounts_rows.length() > 1,
                        rx.el.select(
                            AppState.accounts_rows.to(list[dict[str, Any]]).foreach(
                                lambda a: rx.el.option(a["name"], value=a["id"])
                            ),
                            value=AppState.recon_account_id,
                            on_change=AppState.set_recon_account_id,
                            style={**_select_style(), "margin_bottom": "4px"},
                        ),
                        rx.box(),
                    ),

                    # ── Statement balance input ───────────────────────────
                    rx.vstack(
                        rx.text("Enter your bank balance", style={
                            "font_size": "11px", "letter_spacing": "0.1em",
                            "text_transform": "uppercase", "color": TEXT3,
                            "font_family": MONO,
                        }),
                        rx.input(
                            placeholder="0.00",
                            value=AppState.recon_statement_balance,
                            on_change=AppState.set_recon_statement_balance,
                            type="text", input_mode="decimal",
                            auto_focus=True,
                            style={
                                **_input_style(),
                                "font_size": "22px", "text_align": "center",
                                "font_family": MONO, "font_weight": "700",
                                "border_color": rx.cond(
                                    AppState.recon_statement_balance != "",
                                    rx.cond(AppState.recon_can_finish, GREEN, BORDER),
                                    BORDER,
                                ),
                            },
                        ),
                        gap="6px", width="100%",
                    ),

                    # ── Running totals ────────────────────────────────────
                    rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text("STATEMENT", style={
                                    "font_size": "10px", "letter_spacing": "0.12em",
                                    "color": TEXT3, "font_family": MONO,
                                }),
                                rx.text(
                                    rx.cond(
                                        AppState.recon_statement_balance != "",
                                        "$" + AppState.recon_statement_balance,
                                        "—",
                                    ),
                                    style={"font_size": "15px", "font_family": MONO,
                                           "font_weight": "700", "color": TEXT},
                                ),
                                align_items="center", gap="2px",
                            ),
                            rx.vstack(
                                rx.text("CLEARED", style={
                                    "font_size": "10px", "letter_spacing": "0.12em",
                                    "color": TEXT3, "font_family": MONO,
                                }),
                                rx.text(AppState.recon_cleared_fmt, style={
                                    "font_size": "15px", "font_family": MONO,
                                    "font_weight": "700", "color": TEXT,
                                }),
                                align_items="center", gap="2px",
                            ),
                            rx.vstack(
                                rx.text("DIFFERENCE", style={
                                    "font_size": "10px", "letter_spacing": "0.12em",
                                    "color": TEXT3, "font_family": MONO,
                                }),
                                rx.text(AppState.recon_difference_fmt, style={
                                    "font_size": "20px", "font_family": MONO,
                                    "font_weight": "800",
                                    "color": diff_color,
                                }),
                                align_items="center", gap="2px",
                            ),
                            justify="between", width="100%", align_items="flex-start",
                        ),
                        style={
                            "background": BG3, "border": f"1px solid {BORDER}",
                            "border_radius": "10px", "padding": "12px 16px",
                            "width": "100%",
                        },
                    ),

                    # ── Instruction ───────────────────────────────────────
                    rx.text(
                        "Uncheck any transactions that haven't posted to your bank yet.",
                        style={"font_size": "12px", "color": TEXT3, "font_family": MONO,
                               "text_align": "center"},
                    ),

                    # ── Transaction checklist ─────────────────────────────
                    rx.cond(
                        AppState.recon_txs.length() == 0,
                        rx.box(
                            rx.text("No unreconciled transactions.", style={
                                "font_size": "13px", "color": TEXT3, "font_family": MONO,
                                "text_align": "center", "padding": "20px",
                            }),
                            style={"width": "100%"},
                        ),
                        rx.box(
                            rx.foreach(
                                AppState.recon_txs.to(list[dict[str, Any]]),
                                _recon_tx_row,
                            ),
                            style={
                                "width": "100%",
                                "border": f"1px solid {BORDER}",
                                "border_radius": "10px",
                                "overflow": "hidden",
                                "max_height": "320px",
                                "overflow_y": "auto",
                            },
                        ),
                    ),

                    # ── Error ─────────────────────────────────────────────
                    rx.cond(
                        AppState.recon_error != "",
                        rx.text(AppState.recon_error, style={
                            "color": RED, "font_size": "12px", "font_family": MONO,
                        }),
                        rx.box(),
                    ),

                    # ── Footer ────────────────────────────────────────────
                    rx.hstack(
                        rx.box(
                            "Cancel",
                            on_click=AppState.close_reconcile,
                            style={
                                "flex": "1", "padding": "11px", "border_radius": "8px",
                                "border": f"1px solid {BORDER}", "color": TEXT3,
                                "font_size": "12px", "text_align": "center",
                                "cursor": "pointer", "font_family": MONO,
                                "_hover": {"color": TEXT2},
                            },
                        ),
                        rx.box(
                            rx.cond(
                                AppState.recon_saving,
                                "Saving…",
                                rx.cond(
                                    AppState.recon_can_finish,
                                    "✓  Finish Reconciliation",
                                    "Difference must be $0.00",
                                ),
                            ),
                            on_click=AppState.finish_reconcile,
                            style={
                                "flex": "2", "padding": "11px", "border_radius": "8px",
                                "background": rx.cond(
                                    AppState.recon_can_finish,
                                    rx.cond(AppState.recon_saving, BORDER, GREEN),
                                    BG3,
                                ),
                                "color": rx.cond(AppState.recon_can_finish, "#fff", TEXT3),
                                "border": rx.cond(
                                    AppState.recon_can_finish,
                                    f"1px solid {GREEN}",
                                    f"1px solid {BORDER}",
                                ),
                                "font_size": "12px", "text_align": "center",
                                "cursor": rx.cond(AppState.recon_can_finish, "pointer", "default"),
                                "font_family": MONO, "font_weight": "700",
                                "letter_spacing": "0.06em",
                                "_hover": {"opacity": rx.cond(AppState.recon_can_finish, "0.9", "1")},
                                "transition": "all 0.2s ease",
                            },
                        ),
                        gap="8px", width="100%",
                    ),

                    gap="14px", width="100%",
                ),

                style={
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "16px", "padding": "22px",
                    "width": "100%", "max_width": "480px",
                    "max_height": "90vh", "overflow_y": "auto",
                },
            ),

            style={
                "position": "fixed", "inset": "0",
                "background": "rgba(0,0,0,0.65)",
                "backdrop_filter": "blur(4px)",
                "z_index": "300",
                "display": "flex", "align_items": "center", "justify_content": "center",
                "padding": "20px",
            },
        ),
        rx.box(),
    )


# ── Main panel ────────────────────────────────────────────────────────────────

def accounts_panel() -> rx.Component:
    return rx.box(
        rx.box(
            # ── Left column: filter chips + transactions ──────────────────
            rx.vstack(

                # Account filter chips (contained + labeled)
                rx.box(
                    rx.text("ACCOUNTS", style={
                        "font_size": "10px", "letter_spacing": "0.14em",
                        "text_transform": "uppercase", "color": TEXT3,
                        "font_family": MONO, "margin_bottom": "8px",
                    }),
                    rx.hstack(
                        _all_chip(),
                        rx.foreach(
                            AppState.accounts_rows.to(list[dict[str, Any]]),
                            _filter_chip,
                        ),
                        gap="6px", flex_wrap="wrap",
                    ),
                    style={
                        "background": BG2, "border": f"1px solid {BORDER}",
                        "border_radius": "10px", "padding": "12px 14px",
                        "margin_bottom": "12px", "width": "100%",
                    },
                ),

                # KPI summary boxes
                _kpi_row(),

                # Search bar + CSV export + Add Tx
                rx.hstack(
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
                                "background": "transparent", "border": "none",
                                "outline": "none",
                                "color": TEXT, "font_family": MONO, "font_size": "13px",
                                "flex": "1", "width": "100%",
                            },
                        ),
                        rx.cond(
                            AppState.ledger_query != "",
                            rx.box("×", on_click=AppState.set_ledger_query(""),
                                   style={"color": TEXT3, "cursor": "pointer",
                                          "font_size": "18px",
                                          "_hover": {"color": TEXT}}),
                            rx.box(),
                        ),
                        style={
                            "background": BG2, "border": f"1px solid {BORDER}",
                            "border_radius": "8px", "padding": "9px 14px",
                            "align_items": "center", "gap": "8px", "flex": "1",
                        },
                    ),
                    rx.box(
                        "↓ CSV",
                        on_click=AppState.export_transactions_csv,
                        style={
                            "font_family": MONO, "font_size": "11px",
                            "letter_spacing": "0.08em",
                            "padding": "8px 12px", "border_radius": "8px",
                            "border": f"1px solid {BORDER}", "color": TEXT2,
                            "cursor": "pointer", "white_space": "nowrap",
                            "flex_shrink": "0",
                            "_hover": {"background": BG2, "color": TEXT},
                        },
                    ),
                    rx.box(
                        "⚖ Reconcile",
                        on_click=AppState.open_reconcile(AppState.ledger_acct_filter),
                        style={
                            "font_family": MONO, "font_size": "11px",
                            "letter_spacing": "0.08em",
                            "padding": "8px 12px", "border_radius": "8px",
                            "border": f"1px solid {GREEN}55", "color": GREEN,
                            "cursor": "pointer", "white_space": "nowrap",
                            "flex_shrink": "0",
                            "_hover": {"background": f"{GREEN}0d"},
                        },
                    ),
                    rx.box(
                        "+ Tx",
                        on_click=AppState.open_sheet,
                        style={
                            "font_family": MONO, "font_size": "11px",
                            "letter_spacing": "0.08em",
                            "padding": "8px 12px", "border_radius": "8px",
                            "background": ACCENT, "color": "#fff",
                            "cursor": "pointer", "white_space": "nowrap",
                            "flex_shrink": "0",
                            "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", align_items="center",
                    style={"margin_bottom": "4px", "width": "100%"},
                ),

                # Statement blocks (sections + per-day cards)
                rx.foreach(
                    AppState.ledger_view["blocks"].to(list[dict[str, Any]]),
                    _ledger_block,
                ),

                # Empty state
                rx.cond(
                    AppState.ledger_view["empty"] == "1",
                    rx.box(
                        rx.text("No transactions to show.",
                                style={"color": TEXT3, "font_size": "13px",
                                       "font_family": MONO}),
                        style={"text_align": "center", "padding": "40px 0"},
                    ),
                    rx.box(),
                ),

                gap="0", align_items="stretch", width="100%",
            ),

            # ── Right column: balances ────────────────────────────────────
            rx.box(
                _right_column(),
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

        # Dialogs + modals
        edit_tx_dialog(),
        add_tx_sheet(),
        _add_account_dialog(),
        _account_settings_dialog(),
        _debt_payment_dialog(),
        reconcile_modal(),
    )
