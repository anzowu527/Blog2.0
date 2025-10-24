# page_components/Kingdom_Stats.py
import os
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_echarts import st_echarts
from streamlit_echarts import st_echarts, JsCode
from topia_common import render_topia_title

DATA_PATH = "data/combined.csv"

# ---- S3-only avatar helpers (.webp) + circular text placeholder ----
try:
    from image_config import BASE_IMAGE_URL
    from get_s3_images import _safe_join_url, _placeholder_for
except Exception:
    BASE_IMAGE_URL = ""
    def _safe_join_url(a, b): return f"{a.rstrip('/')}/{b.lstrip('/')}"
    def _placeholder_for(name: str) -> str:
        return "data:image/gif;base64,R0lGODlhAQABAAAAACwAAAAAAQABAAA="

import unicodedata, base64, hashlib
from functools import lru_cache
from io import BytesIO

try:
    import requests
    from PIL import Image, ImageOps, ImageDraw, ImageFont
except Exception:
    requests = None
    Image = None
    ImageFont = None

AVATAR_ROOT = "images/avatar/"  # s3://.../images/avatar/<lowercased-NFC-name>.webp

def _norm_lower_nfc(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "")).strip().lower()

def _avatar_s3_key_for_pet(pet_name: str) -> str:
    return f"{AVATAR_ROOT}{_norm_lower_nfc(pet_name)}.webp"

def _s3_url_for_key(key: str) -> str:
    return _safe_join_url(BASE_IMAGE_URL, key)

@lru_cache(maxsize=4096)
def _fetch_s3_bytes(url: str, timeout=6) -> bytes:
    if not url or not requests:
        return b""
    try:
        r = requests.get(url, timeout=timeout)
        if r.ok:
            return r.content
    except Exception:
        pass
    return b""

def _circle_crop_png_bytes(img_bytes: bytes) -> bytes:
    if not Image or not img_bytes:
        return b""
    try:
        im = Image.open(BytesIO(img_bytes)).convert("RGBA")
        size = min(im.width, im.height)
        im = ImageOps.fit(im, (size, size), centering=(0.5, 0.5))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        im.putalpha(mask)
        out = BytesIO()
        im.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return b""

def _hash_color(name: str) -> tuple[int,int,int]:
    """Stable pastel-ish bg color from name."""
    h = hashlib.sha1((_norm_lower_nfc(name) or "pet").encode("utf-8")).digest()
    # keep it pleasant: high lightness
    r, g, b = h[0], h[1], h[2]
    return int(180 + r % 60), int(160 + g % 70), int(150 + b % 80)

