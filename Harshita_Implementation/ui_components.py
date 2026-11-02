"""HTML/Altair building blocks used by the Streamlit pages."""

from __future__ import annotations

import html
import json

import altair as alt
import numpy as np
import pandas as pd

from app_core import predict_transactions
from ui_theme import PALETTE as P


# ---------------------------------------------------------------- formatting
def fmt_inr(value: float) -> str:
    """Format a number with Indian digit grouping (12,34,567)."""
    value = float(value)
    whole, frac = f"{abs(value):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    out = f"{whole}.{frac}" if frac != "00" else whole
    return ("-" if value < 0 else "") + out


def esc(text) -> str:
    return html.escape(str(text))


def _one_line(markup: str) -> str:
    """Collapse markup to one line so Markdown never treats it as a code block."""
    return "".join(line.strip() for line in markup.strip().splitlines())


# ---------------------------------------------------------------- page chrome
SHIELD_SVG = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#304336" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z"/>'
    '<path d="M9 12l2 2 4-4"/></svg>'
)


def brand_html() -> str:
    return _one_line(f"""
    <div class="brand"><div class="mark">{SHIELD_SVG}</div>
    <div><div class="name">UPI Fraud Lab</div><div class="tag">Research prototype</div></div></div>
    """)


def hero_html(title: str, subtitle: str, stat: dict | None = None) -> str:
    stat_html = ""
    if stat:
        stat_html = (
            f'<div class="stat"><div class="big">{esc(stat["big"])}</div>'
            f'<div class="cap">{esc(stat["caption"])}</div>'
            f'<div class="bar"><i style="width:{stat["pct"]:.2f}%"></i></div>'
            f'<div class="legend"><span>{esc(stat["left"])}</span><span>{esc(stat["right"])}</span></div></div>'
        )
    cls = "hero" if stat else "hero slim"
    return _one_line(f'<div class="{cls}"><div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>{stat_html}</div>')


def cards_html(items: list[dict], cols: int = 4) -> str:
    cells = []
    for it in items:
        tone = it.get("tone", "")
        note = f'<div class="note">{esc(it["note"])}</div>' if it.get("note") else ""
        cells.append(
            f'<div class="card {tone}"><div class="label">{esc(it["label"])}</div>'
            f'<div class="value">{esc(it["value"])}</div>{note}</div>'
        )
    return _one_line(f'<div class="cards c{cols}">{"".join(cells)}</div>')


def info_cards_html(items: list[dict], cols: int = 3) -> str:
    cells = []
    for it in items:
        cells.append(
            f'<div class="card {it.get("tone", "ivory")}"><div class="icon-dot">{it["icon"]}</div>'
            f'<h4>{esc(it["title"])}</h4><p>{esc(it["body"])}</p></div>'
        )
    return _one_line(f'<div class="cards c{cols}">{"".join(cells)}</div>')


def sequence_html(steps: list[tuple[str, str]]) -> str:
    cells = "".join(f'<div class="s"><b>{esc(t)}</b><span>{esc(b)}</span></div>' for t, b in steps)
    return _one_line(f'<div class="seq">{cells}</div>')


def callout_html(text_html: str, tone: str = "info") -> str:
    return f'<div class="callout {tone}">{text_html}</div>'


def confusion_html(tn: int, fp: int, fn: int, tp: int) -> str:
    return _one_line(f"""
    <div class="cm">
      <div></div><div class="h">Model said: no fraud</div><div class="h">Model said: fraud</div>
      <div class="h">Actually<br>legitimate</div>
      <div class="c tn"><div class="n">{tn:,}</div><div class="t">Correctly cleared</div></div>
      <div class="c fp"><div class="n">{fp:,}</div><div class="t">Legitimate, wrongly flagged</div></div>
      <div class="h">Actually<br>fraud</div>
      <div class="c fn"><div class="n">{fn:,}</div><div class="t">Fraud the model missed</div></div>
      <div class="c tp"><div class="n">{tp:,}</div><div class="t">Fraud correctly caught</div></div>
    </div>
    """)


