# page_components/Kingdom_Stats.py
import os
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_echarts import st_echarts
from streamlit_echarts import st_echarts, JsCode

DATA_PATH = "data/combined.csv"

# ---------------- Helpers ----------------
def normalize_platform(val: str) -> str:
    if pd.isna(val): return "Other"
    s = str(val).strip().lower()
    # common aliases you might have
    if s in {"xhs", "小红书", "redbook", "little red book"}:
        return "XHS"
    if s in {"rover"}:
        return "Rover"
    return s.title()  # e.g., "Other"

def _clean_money_like(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
              .str.replace(r"[\$,]", "", regex=True)
              .str.strip()
              .replace({"": None})
              .pipe(pd.to_numeric, errors="coerce")
    )

def compute_box_data_by_species(df: pd.DataFrame):
    """
    Returns:
      {
        "Dog": {"Duration": [...], "Price": [...], "Daily Price": [...]},
        "Cat": {"Duration": [...], "Price": [...], "Daily Price": [...]},
      }
    Uses existing columns, excludes Type contains 'drop'.
    """
    svc_col   = get_service_col(df)
    dur_col   = get_first_existing(df, ["Duration", "Nights", "Days"])
    price_col = get_first_existing(df, ["Price", "Total Price", "Charge", "Amount"])
    daily_col = get_first_existing(df, ["daily price", "DailyPrice", "Rate", "Price/Day", "Price Per Day"])

    x = df.copy()
    if svc_col:
        x = x[~x[svc_col].astype(str).str.lower().str.contains("drop", na=False)].copy()

    out = {"Dog": {"Duration": [], "Price": [], "Daily Price": []},
           "Cat": {"Duration": [], "Price": [], "Daily Price": []}}

    for sp in ["Dog", "Cat"]:
        sub = x[x["__SpeciesNorm__"] == sp].copy()
        if dur_col and dur_col in sub:
            d = pd.to_numeric(sub[dur_col], errors="coerce")
            d = d[np.isfinite(d) & (d > 0)]                      # log-safe
            out[sp]["Duration"] = [float(v) for v in d.tolist()]
        if price_col and price_col in sub:
            p = _clean_money_like(sub[price_col])
            p = p[np.isfinite(p) & (p > 0)]                      # log-safe
            out[sp]["Price"] = [float(v) for v in p.tolist()]
        if daily_col and daily_col in sub:
            r = _clean_money_like(sub[daily_col])
            r = r[np.isfinite(r) & (r > 0)]                      # log-safe
            out[sp]["Daily Price"] = [float(v) for v in r.tolist()]
    return out


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


def _true_five_num(values, log_safe=True):
    """True five-number summary: min, Q1, median, Q3, max (no outlier capping)."""
    import numpy as np
    arr = []
    for v in values or []:
        try:
            f = float(v)
            if np.isfinite(f) and (f > 0 if log_safe else True):
                arr.append(f)
        except Exception:
            pass
    arr = np.asarray(arr, dtype=float)
    n = arr.size
    if n == 0:
        return None
    if n == 1:
        v = float(arr[0])
        return {"min": v, "q1": v, "med": v, "q3": v, "max": v, "n": 1}

    q1  = float(np.percentile(arr, 25))
    med = float(np.percentile(arr, 50))
    q3  = float(np.percentile(arr, 75))
    return {"min": float(arr.min()), "q1": q1, "med": med, "q3": q3, "max": float(arr.max()), "n": n}

