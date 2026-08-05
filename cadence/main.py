"""
Cadence — a fully-live, stay-in-place budgeting app built on NiceGUI.

Run:  python -m cadence.main   (serves on :8110, or $PORT on Railway)

No hx-get / hx-target / hx-swap anywhere. You mutate Python state; the pieces
that depend on it re-render in place over a WebSocket. Scroll and focus never
jump. Sign in to see your real Supabase budget, or open the demo for sample data.
"""
import os
from nicegui import ui, app
from .store import Store as SeedStore

BRAND = "Cadence"          # rename here — it's the only place the name lives
PORT = int(os.environ.get("PORT", 8110))   # Railway injects $PORT


@app.get("/healthz")
def _healthz():
    """Matches the repo's Railway healthcheck path so this service deploys clean."""
    return {"status": "ok"}


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
      .cd-auth{margin-left:auto;display:flex;align-items:center;gap:10px;font-size:12px;color:var(--muted)}
      .cd-chip{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
        padding:4px 9px;border-radius:20px;background:var(--accent-soft);color:var(--accent)}
      .cd-link{color:var(--muted);cursor:pointer;text-decoration:underline;font-weight:500}
      .cd-hero{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:14px;margin:8px 0 26px}
      .cd-stat{background:var(--card);border:1px solid var(--line);border-radius:18px;
        padding:18px 20px;box-shadow:var(--shadow)}
      .cd-stat.primary{background:linear-gradient(135deg,#5b5ff0,#7c6bf5);border:none;color:#fff;
        box-shadow:0 10px 30px rgba(99,102,241,.35)}
      .cd-stat-lbl{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;opacity:.75}
      .cd-stat.primary .cd-stat-lbl{opacity:.85}
      .cd-stat-val{font-size:30px;font-weight:700;letter-spacing:-.02em;margin-top:6px}
      .cd-stat-sub{font-size:12px;opacity:.8;margin-top:2px}
      .cd-cat{margin-bottom:22px}
      .cd-cat-hd{display:flex;align-items:center;gap:10px;padding:0 4px 10px}
      .cd-dot{width:9px;height:9px;border-radius:50%}
      .cd-cat-name{font-weight:700;font-size:15px}
      .cd-cat-avail{margin-left:auto;font-size:13px;color:var(--muted)}
      .cd-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
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
      /* login */
      .cd-login{max-width:400px;margin:12vh auto 0;background:var(--card);border:1px solid var(--line);
        border-radius:22px;padding:34px 32px;box-shadow:var(--shadow);text-align:center}
      .cd-login .cd-logo{width:46px;height:46px;border-radius:13px;font-size:20px;margin:0 auto 16px}
      .cd-login h1{font-size:22px;font-weight:800;letter-spacing:-.02em;margin-bottom:4px}
      .cd-login p{color:var(--muted);font-size:13px;margin-bottom:22px}
    </style>
    """)


# ── shared UI pieces ──────────────────────────────────────────────────────────
def _stat(label, value, primary=False, sub=""):
    cls = "cd-stat primary" if primary else "cd-stat"
    with ui.element("div").classes(cls):
        ui.html(f'<div class="cd-stat-lbl">{label}</div>')
        ui.html(f'<div class="cd-stat-val mono">{money(value)}</div>')
        if sub:
            ui.html(f'<div class="cd-stat-sub">{sub}</div>')


def _app(store, demo: bool):
    with ui.element("div").classes("cd-shell"):
        with ui.element("div").classes("cd-top"):
            ui.html('<div class="cd-logo">C</div>')
            ui.html(f'<div class="cd-brand">{BRAND}</div>')
            with ui.element("div").classes("cd-nav"):
                ui.html('<div class="cd-navbtn active">Buckets</div>')
                ui.html('<div class="cd-navbtn soon">Ledger</div>')
                ui.html('<div class="cd-navbtn soon">Forecast</div>')
            with ui.element("div").classes("cd-auth"):
                if demo:
                    ui.html('<span class="cd-chip">Demo · sample data</span>')
                    signin = ui.html('<span class="cd-link">Sign in</span>')
                    signin.on("click", lambda _: _logout())
                else:
                    ui.html(f'<span>{getattr(store, "email", "") or "Signed in"}</span>')
                    out = ui.html('<span class="cd-link">Sign out</span>')
                    out.on("click", lambda _: _logout())

        @ui.refreshable
        def hero():
            m = store.metrics()
            with ui.element("div").classes("cd-hero"):
                _stat("Unallocated", m["unallocated"], primary=True,
                      sub="Money without a job yet — assign it all")
                _stat("Ready to Spend", m["ready_to_spend"], sub="Unassigned + what's in your buckets")
                _stat("Available Balance", m["available_balance"], sub="Real cash in the bank")

        @ui.refreshable
        def buckets():
            groups = store.groups()
            if not groups:
                ui.html('<div class="cd-sub" style="padding:20px 4px">No buckets yet.</div>')
                return
            for g in groups:
                with ui.element("div").classes("cd-cat"):
                    with ui.element("div").classes("cd-cat-hd"):
                        ui.html(f'<span class="cd-dot" style="background:{g["color"]}"></span>')
                        ui.html(f'<span class="cd-cat-name">{g["name"]}</span>')
                        ui.html(f'<span class="cd-cat-avail">{money(g["available"])} available</span>')
                    with ui.element("div").classes("cd-grid"):
                        for r in g["rows"]:
                            _envelope(r)

        def adjust(eid, delta):
            try:
                store.fund(eid, delta) if delta > 0 else store.defund(eid, -delta)
            except Exception as e:
                ui.notify(f"Couldn't update: {str(e)[:80]}", type="negative")
                return
            hero.refresh()
            buckets.refresh()

        def _envelope(r):
            with ui.element("div").classes("cd-env"):
                with ui.element("div").classes("cd-env-top"):
                    ui.html(f'<span class="cd-env-name">{r["name"]}</span>')
                    if r["type"] in ("goal", "vault"):
                        ui.html(f'<span class="cd-badge {r["type"]}">{r["type"]}</span>')
                col = "var(--neg)" if r["available"] < 0 else "var(--ink)"
                ui.html(f'<div class="cd-avail" style="color:{col}">{money(r["available"])}'
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
                    m = ui.html('<div class="cd-fbtn">− $50</div>')
                    m.on("click", lambda _, e=r["id"]: adjust(e, -50))
                    p = ui.html('<div class="cd-fbtn">＋ $50</div>')
                    p.on("click", lambda _, e=r["id"]: adjust(e, 50))

        hero()
        buckets()


def _login(error: str = ""):
    _theme()
    with ui.element("div").classes("cd-shell"):
        with ui.element("div").classes("cd-login"):
            ui.html('<div class="cd-logo">C</div>')
            ui.html(f'<h1>{BRAND}</h1>')
            ui.html('<p>Sign in with your budget account.</p>')
            email = ui.input("Email").props("outlined dense").classes("w-full")
            pw = ui.input("Password", password=True).props("outlined dense").classes("w-full")

            def do_login():
                try:
                    from .data import sign_in
                    r = sign_in(email.value.strip(), pw.value)
                except Exception as e:
                    ui.notify(f"Sign in failed: {str(e)[:100]}", type="negative")
                    return
                app.storage.user.update({"token": r["token"], "uid": r["uid"],
                                         "email": r["email"], "demo": False})
                ui.navigate.to("/")

            ui.button("Sign in", on_click=do_login).props("unelevated color=indigo").classes("w-full")
            ui.button("Open the demo", on_click=lambda: (
                app.storage.user.update({"demo": True, "token": None}), ui.navigate.to("/"))
            ).props("flat color=indigo").classes("w-full")
            if error:
                ui.notify(error, type="negative")


def _logout():
    app.storage.user.clear()
    ui.navigate.to("/")


@ui.page("/")
def index():
    u = app.storage.user
    if u.get("token"):
        _theme()
        try:
            from .data import LiveStore
            _app(LiveStore(u["uid"], u["token"], u.get("email", "")), demo=False)
        except Exception as e:
            u.clear()
            _login(error=f"Session expired — please sign in again.")
    elif u.get("demo"):
        _theme()
        _app(SeedStore(), demo=True)
    else:
        _login()


def run():
    ui.run(host="0.0.0.0", port=PORT, title=BRAND, reload=False, show=False,
           favicon="🪙", storage_secret=os.environ.get("SECRET_KEY", "cadence-dev-secret"))


if __name__ in {"__main__", "__mp_main__"}:
    run()
