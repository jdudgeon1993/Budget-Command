"""Buckets panel — zero-based budgeting view (allocation-first design)."""

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


# ── RTS Hero (ZBB-first) ──────────────────────────────────────────────────────

def _rts_hero() -> rx.Component:
    border = rx.cond(
        AppState.rts_negative, f"1px solid {RED}55",
        rx.cond(AppState.rts_zero, f"1px solid {GREEN}55", f"1px solid {BORDER}"),
    )
    return rx.box(
        rx.vstack(
            # Label row + Distribute CTA
            rx.hstack(
                rx.text("READY TO ASSIGN", style={
                    "font_size": "11px", "letter_spacing": "0.18em",
                    "color": TEXT3, "font_family": MONO,
                }),
                rx.spacer(),
                rx.cond(
                    AppState.distribute_visible,
                    rx.box(
                        "Distribute",
                        on_click=AppState.distribute_rts,
                        style={
                            "padding": "6px 16px", "border_radius": "20px",
                            "background": ACCENT, "color": "#fff",
                            "font_size": "12px", "font_family": MONO,
                            "letter_spacing": "0.08em", "cursor": "pointer",
                            "font_weight": "600",
                            "_hover": {"opacity": "0.85"},
                            "_active": {"transform": "scale(0.97)"},
                        },
                    ),
                    rx.box(),
                ),
                align_items="center", width="100%",
            ),

            # Big amount
            rx.text(AppState.rts_fmt, style={
                "font_size": "40px", "font_weight": "800",
                "font_family": MONO, "color": AppState.rts_color,
                "line_height": "1", "letter_spacing": "-0.02em",
            }),

            # Subtitle / urgency message
            rx.text(AppState.rts_sub, style={
                "font_size": "13px", "color": TEXT3, "line_height": "1.4",
            }),

            # Thin allocation progress bar
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
                style={"height": "5px", "border_radius": "3px", "background": BG3,
                       "overflow": "hidden", "width": "100%"},
            ),

            # KPI trio
            rx.hstack(
                rx.hstack(
                    rx.box(style={
                        "width": "7px", "height": "7px", "border_radius": "50%",
                        "background": GREEN, "flex_shrink": "0",
                    }),
                    rx.text("Income", style={"font_size": "12px", "color": TEXT3}),
                    rx.text(AppState.income_fmt, style={
                        "font_size": "13px", "color": GREEN,
                        "font_family": MONO, "font_weight": "600",
                    }),
                    align_items="center", gap="5px",
                ),
                rx.hstack(
                    rx.box(style={
                        "width": "7px", "height": "7px", "border_radius": "50%",
                        "background": ACCENT, "flex_shrink": "0",
                    }),
                    rx.text("Alloc'd", style={"font_size": "12px", "color": TEXT3}),
                    rx.text(AppState.alloc_fmt, style={
                        "font_size": "13px", "color": ACCENT,
                        "font_family": MONO, "font_weight": "600",
                    }),
                    align_items="center", gap="5px",
                ),
                rx.hstack(
                    rx.box(style={
                        "width": "7px", "height": "7px", "border_radius": "50%",
                        "background": AMBER, "flex_shrink": "0",
                    }),
                    rx.text("Spent", style={"font_size": "12px", "color": TEXT3}),
                    rx.text(AppState.spent_fmt, style={
                        "font_size": "13px", "color": AMBER,
                        "font_family": MONO, "font_weight": "600",
                    }),
                    align_items="center", gap="5px",
                ),
                gap="16px", width="100%", flex_wrap="wrap",
            ),

            gap="12px", width="100%",
        ),
        style={
            "background": BG2, "border": border,
            "border_radius": "12px", "padding": "18px 20px", "margin_bottom": "14px",
        },
    )


# ── Needs-attention row (scoreboard right panel) ──────────────────────────────

def _attention_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.text(row["name"], style={
            "font_size": "14px", "color": TEXT, "flex": "1",
            "min_width": "0", "overflow": "hidden",
            "text_overflow": "ellipsis", "white_space": "nowrap",
            "font_weight": "600",
        }),
        rx.text(row["label"], style={
            "font_size": "13px", "font_family": MONO, "white_space": "nowrap",
            "flex_shrink": "0",
            "color": rx.cond(row["is_over"] == "1", RED, AMBER),
        }),
        rx.cond(
            row["is_over"] != "1",
            rx.box(
                "Fill",
                on_click=AppState.fill_bucket(row["id"], row["budget"]),
                style={
                    "font_family": MONO, "font_size": "12px",
                    "padding": "4px 12px", "border_radius": "6px",
                    "border": f"1px solid {ACCENT}55", "color": ACCENT,
                    "cursor": "pointer", "flex_shrink": "0",
                    "_hover": {"background": f"{ACCENT}11"},
                },
            ),
            rx.box(),
        ),
        align_items="center", gap="10px", width="100%",
        style={
            "padding": "9px 12px", "border_radius": "8px",
            "background": rx.cond(
                row["is_over"] == "1", f"{RED}0d", f"{AMBER}0a",
            ),
            "border": rx.cond(
                row["is_over"] == "1",
                f"1px solid {RED}33", f"1px solid {AMBER}22",
            ),
            "margin_bottom": "6px",
        },
    )