def comparison_table_html(df: pd.DataFrame, selected: str) -> str:
    cols = [
        ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"),
        ("pr_auc_average_precision", "PR-AUC"), ("roc_auc", "ROC-AUC"),
    ]
    best = {c: df[c].max() for c, _ in cols}
    head = "<tr><th>Model</th><th>Threshold</th>" + "".join(f"<th>{n}</th>" for _, n in cols) + "<th>Fit time</th></tr>"
    body = []
    for _, r in df.iterrows():
        sel = r["model"] == selected
        name = esc(r["model"]) + (' <span class="badge best">Selected</span>' if sel else "")
        cells = "".join(
            f'<td class="{"top" if np.isclose(r[c], best[c]) else ""}">{r[c]:.4f}</td>' for c, _ in cols
        )
        body.append(
            f'<tr class="{"sel" if sel else ""}"><td>{name}</td><td>{r["threshold"]:.4f}</td>{cells}'
            f'<td>{r["training_time_seconds"]:.1f}s</td></tr>'
        )
    return _one_line(f'<div class="tbl-wrap"><table class="tbl">{head}{"".join(body)}</table></div>')


def feed_html(history: list[dict], threshold_pct: float) -> str:
    head = (
        '<div class="row head"><div>Time</div><div>Type</div><div class="hide-sm">Amount</div>'
        '<div class="hide-sm">Score vs threshold</div><div>Result</div></div>'
    )
    if not history:
        return _one_line(f'<div class="feed">{head}<div class="row empty">No payments checked yet. '
                         'Send one above and it appears here.</div></div>')
    rows = []
    for h in history:
        flagged = h["flagged"]
        badge = '<span class="badge flag">Flagged</span>' if flagged else '<span class="badge ok">Cleared</span>'
        rows.append(
            f'<div class="row"><div class="mono">{esc(h["time"])}</div><div>{esc(h["type"])}</div>'
            f'<div class="mono hide-sm">₹{fmt_inr(h["amount"])}</div>'
            f'<div class="hide-sm"><div class="bar-mini"><i class="{"flag" if flagged else ""}" '
            f'style="width:{h["score"]:.1f}%"></i><u style="left:{threshold_pct:.2f}%"></u></div>'
            f'<small class="mono">{h["score"]:.1f}%</small></div><div>{badge}</div></div>'
        )
    return _one_line(f'<div class="feed">{head}{"".join(rows)}</div>')


# ---------------------------------------------------------------- icons
def icon(name: str, color: str = "#304336") -> str:
    paths = {
        "keyboard": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10"/>',
        "forest": '<path d="M12 3l5 8h-3l4 6H6l4-6H7l5-8z"/><path d="M12 17v4"/>',
        "scale": '<path d="M12 3v18M5 7h14M5 7l-3 7a3 3 0 0 0 6 0L5 7zM19 7l-3 7a3 3 0 0 0 6 0l-3-7z"/>',
        "shield": '<path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z"/>',
        "flask": '<path d="M9 3h6M10 3v6L4 19a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3l-6-10V3"/>',
        "alert": '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18h.01"/>',
        "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z"/><path d="M14 3v5h5"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    }
    return (f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>')


# ---------------------------------------------------------------- charts
FONT = "Figtree, Segoe UI, Helvetica Neue, Arial, sans-serif"


def _style(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure(background="transparent", font=FONT)
        .configure_axis(labelColor=P["muted"], titleColor=P["ink"], gridColor="#E5EBDA", domainColor=P["mid_sage_2"],
                        tickColor=P["mid_sage_2"], labelFontSize=11, titleFontSize=12, titleFontWeight=600, labelFont=FONT, titleFont=FONT, labelOverlap=False)
        .configure_legend(labelColor=P["ink"], titleColor=P["ink"], orient="bottom", labelFont=FONT, titleFont=FONT)
        .configure_view(strokeWidth=0)
    )


def score_curve(bundle, tx_type: str, step: int) -> pd.DataFrame:
    """Score a log-spaced range of amounts with everything else held fixed."""
    amounts = np.unique(np.round(np.logspace(0, 7, 90), 2))
    frame = pd.DataFrame({"step": step, "type": tx_type, "amount": amounts})
    frame["step"] = frame["step"].astype(int)
    scores = predict_transactions(bundle, frame)["fraud_probability_percent"].to_numpy()
    return pd.DataFrame({"amount": amounts, "score": scores})


def curve_chart(curve: pd.DataFrame, amount: float, score: float, threshold_pct: float, tx_type: str) -> alt.Chart:
    line = alt.Chart(curve).mark_line(color=P["deep"], strokeWidth=2.5, interpolate="monotone").encode(
        x=alt.X("amount:Q", scale=alt.Scale(type="log", domain=[1, 1e7]), title="Amount", axis=alt.Axis(format="~s", grid=False)),
        y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100]), title="Model score (%)"),
        tooltip=[alt.Tooltip("amount:Q", format=",.0f", title="Amount"), alt.Tooltip("score:Q", format=".1f", title="Score %")],
    )
    zone = alt.Chart(pd.DataFrame({"a": [threshold_pct], "b": [100]})).mark_rect(color=P["red"], opacity=0.07).encode(
        y="a:Q", y2="b:Q")
    rule = alt.Chart(pd.DataFrame({"y": [threshold_pct]})).mark_rule(color=P["red"], strokeDash=[6, 4], strokeWidth=1.5).encode(y="y:Q")
    label = alt.Chart(pd.DataFrame({"x": [1.3], "y": [threshold_pct - 4], "t": [f"Flag threshold {threshold_pct:.1f}%"]})).mark_text(
        align="left", color=P["red"], fontSize=11, fontWeight=600, font=FONT).encode(x="x:Q", y="y:Q", text="t:N")
    flagged = score / 100 >= threshold_pct / 100
    point = alt.Chart(pd.DataFrame({"amount": [max(amount, 1.0)], "score": [score]})).mark_point(
        filled=True, size=190, color=P["red"] if flagged else P["yellow_2"], stroke=P["deep"], strokeWidth=2).encode(x="amount:Q", y="score:Q")
    return _style(alt.layer(zone, line, rule, label, point).properties(height=270))


