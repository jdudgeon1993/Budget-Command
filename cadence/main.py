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
      body{background:var(--bg);font-family:'Inter',-apple-system,'Segoe UI',Roboto,sans-serif;color:var(--ink)}
      .mono{font-family:'JetBrains Mono',ui-monospace,monospace;font-feature-settings:"tnum"}
      .cd-shell{max-width:960px;margin:0 auto;padding:0 20px 80px}
      .cd-top{display:flex;align-items:center;gap:18px;padding:22px 4px 10px}
      .cd-logo{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--violet));
        display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;box-shadow:0 6px 16px rgba(99,102,241,.35)}
      .cd-brand{font-weight:800;font-size:19px;letter-spacing:-.02em}
      .cd-nav{display:flex;gap:4px;margin-left:8px}
      .cd-navbtn{font-size:13px;font-weight:600;color:var(--muted);padding:7px 14px;border-radius:9px;cursor:pointer;transition:.15s}
      .cd-navbtn.active{color:var(--accent);background:var(--accent-soft)}
      .cd-navbtn.soon{opacity:.5;cursor:default}
      .cd-auth{margin-left:auto;display:flex;align-items:center;gap:10px;font-size:12px;color:var(--muted)}
      .cd-chip{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:4px 9px;border-radius:20px;background:var(--accent-soft);color:var(--accent)}
      .cd-link{color:var(--muted);cursor:pointer;text-decoration:underline;font-weight:500}
      .cd-hero{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:14px;margin:8px 0 20px}
      .cd-stat{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px 20px;box-shadow:var(--shadow)}
      .cd-stat.primary{background:linear-gradient(135deg,#5b5ff0,#7c6bf5);border:none;color:#fff;box-shadow:0 10px 30px rgba(99,102,241,.35)}
      .cd-stat-lbl{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;opacity:.75}
      .cd-stat.primary .cd-stat-lbl{opacity:.85}
      .cd-stat-val{font-size:30px;font-weight:700;letter-spacing:-.02em;margin-top:6px}
      .cd-stat-sub{font-size:12px;opacity:.8;margin-top:2px}
      /* one-number money header */
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
      .cd-actionbar{display:flex;align-items:center;margin:6px 4px 18px}
      .cd-newbtn{font-size:13px;font-weight:700;color:#fff;background:linear-gradient(135deg,var(--accent),var(--violet));
        padding:9px 16px;border-radius:10px;cursor:pointer;box-shadow:0 4px 14px rgba(99,102,241,.32)}
      .cd-hint{margin-left:auto;font-size:12px;color:var(--muted)}
      .cd-cat{margin-bottom:22px}
      .cd-cat-hd{display:flex;align-items:center;gap:10px;padding:0 4px 10px}
      .cd-dot{width:9px;height:9px;border-radius:50%}
      .cd-cat-name{font-weight:700;font-size:15px}
      .cd-cat-avail{margin-left:auto;font-size:13px;color:var(--muted)}
      .cd-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
      .cd-env{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 16px 14px;
        box-shadow:var(--shadow);transition:transform .12s,box-shadow .12s;cursor:pointer}
      .cd-env:hover{transform:translateY(-2px);box-shadow:0 2px 4px rgba(16,18,34,.05),0 14px 34px rgba(16,18,34,.10);border-color:#dfe1ee}
      .cd-env-top{display:flex;align-items:baseline;gap:8px}
      .cd-env-name{font-weight:600;font-size:14px}
      .cd-badge{font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;border-radius:20px;margin-left:auto}
      .cd-badge.goal{background:#f3efff;color:var(--violet)}
      .cd-badge.vault{background:#eafaf3;color:var(--pos)}
      .cd-avail{font-size:22px;font-weight:700;letter-spacing:-.02em;margin:8px 0 2px}
      .cd-sub{font-size:11px;color:var(--muted)}
      .cd-bar{height:7px;border-radius:6px;background:var(--line);overflow:hidden;margin:12px 0 6px}
      .cd-bar-fill{height:100%;border-radius:6px;transition:width .35s cubic-bezier(.2,.8,.2,1)}
      .cd-tap{font-size:11px;color:var(--accent);font-weight:600;margin-top:8px}
      /* modal */
      .cd-modal{width:460px;max-width:94vw;padding:22px 22px 18px !important;border-radius:20px !important;box-shadow:0 30px 80px rgba(16,18,34,.3) !important}
      .cdm-title{font-size:18px;font-weight:800;letter-spacing:-.01em}
      .cdm-sub{font-size:12px;color:var(--muted);margin:2px 0 14px}
      .cdm-opt{border:1px solid var(--line);border-radius:13px;padding:11px 13px;margin-bottom:9px}
      .cdm-ohd{display:flex;align-items:center;gap:8px;margin-bottom:9px}
      .cdm-num{width:20px;height:20px;border-radius:6px;background:var(--accent);color:#fff;font-size:11px;font-weight:800;
        display:inline-flex;align-items:center;justify-content:center}
      .cdm-lbl{font-size:12px;font-weight:700;color:var(--ink)}
      .cdm-manage{display:flex;flex-wrap:wrap;align-items:center;gap:8px;border-top:1px dashed var(--line);margin-top:6px;padding-top:12px}
      .cdm-input{max-width:150px}
    </style>
    """)


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
                    ui.html('<span class="cd-link">Sign in</span>').on("click", lambda _: _logout())
                else:
                    ui.html(f'<span>{getattr(store, "email", "") or "Signed in"}</span>')
                    ui.html('<span class="cd-link">Sign out</span>').on("click", lambda _: _logout())

        @ui.refreshable
        def hero():
            m = store.metrics()
            un, bal = m["unallocated"], m["available_balance"]
            inb, inv = m["in_buckets"], m["in_vaults"]
            tot = bal if bal > 0 else 1
            wu, wb, wv = (max(0, un) / tot * 100, max(0, inb) / tot * 100, max(0, inv) / tot * 100)
            un_col = "var(--neg)" if un < 0 else "var(--accent)"
            ui.html(f'''
              <div class="cd-money">
                <div>
                  <div class="cd-money-lbl">Unallocated · give it a job</div>
                  <div class="cd-money-big mono" style="color:{un_col}">{money(un)}</div>
                  <div class="cd-money-sub">of {money(bal)} total cash in the bank</div>
                </div>
                <div>
                  <div class="cd-segbar">
                    <span style="width:{wu:.1f}%;background:var(--accent)"></span>
                    <span style="width:{wb:.1f}%;background:var(--pos)"></span>
                    <span style="width:{wv:.1f}%;background:var(--violet)"></span>
                  </div>
                  <div class="cd-legend">
                    <span><i style="background:var(--accent)"></i>Unallocated <b>{money(un)}</b></span>
                    <span><i style="background:var(--pos)"></i>In buckets <b>{money(inb)}</b></span>
                    <span><i style="background:var(--violet)"></i>In vaults <b>{money(inv)}</b></span>
                  </div>
                </div>
              </div>''')

        @ui.refreshable
        def buckets():
            groups = store.groups()
            if not groups:
                ui.html('<div class="cd-sub" style="padding:20px 4px">No buckets yet — add one above.</div>')
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

        def refresh_page():
            hero.refresh()
            buckets.refresh()

        def _envelope(r):
            card = ui.element("div").classes("cd-env")
            with card:
                with ui.element("div").classes("cd-env-top"):
                    ui.html(f'<span class="cd-env-name">{r["name"]}</span>')
                    if r["type"] in ("goal", "vault"):
                        ui.html(f'<span class="cd-badge {r["type"]}">{r["type"]}</span>')
                col = "var(--neg)" if r["available"] < 0 else "var(--ink)"
                ui.html(f'<div class="cd-avail" style="color:{col}">{money(r["available"])}'
                        f'<span class="cd-sub" style="font-weight:500"> available</span></div>')
                if r["type"] == "spend":
                    sub = f'{money(r["spent"])} spent of {money(r["funded"])} funded'
                    fill = ("var(--neg)" if r["pct"] >= 1 else "var(--warn)" if r["pct"] >= 0.85 else "var(--pos)")
                else:
                    sub = f'{money(r["funded"])} of {money(r["target"])} goal'
                    fill = "var(--violet)"
                ui.html(f'<div class="cd-sub">{sub}</div>')
                ui.html(f'<div class="cd-bar"><div class="cd-bar-fill" style="width:{r["pct"]*100:.0f}%;background:{fill}"></div></div>')
                ui.html('<div class="cd-tap">Tap to assign / manage →</div>')
            card.on("click", lambda _, e=r["id"]: _open_assign(e))

        # ── the numbered "Assign" showcase modal ──────────────────────────────
        def _open_assign(eid):
            with ui.dialog() as dlg, ui.card().classes("cd-modal"):
                @ui.refreshable
                def body():
                    b = store.bucket(eid)
                    m = store.metrics()

                    def act(fn):
                        try:
                            fn()
                        except Exception as e:
                            ui.notify(str(e)[:140], type="warning")
                            return
                        body.refresh()
                        refresh_page()

                    av_col = "var(--neg)" if b["available"] < 0 else "var(--ink)"
                    ui.html(f'<div class="cdm-title">Fund {b["name"]}</div>')
                    ui.html(f'<div class="cdm-sub"><b style="color:{av_col}">{money(b["available"])} available</b>'
                            f' · {money(b["target"])} target · {money(b["spent"])} spent this month</div>')

                    gap = b["gap"]
                    over = round(max(0.0, -b["available"]), 2)

                    sources = store.fund_sources(eid)
                    src_avail = {s["id"]: s["avail"] for s in sources}
                    src_map = {s["id"]: f'{s["name"]}  ·  {money(s["avail"])}' for s in sources}

                    # amount is the single source of truth; slider + presets drive it
                    amount = ui.number(value=0, format="%.2f").props("outlined dense hide-bottom-space").classes("w-full")
                    sld = ui.slider(min=0, max=max(src_avail.get("unallocated", 0), 1), step=1) \
                        .props("label-always color=indigo").classes("q-mt-sm")
                    sld.bind_value(amount)

                    def set_amt(v):
                        amount.value = round(v, 2)

                    # the three reasons, as one-tap amount setters
                    with ui.row().classes("q-gutter-xs q-mt-xs"):
                        if gap > 0:
                            ui.button(f"Fill to target  +{money(gap)}",
                                      on_click=lambda: set_amt(gap)).props("outline color=indigo no-caps size=sm")
                        if over > 0:
                            ui.button(f"Cover overspend  +{money(over)}",
                                      on_click=lambda: set_amt(over)).props("outline color=deep-orange no-caps size=sm")

                    # where the money comes from (Unallocated, or another bucket = "move")
                    src = ui.select(src_map, value="unallocated", label="From").props("outlined dense").classes("w-full q-mt-sm")

                    def on_src():
                        sld._props["max"] = max(src_avail.get(src.value, 0), 1)
                        sld.update()
                    src.on("update:model-value", lambda: on_src())

                    def do_assign():
                        amt = float(amount.value or 0)
                        if amt <= 0:
                            ui.notify("Enter an amount (or tap a shortcut).", type="warning")
                            return
                        un = store.metrics()["unallocated"]
                        if src.value == "unallocated" and amt > un + 0.005:
                            ui.notify(f"Only {money(un)} is unallocated — assigning that.", type="info")
                        act(lambda: store.assign(eid, src.value, amt))
                    ui.button("Add to this bucket", on_click=do_assign) \
                        .props("unelevated color=indigo no-caps").classes("w-full q-mt-sm")

                    with ui.row().classes("items-center q-mt-xs"):
                        ui.html('<span class="cd-sub">Pull money back out →</span>')
                        rem = ui.number(placeholder="0.00").props("dense outlined hide-bottom-space").classes("cdm-input")
                        ui.button("Remove", on_click=lambda: act(lambda: store.defund(eid, float(rem.value or 0)))) \
                            .props("flat color=grey no-caps")

                    # manage — edits auto-save on change; no explicit save buttons
                    def save(fn):
                        try:
                            fn()
                        except Exception as e:
                            ui.notify(str(e)[:140], type="warning")
                            return
                        refresh_page()   # update cards behind; keep the modal steady

                    with ui.element("div").classes("cdm-manage"):
                        rn = ui.input("Name", value=b["name"]).props("dense outlined hide-bottom-space").classes("cdm-input")
                        rn.on("blur", lambda: save(lambda: store.rename(eid, rn.value)))
                        tg = ui.number("Target", value=b["target"]).props("dense outlined hide-bottom-space").classes("cdm-input")
                        tg.on("blur", lambda: save(lambda: store.set_target(eid, float(tg.value or 0))))
                        ui.space()

                        def do_delete():
                            try:
                                store.delete(eid)
                            except Exception as e:
                                ui.notify(str(e)[:140], type="warning")
                                return
                            dlg.close()
                            refresh_page()
                        ui.button("Delete", on_click=do_delete).props("flat color=red no-caps")
                        ui.button("Done", on_click=dlg.close).props("unelevated color=indigo no-caps")
                body()
            dlg.open()

        # ── create bucket ─────────────────────────────────────────────────────
        def _open_create():
            with ui.dialog() as dlg, ui.card().classes("cd-modal"):
                ui.html('<div class="cdm-title">New bucket</div>')
                ui.html('<div class="cdm-sub">Give it a name, a home, and a target.</div>')
                name = ui.input("Name").props("dense outlined").classes("w-full")
                cats = store.categories()
                cat = ui.select({c["id"]: c["name"] for c in cats}, label="Category",
                                value=(cats[0]["id"] if cats else None)).props("dense outlined").classes("w-full")
                typ = ui.select({"spend": "Spend", "goal": "Goal", "vault": "Vault"},
                                label="Type", value="spend").props("dense outlined").classes("w-full")
                tgt = ui.number("Monthly target / goal amount", value=0).props("dense outlined").classes("w-full")

                def create():
                    try:
                        store.add_bucket((name.value or "New bucket").strip(), cat.value, typ.value, float(tgt.value or 0))
                    except Exception as e:
                        ui.notify(str(e)[:140], type="warning")
                        return
                    dlg.close()
                    refresh_page()
                with ui.row().classes("w-full justify-end q-mt-sm"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Create bucket", on_click=create).props("unelevated color=indigo")
            dlg.open()

        hero()
        with ui.element("div").classes("cd-actionbar"):
            ui.html('<div class="cd-newbtn">＋ New bucket</div>').on("click", lambda _: _open_create())
            ui.html('<span class="cd-hint">Tap any bucket to assign money or manage it</span>')
        buckets()


def _login(error: str = ""):
    _theme()
    with ui.element("div").classes("cd-shell"):
        with ui.element("div").classes("cd-login"):
            ui.html('<div class="cd-logo" style="width:46px;height:46px;border-radius:13px;font-size:20px;margin:0 auto 16px">C</div>')
            ui.html(f'<h1 style="font-size:22px;font-weight:800;text-align:center;margin-bottom:4px">{BRAND}</h1>')
            ui.html('<p style="color:var(--muted);font-size:13px;text-align:center;margin-bottom:22px">Sign in with your budget account.</p>')
            email = ui.input("Email").props("outlined dense").classes("w-full")
            pw = ui.input("Password", password=True).props("outlined dense").classes("w-full")

            def do_login():
                try:
                    from .data import sign_in
                    r = sign_in(email.value.strip(), pw.value)
                except Exception as e:
                    ui.notify(f"Sign in failed: {str(e)[:100]}", type="negative")
                    return
                app.storage.user.update({"token": r["token"], "uid": r["uid"], "email": r["email"], "demo": False})
                ui.navigate.reload()

            ui.button("Sign in", on_click=do_login).props("unelevated color=indigo").classes("w-full")
            ui.button("Open the demo", on_click=lambda: (
                app.storage.user.update({"demo": True, "token": None}), ui.navigate.reload())
            ).props("flat color=indigo").classes("w-full")
            if error:
                ui.notify(error, type="negative")
    ui.add_head_html('<style>.cd-login{max-width:400px;margin:12vh auto 0;background:var(--card);'
                     'border:1px solid var(--line);border-radius:22px;padding:34px 32px;box-shadow:var(--shadow)}</style>')


def _logout():
    app.storage.user.clear()
    ui.navigate.reload()


@ui.page("/")
def index():
    u = app.storage.user
    if u.get("token"):
        _theme()
        try:
            from .data import LiveStore
            _app(LiveStore(u["uid"], u["token"], u.get("email", "")), demo=False)
        except Exception:
            u.clear()
            _login(error="Session expired — please sign in again.")
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