# ── Category progress bar (scoreboard right panel) ───────────────────────────

def _cat_bar(row: dict) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.box(style={
                    "width": "9px", "height": "9px", "border_radius": "50%",
                    "background": row["color"], "flex_shrink": "0",
                }),
                rx.text(row["name"], style={
                    "font_size": "13px", "color": TEXT, "font_weight": "600",
                }),
                gap="7px", align_items="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.cond(
                    row["budget_fmt"] != "",
                    rx.text(row["alloc_fmt"], " / ", row["budget_fmt"], style={
                        "font_size": "12px", "font_family": MONO, "color": TEXT3,
                    }),
                    rx.text(row["alloc_fmt"], style={
                        "font_size": "12px", "font_family": MONO, "color": TEXT3,
                    }),
                ),
                rx.text(row["pct_str"], style={
                    "font_size": "12px", "font_family": MONO, "font_weight": "700",
                    "color": rx.cond(row["is_funded"] == "1", GREEN, AMBER),
                }),
                gap="8px", align_items="center",
            ),
            align_items="center", width="100%",
        ),
        rx.box(
            rx.box(
                style={
                    "height": "100%", "border_radius": "3px",
                    "background": rx.cond(row["is_funded"] == "1", GREEN, ACCENT),
                    "width": row["pct_str"],
                    "transition": "width 0.35s ease",
                },
            ),
            style={
                "height": "5px", "border_radius": "3px",
                "background": BG3, "overflow": "hidden", "width": "100%",
            },
        ),
        gap="6px", width="100%",
        style={"margin_bottom": "12px"},
    )


# ── Month scoreboard (right column) ──────────────────────────────────────────

def _scoreboard() -> rx.Component:
    return rx.vstack(
        _rts_hero(),

        # Needs Attention card
        rx.box(
            rx.hstack(
                rx.text("NEEDS ATTENTION", style={
                    "font_size": "11px", "letter_spacing": "0.14em",
                    "text_transform": "uppercase", "color": TEXT3,
                    "font_family": MONO, "font_weight": "600",
                }),
                rx.cond(
                    AppState.attention_rows.length() > 0,
                    rx.box(
                        AppState.attention_rows.length(),
                        style={
                            "background": f"{RED}22", "color": RED,
                            "border_radius": "10px", "padding": "1px 9px",
                            "font_size": "12px", "font_family": MONO, "font_weight": "700",
                        },
                    ),
                    rx.box(
                        "✓",
                        style={
                            "background": f"{GREEN}22", "color": GREEN,
                            "border_radius": "10px", "padding": "1px 9px",
                            "font_size": "12px",
                        },
                    ),
                ),
                align_items="center", gap="8px",
                style={"margin_bottom": "12px"},
            ),
            rx.cond(
                AppState.attention_rows.length() > 0,
                rx.foreach(
                    AppState.attention_rows.to(list[dict[str, Any]]),
                    _attention_row,
                ),
                rx.hstack(
                    rx.text("All buckets funded for this month", style={
                        "font_size": "14px", "color": TEXT2,
                    }),
                    align_items="center",
                    style={"padding": "4px 0 8px"},
                ),
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "12px", "padding": "16px 18px",
                "margin_bottom": "14px", "width": "100%",
            },
        ),

        # Category rollup card
        rx.cond(
            AppState.cat_rollup_rows.length() > 0,
            rx.box(
                rx.text("CATEGORIES", style={
                    "font_size": "11px", "letter_spacing": "0.14em",
                    "text_transform": "uppercase", "color": TEXT3,
                    "font_family": MONO, "font_weight": "600",
                    "display": "block", "margin_bottom": "14px",
                }),
                rx.foreach(
                    AppState.cat_rollup_rows.to(list[dict[str, Any]]),
                    _cat_bar,
                ),
                style={
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "12px", "padding": "16px 18px",
                    "width": "100%",
                },
            ),
            rx.box(),
        ),

        gap="0", width="100%", align_items="stretch",
    )


# ── Bucket settings dialog ────────────────────────────────────────────────────

