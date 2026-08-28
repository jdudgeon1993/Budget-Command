"""
Cadence — a fully-live, stay-in-place budgeting app built on NiceGUI.

Run:  python -m cadence.main   (serves on :8110, or $PORT on Railway)

No hx-get / hx-target / hx-swap anywhere. You mutate Python state; the pieces
that depend on it re-render in place over a WebSocket. Scroll and focus never
jump. Sign in to see your real Supabase budget, or open the demo for sample data.
"""
import os
from datetime import date, timedelta
from html import escape as _esc
from nicegui import ui, app
from . import theme, forecast
from .store import Store as SeedStore

BRAND = "Cadence"          # rename here — it's the only place the name lives
PORT = int(os.environ.get("PORT", 8110))   # Railway injects $PORT


@app.get("/healthz")
def _healthz():
    return {"status": "ok"}


def money(v: float) -> str:
    return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"


GREEN, AMBER, RED, PURPLE, BLUE = (
    "var(--pos)", "var(--warn)", "var(--neg)", "var(--violet)", "var(--info)")


def _due_word(d) -> str:
    return "today" if d == 0 else "tomorrow" if d == 1 else f"in {d}d"


def _days_tag(d):
    """(label, colour-class) for a days-until-due value."""
    if d is None:
        return ("no date", "muted")
    if d < 0:
        return ("past due", "red")
    if d <= 7:
        return (_due_word(d), "amber")
    return (f"in {d}d", "muted")


def _item_due_tag(it: dict):
    """(label, colour-class, row-class) for a split line-item's timing."""
    if it.get("paid"):
        return ("paid", "green", "paid")
    txt, cls = _days_tag(it.get("days_until_due"))
    row = "soon" if cls == "amber" else "past" if cls == "red" else ""
    return (txt, cls, row)


def _bucket_visual(r: dict) -> dict:
    """One place that decides a bucket card's colour language:

        green  = done  → Funded (reached target) or Paid (spent it all) or Handled
        amber  = funding in progress toward a target
        red    = needs attention → Overspent or Past due (requires allocation)
        purple = a Vault (savings, set apart)
        blue   = Flexible (no target — just shows what's been spent, no bar)

    The bar itself changes meaning with the bucket's state: while under-funded it
    shows *funding* progress (funded/target); once funded it shows *spending*
    progress (spent/funded). Returns badge=(text, css), bar=(pct, colour)|None, sub.
    """
    typ, av, funded, target = r["type"], r["available"], r["funded"], r["target"]
    spent, gap, d = r["spent"], r["gap"], r["days_until_due"]

    def out(badge, badge_cls, bar, color, sub):
        return {"badge": badge, "badge_cls": badge_cls,
                "bar": None if bar is None else max(0.0, min(1.0, bar)),
                "color": color, "sub": sub}

    if r["handled"]:
        return out("Handled", "green", 1.0, GREEN, f"{money(spent)} spent · handled this cycle")
    if typ == "vault":
        pct = funded / target if target > 0 else 0.0
        return out("Vault", "purple", pct, PURPLE, f"{money(funded)} of {money(target)} saved")
    if r["flex"]:
        return out("Flexible", "blue", None, BLUE, f"{money(spent)} spent this cycle · no set target")
    if typ == "goal":
        if gap <= 0.005 and target > 0:
            return out("Funded", "green", 1.0, GREEN, f"{money(funded)} of {money(target)} · goal reached")
        pct = funded / target if target > 0 else 0.0
        # surface the monthly pace to hit the goal by its target date, right on the card
        pace, td = "", r.get("target_date")
        if td and gap > 0:
            months = _months_until_month(td)
            if months and months > 0:
                pace = f" · {money(gap / months)}/mo to stay on pace"
            elif months is not None and months <= 0:
                pace = " · target date passed"
        return out("Funding", "amber", pct, AMBER, f"{money(funded)} of {money(target)} goal{pace}")

    # ── spend buckets ──
    if av < -0.005:                                   # overspent
        return out("Overspent", "red", 1.0, RED, f"{money(spent)} spent of {money(funded)} funded")
    if gap > 0.005:                                   # under-funded → funding progress
        pct = funded / target if target > 0 else 0.0
        if d is not None and d < 0:
            return out("Past due", "red", pct, RED, f"{money(funded)} of {money(target)} · needs {money(gap)}")
        badge = (f"Due {_due_word(d)}", "amber") if (d is not None and d <= 10) else ("Funding", "amber")
        return out(badge[0], badge[1], pct, AMBER, f"{money(funded)} of {money(target)} funded · needs {money(gap)}")
    # ── fully funded → spending progress ──
    if funded > 0 and spent >= funded - 0.005:        # paid in full
        return out("Paid", "green", 1.0, GREEN, f"{money(spent)} spent · paid in full")
    pct = spent / funded if funded > 0 else 0.0
    return out("Funded", "green", pct, GREEN, f"{money(spent)} spent of {money(funded)} funded")


# ── due-day + frequency options (mirrors the old app: 1–28 + End of Month) ────
def _dueday_options() -> dict:
    opts = {"": "— none —"}
    for d in range(1, 29):
        suf = "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
        opts[str(d)] = f"{d}{suf}"
    opts["eom"] = "End of month"
    return opts


def _dueday_key(due_day) -> str:
    """Current stored due_day (int, 'eom', or None) → select key.

    The dropdown only offers 1–28 + End of month (any month has at least 28 days,
    so those never crash the calendar math); the data model has always accepted
    1–31. A stored 29/30/31 — from before this screen existed, an import, or a
    split item whose own day never went through this same dropdown — has no
    matching option. Passing it straight to ui.select raises (NiceGUI validates
    the initial value against the option keys), which silently killed the whole
    sheet. Map it to the nearest real option instead of crashing."""
    if due_day is None or due_day == "":
        return ""
    if str(due_day).lower() == "eom":
        return "eom"
    try:
        d = int(due_day)
    except (ValueError, TypeError):
        return ""
    return "eom" if d >= 29 else str(d)


# Frequency options — triweekly included, for parity with the Forecast engine.
_FREQ = {"": "— none —", "weekly": "Weekly", "biweekly": "Biweekly",
         "triweekly": "Triweekly", "monthly": "Monthly"}
_PERIODS_PER_MONTH = {"weekly": 30.44 / 7, "biweekly": 30.44 / 14,
                      "triweekly": 30.44 / 21, "monthly": 1.0}
_PERIOD_WORD = {"weekly": "week", "biweekly": "2 weeks",
                "triweekly": "3 weeks", "monthly": "month"}


def _months_until_month(target_date) -> int | None:
    """Whole months from this month to a 'YYYY-MM' target, or None."""
    try:
        from datetime import date
        y, m = str(target_date).split("-")[:2]
        today = date.today()
        return (int(y) - today.year) * 12 + (int(m) - today.month)
    except (ValueError, AttributeError):
        return None


def _day_label(iso: str):
    """(bold label, sub) for a ledger date group. Recent days read relative
    (Today / Yesterday / weekday); anything older reads as a plain date."""
    try:
        d = date.fromisoformat(iso)
    except (ValueError, TypeError):
        return (iso or "Undated", "")
    md = d.strftime("%b ") + str(d.day)
    delta = (date.today() - d).days
    if delta == 0:
        return ("Today", md)
    if delta == 1:
        return ("Yesterday", md)
    if 2 <= delta <= 6:
        return (d.strftime("%A"), md)
    return (md, d.strftime("%A"))


def _period_hint(r: dict) -> str:
    """A one-line 'feeds the Forecast' hint: goals show the pace to their target
    date; dated/recurring expenses show the per-paycheck slice of the bill."""
    if r["type"] == "goal":
        td, gap = r.get("target_date"), r["gap"]
        if td and gap > 0:
            months = _months_until_month(td)
            if months and months > 0:
                return f"Save ≈ {money(gap / months)}/mo to reach {money(r['target'])} by {td}"
            if months is not None and months <= 0:
                return f"Target date {td} has passed — {money(gap)} still to go"
        return ""
    freq, target = r["frequency"], r["target"]
    if freq in _PERIODS_PER_MONTH and target > 0:
        per = target / _PERIODS_PER_MONTH[freq]
        return f"≈ {money(per)} per {_PERIOD_WORD[freq]} · feeds Forecast"
    return ""


def _theme() -> None:
    theme.apply()


# Refreshing a list momentarily collapses the page height and the browser snaps
# scroll to the top. We freeze the page + open-sheet scroll positions *before* the
# refresh (order-preserved over the socket) and restore them two frames after.
_CAP_WIN = "window.__wsF=window.scrollY;"
_RES_WIN = ("[0,60,140,260].forEach(t=>setTimeout(()=>{if(window.__wsF)"
            "window.scrollTo(0,window.__wsF);},t));")
_CAP_SHEET = 'window.__ssF=(document.querySelector(".cd-sheet")||{}).scrollTop||0;'
_RES_SHEET = ('[0,60,140,260].forEach(t=>setTimeout(()=>{const s=document.querySelector(".cd-sheet");'
              'if(s&&window.__ssF)s.scrollTop=window.__ssF;},t));')


