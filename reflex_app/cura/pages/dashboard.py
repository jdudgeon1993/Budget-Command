"""Dashboard page — the main app shell with sidebar + panel switcher."""

import reflex as rx
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3,
                     GREEN, AMBER, ACCENT, RED, MONO, SANS, SIDEBAR_W, NAV_H, HDR_H, GLOBAL_CSS)
from ..components.sidebar   import sidebar
from ..components.buckets   import buckets_panel
from ..components.forecast  import forecast_panel
from ..components.setup     import setup_panel
from ..components.payday    import payday_modal
from ..components.accounts  import accounts_panel
from ..components.reports   import reports_panel


# ── Mobile header ─────────────────────────────────────────────────────────────

_MOB_BRAND_ICON = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
    'stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
    '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
    '<rect x="3" y="14" width="7" height="7" rx="1.5"/>'
    '<rect x="14" y="14" width="7" height="7" rx="1.5"/>'
    '</svg>'
)


def mobile_header() -> rx.Component:
    return rx.hstack(
        # Brand mark
        rx.hstack(
            rx.box(
                rx.html(_MOB_BRAND_ICON),
                style={
                    "width": "26px", "height": "26px", "flex_shrink": "0",
                    "background": ACCENT, "border_radius": "7px",
                    "display": "flex", "align_items": "center", "justify_content": "center",
                },
            ),
            rx.text("CURA", style={
                "font_size": "13px", "font_weight": "700",
                "letter_spacing": "0.14em", "color": "#fff",
                "text_transform": "uppercase",
            }),
            align_items="center", gap="7px",
        ),
        rx.spacer(),
        # RTS — most important number
        rx.vstack(
            rx.text(AppState.rts_fmt, style={
                "font_size": "17px", "font_weight": "600", "font_family": MONO,
                "color": "#BF5AF2", "line_height": "1", "letter_spacing": "-0.01em",
            }),
            rx.text("ready to assign", style={
                "font_size": "10px", "color": "rgba(255,255,255,0.30)",
                "letter_spacing": "0.08em", "text_transform": "uppercase",
                "font_family": MONO, "line_height": "1",
            }),
            align_items="center", gap="3px",
        ),
        rx.spacer(),
        # Month nav
        rx.hstack(
            rx.box("←", on_click=AppState.go_prev_month,
                   role="button", tab_index=0, aria_label="Previous month",
                   style={
                       "cursor": "pointer", "color": "rgba(255,255,255,0.30)",
                       "padding": "6px 10px", "border_radius": "6px",
                       "font_size": "15px", "line_height": "1",
                       "_hover": {"color": "#BF5AF2", "background": "rgba(255,255,255,0.05)"},
                   }),
            rx.text(AppState.month_display,
                    style={
                        "font_size": "11px", "color": "rgba(255,255,255,0.42)",
                        "letter_spacing": "0.06em", "font_family": MONO,
                        "white_space": "nowrap",
                    }),
            rx.box("→", on_click=AppState.go_next_month,
                   role="button", tab_index=0, aria_label="Next month",
                   style={
                       "cursor": "pointer", "color": "rgba(255,255,255,0.30)",
                       "padding": "6px 10px", "border_radius": "6px",
                       "font_size": "15px", "line_height": "1",
                       "_hover": {"color": "#BF5AF2", "background": "rgba(255,255,255,0.05)"},
                   }),
            align_items="center", gap="0px",
        ),
        align_items="center",
        class_name="mobile-only",
        style={
            "position": "fixed", "top": "0", "left": "0", "right": "0",
            "height": HDR_H, "background": BG, "border_bottom": f"1px solid {BORDER}",
            "padding": "0 4px 0 10px", "gap": "4px", "z_index": "90",
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
            {"color": "#D8A4FF", "cursor": "pointer", "align_items": "center",
             "gap": "4px", "flex": "1", "justify_content": "center",
             "min_height": "44px", "padding": "4px 0",
             "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"}},
            {"color": "rgba(255,255,255,0.30)", "cursor": "pointer", "align_items": "center",
             "gap": "4px", "flex": "1", "justify_content": "center",
             "min_height": "44px", "padding": "4px 0",
             "_hover": {"color": "rgba(255,255,255,0.60)"},
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
        # FAB — pulsing violet
        rx.box(
            rx.html(
                '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
                'stroke="white" stroke-width="2.5" aria-hidden="true">'
                '<line x1="12" y1="5" x2="12" y2="19"/>'
                '<line x1="5" y1="12" x2="19" y2="12"/></svg>'
            ),
            on_click=AppState.open_sheet,
            class_name="mobile-fab",
            role="button",
            tab_index=0,
            aria_label="Add transaction",
            style={
                "width": "52px", "height": "52px", "border_radius": "50%",
                "background": ACCENT, "color": "#fff",
                "display": "flex", "align_items": "center", "justify_content": "center",
                "cursor": "pointer", "flex_shrink": "0",
                "margin_bottom": "4px",
                "_active": {"transform": "scale(0.92)"},
            },
        ),
        class_name="mobile-only",
        style={
            "position": "fixed", "bottom": "0", "left": "0", "right": "0",
            "width": "100%", "height": NAV_H, "background": BG,
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
                        style={
                            "font_size": "10px", "letter_spacing": "0.14em",
                            "text_transform": "uppercase", "color": "rgba(255,255,255,0.28)",
                            "font_family": MONO, "flex": "1",
                        }),
                rx.hstack(
                    rx.box("←", on_click=AppState.go_prev_month,
                           role="button", tab_index=0, aria_label="Previous month",
                           style={
                               "cursor": "pointer", "color": "rgba(255,255,255,0.30)",
                               "padding": "6px 12px", "border_radius": "6px",
                               "font_size": "15px", "line_height": "1",
                               "_hover": {"color": "#BF5AF2", "background": "rgba(255,255,255,0.05)"},
                               "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
                           }),
                    rx.text(AppState.month_display,
                            style={
                                "font_size": "12px", "color": "rgba(255,255,255,0.42)",
                                "letter_spacing": "0.06em", "font_family": MONO,
                            }),
                    rx.box("→", on_click=AppState.go_next_month,
                           role="button", tab_index=0, aria_label="Next month",
                           style={
                               "cursor": "pointer", "color": "rgba(255,255,255,0.30)",
                               "padding": "6px 12px", "border_radius": "6px",
                               "font_size": "15px", "line_height": "1",
                               "_hover": {"color": "#BF5AF2", "background": "rgba(255,255,255,0.05)"},
                               "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
                           }),
                    align_items="center", gap="2px",
                ),
                class_name="desktop-only",
                style={
                    "background": BG2, "border_bottom": f"1px solid {BORDER}",
                    "padding": "0 24px", "height": HDR_H, "align_items": "center",
                    "position": "sticky", "top": "0", "z_index": "40",
                    "gap": "12px",
                    "backdrop_filter": "blur(8px)",
                    "-webkit-backdrop_filter": "blur(8px)",
                },
            ),

            # Loading indicator
            rx.cond(
                AppState.is_loading,
                rx.box(
                    rx.vstack(
                        rx.box(class_name="skeleton", style={"height": "18px", "width": "180px", "border_radius": "6px"}),
                        rx.box(class_name="skeleton", style={"height": "14px", "width": "120px", "border_radius": "6px"}),
                        rx.box(class_name="skeleton", style={"height": "14px", "width": "150px", "border_radius": "6px"}),
                        gap="10px", align_items="flex_start",
                    ),
                    style={"padding": "40px"},
                ),
                # Panels
                rx.box(
                    panel_content(),
                    class_name="panel-content-box",
                    style={
                        "padding": "20px 16px",
                        "padding_top": f"calc(16px + {HDR_H})",
                        "padding_bottom": f"calc(20px + {NAV_H})",  # mobile: clear bottom nav
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
