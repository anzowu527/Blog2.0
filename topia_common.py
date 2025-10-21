# page_components/topia_common.py
from __future__ import annotations
import uuid
import unicodedata
from typing import Dict, List, Iterable, Tuple

import streamlit as st
import pandas as pd

from image_config import BASE_IMAGE_URL
# Use the **public** helpers (avoid underscored imports)
from get_s3_images import get_index, pick_cover_key, _safe_join_url, _placeholder_for


# ---------- small utilities ----------
def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").lower().strip()

def _ensure_columns(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df

def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_columns(df, ["Name", "Breed", "Sex", "Species", "Platform"])
    df["Name"]    = df["Name"].astype(str).str.strip()
    df["Breed"]   = df["Breed"].astype(str).str.strip()
    df["Sex"]     = df["Sex"].astype(str).str.title().str.strip()
    df["Species"] = df["Species"].astype(str).str.title().str.strip()
    df["Platform"]= df["Platform"].astype(str).str.lower().str.strip()
    return df

# replace the old helper
def _aggregate_visits(df: pd.DataFrame, species: str | None, platforms: Tuple[str, ...]) -> pd.DataFrame:
    subset = df[df["Platform"].isin(platforms)]
    if species:  # only filter by species if provided
        subset = subset[subset["Species"] == species.title()]
    return (
        subset.groupby("Name", dropna=False)
        .agg({
            "Breed": "first",
            "Sex": "first",
            "Species": "first",
            "Platform": "first",
            "Name": "count",
        })
        .rename(columns={"Name": "Visits"})
        .reset_index()
    )


def _build_pets(stats: pd.DataFrame, idx: Dict[str, List[str]], route_param: str) -> List[dict]:
    idx_lower = {_norm(k): v for k, v in idx.items()}
    pets: List[dict] = []

    for _, row in stats.iterrows():
        name = str(row["Name"]).strip()
        if not name:
            continue

        keys_for_entity = idx_lower.get(_norm(name), [])
        cover_key = pick_cover_key(keys_for_entity, name_hint=name)

        if cover_key:
            img_url = _safe_join_url(BASE_IMAGE_URL, cover_key)
        else:
            img_url = _placeholder_for(name)

        pets.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "breed": row.get("Breed", ""),
            "gender": row.get("Sex", ""),
            "visits": int(row.get("Visits", 0)),
            "species": row.get("Species", ""),
            "platform": row.get("Platform", ""),
            "image": img_url,
            "route": f"/?page={route_param}&{route_param}={name}",
        })
    return pets


