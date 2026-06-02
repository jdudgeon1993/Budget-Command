"""Dashboard page — the main app shell with sidebar + panel switcher."""

import reflex as rx
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS, SIDEBAR_W, NAV_H, HDR_H, GLOBAL_CSS)
from ..components.sidebar   import sidebar
from ..components.buckets   import buckets_panel
from ..components.ledger    import ledger_panel
from ..components.forecast  import forecast_panel
from ..components.setup     import setup_panel
from ..components.payday    import payday_modal
from ..components.accounts  import accounts_panel
from ..components.reports   import reports_panel


# ── Mobile header ─────────────────────────────────────────────────────────────

def mobile_header() -> rx.Component:
    return rx.hstack(
        rx.text("CURA", style={"font_size": "13px", "font_weight": "700",
                                "letter_spacing": "0.16em", "color": ACCENT}),
        rx.spacer(),
        # RTS — the most important number
        rx.vstack(
            rx.text(AppState.rts_fmt, style={
                "font_size": "15px", "font_weight": "700", "font_family": MONO,
                "color": AppState.rts_color, "line_height": "1",
            }),
            rx.text("ready to spend", style={
                "font_size": "12px", "color": TEXT3, "letter_spacing": "0.08em",
                "text_transform": "uppercase", "font_family": MONO,
            }),
            align_items="center", gap="1px",
        ),
        rx.spacer(),
        # Month nav
        rx.hstack(
            rx.box("←", on_click=AppState.go_prev_month,
                   role="button", tab_index=0, aria_label="Previous month",
                   style={"cursor": "pointer", "color": TEXT3, "padding": "8px 10px",
                          "border_radius": "6px", "font_size": "16px", "line_height": "1",
                          "_hover": {"color": ACCENT}}),
            rx.text(AppState.month_display,
                    style={"font_size": "12px", "color": TEXT2, "letter_spacing": "0.06em",
                           "background": BG3, "border": f"1px solid {BORDER}",
                           "border_radius": "8px", "padding": "4px 10px",
                           "white_space": "nowrap"}),
            rx.box("→", on_click=AppState.go_next_month,
                   role="button", tab_index=0, aria_label="Next month",
                   style={"cursor": "pointer", "color": TEXT3, "padding": "8px 10px",
                          "border_radius": "6px", "font_size": "16px", "line_height": "1",
                          "_hover": {"color": ACCENT}}),
            align_items="center", gap="2px",
        ),
        # Setup gear — moved out of bottom nav
        rx.box(
            rx.html(
                '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="1.75">'
                '<circle cx="12" cy="12" r="3"/>'
                '<path d="M19.1 12a7.1 7.1 0 0 0-.1-1l2.2-1.7-2.1-3.6-2.6 1'
                'a7 7 0 0 0-1.7-1l-.4-2.7h-4.2l-.4 2.7a7 7 0 0 0-1.7 1l-2.6-1'
                '-2.1 3.6 2.2 1.7a7.1 7.1 0 0 0 0 2l-2.2 1.7 2.1 3.6 2.6-1'
                'a7 7 0 0 0 1.7 1l.4 2.7h4.2l.4-2.7a7 7 0 0 0 1.7-1l2.6 1'
                ' 2.1-3.6-2.2-1.7a7.1 7.1 0 0 0 .1-1z"/>'
                '</svg>'
            ),
            on_click=AppState.set_panel("setup"),
            style={
                "color": rx.cond(AppState.active_panel == "setup", ACCENT, TEXT3),
                "cursor": "pointer", "padding": "6px",
                "border_radius": "8px",
                "_hover": {"color": TEXT2},
                "_active": {"opacity": "0.7"},
            },
        ),
        align_items="center",
        class_name="mobile-only",
        style={
            "position": "fixed", "top": "0", "left": "0", "right": "0",
            "height": HDR_H, "background": BG2, "border_bottom": f"1px solid {BORDER}",
            "padding": "0 8px 0 12px", "gap": "6px", "z_index": "90",
        },
    )


