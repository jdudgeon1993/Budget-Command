"""
Cadence — a fully-live, stay-in-place budgeting app built on NiceGUI.

Run:  python -m cadence.main   (serves on :8110, or $PORT on Railway)

No hx-get / hx-target / hx-swap anywhere. You mutate Python state; the pieces
that depend on it re-render in place over a WebSocket. Scroll and focus never
jump. Sign in to see your real Supabase budget, or open the demo for sample data.
"""
import os
from datetime import date
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
        return out("Funding", "amber", pct, AMBER, f"{money(funded)} of {money(target)} goal")

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
    """Current stored due_day (int, 'eom', or None) → select key."""
    if due_day is None or due_day == "":
        return ""
    return "eom" if str(due_day).lower() == "eom" else str(due_day)


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
            card.on("click", lambda _, e=r["id"]: _open_assign(e))

        # ── bucket sheet: assign · spend · details ────────────────────────────
        def _open_assign(eid):
            dialog_host.clear()
            with dialog_host:
                dlg = ui.dialog().props("position=bottom")
            with dlg, ui.card().classes("cd-sheet"):
                @ui.refreshable
                def body():
                    b = store.bucket(eid)

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

                    # ── HEADER (status at a glance) ──
                    v = _bucket_visual(b)
                    av_col = "var(--neg)" if b["available"] < 0 else "var(--ink)"
                    tgt_txt = "" if b["flex"] else f'{money(b["target"])} target · '
                    bar = ('<div class="cd-flexbar" style="margin-top:12px"></div>' if v["bar"] is None
                           else f'<div class="cd-bar" style="margin:12px 0 0"><div class="cd-bar-fill" '
                                f'style="width:{v["bar"] * 100:.0f}%;background:{v["color"]}"></div></div>')
                    ui.html(f'''
                      <div class="cd-hdl"></div>
                      <div class="cd-sh-head">
                        <div class="cd-sh-top"><span class="cd-sh-name">{_esc(b["name"])}</span>
                          <span class="cd-pill {v["badge_cls"]}">{v["badge"]}</span></div>
                        <div class="cd-sh-avail" style="color:{av_col}">{money(b["available"])}<span> available</span></div>
                        <div class="cd-sub">{tgt_txt}{money(b["spent"])} spent</div>
                        {bar}
                      </div>''')

                    # ── ASSIGN MONEY ──
                    with ui.element("div").classes("cd-sh-sec"):
                        ui.html('<div class="cd-sh-h">Assign money</div>')
                        gap, over = b["gap"], round(max(0.0, -b["available"]), 2)
                        sources = store.fund_sources(eid)
                        src_avail = {s["id"]: s["avail"] for s in sources}
                        src_map = {s["id"]: f'{s["name"]}  ·  {money(s["avail"])}' for s in sources}
                        amount = ui.number(value=0, format="%.2f", prefix="$").props("outlined hide-bottom-space").classes("w-full")
                        sld = ui.slider(min=0, max=max(src_avail.get("unallocated", 0), 1), step=1) \
                            .props("label-always color=indigo").classes("q-mt-xs")
                        sld.bind_value(amount)
                        if gap > 0 or over > 0:
                            with ui.row().classes("q-gutter-xs q-mt-sm"):
                                if gap > 0:
                                    ui.button(f"Fill to target · {money(gap)}",
                                              on_click=lambda: amount.set_value(gap)).props("outline color=indigo no-caps size=sm")
                                if over > 0:
                                    ui.button(f"Cover overspend · {money(over)}",
                                              on_click=lambda: amount.set_value(over)).props("outline color=deep-orange no-caps size=sm")
                        src = ui.select(src_map, value="unallocated", label="From").props("outlined dense").classes("w-full q-mt-sm")
                        src.on("update:model-value", lambda: (sld._props.__setitem__("max", max(src_avail.get(src.value, 0), 1)), sld.update()))

                        def do_assign():
                            amt = float(amount.value or 0)
                            if amt <= 0:
                                ui.notify("Enter an amount (or tap a shortcut).", type="warning"); return
                            un = store.metrics()["unallocated"]
                            if src.value == "unallocated" and amt > un + 0.005:
                                ui.notify(f"Only {money(un)} is unallocated — assigning that.", type="info")
                            act(lambda: store.assign(eid, src.value, amt))
                        ui.button("Add to bucket", on_click=do_assign).props("unelevated color=indigo no-caps").classes("w-full q-mt-sm")
                        with ui.row().classes("items-center no-wrap q-mt-sm cd-pullrow"):
                            ui.html('<span class="cd-sub" style="white-space:nowrap">Pull back out</span>')
                            rem = ui.number(placeholder="0.00", prefix="$").props("dense outlined hide-bottom-space").style("width:120px")
                            ui.button("Remove", on_click=lambda: act(lambda: store.defund(eid, float(rem.value or 0)))).props("flat color=grey no-caps size=sm")

                    # ── LOG A SPEND ──
                    if b["type"] != "vault":
                        with ui.element("div").classes("cd-sh-sec"):
                            ui.html('<div class="cd-sh-h">Log a spend</div>')
                            with ui.row().classes("items-center no-wrap w-full"):
                                sp = ui.number(placeholder="0.00", prefix="$").props("dense outlined hide-bottom-space").style("width:130px")
                                note = ui.input(placeholder="note (optional)").props("dense outlined hide-bottom-space").style("flex:1")

                                def do_spend():
                                    amt = float(sp.value or 0)
                                    if amt <= 0:
                                        ui.notify("Enter a spend amount.", type="warning"); return
                                    act(lambda: store.record_spend(eid, amt, note.value or ""))
                                ui.button("Log", on_click=do_spend).props("unelevated color=deep-orange no-caps")

                    # ── DETAILS (auto-save; feeds the Forecast) ──
                    is_goal, is_vault = b["type"] == "goal", b["type"] == "vault"
                    with ui.element("div").classes("cd-sh-sec"):
                        ui.html('<div class="cd-sh-h">Details</div>')
                        with ui.row().classes("items-center q-gutter-sm w-full"):
                            rn = ui.input("Name", value=b["name"]).props("dense outlined hide-bottom-space").classes("cd-half")
                            rn.on("blur", lambda: save(lambda: store.rename(eid, rn.value)))
                            if not b["flex"]:
                                tlbl = "Goal amount" if is_goal else "Amount / target"
                                tg = ui.number(tlbl, value=b["target"], prefix="$").props("dense outlined hide-bottom-space").classes("cd-half")
                                tg.on("blur", lambda: act(lambda: store.set_target(eid, float(tg.value or 0))))
                        if is_goal:
                            with ui.row().classes("items-center q-gutter-sm w-full"):
                                td = ui.input("Target month", value=b.get("target_date") or "").props("dense outlined hide-bottom-space type=month").classes("cd-half")
                                td.on("blur", lambda: act(lambda: store.set_target_date(eid, td.value)))
                                fq = ui.select(_FREQ, value=b["frequency"] or "", label="Contribution cadence").props("dense outlined").classes("cd-half")
                                fq.on("update:model-value", lambda: act(lambda: store.set_frequency(eid, fq.value)))
                        elif not is_vault:
                            with ui.row().classes("items-center q-gutter-sm w-full"):
                                dd = ui.select(_dueday_options(), value=_dueday_key(b["due_day"]), label="Due day").props("dense outlined").classes("cd-half")
                                dd.on("update:model-value", lambda: act(lambda: store.set_due_day(eid, dd.value)))
                                fq = ui.select(_FREQ, value=b["frequency"] or "", label="Frequency (if no due day)").props("dense outlined").classes("cd-half")
                                fq.on("update:model-value", lambda: act(lambda: store.set_frequency(eid, fq.value)))
                        hint = _period_hint(b)
                        if hint:
                            ui.html(f'<div class="cd-sub" style="margin:6px 2px 0;color:var(--accent)">↳ {hint}</div>')
                        notes = ui.textarea("Notes", value=b.get("notes") or "").props("dense outlined hide-bottom-space autogrow").classes("w-full q-mt-sm")
                        notes.on("blur", lambda: save(lambda: store.set_notes(eid, notes.value)))
                        with ui.row().classes("items-center q-gutter-md q-mt-sm"):
                            if b["type"] == "spend":
                                fx = ui.switch("Flexible", value=b["flex"])
                                fx.on("update:model-value", lambda: act(lambda: store.set_flex(eid, fx.value)))
                            hd = ui.switch("Handled this month", value=b["handled"])
                            hd.on("update:model-value", lambda: act(lambda: store.toggle_handled(eid)))

                    # ── BILL SCHEDULE (split one pool into scheduled line-items) ──
                    if b["type"] == "spend" and not b["flex"]:
                        with ui.element("div").classes("cd-sh-sec"):
                            with ui.row().classes("items-center no-wrap w-full").style("margin-bottom:10px"):
                                ui.html('<div class="cd-sh-h" style="margin:0">Bill schedule</div>')
                                ui.space()
                                sp = ui.switch(value=b["split"]).props("dense")
                                sp.on("update:model-value", lambda: act(lambda: store.set_split(eid, sp.value)))
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
                                    with ui.row().classes("w-full items-center no-wrap cd-item " + row_cls):
                                        pd = ui.checkbox(value=it["paid"]).props("dense")
                                        pd.on("update:model-value", lambda i=it["id"]: act(lambda: store.toggle_item_paid(eid, i)))
                                        nm = ui.input(value=it["name"]).props("dense outlined hide-bottom-space").style("flex:1;min-width:64px")
                                        nm.on("blur", lambda i=it["id"], el=nm: save(lambda: store.edit_item(eid, i, name=el.value)))
                                        am = ui.number(value=it["amount"], format="%.2f", prefix="$").props("dense outlined hide-bottom-space").style("width:88px")
                                        am.on("blur", lambda i=it["id"], el=am: act(lambda: store.edit_item(eid, i, amount=el.value)))
                                        du = ui.select(_dueday_options(), value=_dueday_key(it["due_day"])).props("dense outlined").style("width:84px")
                                        du.on("update:model-value", lambda i=it["id"], el=du: act(lambda: store.edit_item(eid, i, due_day=el.value)))
                                        # funded state of this individual bill, from the shared pool
                                        if it.get("paid"):
                                            ui.html('<span class="cd-idtag green">paid</span>')
                                        elif it.get("item_gap", 0.0) > 0.005:
                                            ui.html(f'<span class="cd-idtag red">needs {money(it["item_gap"])}</span>')
                                        else:
                                            ui.html('<span class="cd-idtag green">funded</span>')
                                        ui.html(f'<span class="cd-idtag {tag_cls}">{tag_txt}</span>')
                                        ui.button(icon="close", on_click=lambda i=it["id"]: act(lambda: store.remove_item(eid, i))).props("flat dense round size=sm color=grey")
                                for it in b["items"]:
                                    _item_row(it)

                                with ui.row().classes("w-full items-center no-wrap cd-item q-mt-sm"):
                                    inm = ui.input(placeholder="Add item — e.g. Netflix").props("dense outlined hide-bottom-space").style("flex:1;min-width:64px")
                                    iamt = ui.number(placeholder="0.00", format="%.2f", prefix="$").props("dense outlined hide-bottom-space").style("width:88px")
                                    idd = ui.select(_dueday_options(), value="", label="Due").props("dense outlined").style("width:84px")

                                    def add_it():
                                        if not (inm.value or "").strip():
                                            ui.notify("Name the item.", type="warning"); return
                                        act(lambda: store.add_item(eid, inm.value, iamt.value or 0, idd.value))
                                    ui.button(icon="add", on_click=add_it).props("flat dense round size=sm color=indigo")

                    with ui.row().classes("w-full items-center cd-sh-foot"):
                        def do_delete():
                            try:
                                store.delete(eid)
                            except Exception as e:
                                ui.notify(str(e)[:140], type="warning"); return
                            dlg.close(); refresh_page()
                        ui.button("Delete", on_click=do_delete).props("flat color=red no-caps size=sm")
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
                cat = ui.select({c["id"]: c["name"] for c in cats}, label="Category",
                                value=(cats[0]["id"] if cats else None)).props("dense outlined").classes("w-full")
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
                                    store.assign(n["id"], "unallocated", a); moved += a
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


