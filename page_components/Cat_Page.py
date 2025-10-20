# page_components/Dog_Page.py
import os
import json
import base64
from typing import List, Dict
import streamlit as st
from streamlit.components.v1 import html
from typing import List, Optional
from image_config import BASE_IMAGE_URL
import boto3
from botocore.config import Config
from botocore import UNSIGNED
from botocore.exceptions import ClientError

# ---------- Helpers ----------
def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

import random
from pathlib import Path
def go_back_to_sheltopia():
    
    try:
        st.experimental_set_query_params(page="catopia")
    except Exception:
        # Old versions only
        st.experimental_set_query_params(page="catopia")

    st.rerun()

def get_s3_filenames(
    bucket: str,
    prefix: str = "",
    aws_profile: Optional[str] = None,
    suffix: Optional[str] = None,
    return_full_path: bool = False,
    max_results: Optional[int] = None,
) -> List[str]:
    """
    Return a list of object keys (filenames) under the given S3 prefix (folder).

    Args:
        bucket: S3 bucket name.
        prefix: Prefix / "folder" to list under. Can be empty or end with '/'.
        aws_profile: Optional AWS profile name (uses default session if None).
        suffix: Optional suffix filter (e.g., '.jpg', '.csv').
        return_full_path: If True, returns full S3 URIs like `s3://bucket/key`.
        max_results: Optional overall maximum number of results to return.

    Returns:
        List of keys (or S3 URIs if return_full_path=True).
    """
    if not bucket:
        raise ValueError("bucket must be provided")

    session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
    s3 = session.client("s3",config=Config(signature_version=UNSIGNED))

    # Normalize prefix: no change required, list_objects_v2 accepts as-is
    continuation_token = None
    results: List[str] = []

    try:
        while True:
            kwargs = {
                "Bucket": bucket,
                "Prefix": prefix,
                "MaxKeys": 1000,  # page size
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            resp = s3.list_objects_v2(**kwargs)

            contents = resp.get("Contents", [])
            for obj in contents:
                key = obj["Key"]
                if suffix and not key.endswith(suffix):
                    continue
                if return_full_path:
                    results.append(f"s3://{bucket}/{key}")
                else:
                    results.append(key)

                if max_results is not None and len(results) >= max_results:
                    return results[:max_results]

            if not resp.get("IsTruncated"):  # no more pages
                break
            continuation_token = resp.get("NextContinuationToken")
    except ClientError:
        # Re-raise, caller can catch and handle (or log)
        raise

    return results

def get_dog_images(dog_name: str) -> List[Dict[str, str]]:
    """
    Pick up to 10 random, non-repeating images from images/shelter/<dog_name>,
    excluding the cover "{dog_name}1.webp". Returns [{url, alt}] with base64 data URLs.
    """
    folder = Path("images") / "catopia" / dog_name
    if not folder.is_dir():
        return []

    # Allowed image extensions (extend if needed)
    exts = {".webp", ".jpg", ".jpeg", ".png", ".gif"}

    candidates = get_s3_filenames(
        bucket="annablog",
        prefix=f"images/catopia/{dog_name}/")

    if not candidates:
        # Nothing to show after exclusion
        return []

    # Sample up to 10 at random without repetition
    k = min(10, len(candidates))
    picks = random.sample(candidates, k=k)

    images: List[Dict[str, str]] = []
    for p in picks:
        try:
            images.append({
                "url": f"{BASE_IMAGE_URL}/{p}",
                "alt": f"{dog_name} - {p}",
            })
        except Exception:
            # Skip unreadable files
            continue

    return images


def set_query_params_safe(**params):
    """
    Safely set query params across Streamlit versions.
    """
    try:
        # Newer Streamlit: st.query_params is a MutableMapping-like object
        for k, v in params.items():
            st.query_params[k] = v
        # Remove keys explicitly set to None
        for k, v in list(params.items()):
            if v is None and k in st.query_params:
                del st.query_params[k]
    except Exception:
        # Fallback for older versions
        clean = {k: v for k, v in params.items() if v is not None}
        st.experimental_set_query_params(**clean)

# ---------- Page ----------
def main(dog_name: str):
    # NOTE: do NOT call st.set_page_config here (it’s already called in streamlit_app)
    st.title(f"🐱 Story of {dog_name.capitalize()}")

    # --- Hide sidebar ONLY on this page ---
    st.markdown("""
    <style>
      [data-testid="stSidebar"] { display: none !important; }
      [data-testid="stSidebarCollapsedControl"] { display: none !important; }
      /* Optional: tuck the main content nicely edge-to-edge */
      .block-container { padding-left: 16px !important; padding-right: 16px !important; }
    </style>
    """, unsafe_allow_html=True)

    # Normalize and map dog_name to the true casing of the folder
    base_dir = os.path.join("images", "catopia")
    if not os.path.isdir(base_dir):
        st.error("'images/catopia' folder not found.")
        return

    all_dog_folders = [name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))]
    if not all_dog_folders:
        st.error("No dog folders found under images/catopia.")
        return

    name_map = {name.lower(): name for name in all_dog_folders}
    key_lower = (dog_name or "").lower()
    if key_lower not in name_map:
        st.error(f"Cat '{dog_name}' not found.")
        return

    true_dog_name = name_map[key_lower]

    # Images for carousel
    images = get_dog_images(true_dog_name)
    images_json = json.dumps(images)

    # --- 3D Carousel (responsive + touch + mouse drag) ---
    html(
        f"""
        <div id="vue-carousel"></div>

        <script>
        const images = {images_json};

        const container = document.createElement("div");
        container.className = "gallery-container";

        const scope = document.createElement("div");
        scope.className = "scope";
        container.appendChild(scope);

        const count = Math.max(images.length, 1);
        const step = 360 / count;
        const radius = Math.min(420, 120 + count * 32);

        images.forEach((img, i) => {{
            const span = document.createElement("span");
            span.style.setProperty("--i", i);
            span.style.setProperty("--step", step + "deg");
            span.style.setProperty("--radius", radius + "px");
            const imageEl = document.createElement("img");
            imageEl.loading = "lazy";
            imageEl.decoding = "async";
            imageEl.src = img.url;
            imageEl.alt = img.alt;
            span.appendChild(imageEl);
            scope.appendChild(span);
        }});

        document.getElementById("vue-carousel").appendChild(container);

        let angle = 0;
        let isPaused = false;
        let startX = 0;
        let dragging = false;

        function rotateCarousel() {{
            if (!isPaused) {{
                angle += 0.25;
                scope.style.transform = `perspective(1200px) rotateY(${{angle}}deg)`;
            }}
            requestAnimationFrame(rotateCarousel);
        }}

        container.addEventListener("mouseenter", () => isPaused = true);
        container.addEventListener("mouseleave", () => isPaused = false);

        // Touch drag
        container.addEventListener("touchstart", (e) => {{
            isPaused = true;
            startX = e.touches[0].clientX;
        }});
        container.addEventListener("touchmove", (e) => {{
            const deltaX = e.touches[0].clientX - startX;
            angle += deltaX * 0.4;
            startX = e.touches[0].clientX;
            scope.style.transform = `perspective(1200px) rotateY(${{angle}}deg)`;
        }});
        container.addEventListener("touchend", () => {{
            setTimeout(() => {{ isPaused = false; }}, 600);
        }});

        // Mouse drag (desktop)
        container.addEventListener("mousedown", (e) => {{
            dragging = true; isPaused = true; startX = e.clientX;
        }});
        window.addEventListener("mousemove", (e) => {{
            if (!dragging) return;
            const deltaX = e.clientX - startX;
            angle += deltaX * 0.4;
            startX = e.clientX;
            scope.style.transform = `perspective(1200px) rotateY(${{angle}}deg)`;
        }});
        window.addEventListener("mouseup", () => {{
            if (dragging) {{ dragging = false; setTimeout(() => {{ isPaused = false; }}, 600); }}
        }});

        rotateCarousel();
        </script>

        <style>
        .gallery-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            touch-action: pan-y;
            height: 80vh;
            max-height: 820px;
            width: 100%;
            padding: 0;
            margin: 0 auto 8px auto;
            background: transparent;
            box-sizing: border-box;
            position: relative;
        }}

        .scope {{
            width: min(240px, 70vw);
            height: min(300px, 44vh);
            transform-style: preserve-3d;
            position: relative;
            transition: transform 0.08s ease;
            transform: translateY(100px);
        }}

        .scope span {{
            position: absolute;
            width: 100%;
            height: 100%;
            transform-origin: center;
            transform-style: preserve-3d;
            transform: rotateY(calc(var(--i) * var(--step))) translateZ(var(--radius));
        }}

        .scope span img {{
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 14px;
            object-fit: cover;
            border: 5px solid #c18c5d;
            box-sizing: border-box;
            box-shadow: 0 12px 24px rgba(0,0,0,0.18);
            background: #ffeada;
        }}

        @media (max-width: 768px) {{
            .gallery-container {{ height: 56vh; }}
            .scope {{ width: min(200px, 76vw); height: min(280px, 40vh); }}
        }}
        </style>
        """,
        height=680,
    )

    # === Dog Stories ===
    stories = {
        "appa": """
        **Appa** is our fluffy cloud of joy. Ever since his first visit, he's captured hearts with his laid-back
        attitude and goofy zoomies. Whether he's chilling on the grass or nudging us for treats, Appa reminds us
        daily to take things slow and enjoy the moment.
        """,
        "archie": """
        **Archie** is an explorer at heart. He's always the first to investigate new toys, sniff out every corner of
        the play area, and greet every guest like royalty. His energy is infectious and his loyalty unmatched.
        """,
        "milo": """
        **Milo** is the quiet charmer. With those deep eyes and gentle paws, he wins affection without making a sound.
        He's a nap-time enthusiast, a belly-rub addict, and a friend to every pup who crosses his path.
        """,
        # Add more stories here...
    }

    st.markdown("---")
    dog_story = stories.get(true_dog_name.lower(), "*This dog's story is still being written. Stay tuned!*")
    st.markdown(dog_story)

    # === Prev / Back / Next Controls (alphabetical by folder name) ===
    all_dog_names_sorted = sorted([n for n in name_map.values()], key=lambda n: n.lower())
    current_index = all_dog_names_sorted.index(true_dog_name)
    prev_dog = all_dog_names_sorted[current_index - 1] if current_index > 0 else None
    next_dog = all_dog_names_sorted[current_index + 1] if current_index < len(all_dog_names_sorted) - 1 else None

    # === Prev / Back / Next Controls (HTML nav — dark brown buttons, robust clicks) ===
    from urllib.parse import quote

    NAV_ALIGN = "space-between"  # 'center' | 'flex-start' | 'flex-end' | 'space-around' | 'space-between'

    prev_html = (
        f"<a class='dog-btn' href='javascript:void(0)' onclick=\"goDog('{quote(prev_dog)}')\">"
        f"⬅️ Previous ({prev_dog.capitalize()})</a>"
        if prev_dog else ""
    )
    back_html = "<a class='dog-btn' href='javascript:void(0)' onclick='backDogtopia()'>🏠 Back to Catopia</a>"
    next_html = (
        f"<a class='dog-btn' href='javascript:void(0)' onclick=\"goDog('{quote(next_dog)}')\">"
        f"Next ({next_dog.capitalize()}) ➡️</a>"
        if next_dog else ""
    )

    nav_html = f"""
    <style>
    .dog-nav {{
        display: flex; gap: 12px; align-items: center;
        justify-content: {NAV_ALIGN};
        max-width: 820px; margin: 8px auto 16px;
    }}
    .dog-btn {{
        display:inline-block; text-decoration:none;
        background:#5a3b2e; color:#ffeada;
        padding:10px 14px; border-radius:10px; font-weight:700;
        box-shadow:0 6px 12px rgba(0,0,0,0.18);
        transition: transform .12s ease, filter .2s ease;
    }}
    .dog-btn:hover {{ filter:brightness(1.05); transform:translateY(-1px); }}
    .dog-btn:active {{ transform:translateY(0); }}
    </style>

    <div class="dog-nav">
    {prev_html}
    {back_html}
    {next_html}
    </div>

    <script>
    const TOP = (window.top && window.top.location) ? window.top.location : window.location;
    const APP_BASE = TOP.origin + TOP.pathname;

    function safeOpen(url) {{
        try {{
        // Most reliable inside Streamlit's sandbox: open a new tab
        window.open(url, '_blank');
        }} catch (e) {{
        // Fallback: try to navigate the top window
        try {{ TOP.href = url; }} catch (_e) {{ console.error('Navigation blocked:', _e); }}
        }}
    }}

    function goDog(name) {{
        const url = APP_BASE + '?page=cat&cat=' + encodeURIComponent(name);
        safeOpen(url);
    }}

    function backDogtopia() {{
        const url = APP_BASE + '?page=catopia';
        safeOpen(url);
    }}
    </script>
    """

    html(nav_html, height=96)

# Allow running this module directly for quick testing
if __name__ == "__main__":
    q = st.query_params.get("cat") if hasattr(st, "query_params") else None
    dog_param = q[0] if isinstance(q, list) else (q if isinstance(q, str) else None)
    if not dog_param:
        base_dir = os.path.join("images", "catopia")
        if os.path.isdir(base_dir):
            folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            dog_param = folders[0] if folders else ""
    if dog_param:
        main(dog_param)
    else:
        st.info("Add some folders under images/dogtopia and pass ?page=cat&cat=Name in the URL.")
