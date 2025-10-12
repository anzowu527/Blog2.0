# page_components/Kingdom_Stats.py
import os
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_echarts import st_echarts
from streamlit_echarts import st_echarts, JsCode

DATA_PATH = "data/combined.csv"

# ---------------- Helpers ----------------
def _clean_money_like(series: pd.Series) -> pd.Series:
    """Remove $, commas, spaces; coerce to float."""
    return (
        series.astype(str)
              .str.replace(r"[\$,]", "", regex=True)
              .str.strip()
              .replace({"": None})
              .pipe(pd.to_numeric, errors="coerce")
    )

def compute_box_data(df: pd.DataFrame):
    """
    Build arrays for boxplots using your existing columns:
      - Duration        <- 'Duration' column
      - Price per stay  <- 'Price' (total per booking)
      - Daily price     <- 'Daily Price' column
    Filters out rows where Type contains 'drop' (Drop-In).
    Each metric is computed independently (no cross-dropping).
    """
    svc_col    = get_service_col(df)
    price_col  = get_first_existing(df, ["Price", "Total Price"])
    dur_col    = get_first_existing(df, ["Duration", "Nights", "Days"])
    daily_col  = get_first_existing(df, ["daily price"])

    if not (dur_col or price_col or daily_col):
        return None  # nothing to plot

    x = df.copy()
    # Exclude Drop-Ins if Type exists
    if svc_col:
        svc = x[svc_col].astype(str).str.lower()
        x = x[~svc.str.contains("drop", na=False)].copy()

    # ----- Duration (from column) -----
    durations = []
    if dur_col:
        dur_vals = pd.to_numeric(x[dur_col], errors="coerce")
        durations = [int(v) if float(v).is_integer() else float(v) for v in dur_vals.dropna().tolist()]

    # ----- Price per stay (from Price column) -----
    prices = []
    if price_col:
        price_vals = _clean_money_like(x[price_col]).dropna()
        prices = [float(v) for v in price_vals.tolist()]

    # ----- Daily price (from daily price column) -----
    daily = []
    if daily_col:
        daily_vals = _clean_money_like(x[daily_col]).dropna()
        daily = [float(v) for v in daily_vals.tolist()]

    if not (durations or prices or daily):
        return None

    return {
        "Duration": durations,
        "Price": prices,
        "Daily Price": daily,
    }


