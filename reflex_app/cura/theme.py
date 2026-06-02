# ── Color palette matching the Flask/Cura design system ──────────────────────

BG      = "#0c0c10"
BG2     = "#14141c"
BG3     = "#1c1c25"
BORDER  = "#252535"
BORDER2 = "#3c3c56"
TEXT    = "#f0f0fa"
TEXT2   = "#8282a2"
TEXT3   = "#6868a2"
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
        "font_size": "11px",
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
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}}

/* Text selection picks up the accent instead of the browser default */
::selection {{ background: {ACCENT}44; color: {TEXT}; }}

/* Progress bar fill animation */
.prog-fill {{ transition: width 0.35s ease; }}

/* Tabular figures so money columns line up cleanly */
.mono, [style*="Share Tech Mono"] {{ font-variant-numeric: tabular-nums; }}

/* Modal / sheet entrance — gentle fade + lift */
@keyframes sheet-in {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes backdrop-in {{
  from {{ opacity: 0; }}
  to   {{ opacity: 1; }}
}}
.sheet-backdrop-fx {{ animation: backdrop-in 0.18s ease-out; }}
.sheet-card {{ animation: sheet-in 0.24s cubic-bezier(0.16, 1, 0.3, 1); }}

/* Focus-visible ring — keyboard users see a clear outline on any focusable element */
:focus-visible {{
  outline: 2px solid {ACCENT} !important;
  outline-offset: 2px;
  border-radius: 4px;
}}

/* Touch-target utility — wrap small clickable things to meet 44px minimum */
.touch-target {{
  min-height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}}

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
  animation: backdrop-in 0.18s ease-out;
}}
.sheet-backdrop > * {{ animation: sheet-in 0.22s cubic-bezier(0.16, 1, 0.3, 1); }}
@media (min-width: 768px) {{
  .sheet-backdrop {{ align-items: center; }}
}}

/* Respect users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }}
}}
"""
