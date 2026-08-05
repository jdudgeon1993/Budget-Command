"""
Cadence design system — one stylesheet, shared by every pillar.

Buckets, Ledger and Forecast all pull their look from here, so a change to a
token or a component ripples across the whole app. Page-specific rules live in
clearly-labelled sections but reuse the same tokens, radii, shadows and pills.

Usage:  from . import theme  →  theme.apply()   (call once per page render)
"""
from nicegui import ui

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800'
    '&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">'
)

CSS = """
:root{
  --bg:#f6f7fb; --card:#ffffff; --ink:#0f1222; --muted:#6b7192;
  --line:#eceef5; --accent:#6366f1; --accent-soft:#eef0ff;
  --pos:#10b981; --pos-soft:#eafaf3; --warn:#f59e0b; --warn-ink:#b7791f;
  --warn-soft:#fff4e5; --neg:#f43f5e; --neg-soft:#fdecec; --violet:#8b5cf6;
  --violet-soft:#f3efff; --info:#3b82f6; --info-soft:#e8f0fe; --info-ink:#2563eb;
  --shadow:0 1px 2px rgba(16,18,34,.04),0 8px 24px rgba(16,18,34,.06);
  --shadow-lift:0 2px 4px rgba(16,18,34,.05),0 14px 34px rgba(16,18,34,.10);
}
body{background:var(--bg);font-family:'Inter',-apple-system,'Segoe UI',Roboto,sans-serif;color:var(--ink)}
.mono{font-family:'JetBrains Mono',ui-monospace,monospace;font-feature-settings:"tnum"}

/* ── shell + top nav (shared) ─────────────────────────────────────────────── */
.cd-shell{max-width:960px;margin:0 auto;padding:0 20px 80px}
.cd-top{display:flex;align-items:center;gap:18px;padding:22px 4px 10px}
.cd-logo{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--violet));
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;box-shadow:0 6px 16px rgba(99,102,241,.35)}
.cd-brand{font-weight:800;font-size:19px;letter-spacing:-.02em}
.cd-nav{display:flex;gap:4px;margin-left:8px}
.cd-navbtn{font-size:13px;font-weight:600;color:var(--muted);padding:7px 14px;border-radius:9px;cursor:pointer;transition:.15s}
.cd-navbtn:hover{color:var(--ink);background:var(--line)}
.cd-navbtn.active{color:var(--accent);background:var(--accent-soft)}
.cd-navbtn.active:hover{color:var(--accent);background:var(--accent-soft)}
.cd-navbtn.soon{opacity:.5;cursor:default}
.cd-navbtn.soon:hover{background:none;color:var(--muted)}
.cd-auth{margin-left:auto;display:flex;align-items:center;gap:10px;font-size:12px;color:var(--muted)}
.cd-chip{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:4px 9px;border-radius:20px;background:var(--accent-soft);color:var(--accent)}
.cd-link{color:var(--muted);cursor:pointer;text-decoration:underline;font-weight:500}
.cd-gear{font-size:18px;cursor:pointer;color:var(--muted);line-height:1;transition:.15s;user-select:none}
.cd-gear:hover{color:var(--ink);transform:rotate(30deg)}
.cd-gear.active{color:var(--accent)}

/* ── one-number money header (Buckets) ────────────────────────────────────── */
.cd-money{display:grid;grid-template-columns:auto 1fr;gap:28px;align-items:center;
  background:var(--card);border:1px solid var(--line);border-radius:20px;padding:22px 26px;
  box-shadow:var(--shadow);margin:8px 0 22px}
.cd-money-lbl{font-size:11px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--accent)}
.cd-money-big{font-size:44px;font-weight:800;letter-spacing:-.03em;line-height:1.05;margin:4px 0 2px}
.cd-money-sub{font-size:12px;color:var(--muted)}
.cd-segbar{display:flex;height:12px;border-radius:7px;overflow:hidden;background:var(--line)}
.cd-segbar span{display:block;height:100%}
.cd-segbar span+span{box-shadow:inset 2px 0 0 #fff}
.cd-legend{display:flex;flex-wrap:wrap;gap:16px;margin-top:12px}
.cd-legend span{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:var(--muted)}
.cd-legend b{color:var(--ink);font-weight:700}
.cd-legend i{width:9px;height:9px;border-radius:3px;display:inline-block}

/* ── action bar + buttons (shared) ────────────────────────────────────────── */
.cd-actionbar{display:flex;align-items:center;margin:6px 4px 18px}
.cd-newbtn{font-size:13px;font-weight:700;color:#fff;background:linear-gradient(135deg,var(--accent),var(--violet));
  padding:9px 16px;border-radius:10px;cursor:pointer;box-shadow:0 4px 14px rgba(99,102,241,.32)}
.cd-newbtn:hover{filter:brightness(1.05)}
.cd-distbtn{font-size:13px;font-weight:700;color:var(--accent);background:var(--accent-soft);border:1px solid #dcdefb;
  padding:8px 15px;border-radius:10px;cursor:pointer;margin-left:10px;display:inline-flex;align-items:center;gap:7px}
.cd-distbtn.hot{color:var(--warn-ink);background:var(--warn-soft);border-color:#f6e2c0}
.cd-hint{margin-left:auto;font-size:12px;color:var(--muted)}

/* ── distribute sheet (Buckets) ───────────────────────────────────────────── */
.cd-drow{display:flex;align-items:center;gap:12px;padding:11px 2px;border-top:1px solid var(--line)}
.cd-drow:first-of-type{border-top:none}
.cd-dname{font-weight:600;font-size:13px}
.cd-dmeta{font-size:11px;color:var(--muted);margin-top:1px}
.cd-dleft{position:sticky;bottom:0;background:var(--card);padding:12px 0 2px;border-top:1px solid var(--line);
  display:flex;align-items:center;font-size:13px;font-weight:600}

/* ── category groups + envelope cards (Buckets) ───────────────────────────── */
.cd-cat{margin-bottom:22px}
.cd-cat-hd{display:flex;align-items:center;gap:10px;padding:0 4px 10px}
.cd-dot{width:9px;height:9px;border-radius:50%}
.cd-cat-name{font-weight:700;font-size:15px}
.cd-cat-avail{margin-left:auto;font-size:13px;color:var(--muted)}
.cd-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.cd-env{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 16px 14px;
  box-shadow:var(--shadow);transition:transform .12s,box-shadow .12s;cursor:pointer}
.cd-env:hover{transform:translateY(-2px);box-shadow:var(--shadow-lift);border-color:#dfe1ee}
.cd-env-top{display:flex;align-items:baseline;gap:8px}
.cd-env-name{font-weight:600;font-size:14px}
.cd-badge{font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;border-radius:20px;margin-left:auto}
.cd-badge.goal{background:#f3efff;color:var(--violet)}
.cd-badge.vault{background:var(--pos-soft);color:var(--pos)}
.cd-avail{font-size:22px;font-weight:700;letter-spacing:-.02em;margin:8px 0 2px}
.cd-sub{font-size:11px;color:var(--muted)}
.cd-bar{height:7px;border-radius:6px;background:var(--line);overflow:hidden;margin:12px 0 6px}
.cd-bar-fill{height:100%;border-radius:6px;transition:width .35s cubic-bezier(.2,.8,.2,1)}
.cd-tap{font-size:11px;color:var(--accent);font-weight:600;margin-top:8px}

/* ── status badges (Buckets card corner) — one colour language ────────────── */
.cd-pill{font-size:9px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:2px 7px;border-radius:20px;margin-left:auto;white-space:nowrap}
.cd-pill.green{background:var(--pos-soft);color:var(--pos)}
.cd-pill.amber{background:var(--warn-soft);color:var(--warn-ink)}
.cd-pill.red{background:var(--neg-soft);color:var(--neg)}
.cd-pill.purple{background:var(--violet-soft);color:var(--violet)}
.cd-pill.blue{background:var(--info-soft);color:var(--info-ink)}
/* flex buckets: a flat marker instead of a progress bar */
.cd-flexbar{height:7px;border-radius:6px;margin:12px 0 6px;
  background:repeating-linear-gradient(90deg,var(--info-soft) 0 8px,transparent 8px 14px)}
.cd-env.is-handled{opacity:.55}
.cd-env.is-handled .cd-pill.green{opacity:1}

/* ── bottom sheet + form bits (shared by every sheet) ─────────────────────── */
.cd-sheet{width:100%;max-width:560px;margin:0 auto;padding:14px 22px 20px !important;
  border-radius:22px 22px 0 0 !important;box-shadow:0 -20px 60px rgba(16,18,34,.25) !important;
  max-height:92vh;overflow-y:auto}
.cd-hdl{width:40px;height:4px;border-radius:3px;background:var(--line);margin:0 auto 14px}
.cd-seclbl{font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:18px 0 8px}
.cdm-title{font-size:18px;font-weight:800;letter-spacing:-.01em}
.cdm-sub{font-size:12px;color:var(--muted);margin:2px 0 14px}
.cdm-input{max-width:150px}
.cd-half{flex:1 1 46%;min-width:150px}

/* ── segmented control (shared: e.g. Ledger tx type) ──────────────────────── */
.cd-seg{display:flex;width:100%;gap:4px;background:var(--line);padding:4px;border-radius:12px;margin-top:6px}
.cd-seg .cd-segopt{flex:1;text-align:center;font-size:13px;font-weight:600;color:var(--muted);
  padding:8px 0;border-radius:9px;cursor:pointer;transition:.15s}
.cd-seg .cd-segopt.on{background:var(--card);color:var(--ink);box-shadow:var(--shadow)}
.cd-seg .cd-segopt.on.out{color:var(--neg)}
.cd-seg .cd-segopt.on.in{color:var(--pos)}
.cd-seg .cd-segopt.on.refund{color:var(--accent)}

/* ── Ledger ───────────────────────────────────────────────────────────────── */
.cd-led-hd{display:flex;gap:14px;margin:8px 0 18px}
.cd-led-stat{flex:1;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:15px 18px;box-shadow:var(--shadow)}
.cd-led-stat .l{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.cd-led-stat .v{font-size:24px;font-weight:800;letter-spacing:-.02em;margin-top:3px}
.cd-led-search{margin:0 0 14px}
/* year header + collapsible month cards */
.cd-year{font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:20px 4px 10px}
.cd-month{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);margin-bottom:12px;overflow:hidden}
.cd-month-hd{display:flex;align-items:center;gap:10px;padding:14px 16px;cursor:pointer;user-select:none}
.cd-month-hd:hover{background:#fafbff}
.cd-month-chev{width:14px;text-align:center;color:var(--muted);transition:transform .18s;font-size:11px}
.cd-month.open .cd-month-chev{transform:rotate(90deg)}
.cd-month-nm{font-weight:700;font-size:14px}
.cd-month-meta{font-size:11px;color:var(--muted)}
.cd-month-bal{margin-left:auto;font-weight:700;font-size:14px}
.cd-month-body{padding:2px 14px 12px}
.cd-month-body .cd-txcard{border:none;box-shadow:none;border-radius:0;background:transparent}
.cd-month-body .cd-daygrp:first-child .cd-daylbl{padding-top:2px}
.cd-daygrp{margin-bottom:16px}
.cd-daylbl{padding:0 4px 8px;font-size:13px;overflow:hidden}
.cd-daylbl b{font-weight:700}
.cd-daylbl .d{margin-left:8px;font-size:11px;color:var(--muted)}
.cd-daylbl .t{float:right;font-size:11px;color:var(--muted);font-weight:600}
.cd-txcard{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);overflow:hidden}
.cd-tx{display:grid;grid-template-columns:36px 1fr auto;gap:12px;align-items:center;padding:12px 16px;cursor:pointer;transition:background .12s}
.cd-tx:hover{background:#fafbff}
.cd-tx+.cd-tx{border-top:1px solid var(--line)}
.cd-tx-ic{width:36px;height:36px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700}
.cd-tx-ic.out{background:var(--neg-soft);color:var(--neg)}
.cd-tx-ic.in{background:var(--pos-soft);color:var(--pos)}
.cd-tx-ic.refund{background:var(--accent-soft);color:var(--accent)}
.cd-tx-name{font-weight:600;font-size:14px}
.cd-tx-meta{font-size:11px;color:var(--muted);margin-top:2px;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.cd-tx-tag{display:inline-flex;align-items:center;gap:5px}
.cd-tx-tag i{width:7px;height:7px;border-radius:50%;display:inline-block}
.cd-tx-amt{font-size:15px;font-weight:700;letter-spacing:-.01em;text-align:right;white-space:nowrap}
.cd-tx-amt.pos{color:var(--pos)}
.cd-tx-amt.neg{color:var(--ink)}
.cd-empty{background:var(--card);border:1px dashed var(--line);border-radius:16px;padding:38px 20px;text-align:center;color:var(--muted)}
.cd-empty .big{font-size:15px;font-weight:700;color:var(--ink);margin-bottom:4px}

/* ── Settings ─────────────────────────────────────────────────────────────── */
.cd-set-title{font-size:24px;font-weight:800;letter-spacing:-.02em;margin:6px 2px 2px}
.cd-setcard{background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);padding:16px 18px;margin-bottom:16px}
.cd-set-seclbl{font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:2px 2px 10px}
.cd-setrow{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center;padding:11px 8px;border-radius:12px;border-top:1px solid var(--line);cursor:pointer;transition:background .12s}
.cd-setrow:first-of-type{border-top:none}
.cd-setrow:hover{background:#fafbff}
.cd-setrow.off{opacity:.5}
.cd-set-ic{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;background:var(--pos-soft);color:var(--pos)}
.cd-set-name{font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cd-set-meta{font-size:11px;color:var(--muted);margin-top:2px;display:flex;align-items:center;gap:6px}
.cd-set-val{font-weight:700;font-size:14px;white-space:nowrap}
.cd-toggle{font-size:10px;font-weight:800;letter-spacing:.05em;padding:5px 10px;border-radius:8px;background:var(--line);color:var(--muted);cursor:pointer;user-select:none;min-width:44px;text-align:center}
.cd-toggle.on{background:var(--pos-soft);color:var(--pos)}
.cd-rule-badge{font-size:9px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:2px 6px;border-radius:6px}
.cd-rule-badge.internal{background:var(--accent-soft);color:var(--accent)}
.cd-rule-badge.external{background:var(--warn-soft);color:var(--warn-ink)}
.cd-tally{font-size:12px;color:var(--muted);padding:0 2px 12px}
.cd-tally b{color:var(--ink)}
.cd-set-add{display:inline-block;margin-top:10px;font-size:13px;font-weight:700;color:var(--accent);background:var(--accent-soft);padding:8px 14px;border-radius:10px;cursor:pointer}
.cd-set-add:hover{filter:brightness(.97)}
"""


def apply() -> None:
    """Inject fonts + the shared stylesheet into the current page's <head>."""
    ui.add_head_html(FONTS + f"<style>{CSS}</style>")