def _app(store, demo: bool):
    state = {"view": "buckets"}          # which pillar is on screen

    def go(view):
        if view == state["view"]:
            return
        # Ledger and Forecast are inherently "now / forward" views — they must never
        # read a browsed past month (Buckets & Reports share that browse state).
        if view in ("ledger", "forecast") and hasattr(store, "set_view_month"):
            store.set_view_month(None)
        state["view"] = view
        nav.refresh()
        gear.refresh()
        content.refresh()

    with ui.element("div").classes("cd-shell"):
        with ui.element("div").classes("cd-top"):
            ui.html('<div class="cd-logo">C</div>')
            ui.html(f'<div class="cd-brand">{BRAND}</div>')

            @ui.refreshable
            def nav():
                with ui.element("div").classes("cd-nav"):
                    for key, label in (("buckets", "Buckets"), ("ledger", "Ledger"), ("forecast", "Forecast")):
                        cls = "cd-navbtn active" if state["view"] == key else "cd-navbtn"
                        ui.html(f'<div class="{cls}">{label}</div>').on("click", lambda _, k=key: go(k))
            nav()

            with ui.element("div").classes("cd-auth"):
                @ui.refreshable
                def gear():
                    rcls = "cd-gear active" if state["view"] == "reports" else "cd-gear"
                    ui.html(f'<span class="{rcls}" title="Reports">📊</span>').on("click", lambda _: go("reports"))
                    cls = "cd-gear active" if state["view"] == "settings" else "cd-gear"
                    ui.html(f'<span class="{cls}" title="Settings">⚙</span>').on("click", lambda _: go("settings"))
                gear()
                if demo:
                    ui.html('<span class="cd-chip">Demo · sample data</span>')
                    ui.html('<span class="cd-link">Sign in</span>').on("click", lambda _: _logout())
                else:
                    ui.html(f'<span>{getattr(store, "email", "") or "Signed in"}</span>')
                    ui.html('<span class="cd-link">Sign out</span>').on("click", lambda _: _logout())

        # A mutation refreshes only the pieces that changed — never the whole page —
        # so scroll position is preserved (content.refresh is for view switches only).
        # A stable home for the bucket sheet — it stays open while the page behind
        # it refreshes, so it must live outside the `content` refreshable's slot.
        dialog_host = ui.element("div")

        def refresh_page():
            ui.run_javascript(_CAP_WIN)
            content.refresh()
            ui.run_javascript(_RES_WIN)

        def hero():
            m = store.metrics()
            un, cash, inb = m["unallocated"], m["cash"], m["in_buckets"]
            aom = m.get("age_of_money")
            tot = cash if cash > 0 else 1
            wu, wb = (max(0, un) / tot * 100, max(0, inb) / tot * 100)
            if un <= 0.005:   # zero-based win — every dollar has a job
                left = f'''<div>
                    <div class="cd-money-lbl" style="color:var(--pos)">Every dollar has a job ✨</div>
                    <div class="cd-money-big mono" style="color:var(--pos)">$0.00</div>
                    <div class="cd-money-sub">unallocated · {money(cash)} in checking, all assigned</div>
                  </div>'''
            else:
                left = f'''<div>
                    <div class="cd-money-lbl">Unallocated · give it a job</div>
                    <div class="cd-money-big mono" style="color:var(--accent)">{money(un)}</div>
                    <div class="cd-money-sub">of {money(cash)} in your checking account</div>
                  </div>'''
            ui.html(f'''
              <div class="cd-money">
                {left}
                <div>
                  <div class="cd-segbar">
                    <span style="width:{wu:.1f}%;background:var(--accent)"></span>
                    <span style="width:{wb:.1f}%;background:var(--pos)"></span>
                  </div>
                  <div class="cd-legend">
                    <span><i style="background:var(--accent)"></i>Unallocated <b>{money(un)}</b></span>
                    <span><i style="background:var(--pos)"></i>In buckets <b>{money(inb)}</b></span>
                    <span style="margin-left:auto"><i style="background:var(--ink);opacity:.25"></i>Checking <b>{money(cash)}</b></span>
                  </div>
                  <div class="cd-aom" title="Age of Money — days between earning a dollar and spending it. Higher means you're spending last month's money, not this one's.">
                    <span class="cd-aom-ic">🕰</span>
                    <span class="cd-aom-lbl">Age of money</span>
                    <span class="cd-aom-val">{(str(aom) + (" days" if aom != 1 else " day")) if aom is not None else "—"}</span>
                  </div>
                </div>
              </div>''')

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

        def _envelope(r):
            v = _bucket_visual(r)
            card = ui.element("div").classes("cd-env" + (" is-handled" if r["handled"] else ""))
            with card:
                with ui.element("div").classes("cd-env-top"):
                    ui.html(f'<span class="cd-env-name">{_esc(r["name"])}</span>')
                    ui.html(f'<span class="cd-pill {v["badge_cls"]}">{v["badge"]}</span>')
                col = "var(--neg)" if r["available"] < 0 else "var(--ink)"
                ui.html(f'<div class="cd-avail" style="color:{col}">{money(r["available"])}'
                        f'<span class="cd-sub" style="font-weight:500"> available</span></div>')
                ui.html(f'<div class="cd-sub">{v["sub"]}</div>')
                if v["bar"] is None:                  # flex — a flat marker, no progress bar
                    ui.html('<div class="cd-flexbar"></div>')
                else:
                    ui.html(f'<div class="cd-bar"><div class="cd-bar-fill" '
                            f'style="width:{v["bar"] * 100:.0f}%;background:{v["color"]}"></div></div>')
                if r.get("split") and r["items"]:
                    unfunded = sum(1 for it in r["items"] if not it.get("paid") and it.get("item_gap", 0.0) > 0.005)
                    extra = f' · {unfunded} to fund' if unfunded else ' · all funded ✓'
                    ui.html(f'<div class="cd-sub" style="margin-top:1px">🗓 {r["items_paid"]}/{len(r["items"])} bills paid{extra}</div>')
                ui.html('<div class="cd-tap">Tap to assign / manage →</div>')

            def _open_safe(eid):
                try:
                    _open_assign(eid)
                except Exception as e:
                    ui.notify(f"Couldn't open that bucket: {str(e)[:150]}", type="negative")
            card.on("click", lambda _, e=r["id"]: _open_safe(e))

        # ── bucket sheet: assign · spend · details ────────────────────────────
        def _open_assign(eid):
            dialog_host.clear()
            with dialog_host:
                dlg = ui.dialog().props("position=bottom")
            with dlg, ui.card().classes("cd-sheet"):
                @ui.refreshable
                def body():
                    b = store.bucket(eid)
                    is_vault = b["type"] == "vault"

                    def act(fn):
                        try:
                            fn()
                        except Exception as e:
                            ui.notify(str(e)[:140], type="warning"); return
                        ui.run_javascript(_CAP_SHEET)     # freeze sheet scroll before rebuild
                        body.refresh(); refresh_page()
                        ui.run_javascript(_RES_SHEET)

                    def save(fn):        # for text fields — persist without rebuilding the sheet
                        try:
                            fn()
                        except Exception as e:
                            ui.notify(str(e)[:140], type="warning"); return
                        refresh_page()

                    is_goal = b["type"] == "goal"

                    # ── HERO: name · status · available · progress · one context line ──
                    v = _bucket_visual(b)
                    av_col = "var(--neg)" if b["available"] < 0 else "var(--ink)"
                    barhtml = ('<div class="cd-bs-flex"></div>' if v["bar"] is None
                               else f'<div class="cd-bs-bar"><i style="width:{v["bar"] * 100:.0f}%;background:{v["color"]}"></i></div>')
                    ui.html(f'''
                      <div class="cd-hdl"></div>
                      <div class="cd-bs-head">
                        <div class="cd-bs-top"><span class="cd-bs-name">{_esc(b["name"])}</span>
                          <span class="cd-pill {v["badge_cls"]}">{v["badge"]}</span></div>
                        <div class="cd-bs-avail" style="color:{av_col}">{money(b["available"])}<span>available</span></div>
                        {barhtml}
                        <div class="cd-bs-meta">{v["sub"]}</div>
                      </div>''')

                    # ── PRIMARY ACTION ──
                    if is_vault:
                        with ui.element("div").classes("cd-bs-sec"):
                            ui.html('<div class="cd-bs-lbl">🔒 Locked savings</div>')
                            with ui.element("div").classes("cd-bs-card vault"):
                                ui.html('<div class="cd-sub" style="margin:0 0 12px;line-height:1.5">A transaction can never '
                                        'touch a vault. Move money in from a bucket; releasing only sends it back to '
                                        'Ready to Assign.</div>')
                                sources = store.fund_sources(eid)
                                src_map = {s["id"]: f'{s["name"]} · {money(s["avail"])}' for s in sources}
                                addamt = ui.number(placeholder="Amount to add", prefix="$").props("outlined hide-bottom-space").classes("w-full")
                                addsrc = ui.select(src_map, value="unallocated", label="From").props("outlined dense").classes("w-full q-mt-sm")

                                def do_add():
                                    amt = float(addamt.value or 0)
                                    if amt <= 0:
                                        ui.notify("Enter an amount to add.", type="warning"); return
                                    act(lambda: store.assign(eid, addsrc.value, amt))
                                ui.button("＋ Add to vault", on_click=do_add).props("unelevated color=purple no-caps").classes("w-full q-mt-sm")
                                with ui.element("div").classes("cd-bs-out"):
                                    ui.html('<span class="l">Release</span>')
                                    relamt = ui.number(placeholder="0.00", prefix="$", value=round(b["available"], 2)).props("dense outlined hide-bottom-space").style("flex:1")

                                    def do_release():
                                        amt = float(relamt.value or 0)
                                        if amt <= 0:
                                            ui.notify("Enter an amount to release.", type="warning"); return
                                        act(lambda: store.release_vault(eid, amt))
                                    ui.button("Release", on_click=do_release).props("outline color=purple no-caps size=sm")
                    else:
                        with ui.element("div").classes("cd-bs-sec"):
                            gap, over = b["gap"], round(max(0.0, -b["available"]), 2)
                            ui.html('<div class="cd-bs-lbl">Assign money</div>')
                            with ui.element("div").classes("cd-bs-card primary"):
                                sources = store.fund_sources(eid)
                                src_map = {s["id"]: f'{s["name"]} · {money(s["avail"])}' for s in sources}
                                amount = ui.number(placeholder="Amount to assign", prefix="$").props("outlined hide-bottom-space").classes("w-full")
                                if gap > 0 or over > 0:
                                    with ui.element("div").classes("cd-bs-chips"):
                                        if gap > 0:
                                            ui.button(f"Fill to target · {money(gap)}",
                                                      on_click=lambda g=gap: amount.set_value(round(g, 2))).props("outline color=indigo no-caps size=sm rounded")
                                        if over > 0:
                                            ui.button(f"Cover overspend · {money(over)}",
                                                      on_click=lambda o=over: amount.set_value(round(o, 2))).props("outline color=deep-orange no-caps size=sm rounded")
                                src = ui.select(src_map, value="unallocated", label="From").props("outlined dense").classes("w-full q-mt-sm")

                                def do_assign():
                                    amt = float(amount.value or 0)
                                    if amt <= 0:
                                        ui.notify("Enter an amount (or tap a shortcut).", type="warning"); return
                                    un = store.metrics()["unallocated"]
                                    if src.value == "unallocated" and amt > un + 0.005:
                                        ui.notify(f"Only {money(un)} is unallocated — assigning that.", type="info")
                                    act(lambda: store.assign(eid, src.value, amt))
                                ui.button("Add to bucket", on_click=do_assign).props("unelevated color=indigo no-caps").classes("w-full q-mt-sm")
                                with ui.element("div").classes("cd-bs-out"):
                                    ui.html('<span class="l">Move money out</span>')
                                    rem = ui.number(placeholder="0.00", prefix="$").props("dense outlined hide-bottom-space").style("flex:1")
                                    ui.button("Remove", on_click=lambda: act(lambda: store.defund(eid, float(rem.value or 0)))).props("outline color=grey no-caps size=sm")

                    # ── LOG A SPEND (never for vaults) ──
                    if not is_vault:
                        with ui.element("div").classes("cd-bs-sec"):
                            ui.html('<div class="cd-bs-lbl">Log a spend</div>')
                            with ui.row().classes("items-center no-wrap w-full q-gutter-sm"):
                                sp = ui.number(placeholder="0.00", prefix="$").props("dense outlined hide-bottom-space").style("width:120px")
                                note = ui.input(placeholder="note (optional)").props("dense outlined hide-bottom-space").style("flex:1;min-width:0")

                                def do_spend():
                                    amt = float(sp.value or 0)
                                    if amt <= 0:
                                        ui.notify("Enter a spend amount.", type="warning"); return
                                    act(lambda: store.record_spend(eid, amt, note.value or ""))
                                ui.button("Log", on_click=do_spend).props("unelevated color=deep-orange no-caps")

                    # ── DETAILS · settings (auto-save; feeds the Forecast) ──
                    with ui.element("div").classes("cd-bs-sec"):
                        ui.html('<div class="cd-bs-lbl">Details</div>')
                        with ui.element("div").classes("cd-bs-settings"):
                            with ui.row().classes("items-center q-gutter-sm w-full q-pt-sm"):
                                rn = ui.input("Name", value=b["name"]).props("dense outlined hide-bottom-space").classes("cd-half")
                                rn.on("blur", lambda: save(lambda: store.rename(eid, rn.value)))
                                if not b["flex"]:
                                    tlbl = "Goal amount" if is_goal else "Amount / target"
                                    tg = ui.number(tlbl, value=b["target"], prefix="$").props("dense outlined hide-bottom-space").classes("cd-half")
                                    tg.on("blur", lambda: act(lambda: store.set_target(eid, float(tg.value or 0))))
                            if is_goal:
                                with ui.row().classes("items-center q-gutter-sm w-full q-mt-sm"):
                                    td = ui.input("Target month", value=b.get("target_date") or "").props("dense outlined hide-bottom-space type=month").classes("cd-half")
                                    td.on("blur", lambda: act(lambda: store.set_target_date(eid, td.value)))
                                    fq = ui.select(_FREQ, value=b["frequency"] or "", label="Contribution cadence").props("dense outlined").classes("cd-half")
                                    fq.on("update:model-value", lambda: act(lambda: store.set_frequency(eid, fq.value)))
                            elif not is_vault:
                                with ui.row().classes("items-center q-gutter-sm w-full q-mt-sm"):
                                    dd = ui.select(_dueday_options(), value=_dueday_key(b["due_day"]), label="Due day").props("dense outlined").classes("cd-half")
                                    dd.on("update:model-value", lambda: act(lambda: store.set_due_day(eid, dd.value)))
                                    fq = ui.select(_FREQ, value=b["frequency"] or "", label="Frequency (if no due day)").props("dense outlined").classes("cd-half")
                                    fq.on("update:model-value", lambda: act(lambda: store.set_frequency(eid, fq.value)))
                            hint = _period_hint(b)
                            if hint:
                                ui.html(f'<div class="cd-sub" style="margin:8px 2px 2px;color:var(--accent)">↳ {hint}</div>')
                            notes = ui.textarea("Notes", value=b.get("notes") or "").props("dense outlined hide-bottom-space autogrow").classes("w-full q-mt-sm")
                            notes.on("blur", lambda: save(lambda: store.set_notes(eid, notes.value)))
                            if b["type"] == "spend":
                                with ui.element("div").classes("cd-bs-toggle"):
                                    ui.html('<div><div class="t">Flexible</div><div class="s">Variable spending — no set target</div></div>')
                                    fx = ui.switch(value=b["flex"]).props("dense color=indigo")
                                    fx.on("update:model-value", lambda: act(lambda: store.set_flex(eid, fx.value)))
                            with ui.element("div").classes("cd-bs-toggle"):
                                ui.html('<div><div class="t">Handled this month</div><div class="s">Covered elsewhere — not owed from this budget</div></div>')
                                hd = ui.switch(value=b["handled"]).props("dense color=indigo")
                                hd.on("update:model-value", lambda: act(lambda: store.toggle_handled(eid)))

                    # ── BILL SCHEDULE — a bucket can convert to a bill split and back ──
                    def _open_convert():
                        to_split = not b["split"]
                        cdlg = ui.dialog().props("position=bottom")
                        with cdlg, ui.card().classes("cd-sheet"):
                            ui.html('<div class="cd-hdl"></div>')
                            if to_split:
                                due_txt = ""
                                if b["due_day"] is not None:
                                    due_txt = f' and its {_dueday_options().get(_dueday_key(b["due_day"]), "due date")} due date'
                                ui.html(f'<div class="cd-sh-title">Split “{_esc(b["name"])}” into bills</div>')
                                ui.html('<div class="cdm-sub">Bill split is for one bucket whose money leaves on '
                                        '<b>different dates</b> — a utility that bills on the 5th and again on the 20th, say. '
                                        f'Its current {money(b["target"])} target{due_txt} becomes the first bill; add the rest '
                                        'after. You can merge it back to a single bucket anytime.</div>')

                                def do_split():
                                    act(lambda: store.convert_to_split(eid)); cdlg.close()
                                with ui.row().classes("w-full justify-end q-gutter-sm q-mt-md"):
                                    ui.button("Cancel", on_click=cdlg.close).props("flat no-caps")
                                    ui.button("Convert to bill split", on_click=do_split).props("unelevated color=indigo no-caps")
                            else:
                                n, total = len(b["items"]), b["items_total"]
                                soonest = next((it["due_day"] for it in b["items"] if not it.get("paid") and it["due_day"] is not None),
                                               next((it["due_day"] for it in b["items"] if it["due_day"] is not None), None))
                                ui.html(f'<div class="cd-sh-title">Convert “{_esc(b["name"])}” back</div>')
                                ui.html(f'<div class="cdm-sub">This bucket holds {n} bill{"s" if n != 1 else ""}. '
                                        'Turn them into separate buckets — one per bill — or collapse them into one.</div>')
                                choice = ui.radio(
                                    {"separate": f"Separate buckets — one per bill ({n}), each keeping its own amount & due date",
                                     "one": f"One bucket — collapse into a single {money(total)} bucket"},
                                    value="separate").props("color=indigo").classes("w-full")
                                duesel = ui.select(_dueday_options(), value=_dueday_key(soonest),
                                                   label="Due day for the single bucket").props("outlined dense").classes("w-full q-mt-sm")
                                duesel.bind_visibility_from(choice, "value", backward=lambda v: v == "one")
                                ui.html('<div class="cd-sub" style="margin:10px 2px 0;line-height:1.5">Funded money follows the '
                                        'bills; anything left over returns to Ready to Assign. Splitting again later is easy.</div>')

                                def do_back():
                                    if choice.value == "separate":
                                        # the split bucket is deleted — close the sheet, don't refresh its body
                                        try:
                                            store.explode_to_buckets(eid)
                                        except Exception as ex:
                                            ui.notify(str(ex)[:150], type="warning"); return
                                        cdlg.close(); dlg.close(); refresh_page()
                                        ui.notify("Split into separate buckets.", type="positive")
                                    else:
                                        act(lambda: store.convert_to_bucket(eid, duesel.value)); cdlg.close()
                                with ui.row().classes("w-full justify-end q-gutter-sm q-mt-md"):
                                    ui.button("Cancel", on_click=cdlg.close).props("flat no-caps")
                                    ui.button("Convert", on_click=do_back).props("unelevated color=indigo no-caps")
                        cdlg.open()

                    if b["type"] == "spend" and not b["flex"]:
                        with ui.element("div").classes("cd-bs-sec"):
                            if not b["split"]:
                                ui.html('<div class="cd-bs-lbl">Bill schedule</div>')
                                with ui.element("div").classes("cd-bs-card"):
                                    ui.html('<div class="cd-sub" style="line-height:1.55;margin-bottom:13px">Right now this is '
                                            'one bucket with one due date. If the same money leaves on <b>different dates</b> — '
                                            'utilities on the 5th and the 20th, a subscription bundle — split it into separate '
                                            'bills, each with its own due date and Forecast entry.</div>')
                                    ui.button("Split into bills", on_click=_open_convert).props("outline color=indigo no-caps")
                            else:
                                with ui.row().classes("items-center no-wrap w-full").style("margin-bottom:11px"):
                                    ui.html('<div class="cd-bs-lbl" style="margin:0">Bill schedule</div>')
                                    ui.space()
                                    ui.button("↩ Merge to one bucket", on_click=_open_convert).props("flat color=grey no-caps size=sm")
                            if b["split"]:
                                if b["items"]:
                                    need = round(sum(it.get("item_gap", 0.0) for it in b["items"] if not it.get("paid")), 2)
                                    if need > 0.005:
                                        ui.html(f'<div class="cd-recon">{money(b["items_total"])} scheduled across {len(b["items"])} bills '
                                                f'· <b>{money(need)} still to fund</b> — nearest bills first</div>')
                                    else:
                                        ui.html(f'<div class="cd-recon ok">Every bill funded ✓ · {money(b["items_total"])} '
                                                f'scheduled across {len(b["items"])}</div>')

                                def _item_row(it):
                                    tag_txt, tag_cls, row_cls = _item_due_tag(it)
                                    with ui.element("div").classes("cd-bill " + row_cls):
                                        with ui.element("div").classes("cd-bill-r1"):
                                            pd = ui.checkbox(value=it["paid"]).props("dense color=positive")
                                            pd.on("update:model-value", lambda i=it["id"]: act(lambda: store.toggle_item_paid(eid, i)))
                                            nm = ui.input(value=it["name"]).props("dense borderless hide-bottom-space").classes("nm")
                                            nm.on("blur", lambda i=it["id"], el=nm: save(lambda: store.edit_item(eid, i, name=el.value)))
                                            if it.get("paid"):
                                                ui.html('<span class="cd-idtag green">paid</span>')
                                            elif it.get("item_gap", 0.0) > 0.005:
                                                ui.html(f'<span class="cd-idtag red">needs {money(it["item_gap"])}</span>')
                                            else:
                                                ui.html('<span class="cd-idtag green">funded</span>')
                                            ui.button(icon="close", on_click=lambda i=it["id"]: act(lambda: store.remove_item(eid, i))).props("flat dense round size=sm color=grey")
                                        with ui.element("div").classes("cd-bill-r2"):
                                            am = ui.number(value=it["amount"], format="%.2f", prefix="$").props("dense outlined hide-bottom-space").style("width:106px")
                                            am.on("blur", lambda i=it["id"], el=am: act(lambda: store.edit_item(eid, i, amount=el.value)))
                                            du = ui.select(_dueday_options(), value=_dueday_key(it["due_day"])).props("dense outlined").style("width:104px")
                                            du.on("update:model-value", lambda i=it["id"], el=du: act(lambda: store.edit_item(eid, i, due_day=el.value)))
                                            ui.html(f'<span class="cd-idtag {tag_cls}">{tag_txt}</span>')
                                for it in b["items"]:
                                    _item_row(it)

                                with ui.element("div").classes("cd-bill"):
                                    with ui.row().classes("items-center no-wrap w-full q-gutter-xs"):
                                        inm = ui.input(placeholder="Add a bill — e.g. Netflix").props("dense outlined hide-bottom-space").style("flex:1;min-width:0")
                                        iamt = ui.number(placeholder="0.00", format="%.2f", prefix="$").props("dense outlined hide-bottom-space").style("width:92px")
                                        idd = ui.select(_dueday_options(), value="", label="Due").props("dense outlined").style("width:86px")

                                        def add_it():
                                            if not (inm.value or "").strip():
                                                ui.notify("Name the bill.", type="warning"); return
                                            act(lambda: store.add_item(eid, inm.value, iamt.value or 0, idd.value))
                                        ui.button(icon="add", on_click=add_it).props("flat dense round color=indigo")

                    with ui.row().classes("w-full items-center cd-bs-foot"):
                        def do_delete():
                            try:
                                store.delete(eid)
                            except Exception as e:
                                ui.notify(str(e)[:140], type="warning"); return
                            dlg.close(); refresh_page()
                        ui.button("Delete bucket", on_click=do_delete).props("flat color=red no-caps size=sm")
                        ui.space()
                        ui.button("Done", on_click=dlg.close).props("unelevated color=indigo no-caps")
                body()
            dlg.open()

        # ── create bucket ─────────────────────────────────────────────────────
        def _open_create():
            with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
                ui.html('<div class="cd-hdl"></div>')
                ui.html('<div class="cd-sh-title">New bucket</div>')
                ui.html('<div class="cdm-sub">Name it, give it a home, and tell the Forecast when it is due.</div>')
                name = ui.input("Name").props("dense outlined").classes("w-full")
                cats = store.categories()
                with ui.row().classes("w-full items-center no-wrap q-gutter-xs"):
                    cat = ui.select({c["id"]: c["name"] for c in cats}, label="Category",
                                    value=(cats[0]["id"] if cats else None)).props("dense outlined").style("flex:1;min-width:0")

                    def add_cat_inline():
                        nm = (newcat.value or "").strip()
                        if not nm:
                            ui.notify("Type a category name first.", type="warning"); return
                        try:
                            store.add_category(nm)
                        except Exception as e:
                            ui.notify(str(e)[:140], type="warning"); return
                        fresh = store.categories()
                        cid = next((x["id"] for x in fresh if x["name"] == nm), None)
                        cat.set_options({x["id"]: x["name"] for x in fresh}, value=cid)
                        newcat.set_value("")
                        ui.notify(f"Added category “{nm}”.", type="positive")
                    ui.button(icon="add", on_click=add_cat_inline).props("flat dense round color=indigo").tooltip("Create a new category")
                newcat = ui.input(placeholder="…or type a new category name").props("dense outlined hide-bottom-space").classes("w-full")
                typ = ui.select({"spend": "Spend", "goal": "Goal", "vault": "Vault"}, label="Type", value="spend").props("dense outlined").classes("w-full")
                flex = ui.switch("Flexible — variable spending, no target").bind_visibility_from(typ, "value", backward=lambda v: v == "spend")
                typ.on("update:model-value", lambda: typ.value != "spend" and flex.set_value(False))
                tgt = ui.number("Amount / target", value=0).props("dense outlined").classes("w-full") \
                    .bind_visibility_from(flex, "value", backward=lambda v: not v)
                with ui.row().classes("w-full q-gutter-sm").bind_visibility_from(typ, "value", backward=lambda v: v != "vault"):
                    dd = ui.select(_dueday_options(), value="", label="Due day").props("dense outlined").classes("cd-half") \
                        .bind_visibility_from(typ, "value", backward=lambda v: v == "spend")
                    tm = ui.input("Target month").props("dense outlined hide-bottom-space type=month").classes("cd-half") \
                        .bind_visibility_from(typ, "value", backward=lambda v: v == "goal")
                    fq = ui.select(_FREQ, value="", label="Frequency").props("dense outlined").classes("cd-half")
                notes = ui.textarea("Notes (optional)").props("dense outlined hide-bottom-space autogrow").classes("w-full")

                def create():
                    try:
                        store.add_bucket((name.value or "New bucket").strip(), cat.value, typ.value,
                                         float(tgt.value or 0),
                                         due_day=(dd.value if typ.value == "spend" else None),
                                         frequency=(fq.value or None), flex=bool(flex.value),
                                         target_date=(tm.value if typ.value == "goal" else None),
                                         notes=notes.value or "")
                    except Exception as e:
                        ui.notify(str(e)[:140], type="warning"); return
                    dlg.close(); refresh_page()
                with ui.row().classes("w-full justify-end q-mt-sm"):
                    ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                    ui.button("Create bucket", on_click=create).props("unelevated color=indigo no-caps")
            dlg.open()

        # ── the one distribution flow: rules → fill what's due → get ahead ─────
        # Shared by the Buckets "Distribute" button and a logged paycheck, so both
        # read the same. You stay in charge — every line is a checkbox.
        def _open_distribute(paycheck_amount=None):
            st = store.distribute_steps(paycheck_amount)
            has_any = st["external"] or st["internal"] or st["obligations"]
            if not has_any and st["unallocated"] <= 0.005:
                ui.notify("Nothing to distribute — every dollar already has a job. ✨", type="positive")
                return
            checked = ({"ext:" + e["id"] for e in st["external"]}
                       | {"int:" + r["id"] for r in st["internal"]}
                       | {"ob:" + o["key"] for o in st["obligations"]})   # get-ahead starts off

            def _compute():
                cap = st["unallocated"]
                remaining, total, extra = cap, 0.0, {}
                amt = {}
                for e in st["external"]:
                    if "ext:" + e["id"] in checked:
                        a = round(min(e["amount"], remaining), 2)
                        amt["ext:" + e["id"]] = a; remaining = round(remaining - a, 2); total += a
                for r in st["internal"]:
                    if "int:" + r["id"] in checked:
                        a = round(min(r["amount"], remaining), 2)
                        amt["int:" + r["id"]] = a; remaining = round(remaining - a, 2); total += a
                        extra[r["bucket_id"]] = round(extra.get(r["bucket_id"], 0) + a, 2)
                for o in st["obligations"]:
                    if "ob:" + o["key"] in checked:
                        # split items are distinct bills sharing one pool — each funds its
                        # own gap; non-split obligations net out any rule already aimed here.
                        gap_now = o["gap"] if o.get("split_item") else max(0.0, round(o["gap"] - extra.get(o["id"], 0), 2))
                        a = round(min(gap_now, remaining), 2)
                        amt["ob:" + o["key"]] = a; remaining = round(remaining - a, 2); total += a
                        extra[o["id"]] = round(extra.get(o["id"], 0) + a, 2)
                for n in st["next"]:
                    if "next:" + n["id"] in checked:
                        a = round(min(n["amount"], remaining), 2)
                        amt["next:" + n["id"]] = a; remaining = round(remaining - a, 2); total += a
                return amt, round(total, 2), round(remaining, 2)

            dialog_host.clear()
            with dialog_host:
                dlg = ui.dialog().props("position=bottom")
            with dlg, ui.card().classes("cd-sheet"):
                @ui.refreshable
                def body():
                    amt, total, remaining = _compute()

                    def toggle(k):
                        checked.discard(k) if k in checked else checked.add(k)
                        ui.run_javascript(_CAP_SHEET); body.refresh(); ui.run_javascript(_RES_SHEET)

                    def srow(key, name, detail, kind="fund", tag=None):
                        on = key in checked
                        a = amt.get(key, 0.0)
                        with ui.row().classes("w-full items-center no-wrap cd-srow" + ("" if on else " off")):
                            cb = ui.checkbox(value=on).props("dense")
                            cb.on("update:model-value", lambda k=key: toggle(k))
                            if tag:
                                ui.html(f'<span class="cd-idtag {tag[1]}">{tag[0]}</span>')
                            with ui.element("div").style("flex:1;min-width:0"):
                                ui.html(f'<div class="cd-srow-name">{_esc(name)}</div>'
                                        f'<div class="cd-srow-det">{_esc(detail)}</div>')
                            if kind == "transfer":
                                txt, col = (f'−{money(a)}' if on else '—'), "var(--warn-ink)"
                            else:
                                txt, col = (f'+{money(a)}' if (on and a > 0.005) else '—'), "var(--pos)"
                            ui.html(f'<div class="cd-srow-amt" style="color:{col if on else "var(--muted)"}">{txt}</div>')

                    ui.html('<div class="cd-hdl"></div>')
                    if paycheck_amount:
                        ui.html(f'<div class="cd-sh-title">Distribute your {money(paycheck_amount)} paycheck</div>')
                        ui.html(f'<div class="cdm-sub">You\'re in charge — review each step, uncheck anything you\'d '
                                f'rather handle yourself. <b style="color:var(--accent)">{money(st["unallocated"])}</b> unallocated.</div>')
                    else:
                        ui.html('<div class="cd-sh-title">Give every dollar a job</div>')
                        ui.html(f'<div class="cdm-sub"><b style="color:var(--accent)">{money(st["unallocated"])}</b> unallocated. '
                                f'Uncheck anything you\'d rather handle yourself.</div>')

                    # Step 1 — rules
                    if st["external"] or st["internal"]:
                        ui.html('<div class="cd-step-h"><span class="cd-step-n">1</span>Apply your rules</div>')
                        for e in st["external"]:
                            srow("ext:" + e["id"], e["name"], e["detail"] + " → savings", kind="transfer",
                                 tag=("transfer", "amber"))
                        for r in st["internal"]:
                            srow("int:" + r["id"], r["bucket_name"], f'{r["name"]} · {r["detail"]}')

                    # Step 2 — obligations
                    ui.html('<div class="cd-step-h"><span class="cd-step-n">2</span>Fill what\'s due</div>')
                    if st["obligations"]:
                        for o in st["obligations"]:
                            srow("ob:" + o["key"], o["name"], f'needs {money(o["gap"])}',
                                 tag=_days_tag(o["days_until_due"]))
                    else:
                        ui.html('<div class="cd-sub" style="padding:2px 2px 8px">Nothing underfunded — every bill is covered. ✓</div>')

                    # Step 3 — get ahead (optional)
                    if st["next"] and remaining > 0.005:
                        ui.html('<div class="cd-step-h"><span class="cd-step-n">3</span>Get ahead · pre-fund next month</div>')
                        ui.html('<div class="cd-sub" style="margin:-6px 2px 8px">You\'ve covered what\'s due. Put the rest '
                                'toward next month\'s bills to build a buffer.</div>')
                        for n in st["next"]:
                            srow("next:" + n["id"], n["name"], f'another {money(n["amount"])}',
                                 tag=_days_tag(n["days_until_due"]))

                    # totals
                    rcol = "var(--pos)" if remaining <= 0.005 else "var(--muted)"
                    ui.html(f'<div class="cd-dtot"><span>Distributing <b>{money(total)}</b></span>'
                            f'<span style="color:{rcol}">{money(remaining)} left unallocated</span></div>')

                    def do_apply():
                        amt2, _t, _r = _compute()
                        frm, to = store.default_transfer_accounts()
                        moved = 0.0
                        try:
                            for e in st["external"]:
                                a = amt2.get("ext:" + e["id"], 0)
                                if a > 0.005:
                                    store.add_transfer(frm, to, a, e["name"]); moved += a
                            for r in st["internal"]:
                                a = amt2.get("int:" + r["id"], 0)
                                if a > 0.005:
                                    store.assign(r["bucket_id"], "unallocated", a); moved += a
                            for o in st["obligations"]:
                                a = amt2.get("ob:" + o["key"], 0)
                                if a > 0.005:
                                    store.assign(o["id"], "unallocated", a); moved += a
                            for n in st["next"]:
                                a = amt2.get("next:" + n["id"], 0)
                                if a > 0.005:
                                    store.prefund(n["id"], a); moved += a   # lands in NEXT month
                        except Exception as e:
                            ui.notify(str(e)[:150], type="warning"); return
                        dlg.close(); refresh_page()
                        ui.notify(f"Distributed {money(round(moved, 2))}.", type="positive")

                    with ui.row().classes("w-full items-center cd-sh-foot"):
                        ui.button("Skip", on_click=dlg.close).props("flat color=grey no-caps size=sm")
                        ui.space()
                        ui.button("Apply distribution", on_click=do_apply).props("unelevated color=indigo no-caps")
                body()
            dlg.open()

        def actionbar():
            un = store.metrics()["unallocated"]
            with ui.element("div").classes("cd-actionbar"):
                ui.html('<div class="cd-newbtn">＋ New bucket</div>').on("click", lambda _: _open_create())
                if un > 0.005:
                    ui.html(f'<div class="cd-distbtn hot">⚡ Distribute {money(un)}</div>').on("click", lambda _: _open_distribute())
                    ui.html('<span class="cd-hint">Tap a bucket to manage · or distribute what\'s unallocated</span>').style("margin-left:auto")
                else:
                    ui.html('<span class="cd-hint">Every dollar has a job — tap any bucket to manage it</span>').style("margin-left:auto")

        def monthbar():
            # Month navigation is a live-data feature — the demo has no month model.
            if demo or not hasattr(store, "view_month"):
                return
            vm = store.view_month()
            opts, ids = vm["options"], [o["mid"] for o in vm["options"]]
            labels = {o["mid"]: (o["label"] + (" · planning" if o["rel"] == "future" else "")) for o in opts}
            i = ids.index(vm["mid"]) if vm["mid"] in ids else len(ids) - 1
            rel = next((o["rel"] for o in opts if o["mid"] == vm["mid"]), "current")

            def go(mid):
                store.set_view_month(mid); refresh_page()

            with ui.element("div").classes("cd-monthbar" + ("" if vm["is_current"] else f" {rel}")):
                ui.html('<span class="cd-mb-ic">‹</span>').on("click", lambda _: go(ids[max(0, i - 1)]))
                sel = ui.select(labels, value=vm["mid"]).props("dense borderless options-dense").classes("cd-mb-sel")
                sel.on("update:model-value", lambda: go(sel.value))
                ui.html('<span class="cd-mb-ic">›</span>').on("click", lambda _: go(ids[min(len(ids) - 1, i + 1)]))
                if not vm["is_current"]:
                    tag = "catching up · previous month" if rel == "past" else "planning ahead"
                    ui.html(f'<span class="cd-mb-tag {rel}">{tag}</span>')
                    ui.html('<span class="cd-mb-today">Back to today →</span>').on("click", lambda _: go(vm["today"]))

        @ui.refreshable
        def content():
            if state["view"] == "ledger":
                _ledger_view(store, refresh_page, _open_distribute)
            elif state["view"] == "forecast":
                _forecast_view(store, refresh_page)
            elif state["view"] == "settings":
                _settings_view(store, refresh_page)
            elif state["view"] == "reports":
                _reports_view(store, refresh_page, monthbar)
            else:
                hero()
                monthbar()
                actionbar()
                buckets()
        content()