def _toggle_row(label: str, sub: str, checked, on_change) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(label, style={"font_size": "13px", "color": TEXT}),
            rx.text(sub, style={"font_size": "11px", "color": TEXT3}),
            gap="1px", align_items="flex-start",
        ),
        rx.spacer(),
        rx.switch(checked=checked, on_change=on_change, color_scheme="indigo"),
        align_items="center", width="100%",
    )


def _expense_fields() -> rx.Component:
    return rx.fragment(
        _field("Default Budget (applies to future months) ($)",
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
    return rx.fragment(
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("VAULT BALANCE", style={
                        "font_size": "11px", "letter_spacing": "0.14em",
                        "color": TEXT3, "font_family": MONO,
                    }),
                    rx.text(AppState.bsf_vault_total_fmt, style={
                        "font_size": "24px", "font_weight": "700",
                        "font_family": MONO, "color": VIOLET,
                    }),
                    gap="2px", align_items="flex-start",
                ),
                rx.text("Total saved across all months",
                        style={"font_size": "11px", "color": TEXT3}),
                justify="between", width="100%", align_items="center",
            ),
            style={
                "background": f"{VIOLET}0d", "border": f"1px solid {VIOLET}33",
                "border_radius": "8px", "padding": "12px 14px",
            },
        ),
        rx.divider(style={"border_color": BORDER}),
        rx.vstack(
            rx.text("Transfer to Bucket", style={
                "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
                "text_transform": "uppercase", "font_family": MONO,
            }),
            rx.text("Move allocation to another bucket (net RTS = 0)",
                    style={"font_size": "11px", "color": TEXT3}),
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
                        "font_size": "12px", "cursor": "pointer",
                        "font_family": MONO, "white_space": "nowrap",
                        "flex_shrink": "0", "_hover": {"opacity": "0.85"},
                    },
                ),
                gap="8px", width="100%", align_items="center",
            ),
            gap="6px", align_items="stretch", width="100%",
        ),
        rx.divider(style={"border_color": BORDER}),
        rx.vstack(
            rx.text("Release to Pool", style={
                "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
                "text_transform": "uppercase", "font_family": MONO,
            }),
            rx.text("Return savings to RTS (frees up cash)",
                    style={"font_size": "11px", "color": TEXT3}),
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
                        "font_size": "12px", "cursor": "pointer",
                        "font_family": MONO, "white_space": "nowrap",
                        "flex_shrink": "0",
                        "_hover": {"background": f"{RED}11"},
                    },
                ),
                gap="8px", width="100%", align_items="center",
            ),
            gap="6px", align_items="stretch", width="100%",
        ),
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
                rx.hstack(
                    rx.text("Bucket Settings", style={
                        "font_size": "12px", "letter_spacing": "0.14em",
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
                rx.match(
                    AppState.bsf_type,
                    ("expense", _expense_fields()),
                    ("sinking", _sinking_goal_fields()),
                    ("goal",    _sinking_goal_fields()),
                    ("vault",   _vault_fields()),
                    _expense_fields(),
                ),
                _field("Notes",
                    rx.text_area(
                        value=AppState.bsf_notes, on_change=AppState.set_bsf_notes,
                        placeholder="Optional notes…", rows="2",
                        style={**_input_style(), "resize": "none", "font_family": SANS},
                    )
                ),
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
                            style={"color": RED, "font_size": "12px", "font_family": MONO}),
                    rx.box(),
                ),
                rx.divider(style={"border_color": BORDER}),
                rx.hstack(
                    rx.box(
                        "Archive",
                        on_click=AppState.archive_bucket_confirm(AppState.bsettings_bid),
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
                        rx.cond(AppState.bsf_saving, "Saving…", "Save"),
                        on_click=AppState.save_bucket_settings,
                        style={
                            "flex": "2", "padding": "10px", "border_radius": "8px",
                            "background": rx.cond(AppState.bsf_saving, BORDER, ACCENT),
                            "color": "#fff", "font_size": "12px",
                            "text_align": "center", "cursor": "pointer",
                            "font_family": MONO, "letter_spacing": "0.08em",
                            "text_transform": "uppercase", "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", width="100%",
                ),
                gap="14px", width="100%",
            ),
            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "14px", "padding": "24px",
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
                    "width": "88px", "background": BG3,
                    "border": f"1px solid {ACCENT}",
                    "border_radius": "6px", "color": TEXT,
                    "font_family": MONO, "font_size": "13px",
                    "padding": "3px 8px", "outline": "none",
                    "text_align": "right",
                    "_focus": {"border_color": ACCENT},
                },
            ),
            rx.box("✓", on_click=AppState.save_alloc_edit, style={
                "font_size": "14px", "color": GREEN, "cursor": "pointer",
                "padding": "2px 3px", "line_height": "1",
                "_hover": {"opacity": "0.7"},
            }),
            rx.box("✗", on_click=AppState.cancel_alloc_edit, style={
                "font_size": "14px", "color": TEXT3, "cursor": "pointer",
                "padding": "2px 3px", "line_height": "1",
                "_hover": {"color": RED},
            }),
            align_items="center", gap="3px",
        ),
        # Display: alloc_fmt — click to edit allocation
        rx.text(
            row["alloc_fmt"],
            on_click=AppState.start_edit_alloc(row["id"], row["alloc_fmt"]),
            style={
                "font_size": "15px", "font_family": MONO,
                "font_weight": "700", "color": ACCENT,
                "cursor": "text", "line_height": "1.2",
                "_hover": {"opacity": "0.75"},
            },
        ),
    )


