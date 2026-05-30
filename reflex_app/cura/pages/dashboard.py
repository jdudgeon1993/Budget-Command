"""Dashboard page — the main app shell with sidebar + panel switcher."""

import reflex as rx
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS, SIDEBAR_W, NAV_H, HDR_H, GLOBAL_CSS)
from ..components.sidebar  import sidebar
from ..components.buckets  import buckets_panel
from ..components.ledger   import ledger_panel


# ── Mobile header ─────────────────────────────────────────────────────────────

def mobile_header() -> rx.Component:
    return rx.hstack(
        rx.text("CURA", style={"font_size": "13px", "font_weight": "700",
                                "letter_spacing": "0.16em", "color": ACCENT, "flex": "1"}),
        rx.hstack(
            rx.box("←", on_click=AppState.go_prev_month,
                   style={"cursor": "pointer", "color": TEXT3, "padding": "4px 6px"}),
            rx.text(AppState.month_display,
                    style={"font_size": "11px", "color": TEXT2, "letter_spacing": "0.06em",
                           "background": BG3, "border": f"1px solid {BORDER}",
                           "border_radius": "8px", "padding": "4px 10px"}),
            rx.box("→", on_click=AppState.go_next_month,
                   style={"cursor": "pointer", "color": TEXT3, "padding": "4px 6px"}),
            align_items="center", gap="2px",
        ),
        align_items="center",
        class_name="mobile-only",
        style={
            "position": "fixed", "top": "0", "left": "0", "right": "0",
            "height": HDR_H, "background": BG2, "border_bottom": f"1px solid {BORDER}",
            "padding": "0 14px", "gap": "10px", "z_index": "90",
        },
    )


# ── Mobile bottom nav ─────────────────────────────────────────────────────────

def _mob_tab(label: str, panel: str, icon_d: str) -> rx.Component:
    is_active = AppState.active_panel == panel
    return rx.vstack(
        rx.html(f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="1.75">{icon_d}</svg>'),
        rx.text(label, style={"font_size": "9px", "letter_spacing": "0.08em",
                               "text_transform": "uppercase", "line_height": "1"}),
        on_click=AppState.set_panel(panel),
        style=rx.cond(
            is_active,
            {"color": ACCENT, "cursor": "pointer", "align_items": "center",
             "gap": "4px", "flex": "1", "justify_content": "center"},
            {"color": TEXT3, "cursor": "pointer", "align_items": "center",
             "gap": "4px", "flex": "1", "justify_content": "center"},
        ),
    )


def mobile_nav() -> rx.Component:
    return rx.hstack(
        _mob_tab("Buckets", "buckets",
            '<rect x="3" y="3" width="7" height="7" rx="1"/>'
            '<rect x="14" y="3" width="7" height="7" rx="1"/>'
            '<rect x="3" y="14" width="7" height="7" rx="1"/>'
            '<rect x="14" y="14" width="7" height="7" rx="1"/>'),
        _mob_tab("Ledger", "ledger",
            '<line x1="8" y1="6" x2="21" y2="6"/>'
            '<line x1="8" y1="12" x2="21" y2="12"/>'
            '<line x1="8" y1="18" x2="21" y2="18"/>'
            '<circle cx="3" cy="6" r="1" fill="currentColor" stroke="none"/>'
            '<circle cx="3" cy="12" r="1" fill="currentColor" stroke="none"/>'
            '<circle cx="3" cy="18" r="1" fill="currentColor" stroke="none"/>'),
        _mob_tab("Accounts", "accounts",
            '<rect x="2" y="5" width="20" height="14" rx="2"/>'
            '<line x1="2" y1="10" x2="22" y2="10"/>'),
        _mob_tab("Insights", "insights",
            '<line x1="18" y1="20" x2="18" y2="10"/>'
            '<line x1="12" y1="20" x2="12" y2="4"/>'
            '<line x1="6" y1="20" x2="6" y2="14"/>'),
        # FAB
        rx.box(
            "+",
            on_click=AppState.open_sheet,
            style={
                "width": "50px", "height": "50px", "border_radius": "50%",
                "background": ACCENT, "color": "#fff",
                "display": "flex", "align_items": "center", "justify_content": "center",
                "font_size": "26px", "font_weight": "300", "cursor": "pointer",
                "margin": "0 8px 0 4px", "flex_shrink": "0",
                "box_shadow": f"0 4px 16px {ACCENT}80",
                "_active": {"transform": "scale(0.93)"},
            },
        ),
        class_name="mobile-only",
        style={
            "position": "fixed", "bottom": "0", "left": "0", "right": "0",
            "height": NAV_H, "background": BG2, "border_top": f"1px solid {BORDER}",
            "padding": "0 6px 0 0", "z_index": "100", "align_items": "center",
        },
    )


# ── Panel switcher ────────────────────────────────────────────────────────────

def _accounts_stub() -> rx.Component:
    return rx.vstack(
        rx.text("Accounts", style={"font_size": "16px", "font_weight": "700",
                                    "color": TEXT, "margin_bottom": "12px"}),
        rx.foreach(
            AppState.accounts_rows.to(list[dict]),
            lambda a: rx.hstack(
                rx.box(style={"width": "10px", "height": "10px", "border_radius": "50%",
                               "background": a["color"], "flex_shrink": "0"}),
                rx.text(a["name"], style={"flex": "1", "color": TEXT}),
                rx.text(a["type_upper"],
                        style={"font_size": "9px", "color": TEXT3, "letter_spacing": "0.08em"}),
                rx.text(a["balance_fmt"],
                        style={"font_family": MONO, "color": a["bal_color"], "font_weight": "700"}),
                align_items="center",
                style={
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "8px", "padding": "10px 14px", "width": "100%",
                },
            ),
        ),
        align_items="stretch",
    )


def _stub_panel(title: str) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.text(title, style={"font_size": "18px", "color": TEXT2}),
            rx.text("Coming soon", style={"font_size": "12px", "color": TEXT3}),
            align_items="center", gap="8px",
        ),
        style={"min_height": "300px"},
    )