def session_chart(history: list[dict], threshold_pct: float) -> alt.Chart:
    df = pd.DataFrame(history)[::-1].reset_index(drop=True)
    df["n"] = df.index + 1
    df["result"] = np.where(df["flagged"], "Flagged", "Cleared")
    bars = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("n:O", title="Payment checked (oldest to newest)", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100]), title="Model score (%)"),
        color=alt.Color("result:N", scale=alt.Scale(domain=["Cleared", "Flagged"], range=[P["sage"], P["red"]]), title=None),
        tooltip=["type", alt.Tooltip("amount:Q", format=",.2f"), alt.Tooltip("score:Q", format=".1f")],
    )
    rule = alt.Chart(pd.DataFrame({"y": [threshold_pct]})).mark_rule(color=P["red"], strokeDash=[6, 4]).encode(y="y:Q")
    return _style(alt.layer(bars, rule).properties(height=220))


def model_bars(df: pd.DataFrame) -> alt.Chart:
    long = df.melt(id_vars="model", value_vars=["precision", "recall", "f1", "pr_auc_average_precision"],
                   var_name="metric", value_name="value")
    names = {"precision": "Precision", "recall": "Recall", "f1": "F1", "pr_auc_average_precision": "PR-AUC"}
    long["metric"] = long["metric"].map(names)
    chart = alt.Chart(long).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("metric:N", title=None, sort=list(names.values()), axis=alt.Axis(labelAngle=0)),
        xOffset="model:N",
        y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 1]), title="Validation score"),
        color=alt.Color("model:N", title=None, scale=alt.Scale(
            domain=["Logistic Regression", "Decision Tree", "Random Forest"],
            range=[P["mid_sage_2"], P["yellow_2"], P["deep"]])),
        tooltip=["model", "metric", alt.Tooltip("value:Q", format=".4f")],
    )
    return _style(chart.properties(height=280))


def batch_hist(result: pd.DataFrame, threshold_pct: float) -> alt.Chart:
    hist = alt.Chart(result).mark_bar(color=P["sage"], cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("fraud_probability_percent:Q", bin=alt.Bin(maxbins=25, extent=[0, 100]), title="Model score (%)"),
        y=alt.Y("count():Q", title="Transactions"),
    )
    rule = alt.Chart(pd.DataFrame({"x": [threshold_pct]})).mark_rule(color=P["red"], strokeDash=[6, 4], strokeWidth=2).encode(x="x:Q")
    return _style(alt.layer(hist, rule).properties(height=240))


