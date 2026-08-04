"""
Cadence — a fully-live, stay-in-place budgeting app built on NiceGUI.

Run:  python -m cadence.main   (serves on :8110)

No hx-get / hx-target / hx-swap anywhere. You mutate Python state; the pieces
that depend on it re-render in place over a WebSocket. Scroll and focus never
jump.
"""
import os
from nicegui import ui
from .store import Store

BRAND = "Cadence"          # rename here — it's the only place the name lives
PORT = int(os.environ.get("PORT", 8110))   # Railway injects $PORT


def money(v: float) -> str:
    return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"


def _theme() -> None:
    ui.add_head_html("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
    <style>
      :root{
        --bg:#f6f7fb; --card:#ffffff; --ink:#0f1222; --muted:#6b7192;
        --line:#eceef5; --accent:#6366f1; --accent-soft:#eef0ff;
        --pos:#10b981; --warn:#f59e0b; --neg:#f43f5e; --violet:#8b5cf6;
        --shadow:0 1px 2px rgba(16,18,34,.04),0 8px 24px rgba(16,18,34,.06);
      }
      body{background:var(--bg);
        font-family:'Inter',-apple-system,'Segoe UI',Roboto,sans-serif;color:var(--ink)}
      .mono{font-family:'JetBrains Mono',ui-monospace,monospace;font-feature-settings:"tnum"}
      .cd-shell{max-width:960px;margin:0 auto;padding:0 20px 80px}
      /* header */
      .cd-top{display:flex;align-items:center;gap:18px;padding:22px 4px 10px}
      .cd-logo{width:34px;height:34px;border-radius:10px;
        background:linear-gradient(135deg,var(--accent),var(--violet));
        display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;
        box-shadow:0 6px 16px rgba(99,102,241,.35)}
      .cd-brand{font-weight:800;font-size:19px;letter-spacing:-.02em}
      .cd-nav{display:flex;gap:4px;margin-left:8px}
      .cd-navbtn{font-size:13px;font-weight:600;color:var(--muted);padding:7px 14px;
        border-radius:9px;cursor:pointer;transition:.15s}
      .cd-navbtn.active{color:var(--accent);background:var(--accent-soft)}
      .cd-navbtn.soon{opacity:.5;cursor:default}
      /* hero */
      .cd-hero{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:14px;margin:8px 0 26px}
      .cd-stat{background:var(--card);border:1px solid var(--line);border-radius:18px;
        padding:18px 20px;box-shadow:var(--shadow)}
      .cd-stat.primary{background:linear-gradient(135deg,#5b5ff0,#7c6bf5);border:none;color:#fff;
        box-shadow:0 10px 30px rgba(99,102,241,.35)}
      .cd-stat-lbl{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
        opacity:.75}
      .cd-stat.primary .cd-stat-lbl{opacity:.85}
      .cd-stat-val{font-size:30px;font-weight:700;letter-spacing:-.02em;margin-top:6px}
      .cd-stat-sub{font-size:12px;opacity:.8;margin-top:2px}
      /* category */
      .cd-cat{margin-bottom:22px}
      .cd-cat-hd{display:flex;align-items:center;gap:10px;padding:0 4px 10px}
      .cd-dot{width:9px;height:9px;border-radius:50%}
      .cd-cat-name{font-weight:700;font-size:15px}
      .cd-cat-avail{margin-left:auto;font-size:13px;color:var(--muted)}
      .cd-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
      /* envelope card */
      .cd-env{background:var(--card);border:1px solid var(--line);border-radius:16px;
        padding:16px 16px 14px;box-shadow:var(--shadow);transition:transform .12s,box-shadow .12s}
      .cd-env:hover{transform:translateY(-2px);box-shadow:0 2px 4px rgba(16,18,34,.05),0 14px 34px rgba(16,18,34,.10)}
      .cd-env-top{display:flex;align-items:baseline;gap:8px}
      .cd-env-name{font-weight:600;font-size:14px}
      .cd-badge{font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
        padding:2px 7px;border-radius:20px;margin-left:auto}
      .cd-badge.goal{background:#f3efff;color:var(--violet)}
      .cd-badge.vault{background:#eafaf3;color:var(--pos)}
      .cd-avail{font-size:22px;font-weight:700;letter-spacing:-.02em;margin:8px 0 2px}
      .cd-sub{font-size:11px;color:var(--muted)}
      .cd-bar{height:7px;border-radius:6px;background:var(--line);overflow:hidden;margin:12px 0 12px}
      .cd-bar-fill{height:100%;border-radius:6px;transition:width .35s cubic-bezier(.2,.8,.2,1)}
      .cd-fund{display:flex;gap:7px}
      .cd-fbtn{flex:1;font-size:12px;font-weight:600;border-radius:9px;padding:7px 0;text-align:center;
        cursor:pointer;border:1px solid var(--line);color:var(--muted);transition:.14s;user-select:none}
      .cd-fbtn:hover{border-color:var(--accent);color:var(--accent);background:var(--accent-soft)}
    </style>
    """)


@ui.page("/")
def index():
    _theme()
    store = Store()

    with ui.element("div").classes("cd-shell"):
        # ── header ────────────────────────────────────────────────────────────
        with ui.element("div").classes("cd-top"):
            ui.html(f'<div class="cd-logo">C</div>')
            ui.html(f'<div class="cd-brand">{BRAND}</div>')
            with ui.element("div").classes("cd-nav"):
                ui.html('<div class="cd-navbtn active">Buckets</div>')
                ui.html('<div class="cd-navbtn soon">Ledger</div>')
                ui.html('<div class="cd-navbtn soon">Forecast</div>')

        # ── hero metrics (re-renders live on any change) ──────────────────────
        @ui.refreshable
        def hero():
            m = store.metrics()
            with ui.element("div").classes("cd-hero"):
                _stat("Unallocated", m["unallocated"], primary=True,
                      sub="Money without a job yet — assign it all")
                _stat("Ready to Spend", m["ready_to_spend"], sub="Unassigned + what's in your buckets")
                _stat("Available Balance", m["available_balance"], sub="Real cash in the bank")

        # ── buckets (re-renders live on any change) ───────────────────────────
        @ui.refreshable
        def buckets():
            for g in store.groups():
                with ui.element("div").classes("cd-cat"):
                    with ui.element("div").classes("cd-cat-hd"):
                        ui.html(f'<span class="cd-dot" style="background:{g["color"]}"></span>')
                        ui.html(f'<span class="cd-cat-name">{g["name"]}</span>')
                        ui.html(f'<span class="cd-cat-avail">{money(g["available"])} available</span>')
                    with ui.element("div").classes("cd-grid"):
                        for r in g["rows"]:
                            _envelope(r)

        def adjust(eid: str, delta: float):
            store.fund(eid, delta) if delta > 0 else store.defund(eid, -delta)
            hero.refresh()
            buckets.refresh()

        def _envelope(r: dict):
            with ui.element("div").classes("cd-env"):
                with ui.element("div").classes("cd-env-top"):
                    ui.html(f'<span class="cd-env-name">{r["name"]}</span>')
                    if r["type"] in ("goal", "vault"):
                        ui.html(f'<span class="cd-badge {r["type"]}">{r["type"]}</span>')
                av_color = "var(--neg)" if r["available"] < 0 else "var(--ink)"
                ui.html(f'<div class="cd-avail" style="color:{av_color}">{money(r["available"])}'
                        f'<span class="cd-sub" style="font-weight:500"> available</span></div>')
                if r["type"] == "spend":
                    sub = f'{money(r["spent"])} spent of {money(r["funded"])} funded'
                    fill = ("var(--neg)" if r["pct"] >= 1 else
                            "var(--warn)" if r["pct"] >= 0.85 else "var(--pos)")
                else:
                    sub = f'{money(r["funded"])} of {money(r["target"])} goal'
                    fill = "var(--violet)"
                ui.html(f'<div class="cd-sub">{sub}</div>')
                ui.html(f'<div class="cd-bar"><div class="cd-bar-fill" '
                        f'style="width:{r["pct"]*100:.0f}%;background:{fill}"></div></div>')
                with ui.element("div").classes("cd-fund"):
                    minus = ui.html('<div class="cd-fbtn">− $50</div>')
                    minus.on("click", lambda _, e=r["id"]: adjust(e, -50))
                    plus = ui.html('<div class="cd-fbtn">＋ $50</div>')
                    plus.on("click", lambda _, e=r["id"]: adjust(e, 50))

        def _stat(label: str, value: float, primary: bool = False, sub: str = ""):
            cls = "cd-stat primary" if primary else "cd-stat"
            with ui.element("div").classes(cls):
                ui.html(f'<div class="cd-stat-lbl">{label}</div>')
                ui.html(f'<div class="cd-stat-val mono">{money(value)}</div>')
                if sub:
                    ui.html(f'<div class="cd-stat-sub">{sub}</div>')

        hero()
        buckets()


def run():
    ui.run(host="0.0.0.0", port=PORT, title=BRAND, reload=False, show=False,
           favicon="🪙", storage_secret=os.environ.get("SECRET_KEY", "cadence-dev-secret"))


if __name__ in {"__main__", "__mp_main__"}:
    run()
