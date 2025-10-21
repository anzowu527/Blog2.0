# page_components/pet_pages_common.py
import json
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

import streamlit as st
from streamlit.components.v1 import html

from get_s3_images import get_s3_filenames, build_prefix_index
from image_config import BASE_IMAGE_URL


# ---- small utils ----
_IMG_SUFFIXES: Tuple[str, ...] = (".webp", ".jpg", ".jpeg", ".png", ".gif")

def _safe_join_url(base: str, key: str) -> str:
    # keep / but escape non-ASCII
    return f"{base.rstrip('/')}/{quote(key.lstrip('/'), safe='/')}"

def _random_image_urls(
    bucket: str,
    person_name: str,
    root_prefix: str,
    max_count: int = 10,
    suffixes: Sequence[str] = _IMG_SUFFIXES,
) -> List[Dict[str, str]]:
    prefix = f"{root_prefix.rstrip('/')}/{person_name}/"
    keys = get_s3_filenames(bucket=bucket, prefix=prefix, suffixes=tuple(suffixes))
    if not keys:
        return []
    picks = random.sample(keys, k=min(max_count, len(keys)))
    return [{"url": _safe_join_url(BASE_IMAGE_URL, k), "alt": f"{person_name} - {k}"} for k in picks]


def _prev_next_names(bucket: str, root_prefix: str, current: str) -> Tuple[Optional[str], Optional[str], List[str]]:
    idx = build_prefix_index(bucket, root_prefix, group_depth=1, suffixes=_IMG_SUFFIXES)
    # folder names under root
    folders = sorted(idx.keys(), key=lambda s: s.lower())
    if not folders:
        return None, None, []
    # try case-insensitive match to determine the true-cased entry
    lower_map = {k.lower(): k for k in folders}
    current_true = lower_map.get((current or "").lower(), None)
    if current_true is None:
        # not found in S3 index -> best effort alphabet position
        return None, None, folders
    i = folders.index(current_true)
    prev_name = folders[i - 1] if i > 0 else None
    next_name = folders[i + 1] if i < len(folders) - 1 else None
    return prev_name, next_name, folders


# ---- main renderer ----
def render_pet_detail_page(
    person_name: str,
    *,
    bucket: str,
    root_prefix: str,     # e.g. "images/dogtopia" / "images/catopia" / "images/shelter"
    title_text: str,      # e.g. "🐶 Story of Appa"
    page_param: str,      # e.g. "dog", "cat", "shelter"
    back_page: str,       # e.g. "dogtopia", "catopia", "sheltopia"
    story_getter: Optional[Callable[[str], str]] = None,  # optional callback
    max_photos: int = 10,
) -> None:
    """One-liner detail page renderer for Dog/Cat/Shelter detail pages."""

    # Title
    st.title(title_text)

    # Hide sidebar on detail pages
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
          .block-container { padding-left: 16px !important; padding-right: 16px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Images (S3 → CloudFront URLs)
    images = _random_image_urls(bucket=bucket, person_name=person_name, root_prefix=root_prefix, max_count=max_photos)
    images_json = json.dumps(images)

    # 3D carousel (your existing HTML/JS)
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

    # Story
    st.markdown("---")
    story = None
    if story_getter:
        try:
            story = story_getter(person_name)
        except Exception:
            story = None
    st.markdown(story or "*This friend's story is still being written. Stay tuned!*")

    # Prev / Back / Next
    prev_name, next_name, _ = _prev_next_names(bucket, root_prefix, person_name)

    prev_html = (
        f"<a class='dog-btn' href='javascript:void(0)' onclick=\"goPet('{quote(prev_name)}')\">"
        f"⬅️ Previous ({prev_name})</a>" if prev_name else ""
    )
    back_html = "<a class='dog-btn' href='javascript:void(0)' onclick='backList()'>🏠 Back</a>"
    next_html = (
        f"<a class='dog-btn' href='javascript:void(0)' onclick=\"goPet('{quote(next_name)}')\">"
        f"Next ({next_name}) ➡️</a>" if next_name else ""
    )

    html(
        f"""
        <style>
        .dog-nav {{ display:flex; gap:12px; align-items:center; justify-content:space-between;
                    max-width:820px; margin: 8px auto 16px; }}
        .dog-btn {{ display:inline-block; text-decoration:none; background:#5a3b2e; color:#ffeada;
                    padding:10px 14px; border-radius:10px; font-weight:700;
                    box-shadow:0 6px 12px rgba(0,0,0,0.18);
                    transition: transform .12s ease, filter .2s ease; }}
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
            try {{ window.open(url, '_blank'); }}
            catch (e) {{ try {{ TOP.href = url; }} catch (_e) {{ console.error('Navigation blocked:', _e); }} }}
        }}

        function goPet(name) {{
            const url = APP_BASE + '?page={page_param}&{page_param}=' + encodeURIComponent(name);
            safeOpen(url);
        }}

        function backList() {{
            const url = APP_BASE + '?page={back_page}';
            safeOpen(url);
        }}
        </script>
        """,
        height=96,
    )
