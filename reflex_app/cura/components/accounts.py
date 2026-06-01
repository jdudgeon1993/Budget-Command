"""Accounts panel — balances, transaction history, debt payments, account settings."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _inp(placeholder: str, value, on_change, type_: str = "text", **extra) -> rx.Component:
    return rx.input(
        placeholder=placeholder, value=value, on_change=on_change, type=type_,
        style={
            "background": BG3, "border": f"1px solid {BORDER}",
            "border_radius": "8px", "color": TEXT, "font_family": MONO,
            "font_size": "12px", "padding": "8px 12px", "outline": "none",
            "_focus": {"border_color": ACCENT}, "_placeholder": {"color": TEXT3},
            **extra,
        },
    )


def _field(label: str, child: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={
            "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
            "text_transform": "uppercase", "font_family": MONO,
        }),
        child,
        gap="4px", align_items="stretch", width="100%",
    )


def _sel(*opts, value, on_change, **extra) -> rx.Component:
    return rx.el.select(
        *opts, value=value, on_change=on_change,
        style={
            "background": BG3, "border": f"1px solid {BORDER}",
            "border_radius": "8px", "color": TEXT, "font_size": "12px",
            "padding": "8px 10px", **extra,
        },
    )


def _btn(label, on_click, bg=ACCENT, loading_label: str = "…", saving: bool = False) -> rx.Component:
    return rx.box(
        rx.cond(saving, loading_label, label),
        on_click=on_click,
        style={
            "padding": "9px 16px", "border_radius": "8px",
            "background": rx.cond(saving, BORDER, bg),
            "color": "#fff", "font_size": "12px", "cursor": "pointer",
            "font_family": MONO, "letter_spacing": "0.06em",
            "text_transform": "uppercase", "white_space": "nowrap",
            "_hover": {"opacity": "0.9"},
        },
    )


def _err(msg) -> rx.Component:
    return rx.cond(
        msg != "",
        rx.text(msg, style={"color": RED, "font_size": "11px", "font_family": MONO}),
        rx.box(),
    )


# ── Account transaction mini-ledger ──────────────────────────────────────────

def _acct_tx_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(row["desc"], style={"font_size": "12px", "color": TEXT, "font_weight": "500"}),
            rx.hstack(
                rx.text(row["date_label"], style={"font_size": "11px", "color": TEXT3, "font_family": MONO}),
                rx.cond(
                    row["bucket"] != "",
                    rx.text("·", row["bucket"],
                            style={"font_size": "11px", "color": TEXT3, "font_family": MONO}),
                    rx.box(),
                ),
                gap="4px",
            ),
            gap="1px", align_items="flex-start", flex="1",
        ),
        rx.text(row["amount_fmt"], style={
            "font_family": MONO, "font_size": "13px", "font_weight": "600",
            "color": row["amt_color"], "white_space": "nowrap",
        }),
        align_items="center", width="100%", gap="8px",
        style={"padding": "7px 12px", "border_bottom": f"1px solid {BORDER}"},
    )


# ── Account card ─────────────────────────────────────────────────────────────

def _acct_card(row: dict) -> rx.Component:
    is_expanded = AppState.acct_expanded_id == row["id"]
    is_debt     = row["type"] == "debt"

    return rx.vstack(
        # Header row
        rx.hstack(
            rx.box(style={
                "width": "10px", "height": "10px", "border_radius": "50%",
                "background": row["color"], "flex_shrink": "0",
            }),
            rx.vstack(
                rx.text(row["name"], style={"font_size": "14px", "font_weight": "600", "color": TEXT}),
                rx.text(row["type_upper"], style={
                    "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
                    "font_family": MONO,
                }),
                gap="1px", align_items="flex-start", flex="1",
            ),
            rx.text(row["balance_fmt"], style={
                "font_family": MONO, "font_size": "16px", "font_weight": "700",
                "color": row["bal_color"],
            }),
            # Expand toggle
            rx.box(
                rx.cond(is_expanded, "▲", "▼"),
                on_click=AppState.toggle_acct_expand(row["id"]),
                style={
                    "font_size": "11px", "color": TEXT3, "cursor": "pointer",
                    "padding": "4px 8px", "border_radius": "4px",
                    "_hover": {"color": TEXT2, "background": BG3},
                },
            ),
            # Settings gear
            rx.box(
                rx.html('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
                        'stroke="currentColor" stroke-width="1.75" aria-hidden="true">'
                        '<circle cx="12" cy="12" r="3"/>'
                        '<path d="M19.1 12a7.1 7.1 0 0 0-.1-1l2.2-1.7-2.1-3.6-2.6 1'
                        'a7 7 0 0 0-1.7-1l-.4-2.7h-4.2l-.4 2.7a7 7 0 0 0-1.7 1l-2.6-1'
                        '-2.1 3.6 2.2 1.7a7.1 7.1 0 0 0 0 2l-2.2 1.7 2.1 3.6 2.6-1'
                        'a7 7 0 0 0 1.7 1l.4 2.7h4.2l.4-2.7a7 7 0 0 0 1.7-1l2.6 1'
                        ' 2.1-3.6-2.2-1.7a7.1 7.1 0 0 0 .1-1z"/></svg>'),
                on_click=AppState.open_account_settings(row["id"]),
                style={
                    "color": TEXT3, "cursor": "pointer", "padding": "4px 6px",
                    "border_radius": "4px",
                    "_hover": {"color": ACCENT, "background": f"{ACCENT}11"},
                },
            ),
            # Debt payment button
            rx.cond(
                is_debt,
                rx.box(
                    "Pay",
                    on_click=AppState.open_debt_payment(row["id"]),
                    style={
                        "font_size": "11px", "color": AMBER, "cursor": "pointer",
                        "padding": "4px 8px", "border_radius": "4px",
                        "border": f"1px solid {AMBER}44",
                        "_hover": {"background": f"{AMBER}11"},
                        "font_family": MONO,
                    },
                ),
                rx.box(),
            ),
            align_items="center", width="100%", gap="8px",
            style={"padding": "12px 14px"},
        ),

        # Expanded mini-ledger
        rx.cond(
            is_expanded,
            rx.vstack(
                rx.cond(
                    AppState.acct_ledger_rows.length() == 0,
                    rx.text("No transactions yet.",
                            style={"font_size": "12px", "color": TEXT3, "padding": "12px 14px",
                                   "font_family": MONO}),
                    rx.foreach(
                        AppState.acct_ledger_rows.to(list[dict[str, Any]]),
                        _acct_tx_row,
                    ),
                ),
                width="100%", gap="0px",
                style={"border_top": f"1px solid {BORDER}"},
            ),
            rx.box(),
        ),

        width="100%", gap="0px",
        style={
            "background": BG2, "border": f"1px solid {BORDER}",
            "border_radius": "10px", "overflow": "hidden",
            "margin_bottom": "6px",
        },
    )


# ── Summary bar ───────────────────────────────────────────────────────────────

def _summary_bar() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text("Cash & Budget", style={"font_size": "11px", "color": TEXT3,
                                             "letter_spacing": "0.1em", "text_transform": "uppercase",
                                             "font_family": MONO}),
            rx.text(AppState.total_cash_fmt, style={
                "font_size": "18px", "font_weight": "700", "font_family": MONO, "color": GREEN,
            }),
            gap="2px", align_items="flex-start", flex="1",
        ),
        rx.vstack(
            rx.text("Debt", style={"font_size": "11px", "color": TEXT3,
                                    "letter_spacing": "0.1em", "text_transform": "uppercase",
                                    "font_family": MONO}),
            rx.text(AppState.total_debt_fmt, style={
                "font_size": "18px", "font_weight": "700", "font_family": MONO, "color": RED,
            }),
            gap="2px", align_items="flex-start", flex="1",
        ),
        width="100%",
        style={
            "background": BG2, "border": f"1px solid {BORDER}",
            "border_radius": "10px", "padding": "14px 16px",
            "margin_bottom": "16px",
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
                rx.hstack(
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
                _field("Opening Balance",
                    _inp("0.00", AppState.acct_settings_opening,
                         AppState.set_acct_settings_opening, type_="number",
                         input_mode="decimal"),
                ),

                # Debt-specific fields
                rx.cond(
                    is_debt,
                    rx.vstack(
                        rx.hstack(
                            _field("APR (%)",
                                _inp("e.g. 22.99", AppState.acct_settings_apr,
                                     AppState.set_acct_settings_apr, type_="number",
                                     input_mode="decimal"),
                            ),
                            _field("Min Payment",
                                _inp("e.g. 25.00", AppState.acct_settings_min_pay,
                                     AppState.set_acct_settings_min_pay, type_="number",
                                     input_mode="decimal"),
                            ),
                            gap="10px", width="100%",
                        ),
                        _field("Credit Limit",
                            _inp("e.g. 5000", AppState.acct_settings_credit,
                                 AppState.set_acct_settings_credit, type_="number",
                                 input_mode="decimal"),
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
                        style={
                            "background": BG3, "border": f"1px solid {BORDER}",
                            "border_radius": "8px", "color": TEXT, "font_size": "12px",
                            "padding": "8px 10px", "width": "100%",
                        },
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
                        style={
                            "background": BG3, "border": f"1px solid {BORDER}",
                            "border_radius": "8px", "color": TEXT, "font_size": "12px",
                            "padding": "8px 10px", "width": "100%",
                        },
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


# ── Main panel ────────────────────────────────────────────────────────────────

def accounts_panel() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.text("Accounts", style={
                "font_size": "16px", "font_weight": "700", "color": TEXT,
            }),
            rx.spacer(),
            rx.box(
                "+ Add Account",
                on_click=AppState.open_add_account,
                style={
                    "font_size": "11px", "letter_spacing": "0.08em",
                    "text_transform": "uppercase", "padding": "7px 14px",
                    "border_radius": "8px", "border": f"1px dashed {ACCENT}55",
                    "color": ACCENT, "cursor": "pointer", "font_family": MONO,
                    "_hover": {"background": f"{ACCENT}0d"},
                },
            ),
            align_items="center", width="100%", margin_bottom="16px",
        ),

        # Summary
        _summary_bar(),

        # Account list
        rx.cond(
            AppState.accounts_rows.length() == 0,
            rx.text("No accounts yet. Add one above.",
                    style={"font_size": "13px", "color": TEXT3, "font_family": MONO,
                           "padding": "20px 0"}),
            rx.foreach(
                AppState.accounts_rows.to(list[dict[str, Any]]),
                _acct_card,
            ),
        ),

        # Dialogs
        _add_account_dialog(),
        _account_settings_dialog(),
        _debt_payment_dialog(),

        gap="0px", align_items="stretch", width="100%",
    )