def _best_font(size: int = 64):
    """Try a Unicode font (for CJK); fall back to default."""
    if not ImageFont:
        return None
    # common fonts that often exist in many envs
    for fn in ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(fn, size=size)
        except Exception:
            pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def _make_circle_text_png_bytes(name: str, size: int = 256) -> bytes:
    """Create a circular PNG with name centered. Works even if we can't load a TTF."""
    if not Image:
        return b""
    try:
        bg = _hash_color(name or "pet")
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        # draw filled circle
        draw = ImageDraw.Draw(im)
        draw.ellipse((0, 0, size, size), fill=bg + (255,))

        # choose text to draw: try full name, else initials fallback
        text = (name or "Pet").strip()
        if not text:
            text = "Pet"

        # pick font & auto-shrink to fit
        # start large and shrink until it fits inside 80% width
        max_box = int(size * 0.8)
        font_size = int(size * 0.38)  # initial guess
        font = _best_font(font_size)
        if font:
            while font_size > 10:
                bbox = ImageDraw.Draw(im).textbbox((0,0), text, font=font, anchor="lt")
                tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                if tw <= max_box and th <= max_box:
                    break
                font_size = int(font_size * 0.9)
                font = _best_font(font_size)
        # center the text
        if font:
            bbox = draw.textbbox((0,0), text, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            x = (size - tw) // 2
            y = (size - th) // 2
            # subtle shadow for legibility
            shadow = (0,0,0,80)
            draw.text((x+1, y+1), text, font=font, fill=shadow)
            draw.text((x, y), text, font=font, fill=(255,255,255,230))

        out = BytesIO()
        im.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return b""
@st.cache_data(show_spinner=False, ttl=24*3600, max_entries=4096)
def circle_avatar_or_placeholder_data_uri(pet_name: str) -> str:
    """Return a circular PNG data URI for this pet (S3 or generated).
       Cached for 24h to avoid refetching every rerun."""
    key = _avatar_s3_key_for_pet(pet_name)
    url = _s3_url_for_key(key)
    raw = _fetch_s3_bytes(url)  # already lru_cached (good)
    if raw:
        circ = _circle_crop_png_bytes(raw)
        if circ:
            b64 = base64.b64encode(circ).decode("ascii")
            return f"data:image/png;base64,{b64}"

    # fallback: generated circle with name
    ph = _make_circle_text_png_bytes(pet_name or "Pet", size=256)
    if ph:
        b64 = base64.b64encode(ph).decode("ascii")
        return f"data:image/png;base64,{b64}"

    # ultimate fallback: 1x1 transparent
    return "data:image/gif;base64,R0lGODlhAQABAAAAACwAAAAAAQABAAA="

def _data_version_from_path(path: str) -> int:
    try:
        return int(os.path.getmtime(path))
    except Exception:
        return 0

@st.cache_data(show_spinner=False)
def build_top_breeds_and_matched_avatars_cached(
    species: str,
    df_slice: pd.DataFrame,       # only the columns we need
    name_col: str,
    breed_col: str,
    limit: int,
    data_version: int,
):
    """Cached wrapper. Recomputes only when data_version changes."""
    reps = representative_breed_per_pet(
        df_slice[df_slice["__SpeciesNorm__"] == species], name_col, breed_col
    )
    if reps.empty:
        return [], [], {}

    vc = reps["__breed_rep__"].value_counts()
    top_items = vc.head(limit)
    breed_names  = top_items.index.tolist()
    breed_counts = top_items.values.astype(int).tolist()

    # normalized key -> display name
    name_map = (
        df_slice[[name_col]]
        .assign(__name_norm__=safe_name_series(df_slice[name_col]))
        .dropna(subset=["__name_norm__"])
        .drop_duplicates("__name_norm__")
        .set_index("__name_norm__")[name_col]
        .to_dict()
    )

    avatars_by_breed = {}
    for breed in breed_names:
        pet_keys = (
            reps.loc[reps["__breed_rep__"] == breed, "__name_norm__"]
                .dropna().unique().tolist()
        )
        items = []
        for key in pet_keys:
            display_name = name_map.get(key, key)
            data_uri = circle_avatar_or_placeholder_data_uri(str(display_name))  # ← cached
            items.append({"img": data_uri, "label": str(display_name)})
        avatars_by_breed[breed] = items

    return breed_names, breed_counts, avatars_by_breed

# ---------- Data builder: top 10 breeds + matched avatars that exist ----------
def build_top_breeds_and_matched_avatars(
    df: pd.DataFrame, species: str, name_col: str, breed_col: str, limit: int = 10
):
    reps = representative_breed_per_pet(df[df["__SpeciesNorm__"] == species], name_col, breed_col)
    if reps.empty:
        return [], [], {}

    vc = reps["__breed_rep__"].value_counts()
    top_items = vc.head(limit)
    breed_names  = top_items.index.tolist()
    breed_counts = top_items.values.astype(int).tolist()

    # normalized key -> display name
    name_map = (
        df[[name_col]]
        .assign(__name_norm__=safe_name_series(df[name_col]))
        .dropna(subset=["__name_norm__"])
        .drop_duplicates("__name_norm__")
        .set_index("__name_norm__")[name_col]
        .to_dict()
    )

    avatars_by_breed = {}
    for breed in breed_names:
        pet_keys = (
            reps.loc[reps["__breed_rep__"] == breed, "__name_norm__"]
                .dropna().unique().tolist()
        )
        items = []
        for key in pet_keys:
            display_name = name_map.get(key, key)
            url = _s3_url_for_key(_avatar_s3_key_for_pet(display_name))
            raw = _fetch_s3_bytes(url, timeout=6)

            if raw:
                img_bytes = _circle_crop_png_bytes(raw)
            else:
                img_bytes = _make_circle_text_png_bytes(display_name, size=256)

            if img_bytes:
                data_uri = "data:image/png;base64," + base64.b64encode(img_bytes).decode("ascii")
                items.append({"img": data_uri, "label": str(display_name)})

        avatars_by_breed[breed] = items
    return breed_names, breed_counts, avatars_by_breed


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
            "axisLabel": {"interval": 0, "rotate": 0},
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

    /* phone: pull wrapper to the left, reduce font a bit, left-align labels */
    @media (max-width: 720px){{
      .ks-wrap {{ padding-left: 8px !important; padding-right: 8px !important; }}
      .ks-mini2 td.stat {{ text-align: left; padding-left: 2px; }}
      .ks-mini2 th, .ks-mini2 td {{ font-size: 12px; }}
      .ks-mini2 table {{ margin-left: 0 !important; width: 100% !important; table-layout: fixed; }}
    }}
    </style>

    <div class="ks-wrap" style="padding-left:{pad_left}px;padding-right:{pad_right}px;">
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
            <tr><td class="stat">n</td><td>{get_n(dog_stats)}</td><td>{get_n(cat_stats)}</td></tr>
            <tr><td class="stat">min</td><td>{get(dog_stats,"min")}</td><td>{get(cat_stats,"min")}</td></tr>
            <tr><td class="stat">Q1</td><td>{get(dog_stats,"q1")}</td><td>{get(cat_stats,"q1")}</td></tr>
            <tr class="median"><td class="stat">median</td><td>{get(dog_stats,"med")}</td><td>{get(cat_stats,"med")}</td></tr>
            <tr><td class="stat">Q3</td><td>{get(dog_stats,"q3")}</td><td>{get(cat_stats,"q3")}</td></tr>
            <tr><td class="stat">max</td><td>{get(dog_stats,"max")}</td><td>{get(cat_stats,"max")}</td></tr>
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

    # Only set border color (dark brown). Keep fill default.
    BROWN = "#5a3b2e"
    item_styles = [{"itemStyle": {"borderColor": BROWN, "borderWidth": 1.8}}
                   if boxes[i] else {}
                   for i in range(4)]

    option = {
        "title": {
            "text": f"{title_text}",
            "left": "center", "top": 8,
            "textStyle": {"fontSize": 12, "color": BROWN}
        },
        "tooltip": {"show": False},
        "legend": {
            "show": True,
            "bottom": 0,
            "data": ["Rover", "XHS"],
            "textStyle": {"color": BROWN}
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
                "itemStyle": {"borderColor": BROWN, "borderWidth": 1.8},
                "emphasis": {"itemStyle": {"borderColor": BROWN, "borderWidth": 2.2}},
                "z": 2,
            },
            # Keep your legend color chips (no data)
            {"name": "Rover", "type": "scatter", "data": [], "itemStyle": {"color": "#8b5e3c"}},
            {"name": "XHS",   "type": "scatter", "data": [], "itemStyle": {"color": "#f4cbba"}},
        ],
        "animationDuration": 900, "animationEasing": "cubicOut",
    }

    # Keep outliers (unchanged)
    if outs:
        option["series"].append({
            "name": "Outliers",
            "type": "scatter",
            "data": outs,
            "symbolSize": 7,
            "itemStyle": {"color": BROWN},
            "z": 3,
        })

    if not any(boxes):
        option["graphic"] = [{
            "type": "text", "left": "center", "top": "middle",
            "style": {"text": "No data", "fontSize": 12, "fill": BROWN}
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

    @media (max-width: 720px){{
      .ks-wrap {{ padding-left: 8px !important; padding-right: 8px !important; }}
      .ks-mini th, .ks-mini td {{ font-size: 12px; }}
      .ks-mini table {{ margin-left: 0 !important; width: 100% !important; table-layout: fixed; }}
      .ks-mini td.stat {{ padding-left: 2px; }}
    }}
    </style>

    <div class="ks-wrap" style="padding-left:{pad_left}px;padding-right:{pad_right}px;">
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

def make_responsive(option: dict, mobile_option: dict, max_width: int = 720) -> dict:
    """
    Wrap a normal ECharts option so that when the chart container width is <= max_width,
    ECharts applies `mobile_option` overrides automatically.
    """
    return {
        "baseOption": option,
        "media": [
            {
                "query": {"maxWidth": max_width},
                "option": mobile_option
            }
        ]
    }


st.markdown("""
<style>
@media (max-width: 720px){
  /* kill page/container padding */
  .block-container { padding-left: 1 !important; padding-right: 1 !important; }
  /* kill column inner padding */
  [data-testid="column"] > div:first-child { padding-left: 0 !important; padding-right: 0 !important; }
  /* optional: reduce caption & subheader side spacing */
  [data-testid="stMarkdown"] { padding-left: 8px; padding-right: 8px; }
}
</style>
""", unsafe_allow_html=True)

def echarts_scroll_container_start(min_width_px: int = 1100):
    # Horizontal scroll container with a wide inner div
    st.markdown(
        f"""
        <div style="overflow-x:auto; -webkit-overflow-scrolling:touch;">
          <div style="min-width:{min_width_px}px;">
        """,
        unsafe_allow_html=True
    )

def echarts_scroll_container_end():
    st.markdown("</div></div>", unsafe_allow_html=True)

def ec_bar_vertical_with_inline_avatars_fullheight(
    names, values, avatars_by_breed, title_text="",
    dot_size=32, y_pad=1.2, y_step=1.0, y_offset=0.4
):
    """
    Vertical version of the avatar chart — each breed as a vertical bar
    with avatars stacked upwards.
    """
    import numpy as np

    order = np.argsort(values)[::-1]
    names_ord  = [names[i] for i in order]
    values_ord = [int(values[i]) for i in order]

    x_labels = names_ord
    bar_vals = values_ord

    # Prepare scatter image points (avatars)
    mp_data_img = []
    max_needed_y = 0
    for breed, count in zip(x_labels, bar_vals):
        items = avatars_by_breed.get(breed, [])
        n = len(items)
        max_needed_y = max(max_needed_y, int((n - 1) * y_step + y_offset + 0.5))
        for i in range(n):
            y_pos = i * y_step + y_offset
            mp_data_img.append({
                "name": items[i].get("label", ""),
                "coord": [breed, y_pos],
                "symbol": f"image://{items[i]['img']}",
                "symbolKeepAspect": True,
                "label": {"show": False},
                "z": 3,
            })

    y_max = max(max(bar_vals) if bar_vals else 0, max_needed_y) + y_pad * 1.2 

    return {
        "title": {"text": title_text, "left": "center", "top": 2,
                  "textStyle": {"fontSize": 16, "color": "#5a3b2e", "fontWeight": "600"}},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 40, "right": 24, "top": 46, "bottom": 60, "containLabel": True},
        "xAxis": {"type": "category", "data": x_labels, "axisLabel": {"rotate": 30, "margin": 8}},
        "yAxis": {"type": "value", "min": 0, "max": y_max, "axisLabel": {"margin": 4}},
        "series": [{
            "type": "bar",
            "data": bar_vals,
            "barWidth": 44,
            "label": {"show": True, "position": "top", "formatter": "{c}"},
            "itemStyle": {
                "borderRadius": [10, 10, 0, 0],
                "shadowBlur": 10,
                "shadowColor": "rgba(90,59,46,0.18)",
                "color": {
                    "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": "#8b5e3c"},
                        {"offset": 1, "color": "#f4cbba"},
                    ],
                },
            },
            "markPoint": {
                "symbol": "circle",
                "symbolSize": dot_size,
                "data": mp_data_img,
                "animation": True,
                "tooltip": {"show": True, "formatter": "{b}"},
            },
            "animationDuration": 900,
            "animationEasing": "cubicOut",
        }]
    }

