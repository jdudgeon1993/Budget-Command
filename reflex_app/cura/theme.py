# ── Color palette matching the Flask/Cura design system ──────────────────────

BG      = "#0c0c10"
BG2     = "#14141c"
BG3     = "#1c1c25"
BORDER  = "#252535"
BORDER2 = "#3c3c56"
TEXT    = "#f0f0fa"
TEXT2   = "#8282a2"
TEXT3   = "#4e4e6a"
GREEN   = "#34d399"
RED     = "#f87171"
AMBER   = "#fbbf24"
ACCENT  = "#818cf8"
VIOLET  = "#a78bfa"

SANS  = "Rajdhani, system-ui, sans-serif"
MONO  = "'Share Tech Mono', monospace"
DISP  = "'Bebas Neue', sans-serif"

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

PANEL_STYLE = {
    "background": BG2,
    "border": f"1px solid {BORDER}",
    "border_radius": "8px",
    "padding": "14px",
    "margin_bottom": "6px",
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
    return {
        "font_family": MONO,
        "font_size": "9px",
        "letter_spacing": "0.07em",
        "text_transform": "uppercase",
        "padding": "2px 7px",
        "border_radius": "10px",
        "color": color,
        "border": f"1px solid {color}22",
        "background": f"{color}18",
        "white_space": "nowrap",
        "flex_shrink": "0",
    }

GLOBAL_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background: {BG} !important;
  color: {TEXT} !important;
  font-family: {SANS};
  font-size: 14px;
  overflow-x: hidden;
}}

/* Progress bar fill animation */
.prog-fill {{ transition: width 0.35s ease; }}

/* Scrollbars */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER2}; border-radius: 2px; }}

/* Sidebar fixed */
.sidebar-fixed {{
  position: fixed !important;
  top: 0; left: 0; bottom: 0;
  width: {SIDEBAR_W};
  z-index: 50;
  display: flex;
  flex-direction: column;
  background: {BG2};
  border-right: 1px solid {BORDER};
  overflow-y: auto;
}}

/* Main content offset */
.main-content {{
  margin-left: {SIDEBAR_W};
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}}

/* Mobile */
@media (max-width: 767px) {{
  .sidebar-fixed {{ display: none !important; }}
  .main-content {{ margin-left: 0 !important; padding-bottom: {NAV_H}; }}
  .mobile-only {{ display: flex !important; }}
  .desktop-only {{ display: none !important; }}
  .split-grid {{ grid-template-columns: 1fr !important; }}
}}
@media (min-width: 768px) {{
  .mobile-only {{ display: none !important; }}
}}

/* Sheet/Modal */
.sheet-backdrop {{
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}}
@media (min-width: 768px) {{
  .sheet-backdrop {{ align-items: center; }}
}}
"""