def _budget_cell(row: dict) -> rx.Component:
    """Inline editable budget target for the current month."""
    is_editing = AppState.editing_budget_bid == row["id"]
    return rx.cond(
        is_editing,
        rx.hstack(
            rx.input(
                value=AppState.edit_budget_val,
                on_change=AppState.set_edit_budget_val,
                on_blur=AppState.save_budget_edit,
                on_key_down=AppState.handle_budget_key,
                auto_focus=True,
                type="number",
                input_mode="decimal",
                style={
                    "width": "88px", "background": BG3,
                    "border": f"1px solid {ACCENT}",
                    "border_radius": "6px", "color": TEXT,
                    "font_family": MONO, "font_size": "13px",
                    "padding": "3px 8px", "outline": "none",
                    "text_align": "right",
                    "_focus": {"border_color": ACCENT},
                },
            ),
            rx.box("✓", on_click=AppState.save_budget_edit, style={
                "font_size": "14px", "color": GREEN, "cursor": "pointer",
                "padding": "2px 3px", "line_height": "1",
                "_hover": {"opacity": "0.7"},
            }),
            rx.box("✗", on_click=AppState.cancel_budget_edit, style={
                "font_size": "14px", "color": TEXT3, "cursor": "pointer",
                "padding": "2px 3px", "line_height": "1",
                "_hover": {"color": RED},
            }),
            align_items="center", gap="3px",
        ),
        # Display: budget_fmt or "—" — click to edit monthly budget
        rx.text(
            rx.cond(row["budget_fmt"] != "", row["budget_fmt"], "—"),
            on_click=AppState.start_edit_budget(row["id"], row["budget_fmt"]),
            style={
                "font_size": "14px", "font_family": MONO,
                "font_weight": "600", "color": TEXT2,
                "cursor": "text", "line_height": "1.2",
                "_hover": {"opacity": "0.75"},
            },
        ),
    )


# ── Bucket row (header + bucket in one flat foreach) ─────────────────────────

