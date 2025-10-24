# page_components/Members.py
import os
import pandas as pd
import streamlit as st
import unicodedata

from image_config import BASE_IMAGE_URL
from get_s3_images import _safe_join_url, _placeholder_for

DATA_PATH = "data/combined.csv"

BUCKET = "annablog"
AVATAR_ROOT = "images/avatar/"   # s3://annablog/images/members/<MemberName>/*

AVATAR_ROOT = "images/avatar/"   # s3://annablog/images/avatar/<lowercased-name>.webp

# ---------- S3 avatar helpers (flat files, no indexing needed) ----------
def _norm_lower(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "")).strip().lower()

def avatar_url_for(member_name: str) -> str:
    """
    Returns public HTTPS URL to the member's avatar using the convention:
      images/avatar/<lowercased name>.webp
    Fallbacks to a placeholder if name empty.
    """
    if not member_name:
        return _placeholder_for("Member")
    key = f"{AVATAR_ROOT}{_norm_lower(member_name)}.webp"
    return _safe_join_url(BASE_IMAGE_URL, key)

# ---------- data helpers ----------
def read_df_safe(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def get_first_existing(df: pd.DataFrame, options):
    return next((c for c in options if c in df.columns), None)

def normalize_species(val) -> str:
    if pd.isna(val): return "Unknown"
    s = str(val).strip().lower()
    if s in {"dog","dogs","canine"}: return "Dog"
    if s in {"cat","cats","feline"}: return "Cat"
    return "Unknown"

def most_common_nonempty(series: pd.Series, prefer_first=True):
    s = series.dropna().astype(str).str.strip()
    s = s[s != ""]
    if s.empty: return "Unknown"
    vc = s.value_counts()
    top_count = vc.iloc[0]
    candidates = vc[vc == top_count].index.tolist()
    if prefer_first:
        for v in s:
            if v in candidates:
                return v
    return vc.index[0]

def title_name(name: str) -> str:
    try:
        return " ".join([w.capitalize() if w.isascii() else w for w in str(name).split()])
    except Exception:
        return str(name).title()

def build_members(df: pd.DataFrame):
    name_col = get_first_existing(df, ["Name","Pet Name","Pet"])
    if not name_col:
        st.error("Could not find a pet name column (expected 'Name' / 'Pet Name' / 'Pet').")
        return pd.DataFrame()

    species_col  = get_first_existing(df, ["Species","Type","Category","Kind"])
    gender_col   = get_first_existing(df, ["Gender","Sex","Pet Gender","Pet Sex"])
    breed_col    = get_first_existing(df, ["Breed","Breeds","Dog Breed","Cat Breed"])
    platform_col = get_first_existing(df, ["Platform","Source","Channel"])

    # Dates / price columns (best-effort)
    arr_col  = get_first_existing(df, ["Arrival Date","Check-in","Start Date","Start"])
    dep_col  = get_first_existing(df, ["Departure Date","Check-out","End Date","End"])
    rate_col = get_first_existing(df, ["daily price","Daily Price","Rate","Price per Day","Price/Day"])

    if species_col is None:
        df["__Species__"] = "Unknown"
        species_col = "__Species__"
    df["__SpeciesNorm__"] = df[species_col].apply(normalize_species)

    # Columns for avg daily price = SUM(Price) / SUM(Duration)
    price_col    = get_first_existing(df, ["Price","Total Price","Charge","Amount"])
    duration_col = get_first_existing(df, ["Duration","Nights","Length","Days"])

    # Normalize types used in metrics
    if arr_col:      df[arr_col]      = pd.to_datetime(df[arr_col], errors="coerce")
    if dep_col:      df[dep_col]      = pd.to_datetime(df[dep_col], errors="coerce")
    if rate_col:     df[rate_col]     = pd.to_numeric(df[rate_col], errors="coerce")
    if price_col:    df[price_col]    = pd.to_numeric(df[price_col], errors="coerce")
    if duration_col: df[duration_col] = pd.to_numeric(df[duration_col], errors="coerce")

    df["__name_key__"] = df[name_col].astype(str).str.strip().str.lower()
    groups = df.groupby("__name_key__", dropna=True)

    rows = []
    for key, g in groups:
        display_name = title_name(most_common_nonempty(g[name_col]))
        species = most_common_nonempty(g["__SpeciesNorm__"])
        gender  = most_common_nonempty(g[gender_col]) if gender_col else "Unknown"
        breed   = most_common_nonempty(g[breed_col]) if breed_col else "Unknown"
        platform= most_common_nonempty(g[platform_col]) if platform_col else "Unknown"
        avatar  = avatar_url_for(display_name)  # <<< S3 URL or data-URL placeholder

        # ---- Metrics ----
        if arr_col and dep_col:
            valid = g[[arr_col, dep_col]].dropna()
            visits = len(valid[valid[dep_col] >= valid[arr_col]])
            nights = valid.apply(lambda r: max((r[dep_col] - r[arr_col]).days, 0), axis=1).sum()
            first_visit = g[arr_col].min()
        else:
            visits, nights, first_visit = 0, 0, pd.NaT

        # AvgDailyPrice = SUM(Price) / SUM(Duration)
        total_price = None
        total_duration = None

        if price_col:
            total_price = pd.to_numeric(g[price_col], errors="coerce").dropna().sum()

        if duration_col:
            total_duration = pd.to_numeric(g[duration_col], errors="coerce").dropna()
            total_duration = total_duration[total_duration > 0].sum()

        if (total_duration is None or total_duration == 0) and (arr_col and dep_col):
            valid_dates = g[[arr_col, dep_col]].dropna()
            if not valid_dates.empty:
                nights_series = valid_dates.apply(
                    lambda r: max((r[dep_col] - r[arr_col]).days, 0), axis=1
                )
                total_duration = float(nights_series.sum())

        if (total_price is None or total_price == 0) and rate_col and total_duration and total_duration > 0:
            avg_rate = pd.to_numeric(g[rate_col], errors="coerce").dropna().mean()
            if pd.notna(avg_rate):
                total_price = float(avg_rate) * float(total_duration)

        if (total_price is not None) and pd.notna(total_price) and total_price > 0 and \
           (total_duration is not None) and pd.notna(total_duration) and total_duration > 0:
            avg_daily_price = float(total_price) / float(total_duration)
        else:
            avg_daily_price = float("nan")

        rows.append({
            "name_key": key,
            "Name": display_name,
            "Species": species,
            "Gender": gender,
            "Breed": breed,
            "Platform": platform,
            "Avatar": avatar,            # <<< already browser-loadable
            "Visits": int(visits),
            "Nights": int(nights),
            "AvgDailyPrice": avg_daily_price,
            "FirstVisit": first_visit,
        })

    members = pd.DataFrame(rows)

    # Cleanups
    for c in ["Gender","Breed","Platform"]:
        if c in members.columns:
            members[c] = members[c].astype(str).str.strip().replace({"": "Unknown"})
    if "FirstVisit" in members.columns:
        members["FirstVisit"] = pd.to_datetime(members["FirstVisit"], errors="coerce")

    return members

# ---------- UI helpers ----------
# ---------- UI helpers (responsive grid: 2 per row on phones) ----------
def grid_cards(df: pd.DataFrame, img_size=140, label_col="Name", meta_col=None):
    if df.empty:
        st.info("No members match your filters yet.")
        return

    # CSS (no Python {} inside; we just replace the size token)
    css = """
    <style>
      .members-grid {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(8, minmax(0, 1fr));
      }
      @media (max-width: 1400px) { .members-grid { grid-template-columns: repeat(6, 1fr); } }
      @media (max-width: 1100px) { .members-grid { grid-template-columns: repeat(5, 1fr); } }
      @media (max-width: 900px)  { .members-grid { grid-template-columns: repeat(4, 1fr); } }
      @media (max-width: 700px)  { .members-grid { grid-template-columns: repeat(4, 1fr); } }
      @media (max-width: 520px)  { .members-grid { grid-template-columns: repeat(4, 1fr); } } /* phones */

      .member-card  { text-align:center; padding:8px 4px; }
      .member-name  { margin-top:8px; font-weight:700; color:#5a3b2e; line-height:1.2; font-size:15px; word-break:break-word; }
      .member-meta  { margin-top:2px; color:#7a7a7a; font-size:12px; line-height:1.2; }

      .member-avatar {
        width: 100%;
        max-width: VAR_IMG_SIZEpx;  /* replaced below */
        aspect-ratio: 1/1;
        margin: 0 auto;
        display: block;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #f4cbba;
        box-shadow: 0 2px 8px rgba(90,59,46,0.15);
      }
      
    </style>
    """.replace("VAR_IMG_SIZE", str(int(img_size)))
    st.markdown(css, unsafe_allow_html=True)

    # Build flat, no-indent HTML (important: no starting spaces/newlines)
    cards = []
    for _, row in df.iterrows():
        src   = row.get("Avatar", _placeholder_for("Member"))
        label = row.get(label_col, row.get("Name", ""))
        meta  = str(row.get(meta_col, "")) if meta_col else ""
        meta_html = f'<div class="member-meta">{meta}</div>' if meta else ""
        cards.append(
            f'<div class="member-card">'
            f'<img class="member-avatar" src="{src}" alt="{label}"/>'
            f'<div class="member-name">{label}</div>'
            f'{meta_html}'
            f'</div>'
        )

    html = '<div class="members-grid">' + "".join(cards) + '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ---------- page ----------
def main():
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

    st.title("🧑‍🤝‍🧑 Members")
    # --- brown accent styling ---
    st.markdown("""
    <style>
    :root { --primary-color: #603D35; }
    [data-baseweb="tab-list"] > [role="tab"][aria-selected="true"] {
        color: #603D35 !important; border-bottom: 2px solid #603D35 !important;
    }
    [data-baseweb="tab-list"] > [role="tab"]:focus { outline-color: #603D35 !important; }
    .stMultiSelect [data-baseweb="tag"] { background-color:#f4cbba !important; border-color:#e2b6a2 !important; color:#3a251c !important; }
    .stMultiSelect [data-baseweb="menu"] [aria-selected="true"] { background-color:#f6e7e0 !important; color:#3a251c !important; }
    input[type="checkbox"]:checked, input[type="radio"]:checked { accent-color:#603D35; }
    </style>
    """, unsafe_allow_html=True)

    st.caption("All unique pets that have visited the kingdom. Filter by Species, Gender, Breed, and Platform.")

    df = read_df_safe(DATA_PATH)
    if df.empty:
        st.info("No data yet.")
        return

    members = build_members(df)
    if members.empty:
        return

    # ---- Filters ----
    c1, c2, c3, c4 = st.columns([1,1,1,1.2])

    species_opts = sorted(members["Species"].fillna("Unknown").unique().tolist())
    species_sel = c1.multiselect("Species", species_opts, default=species_opts)

    gender_opts = sorted(members["Gender"].fillna("Unknown").unique().tolist())
    gender_sel  = c2.multiselect("Gender", gender_opts, default=gender_opts)

    platform_opts = sorted(members["Platform"].fillna("Unknown").unique().tolist())
    platform_sel  = c3.multiselect("Platform", platform_opts, default=platform_opts)

    breed_opts = ["All"] + sorted(members["Breed"].fillna("Unknown").unique().tolist())
    breed_sel = c4.selectbox("Breed", breed_opts, index=0)

    # Apply filters
    view = members.copy()
    view = view[view["Species"].isin(species_sel)]
    view = view[view["Gender"].isin(gender_sel)]
    view = view[view["Platform"].isin(platform_sel)]
    if breed_sel != "All":
        view = view[view["Breed"] == breed_sel]
    
    # ---- Sort controls ----
    sort_config = {
        "Name (A→Z)": {
            "col": "Name",
            "orders": [("A → Z", True), ("Z → A", False)],
            "metric": None,
        },
        "Number of Visits": {
            "col": "Visits",
            "orders": [("Most visits first", False), ("Fewest visits first", True)],
            "metric": "visits",
        },
        "Total Staying Length (nights)": {
            "col": "Nights",
            "orders": [("Longest first", False), ("Shortest first", True)],
            "metric": "nights",
        },
        "Average Daily Price": {
            "col": "AvgDailyPrice",
            "orders": [("Highest first", False), ("Lowest first", True)],
            "metric": "avg_price",
        },
        "First Visit date": {
            "col": "FirstVisit",
            "orders": [("Newest first", False), ("Oldest first", True)],
            "metric": None,
        },
    }

    sort_choice = st.selectbox("Sort by", list(sort_config.keys()), index=0)
    cfg = sort_config[sort_choice]

    # --- metric line formatter ---
    def _plural(n, singular, plural=None):
        try:
            n_int = int(n) if pd.notna(n) else 0
        except Exception:
            n_int = 0
        return f"{n_int} {singular if abs(n_int)==1 else (plural or singular+'s')}"

    def _fmt_money(x):
        return f"${x:,.2f}" if pd.notna(x) else "—"

    # --- Add secondary info line under names ---
    view = view.copy()
    metric_kind = cfg.get("metric")

    if metric_kind == "visits":
        view["MetricLine"] = view.apply(lambda r: f"{_plural(r.get('Visits'), 'visit')}", axis=1)
    elif metric_kind == "nights":
        view["MetricLine"] = view.apply(lambda r: f"{_plural(r.get('Nights'), 'night')}", axis=1)
    elif metric_kind == "avg_price":
        view["MetricLine"] = view.apply(lambda r: f"{_fmt_money(r.get('AvgDailyPrice'))} / day", axis=1)
    else:
        view["MetricLine"] = ""

    # --- apply sorting ---
    order_labels = [lbl for (lbl, _) in cfg["orders"]]
    order_choice = st.radio("Order", order_labels, index=0, horizontal=True)
    ascending = dict(cfg["orders"])[order_choice]

    sort_col = cfg["col"]
    view = view.sort_values(
        by=[sort_col, "Name"],
        ascending=[ascending, True],
        kind="mergesort",
        na_position="last",
    )

    st.caption(f"Showing **{len(view)}** members")
    grid_cards(view, img_size=140, label_col="Name", meta_col="MetricLine")


if __name__ == "__main__":
    main()