def render_summary_table_2cats(dog_stats, cat_stats,
                               *, is_currency=False, unit="",
                               pad_left=56, pad_right=16,
                               dog_label="🐶 Dog", cat_label="🐱 Cat"):
    def fmt(v):
        if v is None: return "—"
        return f"${v:,.0f}" if is_currency else f"{v:,.0f}{(' ' + unit) if unit else ''}"
    def get(s, k): return fmt(s.get(k)) if s else "—"
    def get_n(s):  return (s or {}).get("n", 0)

    html = f"""
    <style>
    .ks-mini2 table, .ks-mini2 td, .ks-mini2 th {{ border: none; }}
    .ks-mini2 th {{ font-weight: 600; text-align: center; padding: 4px 6px; }}
    .ks-mini2 td {{ text-align: center; padding: 3px 8px; }}
    .ks-mini2 td.stat {{ font-weight: 600; opacity:.85; }}
    .ks-mini2 tr:nth-child(odd):not(.median) td {{ background: rgba(0,0,0,0.025); border-radius: 6px; }}
    .ks-mini2 tr.median td {{ font-weight: 700; }}
    </style>
    <div style="padding-left:{pad_left}px;padding-right:{pad_right}px;">
    <div class="ks-mini2">
    <table style="width:100%; border-collapse:separate; border-spacing:0 4px;">
    <colgroup>
    <col style="width:100px" />
    <col /><col />
    </colgroup>
    <thead>
    <tr>
    <th></th>
    <th>{dog_label}</th>
    <th>{cat_label}</th>
    </tr>
    </thead>
    <tbody>
    <tr><td class="stat">n</td>
    <td>{get_n(dog_stats)}</td>
    <td>{get_n(cat_stats)}</td></tr>
    <tr><td class="stat">min</td>
    <td>{get(dog_stats,"min")}</td>
    <td>{get(cat_stats,"min")}</td></tr>
    <tr><td class="stat">Q1</td>
    <td>{get(dog_stats,"q1")}</td>
    <td>{get(cat_stats,"q1")}</td></tr>
    <tr class="median"><td class="stat">median</td>
    <td>{get(dog_stats,"med")}</td>
    <td>{get(cat_stats,"med")}</td></tr>
    <tr><td class="stat">Q3</td>
    <td>{get(dog_stats,"q3")}</td>
    <td>{get(cat_stats,"q3")}</td></tr>
    <tr><td class="stat">max</td>
    <td>{get(dog_stats,"max")}</td>
    <td>{get(cat_stats,"max")}</td></tr>
    </tbody>
    </table>
    </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def ec_box_species_platform_4cats(
    title_text: str,
    rover_dog_vals, xhs_dog_vals,
    rover_cat_vals, xhs_cat_vals,
    *, is_currency=False, y_label="", log_scale=True
):
    import numpy as np

    def tukey_box_and_outliers(vals):
        arr = []
        for v in vals or []:
            try:
                f = float(v)
                if np.isfinite(f) and f > 0:
                    arr.append(f)
            except Exception:
                pass
        arr = np.asarray(arr, dtype=float)
        if arr.size == 0:
            return None, []
        if arr.size == 1:
            v = float(arr[0]); return [v, v, v, v, v], []
        q1 = float(np.percentile(arr, 25))
        q2 = float(np.percentile(arr, 50))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        low  = max(float(arr.min()), q1 - 1.5 * iqr)
        high = min(float(arr.max()), q3 + 1.5 * iqr)
        outs = arr[(arr < low) | (arr > high)].tolist()
        return [round(low,4), round(q1,4), round(q2,4), round(q3,4), round(high,4)], outs

    # Build in the same order as categories below
    boxes = []
    outs  = []
    vals_list = [
        ("Dog", "Rover", rover_dog_vals),
        ("Dog", "XHS",   xhs_dog_vals),
        ("Cat", "Rover", rover_cat_vals),
        ("Cat", "XHS",   xhs_cat_vals),
    ]
    counts = {}
    for i, (sp, plat, v) in enumerate(vals_list):
        b, o = tukey_box_and_outliers(v)
        boxes.append(b)
        outs += [[i, float(y)] for y in o]
        counts[(sp, plat)] = sum(1 for t in (v or []) if isinstance(t, (int, float)) and t > 0)

    categories = ["Dog", "Dog", "Cat", "Cat"]

    y_axis = {"type": "log", "logBase": 10, "axisLabel": {"margin": 4}} if log_scale else \
             {"type": "value", "min": 0, "axisLabel": {"margin": 4}}
    if is_currency:
        y_axis["axisLabel"]["formatter"] = "${value}"
    elif y_label:
        y_axis["axisLabel"]["formatter"] = "{value} " + y_label

    # Platform color mapping
    def color_for_cat(idx):
        return "#8b5e3c" if idx in (0, 2) else "#f4cbba"  # Rover for 0,2 ; XHS for 1,3

    # Per-item colors
    item_styles = [{"itemStyle": {"color": color_for_cat(i), "borderColor": "#5a3b2e", "borderWidth": 1.2}}
                   if boxes[i] else {}
                   for i in range(4)]

    option = {
        "title": {
            "text": (
                f"{title_text}  "

            ),
            "left": "center", "top": 8,
            "textStyle": {"fontSize": 12, "color": "#5a3b2e"}
        },
        "tooltip": {"show": False},
        "legend": {
            "show": True,
            "bottom": 0,
            "data": ["Rover", "XHS"],
            "textStyle": {"color": "#5a3b2e"}
        },
        "grid": {"left": 56, "right": 16, "top": 36, "bottom": 40, "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": categories,
            "axisTick": {"show": False},
            "axisLabel": {"margin": 6},
        },
        "yAxis": y_axis,
        "series": [
            {
                "name": "Boxes",
                "type": "boxplot",
                "data": [
                    {"value": boxes[i], **item_styles[i]} if boxes[i] else None
                    for i in range(4)
                ],
                "boxWidth": [16, 44],
                "z": 2,
            },
            # Dummy legend markers (no data) so legend shows platform colors
            {"name": "Rover", "type": "scatter", "data": [], "itemStyle": {"color": "#8b5e3c"}},
            {"name": "XHS",   "type": "scatter", "data": [], "itemStyle": {"color": "#f4cbba"}},
        ],
        "animationDuration": 900, "animationEasing": "cubicOut",
    }

    if outs:
        # Outliers align perfectly because their x matches the exact category index
        option["series"].append({
            "name": "Outliers",
            "type": "scatter",
            "data": outs,
            "symbolSize": 7,
            "itemStyle": {"color": "#5a3b2e"},
            "z": 3,
        })

    if not any(boxes):
        option["graphic"] = [{
            "type": "text", "left": "center", "top": "middle",
            "style": {"text": "No data", "fontSize": 12, "fill": "#8b5e3c"}
        }]
    return option

def render_summary_table_4cats(dr_stats, dx_stats, cr_stats, cx_stats,
                               *, is_currency=False, unit="",
                               pad_left=56, pad_right=16):
    def fmt(v):
        if v is None: return "—"
        return f"${v:,.0f}" if is_currency else f"{v:,.0f}{(' ' + unit) if unit else ''}"

    def get(s, key):   return fmt(s.get(key)) if s else "—"
    def get_n(s):      return (s or {}).get("n", 0)

    headers = ["🐶 Rover", "🐶 XHS", "🐱 Rover", "🐱 XHS"]

    html = f"""
    <style>
    .ks-mini table, .ks-mini td, .ks-mini th {{ border: none; }}
    .ks-mini th {{ font-weight: 600; text-align: center; padding: 4px 6px; }}
    .ks-mini td.stat {{ font-weight: 600; text-align: left; opacity:.85; padding: 3px 6px; }}
    .ks-mini td.val  {{ text-align: center; padding: 3px 8px; }}
    .ks-mini tr:nth-child(odd):not(.median) td.val {{ background: rgba(0,0,0,0.025); border-radius: 6px; }}
    .ks-mini tr.median td.val {{ font-weight: 700; }}
    </style>
    <div style="padding-left:{pad_left}px;padding-right:{pad_right}px;">
    <div class="ks-mini">
    <table style="width:100%; border-collapse:separate; border-spacing:0 4px;">
    <colgroup>
    <col style="width:100px" />
    <col /><col /><col /><col />
    </colgroup>
    <thead>
    <tr>
    <th></th>
    <th>{headers[0]}</th>
    <th>{headers[1]}</th>
    <th>{headers[2]}</th>
    <th>{headers[3]}</th>
    </tr>
    </thead>
    <tbody>
    <tr><td class="stat">n</td>
    <td class="val">{get_n(dr_stats)}</td>
    <td class="val">{get_n(dx_stats)}</td>
    <td class="val">{get_n(cr_stats)}</td>
    <td class="val">{get_n(cx_stats)}</td></tr>
    <tr><td class="stat">min</td>
    <td class="val">{get(dr_stats,"min")}</td>
    <td class="val">{get(dx_stats,"min")}</td>
    <td class="val">{get(cr_stats,"min")}</td>
    <td class="val">{get(cx_stats,"min")}</td></tr>
    <tr><td class="stat">Q1</td>
    <td class="val">{get(dr_stats,"q1")}</td>
    <td class="val">{get(dx_stats,"q1")}</td>
    <td class="val">{get(cr_stats,"q1")}</td>
    <td class="val">{get(cx_stats,"q1")}</td></tr>
    <tr class="median"><td class="stat">median</td>
    <td class="val">{get(dr_stats,"med")}</td>
    <td class="val">{get(dx_stats,"med")}</td>
    <td class="val">{get(cr_stats,"med")}</td>
    <td class="val">{get(cx_stats,"med")}</td></tr>
    <tr><td class="stat">Q3</td>
    <td class="val">{get(dr_stats,"q3")}</td>
    <td class="val">{get(dx_stats,"q3")}</td>
    <td class="val">{get(cr_stats,"q3")}</td>
    <td class="val">{get(cx_stats,"q3")}</td></tr>
    <tr><td class="stat">max</td>
    <td class="val">{get(dr_stats,"max")}</td>
    <td class="val">{get(dx_stats,"max")}</td>
    <td class="val">{get(cr_stats,"max")}</td>
    <td class="val">{get(cx_stats,"max")}</td></tr>
    </tbody>
    </table>
    </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
