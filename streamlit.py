import html
import pickle

import numpy as np
import streamlit as st

st.set_page_config(page_title="BookNest · Book Recommender", page_icon="📚", layout="wide")

PLACEHOLDER = "https://placehold.co/300x450/1f2937/9ca3af?text=No+Cover"

# ---------- Styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
.stApp { background: radial-gradient(circle at top left, #1e1b4b 0%, #0f172a 45%, #020617 100%); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1250px; }

.hero { text-align:center; padding: 2.2rem 1rem 1.2rem; }
.hero h1 { font-size: 3rem; font-weight: 700; margin: 0;
  background: linear-gradient(90deg,#f59e0b,#f472b6,#818cf8); -webkit-background-clip: text;
  -webkit-text-fill-color: transparent; }
.hero p { color:#94a3b8; font-size:1.05rem; margin-top:.4rem; }

.section-title { color:#f1f5f9; font-size:1.5rem; font-weight:600; margin:1.6rem 0 1rem;
  border-left: 5px solid #f59e0b; padding-left: .75rem; }

.grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 22px; }
.card { background: rgba(30,41,59,.65); border:1px solid rgba(148,163,184,.15); border-radius:16px;
  overflow:hidden; backdrop-filter: blur(6px); transition: transform .25s ease, box-shadow .25s ease;
  position:relative; }
.card:hover { transform: translateY(-8px); box-shadow: 0 18px 40px rgba(244,114,182,.25); }
.card img { width:100%; aspect-ratio: 2/3; object-fit:cover; display:block; background:#1f2937; }
.info { padding: 12px 14px 16px; }
.title { color:#f8fafc; font-weight:600; font-size:.92rem; line-height:1.3;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height:2.4em; }
.author { color:#94a3b8; font-size:.8rem; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.meta { margin-top:10px; display:flex; gap:8px; flex-wrap:wrap; }
.pill { font-size:.72rem; padding:3px 9px; border-radius:999px; font-weight:500; }
.rate { background:rgba(245,158,11,.18); color:#fbbf24; }
.votes { background:rgba(129,140,248,.18); color:#a5b4fc; }
.match { background:rgba(52,211,153,.18); color:#6ee7b7; }
.rank { position:absolute; top:10px; left:10px; background:linear-gradient(135deg,#f59e0b,#ef4444);
  color:white; font-weight:700; font-size:.8rem; padding:4px 10px; border-radius:999px; z-index:2; }

.picked { display:flex; gap:22px; align-items:center; background:rgba(30,41,59,.65);
  border:1px solid rgba(244,114,182,.35); border-radius:18px; padding:16px; margin-bottom:6px; }
.picked img { width:110px; border-radius:10px; }
.picked .t { color:#f8fafc; font-size:1.25rem; font-weight:600; }
.picked .a { color:#94a3b8; }

div[data-baseweb="select"] > div { background:#0f172a !important; border-radius:12px !important; }
.stButton > button { background:linear-gradient(90deg,#f59e0b,#ef4444); color:white; border:0;
  border-radius:12px; padding:.6rem 1.6rem; font-weight:600; transition: transform .2s; }
.stButton > button:hover { transform: scale(1.04); color:white; }
button[data-baseweb="tab"] { font-size:1.05rem; color:#cbd5e1; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------- Data ----------
@st.cache_resource
def load_data():
    popular = pickle.load(open("popular.pkl", "rb"))
    books = pickle.load(open("books.pkl", "rb"))
    pt = pickle.load(open("pt.pkl", "rb"))
    sim = pickle.load(open("similarity_score.pkl", "rb"))

    uniq = books.drop_duplicates("Book-Title")
    popular_full = (
        popular.merge(uniq, on="Book-Title")
        [["Book-Title", "Book-Author", "Image-URL-M", "num_ratings", "avg_ratings"]]
        .sort_values("avg_ratings", ascending=False)
        .reset_index(drop=True)
    )
    lookup = uniq.set_index("Book-Title")[["Book-Author", "Image-URL-M"]]
    return popular_full, lookup, pt, sim


popular_full, lookup, pt, sim = load_data()


def get_info(title):
    row = lookup.loc[title]
    return row["Book-Author"], str(row["Image-URL-M"]).replace("http://", "https://")


def recommend(title, n=5):
    idx = int(np.where(pt.index == title)[0][0])
    top = sorted(enumerate(sim[idx]), key=lambda x: x[1], reverse=True)[1 : n + 1]
    out = []
    for i, score in top:
        t = pt.index[i]
        author, img = get_info(t)
        out.append({"title": t, "author": author, "img": img, "match": score})
    return out


def card(item, rank=None):
    e = html.escape
    badge = f'<div class="rank">#{rank}</div>' if rank else ""
    pills = ""
    if "avg" in item:
        pills += f'<span class="pill rate">⭐ {item["avg"]:.2f}</span>'
        pills += f'<span class="pill votes">{item["votes"]} votes</span>'
    if "match" in item:
        pills += f'<span class="pill match">{item["match"] * 100:.0f}% match</span>'
    return (
        f'<div class="card">{badge}'
        f'<img src="{e(item["img"])}" onerror="this.onerror=null;this.src=\'{PLACEHOLDER}\';" loading="lazy">'
        f'<div class="info"><div class="title" title="{e(item["title"])}">{e(item["title"])}</div>'
        f'<div class="author">✍️ {e(str(item["author"]))}</div>'
        f'<div class="meta">{pills}</div></div></div>'
    )


def grid(items, ranked=False):
    cards = "".join(card(it, i + 1 if ranked else None) for i, it in enumerate(items))
    st.markdown(f'<div class="grid">{cards}</div>', unsafe_allow_html=True)


# ---------- UI ----------
st.markdown(
    '<div class="hero"><h1>📚 BookNest</h1>'
    "<p>Discover your next favourite read — trending picks & personalised recommendations</p></div>",
    unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["🔥 Top Books", "✨ Recommend For Me"])

with tab1:
    c1, c2 = st.columns([3, 1])
    with c2:
        top_n = st.slider("Kitni books dikhani hain?", 10, len(popular_full), 20, step=5)
    st.markdown('<div class="section-title">Most loved by readers</div>', unsafe_allow_html=True)
    items = [
        {
            "title": r["Book-Title"],
            "author": r["Book-Author"],
            "img": str(r["Image-URL-M"]).replace("http://", "https://"),
            "avg": r["avg_ratings"],
            "votes": int(r["num_ratings"]),
        }
        for _, r in popular_full.head(top_n).iterrows()
    ]
    grid(items, ranked=True)

with tab2:
    st.markdown('<div class="section-title">Ek book chuno, baaki hum batate hain</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns([4, 1])
    with col_a:
        selected = st.selectbox(
            "Book select karo (type karke search bhi kar sakte ho)",
            pt.index.tolist(),
            index=None,
            placeholder="e.g. 1984, The Notebook, Life of Pi...",
            label_visibility="collapsed",
        )
    with col_b:
        go = st.button("Recommend 🚀", use_container_width=True)

    if go and not selected:
        st.warning("Pehle koi book select karo.")
    elif go and selected:
        author, img = get_info(selected)
        st.markdown(
            f'<div class="picked"><img src="{html.escape(img)}" '
            f"onerror=\"this.onerror=null;this.src='{PLACEHOLDER}';\">"
            f'<div><div class="a">You picked</div><div class="t">{html.escape(selected)}</div>'
            f'<div class="a">by {html.escape(str(author))}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-title">Readers who liked this also liked</div>', unsafe_allow_html=True)
        grid(recommend(selected, 5))