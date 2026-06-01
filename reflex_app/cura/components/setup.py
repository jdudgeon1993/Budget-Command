"""Setup panel — paychecks and allocation rules."""

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


def _sel(*options, value, on_change, **extra) -> rx.Component:
    return rx.el.select(
        *options,
        value=value, on_change=on_change,
        style={
            "background": BG3, "border": f"1px solid {BORDER}",
            "border_radius": "8px", "color": TEXT, "font_size": "12px",
            "padding": "8px 10px", **extra,
        },
    )


def _section_head(label: str) -> rx.Component:
    return rx.text(label, style={
        "font_size": "11px", "letter_spacing": "0.16em",
        "text_transform": "uppercase", "color": TEXT3,
        "font_family": MONO, "padding_bottom": "8px",
        "border_bottom": f"1px solid {BORDER}",
        "margin_bottom": "10px", "width": "100%",
    })


def _pill_btn(label: str, on_click, color: str = ACCENT) -> rx.Component:
    return rx.box(
        label,
        on_click=on_click,
        style={
            "font_family": MONO, "font_size": "11px", "letter_spacing": "0.08em",
            "text_transform": "uppercase", "padding": "3px 10px",
            "border_radius": "10px", "border": f"1px solid {color}44",
            "color": color, "cursor": "pointer", "flex_shrink": "0",
            "_hover": {"background": f"{color}11"},
        },
    )


# ── Paycheck row ──────────────────────────────────────────────────────────────

def _pc_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(row["label"], style={"font_size": "13px", "color": TEXT, "font_weight": "600"}),
            rx.text(row["freq_label"],
                    style={"font_size": "12px", "color": TEXT3, "font_family": MONO}),
            gap="1px", align_items="flex-start", flex="1",
        ),
        rx.text(row["amount_fmt"], style={
            "font_family": MONO, "font_size": "14px", "font_weight": "700",
            "color": GREEN, "white_space": "nowrap",
        }),
        rx.box(
            "✕",
            on_click=AppState.delete_paycheck_item(row["id"]),
            style={
                "font_size": "14px", "color": TEXT3, "cursor": "pointer",
                "padding": "2px 6px", "border_radius": "4px",
                "_hover": {"color": RED, "background": f"{RED}11"},
            },
        ),
        align_items="center", width="100%", gap="8px",
        style={
            "background": BG2, "border": f"1px solid {BORDER}",
            "border_radius": "8px", "padding": "10px 12px",
            "margin_bottom": "5px",
        },
    )


# ── Paychecks section ─────────────────────────────────────────────────────────

def _paychecks_section() -> rx.Component:
    return rx.vstack(
        _section_head("Paychecks"),

        rx.cond(
            AppState.paycheck_rows.length() == 0,
            rx.text("No paychecks yet. Add one below.",
                    style={"font_size": "12px", "color": TEXT3, "font_family": MONO,
                           "padding": "8px 0"}),
            rx.foreach(
                AppState.paycheck_rows.to(list[dict[str, Any]]),
                _pc_row,
            ),
        ),

        # Add strip
        rx.vstack(
            rx.hstack(
                _inp("Label (e.g. Main Job)", AppState.setup_pc_label,
                     AppState.set_setup_pc_label, flex="2"),
                _inp("Amount", AppState.setup_pc_amount,
                     AppState.set_setup_pc_amount, type_="number",
                     input_mode="decimal", flex="1"),
                gap="8px", width="100%",
            ),
            rx.hstack(
                _sel(
                    rx.el.option("Biweekly (every 2 weeks)", value="14"),
                    rx.el.option("Weekly", value="7"),
                    rx.el.option("Semi-monthly (1st & 15th)", value="15"),
                    value=AppState.setup_pc_freq,
                    on_change=AppState.set_setup_pc_freq,
                    flex="2",
                ),
                _inp("Anchor date (YYYY-MM-DD)", AppState.setup_pc_anchor,
                     AppState.set_setup_pc_anchor, flex="2"),
                rx.box(
                    rx.cond(AppState.setup_pc_saving, "…", "+ Add"),
                    on_click=AppState.add_paycheck_submit,
                    style={
                        "padding": "8px 14px", "border_radius": "8px",
                        "background": rx.cond(AppState.setup_pc_saving, BORDER, ACCENT),
                        "color": "#fff", "font_size": "11px", "cursor": "pointer",
                        "font_family": MONO, "white_space": "nowrap",
                        "flex_shrink": "0", "_hover": {"opacity": "0.9"},
                    },
                ),
                gap="8px", width="100%", align_items="center",
            ),
            rx.cond(
                AppState.setup_pc_error != "",
                rx.text(AppState.setup_pc_error,
                        style={"font_size": "11px", "color": RED, "font_family": MONO}),
                rx.box(),
            ),
            gap="8px", width="100%",
            style={
                "border": f"1px dashed {BORDER2}", "border_radius": "8px",
                "padding": "10px 12px", "margin_top": "6px",
            },
        ),

        gap="0px", align_items="stretch", width="100%",
    )