# ── Mobile bottom nav ─────────────────────────────────────────────────────────

def _mob_tab(label: str, panel: str, icon_d: str) -> rx.Component:
    is_active = AppState.active_panel == panel
    return rx.vstack(
        rx.html(f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="1.75" aria-hidden="true">{icon_d}</svg>'),
        rx.text(label, style={"font_size": "11px", "letter_spacing": "0.06em",
                               "text_transform": "uppercase", "line_height": "1"}),
        on_click=AppState.set_panel(panel),
        role="button",
        tab_index=0,
        aria_label=label,
        aria_current=rx.cond(is_active, "page", "false"),
        style=rx.cond(
            is_active,
            {"color": ACCENT, "cursor": "pointer", "align_items": "center",
             "gap": "4px", "flex": "1", "justify_content": "center",
             "min_height": "44px", "padding": "4px 0",
             "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"}},
            {"color": TEXT3, "cursor": "pointer", "align_items": "center",
             "gap": "4px", "flex": "1", "justify_content": "center",
             "min_height": "44px", "padding": "4px 0",
             "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"}},
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
        _mob_tab("Reports", "reports",
            '<rect x="3" y="3" width="18" height="4" rx="1"/>'
            '<rect x="3" y="10" width="12" height="4" rx="1"/>'
            '<rect x="3" y="17" width="15" height="4" rx="1"/>'),
        _mob_tab("Insights", "insights",
            '<line x1="18" y1="20" x2="18" y2="10"/>'
            '<line x1="12" y1="20" x2="12" y2="4"/>'
            '<line x1="6" y1="20" x2="6" y2="14"/>'),
        # FAB
        rx.box(
            "+",
            on_click=AppState.open_sheet,
            style={
                "width": "48px", "height": "48px", "border_radius": "50%",
                "background": ACCENT, "color": "#fff",
                "display": "flex", "align_items": "center", "justify_content": "center",
                "font_size": "26px", "font_weight": "300", "cursor": "pointer",
                "margin": "0 10px", "flex_shrink": "0",
                "box_shadow": f"0 4px 16px {ACCENT}80",
                "_active": {"transform": "scale(0.93)"},
            },
        ),
        class_name="mobile-only",
        style={
            "position": "fixed", "bottom": "0", "left": "0", "right": "0",
            "width": "100%", "height": NAV_H, "background": BG2,
            "border_top": f"1px solid {BORDER}",
            "display": "flex", "align_items": "center",
            "padding": "0", "z_index": "100",
        },
    )


# ── Panel switcher ────────────────────────────────────────────────────────────

def panel_content() -> rx.Component:
    return rx.box(
        rx.match(
            AppState.active_panel,
            ("buckets",  buckets_panel()),
            ("ledger",   ledger_panel()),
            ("accounts", accounts_panel()),
            ("reports",  reports_panel()),
            ("insights", forecast_panel()),
            ("setup",    setup_panel()),
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
                           role="button", tab_index=0, aria_label="Previous month",
                           style={"cursor": "pointer", "color": TEXT3, "padding": "6px 10px",
                                  "border_radius": "6px", "font_size": "15px",
                                  "_hover": {"color": ACCENT, "background": BG3}}),
                    rx.text(AppState.month_display,
                            style={"font_size": "13px", "color": TEXT2}),
                    rx.box("→", on_click=AppState.go_next_month,
                           role="button", tab_index=0, aria_label="Next month",
                           style={"cursor": "pointer", "color": TEXT3, "padding": "6px 10px",
                                  "border_radius": "6px", "font_size": "15px",
                                  "_hover": {"color": ACCENT, "background": BG3}}),
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
                        "max_width": "1400px",
                        "margin_left": "auto",
                        "margin_right": "auto",
                        "width": "100%",
                    },
                ),
            ),

            class_name="main-content",
        ),

        # Toast notifications + payday modal
        rx.toast.provider(),
        payday_modal(),

        on_mount=AppState.on_dashboard_load,
        style={"background": BG, "color": TEXT, "font_family": SANS, "min_height": "100vh"},
    )