# ── Ledger pillar ─────────────────────────────────────────────────────────────
def _today_iso() -> str:
    return date.today().isoformat()


def _cur_ym() -> str:
    return date.today().strftime("%Y-%m")


def _month_name(ym: str) -> str:
    try:
        y, m = ym.split("-")[:2]
        return date(int(y), int(m), 1).strftime("%B")
    except (ValueError, TypeError):
        return ym


def _bucket_options(store) -> dict:
    """Non-vault buckets a transaction can point at, {id: name}."""
    opts = {}
    for g in store.groups():
        for r in g["rows"]:
            if r["type"] != "vault":
                opts[r["id"]] = r["name"]
    return opts


def _best_bucket(payee: str, opts: dict):
    """Guess which bucket a payee belongs in by name — exact match first, then a
    loose contains either way (so a 'Netflix' charge finds the 'Netflix' bucket)."""
    p = (payee or "").strip().lower()
    if not p:
        return None
    for bid, name in opts.items():
        if name.strip().lower() == p:
            return bid
    for bid, name in opts.items():
        n = name.strip().lower()
        if n and (n in p or p in n):
            return bid
    return None


_TX_ICON = {"expense": "−", "income": "+", "refund": "↺", "transfer": "→"}
_TX_CLASS = {"expense": "out", "income": "in", "refund": "refund", "transfer": "transfer"}