# ---------- UI (CSS + Gallery) ----------
def render_topia_title(css_class: str, title_text: str):
    st.markdown(f"""
    <style>
      .{css_class} {{
        color:#5a3b2e; text-align:center; margin-top:10px;
        font-size:42px !important; line-height:1.2;
      }}
      @media (max-width: 768px) {{
        .{css_class}{{ font-size:30px !important; }}
      }}
      @media (max-width: 640px) {{
        .{css_class}{{ font-size:24px !important; }}
      }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"<h1 class='{css_class}'>{title_text}</h1>", unsafe_allow_html=True)

def render_gallery(pets: List[dict], route_param: str):
    cards_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Special+Elite&display=swap');
    body, .gallery, .card, .overlay, .view-button { font-family: 'Special+Elite', serif !important; }

    .gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 30px;
        padding: 20px;
        max-width: 100%;
        margin: 0 auto;
        justify-content: center;
    }
    @media (max-width: 640px) {
      .gallery {
          grid-template-columns: repeat(2, 1fr) !important;
          gap: 16px;
          padding: 12px;
      }
      .overlay h2 { font-size: 16px; }
      .overlay p  { font-size: 12px; }
      .view-button { font-size: 12px; padding: 7px 10px; }
    }

    .card {
        aspect-ratio: 2 / 3;
        width: 100%;
        border-radius: 12px;
        overflow: hidden;
        cursor: pointer;
        transition: transform 0.25s ease;
        position: relative;
        background: #c8a18f;
        box-shadow: 0 8px 18px rgba(0,0,0,0.15);
    }
    .card:hover { transform: scale(1.03); }
    .card img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .overlay {
        position: absolute; inset: 0;
        background: linear-gradient(to top, rgba(0,0,0,0.55) 30%, rgba(0,0,0,0.1) 70%);
        color: white; opacity: 0; transition: opacity 0.3s ease;
        padding: 20px 15px; display:flex; flex-direction:column; justify-content:flex-end;
    }
    .card:hover .overlay { opacity: 1; }
    .overlay * { transform: translateY(30px); opacity: 0; transition: all 0.35s ease; }
    .card:hover .overlay * { transform: translateY(0); opacity: 1; }
    .overlay h2 { margin: 0 0 10px 0; font-size: 20px; }
    .overlay p  { font-size: 13px; margin: 0; }

    .view-button {
        display: inline-block; margin-top: 12px; padding: 10px 14px; font-size: 14px; font-weight: 700;
        color: #ffffff !important; background-color: #c8a18f; border: none; border-radius: 10px;
        text-decoration: none !important; box-shadow: 0 6px 12px rgba(0,0,0,0.18);
        transition: transform 0.12s ease, background-color 0.2s ease, box-shadow 0.2s ease;
    }
    .view-button:hover { background-color: #a56f5c; box-shadow: 0 10px 18px rgba(0,0,0,0.24); transform: translateY(-1px); }
    .view-button:active { transform: translateY(0); box-shadow: 0 6px 12px rgba(0,0,0,0.18); }
    </style>
    <script>
      const APP_BASE = (window.top?.location ?? window.location).origin
                     + (window.top?.location ?? window.location).pathname;
      function goEntity(name) {
          return APP_BASE + `?page=${encodeURIComponent('%ROUTE%')}&${encodeURIComponent('%ROUTE%')}=` + encodeURIComponent(name);
      }
    </script>
    """.replace("%ROUTE%", route_param)

    cards_html += '<div class="gallery">'
    for pet in pets:
        name = pet["name"]
        img_src = pet["image"]
        cards_html += f"""
        <div class="card" onclick="window.open(goEntity('{name}'), '_blank')">
          <img src="{img_src}" alt="{name}" />
          <div class="overlay">
            <h2>{name}</h2>
            <p><strong>Breed:</strong> {pet.get('breed','')}<br/>
               <strong>Gender:</strong> {pet.get('gender','')}<br/>
               <strong>Visit(s):</strong> {pet.get('visits',0)}</p>
            <a class="view-button"
               href="javascript:void(0)"
               onclick="event.stopPropagation(); window.open(goEntity('{name}'), '_blank');">
               View Story →
            </a>
          </div>
        </div>
        """
    cards_html += "</div>"

    st.components.v1.html(
        f"""<div style="height:96vh; overflow-y:auto; overflow-x:hidden; margin-top:4vh;">{cards_html}</div>""",
        height=1200,
        scrolling=False,
    )


# ---------- One-call topia page ----------
def render_topia_page(
    *,
    data_path: str,
    bucket: str,
    root_prefix: str,     # e.g., "images/catopia/" or "images/dogtopia/"
    species: str,         # "Cat" / "Dog" / etc.
    route_param: str,     # "cat" / "dog" / etc.
    title_text: str,      # "🐱 Welcome to Catopia"
    title_css_class: str, # "catopia-title"
    platforms: Tuple[str, ...] = ("xhs", "rover","shelter"),
):
    render_topia_title(title_css_class, title_text)

    # Data
    df = pd.read_csv(data_path)
    df = _sanitize(df)
    stats = _aggregate_visits(df, species=species, platforms=platforms)

    # S3 index (cached)
    idx = get_index(bucket, root_prefix)

    # Cards
    pets = _build_pets(stats, idx, route_param=route_param)

    # Gallery
    render_gallery(pets, route_param=route_param)
