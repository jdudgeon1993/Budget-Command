"""Payday modal — shown after logging income to apply allocation rules."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import (BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS)


def _payday_row(row: dict) -> rx.Component:
    is_internal = row["rule_type"] == "internal"
    is_included = row["included"] == "1"
    return rx.hstack(
        # Toggle checkbox area
        rx.box(
            rx.cond(
                is_included,
                rx.text("✓", style={"font_size": "11px", "color": "#fff", "line_height": "1"}),
                rx.box(),
            ),
            on_click=AppState.toggle_payday_row(row["id"]),
            style={
                "width": "18px", "height": "18px", "border_radius": "4px",
                "border": rx.cond(
                    is_included,
                    f"2px solid {ACCENT}",
                    f"2px solid {BORDER2}",
                ),
                "background": rx.cond(is_included, ACCENT, "transparent"),
                "cursor": "pointer", "flex_shrink": "0",
                "display": "flex", "align_items": "center", "justify_content": "center",
            },
        ),

        # Rule info
        rx.vstack(
            rx.text(row["name"], style={
                "font_size": "13px", "color": rx.cond(is_included, TEXT, TEXT3),
                "font_weight": "600", "line_height": "1.2",
            }),
            rx.cond(
                is_internal,
                rx.text("→ ", row["bucket_name"],
                        style={"font_size": "12px", "color": TEXT3, "font_family": MONO}),
                rx.text("External transfer",
                        style={"font_size": "12px", "color": AMBER, "font_family": MONO}),
            ),
            gap="1px", align_items="flex-start", flex="1",
        ),

        # Value label
        rx.text(row["value_str"], style={
            "font_size": "12px", "color": TEXT3, "font_family": MONO,
            "white_space": "nowrap",
        }),

        # Amount
        rx.text(row["amount_fmt"], style={
            "font_family": MONO, "font_size": "14px", "font_weight": "700",
            "color": rx.cond(is_internal, ACCENT, AMBER),
            "white_space": "nowrap",
            "opacity": rx.cond(is_included, "1", "0.4"),
        }),

        align_items="center", width="100%", gap="10px",
        style={
            "padding": "10px 0",
            "border_bottom": f"1px solid {BORDER}",
            "opacity": rx.cond(is_included, "1", "0.6"),
        },
    )


def payday_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.text("PAYDAY", style={
                            "font_size": "12px", "letter_spacing": "0.18em",
                            "color": TEXT3, "font_family": MONO,
                        }),
                        rx.hstack(
                            rx.text("Income received: ", style={"font_size": "13px", "color": TEXT2}),
                            rx.text(AppState.payday_amount_fmt, style={
                                "font_size": "16px", "font_weight": "700",
                                "font_family": MONO, "color": GREEN,
                            }),
                            gap="4px", align_items="baseline",
                        ),
                        gap="2px", align_items="flex-start",
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

                rx.text(
                    "Toggle rules on/off, then apply to update this month's allocations.",
                    style={"font_size": "11px", "color": TEXT3, "line_height": "1.5"},
                ),

                rx.cond(
                    AppState.payday_rows.length() == 0,
                    rx.text("No active rules. Set them up in Setup.",
                            style={"font_size": "12px", "color": TEXT3, "font_family": MONO,
                                   "padding": "12px 0"}),
                    rx.vstack(
                        rx.foreach(
                            AppState.payday_rows.to(list[dict[str, Any]]),
                            _payday_row,
                        ),
                        gap="0px", width="100%",
                    ),
                ),

                rx.divider(style={"border_color": BORDER}),

                # Footer buttons
                rx.hstack(
                    rx.dialog.close(
                        rx.box(
                            "Skip",
                            style={
                                "flex": "1", "padding": "10px", "border_radius": "8px",
                                "border": f"1px solid {BORDER}", "color": TEXT3,
                                "font_size": "12px", "text_align": "center",
                                "cursor": "pointer", "font_family": MONO,
                            },
                        ),
                    ),
                    rx.box(
                        rx.cond(AppState.payday_saving, "Applying…", "Apply Allocations"),
                        on_click=AppState.apply_payday,
                        style={
                            "flex": "2", "padding": "10px", "border_radius": "8px",
                            "background": rx.cond(AppState.payday_saving, BORDER, GREEN),
                            "color": "#fff", "font_size": "12px", "text_align": "center",
                            "cursor": "pointer", "font_family": MONO,
                            "letter_spacing": "0.06em", "text_transform": "uppercase",
                            "font_weight": "700", "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="8px", width="100%",
                ),

                gap="14px", width="100%",
            ),
            style={
                "background": "rgba(14,14,22,0.96)",
                "border": f"1px solid {BORDER2}",
                "border_radius": "16px", "padding": "24px",
                "max_width": "460px", "width": "95vw",
                "box_shadow": "0 24px 60px rgba(0,0,0,0.65)",
            },
        ),
        open=AppState.payday_open,
        on_open_change=AppState.set_payday_open,
    )