def _ledger_view(store, refresh_bg, on_paycheck=None):
    """The cleared-money timeline: income, spending and refunds, grouped by day."""
    q = {"v": ""}
    cur_ym = _cur_ym()
    # Which months are expanded — the current cycle opens by default, the rest stay
    # collapsed until tapped. Kept on the store so it survives list refreshes.
    exp = getattr(store, "_led_expanded", None)
    if exp is None:
        exp = {_cur_ym()}
        store._led_expanded = exp

    def _toggle(ym):
        exp.discard(ym) if ym in exp else exp.add(ym)
        lst.refresh()

    def _open_tx(tid=None):
        rows = store.transactions()
        existing = next((t for t in rows if t["id"] == tid), None) if tid else None
        st = {"kind": existing["kind"] if existing else "expense"}
        bopts = _bucket_options(store)

        with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
            ui.html('<div class="cd-hdl"></div>')
            ui.html(f'<div class="cd-sh-title">{"Edit transaction" if existing else "Add transaction"}</div>')
            ui.html('<div class="cdm-sub">Expense draws from a bucket · income lifts Unallocated · '
                    'refund returns money to a bucket · transfer moves it between accounts.</div>')

            @ui.refreshable
            def segbar():
                with ui.element("div").classes("cd-seg"):
                    for k, label in (("expense", "Expense"), ("income", "Income"),
                                     ("refund", "Refund"), ("transfer", "Transfer")):
                        cls = "cd-segopt" + (f" on {_TX_CLASS[k]}" if st["kind"] == k else "")
                        ui.html(f'<div class="{cls}">{label}</div>').on("click", lambda _, kk=k: _set_kind(kk)).style("flex:1")
            segbar()

            with ui.row().classes("w-full q-gutter-sm q-mt-sm"):
                amount = ui.number("Amount", value=existing["amount"] if existing else None, format="%.2f") \
                    .props("outlined dense hide-bottom-space").classes("cd-half")
                datef = ui.input("Date", value=existing["date"] if existing else _today_iso()) \
                    .props("outlined dense hide-bottom-space type=date").classes("cd-half")

            bucket_row = ui.row().classes("w-full q-mt-sm")
            with bucket_row:
                bval = existing["bucket_id"] if (existing and existing.get("bucket_id") in bopts) else next(iter(bopts), None)
                bucket = ui.select(bopts, label="Bucket", value=bval).props("outlined dense").classes("w-full")
            bucket_row.set_visibility(st["kind"] in ("expense", "refund"))

            # transfer: between two accounts
            accts = store.accounts()
            aopts = {a["id"]: f'{a["name"]} · {money(a["balance"])}' for a in accts}
            chk = next((a["id"] for a in accts if a["type"] == "budget"), next(iter(aopts), None))
            sav = next((a["id"] for a in accts if a["type"] != "budget"), chk)
            acct_row = ui.row().classes("w-full q-gutter-sm q-mt-sm")
            with acct_row:
                from_sel = ui.select(aopts, label="From", value=(existing.get("from_acct") if existing else chk) or chk).props("outlined dense").classes("cd-half")
                to_sel = ui.select(aopts, label="To", value=(existing.get("to_acct") if existing else sav) or sav).props("outlined dense").classes("cd-half")
            acct_row.set_visibility(st["kind"] == "transfer")

            payee = ui.select(store.payees(), label="Payee / note", value=existing["desc"] if existing else None,
                              with_input=True, new_value_mode="add-unique").props("outlined dense").classes("w-full q-mt-sm")

            has_rules = any(r["active"] for r in store.rules())
            auto = ui.switch("Auto-distribute across my rules", value=has_rules and not existing).classes("q-mt-xs")
            auto.set_visibility(st["kind"] == "income" and has_rules)

            def _set_kind(k):
                st["kind"] = k
                segbar.refresh()
                bucket_row.set_visibility(k in ("expense", "refund"))
                acct_row.set_visibility(k == "transfer")
                auto.set_visibility(k == "income" and has_rules)

            def save():
                amt = float(amount.value or 0)
                if amt <= 0:
                    ui.notify("Enter an amount greater than zero.", type="warning"); return
                kind = st["kind"]
                desc = (payee.value or "").strip()
                when = datef.value or _today_iso()
                open_paycheck = None
                try:
                    if kind == "transfer":
                        if from_sel.value == to_sel.value:
                            ui.notify("Pick two different accounts.", type="warning"); return
                        if existing:
                            store.delete_transaction(existing["id"])
                        store.add_transfer(from_sel.value, to_sel.value, amt, desc, when)
                    else:
                        bid = bucket.value if kind in ("expense", "refund") else None
                        if kind in ("expense", "refund") and not bid:
                            ui.notify("Pick a bucket for this transaction.", type="warning"); return
                        if existing and kind == existing["kind"]:
                            ch = {"amount": amt, "desc": desc, "date": when}
                            if bid:
                                ch["envelope_id"] = bid
                            store.edit_transaction(existing["id"], **ch)
                        else:
                            if existing:                   # type changed → replace
                                store.delete_transaction(existing["id"])
                            store.add_transaction(kind, amt, bid, desc, when)
                            if kind == "income" and not existing and auto.value and on_paycheck:
                                open_paycheck = amt        # hand off to the distribute flow
                except Exception as e:
                    ui.notify(str(e)[:150], type="warning"); return
                dlg.close(); refresh_bg()
                if open_paycheck is not None:
                    on_paycheck(open_paycheck)

            with ui.row().classes("w-full items-center q-mt-md"):
                if existing:
                    def do_delete():
                        try:
                            store.delete_transaction(existing["id"])
                        except Exception as e:
                            ui.notify(str(e)[:150], type="warning"); return
                        dlg.close(); refresh_bg()
                    ui.button("Delete", on_click=do_delete).props("flat color=red no-caps")
                ui.space()
                ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                ui.button("Save" if existing else "Add", on_click=save).props("unelevated color=indigo no-caps")
        dlg.open()

    def _open_fix(orphans):
        """Re-home current-month transactions whose bucket was removed. Orphans are
        grouped by payee, each group pre-set to its best-matching bucket."""
        opts = _bucket_options(store)
        # group by payee (fallback: the old bucket name, then a catch-all)
        groups: "dict[str, list]" = {}
        for r in orphans:
            key = (r["desc"] or r["bucket_name"] or "Unlabelled").strip()
            groups.setdefault(key, []).append(r)
        picks = {}  # payee -> {"sel": select, "tids": [...]}
        with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
            ui.html('<div class="cd-hdl"></div>')
            ui.html('<div class="cd-sh-title">Re-home these transactions</div>')
            ui.html(f'<div class="cdm-sub">{len(orphans)} transaction'
                    f'{"s" if len(orphans) != 1 else ""} this month lost their bucket — a bucket they '
                    'pointed at was removed or exploded. Pick a home for each; matching payees are grouped.</div>')
            if not opts:
                ui.html('<div class="cd-sub" style="padding:6px 2px">No buckets to move them into — make one first.</div>')
            for payee, rows in sorted(groups.items(), key=lambda kv: -sum(x["amount"] for x in kv[1])):
                total = round(sum(x["amount"] for x in rows), 2)
                with ui.element("div").classes("cd-fixrow"):
                    ui.html(f'<div class="cd-fix-info"><div class="cd-fix-payee">{_esc(payee)}</div>'
                            f'<div class="cd-sub">{len(rows)} · {money(total)}</div></div>')
                    sel = ui.select(opts, value=_best_bucket(payee, opts), label="Move to") \
                        .props("outlined dense").classes("cd-fix-sel")
                    picks[payee] = {"sel": sel, "tids": [x["id"] for x in rows]}

            def do_fix():
                moves = [(g["tids"], g["sel"].value) for g in picks.values() if g["sel"].value]
                if not moves:
                    ui.notify("Pick a bucket for at least one group.", type="warning"); return
                try:
                    for tids, bid in moves:
                        store.reassign_transactions(tids, bid)
                except Exception as e:
                    ui.notify(str(e)[:150], type="warning"); return
                done = sum(len(t) for t, _ in moves)
                dlg.close(); refresh_bg()
                ui.notify(f"Re-homed {done} transaction{'s' if done != 1 else ''}.", type="positive")
            with ui.row().classes("w-full items-center q-mt-md"):
                ui.space()
                ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                ui.button("Re-home all", on_click=do_fix).props("unelevated color=indigo no-caps")
        dlg.open()

    def _tx_row(r):
        row = ui.element("div").classes("cd-tx")
        with row:
            ui.html(f'<div class="cd-tx-ic {_TX_CLASS[r["kind"]]}">{_TX_ICON[r["kind"]]}</div>')
            if r["kind"] == "transfer":
                title = _esc(r["bucket_name"] or "Transfer")
                meta = f'<span class="cd-tx-tag">{_esc(r["desc"])}</span>' if r["desc"] else '<span class="cd-tx-tag">account transfer</span>'
            elif r["kind"] == "income":
                title = _esc(r["desc"] or "Income")
                meta = '<span class="cd-tx-tag">Income → Unallocated</span>'
            elif r.get("orphaned") and r["date"][:7] == cur_ym:
                title = _esc(r["desc"] or "Expense")
                meta = '<span class="cd-tx-tag cd-tx-orphan">⚠ needs a bucket</span>'
            else:
                title = _esc(r["desc"] or r["bucket_name"])
                verb = "refund →" if r["kind"] == "refund" else ""
                meta = (f'<span class="cd-tx-tag">{verb}<i style="background:{r["color"]}"></i>'
                        f'{_esc(r["bucket_name"] or "—")}</span>')
            with ui.element("div"):
                ui.html(f'<div class="cd-tx-name">{title}</div>')
                ui.html(f'<div class="cd-tx-meta">{meta}</div>')
            pos = r["kind"] in ("income", "refund")
            signed = ("+" if pos else "−") + money(r["amount"]).lstrip("-")
            ui.html(f'<div class="cd-tx-amt {"pos" if pos else "neg"} mono">{signed}</div>')
        row.on("click", lambda _, t=r["id"]: _open_tx(t))

    def _render_days(rows, day_end):
        """A run of day-groups. day_end maps date→end-of-day balance (or None to
        omit the running balance, e.g. in search results)."""
        groups: list[tuple[str, list]] = []
        for r in rows:
            if not groups or groups[-1][0] != r["date"]:
                groups.append((r["date"], []))
            groups[-1][1].append(r)
        for datestr, items in groups:
            lbl, sub = _day_label(datestr)
            right = ""
            if day_end is not None:
                bal = day_end.get(datestr, 0.0)
                bcol = "var(--neg)" if bal < 0 else "var(--muted)"
                right = f'<span class="t" style="color:{bcol}">balance {money(bal)}</span>'
            with ui.element("div").classes("cd-daygrp"):
                with ui.element("div").classes("cd-daylbl"):
                    ui.html(f'<b>{lbl}</b><span class="d">{sub}</span>{right}')
                with ui.element("div").classes("cd-txcard"):
                    for r in items:
                        _tx_row(r)

    @ui.refreshable
    def lst():
        all_rows = store.transactions()
        if not all_rows:
            ui.html('<div class="cd-empty"><div class="big">No transactions yet.</div>'
                    'Add your first one above to start the timeline.</div>')
            return

        qv = q["v"].strip().lower()
        if qv:                                        # search: flat matches, no collapse
            rows = [r for r in all_rows if qv in r["desc"].lower() or qv in r["bucket_name"].lower()]
            if not rows:
                ui.html('<div class="cd-empty"><div class="big">No matches.</div>Try another search.</div>')
                return
            _render_days(rows, None)
            return

        # end-of-day running balances, computed from the full history
        total = store.ledger_metrics()["balance"]
        day_sign, dates_desc, seen = {}, [], set()
        for r in all_rows:
            s = r["amount"] if r["kind"] in ("income", "refund") else -r["amount"]
            day_sign[r["date"]] = round(day_sign.get(r["date"], 0.0) + s, 2)
            if r["date"] not in seen:
                seen.add(r["date"]); dates_desc.append(r["date"])
        day_end, running = {}, total
        for dt in dates_desc:
            day_end[dt] = round(running, 2)
            running = round(running - day_sign[dt], 2)

        # year → month → day, all newest-first; collapse months, current one open
        from collections import OrderedDict
        tree: "OrderedDict[str, OrderedDict]" = OrderedDict()
        for r in all_rows:
            y = r["date"][:4] if len(r["date"]) >= 4 else "—"
            ym = r["date"][:7] if len(r["date"]) >= 7 else "—"
            tree.setdefault(y, OrderedDict()).setdefault(ym, OrderedDict()).setdefault(r["date"], []).append(r)

        for year, months in tree.items():
            ui.html(f'<div class="cd-year">{year}</div>')
            for ym, days in months.items():
                is_open = ym in exp
                n = sum(len(v) for v in days.values())
                endbal = day_end.get(next(iter(days)), 0.0)
                inc = sum(r["amount"] for ds in days.values() for r in ds if r["kind"] in ("income", "refund"))
                out = sum(r["amount"] for ds in days.values() for r in ds if r["kind"] == "expense")
                card = ui.element("div").classes("cd-month" + (" open" if is_open else ""))
                with card:
                    hd = ui.element("div").classes("cd-month-hd")
                    with hd:
                        ui.html('<span class="cd-month-chev">▸</span>')
                        ui.html(f'<span class="cd-month-nm">{_month_name(ym)}</span>')
                        ui.html(f'<span class="cd-month-meta">{n} txn{"" if n == 1 else "s"} · '
                                f'{money(inc)} in · {money(out)} out</span>')
                        ui.html(f'<span class="cd-month-bal mono">{money(endbal)}</span>').style("margin-left:auto")
                    hd.on("click", lambda _, k=ym: _toggle(k))
                    if is_open:
                        with ui.element("div").classes("cd-month-body"):
                            _render_days([r for ds in days.values() for r in ds], day_end)

    # ── render: header stats · action bar · search · list ─────────────────────
    lm = store.ledger_metrics()
    with ui.element("div").classes("cd-led-hd"):
        for label, val, col in (("In checking", lm["balance"], "var(--ink)"),
                                ("Income · this month", lm["income"], "var(--pos)"),
                                ("Spent · this month", lm["spent"], "var(--neg)")):
            with ui.element("div").classes("cd-led-stat"):
                ui.html(f'<div class="l">{label}</div>'
                        f'<div class="v mono" style="color:{col}">{money(val)}</div>')

    if any(r["kind"] == "roundup" and r["active"] for r in store.rules()):
        rs = store.roundup_status()
        if rs["swept_this_month"] > 0.005 or rs["pending"] > 0.005:
            ui.html(f'<div class="cd-roundup-tally">🪙 Roundup savings this month: '
                    f'<b>{money(rs["swept_this_month"])}</b>'
                    + (f' · {money(rs["pending"])} queued' if rs["pending"] > 0.005 else '') + '</div>')

    with ui.element("div").classes("cd-actionbar"):
        ui.html('<div class="cd-newbtn">＋ Add transaction</div>').on("click", lambda _: _open_tx())
        ui.html('<span class="cd-hint">Tap any row to edit · income lifts Unallocated</span>').style("margin-left:auto")

    # current-month transactions whose bucket was removed/exploded — flag to re-home
    orphans = [r for r in store.transactions() if r.get("orphaned") and r["date"][:7] == cur_ym]
    if orphans:
        n, tot = len(orphans), round(sum(r["amount"] for r in orphans), 2)
        with ui.element("div").classes("cd-orphan-banner"):
            ui.html(f'<div><div class="cd-ob-t">⚠ {n} transaction{"s" if n != 1 else ""} this month lost '
                    f'their bucket</div><div class="cd-ob-s">{money(tot)} needs a home — a bucket they used '
                    'was removed or split apart.</div></div>')
            ui.button("Re-home", on_click=lambda o=orphans: _open_fix(o)).props("unelevated color=deep-orange no-caps size=sm")

    search = ui.input(placeholder="Search payee or bucket…").props("outlined dense clearable").classes("w-full cd-led-search")
    search.on("update:model-value", lambda: (q.__setitem__("v", search.value or ""), lst.refresh()))
    lst()


