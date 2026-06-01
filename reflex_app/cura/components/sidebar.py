"""Desktop sidebar — replaces the <aside class="sidebar"> in the Flask template."""

import reflex as rx
from ..state import AppState
from ..theme import BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3, GREEN, AMBER, ACCENT, MONO, SANS

def _kpi(label: str, value: rx.Component, color: str = TEXT) -> rx.Component:
    return rx.box(
        rx.text(label, style={"font_size": "11px", "letter_spacing": "0.09em",
                               "text_transform": "uppercase", "color": TEXT3, "margin_bottom": "3px"}),
        rx.text(value, style={"font_size": "13px", "font_weight": "700",
                               "font_family": MONO, "color": color}),
        style={"background": BG3, "border_radius": "8px", "padding": "7px 8px"},
    )


def _nav_item(label: str, panel: str, icon_path: str) -> rx.Component:
    is_active = AppState.active_panel == panel
    return rx.box(
        rx.html(f'''<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"
            aria-hidden="true">
            {icon_path}</svg>'''),
        rx.text(label, style={"font_size": "13px", "letter_spacing": "0.04em"}),
        on_click=AppState.set_panel(panel),
        role="button",
        tab_index=0,
        aria_label=label,
        style=rx.cond(
            is_active,
            {
                "display": "flex", "align_items": "center", "gap": "10px",
                "padding": "10px 10px", "border_radius": "8px", "cursor": "pointer",
                "background": f"{ACCENT}1f", "color": ACCENT,
                "user_select": "none",
                "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
            },
            {
                "display": "flex", "align_items": "center", "gap": "10px",
                "padding": "10px 10px", "border_radius": "8px", "cursor": "pointer",
                "color": TEXT3, "user_select": "none",
                "_hover": {"background": BG3, "color": TEXT2},
                "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
            },
        ),
    )