# ── Rule row ──────────────────────────────────────────────────────────────────

def _rule_row(row: dict) -> rx.Component:
    is_internal = row["rule_type"] == "internal"
    is_active   = row["active_str"] == "1"
    return rx.hstack(
        rx.box(
            style={
                "width": "8px", "height": "8px", "border_radius": "50%",
                "background": rx.cond(
                    row["rule_type"] == "internal",
                    ACCENT,
                    AMBER,
                ),
                "flex_shrink": "0",
            },
        ),
        rx.vstack(
            rx.hstack(
                rx.text(row["name"], style={
                    "font_size": "13px", "color": rx.cond(is_active, TEXT, TEXT3),
                    "font_weight": "600",
                }),
                rx.cond(
                    row["rule_type"] == "internal",
                    rx.text("INTERNAL", style={
                        "font_size": "11px", "color": ACCENT, "font_family": MONO,
                        "letter_spacing": "0.1em", "background": f"{ACCENT}1a",
                        "padding": "1px 5px", "border_radius": "4px",
                    }),
                    rx.text("EXTERNAL", style={
                        "font_size": "11px", "color": AMBER, "font_family": MONO,
                        "letter_spacing": "0.1em", "background": f"{AMBER}1a",
                        "padding": "1px 5px", "border_radius": "4px",
                    }),
                ),
                gap="6px", align_items="center",
            ),
            rx.cond(
                row["rule_type"] == "internal",
                rx.text(row["value_str"], " → ", row["bucket_name"],
                        style={"font_size": "12px", "color": TEXT3, "font_family": MONO}),
                rx.text(row["value_str"], " (external transfer)",
                        style={"font_size": "12px", "color": TEXT3, "font_family": MONO}),
            ),
            gap="1px", align_items="flex-start", flex="1",
        ),
        rx.spacer(),
        rx.switch(
            checked=is_active,
            on_change=AppState.toggle_alloc_rule_item(row["id"]),
            color_scheme="indigo",
        ),
        rx.box(
            "✕",
            on_click=AppState.delete_alloc_rule_item(row["id"]),
            style={
                "font_size": "14px", "color": TEXT3, "cursor": "pointer",
                "padding": "2px 6px", "border_radius": "4px",
                "_hover": {"color": RED, "background": f"{RED}11"},
            },
        ),
        align_items="center", width="100%", gap="8px",
        style={
            "background": BG2, "border": f"1px solid {BORDER}",
            "border_radius": "8px", "padding": "10px 12px",
            "margin_bottom": "5px",
            "opacity": rx.cond(is_active, "1", "0.5"),
        },
    )


# ── Add rule dialog ───────────────────────────────────────────────────────────