# ── Settings pillar (income + allocation rules → the Forecast engine) ─────────
_FREQ_LBL = {"weekly": "Weekly", "biweekly": "Bi-weekly",
             "semimonthly": "Semi-monthly", "monthly": "Monthly"}
_RULE_KIND_LBL = {"internal": "Internal — fund a bucket", "external": "External — leaves the budget",
                  "roundup": "Roundup — spare change to a bucket"}
_RULE_VT_LBL = {"fund": "Fund to target", "pct": "% of each paycheck", "fixed": "$ fixed amount"}


def _friendly_date(iso: str) -> str:
    try:
        d = date.fromisoformat(iso[:10])
        return d.strftime("%b ") + str(d.day)
    except (ValueError, TypeError):
        return iso or "—"


def _next_payday(p: dict, today: date | None = None) -> str:
    """The real next occurrence for a paycheck, computed forward from whatever
    anchor is on file — however stale (a raw anchor set once at signup and
    never touched again is normal, not a bug). Never shows a display date in
    the past: Settings should always read as "next Sep 11", never "next Apr 15"."""
    today = today or date.today()
    dates = forecast.pay_dates(p["anchor"], p["freq"], today, today + timedelta(days=400))
    return dates[0].isoformat() if dates else (p["anchor"] or "")


def _reconciled_paychecks(store, today: date) -> list[dict]:
    """Self-healing fix for the Forecast double-counting a paycheck that's
    already landed: if a paycheck's cadence puts an occurrence on `today` AND
    a real income transaction dated today with a close-enough amount is
    already in the Ledger, project from its NEXT occurrence instead — no
    click, no stored-anchor mutation, re-evaluated fresh on every render."""
    todays_income = [t for t in store.transactions()
                     if t.get("kind") == "income" and (t.get("date") or "")[:10] == today.isoformat()]
    used_ids = set()
    out = []
    for pc in store.paychecks():
        pc = dict(pc)
        if forecast.pay_dates(pc["anchor"], pc["freq"], today, today):
            tol = max(5.0, pc["amount"] * 0.03)
            match = next((t for t in todays_income if t["id"] not in used_ids
                         and abs(t["amount"] - pc["amount"]) <= tol), None)
            if match:
                used_ids.add(match["id"])
                nxt = forecast.next_payday(pc["anchor"], pc["freq"], today)
                if nxt:
                    pc["anchor"] = nxt
        out.append(pc)
    return out


def _rule_value_text(r: dict) -> str:
    if r["kind"] == "roundup":
        return "spare change"
    if r["value_type"] == "fund":
        return "fund to target"
    if r["value_type"] == "pct":
        return f'{r["value"]:g}%'
    return money(r["value"])


def _all_bucket_options(store) -> dict:
    opts = {}
    for g in store.groups():
        for r in g["rows"]:
            opts[r["id"]] = r["name"]
    return opts