def panel_content() -> rx.Component:
    return rx.box(
        rx.match(
            AppState.active_panel,
            ("buckets",  buckets_panel()),
            ("ledger",   ledger_panel()),
            ("accounts", _accounts_stub()),
            ("insights", _stub_panel("Insights")),
            ("setup",    _stub_panel("Setup")),
            buckets_panel(),
        ),
        style={"width": "100%"},
    )


# ── Full dashboard page ───────────────────────────────────────────────────────

def dashboard_page() -> rx.Component:
    return rx.box(
        # Inject global CSS + fonts
        rx.html(f"<style>{GLOBAL_CSS}</style>"),

        # Desktop sidebar
        sidebar(),

        # Mobile header + nav
        mobile_header(),
        mobile_nav(),

        # Main content area
        rx.box(
            # Desktop top header bar
            rx.hstack(
                rx.text(AppState.active_panel.upper(),
                        style={"font_size": "11px", "letter_spacing": "0.12em",
                               "text_transform": "uppercase", "color": TEXT2, "flex": "1"}),
                rx.hstack(
                    rx.box("←", on_click=AppState.go_prev_month,
                           style={"cursor": "pointer", "color": TEXT3, "padding": "4px 8px",
                                  "border_radius": "6px", "_hover": {"color": ACCENT, "background": BG3}}),
                    rx.text(AppState.month_display,
                            style={"font_size": "11px", "color": TEXT2}),
                    rx.box("→", on_click=AppState.go_next_month,
                           style={"cursor": "pointer", "color": TEXT3, "padding": "4px 8px",
                                  "border_radius": "6px", "_hover": {"color": ACCENT, "background": BG3}}),
                    align_items="center", gap="4px",
                ),
                class_name="desktop-only",
                style={
                    "background": BG2, "border_bottom": f"1px solid {BORDER}",
                    "padding": "0 24px", "height": HDR_H, "align_items": "center",
                    "position": "sticky", "top": "0", "z_index": "40",
                    "gap": "12px",
                },
            ),

            # Loading indicator
            rx.cond(
                AppState.is_loading,
                rx.box(
                    rx.text("Loading…", style={"color": TEXT3, "font_size": "12px",
                                               "font_family": MONO}),
                    style={"padding": "40px", "text_align": "center"},
                ),
                # Panels
                rx.box(
                    panel_content(),
                    style={
                        "padding": "20px 24px",
                        "padding_top": f"calc(20px + {HDR_H})",  # desktop: below sticky header
                    },
                ),
            ),

            class_name="main-content",
        ),

        on_mount=AppState.on_dashboard_load,
        style={"background": BG, "color": TEXT, "font_family": SANS, "min_height": "100vh"},
    )
