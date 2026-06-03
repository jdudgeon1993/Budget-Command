"""Signup page — Electric theme."""

import reflex as rx
from ..state import AppState
from ..theme import (BG, BG2, BG3, BORDER, TEXT, TEXT2, TEXT3,
                     ACCENT, ACCENT_GLOW, RED, MONO, SANS,
                     SHADOW_MD, INPUT_STYLE, GLOBAL_CSS)

_BRAND_ICON = (
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
    '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
    '<rect x="3" y="14" width="7" height="7" rx="1.5"/>'
    '<rect x="14" y="14" width="7" height="7" rx="1.5"/>'
    '</svg>'
)


def _input(name: str, label: str, type_: str = "text", placeholder: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, style={
            "font_size": "11px", "color": TEXT3,
            "letter_spacing": "0.1em", "text_transform": "uppercase",
            "font_family": MONO,
        }),
        rx.input(
            name=name,
            type=type_,
            placeholder=placeholder,
            style={"width": "100%", **INPUT_STYLE},
        ),
        gap="5px", align_items="stretch",
    )


def signup_page() -> rx.Component:
    return rx.box(
        rx.html(f"<style>{GLOBAL_CSS}</style>"),
        rx.center(
            rx.box(
                # Brand mark
                rx.vstack(
                    rx.box(
                        rx.html(_BRAND_ICON),
                        style={
                            "width": "44px", "height": "44px",
                            "background": ACCENT, "border_radius": "12px",
                            "display": "flex", "align_items": "center",
                            "justify_content": "center",
                            "box_shadow": f"0 4px 18px {ACCENT_GLOW}",
                            "margin_bottom": "2px",
                        },
                    ),
                    rx.text("CURA", style={
                        "font_size": "20px", "font_weight": "700",
                        "letter_spacing": "0.18em", "color": "#fff",
                        "text_transform": "uppercase", "line_height": "1",
                    }),
                    rx.text("Create your account", style={
                        "font_size": "11px", "color": "rgba(255,255,255,0.28)",
                        "letter_spacing": "0.08em", "text_transform": "uppercase",
                    }),
                    gap="6px", align_items="center", margin_bottom="28px",
                ),

                # Error
                rx.cond(
                    AppState.auth_error != "",
                    rx.box(
                        AppState.auth_error,
                        style={
                            "background": "rgba(255,69,58,0.10)",
                            "border": "1px solid rgba(255,69,58,0.30)",
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
                        _input("email",    "Email",            "email",    "you@example.com"),
                        _input("password", "Password",         "password", "Min 6 characters"),
                        _input("confirm",  "Confirm Password", "password", "Repeat password"),
                        rx.el.button(
                            rx.cond(AppState.is_loading, "Creating account…", "Create Account"),
                            type="submit",
                            disabled=AppState.is_loading,
                            style={
                                "width": "100%", "padding": "13px",
                                "background": rx.cond(AppState.is_loading,
                                                      "rgba(255,255,255,0.08)", ACCENT),
                                "color": "#fff", "border": "none",
                                "border_radius": "8px", "font_family": SANS,
                                "font_size": "13px", "font_weight": "600",
                                "letter_spacing": "0.08em", "cursor": "pointer",
                                "text_align": "center", "margin_top": "4px",
                                "box_shadow": f"0 4px 18px {ACCENT_GLOW}",
                                "_hover": {"opacity": "0.9",
                                           "box_shadow": f"0 6px 24px {ACCENT_GLOW}"},
                                "_active": {"transform": "scale(0.98)"},
                            },
                        ),
                        gap="14px",
                    ),
                    on_submit=AppState.signup,
                ),

                # Sign in link
                rx.text(
                    "Already have an account? ",
                    rx.el.a("Sign in", href="/login",
                            style={"color": ACCENT, "text_decoration": "none",
                                   "_hover": {"text_decoration": "underline"}}),
                    style={"font_size": "12px", "color": TEXT3,
                           "text_align": "center", "margin_top": "20px"},
                ),

                style={
                    "width": "100%", "max_width": "380px",
                    "background": BG2, "border": f"1px solid {BORDER}",
                    "border_radius": "16px", "padding": "40px 32px",
                    "font_family": SANS,
                    "box_shadow": SHADOW_MD,
                },
            ),
            style={"min_height": "100vh", "padding": "24px"},
        ),
        style={"background": BG, "min_height": "100vh"},
    )