def _settings_view(store, refresh_bg):
    def _do(fn):
        try:
            fn()
        except Exception as e:
            ui.notify(str(e)[:150], type="warning"); return
        refresh_bg()

    # ── paycheck add/edit sheet ──
    def _open_paycheck(pid=None):
        existing = next((p for p in store.paychecks() if p["id"] == pid), None) if pid else None
        with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
            ui.html('<div class="cd-hdl"></div>')
            ui.html(f'<div class="cd-sh-title">{"Edit paycheck" if existing else "Add paycheck"}</div>')
            ui.html('<div class="cdm-sub">Recurring income the Forecast lands on your calendar.</div>')
            label = ui.input("Label", value=existing["label"] if existing else "").props("outlined dense hide-bottom-space").classes("w-full")
            with ui.row().classes("w-full q-gutter-sm q-mt-sm"):
                amount = ui.number("Amount", value=existing["amount"] if existing else None, format="%.2f").props("outlined dense hide-bottom-space").classes("cd-half")
                freq = ui.select(_FREQ_LBL, value=existing["freq"] if existing else "biweekly", label="Frequency").props("outlined dense").classes("cd-half")
            anchor = ui.input("Next paycheck date", value=existing["anchor"] if existing else _today_iso()).props("outlined dense hide-bottom-space type=date").classes("w-full q-mt-sm")

            def save():
                if not (label.value or "").strip():
                    ui.notify("Give the paycheck a label.", type="warning"); return
                if existing:
                    store.edit_paycheck(existing["id"], label=label.value, amount=amount.value,
                                        freq=freq.value, anchor=anchor.value)
                else:
                    store.add_paycheck(label.value, amount.value, freq.value, anchor.value)
                dlg.close(); refresh_bg()
            with ui.row().classes("w-full items-center q-mt-md"):
                if existing:
                    ui.button("Delete", on_click=lambda: (store.delete_paycheck(existing["id"]), dlg.close(), refresh_bg())).props("flat color=red no-caps")
                ui.space()
                ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                ui.button("Save" if existing else "Add", on_click=lambda: _do(save)).props("unelevated color=indigo no-caps")
        dlg.open()

    # ── rule add/edit sheet ──
    def _open_rule(rid=None):
        existing = next((r for r in store.rules() if r["id"] == rid), None) if rid else None
        allb = _all_bucket_options(store)
        with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
            ui.html('<div class="cd-hdl"></div>')
            ui.html(f'<div class="cd-sh-title">{"Edit rule" if existing else "Add allocation rule"}</div>')
            ui.html('<div class="cdm-sub">Applied to every paycheck — internal rules fund a bucket, '
                    'external rules move money out of the budget, roundup rules share in the spare-change pool.</div>')
            name = ui.input("Rule name", value=existing["name"] if existing else "").props("outlined dense hide-bottom-space").classes("w-full")
            kind = ui.select(_RULE_KIND_LBL, value=existing["kind"] if existing else "internal", label="Type").props("outlined dense").classes("w-full q-mt-sm")
            bucket_row = ui.row().classes("w-full q-mt-sm")
            with bucket_row:
                bval = existing["bucket_id"] if (existing and existing.get("bucket_id") in allb) else next(iter(allb), None)
                bucket = ui.select(allb, label="Fund which bucket", value=bval).props("outlined dense").classes("w-full")
            bucket_row.bind_visibility_from(kind, "value", backward=lambda v: v in ("internal", "roundup"))
            amount_row = ui.row().classes("w-full q-gutter-sm q-mt-sm")
            with amount_row:
                vtype = ui.select(_RULE_VT_LBL, value=existing["value_type"] if existing else "fund", label="How much").props("outlined dense").classes("cd-half")
                value = ui.number("Value", value=existing["value"] if existing else None, format="%.2f").props("outlined dense hide-bottom-space").classes("cd-half")
                value.bind_visibility_from(vtype, "value", backward=lambda v: v != "fund")
            amount_row.bind_visibility_from(kind, "value", backward=lambda v: v != "roundup")
            ui.html('<div class="cdm-sub">Every active roundup rule shares the queued pool equally when it '
                    'sweeps — no amount to set.</div>').bind_visibility_from(kind, "value", backward=lambda v: v == "roundup")

            def save():
                if not (name.value or "").strip():
                    ui.notify("Name the rule.", type="warning"); return
                k = kind.value
                vt = "fixed" if k == "roundup" else vtype.value
                bid = bucket.value if k in ("internal", "roundup") else None
                val = 0 if (vt == "fund" or k == "roundup") else float(value.value or 0)
                if existing:
                    store.edit_rule(existing["id"], name=name.value, kind=k, bucket_id=bid,
                                    value=val, value_type=vt)
                else:
                    store.add_rule(name.value, k, bid, val, vt)
                dlg.close(); refresh_bg()
            with ui.row().classes("w-full items-center q-mt-md"):
                if existing:
                    ui.button("Delete", on_click=lambda: (store.delete_rule(existing["id"]), dlg.close(), refresh_bg())).props("flat color=red no-caps")
                ui.space()
                ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                ui.button("Save" if existing else "Add", on_click=lambda: _do(save)).props("unelevated color=indigo no-caps")
        dlg.open()

    # ── roundup threshold sheet ──
    def _open_roundup_threshold():
        rs = store.roundup_status()
        with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
            ui.html('<div class="cd-hdl"></div>')
            ui.html('<div class="cd-sh-title">Sweep threshold</div>')
            ui.html('<div class="cdm-sub">Spare change queues up quietly until it crosses this amount, '
                    'then it sweeps into your roundup bucket(s) in one move.</div>')
            amt = ui.number("Threshold", value=rs["threshold"], format="%.2f").props(
                "outlined dense hide-bottom-space prefix=$").classes("w-full q-mt-sm")

            def save():
                v = float(amt.value or 0)
                if v <= 0:
                    ui.notify("Threshold has to be more than $0.", type="warning"); return
                store.set_roundup_threshold(v)
                dlg.close(); refresh_bg()
            with ui.row().classes("w-full items-center q-mt-md"):
                ui.space()
                ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                ui.button("Save", on_click=lambda: _do(save)).props("unelevated color=indigo no-caps")
        dlg.open()

    def _paycheck_row(p):
        today = date.today()
        next_date = _next_payday(p, today)
        due = next_date == today.isoformat()
        row = ui.element("div").classes("cd-setrow")
        with row:
            ui.html('<div class="cd-set-ic in">$</div>')
            body = ui.element("div").style("min-width:0;cursor:pointer")
            with body:
                ui.html(f'<div class="cd-set-name">{_esc(p["label"])}</div>')
                ui.html(f'<div class="cd-set-meta">{_FREQ_LBL.get(p["freq"], p["freq"])} · '
                        f'next {_friendly_date(next_date)}</div>')
            body.on("click", lambda _, i=p["id"]: _open_paycheck(i))
            with ui.element("div").style("display:flex;flex-direction:column;align-items:flex-end;gap:4px"):
                ui.html(f'<div class="cd-set-val mono">{money(p["amount"])}</div>')
                if due:
                    got = ui.html('<div class="cd-gotpaid" title="Already got paid — remove today\'s '
                                  'projected paycheck (and its rule transfers) from the Forecast">✓ Got paid</div>')
                    got.on("click", lambda _, i=p["id"]: _do(lambda: store.advance_paycheck(i)))

    def _rule_row(r):
        with ui.element("div").classes("cd-setrow" + ("" if r["active"] else " off")):
            tg = ui.html(f'<div class="cd-toggle {"on" if r["active"] else ""}">{"ON" if r["active"] else "OFF"}</div>')
            tg.on("click", lambda _, i=r["id"]: _do(lambda: store.toggle_rule(i)))
            body = ui.element("div").style("min-width:0;cursor:pointer")
            with body:
                ui.html(f'<div class="cd-set-name">{_esc(r["name"])}</div>')
                if r["kind"] == "external":
                    tgt = "leaves the budget"
                elif r["kind"] == "roundup":
                    tgt = f'→ {_esc(r["bucket_name"] or "—")} · shares the pool'
                else:
                    tgt = f'→ {_esc(r["bucket_name"] or "—")}'
                ui.html(f'<div class="cd-set-meta"><span class="cd-rule-badge {r["kind"]}">{r["kind"]}</span> {tgt}</div>')
            body.on("click", lambda _, i=r["id"]: _open_rule(i))
            ui.html(f'<div class="cd-set-val mono">{_rule_value_text(r)}</div>')

    _ACCT_LBL = {"budget": "Budget · drives Ready to Assign", "savings": "Savings", "cash": "Cash"}
    _ACCT_IC = {"budget": "$", "savings": "★", "cash": "≈"}

    def _account_row(a):
        with ui.element("div").classes("cd-setrow"):
            ui.html(f'<div class="cd-set-ic in">{_ACCT_IC.get(a["type"], "≈")}</div>')
            body = ui.element("div").style("min-width:0;cursor:pointer")
            with body:
                ui.html(f'<div class="cd-set-name">{_esc(a["name"])}</div>')
                ui.html(f'<div class="cd-set-meta">{_ACCT_LBL.get(a["type"], "Cash")}</div>')
            body.on("click", lambda _, i=a["id"]: _open_account(i))
            ui.html(f'<div class="cd-set-val mono">{money(a["balance"])}</div>')

    def _open_account(aid=None):
        accts = store.accounts()
        existing = next((a for a in accts if a["id"] == aid), None) if aid else None
        is_budget = bool(existing and existing.get("is_budget"))
        with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
            ui.html('<div class="cd-hdl"></div>')
            ui.html(f'<div class="cd-sh-title">{"Edit account" if existing else "Add cash-flow account"}</div>')
            ui.html('<div class="cdm-sub">Cash-flow accounts only — checking, savings, cash. '
                    'The budget account drives Ready to Assign; the rest are here so you can see '
                    'your money, and move between them with a transfer.</div>')
            name = ui.input("Name", value=existing["name"] if existing else "").props("outlined dense hide-bottom-space").classes("w-full")
            with ui.row().classes("w-full q-gutter-sm q-mt-sm"):
                tval = existing["type"] if existing else "savings"
                type_sel = ui.select({"savings": "Savings", "cash": "Cash"}, value=(tval if tval in ("savings", "cash") else "cash"),
                                     label="Type").props("outlined dense").classes("cd-half")
                if is_budget:
                    type_sel.set_enabled(False)
                opening = ui.number("Opening balance", value=existing["opening"] if existing else 0, format="%.2f", prefix="$").props("outlined dense hide-bottom-space").classes("cd-half")

            def save():
                if not (name.value or "").strip():
                    ui.notify("Give the account a name.", type="warning"); return
                if existing:
                    store.edit_account(existing["id"], name=name.value,
                                       type=(None if is_budget else type_sel.value), opening=opening.value)
                else:
                    store.add_account(name.value, type_sel.value, opening.value)
                dlg.close(); refresh_bg()
            with ui.row().classes("w-full items-center q-mt-md"):
                if existing and not is_budget:
                    ui.button("Remove", on_click=lambda: _do(lambda: (store.archive_account(existing["id"]), dlg.close()))).props("flat color=red no-caps")
                ui.space()
                ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                ui.button("Save" if existing else "Add", on_click=lambda: _do(save)).props("unelevated color=indigo no-caps")
        dlg.open()

    def _cat_row(c):
        with ui.element("div").classes("cd-setrow"):
            ui.html(f'<span class="cd-dot" style="background:{c.get("color", "#9aa0b5")};margin-right:4px"></span>')
            nm = ui.input(value=c["name"]).props("dense borderless hide-bottom-space").style("flex:1;min-width:0;font-weight:600")
            nm.on("blur", lambda i=c["id"], el=nm: _do(lambda: store.rename_category(i, el.value)))
            n = c.get("bucket_count", 0)
            ui.html(f'<span class="cd-set-meta" style="white-space:nowrap">{n} bucket{"s" if n != 1 else ""}</span>')
            ui.button(icon="keyboard_arrow_up", on_click=lambda i=c["id"]: _do(lambda: store.move_category(i, "up"))).props("flat dense round size=sm color=grey")
            ui.button(icon="keyboard_arrow_down", on_click=lambda i=c["id"]: _do(lambda: store.move_category(i, "down"))).props("flat dense round size=sm color=grey")
            ui.button(icon="close", on_click=lambda i=c["id"]: _do(lambda: store.archive_category(i))).props("flat dense round size=sm color=grey")

    def _open_add_category():
        with ui.dialog().props("position=bottom") as dlg, ui.card().classes("cd-sheet"):
            ui.html('<div class="cd-hdl"></div>')
            ui.html('<div class="cd-sh-title">New category</div>')
            ui.html('<div class="cdm-sub">A group for your buckets — Housing, Food, Subscriptions.</div>')
            name = ui.input("Name").props("outlined dense hide-bottom-space").classes("w-full")

            def save():
                if not (name.value or "").strip():
                    ui.notify("Name the category.", type="warning"); return
                store.add_category(name.value); dlg.close(); refresh_bg()
            with ui.row().classes("w-full justify-end q-mt-md"):
                ui.button("Cancel", on_click=dlg.close).props("flat no-caps")
                ui.button("Add", on_click=lambda: _do(save)).props("unelevated color=indigo no-caps")
        dlg.open()

    # ── render ──
    ui.html('<div class="cd-set-title">Settings</div>'
            '<div class="cdm-sub" style="margin-bottom:18px">Your accounts, your income, and how each '
            'paycheck is split — the engine behind the Forecast.</div>')

    # ── Reconcile — where every allocated dollar lives (catches ghosts/over-alloc) ──
    rec = store.reconcile()
    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Reconcile · where your money is</div>')
        neg = rec["rts"] < -0.005
        rts_col = "var(--neg)" if neg else "var(--pos)"
        ui.html(f'''<div class="cd-recon-grid">
            <div><div class="l">Checking</div><div class="v mono">{money(rec["cash"])}</div></div>
            <div><div class="l">Assigned to buckets</div><div class="v mono">{money(rec["in_buckets"])}</div></div>
            <div><div class="l">Unallocated</div><div class="v mono" style="color:{rts_col}">{money(rec["rts"])}</div></div>
          </div>''')
        if abs(rec["residual"]) > 0.005:
            ui.html(f'<div class="cd-recon-warn">⚠ Books off by {money(abs(rec["residual"]))} — checking should equal '
                    'unallocated + assigned. This is a bug; tell me and I\'ll trace it.</div>')
        elif neg:
            ui.html(f'<div class="cd-recon-warn">You\'ve assigned <b>{money(abs(rec["rts"]))}</b> more than your '
                    'checking holds. Usually this means money was budgeted twice — e.g. re-funding buckets whose '
                    'money was already spent. Pull the excess back from over-funded buckets to return to $0.</div>')
        else:
            ui.html('<div class="cd-sub" style="padding:2px 2px 6px">Every dollar accounted for ✓</div>')
        if rec["ghosts"]:
            names = ", ".join(f'{_esc(g["name"])} ({money(g["amount"])})' for g in rec["ghosts"][:6])
            ui.html(f'<div class="cd-recon-ghost">👻 <b>{money(rec["ghost_total"])}</b> is stranded on removed '
                    f'buckets: {names}. This is dead weight from an explode/delete — clear it to tidy up '
                    '(does not change your Unallocated).</div>')
            ui.button("Clear stranded allocations", on_click=lambda: _do(
                lambda: store.clear_ghost_allocations())).props("outline color=deep-orange no-caps size=sm")

    # ── buckets you can't see — filed under a category that's gone missing ────
    orphans = store.orphaned_buckets() if hasattr(store, "orphaned_buckets") else []
    if orphans:
        cat_opts = {c["id"]: c["name"] for c in store.categories()}
        with ui.element("div").classes("cd-setcard"):
            ui.html('<div class="cd-set-seclbl">⚠ Buckets you can\'t see</div>')
            ntot = round(sum(o["available"] for o in orphans), 2)
            ui.html(f'<div class="cd-sub" style="padding:2px 2px 12px;line-height:1.5">'
                    f'{len(orphans)} bucket{"s" if len(orphans) != 1 else ""} — {money(ntot)} total — '
                    'filed under a category that no longer exists. The Buckets screen only shows buckets whose '
                    'category is still active, so these were invisible. The money is real and unaffected; '
                    'give each one a home to bring it back.</div>')
            for o in orphans:
                with ui.element("div").classes("cd-orow"):
                    ui.html(f'<div class="cd-orow-info"><div class="cd-orow-name">{_esc(o["name"])}</div>'
                            f'<div class="cd-sub">{money(o["available"])} available · {money(o["funded"])} funded'
                            f'{" · " + money(o["target"]) + " target" if o["target"] else ""}</div></div>')
                    if cat_opts:
                        sel = ui.select(cat_opts, label="Move to category").props("outlined dense").classes("cd-orow-sel")
                        ui.button("Save", on_click=lambda i=o["id"], s=sel: _do(
                            lambda: store.recategorize_bucket(i, s.value))).props("unelevated color=indigo no-caps size=sm")
                    else:
                        ui.html('<span class="cd-sub">Add a category first, in the card below.</span>')

    # ── possible duplicate buckets — same name, likely from an explode ────────
    dupes = store.duplicate_buckets() if hasattr(store, "duplicate_buckets") else []
    if dupes:
        visible_ids = {r["id"] for g in store.groups() for r in g["rows"]}
        with ui.element("div").classes("cd-setcard"):
            ui.html('<div class="cd-set-seclbl">⚠ Possible duplicate buckets</div>')
            ui.html('<div class="cd-sub" style="padding:2px 2px 12px;line-height:1.5">'
                    'These buckets share a name — often two of the same bill after a split exploded one that '
                    'already existed on its own. Merge folds one\'s money and history into the other; nothing is lost.</div>')
            for group in dupes:
                with ui.element("div").classes("cd-dupgrp"):
                    ui.html(f'<div class="cd-orow-name">{_esc(group[0]["name"])} ({len(group)})</div>')
                    for b in group:
                        hidden = "" if b["id"] in visible_ids else " · hidden"
                        with ui.element("div").classes("cd-orow"):
                            ui.html(f'<div class="cd-orow-info"><div class="cd-sub">{money(b["available"])} available · '
                                    f'{money(b["funded"])} funded{hidden}</div></div>')
                            keep_target = next(o for o in group if o["id"] != b["id"])
                            ui.button("Merge into the other one", on_click=lambda keep=keep_target["id"], drop=b["id"]: _do(
                                lambda: store.merge_buckets(keep, drop))).props("outline color=deep-orange no-caps size=sm")

    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Cash-flow accounts</div>')
        accts = store.accounts()
        for a in accts:
            _account_row(a)
        total = sum(a["balance"] for a in accts)
        ui.html(f'<div class="cd-tally">Total cash <b>{money(round(total, 2))}</b> across {len(accts)} '
                f'account{"s" if len(accts) != 1 else ""}</div>')
        ui.html('<div class="cd-set-add">＋ Add account</div>').on("click", lambda _: _open_account())

    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Categories · how buckets are grouped</div>')
        cats = store.categories()
        if not cats:
            ui.html('<div class="cd-sub" style="padding:4px 2px 10px">No categories yet — add one to group your buckets.</div>')
        for c in cats:
            _cat_row(c)
        ui.html('<div class="cd-set-add">＋ Add category</div>').on("click", lambda _: _open_add_category())

    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Income · paychecks</div>')
        pcs = _reconciled_paychecks(store, date.today())
        if not pcs:
            ui.html('<div class="cd-sub" style="padding:4px 2px 10px">No paychecks yet — add your income so the Forecast can project forward.</div>')
        for p in pcs:
            _paycheck_row(p)
        ui.html('<div class="cd-set-add">＋ Add paycheck</div>').on("click", lambda _: _open_paycheck())

    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Allocation rules · applied to each paycheck</div>')
        summ = store.rules_summary()
        parts = ([f'{summ["pct"]:g}%'] if summ["pct"] > 0 else []) + ([money(summ["fixed"])] if summ["fixed"] > 0 else [])
        commit = " + ".join(parts) if parts else "nothing yet"
        warn = ' · <span style="color:var(--neg);font-weight:700">⚠ over 100%</span>' if summ["over"] else ""
        ui.html(f'<div class="cd-tally">Commits <b>{commit}</b> of each paycheck{warn}</div>')
        for r in store.rules():
            _rule_row(r)
        ui.html('<div class="cd-set-add">＋ Add rule</div>').on("click", lambda _: _open_rule())

    active_roundup = [r for r in store.rules() if r["kind"] == "roundup" and r["active"]]
    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Roundup savings · spare change, swept automatically</div>')
        if not active_roundup:
            ui.html('<div class="cd-sub" style="padding:4px 2px 10px">No active roundup rule yet — add '
                    'one above (Type: Roundup) to start banking spare change on every purchase.</div>')
        else:
            rs = store.roundup_status()
            pct = min(1.0, rs["pending"] / rs["threshold"]) if rs["threshold"] > 0 else 0.0
            ui.html(f'<div class="cd-tally">Queued <b>{money(rs["pending"])}</b> of {money(rs["threshold"])} '
                    f'threshold · swept <b>{money(rs["swept_this_month"])}</b> this month</div>')
            ui.html(f'<div class="cd-bar"><div class="cd-bar-fill" '
                    f'style="width:{pct * 100:.0f}%;background:var(--violet)"></div></div>')
        with ui.row().classes("w-full items-center justify-between q-mt-sm"):
            ui.html(f'<div class="cd-sub">Sweep threshold: <b>{money(store.roundup_status()["threshold"])}</b></div>')
            ui.button("Change", on_click=_open_roundup_threshold).props("flat dense no-caps color=indigo size=sm")