# ---------- Revisit / Loyalty Helpers ----------
def _arrival_col(df: pd.DataFrame):
    return get_first_existing(df, ["Arrival Date", "Arrival", "Check-in", "Check In", "Start Date"])

def prepare_visits_table(df: pd.DataFrame, name_col: str) -> pd.DataFrame:
    """
    Returns one row per visit with normalized keys:
      __name_norm__, __species__, __plat__, __arr__ (datetime), __visit_idx__ (per pet)
    Drop-Ins are excluded (boarding-focused loyalty).
    Shelter dogs are already excluded earlier in main().
    """
    arr = _arrival_col(df)
    plat = get_channel_col(df)
    svc = get_service_col(df)
    if not arr or not name_col:
        return pd.DataFrame()

    x = df.copy()
    x = coerce_dates(x)
    if svc:
        x = exclude_dropins(x)

    x["__name_norm__"] = safe_name_series(x[name_col])
    x["__species__"]   = x["__SpeciesNorm__"]
    x["__plat__"]      = x[plat].apply(normalize_platform) if plat else "Other"
    x["__arr__"]       = pd.to_datetime(x[arr], errors="coerce")
    x = x.dropna(subset=["__name_norm__", "__arr__"])
    x = x.sort_values(["__name_norm__", "__arr__"], kind="stable")

    # visit index per pet
    x["__visit_idx__"] = (
        x.groupby("__name_norm__")["__arr__"]
         .rank(method="first")
         .astype(int)
    )
    return x[["__name_norm__", "__species__", "__plat__", "__arr__", "__visit_idx__"]]

