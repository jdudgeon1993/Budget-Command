"""Desktop sidebar — Electric theme."""

import reflex as rx
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, TEXT, TEXT2, TEXT3,
                     GREEN, ACCENT, ACCENT_GLOW, MONO, SANS)

# ── Brand icon SVG ────────────────────────────────────────────────────────────
_BRAND_ICON = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" '
    'stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
    '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
    '<rect x="3" y="14" width="7" height="7" rx="1.5"/>'
    '<rect x="14" y="14" width="7" height="7" rx="1.5"/>'
    '</svg>'
)

# ── Nav item ──────────────────────────────────────────────────────────────────
def _nav_item(label: str, panel: str, icon_path: str) -> rx.Component:
    is_active = AppState.active_panel == panel
    return rx.box(
        rx.html(
            f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.75" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{icon_path}</svg>'
        ),
        rx.text(label, style={"font_size": "13px", "font_weight": "500",
                               "letter_spacing": "0.02em"}),
        on_click=AppState.set_panel(panel),
        role="button",
        tab_index=0,
        aria_label=label,
        style=rx.cond(
            is_active,
            {
                "display": "flex", "align_items": "center", "gap": "10px",
                "padding": "9px 10px", "border_radius": "8px", "cursor": "pointer",
                "background": "rgba(191,90,242,0.14)", "color": "#D8A4FF",
                "user_select": "none",
                "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
            },
            {
                "display": "flex", "align_items": "center", "gap": "10px",
                "padding": "9px 10px", "border_radius": "8px", "cursor": "pointer",
                "color": TEXT3, "user_select": "none",
                "_hover": {"background": "rgba(255,255,255,0.05)", "color": TEXT2},
                "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
            },
        ),
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar() -> rx.Component:
    return rx.box(

        # ── Brand ─────────────────────────────────────────
        rx.box(
            rx.hstack(
                # Violet brand icon
                rx.box(
                    rx.html(_BRAND_ICON),
                    style={
                        "width": "30px", "height": "30px", "flex_shrink": "0",
                        "background": ACCENT, "border_radius": "8px",
                        "display": "flex", "align_items": "center", "justify_content": "center",
                        "box_shadow": f"0 2px 10px {ACCENT_GLOW}",
                    },
                ),
                rx.vstack(
                    rx.text("CURA", style={
                        "font_size": "14px", "font_weight": "700",
                        "letter_spacing": "0.14em", "color": "#fff",
                        "text_transform": "uppercase", "line_height": "1",
                    }),
                    rx.text("Personal Finance", style={
                        "font_size": "10px", "color": "rgba(255,255,255,0.28)",
                        "letter_spacing": "0.07em", "text_transform": "uppercase",
                        "line_height": "1",
                    }),
                    gap="4px", align_items="flex_start",
                ),
                align_items="center", gap="10px",
            ),
            style={
                "padding": "18px 16px 16px",
                "border_bottom": f"1px solid {BORDER}",
            },
        ),

        # ── RTS Block ─────────────────────────────────────
        rx.box(
            rx.text("Ready to assign", style={
                "font_size": "10px", "font_family": MONO,
                "letter_spacing": "0.14em", "text_transform": "uppercase",
                "color": "rgba(255,255,255,0.28)", "margin_bottom": "4px",
            }),
            rx.text(AppState.rts_fmt, style={
                "font_family": MONO, "font_size": "26px", "font_weight": "600",
                "color": "#BF5AF2", "line_height": "1", "letter_spacing": "-0.01em",
            }),
            rx.text(
                AppState.income_fmt + " income",
                style={
                    "font_size": "11px", "color": "rgba(255,255,255,0.25)",
                    "margin_top": "4px", "font_family": MONO,
                },
            ),
            style={
                "padding": "14px 16px",
                "border_bottom": f"1px solid {BORDER}",
            },
        ),

        # ── Month navigation ──────────────────────────────
        rx.hstack(
            rx.box(
                "←",
                on_click=AppState.go_prev_month,
                role="button", tab_index=0, aria_label="Previous month",
                style={
                    "cursor": "pointer", "color": "rgba(255,255,255,0.30)",
                    "padding": "6px 12px", "border_radius": "6px",
                    "font_size": "15px", "line_height": "1",
                    "_hover": {"color": "#BF5AF2", "background": "rgba(255,255,255,0.05)"},
                    "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
                },
            ),
            rx.text(
                AppState.month_display,
                style={
                    "font_size": "12px", "color": "rgba(255,255,255,0.42)",
                    "flex": "1", "text_align": "center",
                    "letter_spacing": "0.06em", "font_family": MONO,
                },
            ),
            rx.box(
                "→",
                on_click=AppState.go_next_month,
                role="button", tab_index=0, aria_label="Next month",
                style={
                    "cursor": "pointer", "color": "rgba(255,255,255,0.30)",
                    "padding": "6px 12px", "border_radius": "6px",
                    "font_size": "15px", "line_height": "1",
                    "_hover": {"color": "#BF5AF2", "background": "rgba(255,255,255,0.05)"},
                    "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
                },
            ),
            style={
                "padding": "6px 8px",
                "border_bottom": f"1px solid {BORDER}",
                "align_items": "center",
            },
        ),

        # ── Nav ───────────────────────────────────────────
        rx.el.nav(
            rx.vstack(
                _nav_item("Buckets", "buckets",
                    '<rect x="3" y="3" width="7" height="7" rx="1"/>'
                    '<rect x="14" y="3" width="7" height="7" rx="1"/>'
                    '<rect x="3" y="14" width="7" height="7" rx="1"/>'
                    '<rect x="14" y="14" width="7" height="7" rx="1"/>'),
                _nav_item("Accounts", "accounts",
                    '<rect x="2" y="5" width="20" height="14" rx="2"/>'
                    '<line x1="2" y1="10" x2="22" y2="10"/>'),
                _nav_item("Insights", "insights",
                    '<line x1="18" y1="20" x2="18" y2="10"/>'
                    '<line x1="12" y1="20" x2="12" y2="4"/>'
                    '<line x1="6" y1="20" x2="6" y2="14"/>'),
                _nav_item("Reports", "reports",
                    '<rect x="3" y="3" width="18" height="4" rx="1"/>'
                    '<rect x="3" y="10" width="12" height="4" rx="1"/>'
                    '<rect x="3" y="17" width="15" height="4" rx="1"/>'),
                _nav_item("Setup", "setup",
                    '<circle cx="12" cy="12" r="3"/>'
                    '<path d="M19.1 12a7.1 7.1 0 0 0-.1-1l2.2-1.7-2.1-3.6-2.6 1'
                    'a7 7 0 0 0-1.7-1l-.4-2.7h-4.2l-.4 2.7a7 7 0 0 0-1.7 1l-2.6-1'
                    '-2.1 3.6 2.2 1.7a7.1 7.1 0 0 0 0 2l-2.2 1.7 2.1 3.6 2.6-1'
                    'a7 7 0 0 0 1.7 1l.4 2.7h4.2l.4-2.7a7 7 0 0 0 1.7-1l2.6 1'
                    ' 2.1-3.6-2.2-1.7a7.1 7.1 0 0 0 .1-1z"/>'),
                gap="2px",
            ),
            style={"flex": "1", "padding": "10px 8px", "overflow_y": "auto"},
            aria_label="Main navigation",
        ),

        # ── Add Transaction CTA ───────────────────────────
        rx.box(
            rx.hstack(
                rx.html(
                    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
                    'stroke="currentColor" stroke-width="2.5" aria-hidden="true">'
                    '<line x1="12" y1="5" x2="12" y2="19"/>'
                    '<line x1="5" y1="12" x2="19" y2="12"/></svg>'
                ),
                rx.text("Add Transaction", style={
                    "font_size": "12px", "font_weight": "600",
                    "letter_spacing": "0.08em", "text_transform": "uppercase",
                    "font_family": MONO,
                }),
                spacing="2",
            ),
            on_click=AppState.open_sheet,
            role="button",
            tab_index=0,
            aria_label="Add a new transaction",
            style={
                "margin": "0 10px 10px",
                "padding": "11px",
                "background": ACCENT,
                "color": "#fff",
                "border_radius": "8px",
                "cursor": "pointer",
                "display": "flex",
                "align_items": "center",
                "justify_content": "center",
                "gap": "8px",
                "box_shadow": f"0 4px 16px {ACCENT_GLOW}",
                "_hover": {"opacity": "0.9", "box_shadow": f"0 6px 22px {ACCENT_GLOW}"},
                "_active": {"transform": "scale(0.97)"},
                "_focus_visible": {"outline": "2px solid #fff", "outline_offset": "2px"},
            },
        ),

        # ── User footer ───────────────────────────────────
        rx.hstack(
            # Avatar circle
            rx.box(
                rx.text("JD", style={
                    "font_size": "10px", "font_weight": "700",
                    "color": "#fff", "line_height": "1",
                }),
                style={
                    "width": "28px", "height": "28px", "border_radius": "50%",
                    "background": f"linear-gradient(135deg, {ACCENT}, #8B5CF6)",
                    "display": "flex", "align_items": "center", "justify_content": "center",
                    "flex_shrink": "0",
                },
            ),
            rx.text(
                AppState.user_email,
                style={
                    "font_size": "11px", "color": "rgba(255,255,255,0.28)",
                    "flex": "1", "overflow": "hidden",
                    "text_overflow": "ellipsis", "white_space": "nowrap",
                },
            ),
            rx.box(
                "↪",
                on_click=AppState.logout,
                role="button", tab_index=0, aria_label="Sign out",
                style={
                    "font_size": "14px", "color": "rgba(255,255,255,0.22)",
                    "cursor": "pointer", "padding": "4px 6px", "border_radius": "4px",
                    "_hover": {"color": "rgba(255,255,255,0.55)"},
                    "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
                },
            ),
            style={
                "padding": "10px 12px 14px",
                "border_top": f"1px solid {BORDER}",
                "align_items": "center",
                "gap": "8px",
            },
        ),

        class_name="sidebar-fixed",
        role="complementary",
        aria_label="Sidebar",
        style={"font_family": SANS},
    )
