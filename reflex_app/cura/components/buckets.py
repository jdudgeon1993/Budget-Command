"""Buckets panel — zero-based budgeting view with inline editing."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, VIOLET, MONO, SANS)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _input_style() -> dict:
    return {
        "background": BG3, "border": f"1px solid {BORDER}",
        "border_radius": "8px", "color": TEXT, "font_family": MONO,
        "font_size": "12px", "padding": "8px 12px", "outline": "none", "width": "100%",
        "_focus": {"border_color": ACCENT, "outline": "none"},
    }


def _select_style() -> dict:
    return {
        "background": BG3, "border": f"1px solid {BORDER}",
        "border_radius": "8px", "color": TEXT,
        "font_size": "12px", "padding": "8px 10px", "width": "100%",
    }


def _field(label: str, child: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, style={
            "font_size": "9px", "color": TEXT3, "letter_spacing": "0.1em",
            "text_transform": "uppercase", "font_family": MONO,
        }),
        child,
        gap="4px", align_items="stretch", width="100%",
    )


# ── RTS Hero card ─────────────────────────────────────────────────────────────

def _rts_hero() -> rx.Component:
    border = rx.cond(
        AppState.rts_negative, f"1px solid {RED}55",
        rx.cond(AppState.rts_zero, f"1px solid {GREEN}55", f"1px solid {BORDER}"),
    )
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("READY TO SPEND", style={
                        "font_size": "8px", "letter_spacing": "0.16em",
                        "color": TEXT3, "font_family": MONO,
                    }),
                    rx.text(AppState.rts_fmt, style={
                        "font_size": "30px", "font_weight": "700",
                        "font_family": MONO, "color": AppState.rts_color,
                        "line_height": "1.05",
                    }),
                    rx.text(AppState.rts_sub, style={"font_size": "11px", "color": TEXT3}),
                    align_items="flex-start", gap="3px",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.hstack(
                        rx.text("Income",
                                style={"font_size": "9px", "color": TEXT3, "min_width": "44px"}),
                        rx.text(AppState.income_fmt,
                                style={"font_size": "12px", "color": GREEN, "font_family": MONO}),
                        justify="between", width="100%",
                    ),
                    rx.hstack(
                        rx.text("Spent",
                                style={"font_size": "9px", "color": TEXT3, "min_width": "44px"}),
                        rx.text(AppState.spent_fmt,
                                style={"font_size": "12px", "color": AMBER, "font_family": MONO}),
                        justify="between", width="100%",
                    ),
                    rx.hstack(
                        rx.text("Alloc'd",
                                style={"font_size": "9px", "color": TEXT3, "min_width": "44px"}),
                        rx.text(AppState.alloc_fmt,
                                style={"font_size": "12px", "color": ACCENT, "font_family": MONO}),
                        justify="between", width="100%",
                    ),
                    gap="5px", min_width="130px",
                ),
                align_items="flex-start", width="100%",
            ),
            # Allocation progress bar
            rx.vstack(
                rx.box(
                    rx.box(
                        class_name="prog-fill",
                        style={
                            "height": "100%", "border_radius": "3px",
                            "background": rx.cond(
                                AppState.total_alloc_val > AppState.income_total, RED, ACCENT),
                            "width": f"{AppState.alloc_pct}%",
                        },
                    ),
                    style={"height": "6px", "border_radius": "3px", "background": BG3,
                           "overflow": "hidden", "width": "100%"},
                ),
                rx.hstack(
                    rx.text(AppState.alloc_fmt, " of ", AppState.income_fmt, " allocated",
                            style={"font_size": "10px", "color": TEXT3}),
                    rx.spacer(),
                    rx.text(f"{AppState.alloc_pct}%",
                            style={"font_size": "10px", "color": TEXT3, "font_family": MONO}),
                    width="100%",
                ),
                gap="4px", width="100%",
            ),
            gap="14px", width="100%",
        ),
        style={
            "background": BG2, "border": border,
            "border_radius": "12px", "padding": "16px 18px", "margin_bottom": "14px",
        },
    )


# ── Bucket settings dialog ────────────────────────────────────────────────────

def _toggle_row(label: str, sub: str, checked, on_change) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(label, style={"font_size": "12px", "color": TEXT}),
            rx.text(sub, style={"font_size": "10px", "color": TEXT3}),
            gap="1px", align_items="flex-start",
        ),
        rx.spacer(),
        rx.switch(checked=checked, on_change=on_change, color_scheme="indigo"),
        align_items="center", width="100%",
    )


def _expense_fields() -> rx.Component:
    """Fields specific to expense-type buckets."""
    return rx.fragment(
        _field("Monthly Budget Target ($)",
            rx.input(value=AppState.bsf_budget, on_change=AppState.set_bsf_budget,
                     type="number", input_mode="decimal", placeholder="0",
                     style=_input_style())
        ),
        rx.hstack(
            _field("Due Day",
                rx.input(value=AppState.bsf_due_day, on_change=AppState.set_bsf_due_day,
                         placeholder="e.g. 15 or eom", style=_input_style())
            ),
            _field("Due Amount ($)",
                rx.input(value=AppState.bsf_due_amount, on_change=AppState.set_bsf_due_amount,
                         type="number", input_mode="decimal", placeholder="exact $ due",
                         style=_input_style())
            ),
            gap="10px", width="100%",
        ),
        _field("Pay Frequency",
            rx.el.select(
                rx.el.option("— None —", value=""),
                rx.el.option("Monthly", value="monthly"),
                rx.el.option("Weekly", value="weekly"),
                rx.el.option("Biweekly", value="biweekly"),
                rx.el.option("Triweekly", value="triweekly"),
                value=AppState.bsf_pay_freq, on_change=AppState.set_bsf_pay_freq,
                style=_select_style(),
            )
        ),
        _toggle_row("Recurring bill", "Auto-show in forecast",
                    AppState.bsf_recurring, AppState.set_bsf_recurring),
        _toggle_row("Roll over unspent balance", "Surplus carries to next month",
                    AppState.bsf_rollover, AppState.set_bsf_rollover),
    )


def _sinking_goal_fields() -> rx.Component:
    """Fields specific to sinking fund / goal buckets."""
    return rx.fragment(
        _field("Monthly Contribution ($)",
            rx.input(value=AppState.bsf_budget, on_change=AppState.set_bsf_budget,
                     type="number", input_mode="decimal", placeholder="0",
                     style=_input_style())
        ),
        rx.hstack(
            _field("Target Amount ($)",
                rx.input(value=AppState.bsf_target_amount,
                         on_change=AppState.set_bsf_target_amount,
                         type="number", input_mode="decimal", placeholder="e.g. 5000",
                         style=_input_style())
            ),
            _field("Target Date (YYYY-MM)",
                rx.input(value=AppState.bsf_target_date,
                         on_change=AppState.set_bsf_target_date,
                         type="month", placeholder="YYYY-MM",
                         style=_input_style())
            ),
            gap="10px", width="100%",
        ),
        _field("Contribution Frequency",
            rx.el.select(
                rx.el.option("— None —", value=""),
                rx.el.option("Monthly", value="monthly"),
                rx.el.option("Biweekly", value="biweekly"),
                rx.el.option("Weekly", value="weekly"),
                value=AppState.bsf_contrib_freq, on_change=AppState.set_bsf_contrib_freq,
                style=_select_style(),
            )
        ),
        _toggle_row("Roll over balance", "Accumulates month to month (recommended)",
                    AppState.bsf_rollover, AppState.set_bsf_rollover),
    )


def _vault_fields() -> rx.Component:
    """Fields specific to vault-type buckets."""
    return rx.fragment(
        # Accumulated balance display
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("VAULT BALANCE", style={
                        "font_size": "8px", "letter_spacing": "0.14em",
                        "color": TEXT3, "font_family": MONO,
                    }),
                    rx.text(AppState.bsf_vault_total_fmt, style={
                        "font_size": "22px", "font_weight": "700",
                        "font_family": MONO, "color": VIOLET,
                    }),
                    gap="2px", align_items="flex-start",
                ),
                rx.text("Total saved across all months",
                        style={"font_size": "10px", "color": TEXT3}),
                justify="between", width="100%", align_items="center",
            ),
            style={
                "background": f"{VIOLET}0d", "border": f"1px solid {VIOLET}33",
                "border_radius": "8px", "padding": "12px 14px",
            },
        ),

        rx.divider(style={"border_color": BORDER}),

        # Transfer to bucket
        rx.vstack(
            rx.text("Transfer to Bucket", style={
                "font_size": "10px", "color": TEXT3, "letter_spacing": "0.1em",
                "text_transform": "uppercase", "font_family": MONO,
            }),
            rx.text("Move allocation to another bucket (net RTS = 0)",
                    style={"font_size": "10px", "color": TEXT3}),
            rx.hstack(
                rx.el.select(
                    rx.el.option("— Select bucket —", value=""),
                    AppState.expense_buckets.to(list[dict[str, Any]]).foreach(
                        lambda b: rx.el.option(b["name"], value=b["id"])
                    ),
                    value=AppState.bsf_transfer_bid,
                    on_change=AppState.set_bsf_transfer_bid,
                    style={**_select_style(), "flex": "2"},
                ),
                rx.input(
                    value=AppState.bsf_transfer_amt,
                    on_change=AppState.set_bsf_transfer_amt,
                    type="number", input_mode="decimal", placeholder="$",
                    style={**_input_style(), "flex": "1"},
                ),
                rx.box(
                    "Transfer",
                    on_click=AppState.vault_transfer,
                    style={
                        "padding": "8px 12px", "border_radius": "8px",
                        "background": ACCENT, "color": "#fff",
                        "font_size": "11px", "cursor": "pointer",
                        "font_family": MONO, "white_space": "nowrap",
                        "flex_shrink": "0", "_hover": {"opacity": "0.85"},
                    },
                ),
                gap="8px", width="100%", align_items="center",
            ),
            gap="6px", align_items="stretch", width="100%",
        ),

        rx.divider(style={"border_color": BORDER}),

        # Release to pool
        rx.vstack(
            rx.text("Release to Pool", style={
                "font_size": "10px", "color": TEXT3, "letter_spacing": "0.1em",
                "text_transform": "uppercase", "font_family": MONO,
            }),
            rx.text("Return savings to RTS (frees up cash)",
                    style={"font_size": "10px", "color": TEXT3}),
            rx.hstack(
                rx.input(
                    value=AppState.bsf_release_amt,
                    on_change=AppState.set_bsf_release_amt,
                    type="number", input_mode="decimal",
                    placeholder="$ amount to release",
                    style={**_input_style(), "flex": "1"},
                ),
                rx.box(
                    "Release",
                    on_click=AppState.vault_release_pool,
                    style={
                        "padding": "8px 12px", "border_radius": "8px",
                        "border": f"1px solid {RED}44", "color": RED,
                        "font_size": "11px", "cursor": "pointer",
                        "font_family": MONO, "white_space": "nowrap",
                        "flex_shrink": "0",
                        "_hover": {"background": f"{RED}11"},
                    },
                ),
                gap="8px", width="100%", align_items="center",
            ),
            gap="6px", align_items="stretch", width="100%",
        ),

        # Monthly contribution field (how much to allocate each month)
        _field("Monthly Contribution ($)",
            rx.input(value=AppState.bsf_budget, on_change=AppState.set_bsf_budget,
                     type="number", input_mode="decimal", placeholder="0",
                     style=_input_style())
        ),
    )


def bucket_settings_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text("Bucket Settings", style={
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

                # Always: name + type + category
                _field("Bucket Name",
                    rx.input(value=AppState.bsf_name, on_change=AppState.set_bsf_name,
                             style=_input_style())
                ),

                rx.hstack(
                    _field("Type",
                        rx.el.select(
                            rx.el.option("Expense", value="expense"),
                            rx.el.option("Sinking Fund", value="sinking"),
                            rx.el.option("Goal", value="goal"),
                            rx.el.option("Vault (internal savings)", value="vault"),
                            value=AppState.bsf_type, on_change=AppState.set_bsf_type,
                            style=_select_style(),
                        )
                    ),
                    _field("Category",
                        rx.el.select(
                            AppState.cat_options.to(list[dict[str, Any]]).foreach(
                                lambda c: rx.el.option(c["name"], value=c["id"])
                            ),
                            value=AppState.bsf_cat_id, on_change=AppState.set_bsf_cat_id,
                            style=_select_style(),
                        )
                    ),
                    gap="10px", width="100%",
                ),

                # Type-aware field groups
                rx.match(
                    AppState.bsf_type,
                    ("expense",  _expense_fields()),
                    ("sinking",  _sinking_goal_fields()),
                    ("goal",     _sinking_goal_fields()),
                    ("vault",    _vault_fields()),
                    _expense_fields(),   # fallback
                ),

                # Notes — always shown
                _field("Notes",
                    rx.text_area(
                        value=AppState.bsf_notes, on_change=AppState.set_bsf_notes,
                        placeholder="Optional notes…", rows="2",
                        style={**_input_style(), "resize": "none", "font_family": SANS},
                    )
                ),

                # Skip this month — shown for non-vault
                rx.cond(
                    AppState.bsf_type != "vault",
                    _toggle_row("Skip this month",
                                "Exclude from budget calculations for this month",
                                AppState.bsf_skip, AppState.set_bsf_skip),
                    rx.box(),
                ),

                rx.cond(
                    AppState.bsf_error != "",
                    rx.text(AppState.bsf_error,
                            style={"color": RED, "font_size": "11px", "font_family": MONO}),
                    rx.box(),
                ),

                rx.divider(style={"border_color": BORDER}),

                rx.hstack(
                    rx.box(
                        "Archive",
                        on_click=AppState.archive_bucket_confirm(AppState.bsettings_bid),
                        style={
                            "flex": "1", "padding": "9px", "border_radius": "8px",
                            "border": f"1px solid {RED}44", "color": RED,
                            "font_size": "11px", "text_align": "center",
                            "cursor": "pointer", "font_family": MONO,
                            "letter_spacing": "0.06em",
                            "_hover": {"background": f"{RED}11"},
                        },
                    ),
                    rx.box(
                        rx.cond(AppState.bsf_saving, "Saving…", "Save"),
                        on_click=AppState.save_bucket_settings,
                        style={
                            "flex": "2", "padding": "9px", "border_radius": "8px",
                            "background": rx.cond(AppState.bsf_saving, BORDER, ACCENT),
                            "color": "#fff", "font_size": "11px",
                            "text_align": "center", "cursor": "pointer",
                            "font_family": MONO, "letter_spacing": "0.08em",
                            "text_transform": "uppercase", "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", width="100%",
                ),

                gap="12px", width="100%",
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "14px", "padding": "22px",
                "max_width": "480px", "width": "95vw",
                "max_height": "90vh", "overflow_y": "auto",
            },
        ),
        open=AppState.bsettings_open,
        on_open_change=AppState.set_bsettings_open,
    )


# ── Inline allocation cell ────────────────────────────────────────────────────

def _alloc_cell(row: dict) -> rx.Component:
    is_editing = AppState.editing_bid == row["id"]
    return rx.cond(
        is_editing,
        rx.hstack(
            rx.input(
                value=AppState.edit_alloc_val,
                on_change=AppState.set_edit_alloc_val,
                on_blur=AppState.save_alloc_edit,
                on_key_down=AppState.handle_alloc_key,
                auto_focus=True,
                type="number",
                input_mode="decimal",
                style={
                    "width": "80px", "background": BG3,
                    "border": f"1px solid {ACCENT}",
                    "border_radius": "6px", "color": TEXT,
                    "font_family": MONO, "font_size": "12px",
                    "padding": "3px 8px", "outline": "none",
                    "text_align": "right",
                    "_focus": {"border_color": ACCENT},
                },
            ),
            rx.box("✓", on_click=AppState.save_alloc_edit, style={
                "font_size": "13px", "color": GREEN, "cursor": "pointer",
                "padding": "2px 3px", "line_height": "1",
                "_hover": {"opacity": "0.7"},
            }),
            rx.box("✗", on_click=AppState.cancel_alloc_edit, style={
                "font_size": "13px", "color": TEXT3, "cursor": "pointer",
                "padding": "2px 3px", "line_height": "1",
                "_hover": {"color": RED},
            }),
            align_items="center", gap="3px",
        ),
        rx.text(
            row["alloc_fmt"],
            on_click=AppState.start_edit_alloc(row["id"], row["alloc_fmt"]),
            style={
                "font_size": "12px", "font_family": MONO, "color": TEXT2,
                "cursor": "text",
                "border_bottom": f"1px dashed {BORDER2}",
                "padding_bottom": "1px",
                "_hover": {"color": ACCENT, "border_bottom_color": ACCENT},
            },
        ),
    )


# ── Bucket row ────────────────────────────────────────────────────────────────

def _bucket_row(row: dict) -> rx.Component:
    return rx.cond(
        row["row_type"] == "header",

        rx.text(
            row["name"],
            style={
                "font_size": "9px", "letter_spacing": "0.14em",
                "text_transform": "uppercase", "color": TEXT3,
                "padding": "14px 2px 5px", "font_family": MONO,
            },
        ),

        rx.box(
            # Top — name + badge + available
            rx.hstack(
                rx.vstack(
                    rx.text(row["name"], style={
                        "font_size": "13px", "color": TEXT,
                        "font_weight": "600", "line_height": "1.2",
                    }),
                    rx.hstack(
                        rx.text(row["budget_fmt"],
                                style={"font_size": "10px", "color": TEXT3}),
                        rx.text(" target · ",
                                style={"font_size": "10px", "color": TEXT3}),
                        rx.text(row["spent_fmt"],
                                style={"font_size": "10px", "color": TEXT3}),
                        rx.text(" spent",
                                style={"font_size": "10px", "color": TEXT3}),
                        gap="0px", align_items="center",
                    ),
                    gap="2px", align_items="flex-start", flex="1", min_width="0",
                ),
                rx.cond(
                    row["status"] != "",
                    rx.text(row["status"], style={
                        "font_family": MONO, "font_size": "9px",
                        "letter_spacing": "0.07em", "text_transform": "uppercase",
                        "padding": "2px 7px", "border_radius": "10px",
                        "white_space": "nowrap",
                        "color": row["avail_color"],
                        "background": row["avail_bg"],
                        "border": row["avail_border"],
                    }),
                    rx.box(),
                ),
                rx.text(row["avail_fmt"], style={
                    "font_size": "16px", "font_weight": "700", "font_family": MONO,
                    "color": row["avail_color"], "white_space": "nowrap",
                }),
                align_items="center", width="100%", gap="8px",
            ),

            # Middle — alloc edit + fill + settings
            rx.hstack(
                rx.text("Alloc:", style={
                    "font_size": "10px", "color": TEXT3, "flex_shrink": "0",
                }),
                _alloc_cell(row),
                rx.spacer(),
                rx.cond(
                    row["show_fill"],
                    rx.box(
                        "Fill",
                        on_click=AppState.fill_bucket(row["id"], row["budget"]),
                        style={
                            "font_family": MONO, "font_size": "9px",
                            "letter_spacing": "0.06em", "text_transform": "uppercase",
                            "padding": "3px 9px", "border_radius": "10px",
                            "border": f"1px dashed {BORDER2}",
                            "color": TEXT3, "cursor": "pointer",
                            "_hover": {"border_color": ACCENT, "color": ACCENT},
                        },
                    ),
                    rx.box(),
                ),
                rx.box(
                    "⋯",
                    on_click=AppState.open_bucket_settings(row["id"]),
                    style={
                        "font_size": "18px", "color": TEXT3, "cursor": "pointer",
                        "padding": "0px 6px", "border_radius": "6px", "line_height": "1.2",
                        "_hover": {"color": TEXT, "background": BG3},
                    },
                ),
                align_items="center", width="100%", gap="6px",
                style={"margin_top": "8px"},
            ),

            # Progress bar
            rx.box(
                rx.box(
                    class_name="prog-fill",
                    style={
                        "height": "100%", "border_radius": "2px",
                        "background": row["bar_color"],
                        "width": row["pct_str"],
                    },
                ),
                style={
                    "height": row["prog_h"], "background": BG3,
                    "border_radius": "2px", "overflow": "hidden",
                    "margin_top": "8px",
                },
            ),

            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "padding": "10px 12px",
                "margin_bottom": "5px",
                "_hover": {"border_color": BORDER2},
            },
        ),
    )


# ── Add bucket strip ──────────────────────────────────────────────────────────

def _add_bucket_strip() -> rx.Component:
    return rx.hstack(
        rx.input(
            placeholder="New bucket name…",
            value=AppState.add_bkt_name,
            on_change=AppState.set_add_bkt_name,
            style={
                "flex": "2", "min_width": "0",
                "background": BG3, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "color": TEXT, "font_family": MONO,
                "font_size": "12px", "padding": "8px 12px", "outline": "none",
                "_focus": {"border_color": ACCENT},
                "_placeholder": {"color": TEXT3},
            },
        ),
        rx.el.select(
            rx.el.option("— Category —", value=""),
            AppState.cat_options.to(list[dict[str, Any]]).foreach(
                lambda c: rx.el.option(c["name"], value=c["id"])
            ),
            value=AppState.add_bkt_cat_id,
            on_change=AppState.set_add_bkt_cat_id,
            style={
                "flex": "1", "min_width": "80px",
                "background": BG3, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "color": TEXT3,
                "font_size": "12px", "padding": "8px 8px",
            },
        ),
        rx.box(
            rx.cond(AppState.add_bkt_saving, "…", "+ Add"),
            on_click=AppState.add_bucket_submit,
            style={
                "padding": "8px 14px", "border_radius": "8px",
                "background": rx.cond(AppState.add_bkt_saving, BORDER, ACCENT),
                "color": "#fff", "font_size": "11px", "cursor": "pointer",
                "font_family": MONO, "letter_spacing": "0.06em",
                "white_space": "nowrap", "flex_shrink": "0",
                "_hover": {"opacity": "0.9"},
            },
        ),
        gap="8px", width="100%", align_items="center",
        style={
            "border": f"1px dashed {BORDER2}",
            "border_radius": "8px", "padding": "10px 12px",
            "margin_top": "6px",
        },
    )


# ── Main panel ────────────────────────────────────────────────────────────────

def buckets_panel() -> rx.Component:
    return rx.box(
        _rts_hero(),
        rx.foreach(AppState.bucket_rows.to(list[dict[str, Any]]), _bucket_row),
        _add_bucket_strip(),
        bucket_settings_dialog(),
        style={"padding": "0"},
    )