def compute_revisit_metrics(vis: pd.DataFrame):
    """
    Computes:
      - unique_pets, returning_pets, revisit_rate_pets
      - total_visits, returning_visits, share_visits_from_returning
      - first_to_second_days list, plus avg/median
      - species splits for (new vs returning) unique pets
    """
    if vis.empty:
        return None

    # Unique pets and returning flag
    counts = vis.groupby("__name_norm__").size()
    unique_pets = int(counts.shape[0])
    returning_pets = int((counts >= 2).sum())
    revisit_rate_pets = (returning_pets / unique_pets) if unique_pets else 0.0

    # Visits that are 2nd+ (returning visits share)
    total_visits = int(vis.shape[0])
    returning_visits = int((vis["__visit_idx__"] >= 2).sum())
    share_visits_from_returning = (returning_visits / total_visits) if total_visits else 0.0

    # First-to-second visit gap per pet
    second_rows = (
        vis[vis["__visit_idx__"] == 2]
          .set_index("__name_norm__")[["__arr__"]]
          .rename(columns={"__arr__": "__arr2__"})
    )
    first_rows = (
        vis[vis["__visit_idx__"] == 1]
          .set_index("__name_norm__")[["__arr__", "__species__", "__plat__"]]
          .rename(columns={"__arr__": "__arr1__"})
    )
    merged = first_rows.join(second_rows, how="inner")
    gaps_days = (merged["__arr2__"] - merged["__arr1__"]).dt.days.dropna().astype(int)
    gap_list = gaps_days.tolist()
    avg_gap = float(np.mean(gap_list)) if len(gap_list) else float("nan")
    med_gap = float(np.median(gap_list)) if len(gap_list) else float("nan")

    # Species split (unique pets grouped as New vs Returning)
    # Map each pet -> species by first row
    pet_species = vis.sort_values("__arr__").groupby("__name_norm__").first()["__species__"]
    pet_is_returning = (counts >= 2)
    species_new = pet_species[~pet_is_returning].value_counts()
    species_ret = pet_species[ pet_is_returning].value_counts()
    species = ["Dog", "Cat"]
    species_new_counts = [int(species_new.get(s, 0)) for s in species]
    species_ret_counts = [int(species_ret.get(s, 0)) for s in species]

    return {
        "unique_pets": unique_pets,
        "returning_pets": returning_pets,
        "revisit_rate_pets": revisit_rate_pets,
        "total_visits": total_visits,
        "returning_visits": returning_visits,
        "share_visits_from_returning": share_visits_from_returning,
        "gap_list": gap_list,
        "avg_gap": avg_gap,
        "med_gap": med_gap,
        "species": species,
        "species_new_counts": species_new_counts,
        "species_ret_counts": species_ret_counts,
    }

def _bin_time_to_return(days_list):
    """
    Buckets for first->second visit gap.
    """
    bins = [(0,14), (15,30), (31,60), (61,120), (121,365), (366, 10_000)]
    labels = ["0–14", "15–30", "31–60", "61–120", "121–365", "366+"]
    counts = [0]*len(bins)
    for d in days_list or []:
        for i,(lo,hi) in enumerate(bins):
            if lo <= d <= hi:
                counts[i] += 1
                break
    return labels, counts

def ec_donut_new_vs_return(new_count: int, ret_count: int, title="Unique Pets"):
    data = [{"name":"New (1 visit)","value":int(new_count)},
            {"name":"Returning (≥2)","value":int(ret_count)}]
    return {
        "tooltip":{"trigger":"item","formatter":"{b}: {c} ({d}%)"},
        "legend":{"show":False},
        "title":{
            "text": f"{new_count + ret_count}",
            "subtext": title, "left":"center", "top":"38%",
            "textStyle":{"fontSize":28,"fontWeight":"bold","color":"#5a3b2e"},
            "subtextStyle":{"fontSize":14,"color":"#5a3b2e"},
        },
        "color":["#f4cbba","#8b5e3c"],
        "series":[{
            "type":"pie","radius":["35%","80%"],"center":["50%","45%"],
            "itemStyle":{"borderRadius":8,"borderColor":"#fff","borderWidth":2},
            "label":{"show":True,"formatter":"{b}: {c}"},
            "data": data
        }]
    }

def ec_stacked_species_new_vs_return(species, new_counts, ret_counts, title="Revisit by Species"):
    return {
        "title":{"text":title,"left":"center","top":0,
                 "textStyle":{"fontSize":14,"color":"#5a3b2e"}},
        "tooltip":{"trigger":"axis","axisPointer":{"type":"shadow"}},
        "legend":{"bottom":0,"data":["New (1 visit)","Returning (≥2)"]},
        "grid":{"left":56,"right":16,"top":40,"bottom":40,"containLabel":True},
        "xAxis":{"type":"category","data":species},
        "yAxis":{"type":"value"},
        "series":[
            {"name":"New (1 visit)","type":"bar","stack":"total","data":new_counts,
             "itemStyle":{"color":"#f4cbba","borderRadius":[10,10,0,0]}},
            {"name":"Returning (≥2)","type":"bar","stack":"total","data":ret_counts,
             "itemStyle":{"color":"#8b5e3c","borderRadius":[10,10,0,0]}},
        ]
    }

def ec_hist_time_to_return(labels, counts, title="Days to 2nd Visit"):
    return {
        "title":{"text":title,"left":"center","top":0,
                 "textStyle":{"fontSize":14,"color":"#5a3b2e"}},
        "tooltip":{"trigger":"axis"},
        "grid":{"left":56,"right":16,"top":40,"bottom":40,"containLabel":True},
        "xAxis":{"type":"category","data":labels},
        "yAxis":{"type":"value"},
        "series":[{"type":"bar","data":counts,"barWidth":28,
                   "itemStyle":{"color":{"type":"linear","x":0,"y":0,"x2":0,"y2":1,
                     "colorStops":[{"offset":0,"color":"#8b5e3c"},
                                   {"offset":1,"color":"#f4cbba"}]},
                     "borderRadius":[10,10,0,0]},
                   "label":{"show":True,"position":"top","formatter":"{c}"}}]
    }

