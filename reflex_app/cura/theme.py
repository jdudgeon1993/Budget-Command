# ── Electric theme — color tokens ────────────────────────────────────────────

# Base backgrounds
BG      = "#0C0C10"                       # body + sidebar (unified dark canvas)
BG2     = "rgba(255,255,255,0.05)"        # glass card surface
BG3     = "rgba(255,255,255,0.08)"        # glass hover / section header tint
BORDER  = "rgba(255,255,255,0.08)"        # default border
BORDER2 = "rgba(255,255,255,0.14)"        # emphasized border / focus ring base

# Text
TEXT    = "#FFFFFF"
TEXT2   = "#9090B8"
TEXT3   = "#606088"

# Semantic
GREEN   = "#30D158"
RED     = "#FF453A"
AMBER   = "#FF9F0A"
ACCENT  = "#BF5AF2"   # Electric violet
VIOLET  = "#BF5AF2"   # alias

# Glow values used in box-shadow and radial-gradient
ACCENT_GLOW = "rgba(191,90,242,0.38)"
GREEN_GLOW  = "rgba(48,209,88,0.25)"
RED_GLOW    = "rgba(255,69,58,0.25)"

# Shadows
SHADOW_SM    = "0 1px 0 rgba(255,255,255,0.05), 0 4px 24px rgba(191,90,242,0.08)"
SHADOW_MD    = "0 8px 40px rgba(191,90,242,0.18)"
SHADOW_GLASS = "inset 0 1px 0 rgba(255,255,255,0.08)"

# Typography
SANS  = "'Inter', system-ui, sans-serif"
MONO  = "'JetBrains Mono', monospace"
DISP  = "'Inter', system-ui, sans-serif"   # kept for compat; no Bebas Neue in Electric

# Layout
SIDEBAR_W = "220px"
NAV_H     = "62px"
HDR_H     = "52px"

# ── Shared style dicts ────────────────────────────────────────────────────────

BODY_STYLE = {
    "background": BG,
    "color": TEXT,
    "font_family": SANS,
    "font_size": "14px",
    "min_height": "100vh",
    "overflow_x": "hidden",
}

# Glass card — the universal surface in Electric
GLASS_CARD = {
    "background": BG2,
    "border": f"1px solid {BORDER}",
    "border_radius": "12px",
    "box_shadow": SHADOW_SM,
}

# Inset tint — used for day-card headers, KPI labels, etc.
GLASS_INSET = {
    "background": BG3,
    "border_radius": "8px",
}

# Primary glow button
GLOW_BTN = {
    "background": ACCENT,
    "color": "#fff",
    "border": "none",
    "border_radius": "8px",
    "cursor": "pointer",
    "box_shadow": f"0 4px 16px {ACCENT_GLOW}",
    "_hover": {"opacity": "0.9", "box_shadow": f"0 6px 24px {ACCENT_GLOW}"},
    "_active": {"transform": "scale(0.97)"},
    "_focus_visible": {"outline": f"2px solid {ACCENT}", "outline_offset": "2px"},
}

# Form input — used in modals and login/signup
INPUT_STYLE = {
    "background": "rgba(255,255,255,0.06)",
    "border": f"1px solid {BORDER}",
    "border_radius": "8px",
    "color": TEXT,
    "font_family": SANS,
    "font_size": "14px",
    "padding": "10px 12px",
    "outline": "none",
    "_focus": {
        "border_color": ACCENT,
        "box_shadow": "0 0 0 3px rgba(191,90,242,0.18)",
        "outline": "none",
    },
    "_placeholder": {"color": TEXT3},
}

# Legacy alias — components still reference PANEL_STYLE
PANEL_STYLE = {
    "background": BG2,
    "border": f"1px solid {BORDER}",
    "border_radius": "8px",
    "padding": "14px",
    "margin_bottom": "6px",
    "box_shadow": SHADOW_SM,
}

MONO_STYLE = {"font_family": MONO}


def pill_color(pill: str) -> str:
    return {
        "paid":       GREEN,
        "funded":     GREEN,
        "overfunded": VIOLET,
        "funding":    AMBER,
        "over":       RED,
        "empty":      TEXT3,
    }.get(pill, TEXT3)


def status_badge_style(pill: str) -> dict:
    color = pill_color(pill)
    bg_map = {
        "paid":       "rgba(48,209,88,0.10)",
        "funded":     "rgba(48,209,88,0.10)",
        "overfunded": "rgba(191,90,242,0.12)",
        "funding":    "rgba(255,159,10,0.10)",
        "over":       "rgba(255,69,58,0.10)",
        "empty":      "rgba(255,255,255,0.06)",
    }
    bg = bg_map.get(pill, "rgba(255,255,255,0.06)")
    return {
        "font_family": MONO,
        "font_size": "11px",
        "letter_spacing": "0.07em",
        "text_transform": "uppercase",
        "padding": "2px 8px",
        "border_radius": "20px",
        "color": color,
        "background": bg,
        "white_space": "nowrap",
        "flex_shrink": "0",
    }