def _rule_dialog() -> rx.Component:
    is_internal = AppState.rule_sheet_itype == "internal"
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        rx.cond(is_internal, "Add Internal Rule", "Add External Rule"),
                        style={
                            "font_size": "11px", "letter_spacing": "0.14em",
                            "text_transform": "uppercase", "color": TEXT2,
                            "flex": "1", "font_family": MONO,
                        },
                    ),
                    rx.dialog.close(
                        rx.box("×", style={
                            "font_size": "22px", "color": TEXT3, "cursor": "pointer",
                            "line_height": "1", "_hover": {"color": TEXT},
                        }),
                    ),
                    align_items="center", width="100%",
                ),
                rx.divider(style={"border_color": BORDER}),

                rx.vstack(
                    rx.text("Rule Name", style={
                        "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
                        "text_transform": "uppercase", "font_family": MONO,
                    }),
                    _inp("e.g. 5% to Emergency Fund", AppState.rule_sheet_name,
                         AppState.set_rule_sheet_name, width="100%"),
                    gap="4px", align_items="stretch", width="100%",
                ),

                rx.hstack(
                    rx.vstack(
                        rx.text("Type", style={
                            "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
                            "text_transform": "uppercase", "font_family": MONO,
                        }),
                        _sel(
                            rx.el.option("Fixed $", value="fixed"),
                            rx.el.option("Percent %", value="pct"),
                            value=AppState.rule_sheet_val_type,
                            on_change=AppState.set_rule_sheet_val_type,
                            flex="1",
                        ),
                        gap="4px", align_items="stretch", flex="1",
                    ),
                    rx.vstack(
                        rx.text(
                            rx.cond(AppState.rule_sheet_val_type == "pct",
                                    "Percent (%)", "Amount ($)"),
                            style={
                                "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
                                "text_transform": "uppercase", "font_family": MONO,
                            },
                        ),
                        _inp("e.g. 5 or 200", AppState.rule_sheet_value,
                             AppState.set_rule_sheet_value, type_="number",
                             input_mode="decimal", flex="1"),
                        gap="4px", align_items="stretch", flex="1",
                    ),
                    gap="10px", width="100%",
                ),

                rx.cond(
                    is_internal,
                    rx.vstack(
                        rx.text("Destination Bucket", style={
                            "font_size": "11px", "color": TEXT3, "letter_spacing": "0.1em",
                            "text_transform": "uppercase", "font_family": MONO,
                        }),
                        rx.el.select(
                            rx.el.option("— Select bucket —", value=""),
                            AppState.expense_buckets.to(list[dict[str, Any]]).foreach(
                                lambda b: rx.el.option(b["name"], value=b["id"])
                            ),
                            value=AppState.rule_sheet_bid,
                            on_change=AppState.set_rule_sheet_bid,
                            style={
                                "background": BG3, "border": f"1px solid {BORDER}",
                                "border_radius": "8px", "color": TEXT, "font_size": "12px",
                                "padding": "8px 10px", "width": "100%",
                            },
                        ),
                        gap="4px", align_items="stretch", width="100%",
                    ),
                    rx.box(),
                ),

                rx.cond(
                    AppState.rule_sheet_error != "",
                    rx.text(AppState.rule_sheet_error,
                            style={"color": RED, "font_size": "11px", "font_family": MONO}),
                    rx.box(),
                ),

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
                        rx.cond(AppState.rule_sheet_saving, "Saving…", "Add Rule"),
                        on_click=AppState.add_alloc_rule_submit,
                        style={
                            "flex": "2", "padding": "9px", "border_radius": "8px",
                            "background": rx.cond(AppState.rule_sheet_saving, BORDER, ACCENT),
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
                "max_width": "400px", "width": "95vw",
            },
        ),
        open=AppState.rule_sheet_open,
        on_open_change=AppState.set_rule_sheet_open,
    )


# ── Allocation rules section ──────────────────────────────────────────────────

def _rules_section() -> rx.Component:
    internal_rules = AppState.alloc_rule_rows.to(list[dict[str, Any]])
    return rx.vstack(
        _section_head("Payday Allocation Rules"),

        rx.text(
            "When you log income, these rules suggest how to allocate it. "
            "Internal rules fill buckets. External rules are cash transfers (reminders only).",
            style={"font_size": "11px", "color": TEXT3, "line_height": "1.5",
                   "margin_bottom": "8px"},
        ),

        rx.cond(
            AppState.alloc_rule_rows.length() == 0,
            rx.text("No rules yet. Add one below.",
                    style={"font_size": "12px", "color": TEXT3, "font_family": MONO,
                           "padding": "8px 0"}),
            rx.foreach(internal_rules, _rule_row),
        ),

        # Add buttons
        rx.hstack(
            rx.box(
                "+ Internal Rule",
                on_click=AppState.open_rule_sheet("internal"),
                style={
                    "flex": "1", "padding": "9px", "border_radius": "8px",
                    "border": f"1px dashed {ACCENT}55", "color": ACCENT,
                    "font_size": "11px", "text_align": "center", "cursor": "pointer",
                    "font_family": MONO, "letter_spacing": "0.06em",
                    "_hover": {"background": f"{ACCENT}0d"},
                },
            ),
            rx.box(
                "+ External Transfer",
                on_click=AppState.open_rule_sheet("external"),
                style={
                    "flex": "1", "padding": "9px", "border_radius": "8px",
                    "border": f"1px dashed {AMBER}55", "color": AMBER,
                    "font_size": "11px", "text_align": "center", "cursor": "pointer",
                    "font_family": MONO, "letter_spacing": "0.06em",
                    "_hover": {"background": f"{AMBER}0d"},
                },
            ),
            gap="8px", width="100%",
        ),

        _rule_dialog(),

        gap="0px", align_items="stretch", width="100%",
    )


# ── Main panel ────────────────────────────────────────────────────────────────

def setup_panel() -> rx.Component:
    return rx.vstack(
        _paychecks_section(),
        rx.divider(style={"border_color": BORDER, "margin": "20px 0"}),
        _rules_section(),
        gap="0px", align_items="stretch", width="100%",
    )