def _bucket_row(row: dict) -> rx.Component:
    return rx.cond(
        row["row_type"] == "header",

        # ── Category header ──────────────────────────────────────────────────
        rx.hstack(
            rx.box(style={
                "width": "3px", "align_self": "stretch",
                "border_radius": "2px", "background": row["color"],
                "flex_shrink": "0", "min_height": "16px",
            }),
            rx.text(row["name"], style={
                "font_size": "11px", "letter_spacing": "0.12em",
                "text_transform": "uppercase", "color": TEXT2,
                "font_family": MONO, "font_weight": "600", "flex": "1",
            }),
            rx.cond(
                row["budget_h_fmt"] != "",
                rx.hstack(
                    rx.text(row["cat_alloc_fmt"], style={
                        "font_size": "11px", "font_family": MONO,
                        "color": rx.cond(row["is_cat_funded"] == "1", GREEN, AMBER),
                        "font_weight": "700",
                    }),
                    rx.text(" / ", row["budget_h_fmt"], style={
                        "font_size": "11px", "font_family": MONO, "color": TEXT3,
                    }),
                    align_items="baseline", gap="0px",
                ),
                rx.box(),
            ),
            align_items="center",
            style={"padding": "14px 2px 5px", "gap": "8px", "width": "100%"},
        ),

        # ── Bucket card ──────────────────────────────────────────────────────
        rx.box(

            # ── Main row: order buttons · name · alloc / budget · spent · left · status · actions ──
            rx.hstack(
                # ▲/▼ reorder buttons (hidden on mobile via .bkt-reorder CSS class)
                rx.vstack(
                    rx.box("▲",
                        on_click=AppState.move_bucket_up(row["id"]),
                        style={
                            "font_size": "9px", "color": TEXT3, "cursor": "pointer",
                            "line_height": "1", "padding": "1px 3px",
                            "_hover": {"color": ACCENT},
                        },
                    ),
                    rx.box("▼",
                        on_click=AppState.move_bucket_down(row["id"]),
                        style={
                            "font_size": "9px", "color": TEXT3, "cursor": "pointer",
                            "line_height": "1", "padding": "1px 3px",
                            "_hover": {"color": ACCENT},
                        },
                    ),
                    gap="0px", align_items="center", flex_shrink="0",
                    class_name="bkt-reorder",
                ),
                # Name — shrinks on mobile via .bkt-name CSS class
                rx.text(row["name"], style={
                    "font_size": "15px", "font_weight": "600",
                    "color": rx.cond(row["is_skipped"] == "1", TEXT3, TEXT),
                    "min_width": "0", "overflow": "hidden",
                    "text_overflow": "ellipsis", "white_space": "nowrap",
                    "flex_shrink": "0", "max_width": "220px",
                }, class_name="bkt-name"),

                # Numbers: alloc / budget · spent · left
                rx.hstack(
                    _alloc_cell(row),
                    rx.text("/", style={
                        "font_size": "13px", "color": TEXT3,
                        "font_family": MONO, "flex_shrink": "0",
                    }),
                    _budget_cell(row),
                    # Spent + left: hidden on mobile — alloc/budget is what matters
                    rx.hstack(
                        rx.text("·", style={
                            "color": TEXT3, "font_size": "12px",
                            "padding": "0 3px", "flex_shrink": "0",
                        }),
                        rx.text(
                            rx.cond(row["spent_fmt"] != "", row["spent_fmt"], "—"),
                            style={
                                "font_size": "14px", "font_family": MONO,
                                "color": rx.cond(row["is_over"] == "1", RED, TEXT2),
                                "flex_shrink": "0",
                            },
                        ),
                        rx.text("spent", style={
                            "font_size": "11px", "color": TEXT3,
                            "font_family": MONO, "flex_shrink": "0",
                        }),
                        rx.text("·", style={
                            "color": TEXT3, "font_size": "12px",
                            "padding": "0 3px", "flex_shrink": "0",
                        }),
                        rx.text(row["left_avail_fmt"], style={
                            "font_size": "14px", "font_family": MONO,
                            "color": rx.cond(row["is_funded"] == "1", GREEN, TEXT2),
                            "flex_shrink": "0",
                        }),
                        rx.text("left", style={
                            "font_size": "11px", "color": TEXT3,
                            "font_family": MONO, "flex_shrink": "0",
                        }),
                        align_items="baseline", gap="5px",
                        class_name="desktop-only",
                    ),
                    align_items="baseline", gap="5px", flex="1", flex_wrap="wrap",
                ),

                # Status + actions
                rx.hstack(
                    rx.cond(
                        row["status_label"] != "",
                        rx.text(row["status_label"], style={
                            "font_size": "11px", "font_family": MONO,
                            "letter_spacing": "0.06em", "white_space": "nowrap",
                            "font_weight": "600",
                            "color": rx.cond(
                                row["is_over"] == "1", RED,
                                rx.cond(row["is_funded"] == "1", GREEN, AMBER)
                            ),
                        }, class_name="desktop-only"),
                        rx.box(),
                    ),
                    rx.cond(
                        row["show_fill"],
                        rx.box("Fill",
                            on_click=AppState.fill_bucket(row["id"], row["budget"]),
                            style={
                                "font_family": MONO, "font_size": "11px",
                                "padding": "3px 9px", "border_radius": "6px",
                                "border": f"1px solid {ACCENT}55", "color": ACCENT,
                                "cursor": "pointer",
                                "_hover": {"background": f"{ACCENT}11"},
                            },
                        ),
                        rx.box(),
                    ),
                    rx.box(
                        rx.cond(AppState.expanded_bucket_id == row["id"], "▾", "▸"),
                        on_click=AppState.toggle_bucket_expand(row["id"]),
                        style={
                            "font_size": "12px", "color": TEXT3, "cursor": "pointer",
                            "padding": "2px 5px", "border_radius": "4px",
                            "_hover": {"color": TEXT2, "background": BG3},
                        },
                    ),
                    rx.box("⋯",
                        on_click=AppState.open_bucket_settings(row["id"]),
                        style={
                            "font_size": "17px", "color": TEXT3, "cursor": "pointer",
                            "padding": "0px 5px", "border_radius": "4px", "line_height": "1.4",
                            "_hover": {"color": TEXT, "background": BG3},
                        },
                    ),
                    align_items="center", gap="6px", flex_shrink="0",
                ),

                align_items="center", width="100%", gap="12px",
            ),

            # ── Meta row: badges + action hint (only when non-empty) ─────────
            rx.cond(
                (row["due_label"] != "") | (row["show_roll"] == "1") |
                (row["show_goal"] == "1") | (row["show_vault"] == "1") |
                (row["action_hint"] != ""),
                rx.hstack(
                    rx.cond(
                        row["due_label"] != "",
                        rx.text(row["due_label"], style={
                            "font_size": "11px", "font_family": MONO,
                            "padding": "1px 7px", "border_radius": "6px",
                            "color": rx.cond(
                                row["due_urgency"] == "overdue", RED,
                                rx.cond(row["due_urgency"] == "urgent", AMBER, TEXT3)
                            ),
                            "background": rx.cond(
                                row["due_urgency"] == "overdue", f"{RED}18",
                                rx.cond(row["due_urgency"] == "urgent", f"{AMBER}18", f"{BORDER}88")
                            ),
                            "border": rx.cond(
                                row["due_urgency"] == "overdue", f"1px solid {RED}44",
                                rx.cond(row["due_urgency"] == "urgent", f"1px solid {AMBER}55",
                                f"1px solid {BORDER}")
                            ),
                        }),
                        rx.box(),
                    ),
                    rx.cond(
                        row["show_roll"] == "1",
                        rx.text(row["roll_fmt"], style={
                            "font_size": "11px", "font_family": MONO, "color": ACCENT,
                            "padding": "1px 7px", "border_radius": "6px",
                            "background": f"{ACCENT}18", "border": f"1px solid {ACCENT}33",
                        }),
                        rx.box(),
                    ),
                    rx.cond(
                        row["show_goal"] == "1",
                        rx.text(row["target_fmt"], style={
                            "font_size": "11px", "color": TEXT3, "font_family": MONO,
                        }),
                        rx.box(),
                    ),
                    rx.cond(
                        row["show_vault"] == "1",
                        rx.text(row["vault_fmt"], style={
                            "font_size": "11px", "color": VIOLET,
                            "font_family": MONO, "font_weight": "600",
                        }),
                        rx.box(),
                    ),
                    rx.cond(
                        row["action_hint"] != "",
                        rx.text(row["action_hint"], style={
                            "font_size": "11px", "font_family": MONO,
                            "color": rx.cond(row["is_over"] == "1", RED, AMBER),
                        }),
                        rx.box(),
                    ),
                    gap="6px", align_items="center", flex_wrap="wrap",
                    style={"margin_top": "5px"},
                ),
                rx.box(),
            ),

            # ── Inline transaction list ───────────────────────────────────────
            rx.cond(
                AppState.expanded_bucket_id == row["id"],
                rx.box(
                    rx.cond(
                        AppState.expanded_bucket_txs.length() == 0,
                        rx.text("No transactions this month", style={
                            "font_size": "12px", "color": TEXT3, "font_family": MONO,
                        }),
                        rx.foreach(
                            AppState.expanded_bucket_txs.to(list[dict[str, Any]]),
                            lambda tx: rx.hstack(
                                rx.text(tx["date_label"], style={
                                    "font_size": "11px", "color": TEXT3,
                                    "font_family": MONO, "width": "78px", "flex_shrink": "0",
                                }),
                                rx.text(tx["desc"], style={
                                    "font_size": "13px", "color": TEXT2, "flex": "1",
                                    "min_width": "0", "overflow": "hidden",
                                    "text_overflow": "ellipsis", "white_space": "nowrap",
                                }),
                                rx.text(tx["amount_fmt"], style={
                                    "font_size": "13px", "font_family": MONO,
                                    "color": RED, "white_space": "nowrap", "flex_shrink": "0",
                                }),
                                align_items="center", width="100%", gap="10px",
                                style={"padding": "3px 0"},
                            ),
                        ),
                    ),
                    style={
                        "border_top": f"1px solid {BORDER}",
                        "margin_top": "8px", "padding_top": "8px",
                    },
                ),
                rx.box(),
            ),

            style={
                "background": BG2,
                "border": f"1px solid {BORDER}",
                "border_left": rx.cond(
                    row["is_over"] == "1",    f"3px solid {RED}",
                    rx.cond(row["is_funded"] == "1", f"3px solid {GREEN}",
                    rx.cond(row["gap_fmt"] != "",    f"3px solid {AMBER}",
                                                     f"1px solid {BORDER}"))
                ),
                "border_radius": "8px",
                "padding": "11px 14px",
                "margin_bottom": "5px",
                "opacity": rx.cond(row["is_skipped"] == "1", "0.4", "1"),
                "_hover": {"border_color": BORDER2},
            },
        ),
    )