# ── Reports (Budget vs Actual + spending mix, for the viewed month) ───────────
def _reports_view(store, refresh_bg, monthbar=None):
    """Budget vs Actual and where the money went — computed from the buckets as
    they stand in the viewed month, so the month bar drives the report too."""
    groups = store.groups()

    # Budget vs Actual: only spend buckets actually spend. A flex bucket has no
    # budget line, so it contributes to spending but not to the variance table.
    bva, grand_b, grand_s = [], 0.0, 0.0
    spend_by_cat = []
    for g in groups:
        rows, cb, cs = [], 0.0, 0.0
        cat_spent = 0.0
        for r in g["rows"]:
            cat_spent += r["spent"]
            if r["type"] != "spend":
                continue
            budget = 0.0 if r["flex"] else round(r["target"], 2)
            spent = round(r["spent"], 2)
            if budget < 0.005 and spent < 0.005:
                continue
            pct = min(999, round(spent / budget * 100)) if budget > 0.005 else 0
            rows.append({"name": r["name"], "budget": budget, "spent": spent,
                         "variance": round(budget - spent, 2), "pct": pct, "flex": r["flex"]})
            cb += budget; cs += spent
        if rows:
            bva.append({"name": g["name"], "color": g["color"], "budget": round(cb, 2),
                        "spent": round(cs, 2), "variance": round(cb - cs, 2), "buckets": rows})
            grand_b += cb; grand_s += cs
        if cat_spent > 0.005:
            spend_by_cat.append({"name": g["name"], "color": g["color"], "spent": round(cat_spent, 2)})

    ui.html('<div class="cd-set-title">Reports</div>'
            '<div class="cdm-sub" style="margin-bottom:8px">Budget vs actual and where your money '
            'went — for the month you\'re viewing.</div>')
    if monthbar:
        monthbar()

    # ── Budget vs Actual ──
    with ui.element("div").classes("cd-setcard"):
        gv = round(grand_b - grand_s, 2)
        gcol = "var(--pos)" if gv >= 0 else "var(--neg)"
        ui.html('<div class="cd-set-seclbl">Budget vs actual</div>')
        if not bva:
            ui.html('<div class="cd-sub" style="padding:6px 2px">No budgeted spending in this month yet.</div>')
        for c in bva:
            vcol = "var(--pos)" if c["variance"] >= 0 else "var(--neg)"
            ui.html(f'''<div class="cd-rpt-cat">
                <span class="cd-dot" style="background:{c['color']}"></span>
                <span class="cd-rpt-cat-name">{_esc(c['name'])}</span>
                <span class="cd-rpt-cat-nums">{money(c['spent'])} <span style="color:var(--muted)">of {money(c['budget'])}</span>
                  · <b style="color:{vcol}">{money(abs(c['variance']))} {'left' if c['variance'] >= 0 else 'over'}</b></span>
              </div>''')
            for b in c["buckets"]:
                if b["flex"]:
                    meta = f'{money(b["spent"])} spent · flexible'
                    bar = '<div class="cd-rpt-bar"><div class="cd-rpt-fill flex" style="width:100%"></div></div>'
                else:
                    over = b["variance"] < 0
                    w = min(100, b["pct"])
                    bar = (f'<div class="cd-rpt-bar"><div class="cd-rpt-fill {"over" if over else ""}" '
                           f'style="width:{w}%"></div></div>')
                    meta = f'{money(b["spent"])} of {money(b["budget"])} · {b["pct"]}%'
                ui.html(f'''<div class="cd-rpt-bkt">
                    <div class="cd-rpt-bkt-top"><span>{_esc(b['name'])}</span><span class="cd-sub">{meta}</span></div>
                    {bar}
                  </div>''')
        if bva:
            ui.html(f'<div class="cd-tally">Overall <b>{money(grand_s)}</b> spent of '
                    f'<b>{money(grand_b)}</b> budgeted · <b style="color:{gcol}">'
                    f'{money(abs(gv))} {"under" if gv >= 0 else "over"}</b></div>')

    # ── Spending mix ──
    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Where the money went</div>')
        total = sum(c["spent"] for c in spend_by_cat)
        if total < 0.005:
            ui.html('<div class="cd-sub" style="padding:6px 2px">No spending recorded in this month.</div>')
        for c in sorted(spend_by_cat, key=lambda x: x["spent"], reverse=True):
            share = round(c["spent"] / total * 100) if total > 0 else 0
            ui.html(f'''<div class="cd-rpt-bkt">
                <div class="cd-rpt-bkt-top"><span><span class="cd-dot" style="background:{c['color']}"></span>
                  {_esc(c['name'])}</span><span class="cd-sub">{money(c['spent'])} · {share}%</span></div>
                <div class="cd-rpt-bar"><div class="cd-rpt-fill" style="width:{share}%;background:{c['color']}"></div></div>
              </div>''')


# ── Forecast pillar (forward cash-flow projection) ────────────────────────────
def _forecast_bills(store) -> list[dict]:
    """Scheduled spend buckets that hit the calendar (feed the projection). A split
    bucket contributes one dated bill per line-item, so each subscription lands on
    its own due date; a paid item is skipped for the current cycle."""
    out = []
    for g in store.groups():
        for r in g["rows"]:
            if r["type"] != "spend" or r["flex"] or r["handled"]:
                continue
            if r["split"] and r["items"]:
                for it in r["items"]:
                    if it["amount"] > 0.005 and it["due_day"] is not None:
                        # per-item funded state: the slice of the pool that reached this bill
                        out.append({"id": None, "name": f'{r["name"]} · {it["name"]}', "amount": it["amount"],
                                    "spent": it["amount"] if it.get("paid") else 0.0,
                                    "available": round(it["amount"] - it.get("item_gap", 0.0), 2),
                                    "due_day": it["due_day"], "frequency": None})
            elif r["target"] > 0 and (r["due_day"] is not None
                                      or r["frequency"] in ("weekly", "biweekly", "triweekly", "monthly")):
                # money already gotten-ahead-of (prefunded into a future month) is
                # otherwise invisible here — bucket_available only sees today's month
                prefunded = store.prefunded(r["id"]) if hasattr(store, "prefunded") else 0.0
                out.append({"id": r["id"], "name": r["name"], "amount": r["target"], "spent": r["spent"],
                            "available": round(r["available"] + prefunded, 2), "due_day": r["due_day"],
                            "frequency": r["frequency"]})
    return out


def _forecast_vaults(store) -> list[dict]:
    """Vault/goal buckets — pure accumulation, no due date, so the Forecast tracks
    their growth (seeded from today, topped up by internal rules aimed at them)
    instead of a funded/shortfall check."""
    return [{"id": r["id"], "name": r["name"], "available": r["available"]}
            for g in store.groups() for r in g["rows"] if r["type"] in ("vault", "goal")]


def _forecast_chart(res: dict) -> str:
    """A balance-over-time line chart (inline SVG) for the projection."""
    traj = res["trajectory"]
    if len(traj) < 2:
        return ""
    t0 = date.fromisoformat(res["today"])
    horizon = max(res["horizon_days"], 1)
    xs = [(date.fromisoformat(p["date"]) - t0).days for p in traj]
    ys = [p["balance"] for p in traj]
    W, H, padL, padR, padT, padB = 820, 210, 10, 12, 16, 22
    cw, ch = W - padL - padR, H - padT - padB
    lo, hi = min(ys + [0]), max(ys)
    rng = (hi - lo) or 1.0

    def X(day):
        return padL + (day / horizon) * cw

    def Y(v):
        return padT + (1 - (v - lo) / rng) * ch

    pts = list(zip((X(x) for x in xs), (Y(y) for y in ys)))
    line = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = (f"M {pts[0][0]:.1f},{Y(0):.1f} L "
            + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            + f" L {pts[-1][0]:.1f},{Y(0):.1f} Z")
    col = "#f43f5e" if res["shortfall"] else "#f59e0b" if res["safe_to_spend"] < 500 else "#10b981"
    zero_line = ""
    if lo < 0:
        zy = Y(0)
        zero_line = (f'<line x1="{padL}" y1="{zy:.1f}" x2="{padL + cw}" y2="{zy:.1f}" '
                     f'stroke="#f43f5e" stroke-width="1" stroke-dasharray="4 4" opacity=".6"/>')
    lx, ly = X((date.fromisoformat(res["low"]["date"]) - t0).days), Y(res["low"]["balance"])
    lbl_anchor = "start" if lx < W * 0.5 else "end"
    lbl_dx = 8 if lx < W * 0.5 else -8
    low_txt = f'${abs(res["low"]["balance"]):,.0f}'
    end_lbl = date.fromisoformat(res["end_date"]).strftime("%b ") + str(date.fromisoformat(res["end_date"]).day)
    return f'''<svg viewBox="0 0 {W} {H}" class="cd-fc-svg" preserveAspectRatio="none">
      <defs><linearGradient id="fcg" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" stop-color="{col}" stop-opacity=".22"/>
        <stop offset="1" stop-color="{col}" stop-opacity="0"/>
      </linearGradient></defs>
      {zero_line}
      <path d="{area}" fill="url(#fcg)"/>
      <path d="{line}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4.5" fill="{col}"/>
      <text x="{lx + lbl_dx:.1f}" y="{ly - 9:.1f}" text-anchor="{lbl_anchor}" font-size="11" font-weight="700" fill="{col}">low {low_txt}</text>
      <text x="{padL}" y="{H - 6}" font-size="10" fill="#9aa0b5">today</text>
      <text x="{padL + cw}" y="{H - 6}" text-anchor="end" font-size="10" fill="#9aa0b5">{end_lbl}</text>
    </svg>'''