def sidebar() -> rx.Component:
    return rx.box(
        # ── Logo ─────────────────────────────────────────
        rx.box(
            rx.text("CURA", style={"font_size": "13px", "font_weight": "700",
                                    "letter_spacing": "0.18em", "color": ACCENT}),
            rx.text(AppState.month_display,
                    style={"font_size": "11px", "letter_spacing": "0.1em",
                           "color": TEXT3, "margin_top": "2px", "text_transform": "uppercase"}),
            style={"padding": "20px 18px 16px", "border_bottom": f"1px solid {BORDER}"},
        ),

        # ── Month navigation ──────────────────────────────
        rx.hstack(
            rx.box(
                "←",
                on_click=AppState.go_prev_month,
                role="button",
                tab_index=0,
                aria_label="Previous month",
                style={"cursor": "pointer", "color": TEXT3,
                       "padding": "8px 14px", "border_radius": "6px",
                       "font_size": "16px", "line_height": "1",
                       "_hover": {"color": ACCENT, "background": BG3},
                       "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"}},
            ),
            rx.text(AppState.month_display,
                    style={"font_size": "13px", "color": TEXT2, "flex": "1", "text_align": "center"}),
            rx.box(
                "→",
                on_click=AppState.go_next_month,
                role="button",
                tab_index=0,
                aria_label="Next month",
                style={"cursor": "pointer", "color": TEXT3,
                       "padding": "8px 14px", "border_radius": "6px",
                       "font_size": "16px", "line_height": "1",
                       "_hover": {"color": ACCENT, "background": BG3},
                       "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"}},
            ),
            style={
                "margin": "12px 12px 0", "background": BG3, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "padding": "2px 4px", "align_items": "center",
            },
        ),

        # ── KPI grid ─────────────────────────────────────
        rx.grid(
            _kpi("Income",  AppState.income_fmt, GREEN),
            _kpi("Ready",   AppState.rts_fmt,    AppState.rts_color),
            _kpi("Spent",   AppState.spent_fmt,  AMBER),
            _kpi("Alloc'd", AppState.alloc_fmt,  ACCENT),
            columns="2", gap="6px",
            style={"padding": "10px 12px", "border_bottom": f"1px solid {BORDER}"},
        ),

        # ── Nav ───────────────────────────────────────────
        rx.el.nav(
            rx.vstack(
                _nav_item("Buckets", "buckets",
                    '<rect x="3" y="3" width="7" height="7" rx="1"/>'
                    '<rect x="14" y="3" width="7" height="7" rx="1"/>'
                    '<rect x="3" y="14" width="7" height="7" rx="1"/>'
                    '<rect x="14" y="14" width="7" height="7" rx="1"/>'),
                _nav_item("Ledger", "ledger",
                    '<line x1="8" y1="6" x2="21" y2="6"/>'
                    '<line x1="8" y1="12" x2="21" y2="12"/>'
                    '<line x1="8" y1="18" x2="21" y2="18"/>'
                    '<circle cx="3" cy="6" r="1" fill="currentColor" stroke="none"/>'
                    '<circle cx="3" cy="12" r="1" fill="currentColor" stroke="none"/>'
                    '<circle cx="3" cy="18" r="1" fill="currentColor" stroke="none"/>'),
                _nav_item("Accounts", "accounts",
                    '<rect x="2" y="5" width="20" height="14" rx="2"/>'
                    '<line x1="2" y1="10" x2="22" y2="10"/>'),
                _nav_item("Insights", "insights",
                    '<line x1="18" y1="20" x2="18" y2="10"/>'
                    '<line x1="12" y1="20" x2="12" y2="4"/>'
                    '<line x1="6" y1="20" x2="6" y2="14"/>'),
                _nav_item("Setup", "setup",
                    '<circle cx="12" cy="12" r="3"/>'
                    '<path d="M19.1 12a7.1 7.1 0 0 0-.1-1l2.2-1.7-2.1-3.6-2.6 1a7 7 0 0 0-1.7-1l-.4-2.7h-4.2l-.4 2.7a7 7 0 0 0-1.7 1l-2.6-1-2.1 3.6 2.2 1.7a7.1 7.1 0 0 0 0 2l-2.2 1.7 2.1 3.6 2.6-1a7 7 0 0 0 1.7 1l.4 2.7h4.2l.4-2.7a7 7 0 0 0 1.7-1l2.6 1 2.1-3.6-2.2-1.7a7.1 7.1 0 0 0 .1-1z"/>'),
                gap="2px",
            ),
            style={"flex": "1", "padding": "10px 8px", "overflow_y": "auto"},
            aria_label="Main navigation",
        ),

        # ── Add Transaction CTA ───────────────────────────
        rx.box(
            rx.hstack(
                rx.html('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
                        'stroke="currentColor" stroke-width="2.5" aria-hidden="true">'
                        '<line x1="12" y1="5" x2="12" y2="19"/>'
                        '<line x1="5" y1="12" x2="19" y2="12"/></svg>'),
                rx.text("Add Transaction",
                        style={"font_size": "13px", "letter_spacing": "0.06em",
                               "text_transform": "uppercase"}),
                spacing="2",
            ),
            on_click=AppState.open_sheet,
            role="button",
            tab_index=0,
            aria_label="Add a new transaction",
            style={
                "margin": "0 12px 8px", "padding": "12px",
                "background": ACCENT, "color": "#fff",
                "border_radius": "8px", "cursor": "pointer",
                "display": "flex", "align_items": "center", "justify_content": "center",
                "gap": "8px", "box_shadow": f"0 4px 14px {ACCENT}59",
                "_hover": {"opacity": "0.9"},
                "_active": {"transform": "scale(0.98)"},
                "_focus_visible": {"outline": "2px solid #fff", "outline_offset": "2px"},
            },
        ),

        # ── User footer ───────────────────────────────────
        rx.hstack(
            rx.text(AppState.user_email,
                    style={"font_size": "12px", "color": TEXT3, "flex": "1",
                           "overflow": "hidden", "text_overflow": "ellipsis",
                           "white_space": "nowrap"}),
            rx.box(
                "Sign out",
                on_click=AppState.logout,
                role="button",
                tab_index=0,
                aria_label="Sign out",
                style={"font_size": "12px", "color": TEXT3, "cursor": "pointer",
                       "padding": "4px 8px", "border_radius": "4px",
                       "_hover": {"color": TEXT2},
                       "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"}},
            ),
            style={"padding": "10px 12px 14px", "border_top": f"1px solid {BORDER}"},
        ),

        class_name="sidebar-fixed",
        role="complementary",
        aria_label="Sidebar",
        style={"font_family": SANS},
    )