def batch_by_type(result: pd.DataFrame) -> alt.Chart:
    g = result.groupby("type").agg(total=("type", "size"), flagged=("prediction", lambda s: int((s == "Fraud indication").sum()))).reset_index()
    g["cleared"] = g["total"] - g["flagged"]
    long = g.melt(id_vars="type", value_vars=["cleared", "flagged"], var_name="result", value_name="count")
    long["result"] = long["result"].str.capitalize()
    return _style(alt.Chart(long).mark_bar().encode(
        y=alt.Y("type:N", title=None, sort="-x"),
        x=alt.X("count:Q", title="Transactions"),
        color=alt.Color("result:N", scale=alt.Scale(domain=["Cleared", "Flagged"], range=[P["sage"], P["red"]]), title=None),
        tooltip=["type", "result", "count"],
    ).properties(height=240))


# ---------------------------------------------------------------- simulation
SIM_TEMPLATE = r"""
<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Figtree:wght@400;500;600;700&display=swap');
:root{--sage:#819777;--pale:#E5EBDA;--mid:#D6E1CC;--mid2:#A9BC9F;--yel:#FBF3CF;--yel2:#EFDA89;--ivory:#FFFCF2;--deep:#304336;--ink:#2B342C;--muted:#687163;--olive:#4F6B47;--dsage:#5E7A54;--red:#A3242F;--red2:#D9212A}
*{box-sizing:border-box}
body{margin:0;font-family:'Figtree',system-ui,sans-serif;color:var(--ink);background:transparent}
.wrap{background:var(--ivory);border:1px solid #EFE9D2;border-radius:20px;padding:20px 24px 22px;position:relative}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.top h3{font-family:'Bricolage Grotesque',sans-serif;font-size:18px;margin:0;color:var(--deep)}
.replay{font:600 13px 'Figtree',sans-serif;color:var(--deep);background:#fff;border:1.5px solid var(--mid2);border-radius:10px;padding:6px 12px;cursor:pointer}
.replay:hover{background:var(--pale)}
.replay:focus-visible{outline:3px solid var(--yel2);outline-offset:2px}
.rail{position:relative;height:104px;margin:14px 56px 4px}
.rail .base,.rail .fill{position:absolute;top:28px;height:4px;border-radius:2px}
.rail .base{left:0;right:0;background:var(--mid)}
.rail .fill{left:0;width:0;background:var(--dsage);transition:width .9s ease,background .3s}
.node{position:absolute;top:0;transform:translateX(-50%);width:110px;text-align:center}
.node .ic{width:60px;height:60px;border-radius:50%;background:var(--pale);border:2px solid var(--mid2);display:grid;place-items:center;margin:0 auto;transition:all .35s}
.node .nm{font-weight:700;font-size:13px;margin-top:7px;color:var(--deep)}
.node .sb{font-size:12px;color:var(--muted)}
.n0{left:0}.n1{left:50%}.n2{left:100%}
.node.ok .ic{background:var(--dsage);border-color:var(--dsage)} .node.ok .ic svg{stroke:#fff}
.node.bad .ic{background:#fff;border-color:var(--red);animation:shake .5s}
.node.bad .ic svg{stroke:var(--red)}
.node.work .ic{border-color:var(--deep);box-shadow:0 0 0 6px rgba(129,151,119,.28)}
.coin{position:absolute;top:18px;left:10%;width:24px;height:24px;margin-left:-12px;border-radius:50%;background:var(--yel2);border:2px solid var(--deep);display:grid;place-items:center;font:700 12px 'Figtree',sans-serif;color:var(--deep);z-index:3;opacity:0;transition:left .95s cubic-bezier(.5,0,.3,1),opacity .3s}
.coin.show{opacity:1}
.coin.red{background:#fff;border-color:var(--red);color:var(--red)}
.main{display:grid;grid-template-columns:1.25fr 1fr;gap:22px;margin-top:6px}
.steps{list-style:none;margin:0;padding:0}
.steps li{display:flex;gap:12px;padding:9px 0;opacity:.45;transition:opacity .3s}
.steps li.on,.steps li.done{opacity:1}
.dot{width:24px;height:24px;border-radius:50%;border:2px solid var(--mid2);flex:none;display:grid;place-items:center;margin-top:1px;transition:all .25s;background:#fff}
.steps li.on .dot{border-color:var(--deep);border-top-color:transparent;animation:spin .7s linear infinite}
.steps li.done .dot{background:var(--deep);border-color:var(--deep)}
.steps li.done .dot::after{content:"";width:10px;height:5px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(-45deg) translate(1px,-1px)}
.steps li.bad .dot{background:var(--red);border-color:var(--red)}
.steps li.bad .dot::after{content:"!";color:#fff;font-weight:700;font-size:13px;border:0;transform:none}
.steps b{display:block;font-size:14.5px;color:var(--deep)}
.steps small{display:block;font-size:12.5px;color:var(--muted);line-height:1.4;margin-top:1px}
.gauge{background:#fff;border:1px solid var(--mid);border-radius:16px;padding:12px 14px 10px;text-align:center}
.gauge svg{width:100%;max-width:290px;display:block;margin:0 auto}
.g-track{stroke:var(--mid);fill:none;stroke-width:14;stroke-linecap:butt}
.g-zone{stroke:var(--red);opacity:.28;fill:none;stroke-width:14}
.g-fill{stroke:var(--dsage);fill:none;stroke-width:14;stroke-linecap:butt;transition:stroke .3s}
.g-fill.red{stroke:var(--red)}
.g-needle{stroke:var(--deep);stroke-width:3;stroke-linecap:round}
.g-hub{fill:var(--deep)}
.g-thr{stroke:var(--red);stroke-width:2.5}
.g-lbl{font:600 9.5px 'Figtree',sans-serif;fill:var(--red)}
.score{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:38px;color:var(--deep);line-height:1;margin-top:-4px}
.score.red{color:var(--red)}
.cap{font-size:12.5px;color:var(--muted);margin-top:3px}
.verdict{margin-top:16px;border-radius:14px;padding:13px 16px;font-size:14.5px;line-height:1.45;display:none;align-items:flex-start;gap:12px}
.verdict.show{display:flex;animation:pop .4s ease}
.verdict.ok{background:var(--mid);color:var(--deep)}
.verdict.flag{background:#fff;border:1.5px solid var(--red);color:var(--ink)}
.verdict b{display:block;font-family:'Bricolage Grotesque',sans-serif;font-size:16px}
.verdict.flag b{color:var(--red)}
.legend{display:flex;align-items:center;justify-content:center;gap:7px;font-size:12.5px;font-weight:600;color:var(--red);margin-top:6px}.legend i{width:3px;height:14px;background:var(--red);border-radius:2px}
.idle{color:var(--muted);font-size:13.5px;margin-top:10px}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes shake{20%{transform:translateX(-5px)}40%{transform:translateX(5px)}60%{transform:translateX(-4px)}80%{transform:translateX(3px)}}
@keyframes pop{from{transform:translateY(6px);opacity:0}to{transform:none;opacity:1}}
@media (max-width:640px){.main{grid-template-columns:1fr}.rail{margin:14px 40px 4px}.node{width:84px}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style></head><body>
<div class="wrap">
  <div class="top"><h3>Payment check</h3><button class="replay" id="replay" type="button" aria-label="Replay the check animation">Replay</button></div>
  <div class="rail" aria-hidden="true">
    <div class="base"></div><div class="fill" id="fill"></div>
    <div class="node n0" id="n0"><div class="ic">__ICON_PERSON__</div><div class="nm">Sender</div><div class="sb" id="sb0">Payment request</div></div>
    <div class="node n1" id="n1"><div class="ic">__ICON_SHIELD__</div><div class="nm">Model check</div><div class="sb">Random Forest</div></div>
    <div class="node n2" id="n2"><div class="ic">__ICON_BANK__</div><div class="nm">Recipient</div><div class="sb" id="sb2">Waiting</div></div>
    <div class="coin" id="coin">₹</div>
  </div>
  <div class="main">
    <ol class="steps" id="steps"></ol>
    <div>
      <div class="gauge">
        <svg viewBox="0 0 200 118" role="img" aria-label="Model score gauge">
          <path class="g-track" d="M20 100 A80 80 0 0 1 180 100" pathLength="100"/>
          <path class="g-zone" id="zone" d="M20 100 A80 80 0 0 1 180 100" pathLength="100"/>
          <path class="g-fill" id="gfill" d="M20 100 A80 80 0 0 1 180 100" pathLength="100" stroke-dasharray="0 100"/>
          <line class="g-thr" id="thr"/>
          <line class="g-needle" id="needle" x1="100" y1="100" x2="30" y2="100"/><circle class="g-hub" cx="100" cy="100" r="6"/>
        </svg>
        <div class="score" id="score">0.0%</div>
        <div class="cap">Model score for this payment</div><div class="legend"><i></i><span id="thrtxt"></span></div>
      </div>
    </div>
  </div>
  <div class="verdict" id="verdict" role="status"><div id="vicon"></div><div id="vtext"></div></div>
  <div class="idle" id="idle"></div>
</div>
<script>
const D = __DATA__;
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = id => document.getElementById(id);
const sleep = ms => new Promise(r => setTimeout(r, reduce ? 0 : ms));
const STEPS = D.steps;
let runId = 0;

// threshold marker on the gauge
(function(){
  const t = D.threshold, a = Math.PI * (1 - t/100);
  const cx=100, cy=100, r1=70, r2=90;
  const thr = $('thr');
  thr.setAttribute('x1', cx + r1*Math.cos(a)); thr.setAttribute('y1', cy - r1*Math.sin(a));
  thr.setAttribute('x2', cx + r2*Math.cos(a)); thr.setAttribute('y2', cy - r2*Math.sin(a));
  $('thrtxt').textContent = 'Flag threshold ' + t.toFixed(1) + '%';
  $('zone').setAttribute('stroke-dasharray', '0 ' + t + ' ' + (100 - t));
})();

function buildSteps(){
  $('steps').innerHTML = STEPS.map((s,i) =>
    `<li id="s${i}"><span class="dot"></span><div><b>${s.title}</b><small>${s.detail}</small></div></li>`).join('');
}
function setGauge(v, flagged){
  const a = Math.PI * (1 - v/100);
  const n = $('needle');
  n.setAttribute('x2', 100 + 70*Math.cos(a)); n.setAttribute('y2', 100 - 70*Math.sin(a));
  $('gfill').setAttribute('stroke-dasharray', v + ' 100');
  $('score').textContent = v.toFixed(1) + '%';
  $('gfill').classList.toggle('red', !!flagged); $('score').classList.toggle('red', !!flagged);
}
function animateGauge(target, ms){
  return new Promise(res => {
    if (reduce) { setGauge(target, false); return res(); }
    const t0 = performance.now(), id = runId;
    (function f(now){
      if (id !== runId) return res();
      const p = Math.min(1, (now - t0)/ms), e = 1 - Math.pow(1 - p, 3);
      setGauge(target * e, false);
      p < 1 ? requestAnimationFrame(f) : res();
    })(t0);
  });
}
function reset(){
  runId++;
  buildSteps(); setGauge(0, false);
  ['n0','n1','n2'].forEach(i => $(i).className = 'node ' + i);
  $('fill').style.width = '0'; $('fill').style.background = '';
  const c = $('coin'); c.className = 'coin'; c.style.transition = 'none'; c.style.left = '10%';
  $('verdict').className = 'verdict'; $('sb2').textContent = 'Waiting';
  $('sb0').textContent = D.mode === 'idle' ? 'Payment request' : D.summary;
  $('idle').textContent = D.mode === 'idle' ? 'Enter a payment and press Send payment to watch it move through the check. The score and threshold shown are the real model values.' : '';
  void c.offsetWidth; c.style.transition = '';
}
const mark = (i, cls) => { const el = $('s'+i); el.className = cls; };

async function run(){
  reset();
  if (D.mode === 'idle') return;
  const id = runId, alive = () => id === runId;
  const coin = $('coin');
  coin.classList.add('show');
  mark(0,'on'); await sleep(650); if(!alive())return; mark(0,'done');
  mark(1,'on'); coin.style.left = '24%'; $('fill').style.width = '24%'; await sleep(750); if(!alive())return; mark(1,'done');
  mark(2,'on'); coin.style.left = '40%'; $('fill').style.width = '40%'; await sleep(800); if(!alive())return; mark(2,'done');
  $('n1').classList.add('work');
  mark(3,'on'); coin.style.left = '50%'; $('fill').style.width = '50%';
  await animateGauge(D.score, 1300); if(!alive())return; mark(3,'done');
  mark(4,'on'); await sleep(750); if(!alive())return;
  setGauge(D.score, D.flagged);
  $('n1').classList.remove('work');
  const v = $('verdict');
  if (D.flagged) {
    mark(4,'bad');
    $('n1').classList.add('bad'); coin.classList.add('red'); coin.textContent = '✕';
    await sleep(450); if(!alive())return;
    coin.style.left = '10%'; $('fill').style.width = '0'; $('sb0').textContent = 'Held for review';
    $('vicon').innerHTML = '__ICON_ALERT__';
    $('vtext').innerHTML = '<b>Fraud indication</b>' + D.flag_text;
    v.className = 'verdict flag show';
  } else {
    mark(4,'done');
    $('n1').classList.add('ok'); await sleep(450); if(!alive())return;
    coin.style.left = '90%'; $('fill').style.width = '100%';
    await sleep(1000); if(!alive())return;
    $('n2').classList.add('ok'); $('sb2').textContent = 'Payment received'; coin.classList.remove('show');
    $('vicon').innerHTML = '__ICON_CHECK__';
    $('vtext').innerHTML = '<b>No fraud indication</b>' + D.ok_text;
    v.className = 'verdict ok show';
  }
}
$('replay').addEventListener('click', run);
run();
</script></body></html>
"""


