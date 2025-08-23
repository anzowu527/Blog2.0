import streamlit as st
import pandas as pd
import uuid
import base64
from streamlit.components.v1 import html
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

DATA_PATH = "data/combined.csv"

# ---------------- Helpers ----------------
def encode_image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def cat_image_or_placeholder(name: str) -> str:
    """
    Return base64 of the cat's image if found,
    otherwise generate placeholder with initials.
    """
    img_path = os.path.join("images", "Zoolotopia", "Catopia", f"{name}1.webp")
    if os.path.exists(img_path):
        return encode_image_to_base64(img_path)

    # Generate placeholder with initials
    initials = "".join([part[0].upper() for part in str(name).split() if part])[:2] or "C"
    size = (340, 500)
    bg = (200, 161, 143)   # warm brown (#c8a18f)
    txt = (255, 234, 218)  # peach (#ffeada)

    im = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(im)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=120)
    except:
        font = ImageFont.load_default()

    w, h = draw.textbbox((0, 0), initials, font=font)[2:]
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2),
              initials, fill=txt, font=font)

    buf = BytesIO()
    im.save(buf, format="WEBP", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

# ---------------- Main ----------------
def main():
    st.set_page_config(page_title="Zoolotopia · Catopia", layout="wide")


    df = pd.read_csv(DATA_PATH)
    for col in ["Name", "Breed", "Sex", "Species", "Platform"]:
        if col not in df.columns:
            df[col] = ""
    df["Name"] = df["Name"].astype(str).str.strip()
    df["Breed"] = df["Breed"].astype(str).str.strip()
    df["Sex"] = df["Sex"].astype(str).str.title().str.strip()
    df["Species"] = df["Species"].astype(str).str.title().str.strip()
    df["Platform"] = df["Platform"].astype(str).str.lower().str.strip()

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

    pets = []
    for _, row in cat_stats.iterrows():
        img_b64 = cat_image_or_placeholder(row["Name"])
        pets.append({
            "id": str(uuid.uuid4()),
            "name": row["Name"],
            "breed": row["Breed"],
            "gender": row["Sex"],
            "visits": int(row["Visits"]),
            "species": row["Species"],
            "platform": row["Platform"],
            "image": img_b64,
            "route": f"/?cat={row['Name'].lower()}",
        })

    # --- Gallery HTML ---
    cards_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Special+Elite&display=swap');
    body, .gallery, .card, .overlay, .view-button {
        font-family: 'Special Elite', serif !important;
    }
    .gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));  /* responsive columns */
        gap: 30px;
        padding: 20px;
        max-width: 100%;
        margin: 0 auto;
        justify-content: center;
    }

    .card {
        aspect-ratio: 2 / 3;            /* keeps card proportional (portrait) */
        width: 100%;                    /* fill grid cell */
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer;
        transition: transform 0.25s ease;
        position: relative;
        background: #c8a18f;
    }

    .card:hover { transform: scale(1.03); }
    .card img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    .overlay {
        position: absolute;
        bottom: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0,0,0,0.4);
        color: white;
        opacity: 0;
        transition: opacity 0.3s ease;
        padding: 20px 15px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }
    .card:hover .overlay { opacity: 1; }
    .overlay * {
        transform: translateY(30px);
        opacity: 0;
        transition: all 0.4s ease;
    }
    .card:hover .overlay * {
        transform: translateY(0);
        opacity: 1;
    }
    .overlay h2 { margin: 0 0 10px 0; font-size: 20px; }
    .overlay p { font-size: 13px; margin: 0; }
    .view-button {
        margin-top: 10px;
        font-size: 13px;
        color: white;
        text-decoration: underline;
    }
    </style>
    <div class="gallery">
    """

    for pet in pets:
        cards_html += f"""
        <div class="card">
            <img src="data:image/webp;base64,{pet['image']}" alt="{pet['name']}" />
            <div class="overlay">
                <h2>{pet['name']}</h2>
                <p><strong>Breed:</strong> {pet['breed']}<br/>
                <strong>Gender:</strong> {pet['gender']}<br/>
                <strong>Visit(s):</strong> {pet['visits']}</p>
                <a class="view-button" href="{pet['route']}" target="_blank">View Stories →</a>
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