_TX_ICON = {"expense": "−", "income": "+", "refund": "↺", "transfer": "→"}
_TX_CLASS = {"expense": "out", "income": "in", "refund": "refund", "transfer": "transfer"}


def _ledger_view(store, refresh_bg, on_paycheck=None):
    """The cleared-money timeline: income, spending and refunds, grouped by day."""
    q = {"v": ""}
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

    with ui.element("div").classes("cd-actionbar"):
        ui.html('<div class="cd-newbtn">＋ Add transaction</div>').on("click", lambda _: _open_tx())
        ui.html('<span class="cd-hint">Tap any row to edit · income lifts Unallocated</span>').style("margin-left:auto")

    search = ui.input(placeholder="Search payee or bucket…").props("outlined dense clearable").classes("w-full cd-led-search")
    search.on("update:model-value", lambda: (q.__setitem__("v", search.value or ""), lst.refresh()))
    lst()


# ── Settings pillar (income + allocation rules → the Forecast engine) ─────────
_FREQ_LBL = {"weekly": "Weekly", "biweekly": "Bi-weekly",
             "semimonthly": "Semi-monthly", "monthly": "Monthly"}
_RULE_KIND_LBL = {"internal": "Internal — fund a bucket", "external": "External — leaves the budget"}
_RULE_VT_LBL = {"fund": "Fund to target", "pct": "% of each paycheck", "fixed": "$ fixed amount"}