def _svg(path: str, color: str = "#304336", size: int = 28) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


def simulation_html(payload: dict | None, threshold_pct: float, trees: int) -> str:
    """Render the animated payment check. payload=None shows the idle state."""
    if payload is None:
        data = {
            "mode": "idle", "threshold": threshold_pct, "score": 0, "flagged": False, "summary": "",
            "steps": [
                {"title": "Payment request received", "detail": "Waiting for a payment"},
                {"title": "Inputs validated", "detail": "Step, type and amount are checked"},
                {"title": "Features prepared", "detail": "Amount is log-scaled, type is one-hot encoded"},
                {"title": f"Random Forest scored it", "detail": f"{trees} trees are averaged into one score"},
                {"title": "Compared with the threshold", "detail": f"Flag at {threshold_pct:.1f}% or higher"},
            ],
            "ok_text": "", "flag_text": "",
        }
    else:
        score = payload["score"]
        flagged = payload["flagged"]
        data = {
            "mode": "run", "threshold": threshold_pct, "score": score, "flagged": flagged,
            "summary": f'{payload["type"]} ₹{fmt_inr(payload["amount"])}',
            "steps": [
                {"title": "Payment request received",
                 "detail": f'{esc(payload["type"])} · ₹{fmt_inr(payload["amount"])} · step {payload["step"]}'},
                {"title": "Inputs validated", "detail": "Step is 1 to 743, type is supported, amount is 0 or more"},
                {"title": "Features prepared", "detail": "Amount log-scaled, type one-hot encoded, step passed through"},
                {"title": "Random Forest scored it", "detail": f"{trees} trees averaged to {score:.1f}%"},
                {"title": "Compared with the threshold",
                 "detail": f"{score:.1f}% is {'at or above' if flagged else 'below'} {threshold_pct:.1f}%"},
            ],
            "ok_text": "The model would let this payment through. That is not a guarantee it is safe: this model misses most fraud.",
            "flag_text": "The model would hold this payment for review before the money reaches the recipient.",
        }
    person = _svg('<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>')
    shield = _svg('<path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z"/><path d="M9 12l2 2 4-4"/>')
    bank = _svg('<path d="M3 10l9-6 9 6M5 10v8M9 10v8M15 10v8M19 10v8M3 21h18"/>')
    alert = _svg('<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18h.01"/>', P["red"], 24)
    check = _svg('<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>', P["deep"], 24)
    out = (SIM_TEMPLATE.replace("__DATA__", json.dumps(data))
           .replace("__ICON_PERSON__", person).replace("__ICON_SHIELD__", shield).replace("__ICON_BANK__", bank)
           .replace("__ICON_ALERT__", alert.replace("'", "\\'")).replace("__ICON_CHECK__", check.replace("'", "\\'")))
    return out