# ── Category color swatches for new category picker ───────────────────────────

_CAT_COLORS = [
    "#818cf8", "#a78bfa", "#f472b6", "#fb923c",
    "#fbbf24", "#34d399", "#38bdf8", "#f87171",
]

def _color_swatch(hex_color: str) -> rx.Component:
    is_selected = AppState.add_bkt_new_cat_color == hex_color
    return rx.box(
        style={
            "width": "22px", "height": "22px", "border_radius": "50%",
            "background": hex_color, "cursor": "pointer", "flex_shrink": "0",
            "border": rx.cond(is_selected, f"2px solid #fff", "2px solid transparent"),
            "box_shadow": rx.cond(is_selected, f"0 0 0 2px {hex_color}", "none"),
            "_hover": {"transform": "scale(1.15)"},
        },
        on_click=AppState.set_add_bkt_new_cat_color(hex_color),
    )


# ── Add bucket strip (category-first, ZBB layout) ────────────────────────────

_INPUT = {
    "background": BG3, "border": f"1px solid {BORDER}",
    "border_radius": "8px", "color": TEXT, "font_family": MONO,
    "font_size": "13px", "padding": "8px 10px", "outline": "none",
    "_focus": {"border_color": ACCENT},
    "_placeholder": {"color": TEXT3},
}