GLOBAL_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background: {BG} !important;
  color: {TEXT} !important;
  font-family: {SANS};
  font-size: 14px;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}}

/* Selection */
::selection {{ background: rgba(191,90,242,0.35); color: {TEXT}; }}

/* Tabular nums for all mono elements */
.mono, [style*="JetBrains"] {{ font-variant-numeric: tabular-nums; }}

/* Progress bar fill */
.prog-fill {{
  transition: width 0.4s cubic-bezier(0.16,1,0.3,1);
  box-shadow: 0 0 8px rgba(191,90,242,0.45);
}}

/* ── Glass card utility ─────────────────────────────────── */
.glass-card {{
  background: {BG2};
  border: 1px solid {BORDER};
  border-radius: 12px;
  box-shadow: {SHADOW_SM};
}}

/* ── Bucket card hover lift ─────────────────────────────── */
.bucket-card-el {{
  transition: box-shadow 0.18s ease, border-color 0.18s ease;
}}
.bucket-card-el:hover {{
  box-shadow: 0 8px 32px rgba(191,90,242,0.14);
  border-color: rgba(255,255,255,0.12) !important;
}}

/* ── Focus ring ─────────────────────────────────────────── */
:focus-visible {{
  outline: 2px solid {ACCENT} !important;
  outline-offset: 2px;
  border-radius: 4px;
}}

/* ── Touch target ───────────────────────────────────────── */
.touch-target {{
  min-height: 44px; min-width: 44px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}}

/* ── Scrollbars ─────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: rgba(191,90,242,0.30); border-radius: 2px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(191,90,242,0.55); }}

/* ── Sidebar (desktop fixed) ────────────────────────────── */
.sidebar-fixed {{
  position: fixed !important;
  top: 0; left: 0; bottom: 0;
  width: {SIDEBAR_W};
  z-index: 50;
  display: flex;
  flex-direction: column;
  background: {BG};
  border-right: 1px solid {BORDER};
  overflow-y: auto;
}}

/* ── Main content ───────────────────────────────────────── */
.main-content {{
  margin-left: {SIDEBAR_W};
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: {BG};
}}

/* ── Animations ─────────────────────────────────────────── */
@keyframes modal-in {{
  from {{ opacity: 0; transform: translateY(16px) scale(0.98); }}
  to   {{ opacity: 1; transform: translateY(0)    scale(1); }}
}}
@keyframes backdrop-in {{
  from {{ opacity: 0; }}
  to   {{ opacity: 1; }}
}}
@keyframes fab-pulse {{
  0%,100% {{ box-shadow: 0 4px 18px rgba(191,90,242,0.50); }}
  50%     {{ box-shadow: 0 4px 28px rgba(191,90,242,0.82); }}
}}
@keyframes shimmer {{
  0%   {{ background-position: -200% 0; }}
  100% {{ background-position:  200% 0; }}
}}
@keyframes sheet-in {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

.sheet-backdrop-fx {{ animation: backdrop-in 0.18s ease-out; }}
.sheet-card        {{ animation: modal-in 0.26s cubic-bezier(0.16,1,0.3,1); }}

/* ── Mobile FAB pulse ───────────────────────────────────── */
.mobile-fab {{
  animation: fab-pulse 2.8s ease-in-out infinite;
}}

/* ── Skeleton shimmer ───────────────────────────────────── */
.skeleton {{
  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.04) 25%,
    rgba(255,255,255,0.08) 50%,
    rgba(255,255,255,0.04) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  border-radius: 6px;
}}

/* ── Sheet / modal backdrop ─────────────────────────────── */
.sheet-backdrop {{
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.72);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: backdrop-in 0.18s ease-out;
}}
.sheet-backdrop > * {{ animation: sheet-in 0.22s cubic-bezier(0.16,1,0.3,1); }}
@media (min-width: 768px) {{
  .sheet-backdrop {{ align-items: center; }}
}}

/* ── Mobile responsive ──────────────────────────────────── */
@media (max-width: 767px) {{
  .sidebar-fixed  {{ display: none !important; }}
  .main-content   {{ margin-left: 0 !important; padding-bottom: {NAV_H}; overflow-x: hidden; }}
  .mobile-only    {{ display: flex !important; }}
  .desktop-only   {{ display: none !important; }}
  .split-grid     {{ grid-template-columns: 1fr !important; }}
  .bkt-reorder    {{ display: none !important; }}
  .bkt-name       {{ max-width: 120px !important; flex-shrink: 1 !important; }}
}}
@media (min-width: 768px) {{
  .mobile-only    {{ display: none !important; }}
}}

/* ── Reduced motion ─────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }}
}}

/* ── Interactive element transitions ────────────────────── */
[role="button"] {{ transition: background 0.12s, color 0.12s, opacity 0.12s; }}
"""