def read_df_safe(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def normalize_species(val) -> str:
    if pd.isna(val): return "Unknown"
    s = str(val).strip().lower()
    if s in {"dog", "dogs", "canine"}: return "Dog"
    if s in {"cat", "cats", "feline"}: return "Cat"
    return "Unknown"

def get_first_existing(df: pd.DataFrame, options):
    return next((c for c in options if c in df.columns), None)

def coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["Arrival Date", "Arrival", "Check-in", "Check In", "Start Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["Departure Date", "Departure", "Check-out", "Check Out", "End Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def safe_name_series(series: pd.Series) -> pd.Series:
    return series.dropna().astype(str).str.strip().str.lower()

def get_channel_col(df: pd.DataFrame):
    return get_first_existing(df, ["Platform", "Source", "Channel"])

def get_service_col(df: pd.DataFrame):
    return get_first_existing(df, ["Type"])

def is_shelter(val) -> bool:
    if pd.isna(val): return False
    s = str(val).strip().lower()
    return s == "shelter"

def exclude_shelter_dogs(df: pd.DataFrame, species_col_norm: str) -> pd.DataFrame:
    """Drop rows where species is Dog AND channel is Shelter. Cats unaffected."""
    ch_col = get_channel_col(df)
    if not ch_col:
        # No channel field — keep as-is (can’t detect shelter)
        return df
    mask_dog = df[species_col_norm] == "Dog"
    mask_shelter = df[ch_col].apply(is_shelter)
    return df[~(mask_dog & mask_shelter)].copy()

def exclude_dropins(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows whose service contains 'drop' (Drop-In / Drop in / dropping)."""
    svc_col = get_service_col(df)
    if not svc_col:
        return df
    svc = df[svc_col].astype(str).str.lower()
    return df[~svc.str.contains("drop", na=False)].copy()

# ---------- Donut ----------
def ec_donut(total: int, dogs: int, cats: int, subtitle: str = "Total"):
    donut_data = [
        {"name": "Dog", "value": int(dogs)},
        {"name": "Cat", "value": int(cats)},
    ]
    option = {
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"show": False},
        "color": ["#8b5e3c", "#f4cbba"],
        "title": {
            "text": f"{total}",
            "subtext": subtitle,                       # <— was "Total"
            "left": "center",
            "top": "38%",
            "textStyle": {"fontSize": 28, "fontWeight": "bold", "color": "#5a3b2e"},
            "subtextStyle": {"fontSize": 14, "color": "#5a3b2e"},
        },
        "series": [{
            "name": subtitle,
            "type": "pie",
            "radius": ["35%", "80%"],
            "center": ["50%", "45%"],
            "avoidLabelOverlap": True,
            "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": True, "formatter": "{b}: {c}"},
            "labelLine": {"show": True},
            "data": donut_data,
        }],
    }
    return option

def is_dropin_service(val) -> bool:
    if pd.isna(val): return False
    s = str(val).strip().lower()
    return "drop" in s  # matches Drop-In / Drop in / dropping

def ec_donut_visits_split(title_total: int,
                          dog_board: int, dog_drop: int,
                          cat_board: int, cat_drop: int,
                          subtitle: str = "Visits"):
    dog_color = "#8b5e3c"   # Dog (same color for both slices)
    cat_color = "#f4cbba"   # Cat (same color for both slices)

    data = [
        {
            "name": "Dog • Boarding",
            "value": int(dog_board),
            "itemStyle": {"color": dog_color},
            # optional visual cue while keeping same color:
            "decal": {"symbol": "line", "dashArrayX": [4, 2], "dashArrayY": [2, 0]}
        },
        {
            "name": "Dog • Drop-In",
            "value": int(dog_drop),
            "itemStyle": {"color": dog_color},
            "decal": {"symbol": "dot"}
        },
        {
            "name": "Cat • Boarding",
            "value": int(cat_board),
            "itemStyle": {"color": cat_color},
            "decal": {"symbol": "line", "dashArrayX": [4, 2], "dashArrayY": [2, 0]}
        },
        {
            "name": "Cat • Drop-In",
            "value": int(cat_drop),
            "itemStyle": {"color": cat_color},
            "decal": {"symbol": "dot"}
        },
    ]

    return {
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"show": False},
        "title": {
            "text": f"{title_total}",
            "subtext": subtitle,
            "left": "center", "top": "38%",
            "textStyle": {"fontSize": 28, "fontWeight": "bold", "color": "#5a3b2e"},
            "subtextStyle": {"fontSize": 14, "color": "#5a3b2e"},
        },
        "series": [{
            "name": subtitle,
            "type": "pie",
            "radius": ["35%", "80%"],
            "center": ["50%", "45%"],
            "avoidLabelOverlap": True,
            "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": True, "formatter": "{b}: {c}"},
            "labelLine": {"show": True},
            "data": data,
            "animationDuration": 900, "animationEasing": "cubicOut",
        }],
    }


# ---------- Vertical Bar (with gradient, rounded corners, labels) ----------
def ec_bar_vertical(names, values, series_name="Count"):
    return {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "toolbox": {"feature": {"saveAsImage": {}, "dataView": {"readOnly": True}}},
        "grid": {"left": "3%", "right": "4%", "bottom": "18%", "top": "8%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": names,
            "axisLabel": {"interval": 0, "rotate": 30},
        },
        "yAxis": {"type": "value"},
        "series": [{
            "name": series_name,
            "type": "bar",
            "data": values,
            "barWidth": 28,
            "itemStyle": {
                "borderRadius": [10, 10, 0, 0],
                "shadowBlur": 8,
                "shadowColor": "rgba(90,59,46,0.2)",
                "color": {
                    "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": "#8b5e3c"},
                        {"offset": 1, "color": "#f4cbba"},
                    ],
                },
            },
            "label": {"show": True, "position": "top", "formatter": "{c}"},
            "animationDuration": 900,
            "animationEasing": "cubicOut",
        }],
    }

# ---------- Species Split Helpers (with filters) ----------
def top_visits_by_species(df: pd.DataFrame, species: str, name_col: str, limit=10, dropin_excluded=False):
    sub = df[df["__SpeciesNorm__"] == species]
    if dropin_excluded:
        sub = exclude_dropins(sub)
    if sub.empty:
        return [], []
    counts = (
        sub.assign(__name_norm__=safe_name_series(sub[name_col]))
           .groupby("__name_norm__", dropna=True)
           .size()
           .sort_values(ascending=False)
           .head(limit)
    )
    names = [n.title() for n in counts.index.tolist()]
    values = counts.values.astype(int).tolist()
    return names, values

def top_days_by_species(df: pd.DataFrame, species: str, name_col: str, arr_col: str, dep_col: str, limit=10):
    sub = df[df["__SpeciesNorm__"] == species]
    if sub.empty or not arr_col or not dep_col:
        return [], []
    x = sub[[name_col, arr_col, dep_col]].dropna(subset=[name_col, arr_col, dep_col]).copy()
    if x.empty:
        return [], []
    x["__name_norm__"] = safe_name_series(x[name_col])
    x["__days__"] = (x[dep_col] - x[arr_col]).dt.days.clip(lower=0).fillna(0)
    totals = (
        x.groupby("__name_norm__")["__days__"]
         .sum()
         .sort_values(ascending=False)
         .head(limit)
    )
    names = [n.title() for n in totals.index.tolist()]
    values = totals.values.astype(int).tolist()
    return names, values

def representative_breed_per_pet(df: pd.DataFrame, name_col: str, breed_col: str) -> pd.DataFrame:
    """
    For each pet (by normalized name), choose the most frequent non-empty breed as representative.
    Returns a DataFrame with columns: __name_norm__, __breed_rep__.
    """
    x = df[[name_col, breed_col]].copy()
    x["__name_norm__"] = safe_name_series(x[name_col])
    x["__breed__"] = x[breed_col].fillna("Unknown").astype(str).str.strip()
    x.loc[x["__breed__"] == "", "__breed__"] = "Unknown"
    # mode per pet (break ties by first occurrence)
    counts = (
        x.groupby(["__name_norm__", "__breed__"])
         .size()
         .reset_index(name="cnt")
         .sort_values(["__name_norm__", "cnt"], ascending=[True, False])
    )
    reps = counts.groupby("__name_norm__", as_index=False).first().rename(columns={"__breed__":"__breed_rep__"})
    return reps[["__name_norm__", "__breed_rep__"]]

def top_breeds_by_species(df: pd.DataFrame, species: str, name_col: str, breed_col: str, limit=10):
    """
    Count breeds AFTER grouping by pet (unique names) -> representative breed.
    """
    sub = df[df["__SpeciesNorm__"] == species]
    if sub.empty or not breed_col:
        return [], []
    reps = representative_breed_per_pet(sub, name_col, breed_col)
    top = reps["__breed_rep__"].value_counts().head(limit)
    names = top.index.tolist()
    values = top.values.astype(int).tolist()
    return names, values

def ec_rose(names, values, title_text):
    data = [{"name": n, "value": int(v)} for n, v in zip(names, values)]
    # Keep names short on petals
    for d in data:
        if len(d["name"]) > 10:
            d["name"] = d["name"][:10] + "…"

    return {
        "title": {"text": title_text, "left": "center", "top": 0,
                  "textStyle": {"fontSize": 14, "color": "#5a3b2e"}},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} visits ({d}%)"},
        "legend": {"show": False},
        "color": ["#8b5e3c", "#a26f4c", "#b7815c", "#cb9370", "#dba885",
                  "#e7b89a", "#efc9ae", "#f4d7c1", "#f6dfcc", "#f9e7d7"],
        "series": [{
            "type": "pie",
            "roseType": "radius",           # Nightingale style
            "radius": ["12%", "70%"],
            "center": ["50%", "55%"],
            "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": True, "formatter": "{b}\n{c}"},
            "labelLine": {"length": 8, "length2": 6},
            "data": data,
            "animationDuration": 900,
            "animationEasing": "cubicOut",
        }]
    }

def ec_sunburst(labels, values, title_text):
    data = [{"name": str(n), "value": int(v)} for n, v in zip(labels, values)]
    # trim long labels a bit for neat petals
    for d in data:
        if len(d["name"]) > 14:
            d["name"] = d["name"][:14] + "…"
    return {
        "title": {"text": title_text, "left": "center", "top": 0,
                  "textStyle": {"fontSize": 14, "color": "#5a3b2e"}},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} pets"},
        "series": [{
            "type": "sunburst",
            "radius": ["12%", "85%"],
            "center": ["50%", "55%"],
            "sort": None,            # keep your order (already top-10)
            "data": data,
            "label": {"rotate": "radial"},
            "itemStyle": {"borderColor": "#fff", "borderWidth": 2},
            "levels": [
                {},  # inner
                {
                    "r0": "12%", "r": "85%",
                    "label": {"rotate": "radial"},
                    "itemStyle": {"shadowBlur": 8, "shadowColor": "rgba(90,59,46,0.15)"},
                },
            ],
            "color": ["#8b5e3c","#a26f4c","#b7815c","#cb9370","#dba885",
                      "#e7b89a","#efc9ae","#f4d7c1","#f6dfcc","#f9e7d7"],
            "animationDuration": 900, "animationEasing": "cubicOut",
        }]
    }

def ec_box_single(title_text: str, values, is_currency: bool = False, y_label: str = "", left_pad=72):
    import numpy as np

    def five_num_summary(vals):
        # keep only finite numbers
        arr = []
        for v in vals or []:
            try:
                f = float(v)
                if np.isfinite(f):
                    arr.append(f)
            except Exception:
                pass
        arr = np.asarray(arr, dtype=float)

        n = arr.size
        if n == 0:
            return None
        if n == 1:
            v = float(arr[0])
            return [v, v, v, v, v]

        q1 = float(np.percentile(arr, 25))
        q2 = float(np.percentile(arr, 50))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        lower = float(max(float(arr.min()), q1 - 1.5 * iqr))
        upper = float(min(float(arr.max()), q3 + 1.5 * iqr))
        return [round(lower, 4), round(q1, 4), round(q2, 4), round(q3, 4), round(upper, 4)]

    stats = five_num_summary(values)
    y_axis = {"type": "value", "min": 0, "axisLabel": {"margin": 6}}
    if is_currency:
        y_axis["axisLabel"]["formatter"] = "${value}"
    elif y_label:
        y_axis["axisLabel"]["formatter"] = "{value} " + y_label

    series_data = [] if stats is None else [stats]

    option = {
        "title": {"text": title_text, "left": "center",
                  "textStyle": {"fontSize": 14, "color": "#5a3b2e"}},
        "tooltip": {"show": False},
        "grid": {"left": left_pad, "right": 24, "top": 48, "bottom": 36, "containLabel": True},
        "xAxis": {"type": "category", "data": [title_text], "axisTick": {"alignWithLabel": True}},
        "yAxis": y_axis,
        "series": [{
            "type": "boxplot",
            "data": series_data,  # [] if no data -> renders nothing (no crash)
            "itemStyle": {"color": "#f4cbba", "borderColor": "#8b5e3c", "borderWidth": 1.5},
            "boxWidth": [20, 60],
        }],
        "animationDuration": 900,
        "animationEasing": "cubicOut",
        "legend": {"show": False},
    }

    # Optional: show a subtle "No data" overlay when empty
    if not series_data:
        option["graphic"] = [{
            "type": "text",
            "left": "center",
            "top": "middle",
            "style": {"text": "No data", "fontSize": 14, "fill": "#8b5e3c"}
        }]

    return option

def five_num_summary_py(values):
    """Pure-Python five-number summary + count/mean (JSON-safe)."""
    import numpy as np
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return None
    q1 = float(np.percentile(arr, 25))
    q2 = float(np.percentile(arr, 50))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    lower = float(max(float(arr.min()), q1 - 1.5 * iqr))
    upper = float(min(float(arr.max()), q3 + 1.5 * iqr))
    return {
        "min": round(lower, 2),
        "Q1": round(q1, 2),
        "median": round(q2, 2),
        "Q3": round(q3, 2),
        "max": round(upper, 2),
        "count": int(arr.size),
        "mean": round(float(arr.mean()), 2),
    }

def fmt_stats_block(title, stats, currency=False, unit=""):
    if not stats:
        return f"**{title}**\n\n_No data_"
    def f(x):
        if currency:
            return f"${x:,.2f}"
        return f"{x:,.2f}{(' ' + unit) if unit else ''}"
    return (
        f"**{title}**  \n"
        f"- min: **{f(stats['min'])}**  \n"
        f"- Q1: **{f(stats['Q1'])}**  \n"
        f"- median: **{f(stats['median'])}**  \n"
        f"- Q3: **{f(stats['Q3'])}**  \n"
        f"- max: **{f(stats['max'])}**  \n"
        f"- mean: **{f(stats['mean'])}**"
    )

# ---------------- Main ----------------
def main():
    st.title("📈 Kingdom Statistics")
    st.caption("Excludes shelter dogs.")

    df = read_df_safe(DATA_PATH)
    if df.empty:
        st.info("No data yet. Add bookings to see stats.")
        return

    # Identify key columns
    name_col = get_first_existing(df, ["Name", "Pet Name", "Pet"])
    if not name_col:
        st.error("Could not find a pet name column (expected 'Name' / 'Pet Name' / 'Pet').")
        return

    species_col = get_first_existing(df, ["Species", "Type", "Category", "Kind"])
    if species_col is None:
        df["__Species__"] = "Unknown"
        species_col = "__Species__"

    breed_col = get_first_existing(df, ["Breed", "Breeds", "Dog Breed", "Cat Breed"])

    # Normalize species and names
    df = coerce_dates(df)
    df["__SpeciesNorm__"] = df[species_col].apply(normalize_species)

    # ---- Global filter: exclude shelter dogs everywhere ----
    df = exclude_shelter_dogs(df, "__SpeciesNorm__")

    # For donut unique counts, dedupe by name within species
    names_series = safe_name_series(df[name_col])
    dog_names = names_series[df["__SpeciesNorm__"] == "Dog"].unique()
    cat_names = names_series[df["__SpeciesNorm__"] == "Cat"].unique()
    dogs = len(dog_names)
    cats = len(cat_names)
    total = dogs + cats


    # ---- Unique Pets + Total Visits donuts ----
    st.subheader("Unique Pets & Total Visits")

    left, right = st.columns(2)

    # Unique pets (already deduped by name within species)
    with left:
        st.markdown("**Unique Pets**")
        st_echarts(ec_donut(total, dogs, cats, subtitle="Unique"), height="380px")

    # Total visits (split by Boarding vs Drop-In, still colored by species)
    with right:
        st.markdown("**Total Visits**")
        svc_col = get_service_col(df)
        if svc_col:
            svc = df[svc_col].astype(str).str.lower()
            is_drop = svc.apply(is_dropin_service)
        else:
            # If no service column, treat all as Boarding/Other
            is_drop = pd.Series(False, index=df.index)

        is_dog = (df["__SpeciesNorm__"] == "Dog")
        is_cat = (df["__SpeciesNorm__"] == "Cat")

        dog_board = int((is_dog & ~is_drop).sum())
        dog_drop  = int((is_dog &  is_drop).sum())
        cat_board = int((is_cat & ~is_drop).sum())
        cat_drop  = int((is_cat &  is_drop).sum())

        visits_total = dog_board + dog_drop + cat_board + cat_drop

        st_echarts(
            ec_donut_visits_split(
                visits_total,
                dog_board, dog_drop,
                cat_board, cat_drop,
                subtitle="Visits"
            ),
            height="380px"
        )

    st.markdown("---")

    # ---------- Boarding Price & Duration Distributions ----------
    box_data = compute_box_data(df)
    if not box_data:
        st.info("Missing columns or not enough boarding data to plot boxplots.")
    else:
        total_stays = len(box_data["Duration"])
        st.subheader(f"Boarding Price & Duration Distributions – {total_stays} Stays")
        st.caption("Excludes Drop-in Visits.")

        c1, c2, c3 = st.columns([1.15, 1, 1])

        with c1:
            st_echarts(
                ec_box_single("Duration (days)", box_data["Duration"], y_label="days", left_pad=84),
                height="360px"
            )
            st.markdown(
                fmt_stats_block("Duration (days)", five_num_summary_py(box_data["Duration"]), currency=False, unit="days")
            )

        with c2:
            st_echarts(
                ec_box_single("Price per stay", box_data["Price"], is_currency=True, left_pad=72),
                height="360px"
            )
            st.markdown(
                fmt_stats_block("Price per stay", five_num_summary_py(box_data["Price"]), currency=True)
            )

        with c3:
            st_echarts(
                ec_box_single("Daily price", box_data["Daily Price"], is_currency=True, left_pad=72),
                height="360px"
            )
            st.markdown(
                fmt_stats_block("Daily price", five_num_summary_py(box_data["Daily Price"]), currency=True)
            )

    st.markdown("---")

    # ---------- Top 10 Pets by Visit Count (rose charts; Drop-Ins excluded) ----------
    st.subheader("Top 10 Pets by Visit Count")
    col_dog, col_cat = st.columns(2)

    d_names, d_vals = top_visits_by_species(df, "Dog", name_col, limit=10, dropin_excluded=True)
    c_names, c_vals = top_visits_by_species(df, "Cat", name_col, limit=10, dropin_excluded=True)

    with col_dog:
        if d_names:
            st_echarts(ec_rose(d_names, d_vals, "Dogs"), height="460px")
        else:
            st.info("No dog visits (after filters).")

    with col_cat:
        if c_names:
            st_echarts(ec_rose(c_names, c_vals, "Cats"), height="460px")
        else:
            st.info("No cat visits (after filters).")


    st.markdown("---")

    # ---------- Top 10 Pets by Total Stay Length (days) (vertical, split) ----------
    st.subheader("Top 10 Pets by Total Stay Length (days)")
    arr_col = get_first_existing(df, ["Arrival Date", "Arrival", "Check-in", "Check In", "Start Date"])
    dep_col = get_first_existing(df, ["Departure Date", "Departure", "Check-out", "Check Out", "End Date"])

    col_dog2, col_cat2 = st.columns(2)
    if arr_col and dep_col:
        d_names2, d_vals2 = top_days_by_species(df, "Dog", name_col, arr_col, dep_col, limit=10)
        c_names2, c_vals2 = top_days_by_species(df, "Cat", name_col, arr_col, dep_col, limit=10)

        with col_dog2:
            st.markdown("**🐶 Dogs**")
            if d_names2:
                st_echarts(ec_bar_vertical(d_names2, d_vals2, series_name="Days"), height="420px")
            else:
                st.info("Not enough dated dog stays (after filters).")

        with col_cat2:
            st.markdown("**🐱 Cats**")
            if c_names2:
                st_echarts(ec_bar_vertical(c_names2, c_vals2, series_name="Days"), height="420px")
            else:
                st.info("Not enough dated cat stays (after filters).")
    else:
        with col_dog2:
            st.info("Arrival/Departure dates not found.")
        with col_cat2:
            st.info("Arrival/Departure dates not found.")

    st.markdown("---")

    # ---------- Top 10 Breeds by Unique Pets (grouped by name first) — SUNBURST ----------
    st.subheader("Top 10 Breeds by Unique Pets")
    col_dog3, col_cat3 = st.columns(2)

    if breed_col:
        d_breeds, d_bvals = top_breeds_by_species(df, "Dog", name_col, breed_col, limit=10)
        c_breeds, c_bvals = top_breeds_by_species(df, "Cat", name_col, breed_col, limit=10)

        with col_dog3:
            if d_breeds:
                st_echarts(ec_sunburst(d_breeds, d_bvals, "Dogs"), height="460px")
            else:
                st.info("No dog breed data (after filters).")

        with col_cat3:
            if c_breeds:
                st_echarts(ec_sunburst(c_breeds, c_bvals, "Cats"), height="460px")
            else:
                st.info("No cat breed data (after filters).")
    else:
        with col_dog3:
            st.info("Breed column not found.")
        with col_cat3:
            st.info("Breed column not found.")


if __name__ == "__main__":
    main()