# ---------------- Main ----------------
def main():
    # --- responsive helpers (local to main for easy paste) ---
    def make_responsive(option: dict, mobile_option: dict, max_width: int = 720) -> dict:
        """Merge mobile overrides when chart container width <= max_width."""
        return {
            "baseOption": option,
            "media": [{"query": {"maxWidth": max_width}, "option": mobile_option}],
        }

    MOBILE_DONUT = {
        "title": {
            "top": "42%",
            "textStyle": {"fontSize": 20},
            "subtextStyle": {"fontSize": 12},
        },
        "series": [{
            "radius": ["38%", "72%"],
            "center": ["50%", "48%"],
            "label": {"fontSize": 10}
        }],
        # keep small global padding
        "grid": {"top": 8, "right": 8, "bottom": 12, "left": 8}
    }

    MOBILE_CARTESIAN = {
        "title": {"top": 0, "textStyle": {"fontSize": 12}},
        "grid": {"left": 8, "right": 8, "top": 24, "bottom": 24, "containLabel": True},
        "xAxis": {"axisLabel": {"fontSize": 10, "rotate": 0, "margin": 4}},  # ← no rotate
        "yAxis": {"axisLabel": {"fontSize": 10, "margin": 4}},
        # NOTE: no "series" override here → preserves your original boxplot colors/borders/widths
    }

    MOBILE_BAR = {
        "title": {"textStyle": {"fontSize": 12}},
        "grid": {"left": 8, "right": 8, "top": 24, "bottom": 24, "containLabel": True},
        "xAxis": {"axisLabel": {"fontSize": 10, "rotate": 0, "margin": 4}},  # ← no rotate
        "yAxis": {"axisLabel": {"fontSize": 10, "margin": 4}},
        "series": [{"barWidth": 40, "label": {"fontSize": 10}}],  # safe tweak, no color change
    }
    # NEW — mobile override tailored for the vertical avatar bar
    def MOBILE_AVATAR_VERT():
        return {
            "title": {"textStyle": {"fontSize": 12}},
            # extra bottom room so long labels don’t clip; still compact overall
            "grid": {"left": 8, "right": 8, "top": 24, "bottom": 88, "containLabel": True},
            "xAxis": {
                # show ALL labels; keep them readable; allow multi-line wraps if needed
                "axisLabel": {
                    "fontSize": 10, "rotate": 90, "interval": 0, "margin": 6,
                    "width": 90, "overflow": "break"  # wrap to 2–3 lines when necessary
                }
            },
            "yAxis": {
                "axisLabel": {"fontSize": 12, "margin": 6},
                "min": 0,
                "max": "dataMax",           # <- scale just to the tallest bar
                "boundaryGap": [0, 0.15],   # <- 15% headroom above bars
            },
            # make bars skinnier + smaller avatar dots + smaller value labels
            "series": [{
                "barWidth": 25,
                "label": {"fontSize": 10},
                "markPoint": {"symbolSize": 23},
                "itemStyle": {
                    "borderRadius": [20, 20, 0, 0],   # ← round top-left/top-right corners
                    "shadowBlur": 10,
                    "shadowColor": "rgba(90,59,46,0.18)",
                },
            }],
            # enable touch scroll/zoom on the x-axis (swipe left/right on mobile)
            "dataZoom": [{"type": "inside", "xAxisIndex": [0]}],
        }
    
    # NEW — laptop override for the vertical avatar bar (>= 1024px)
    def LAPTOP_AVATAR_VERT():
        return {
            "title": {"textStyle": {"fontSize": 14}},
            "grid": {"left": 40, "right": 24, "top": 46, "bottom": 70, "containLabel": True},
            "xAxis": {
                
                "axisLabel": {
                    "fontSize": 12, "rotate": 0, "interval": 0, "margin": 10,
                    "width": 110, "overflow": "truncate"
                }
            },
            "yAxis": {
                "axisLabel": {"fontSize": 12, "margin": 6},
                "min": 0,
                "max": "dataMax",           # <- scale just to the tallest bar
                "boundaryGap": [0, 0.15],   # <- 15% headroom above bars
            },
            "series": [{
                # keep bars comfortable on laptop, slightly thicker than mobile
                "barWidth": 40,
                "label": {"fontSize": 12},
                # BIGGER AVATARS on laptop:
                "markPoint": {"symbolSize": 33},   # ← bump this to taste (e.g., 44)
                "itemStyle": {
                    "borderRadius": [20, 20, 0, 0],   # ← round top-left/top-right corners
                    "shadowBlur": 10,
                    "shadowColor": "rgba(90,59,46,0.18)",
                },
            }]
        }
    # NEW — responsive wrapper: apply mobile (<=720px) and laptop (>=1024px) overrides
    def make_responsive_avatar(option: dict) -> dict:
        return {
            "baseOption": option,
            "media": [
                {"query": {"maxWidth": 720},  "option": MOBILE_AVATAR_VERT()},
                {"query": {"minWidth": 1024}, "option": LAPTOP_AVATAR_VERT()},
            ]
        }

    # chart height presets (feel free to tweak)
    H_DONUT = "320px"
    H_BOX   = "300px"
    H_BAR   = "300px"

    # --- top spacing / title ---
    render_topia_title("svc-title", "📈 Kingdom Statistics")
    st.caption("Excludes shelter dogs & probably need to wait a bit for the page to fully rendered")

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

    # Global filter: exclude shelter dogs
    df = exclude_shelter_dogs(df, "__SpeciesNorm__")

    # Unique counts by species (dedupe by name)
    names_series = safe_name_series(df[name_col])
    dog_names = names_series[df["__SpeciesNorm__"] == "Dog"].unique()
    cat_names = names_series[df["__SpeciesNorm__"] == "Cat"].unique()
    dogs = len(dog_names); cats = len(cat_names); total = dogs + cats

    # ---- Unique Pets + Total Visits donuts ----
    st.subheader("Unique Pets & Total Visits")
    left, right = st.columns(2)

    with left:
        st.markdown("**Unique Pets**")
        st_echarts(
            make_responsive(ec_donut(total, dogs, cats, subtitle="Unique"), MOBILE_DONUT),
            height=H_DONUT,
            renderer="svg",
        )

    with right:
        st.markdown("**Total Visits**")
        svc_col = get_service_col(df)
        if svc_col:
            svc = df[svc_col].astype(str).str.lower()
            is_drop = svc.apply(is_dropin_service)
        else:
            is_drop = pd.Series(False, index=df.index)

        is_dog = (df["__SpeciesNorm__"] == "Dog")
        is_cat = (df["__SpeciesNorm__"] == "Cat")

        dog_board = int((is_dog & ~is_drop).sum())
        dog_drop  = int((is_dog &  is_drop).sum())
        cat_board = int((is_cat & ~is_drop).sum())
        cat_drop  = int((is_cat &  is_drop).sum())
        visits_total = dog_board + dog_drop + cat_board + cat_drop

        st_echarts(
            make_responsive(
                ec_donut_visits_split(
                    visits_total, dog_board, dog_drop, cat_board, cat_drop, subtitle="Visits"
                ),
                MOBILE_DONUT,
            ),
            height=H_DONUT,
            renderer="svg",
        )

    st.markdown("---")

    # ---------- Boarding Price & Duration Distributions ----------
    st.subheader("Boarding Price & Duration Distributions (log scale)")
    df = exclude_dropins(df)

    c1, _, c3 = st.columns([1, 0.1, 1])

    dur_col   = get_first_existing(df, ["Duration", "Nights", "Days"])
    rate_col  = get_first_existing(df, ["daily price", "DailyPrice", "Rate", "Price/Day", "Price Per Day"])
    plat_col  = get_channel_col(df)

    # Duration (days) split by Platform
    with c1:
        if dur_col and plat_col:
            x = df[[dur_col, plat_col, "__SpeciesNorm__"]].copy()
            x = exclude_dropins(x)
            x[dur_col] = pd.to_numeric(x[dur_col], errors="coerce")
            x = x[np.isfinite(x[dur_col]) & (x[dur_col] > 0)]
            x["__plat__"] = x[plat_col].apply(normalize_platform)

            rover_dog = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Dog"), dur_col].astype(float).tolist()
            xhs_dog   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Dog"), dur_col].astype(float).tolist()
            rover_cat = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Cat"), dur_col].astype(float).tolist()
            xhs_cat   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Cat"), dur_col].astype(float).tolist()

            st_echarts(
                make_responsive(
                    ec_box_species_platform_4cats(
                        "Duration (days) — Boarding only",
                        rover_dog, xhs_dog, rover_cat, xhs_cat,
                        is_currency=False, y_label="days", log_scale=True
                    ),
                    MOBILE_CARTESIAN,
                ),
                height=H_BOX,
                renderer="svg",
            )

            dr_stats = _true_five_num(rover_dog or [], log_safe=True)
            dx_stats = _true_five_num(xhs_dog   or [], log_safe=True)
            cr_stats = _true_five_num(rover_cat or [], log_safe=True)
            cx_stats = _true_five_num(xhs_cat   or [], log_safe=True)
            render_summary_table_4cats(
                dr_stats, dx_stats, cr_stats, cx_stats,
                is_currency=False, unit="days", pad_left=56, pad_right=16
            )

    # Daily price split by Platform
    with c3:
        if rate_col and plat_col:
            x = df[[rate_col, plat_col, "__SpeciesNorm__"]].copy()
            x = exclude_dropins(x)
            x[rate_col] = _clean_money_like(x[rate_col])
            x = x[np.isfinite(x[rate_col]) & (x[rate_col] > 0)]
            x["__plat__"] = x[plat_col].apply(normalize_platform)

            rover_dog = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Dog"), rate_col].astype(float).tolist()
            xhs_dog   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Dog"), rate_col].astype(float).tolist()
            rover_cat = x.loc[(x["__plat__"] == "Rover") & (x["__SpeciesNorm__"] == "Cat"), rate_col].astype(float).tolist()
            xhs_cat   = x.loc[(x["__plat__"] == "XHS")   & (x["__SpeciesNorm__"] == "Cat"), rate_col].astype(float).tolist()

            st_echarts(
                make_responsive(
                    ec_box_species_platform_4cats(
                        "Daily price — Boarding only",
                        rover_dog, xhs_dog, rover_cat, xhs_cat,
                        is_currency=True, log_scale=True
                    ),
                    MOBILE_CARTESIAN,
                ),
                height=H_BOX,
                renderer="svg",
            )

            dr_stats = _true_five_num(rover_dog or [], log_safe=True)
            dx_stats = _true_five_num(xhs_dog   or [], log_safe=True)
            cr_stats = _true_five_num(rover_cat or [], log_safe=True)
            cx_stats = _true_five_num(xhs_cat   or [], log_safe=True)
            render_summary_table_4cats(
                dr_stats, dx_stats, cr_stats, cx_stats,
                is_currency=True, pad_left=56, pad_right=16
            )

    st.markdown("---")

    # ---------- Revisit & Loyalty ----------
    st.subheader("Revisit & Loyalty")
    st.caption("Excludes Drop in pets")

    vis = prepare_visits_table(df, name_col)
    if vis.empty:
        st.info("Not enough dated visits to compute revisit metrics.")
    else:
        met = compute_revisit_metrics(vis)

        new_count = met["unique_pets"] - met["returning_pets"]
        ret_count = met["returning_pets"]
        revisit_pct = f"{met['revisit_rate_pets']*100:,.1f}%"
        returning_visit_share = f"{met['share_visits_from_returning']*100:,.1f}%"

        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            st.markdown("**Unique Pets: New vs Returning**")
            st_echarts(
                make_responsive(
                    ec_donut_new_vs_return(new_count, ret_count, title="Unique Pets"),
                    MOBILE_DONUT
                ),
                height=H_DONUT,
                renderer="svg",
            )

        with c2:
            st.markdown("**By Species: New vs Returning (unique pets)**")
            st_echarts(
                make_responsive(
                    ec_stacked_species_new_vs_return(
                        met["species"],
                        met["species_new_counts"],
                        met["species_ret_counts"],
                        title="Revisit by Species"
                    ),
                    MOBILE_BAR
                ),
                height=H_BAR,
                renderer="svg",
            )

        with c3:
            labels, counts = _bin_time_to_return(met["gap_list"])
            st.markdown("**How Fast Do They Return? (1st → 2nd visit)**")
            st_echarts(
                make_responsive(
                    ec_hist_time_to_return(labels, counts, title="Days to 2nd Visit"),
                    MOBILE_BAR
                ),
                height=H_BAR,
                renderer="svg",
            )

        # Narrative summary
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

    # --- Top 10 Popular Breeds ---
    st.subheader("Top 10 Popular Breeds")

    breed_col = get_first_existing(df, ["Breed", "Breeds", "Dog Breed", "Cat Breed"])
    if not breed_col:
        st.info("No breed data.")
        return

    # Create a slim slice with only columns we need (st.cache_data hashes inputs)
    df_breeds = df[[name_col, breed_col, "__SpeciesNorm__"]].copy()
    data_ver = _data_version_from_path(DATA_PATH)

    # Use the cached builder (computes once per data version)
    d_names, d_vals, d_avatars = build_top_breeds_and_matched_avatars_cached(
        "Dog", df_breeds, name_col, breed_col, limit=10, data_version=data_ver
    )
    c_names, c_vals, c_avatars = build_top_breeds_and_matched_avatars_cached(
        "Cat", df_breeds, name_col, breed_col, limit=10, data_version=data_ver
    )

    # ---- Dogs ----
    if d_names:
        st.markdown("#### 🐶 Dogs")
        per_bar_px = 84
        min_w = max(720, len(d_names) * per_bar_px + 120)
        echarts_scroll_container_start(min_w)
        st_echarts(
            make_responsive_avatar(
                ec_bar_vertical_with_inline_avatars_fullheight(
                    d_names, d_vals, d_avatars,
                    title_text="Dogs · Popular Breeds (Unique Pets)",
                )
            ),
            height="600px", renderer="svg",
        )
        echarts_scroll_container_end()
    else:
        st.info("No dog breed data (after filters).")

    # ---- Cats ----
    if c_names:
        st.markdown("#### 🐱 Cats")
        per_bar_px = 84
        min_w = max(720, len(c_names) * per_bar_px + 120)
        echarts_scroll_container_start(min_w)
        st_echarts(
            make_responsive_avatar(
                ec_bar_vertical_with_inline_avatars_fullheight(
                    c_names, c_vals, c_avatars,
                    title_text="Cats · Popular Breeds (Unique Pets)",
                )
            ),
            height="600px", renderer="svg",
        )
        echarts_scroll_container_end()
    else:
        st.info("No cat breed data (after filters).")



if __name__ == "__main__":
    main()
