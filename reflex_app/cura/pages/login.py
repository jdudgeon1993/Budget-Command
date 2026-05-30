"""Login page — replaces login.html."""

import reflex as rx
from ..state import AppState
from ..theme import BG, BG2, BG3, BORDER, BORDER2, TEXT, TEXT2, TEXT3, ACCENT, RED, MONO, SANS


def _input(name: str, label: str, type_: str = "text", placeholder: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, style={"font_size": "11px", "color": TEXT2, "letter_spacing": "0.06em"}),
        rx.input(
            name=name,
            type=type_,
            placeholder=placeholder,
            style={
                "width": "100%", "background": BG3, "border": f"1px solid {BORDER}",
                "border_radius": "8px", "color": TEXT, "font_family": MONO,
                "font_size": "14px", "padding": "11px 14px", "outline": "none",
                "_focus": {"border_color": ACCENT},
            },
        ),
        gap="5px", align_items="stretch",
    )


def login_page() -> rx.Component:
    return rx.center(
        rx.box(
            # Logo
            rx.vstack(
                rx.text("CURA", style={"font_size": "24px", "font_weight": "700",
                                        "letter_spacing": "0.2em", "color": ACCENT,
                                        "text_align": "center"}),
                rx.text("Budget Command", style={"font_size": "11px", "color": TEXT3,
                                                  "letter_spacing": "0.1em", "text_align": "center"}),
                gap="4px", margin_bottom="28px",
            ),

            # Error message
            rx.cond(
                AppState.auth_error != "",
                rx.box(
                    AppState.auth_error,
                    style={
                        "background": f"{RED}18", "border": f"1px solid {RED}44",
                        "border_radius": "8px", "padding": "10px 14px",
                        "color": RED, "font_size": "12px", "margin_bottom": "16px",
                        "font_family": MONO,
                    },
                ),
                rx.box(),
            ),

            # Form
            rx.form(
                rx.vstack(
                    _input("email",    "Email",    "email",    "you@example.com"),
                    _input("password", "Password", "password", "••••••••"),
                    rx.el.button(
                        rx.cond(AppState.is_loading, "Signing in…", "Sign In"),
                        type="submit",
                        disabled=AppState.is_loading,
                        style={
                            "width": "100%", "padding": "12px",
                            "background": rx.cond(AppState.is_loading, BORDER, ACCENT),
                            "color": "#fff", "border": "none", "border_radius": "8px",
                            "font_family": SANS, "font_size": "13px",
                            "letter_spacing": "0.08em", "cursor": "pointer",
                            "text_align": "center", "margin_top": "4px",
                            "box_shadow": f"0 4px 14px {ACCENT}4d",
                            "_hover": {"opacity": "0.9"},
                        },
                    ),
                    gap="14px",
                ),
                on_submit=AppState.login,
            ),

            style={
                "width": "100%", "max_width": "380px",
                "background": BG2, "border": f"1px solid {BORDER}",
                "border_radius": "14px", "padding": "36px 32px",
                "font_family": SANS,
            },
        ),
        style={"background": BG, "min_height": "100vh"},
    )