def _add_bucket_strip() -> rx.Component:
    return rx.vstack(
        # ── New category inline form (shown when creating) ────────────────
        rx.cond(
            AppState.add_bkt_creating_cat,
            rx.hstack(
                rx.box(style={
                    "width": "14px", "height": "14px", "border_radius": "50%",
                    "background": AppState.add_bkt_new_cat_color,
                    "flex_shrink": "0", "margin_top": "1px",
                }),
                rx.input(
                    placeholder="New category name…",
                    value=AppState.add_bkt_new_cat_name,
                    on_change=AppState.set_add_bkt_new_cat_name,
                    style={**_INPUT, "flex": "1", "min_width": "0"},
                ),
                rx.hstack(
                    *[_color_swatch(c) for c in _CAT_COLORS],
                    gap="4px", align_items="center", flex_wrap="wrap",
                ),
                align_items="center", gap="8px", width="100%",
                style={
                    "background": BG3, "border": f"1px solid {BORDER}",
                    "border_radius": "8px", "padding": "8px 12px",
                },
            ),
            rx.box(),
        ),

        # ── Main strip row: [Category ▾] [Name] [Type ▾] [+ Add] ─────────
        # On mobile this wraps to 2 rows via flex-wrap
        rx.hstack(
            rx.cond(
                AppState.add_bkt_creating_cat,
                rx.box(
                    rx.text("New category", style={
                        "font_size": "12px", "color": AppState.add_bkt_new_cat_color,
                        "font_family": MONO, "white_space": "nowrap",
                    }),
                    on_click=AppState.toggle_create_cat,
                    style={
                        "padding": "8px 10px", "border_radius": "8px",
                        "border": f"1px solid {BORDER}",
                        "background": BG3, "cursor": "pointer",
                        "flex_shrink": "0",
                        "_hover": {"border_color": BORDER2},
                    },
                ),
                rx.el.select(
                    rx.el.option("— Category —", value=""),
                    rx.el.option("＋ New Category", value="new"),
                    AppState.cat_options.to(list[dict[str, Any]]).foreach(
                        lambda c: rx.el.option(c["name"], value=c["id"])
                    ),
                    value=AppState.add_bkt_cat_id,
                    on_change=AppState.select_add_bkt_cat,
                    style={
                        **_INPUT, "flex": "0 0 auto", "min_width": "120px",
                        "max_width": "150px",
                    },
                ),
            ),

            rx.input(
                placeholder="Bucket name…",
                value=AppState.add_bkt_name,
                on_change=AppState.set_add_bkt_name,
                style={**_INPUT, "flex": "1", "min_width": "0"},
            ),

            rx.el.select(
                rx.el.option("Expense", value="expense"),
                rx.el.option("Sinking Fund", value="sinking"),
                rx.el.option("Goal", value="goal"),
                rx.el.option("Vault", value="vault"),
                value=AppState.add_bkt_type,
                on_change=AppState.set_add_bkt_type,
                style={**_INPUT, "flex": "0 0 auto", "min_width": "100px", "max_width": "120px"},
            ),

            rx.box(
                rx.cond(AppState.add_bkt_saving, "…", "+ Add"),
                on_click=AppState.add_bucket_submit,
                style={
                    "padding": "9px 16px", "border_radius": "8px",
                    "background": rx.cond(AppState.add_bkt_saving, BORDER, ACCENT),
                    "color": "#fff", "font_size": "13px", "cursor": "pointer",
                    "font_family": MONO, "letter_spacing": "0.06em",
                    "white_space": "nowrap", "flex_shrink": "0",
                    "_hover": {"opacity": "0.9"},
                },
            ),

            gap="8px", width="100%", align_items="center",
            flex_wrap="wrap",
        ),

        gap="6px", width="100%",
        style={
            "border": f"1px dashed {BORDER2}",
            "border_radius": "8px", "padding": "10px 14px",
            "margin_top": "8px",
        },
    )