def _pick_customer_key(df: pd.DataFrame) -> str:
    owner_like = get_first_existing(df, ["Owner", "Client", "Customer", "Guardian", "User", "Buyer"])
    if owner_like: return owner_like
    pet_like = get_first_existing(df, ["Pet", "PetName", "Name", "Pet Name"])
    return pet_like or df.columns[0]

def _pick_arr_dep_cols(df: pd.DataFrame):
    arr = get_first_existing(df, [
        "Arrival", "Check-in", "CheckIn", "Start", "StartDate", "Arrive", "Arrival Date", "Drop-off", "DropOff"
    ])
    dep = get_first_existing(df, [
        "Departure", "Check-out", "CheckOut", "End", "EndDate", "Pickup", "PickUp", "Departure Date"
    ])
    return arr, dep

def _parse_dates_safe(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=False)

def _rfm_quantile_scores(series: pd.Series, higher_is_better=True, bins=5) -> pd.Series:
    s = series.copy()
    if not s.notna().any():
        return pd.Series([3]*len(s), index=s.index, dtype=int)
    s = s.fillna(s.median())
    pct = s.rank(pct=True, method="average")
    score = (pct * bins).apply(np.ceil).astype(int) if higher_is_better else ((1 - pct) * bins).apply(np.ceil).astype(int)
    return score.clip(1, bins)

def _days_between(a: pd.Timestamp, b: pd.Timestamp) -> float:
    if pd.isna(a) and pd.isna(b): return np.nan
    if pd.isna(a): a = b
    if pd.isna(b): b = a
    d = (b.normalize() - a.normalize()).days
    return max(float(d), 1.0)  # at least 1 day to avoid divide-by-zero

