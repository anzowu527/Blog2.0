# page_components/Catopia.py
import streamlit as st
import pandas as pd
import uuid
import base64
from streamlit.components.v1 import html
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import Optional

DATA_PATH = "data/combined.csv"

# ---------------- Helpers ----------------
def encode_image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def _first_matching_webp(folder: str, prefix: str = "a") -> Optional[str]:
    """Pick the first webp like a1.webp..a10.webp if present."""
    for i in range(1, 11):
        c = os.path.join(folder, f"{prefix}{i}.webp")
        if os.path.exists(c):
            return c
    return None

def _any_webp_in_folder(folder: str) -> Optional[str]:
    try:
        for fn in sorted(os.listdir(folder)):
            if fn.lower().endswith(".webp"):
                return os.path.join(folder, fn)
    except FileNotFoundError:
        pass
    return None

def _cat_folder_candidates(name: str):
    """
    Try a few likely folder casings; adjust if your repo uses a different path.
    """
    return [
        os.path.join("images", "catopia", str(name)),
        os.path.join("images", "Catopia", str(name)),
       
    ]

def cat_image_or_placeholder(name: str) -> str:
    """
    Return base64 of the cat's card image.
    Rule: use .../<CatName>/{lower_case_cat_name}1.webp
    Fallbacks: a1.webp -> {Name}1.webp -> any a*.webp -> any .webp -> placeholder.
    ALWAYS returns a base64 string.
    """
    lc = str(name).lower()
    img_path = None

    for folder in _cat_folder_candidates(name):
        if not os.path.isdir(folder):
            continue

        primary   = os.path.join(folder, f"{lc}1.webp")
        alt_a1    = os.path.join(folder, "a1.webp")
        alt_name1 = os.path.join(folder, f"{name}1.webp")

        for candidate in (primary, alt_a1, alt_name1, _first_matching_webp(folder), _any_webp_in_folder(folder)):
            if candidate and os.path.exists(candidate):
                img_path = candidate
                break
        if img_path:
            break

    if img_path:
        return encode_image_to_base64(img_path)

    # Placeholder with initials
    initials = "".join([p[0].upper() for p in str(name).split() if p])[:2] or "C"
    size = (340, 500)
    bg = (200, 161, 143)   # #c8a18f
    txt = (255, 234, 218)  # #ffeada
    im = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=120)
    except Exception:
        font = ImageFont.load_default()
    w, h = draw.textbbox((0, 0), initials, font=font)[2:]
    draw.text(((size[0]-w)/2, (size[1]-h)/2), initials, fill=txt, font=font)
    buf = BytesIO()
    im.save(buf, format="WEBP", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

# ---------------- Main ----------------
def main():
    # --- Global responsive title CSS ---
    st.markdown("""
    <style>
      .catopia-title{
        color:#5a3b2e; text-align:center; margin-top:10px;
        font-size:42px !important; line-height:1.2;
      }
      /* tablets */
      @media (max-width: 768px){
        .catopia-title{ font-size:30px !important; }
      }
      /* phones (match gallery breakpoint) */
      @media (max-width: 640px){
        .catopia-title{ font-size:24px !important; }
      }
    </style>
    """, unsafe_allow_html=True)

    # Title
    st.markdown("<h1 class='catopia-title'>🐱 Welcome to Catopia</h1>", unsafe_allow_html=True)

    # Load & sanitize
    df = pd.read_csv(DATA_PATH)
    for col in ["Name", "Breed", "Sex", "Species", "Platform"]:
        if col not in df.columns:
            df[col] = ""
    df["Name"] = df["Name"].astype(str).str.strip()
    df["Breed"] = df["Breed"].astype(str).str.strip()
    df["Sex"] = df["Sex"].astype(str).str.title().str.strip()
    df["Species"] = df["Species"].astype(str).str.title().str.strip()
    df["Platform"] = df["Platform"].astype(str).str.lower().str.strip()

    # Only cats from selected platforms
    cats = df[(df["Species"] == "Cat") & (df["Platform"].isin(["xhs", "rover"]))]

    cat_stats = (
        cats.groupby("Name", dropna=False)
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

    # Build card data
    pets = []
    for _, row in cat_stats.iterrows():
        name = str(row["Name"]).strip()
        if not name:
            continue
        img_b64 = cat_image_or_placeholder(name)
        pets.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "breed": row["Breed"],
            "gender": row["Sex"],
            "visits": int(row["Visits"]),
            "species": row["Species"],
            "platform": row["Platform"],
            "image": img_b64,
            "route": f"/?page=cat&cat={name}",
        })

    # Gallery HTML (button style + top-level navigation)
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

    /* 🔒 Force exactly 2 columns on phones */
    @media (max-width: 640px) {
    .gallery {
        grid-template-columns: repeat(2, 1fr) !important;  /* two columns */
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
    function catUrl(name) {
        return APP_BASE + "?page=cat&cat=" + encodeURIComponent(name);
    }
    </script>

    <div class="gallery">
    """

    for pet in pets:
        safe_img = pet.get("image") or cat_image_or_placeholder(pet.get("name", "Cat"))
        name = pet.get("name", "Cat")

        cards_html += f"""
        <div class="card" onclick="window.open(catUrl('{name}'), '_blank')">
          <img src="data:image/webp;base64,{safe_img}" alt="{name}" />
          <div class="overlay">
            <h2>{name}</h2>
            <p><strong>Breed:</strong> {pet.get('breed','')}<br/>
            <strong>Gender:</strong> {pet.get('gender','')}<br/>
            <strong>Visit(s):</strong> {pet.get('visits',0)}</p>

            <!-- Open in a new tab reliably from inside the iframe -->
            <a class="view-button"
               href="javascript:void(0)"
               onclick="event.stopPropagation(); window.open(catUrl('{name}'), '_blank');">
               View Story →
            </a>
          </div>
        </div>
        """

    cards_html += "</div>"

    html(f"""
    <div style="height:96vh; overflow-y:auto; overflow-x:hidden; margin-top:4vh;">
        {cards_html}
    </div>
    """, height=1200, scrolling=False)

if __name__ == "__main__":
    main()