_FC_ICON = {"income": "+", "transfer": "→", "bill": "−", "internal": "◇"}


# kind -> (severity color class, icon)
_WARN_META = {
    "overdraft":          ("red", "⚠"),
    "no_income":          ("red", "⚠"),
    "rules_exceed":       ("red", "⚠"),
    "paycheck_shortfall": ("amber", "⚠"),
    "bucket_shortfall":   ("amber", "⚠"),
    "vault_lever":        ("violet", "◇"),
    "ahead":              ("green", "↑"),
    "all_clear":          ("green", "✓"),
}


def _warn_msg(w: dict) -> str:
    """Full detail sentence for one warning — same wording everywhere it appears
    (hero detail line, period card), so there's one source of truth."""
    k = w["kind"]
    if k == "overdraft":
        m = f"Balance dips to {money(w['end_balance'])}."
        if w.get("vaults_total", 0) > 0.005:
            m += (f" You have {money(w['vaults_total'])} in vault savings — since that money never left "
                  "checking, releasing some toward what's short would close the gap without new income.")
        return m
    if k == "no_income":
        return f"No paycheck lands in this stretch, but {money(w['total_out'])} still goes out."
    if k == "rules_exceed":
        return f"Your own rules alone ({money(w['rules_total'])}) outspend this paycheck ({money(w['income'])}) — before a single bill."
    if k == "paycheck_shortfall":
        return f"Even if this whole paycheck went to nothing but catching up, you'd still be {money(w['gap'])} short."
    if k == "bucket_shortfall":
        who = ", ".join(f'{_esc(s["name"])} needs {money(s["shortfall"])} more' for s in w["shortfalls"][:3])
        more = len(w["shortfalls"]) - 3
        who += f" +{more} more" if more > 0 else ""
        return f"{money(w['shortfall_total'])} still needed across underfunded bills — {who}."
    if k == "vault_lever":
        return f"Skipping this period's {money(w['internal_vault'])} vault contribution would leave you at {money(w['would_be'])} instead."
    if k == "ahead":
        return f"{money(w['net'])} left over after everything this period — a good time to get ahead on next month's bills."
    return "Fully funded and solvent this period."


def _warn_headline(w: dict) -> str:
    """Short version for the hero verdict line."""
    return {
        "overdraft": "Heads up — your balance dips below zero",
        "no_income": "No paycheck lands before bills come due",
        "rules_exceed": "Your own rules outspend this paycheck",
        "paycheck_shortfall": f"This paycheck falls {money(w.get('gap', 0))} short",
        "bucket_shortfall": "Some bills aren't fully saved for yet",
        "vault_lever": "You have a lever if things get tight",
        "ahead": "You're ahead",
        "all_clear": "You're on track",
    }.get(w["kind"], "You're on track")


def _forecast_view(store, refresh_bg):
    hz = getattr(store, "_fc_horizon", 90)

    def set_hz(n):
        store._fc_horizon = n
        refresh_bg()

    def toggle_p(k):
        exp.discard(k) if k in exp else exp.add(k)
        refresh_bg()

    if not store.paychecks():
        ui.html('<div class="cd-set-title">Forecast</div>'
                '<div class="cd-empty" style="margin-top:14px"><div class="big">No income set yet.</div>'
                'Add your paychecks in Settings (⚙, top-right) and your forward projection appears here.</div>')
        return

    sched = store.scheduled() if hasattr(store, "scheduled") else []
    vaults = _forecast_vaults(store)
    paychecks = _reconciled_paychecks(store, date.today())
    res = forecast.project(store.metrics()["cash"], paychecks, store.rules(),
                           _forecast_bills(store), vaults=vaults, scheduled=sched, horizon_days=hz)
    # Which periods are expanded — the current one opens by default.
    exp = getattr(store, "_fc_expanded", None)
    if exp is None:
        exp = {res["periods"][0]["start"]} if res["periods"] else set()
        store._fc_expanded = exp
    low_when = _friendly_date(res["low"]["date"])
    # The very next paycheck — the exact question "will THIS one afford everything
    # due" — surfaced up top so it's visible without digging into the periods below.
    next_period = next((p for p in res["periods"] if not p["is_gap"]), None)
    next_warn = (next_period["warnings"][0] if next_period and next_period.get("warnings") else None)

    if res["shortfall"]:
        vcls, verdict = "red", f"Heads up — you dip below zero around {low_when}"
    elif next_warn and next_warn["severity"] <= 4:
        vcls = _WARN_META[next_warn["kind"]][0]
        vcls = "red" if vcls == "red" else "amber"
        verdict = _warn_headline(next_warn)
    elif res["safe_to_spend"] < 500:
        vcls, verdict = "amber", f"Cutting it close around {low_when}"
    elif next_warn and next_warn["kind"] == "ahead":
        vcls, verdict = "green", "You're ahead"
    else:
        vcls, verdict = "green", "You're on track"

    short_line = ""
    if next_warn and next_warn["severity"] <= 4:
        short_line = f'<div class="cd-fc-heroshort">{_WARN_META[next_warn["kind"]][1]} {_warn_msg(next_warn)}</div>'

    # ── hero verdict ──
    ui.html(f'''
      <div class="cd-fc-hero {vcls}">
        <div>
          <div class="cd-fc-verdict">{verdict}</div>
          <div class="cd-fc-safe mono">{money(res["safe_to_spend"])}</div>
          <div class="cd-fc-safe-lbl">safe to spend today · your balance never dips below this</div>
          {short_line}
        </div>
        <div class="cd-fc-low">
          <div class="cd-fc-low-lbl">Lowest point</div>
          <div class="cd-fc-low-val mono">{money(res["low"]["balance"])}</div>
          <div class="cd-fc-low-lbl">on {low_when}</div>
        </div>
      </div>''')

    # ── vaults — internal savings, never left checking, growing paycheck by paycheck ──
    if vaults:
        grown = round((next_period["vaults_total"] if next_period else res["vaults_today"]) - res["vaults_today"], 2)
        grow_txt = f' <span class="cd-fc-vgrow">→ {money(next_period["vaults_total"])} after your next paycheck</span>' if next_period and grown > 0.005 else ''
        ui.html(f'<div class="cd-fc-vaults">🔒 <b>{money(res["vaults_today"])}</b> in vaults today — '
                f'still inside your checking balance, not a separate stash{grow_txt}</div>')

    # ── horizon toggle ──
    with ui.element("div").classes("cd-fc-hztoggle"):
        with ui.element("div").classes("cd-seg").style("max-width:280px"):
            for n, lab in ((30, "30 days"), (60, "60 days"), (90, "90 days")):
                cls = "cd-segopt" + (" on" if hz == n else "")
                ui.html(f'<div class="{cls}">{lab}</div>').on("click", lambda _, k=n: set_hz(k)).style("flex:1")
        ui.html(f'<span class="cd-hint">{money(res["total_income"])} in · {money(res["total_out"])} out over {hz} days</span>').style("margin-left:auto")

    # ── trajectory chart ──
    with ui.element("div").classes("cd-fc-chart"):
        ui.html(_forecast_chart(res))

    # ── pay-period breakdown — each period is a running register ──
    ui.html('<div class="cd-fc-seclbl">Pay periods · what comes in, what goes out</div>')
    for p in res["periods"]:
        is_open = p["start"] in exp
        rng = f'{_friendly_date(p["start"])} – {_friendly_date(p["end"])}'
        ebcol = "var(--neg)" if p["negative"] else "var(--ink)"
        ins = f'<span class="in">+{money(p["income"])}</span>' if p["income"] > 0 else ''
        outs = round(p["external"] + p.get("internal", 0) + p["bills_out"], 2)
        out_s = f'<span class="out">−{money(outs)}</span>' if outs > 0 else ''
        flow = ' · '.join(x for x in (ins, out_s) if x)
        p_warnings = p.get("warnings", [])
        worst = p_warnings[0] if p_warnings else None
        badge = ''
        if worst and worst["kind"] not in ("ahead", "all_clear"):
            wcls, wic = _WARN_META[worst["kind"]]
            badge = f' <span class="cd-fc-warn-badge {wcls}">{wic} {worst["kind"].replace("_", " ")}</span>'
        card = ui.element("div").classes("cd-fc-period" + (" neg" if p["negative"] else "") + (" open" if is_open else ""))
        with card:
            hd = ui.element("div").classes("cd-fc-phd")
            with hd:
                ui.html(f'<span class="cd-fc-chev">▸</span>')
                ui.html(f'<div style="min-width:0"><div class="cd-fc-pname">{_esc(p["label"])}{badge}</div>'
                        f'<div class="cd-fc-prange">{rng} · {flow}</div></div>')
                ui.html(f'<div class="cd-fc-pbal"><div class="cd-sub">projected balance</div>'
                        f'<div class="mono" style="font-weight:800;font-size:16px;color:{ebcol}">{money(p["end_balance"])}</div></div>')
            hd.on("click", lambda _, k=p["start"]: toggle_p(k))
            # worst-first: every warning that genuinely applies to this period, ranked
            for w in p_warnings:
                wcls, wic = _WARN_META[w["kind"]]
                ui.html(f'<div class="cd-fc-warnrow {wcls}">{wic} {_warn_msg(w)}</div>')
            if is_open:
                with ui.element("div").classes("cd-fc-reg"):
                    ui.html(f'<div class="cd-fc-erow open-bal"><span></span>'
                            f'<span class="cd-fc-ename">Starting balance</span><span></span>'
                            f'<span class="cd-fc-ebal mono">{money(p["start_balance"])}</span></div>')
                    for e in p["events"]:
                        kind = e["kind"]
                        cad = f' <span class="cd-fc-cad">{e["cadence"]}</span>' if e.get("cadence") else ''
                        sch = ' <span class="cd-fc-sch">scheduled</span>' if e.get("scheduled") else ''
                        if kind == "internal":         # set aside — depletes the balance like any outflow
                            to = f' → {_esc(e["bucket"])}' if e.get("bucket") else ''
                            tag = f'<span class="cd-fc-set">set aside{to}</span>'
                            if e.get("vault_balance_after") is not None:
                                tag += f' <span class="cd-fc-vnow">vault now {money(e["vault_balance_after"])}</span>'
                            bcol = "var(--neg)" if e["balance"] < 0 else "var(--muted)"
                            ui.html(
                                f'<div class="cd-fc-erow">'
                                f'<span class="cd-fc-edate">{_friendly_date(e["date"])}</span>'
                                f'<span class="cd-fc-ename"><span class="cd-fc-eic internal">◇</span>'
                                f'{_esc(e["name"])} {tag}{sch}</span>'
                                f'<span class="cd-fc-eamt mono" style="color:var(--violet)">−{money(e["amount"])}</span>'
                                f'<span class="cd-fc-ebal mono" style="color:{bcol}">{money(e["balance"])}</span></div>')
                            continue
                        pos = kind == "income"
                        acol = "var(--pos)" if pos else ("var(--neg)" if not e["funded"] else "var(--ink)")
                        sign = "+" if pos else "−"
                        flag = (f' <span class="cd-fc-uf">short {money(e["shortfall"])}</span>'
                                if not e["funded"] and e.get("shortfall", 0) > 0.005
                                else ' <span class="cd-fc-uf">unfunded</span>' if not e["funded"] else '')
                        bcol = "var(--neg)" if e["balance"] < 0 else "var(--muted)"
                        ui.html(
                            f'<div class="cd-fc-erow">'
                            f'<span class="cd-fc-edate">{_friendly_date(e["date"])}</span>'
                            f'<span class="cd-fc-ename"><span class="cd-fc-eic {kind}">{_FC_ICON[kind]}</span>'
                            f'{_esc(e["name"])}{cad}{flag}{sch}</span>'
                            f'<span class="cd-fc-eamt mono" style="color:{acol}">{sign}{money(e["amount"])}</span>'
                            f'<span class="cd-fc-ebal mono" style="color:{bcol}">{money(e["balance"])}</span></div>')


def _login(error: str = ""):
    _theme()
    with ui.element("div").classes("cd-welcome"):
        ui.html(f'''
          <div class="cd-wl-brand">
            <div class="cd-logo" style="width:40px;height:40px;border-radius:12px;font-size:19px">C</div>
            <div class="cd-brand">{BRAND}</div>
          </div>
          <h1 class="cd-wl-h1">Every dollar,<br>a job.</h1>
          <p class="cd-wl-sub">Zero-based envelope budgeting that stays a step ahead —
             live buckets, a running ledger, and a forecast that sees the next 90 days.</p>''')
        with ui.element("div").classes("cd-login"):
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

            pw.on("keydown.enter", lambda: do_login())
            ui.button("Sign in", on_click=do_login).props("unelevated color=indigo").classes("w-full")
            ui.html('<div class="cd-wl-or">or</div>')
            ui.button("Explore the live demo", on_click=lambda: (
                app.storage.user.update({"demo": True, "token": None}), ui.navigate.reload())
            ).props("outline color=indigo").classes("w-full")
        if error:
            ui.notify(error, type="negative")


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