def build_premium_clients_rfmD(df: pd.DataFrame, title="💎 Premium Clients · RFM + Daily Price (Pet-level)"):
    """
    Premium clients analysis using R/F/M + D (Avg Daily Price).
    Client key = normalized pet name + " | " + species, to match the 'Unique Pets' section.
    """
    st.subheader(title)

    if df is None or df.empty:
        st.info("No data available for RFM analysis.")
        return

    # ---- THEME ----
    COL_TEXT   = "#5a3b2e"
    COL_DARK   = "#8b5e3c"
    COL_MID    = "#c8a18f"
    COL_PEACH  = "#f1b69d"
    COL_BG     = "#ffeada"
    COL_BRONZE = "#f6d2c3" 
    # ---- weights UI ----
    with st.expander("⚙️ Scoring Weights (R/F/M/D)", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        wR = c1.slider("R weight (Recency, closer is better)", 0.0, 3.0, 1.0, 0.1)
        wF = c2.slider("F weight (Frequency)",                 0.0, 3.0, 1.0, 0.1)
        wM = c3.slider("M weight (Monetary)",                  0.0, 3.0, 1.0, 0.1)
        wD = c4.slider("D weight (Avg Daily Price)",           0.0, 3.0, 1.0, 0.1)
        st.caption("D (Avg Daily Price) = Total Money ÷ Total Days (each visit min 1 day).")

    # ---- column picks (PET + SPECIES = client key) ----
    pet_name_col = get_first_existing(df, ["Name", "Pet Name", "Pet"])
    species_col  = "__SpeciesNorm__"  # you create this earlier in main()
    arr_col, dep_col = _pick_arr_dep_cols(df)
    price_col = get_first_existing(df, ["Price", "Total", "Amount", "Revenue"])
    tips_col  = get_first_existing(df, ["Tips", "Tip", "Gratuity"])

    if not pet_name_col or species_col not in df.columns:
        st.warning("Missing pet name/species columns for consistent client counting.")
        return
    if not arr_col and not dep_col:
        st.warning("Arrival/Departure date columns not found. Please check your column names.")
        return

    x = df.copy()

    # ---- normalize money ----
    if price_col: x[price_col] = _clean_money_like(x[price_col])
    if tips_col:  x[tips_col]  = _clean_money_like(x[tips_col])
    money_cols = [c for c in [price_col, tips_col] if c]
    x["__Money"] = x[money_cols].sum(axis=1, min_count=1) if money_cols else 0.0

    # ---- normalize dates ----
    if arr_col: x[arr_col] = _parse_dates_safe(x[arr_col])
    if dep_col: x[dep_col] = _parse_dates_safe(x[dep_col])

    # ---- composite PET-LEVEL client key (matches Unique Pets) ----
    x["__pet_norm__"] = safe_name_series(x[pet_name_col])         # lower/trim + dropna
    x["__species__"]  = x[species_col]
    x = x.dropna(subset=["__pet_norm__", "__species__"])           # remove nameless/speciesless rows
    x["__client_key__"] = x["__pet_norm__"] + " | " + x["__species__"]

    # ---- visit key uses the composite key + visit dates ----
    if arr_col and dep_col:
        visit_key = ["__client_key__", arr_col, dep_col]
    else:
        only_date_col = arr_col or dep_col
        visit_key = ["__client_key__", only_date_col]

    # ---- aggregate per visit ----
    per_visit = (
        x.groupby(visit_key, dropna=False, as_index=False)
         .agg(
             Money=("__Money", "sum"),
             Arr=(arr_col, "max") if arr_col else (dep_col, "max"),
             Dep=(dep_col, "max") if dep_col else (arr_col, "max"),
         )
    )

    # duration & daily price per visit
    per_visit["DurationDays"] = per_visit.apply(lambda r: _days_between(r["Arr"], r["Dep"]), axis=1)
    per_visit["DailyPrice_visit"] = per_visit["Money"] / per_visit["DurationDays"]

    # anchor for Recency
    anchor_date = per_visit[["Arr", "Dep"]].max(axis=1, skipna=True).max()
    if pd.isna(anchor_date):
        anchor_date = pd.Timestamp(pd.Timestamp.today())

    # ---- R/F/M + D per composite client ----
    per_visit["EndLike"] = per_visit["Dep"].fillna(per_visit["Arr"])
    rfm = (
        per_visit.sort_values("EndLike")
                 .groupby("__client_key__", dropna=True)
                 .agg(
                     RecencyDays=("EndLike", lambda s: (anchor_date - s.max()).days if s.max() is not pd.NaT else np.nan),
                     Frequency=("Money", "count"),
                     Monetary=("Money", "sum"),
                     TotalDays=("DurationDays", "sum"),
                     LastVisit=("EndLike", "max")
                 )
                 .reset_index()
    )

    # true weighted Avg Daily Price
    rfm["AvgDailyPrice"] = rfm.apply(
        lambda r: (r["Monetary"] / r["TotalDays"]) if (pd.notna(r["TotalDays"]) and r["TotalDays"] > 0) else np.nan,
        axis=1
    )

    # ---- scores 1..5 ----
    rfm["R_Score"] = _rfm_quantile_scores(rfm["RecencyDays"], higher_is_better=False, bins=5)
    rfm["F_Score"] = _rfm_quantile_scores(rfm["Frequency"],    higher_is_better=True,  bins=5)
    rfm["M_Score"] = _rfm_quantile_scores(rfm["Monetary"],     higher_is_better=True,  bins=5)
    rfm["D_Score"] = _rfm_quantile_scores(rfm["AvgDailyPrice"],higher_is_better=True,  bins=5)

    # weighted total; classic RFM if wD=0
    rfm["RFM_Total"] = (wR * rfm["R_Score"] +
                        wF * rfm["F_Score"] +
                        wM * rfm["M_Score"] +
                        wD * rfm["D_Score"])

    # ---- segments
    def _segment(row):
        denom = (wR + wF + wM + wD) if (wR + wF + wM + wD) > 0 else 1.0
        base = row.RFM_Total
        if base >= denom*3.2 and row.F_Score >= 4 and row.M_Score >= 4:
            return "VIP"
        if base >= denom*2.6:
            return "Gold"
        if base >= denom*2.0:
            return "Silver"
        return "Bronze"
    rfm["Segment"] = rfm.apply(_segment, axis=1)

    # ---- split key for readability
    key_split = rfm["__client_key__"].str.split(" | ", n=1, expand=True)
    if isinstance(key_split, pd.DataFrame) and key_split.shape[1] == 2:
        rfm["PetName_norm"] = key_split[0]
        rfm["Species"]      = key_split[1]
        rfm["PetName"]      = rfm["PetName_norm"].str.title()
    else:
        rfm["PetName"] = rfm["__client_key__"]
        rfm["Species"] = ""

    # ---- summary cards (white cards, full-width grid, extra bottom space) ----
    total_clients = rfm["__client_key__"].nunique(dropna=True)
    vip_cnt = int((rfm["Segment"] == "VIP").sum())
    gold_cnt = int((rfm["Segment"] == "Gold").sum())
    vip_rev = float(rfm.loc[rfm["Segment"] == "VIP", "Monetary"].sum())
    total_rev = float(rfm["Monetary"].sum())
    vip_share = (vip_rev / total_rev) if total_rev > 0 else 0.0

    vip_adp  = float(rfm.loc[rfm["Segment"] == "VIP", "AvgDailyPrice"].mean())
    non_adp  = float(rfm.loc[rfm["Segment"] != "VIP", "AvgDailyPrice"].mean())

    st.markdown(f"""
    <div class="ks-kpi" style="width:100%; margin-bottom: 36px;">
    <style>
        .ks-kpi .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 22px;
        align-items: stretch;
        }}
        .ks-kpi .card {{
        background: #ffffff;                 /* white background */
        border: 1px solid {COL_MID};
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(90,59,46,0.12);
        padding: 24px 26px;
        color: {COL_TEXT};
        min-height: 128px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        }}
        .ks-kpi .label {{
        font-size: 15px;
        opacity: .9;
        letter-spacing: .2px;
        }}
        .ks-kpi .value {{
        font-size: 42px;
        font-weight: 800;
        line-height: 1.1;
        margin-top: 8px;
        }}
        @media (min-width: 1200px) {{
        .ks-kpi .card {{ padding: 28px 30px; min-height: 140px; }}
        .ks-kpi .value {{ font-size: 46px; }}
        }}
    </style>

    <div class="grid">
        <div class="card">
        <div class="label">Total Clients (pets)</div>
        <div class="value">{total_clients}</div>
        </div>
        <div class="card">
        <div class="label">VIP Count</div>
        <div class="value">{vip_cnt}</div>
        </div>
        <div class="card">
        <div class="label">Gold Count</div>
        <div class="value">{gold_cnt}</div>
        </div>
        <div class="card">
        <div class="label">VIP Revenue Share</div>
        <div class="value">{vip_share:.1%}</div>
        </div>
        <div class="card">
        <div class="label">VIP Avg Daily Price</div>
        <div class="value">{vip_adp:.2f}</div>
        </div>
        <div class="card">
        <div class="label">Non-VIP Avg Daily Price</div>
        <div class="value">{non_adp:.2f}</div>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Optional: add an explicit spacer if you want *even more* separation
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


    # ---- pie: segment composition (theme colors)
    seg_counts = rfm["Segment"].value_counts().reindex(["VIP","Gold","Silver","Bronze"]).fillna(0).astype(int)
    pie_data = [{"name": seg, "value": int(cnt)} for seg, cnt in seg_counts.items()]
    pie_opt = {
        "color": [COL_DARK, COL_MID, COL_PEACH, COL_BRONZE],
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center", "textStyle": {"color": COL_TEXT}},
        "series": [{
            "name": "Segment",
            "type": "pie",
            "radius": ["36%", "60%"],
            "avoidLabelOverlap": True,
            "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": True, "formatter": "{b}: {d}%"},
            "data": pie_data
        }]
    }

    c1, c2 = st.columns([1,2])
    with c1:
        st_echarts(pie_opt, height="400px")

    # ---- bar: Top 10 VIP by Total Spend — top spender appears at the TOP
    top_vip = (
        rfm[rfm["Segment"] == "VIP"]
        .sort_values(["Monetary", "Frequency", "AvgDailyPrice"], ascending=[False, False, False])
        .head(10)
    )
    if not top_vip.empty:
        # Build lists (descending), then reverse to ascending so inverse y-axis puts max at TOP
        names_desc  = top_vip["PetName"].tolist()
        spend_desc  = top_vip["Monetary"].round(2).astype(float).tolist()
        visits_desc = top_vip["Frequency"].astype(int).tolist()

        bar_names  = names_desc[::1]    # ascending order
        spend_vals = spend_desc[::1]
        visit_vals = visits_desc[::1]

        bar_opt = {
            "color": [COL_DARK, COL_PEACH],  # second series is invisible, used for tooltip
            "title": {
                "text": "Top 10 VIP by Total Spend",
                "left": "center", "top": 0,
                "textStyle": {"color": COL_TEXT, "fontSize": 14}
            },
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": 140, "right": 20, "bottom": 60, "top": 40, "containLabel": True},
            "xAxis": {"type": "value", "axisLabel": {"color": COL_TEXT}},
            "yAxis": {
                "type": "category",
                "data": bar_names,
                "inverse": True,                 # <— key: largest will be at the TOP now
                "axisLabel": {"color": COL_TEXT}
            },
            "series": [
                {
                    "type": "bar",
                    "name": "Total Spend",
                    "data": spend_vals,
                    "barWidth": 15,
                    "itemStyle": {
                        "borderRadius": [12, 12, 12, 12],
                        "color": {
                            "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": COL_DARK},
                                {"offset": 1, "color": COL_MID}
                            ]
                        },
                        "shadowBlur": 8,
                        "shadowColor": "rgba(90,59,46,0.15)"
                    },
                    "label": {"show": True, "position": "right", "color": COL_TEXT}
                },
                {
                    # Invisible series so tooltip shows Visits without drawing another bar
                    "type": "bar",
                    "name": "Visits",
                    "data": visit_vals,
                    "barWidth": 15,
                    "barGap": "-100%",
                    "itemStyle": {"opacity": 0.0, "borderRadius": [12, 12, 12, 12]},
                    "emphasis": {"disabled": True},
                    "label": {"show": False},
                },
            ]
        }
        with c2:
            st_echarts(bar_opt, height="400px")
        st.caption("Sorted by Total Spend. Largest spender is at the top; tooltip includes Visits.")
    else:
        with c2:
            st.info("No VIP clients to display yet.")


    # ---- details table — Only VIP & Gold; scores only
    order = pd.CategoricalDtype(categories=["VIP","Gold","Silver","Bronze"], ordered=True)
    rfm["Segment"] = rfm["Segment"].astype(order)

    show_cols = ["PetName","Species","Segment","RFM_Total","R_Score","F_Score","M_Score","D_Score"]

    rfm_top = rfm[rfm["Segment"].isin(["VIP","Gold"])]

    st.markdown("**Details — VIP & Gold (scores only)**")
    if rfm_top.empty:
        st.info("No VIP or Gold clients to display yet.")
    else:
        st.dataframe(
            rfm_top[show_cols].sort_values(["Segment","RFM_Total"], ascending=[True, False]),
            use_container_width=True
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
    build_premium_clients_rfmD(df, title="Top Clients by Visit Frequency & Spending")
        
    st.markdown("---")

    # ---------- Boarding Price & Duration Distributions (log scale, shared axes) ----------
    st.subheader("Boarding Price & Duration Distributions (log scale)")

    # one row, three even charts
    c1, gap, c3 = st.columns([1,0.1, 1]) 

    # --- Duration (days) ---
    # discover columns once up here (reuse your earlier logic if you prefer)
    dur_col   = get_first_existing(df, ["Duration", "Nights", "Days"])
    rate_col  = get_first_existing(df, ["daily price", "DailyPrice", "Rate", "Price/Day", "Price Per Day"])
    plat_col  = get_channel_col(df)

    # --- Duration (days) split by Platform ---
    with c1:
        if dur_col and plat_col:
            x = df[[dur_col, plat_col, "__SpeciesNorm__"]].copy()
            x[dur_col] = pd.to_numeric(x[dur_col], errors="coerce")
            x = x[np.isfinite(x[dur_col]) & (x[dur_col] > 0)]
            x["__plat__"] = x[plat_col].apply(normalize_platform)

            rover_dog = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Dog"), dur_col].astype(float).tolist()
            xhs_dog   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Dog"), dur_col].astype(float).tolist()
            rover_cat = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Cat"), dur_col].astype(float).tolist()
            xhs_cat   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Cat"), dur_col].astype(float).tolist()

            st_echarts(
                ec_box_species_platform_4cats("Duration (days)",
                                            rover_dog, xhs_dog, rover_cat, xhs_cat,
                                            is_currency=False, y_label="days", log_scale=True),
                height="320px"
            )

            dr_stats = _true_five_num(rover_dog or [], log_safe=True)  # Dog–Rover
            dx_stats = _true_five_num(xhs_dog   or [], log_safe=True)  # Dog–XHS
            cr_stats = _true_five_num(rover_cat or [], log_safe=True)  # Cat–Rover
            cx_stats = _true_five_num(xhs_cat   or [], log_safe=True)  # Cat–XHS
            render_summary_table_4cats(dr_stats, dx_stats, cr_stats, cx_stats,
                                    is_currency=False, unit="days",
                                    pad_left=56, pad_right=16)


    
    # --- Daily price split by Platform ---
    with c3:
        if rate_col and plat_col:
            x = df[[rate_col, plat_col, "__SpeciesNorm__"]].copy()
            x[rate_col] = _clean_money_like(x[rate_col])
            x = x[np.isfinite(x[rate_col]) & (x[rate_col] > 0)]
            x["__plat__"] = x[plat_col].apply(normalize_platform)

            rover_dog = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Dog"), rate_col].astype(float).tolist()
            xhs_dog   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Dog"), rate_col].astype(float).tolist()
            rover_cat = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Cat"), rate_col].astype(float).tolist()
            xhs_cat   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Cat"), rate_col].astype(float).tolist()

            st_echarts(
                ec_box_species_platform_4cats("Daily price",
                                            rover_dog, xhs_dog, rover_cat, xhs_cat,
                                            is_currency=True, log_scale=True),
                height="320px"
            )

            dr_stats = _true_five_num(rover_dog or [], log_safe=True)
            dx_stats = _true_five_num(xhs_dog   or [], log_safe=True)
            cr_stats = _true_five_num(rover_cat or [], log_safe=True)
            cx_stats = _true_five_num(xhs_cat   or [], log_safe=True)
            render_summary_table_4cats(dr_stats, dx_stats, cr_stats, cx_stats,
                                    is_currency=True,
                                    pad_left=56, pad_right=16)

    st.markdown("---")

    # ---------- Revisit & Loyalty ----------
    st.subheader("Revisit & Loyalty")
    st.caption("Excludes Drop in pets")

    vis = prepare_visits_table(df, name_col)
    if vis.empty:
        st.info("Not enough dated visits to compute revisit metrics.")
    else:
        met = compute_revisit_metrics(vis)

        # KPIs / story
        new_count = met["unique_pets"] - met["returning_pets"]
        ret_count = met["returning_pets"]
        revisit_pct = f"{met['revisit_rate_pets']*100:,.1f}%"
        returning_visit_share = f"{met['share_visits_from_returning']*100:,.1f}%"

        c1, c2, c3 = st.columns([1,1,1])

        with c1:
            st.markdown("**Unique Pets: New vs Returning**")
            st_echarts(ec_donut_new_vs_return(new_count, ret_count, title="Unique Pets"), height="360px")

        with c2:
            st.markdown("**By Species: New vs Returning (unique pets)**")
            st_echarts(
                ec_stacked_species_new_vs_return(
                    met["species"],
                    met["species_new_counts"],
                    met["species_ret_counts"],
                    title="Revisit by Species"
                ),
                height="360px"
            )

        with c3:
            labels, counts = _bin_time_to_return(met["gap_list"])
            st.markdown("**How Fast Do They Return? (1st → 2nd visit)**")
            st_echarts(ec_hist_time_to_return(labels, counts, title="Days to 2nd Visit"), height="360px")

        # Narrative summary (auto)
        avg_gap_txt = "—" if np.isnan(met["avg_gap"]) else f"{met['avg_gap']:.1f} days"
        med_gap_txt = "—" if np.isnan(met["med_gap"]) else f"{met['med_gap']:.0f} days"
        dog_new, cat_new = met["species_new_counts"]
        dog_ret, cat_ret = met["species_ret_counts"]

        st.markdown(
            f"""
**What this tells us**

- **Revisit rate (unique pets):** {revisit_pct} — {ret_count} of {met['unique_pets']} pets have stayed at least twice.  
- **Share of visits from loyal customers:** {returning_visit_share} — {met['returning_visits']} of {met['total_visits']} total visits are from returning pets.  
- **Time to come back:** median **{med_gap_txt}** (avg {avg_gap_txt}).  
- **Species view:** Dogs returning **{dog_ret}** vs new **{dog_new}**; Cats returning **{cat_ret}** vs new **{cat_new}**.
            """
        )

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
