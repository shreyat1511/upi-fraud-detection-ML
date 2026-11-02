"""Visual theme for the Streamlit app: sage palette tokens and global CSS."""

from __future__ import annotations

import streamlit as st

PALETTE = {
    "sage": "#819777",
    "pale_sage": "#E5EBDA",
    "mid_sage": "#D6E1CC",
    "mid_sage_2": "#A9BC9F",
    "yellow": "#FBF3CF",
    "yellow_2": "#EFDA89",
    "ivory": "#FFFCF2",
    "deep": "#304336",
    "ink": "#2B342C",
    "muted": "#687163",
    "olive": "#4F6B47",
    "dark_sage": "#5E7A54",
    "red": "#A3242F",
    "red_2": "#D9212A",
    "white": "#FFFFFF",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Figtree:wght@400;500;600;700&display=swap');

:root {
  --sage:#819777; --pale:#E5EBDA; --mid:#D6E1CC; --mid2:#A9BC9F;
  --yel:#FBF3CF; --yel2:#EFDA89; --ivory:#FFFCF2; --deep:#304336;
  --ink:#2B342C; --muted:#687163; --olive:#4F6B47; --dsage:#5E7A54;
  --red:#A3242F; --red2:#D9212A; --line:#DDE5D3;
  --display:'Bricolage Grotesque','Figtree',system-ui,sans-serif;
  --body:'Figtree',system-ui,-apple-system,'Segoe UI',sans-serif;
}

html, body, .stApp, [class*="css"] { font-family: var(--body); }
.stApp { background:#fff; color:var(--ink); }
.block-container { max-width:1240px; padding:2rem 2.4rem 2.5rem; }
h1,h2,h3,h4 { font-family:var(--display); color:var(--deep); letter-spacing:-.02em; font-weight:700; }
h2 { font-size:1.45rem; margin-top:1.8rem; }
h3 { font-size:1.15rem; margin-top:1.2rem; }
p, li { color:var(--ink); line-height:1.6; }
a { color:var(--olive); } a:hover { color:var(--deep); }
[data-testid="stCaptionContainer"] p { color:var(--muted); font-size:.85rem; }
:focus-visible { outline:3px solid var(--yel2) !important; outline-offset:2px; }
header[data-testid="stHeader"] { background:transparent; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background:var(--deep); }
[data-testid="stSidebar"] * { color:#EEF3E7; }
[data-testid="stSidebar"] hr { border-color:rgba(229,235,218,.2); }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#B9C7AE; }
.brand { display:flex; align-items:center; gap:.65rem; padding:.2rem 0 .1rem; }
.brand .mark { width:38px; height:38px; border-radius:11px; background:var(--pale);
  display:grid; place-items:center; flex:none; }
.brand .name { font-family:var(--display); font-weight:700; font-size:1.18rem; line-height:1.05; color:#fff; }
.brand .tag { font-size:.78rem; color:#B9C7AE; margin-top:2px; }
[data-testid="stSidebar"] [role="radiogroup"] { gap:.2rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding:.55rem .75rem; border-radius:10px; width:100%; cursor:pointer;
  transition:background .15s ease; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:rgba(229,235,218,.12); }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child { display:none; }
[data-testid="stSidebar"] [role="radiogroup"] label p { font-weight:600; font-size:.95rem; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:var(--pale); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color:var(--deep) !important; }
.side-note { background:rgba(229,235,218,.1); border-radius:12px; padding:.8rem .9rem;
  font-size:.82rem; line-height:1.5; color:#D4DFC9; }

/* ---------- hero ---------- */
.hero { background:var(--deep); border-radius:22px; padding:2.2rem 2.4rem; margin-bottom:1.5rem;
  display:grid; grid-template-columns:1.35fr 1fr; gap:2rem; align-items:center; position:relative; overflow:hidden; }
.hero.slim { grid-template-columns:1fr; padding:1.6rem 2.2rem; }
.hero::after { content:""; position:absolute; right:-70px; top:-70px; width:240px; height:240px;
  border-radius:50%; background:var(--dsage); opacity:.35; pointer-events:none; }
.hero h1 { font-family:var(--display); color:#fff; font-size:clamp(1.7rem,3.2vw,2.5rem);
  line-height:1.1; margin:0 0 .7rem; font-weight:700; }
.hero.slim h1 { font-size:clamp(1.5rem,2.6vw,2rem); margin-bottom:.4rem; }
.hero p { color:#DCE6D2; font-size:1.02rem; margin:0; max-width:56ch; }
.hero .stat { background:var(--ivory); border-radius:16px; padding:1.1rem 1.3rem; position:relative; z-index:1; }
.hero .stat .big { font-family:var(--display); font-size:2.6rem; font-weight:700; color:var(--dsage); line-height:1; }
.hero .stat .cap { color:var(--ink); font-size:.92rem; margin-top:.35rem; line-height:1.45; }
.hero .stat .bar { display:flex; height:12px; border-radius:6px; overflow:hidden; margin-top:.85rem; background:var(--mid); }
.hero .stat .bar i { display:block; background:var(--deep); }
.hero .stat .legend { display:flex; justify-content:space-between; font-size:.8rem; color:var(--muted); margin-top:.4rem; }

/* ---------- cards ---------- */
.cards { display:grid; gap:1rem; margin:.4rem 0 1rem; }
.cards.c4 { grid-template-columns:repeat(4,1fr); }
.cards.c3 { grid-template-columns:repeat(3,1fr); }
.cards.c5 { grid-template-columns:repeat(5,1fr); }
.cards.c2 { grid-template-columns:repeat(2,1fr); }
.card { border-radius:16px; padding:1.05rem 1.2rem 1.1rem; background:var(--pale); border:1px solid var(--mid); }
.card.ivory { background:var(--ivory); border-color:#EFE9D2; }
.card.yellow { background:var(--yel); border-color:#F0E5AE; }
.card.mid { background:var(--mid); border-color:var(--mid2); }
.card.white { background:#fff; border-color:var(--line); }
.card.alert { background:#fff; border:1.5px solid var(--red); }
.card .label { font-size:.86rem; color:var(--muted); font-weight:600; }
.card .value { font-family:var(--display); font-size:2rem; font-weight:700; color:var(--dsage); line-height:1.15; margin-top:.2rem; }
.card.yellow .value { color:var(--deep); }
.card.alert .value { color:var(--red); }
.card .note { font-size:.82rem; color:var(--muted); margin-top:.25rem; line-height:1.4; }
.card h4 { margin:0 0 .35rem; font-size:1.02rem; }
.card p { margin:0; font-size:.93rem; }
.icon-dot { width:34px; height:34px; border-radius:50%; background:var(--mid2); display:grid; place-items:center; margin-bottom:.6rem; }
.card.yellow .icon-dot { background:var(--yel2); }

/* sequence */
.seq { display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; counter-reset:s; margin:.5rem 0 1rem; }
.seq .s { position:relative; background:var(--ivory); border:1px solid #EFE9D2; border-radius:16px; padding:1.1rem 1.15rem; }
.seq .s::before { counter-increment:s; content:counter(s); position:absolute; top:-12px; left:14px; width:26px; height:26px;
  border-radius:50%; background:var(--deep); color:#fff; font-family:var(--display); font-weight:700; font-size:.85rem;
  display:grid; place-items:center; }
.seq .s b { display:block; font-family:var(--display); color:var(--deep); margin-bottom:.25rem; }
.seq .s span { font-size:.9rem; color:var(--ink); line-height:1.5; }

/* confusion matrix */
.cm { display:grid; grid-template-columns:auto 1fr 1fr; gap:.5rem; align-items:stretch; max-width:560px; }
.cm .h { font-size:.8rem; color:var(--muted); font-weight:600; display:grid; place-items:center; text-align:center; padding:.2rem; }
.cm .c { border-radius:14px; padding:.9rem 1rem; }
.cm .c .n { font-family:var(--display); font-size:1.65rem; font-weight:700; line-height:1.1; }
.cm .c .t { font-size:.82rem; margin-top:.2rem; line-height:1.35; }
.cm .tn { background:var(--pale); } .cm .tn .n { color:var(--dsage); }
.cm .tp { background:var(--mid); } .cm .tp .n { color:var(--deep); }
.cm .fp { background:var(--yel); } .cm .fp .n { color:var(--deep); }
.cm .fn { background:#fff; border:1.5px solid var(--red); } .cm .fn .n { color:var(--red); }

/* badges and feed */
.badge { display:inline-block; padding:.18rem .6rem; border-radius:999px; font-size:.78rem; font-weight:700; }
.badge.ok { background:var(--mid); color:var(--deep); }
.badge.flag { background:#fff; color:var(--red); border:1.5px solid var(--red); }
.badge.best { background:var(--yel2); color:var(--deep); }
.feed { border:1px solid var(--line); border-radius:16px; overflow:hidden; background:#fff; }
.feed .row { display:grid; grid-template-columns:70px 1.1fr 1.2fr 1.3fr 1fr; gap:.6rem; padding:.7rem 1rem;
  align-items:center; font-size:.92rem; border-top:1px solid var(--line); }
.feed .row:nth-child(even) { background:#F5F8F0; }
.feed .row.head { background:var(--pale); border-top:none; font-weight:700; color:var(--deep); font-size:.84rem; }
.feed .row.empty { display:block; text-align:center; color:var(--muted); padding:1.6rem 1rem; }
.feed .mono { font-variant-numeric:tabular-nums; }
.bar-mini { height:8px; background:var(--mid); border-radius:4px; position:relative; }
.bar-mini i { position:absolute; left:0; top:0; bottom:0; border-radius:4px; background:var(--dsage); }
.bar-mini i.flag { background:var(--red); }
.bar-mini u { position:absolute; top:-3px; bottom:-3px; width:2px; background:var(--red); }

/* comparison table */
.tbl { width:100%; border-collapse:separate; border-spacing:0; border:1px solid var(--line); border-radius:16px; overflow:hidden; font-size:.92rem; }
.tbl th { background:var(--pale); color:var(--deep); text-align:right; padding:.7rem .9rem; font-weight:700; font-size:.84rem; }
.tbl th:first-child, .tbl td:first-child { text-align:left; }
.tbl td { padding:.7rem .9rem; text-align:right; border-top:1px solid var(--line); font-variant-numeric:tabular-nums; }
.tbl tr:nth-child(even) td { background:#F5F8F0; }
.tbl tr.sel td { background:var(--yel); font-weight:600; }
.tbl td.top { color:var(--dsage); font-weight:700; }
.tbl-wrap { overflow-x:auto; }

.callout { border-radius:14px; padding:.95rem 1.15rem; font-size:.95rem; line-height:1.55; margin:.6rem 0 1rem; }
.callout.warn { background:var(--yel); border-left:5px solid var(--yel2); }
.callout.alert { background:#fff; border:1.5px solid var(--red); border-left-width:6px; }
.callout.info { background:var(--pale); border-left:5px solid var(--sage); }
.callout b { color:var(--deep); }

/* ---------- streamlit widgets ---------- */
[data-testid="stForm"] { background:var(--ivory); border:1px solid #EFE9D2; border-radius:18px; padding:1.2rem 1.3rem .7rem; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input { border-radius:10px; }
[data-baseweb="select"] > div { border-radius:10px; }
.stButton > button, [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button {
  border-radius:12px; font-weight:700; min-height:2.7rem; border:1.5px solid var(--mid2);
  background:#fff; color:var(--deep); transition:background .15s ease, border-color .15s ease; }
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover { background:var(--pale); border-color:var(--sage); color:var(--deep); }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"], [data-testid="stDownloadButton"] button[kind="primary"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background:var(--deep) !important; border-color:var(--deep) !important; color:#fff !important; }
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover, [data-testid="stDownloadButton"] button[kind="primary"]:hover {
  background:var(--olive) !important; border-color:var(--olive) !important; }
[data-testid="stBaseButton-primary"] *, [data-testid="stBaseButton-primaryFormSubmit"] * { color:#fff !important; }
[data-testid="stTabs"] [role="tablist"] { gap:.3rem; border-bottom:1px solid var(--line); }
[data-testid="stTabs"] button[role="tab"] { border-radius:10px 10px 0 0; font-weight:600; color:var(--muted); padding:.55rem 1.1rem; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:var(--deep); background:var(--pale); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background:var(--deep); }
[data-testid="stFileUploader"] section { background:var(--ivory); border:2px dashed var(--mid2); border-radius:16px; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:14px; overflow:hidden; }
[data-testid="stImage"] img { border:1px solid var(--line); border-radius:14px; background:#fff; padding:.3rem; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:14px; background:#fff; }
[data-testid="stAlert"] { border-radius:12px; }
[data-testid="stSegmentedControl"] button, [data-testid="stPills"] button { border-radius:999px; }

.app-footer { margin-top:2.4rem; padding:1rem 1.3rem; border-radius:14px; background:var(--red); color:#fff;
  display:flex; flex-wrap:wrap; justify-content:space-between; gap:.4rem 1.2rem; font-size:.84rem; }
.app-footer b { font-family:var(--display); font-size:.95rem; color:#fff; }
.app-footer span { color:#FBE3E5; }

@media (max-width:980px) {
  .hero { grid-template-columns:1fr; }
  .cards.c4, .cards.c5 { grid-template-columns:repeat(2,1fr); }
  .cards.c3 { grid-template-columns:1fr; }
  .seq { grid-template-columns:repeat(2,1fr); gap:1.4rem 1rem; }
  .feed .row { grid-template-columns:60px 1fr 1fr; }
  .feed .row .hide-sm { display:none; }
}
@media (max-width:620px) {
  .block-container { padding:1.2rem 1rem 2rem; }
  .cards.c4, .cards.c5, .cards.c2, .seq { grid-template-columns:1fr; }
  .hero { padding:1.5rem 1.3rem; }
}
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