# ── Main panel (2-column: left=buckets, right=scoreboard) ────────────────────


def _month_workflow_bar() -> rx.Component:
    """Contextual actions: copy last month, close/reopen month."""
    return rx.hstack(
        # Month status badge
        rx.cond(
            AppState.month_is_closed,
            rx.box(
                "CLOSED",
                style={
                    "font_size": "10px", "letter_spacing": "0.12em",
                    "text_transform": "uppercase", "color": TEXT3,
                    "font_family": MONO, "padding": "3px 8px",
                    "border": f"1px solid {BORDER2}", "border_radius": "6px",
                },
            ),
            rx.box(),
        ),
        rx.spacer(),
        # Copy last month allocations
        rx.cond(
            ~AppState.month_is_closed,
            rx.box(
                rx.cond(AppState.copy_allocs_saving, "Copying…", "Copy Last Month"),
                on_click=AppState.do_copy_allocs,
                style={
                    "font_size": "11px", "color": TEXT3, "cursor": "pointer",
                    "padding": "5px 10px", "border_radius": "6px",
                    "border": f"1px solid {BORDER}", "font_family": MONO,
                    "_hover": {"color": TEXT2, "border_color": BORDER2},
                },
            ),
            rx.box(),
        ),
        # Close / Reopen month
        rx.cond(
            AppState.month_is_closed,
            rx.box(
                "Reopen Month",
                on_click=AppState.do_reopen_month,
                style={
                    "font_size": "11px", "color": AMBER, "cursor": "pointer",
                    "padding": "5px 10px", "border_radius": "6px",
                    "border": f"1px solid {AMBER}44", "font_family": MONO,
                    "_hover": {"background": f"{AMBER}0d"},
                },
            ),
            rx.cond(
                AppState.month_status_str == "past",
                rx.box(
                    rx.cond(AppState.close_month_saving, "Closing…", "Close Month"),
                    on_click=AppState.do_close_month,
                    style={
                        "font_size": "11px", "color": TEXT3, "cursor": "pointer",
                        "padding": "5px 10px", "border_radius": "6px",
                        "border": f"1px solid {BORDER}", "font_family": MONO,
                        "_hover": {"color": TEXT2, "border_color": BORDER2},
                    },
                ),
                rx.box(),
            ),
        ),
        width="100%", align_items="center", gap="6px",
        style={"margin_bottom": "10px", "flex_wrap": "wrap"},
    )


def _buckets_empty_state() -> rx.Component:
    return rx.vstack(
        rx.text("🪣", style={"font_size": "40px", "line_height": "1"}),
        rx.text("No budget categories yet", style={
            "font_size": "16px", "font_weight": "600", "color": TEXT,
        }),
        rx.text(
            "Go to Setup → add a category, then add buckets below.",
            style={"font_size": "13px", "color": TEXT2, "text_align": "center", "max_width": "280px"},
        ),
        gap="10px", align_items="center",
        style={
            "padding": "48px 24px", "width": "100%",
            "border": f"1px dashed {BORDER2}", "border_radius": "10px",
            "margin_top": "12px",
        },
    )


def buckets_panel() -> rx.Component:
    return rx.box(
        rx.box(
            # ── Left column: bucket list ──────────────────────────────────
            rx.vstack(
                _month_workflow_bar(),
                rx.cond(
                    AppState.bucket_rows.length() == 0,
                    _buckets_empty_state(),
                    rx.foreach(AppState.bucket_rows.to(list[dict[str, Any]]), _bucket_row),
                ),
                _add_bucket_strip(),
                gap="0", align_items="stretch", width="100%",
            ),
            # ── Right column: scoreboard ──────────────────────────────────
            rx.box(
                _scoreboard(),
                style={
                    "position": "sticky",
                    "top": "72px",
                },
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
        bucket_settings_dialog(),
        style={"padding": "0", "overflow_x": "hidden", "width": "100%"},
    )
