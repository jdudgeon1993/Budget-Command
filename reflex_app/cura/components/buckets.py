"""Buckets panel — the core zero-based budgeting view."""

import reflex as rx
from typing import Any
from ..state import AppState
from ..theme import BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3, GREEN, AMBER, ACCENT, RED, VIOLET, MONO, SANS


def _rts_hero() -> rx.Component:
    """The Ready-to-Spend hero card at the top of the buckets panel."""
    border_color = rx.cond(
        AppState.rts_negative, f"1px solid {RED}44",
        rx.cond(AppState.rts_zero, f"1px solid {GREEN}44", f"1px solid {BORDER}"),
    )
    return rx.box(
        rx.vstack(
            # Top row: label + amount + kpis
            rx.hstack(
                # Left: label + amount + sub
                rx.vstack(
                    rx.text("READY TO SPEND",
                            style={"font_size": "8px", "letter_spacing": "0.12em",
                                   "color": TEXT3, "font_family": MONO}),
                    rx.text(AppState.rts_fmt,
                            style={"font_size": "28px", "font_weight": "700",
                                   "font_family": MONO, "color": AppState.rts_color,
                                   "line_height": "1.1"}),
                    rx.text(AppState.rts_sub,
                            style={"font_size": "11px", "color": TEXT3}),
                    align_items="flex-start", gap="3px",
                ),
                rx.spacer(),
                # Right: KPI chips
                rx.vstack(
                    rx.hstack(
                        rx.text("Income", style={"font_size": "9px", "color": TEXT3}),
                        rx.text(AppState.income_fmt,
                                style={"font_size": "11px", "color": GREEN, "font_family": MONO}),
                        justify="between", width="100%",
                    ),
                    rx.hstack(
                        rx.text("Spent", style={"font_size": "9px", "color": TEXT3}),
                        rx.text(AppState.spent_fmt,
                                style={"font_size": "11px", "color": AMBER, "font_family": MONO}),
                        justify="between", width="100%",
                    ),
                    rx.hstack(
                        rx.text("Alloc'd", style={"font_size": "9px", "color": TEXT3}),
                        rx.text(AppState.alloc_fmt,
                                style={"font_size": "11px", "color": ACCENT, "font_family": MONO}),
                        justify="between", width="100%",
                    ),
                    gap="4px", min_width="120px",
                ),
                align_items="flex-start", width="100%",
            ),

            # Allocation progress bar
            rx.vstack(
                rx.box(
                    rx.box(
                        class_name="prog-fill",
                        style={"height": "100%", "border_radius": "3px",
                               "background": rx.cond(
                                   AppState.total_alloc_val > AppState.income_total,
                                   RED, ACCENT),
                               "width": f"{AppState.alloc_pct}%"},
                    ),
                    style={"height": "6px", "border_radius": "3px",
                           "background": BG3, "overflow": "hidden", "width": "100%"},
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

            # Distribute RTS button
            rx.cond(
                AppState.distribute_visible,
                rx.box(
                    "▶ Distribute RTS",
                    style={
                        "font_family": MONO, "font_size": "9px", "letter_spacing": "0.06em",
                        "text_transform": "uppercase", "padding": "3px 10px",
                        "border_radius": "10px", "border": f"1px dashed {BORDER2}",
                        "color": TEXT3, "cursor": "pointer", "align_self": "flex-end",
                        "_hover": {"border_color": ACCENT, "color": ACCENT},
                    },
                ),
                rx.box(),
            ),

            gap="12px", width="100%",
        ),
        style={
            "background": BG2, "border": border_color, "border_radius": "10px",
            "padding": "16px 18px", "margin_bottom": "12px",
        },
    )


def _bucket_row(row: dict) -> rx.Component:
    """Single row — either a category header or a bucket."""
    return rx.cond(
        row["row_type"] == "header",

        # ── Category header ───────────────────────────────────────────────
        rx.text(
            row["name"],
            style={"font_size": "9px", "letter_spacing": "0.12em", "text_transform": "uppercase",
                   "color": TEXT3, "padding": "10px 2px 4px", "font_family": MONO},
        ),

        # ── Bucket row ────────────────────────────────────────────────────
        rx.box(
            # Top: name + fill btn + badge + value
            rx.hstack(
                rx.vstack(
                    rx.text(row["name"],
                            style={"font_size": "13px", "color": TEXT, "font_weight": "600"}),
                    rx.text(row["budget_fmt"], " budget · ", row["spent_fmt"], " spent",
                            style={"font_size": "10px", "color": TEXT3}),
                    gap="1px", align_items="flex-start", flex="1",
                ),
                # Fill shortcut
                rx.cond(
                    row["show_fill"],
                    rx.box(
                        "Fill",
                        on_click=AppState.fill_bucket(row["id"], row["budget"]),
                        style={
                            "font_family": MONO, "font_size": "9px", "letter_spacing": "0.06em",
                            "text_transform": "uppercase", "padding": "2px 7px",
                            "border_radius": "10px", "border": f"1px dashed {BORDER2}",
                            "color": TEXT3, "cursor": "pointer",
                            "_hover": {"border_color": ACCENT, "color": ACCENT},
                        },
                    ),
                    rx.box(),
                ),
                # Status badge
                rx.cond(
                    row["status"] != "",
                    rx.text(
                        row["status"],
                        style={
                            "font_family": MONO, "font_size": "9px", "letter_spacing": "0.07em",
                            "text_transform": "uppercase", "padding": "2px 7px",
                            "border_radius": "10px", "white_space": "nowrap",
                            "color": row["avail_color"],
                            "background": row["avail_bg"],
                            "border": row["avail_border"],
                        },
                    ),
                    rx.box(),
                ),
                # Available amount
                rx.text(
                    row["avail_fmt"],
                    style={"font_size": "14px", "font_weight": "700", "font_family": MONO,
                           "color": row["avail_color"], "white_space": "nowrap"},
                ),
                align_items="center", width="100%",
            ),

            # Progress bar
            rx.box(
                rx.box(
                    class_name="prog-fill",
                    style={"height": "100%", "border_radius": "2px",
                           "background": row["bar_color"],
                           "width": row["pct_str"]},
                ),
                style={"height": row["prog_h"], "background": BG3,
                       "border_radius": "2px", "overflow": "hidden",
                       "margin_top": "8px"},
            ),

            style={
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "padding": "10px 12px",
                "margin_bottom": "5px", "cursor": "default",
                "_hover": {"border_color": BORDER2},
            },
        ),
    )


def buckets_panel() -> rx.Component:
    return rx.box(
        _rts_hero(),
        rx.foreach(AppState.bucket_rows.to(list[dict[str, Any]]), _bucket_row),
        rx.box(
            "+ Add Bucket",
            style={
                "width": "100%", "padding": "10px",
                "background": BG3, "border": f"1px dashed {BORDER2}",
                "border_radius": "8px", "color": TEXT3,
                "font_size": "12px", "text_align": "center",
                "cursor": "pointer", "margin_top": "4px",
                "_hover": {"color": ACCENT, "border_color": ACCENT},
            },
        ),
        style={"padding": "0"},
    )