def _friendly_date(iso: str) -> str:
    try:
        d = date.fromisoformat(iso[:10])
        return d.strftime("%b ") + str(d.day)
    except (ValueError, TypeError):
        return iso or "—"


def _rule_value_text(r: dict) -> str:
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
                    'external rules move money out of the budget.</div>')
            name = ui.input("Rule name", value=existing["name"] if existing else "").props("outlined dense hide-bottom-space").classes("w-full")
            kind = ui.select(_RULE_KIND_LBL, value=existing["kind"] if existing else "internal", label="Type").props("outlined dense").classes("w-full q-mt-sm")
            bucket_row = ui.row().classes("w-full q-mt-sm")
            with bucket_row:
                bval = existing["bucket_id"] if (existing and existing.get("bucket_id") in allb) else next(iter(allb), None)
                bucket = ui.select(allb, label="Fund which bucket", value=bval).props("outlined dense").classes("w-full")
            bucket_row.bind_visibility_from(kind, "value", backward=lambda v: v == "internal")
            with ui.row().classes("w-full q-gutter-sm q-mt-sm"):
                vtype = ui.select(_RULE_VT_LBL, value=existing["value_type"] if existing else "fund", label="How much").props("outlined dense").classes("cd-half")
                value = ui.number("Value", value=existing["value"] if existing else None, format="%.2f").props("outlined dense hide-bottom-space").classes("cd-half")
                value.bind_visibility_from(vtype, "value", backward=lambda v: v != "fund")

            def save():
                if not (name.value or "").strip():
                    ui.notify("Name the rule.", type="warning"); return
                k = kind.value
                vt = vtype.value
                bid = bucket.value if k == "internal" else None
                val = 0 if vt == "fund" else float(value.value or 0)
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

    def _paycheck_row(p):
        row = ui.element("div").classes("cd-setrow")
        with row:
            ui.html('<div class="cd-set-ic in">$</div>')
            with ui.element("div").style("min-width:0"):
                ui.html(f'<div class="cd-set-name">{_esc(p["label"])}</div>')
                ui.html(f'<div class="cd-set-meta">{_FREQ_LBL.get(p["freq"], p["freq"])} · '
                        f'next {_friendly_date(p["anchor"])}</div>')
            ui.html(f'<div class="cd-set-val mono">{money(p["amount"])}</div>')
        row.on("click", lambda _, i=p["id"]: _open_paycheck(i))

    def _rule_row(r):
        with ui.element("div").classes("cd-setrow" + ("" if r["active"] else " off")):
            tg = ui.html(f'<div class="cd-toggle {"on" if r["active"] else ""}">{"ON" if r["active"] else "OFF"}</div>')
            tg.on("click", lambda _, i=r["id"]: _do(lambda: store.toggle_rule(i)))
            body = ui.element("div").style("min-width:0;cursor:pointer")
            with body:
                ui.html(f'<div class="cd-set-name">{_esc(r["name"])}</div>')
                if r["kind"] == "internal":
                    tgt = f'→ {_esc(r["bucket_name"] or "—")}'
                else:
                    tgt = "leaves the budget"
                ui.html(f'<div class="cd-set-meta"><span class="cd-rule-badge {r["kind"]}">{r["kind"]}</span> {tgt}</div>')
            body.on("click", lambda _, i=r["id"]: _open_rule(i))
            ui.html(f'<div class="cd-set-val mono">{_rule_value_text(r)}</div>')

    # ── render ──
    ui.html('<div class="cd-set-title">Settings</div>'
            '<div class="cdm-sub" style="margin-bottom:18px">Your income and how each paycheck is split — '
            'this is the engine behind the Forecast.</div>')

    with ui.element("div").classes("cd-setcard"):
        ui.html('<div class="cd-set-seclbl">Income · paychecks</div>')
        pcs = store.paychecks()
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
                        out.append({"name": f'{r["name"]} · {it["name"]}', "amount": it["amount"],
                                    "spent": it["amount"] if it.get("paid") else 0.0,
                                    "available": round(it["amount"] - it.get("item_gap", 0.0), 2),
                                    "due_day": it["due_day"], "frequency": None})
            elif r["target"] > 0 and (r["due_day"] is not None
                                      or r["frequency"] in ("weekly", "biweekly", "triweekly", "monthly")):
                out.append({"name": r["name"], "amount": r["target"], "spent": r["spent"],
                            "available": r["available"], "due_day": r["due_day"],
                            "frequency": r["frequency"]})
    return out


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


_FC_ICON = {"income": "+", "transfer": "→", "bill": "−"}


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

    res = forecast.project(store.metrics()["cash"], store.paychecks(), store.rules(),
                           _forecast_bills(store), horizon_days=hz)
    # Which periods are expanded — the current one opens by default.
    exp = getattr(store, "_fc_expanded", None)
    if exp is None:
        exp = {res["periods"][0]["start"]} if res["periods"] else set()
        store._fc_expanded = exp
    low_when = _friendly_date(res["low"]["date"])
    if res["shortfall"]:
        vcls, verdict = "red", f"Heads up — you dip below zero around {low_when}"
    elif res["safe_to_spend"] < 500:
        vcls, verdict = "amber", f"Cutting it close around {low_when}"
    else:
        vcls, verdict = "green", "You're on track"

    # ── hero verdict ──
    ui.html(f'''
      <div class="cd-fc-hero {vcls}">
        <div>
          <div class="cd-fc-verdict">{verdict}</div>
          <div class="cd-fc-safe mono">{money(res["safe_to_spend"])}</div>
          <div class="cd-fc-safe-lbl">safe to spend today · your balance never dips below this</div>
        </div>
        <div class="cd-fc-low">
          <div class="cd-fc-low-lbl">Lowest point</div>
          <div class="cd-fc-low-val mono">{money(res["low"]["balance"])}</div>
          <div class="cd-fc-low-lbl">on {low_when}</div>
        </div>
      </div>''')

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
        outs = round(p["external"] + p["bills_out"], 2)
        out_s = f'<span class="out">−{money(outs)}</span>' if outs > 0 else ''
        flow = ' · '.join(x for x in (ins, out_s) if x)
        card = ui.element("div").classes("cd-fc-period" + (" neg" if p["negative"] else "") + (" open" if is_open else ""))
        with card:
            hd = ui.element("div").classes("cd-fc-phd")
            with hd:
                ui.html(f'<span class="cd-fc-chev">▸</span>')
                ui.html(f'<div style="min-width:0"><div class="cd-fc-pname">{_esc(p["label"])}</div>'
                        f'<div class="cd-fc-prange">{rng} · {flow}</div></div>')
                ui.html(f'<div class="cd-fc-pbal"><div class="cd-sub">projected balance</div>'
                        f'<div class="mono" style="font-weight:800;font-size:16px;color:{ebcol}">{money(p["end_balance"])}</div></div>')
            hd.on("click", lambda _, k=p["start"]: toggle_p(k))
            if is_open:
                with ui.element("div").classes("cd-fc-reg"):
                    ui.html(f'<div class="cd-fc-erow open-bal"><span></span>'
                            f'<span class="cd-fc-ename">Starting balance</span><span></span>'
                            f'<span class="cd-fc-ebal mono">{money(p["start_balance"])}</span></div>')
                    for e in p["events"]:
                        pos = e["kind"] == "income"
                        acol = "var(--pos)" if pos else ("var(--neg)" if not e["funded"] else "var(--ink)")
                        sign = "+" if pos else "−"
                        cad = f' <span class="cd-fc-cad">{e["cadence"]}</span>' if e.get("cadence") else ''
                        flag = ' <span class="cd-fc-uf">unfunded</span>' if not e["funded"] else ''
                        bcol = "var(--neg)" if e["balance"] < 0 else "var(--muted)"
                        ui.html(
                            f'<div class="cd-fc-erow">'
                            f'<span class="cd-fc-edate">{_friendly_date(e["date"])}</span>'
                            f'<span class="cd-fc-ename"><span class="cd-fc-eic {e["kind"]}">{_FC_ICON[e["kind"]]}</span>'
                            f'{_esc(e["name"])}{cad}{flag}</span>'
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
