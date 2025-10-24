# page_components/pet_pages_common.py
import json
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

import streamlit as st
from streamlit.components.v1 import html

from get_s3_images import get_s3_filenames, build_prefix_index
from image_config import BASE_IMAGE_URL

import re
AVATAR_ROOT = "images/avatar/"  # s3://annablog/images/avatar/<lowercased-name>.webp

def _norm_lower(s: str) -> str:
    return (s or "").strip().lower()

def _avatar_url_for(name: str) -> str:
    key = f"{AVATAR_ROOT}{_norm_lower(name)}.webp"
    return f"{BASE_IMAGE_URL.rstrip('/')}/{quote(key.lstrip('/'), safe='/')}"

def _slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "pet"

def _bilingual_card_html(
    card_id: str,
    en_html: str,
    zh_html: str,
    *,
    friends: Optional[List[str]] = None,
    page_param: Optional[str] = None,
    card_height: int = 340,           # NEW: desktop/tablet fixed height (px)
    card_height_mobile: int = 400,    # NEW: mobile fixed height (px)
    visit_count: Optional[int] = None,
) -> str:
    en_id = f"text-en-{card_id}"
    zh_id = f"text-zh-{card_id}"
    btn_id = f"ppw-toggle-{card_id}"
    root_id = f"pawpawCard-{card_id}"

    friends = friends or []
    chips = []
    for f in friends:
        avatar = _avatar_url_for(f)
        chips.append(
            f"""
            <div class="chip" data-name="{quote(f)}" title="{f}">
              <img src="{avatar}" alt="{f}" loading="lazy" decoding="async" />
              <span>{f}</span>
            </div>
            """
        )
    friends_block = (
        f"""
        <div class="friends-wrap">
            <div class="friends-title">Best Friends ｜ 好朋友</div>
            <div class="chips-row max-2lines">   <!-- add class here if desired -->
            {''.join(chips)}
            </div>
        </div>
        """ if chips else ""
    )

    nav_js = ""
    if page_param:
        nav_js = f"""
        (function(){{
          const TOP = (window.top && window.top.location) ? window.top.location : window.location;
          const APP_BASE = TOP.origin + TOP.pathname;
          function goPet(name) {{
            const url = APP_BASE + '?page={page_param}&{page_param}=' + encodeURIComponent(name);
            try {{ window.open(url, '_self'); }} catch(e){{ TOP.href = url; }}
          }}
          document.querySelectorAll('#{root_id} .chip').forEach(function(chip){{
            chip.addEventListener('click', function(){{
              const name = chip.getAttribute('data-name');
              if(name) goPet(name);
            }});
          }});
        }})();
        """

    return f"""
    <style>
    .ppw-card {{
        position: relative;
        display: flex;                 /* vertical stack */
        flex-direction: column;
        max-width: 900px; width: 92s%;
        height: 360px;                 /* fixed desktop height (or inject via param) */
        margin: 0 auto 14px auto;
        padding: 22px 20px 22px 20px;
        background: #fff6ef;
        border: 1px solid #c8a18f33;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(95,47,17,.10);
        color: #5a3b2e;
        line-height: 1.72;
        font-size: 17px;
        font-family: 'Hepta Slab', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial;
        border-left: 6px solid #c8a18f66;
        word-break: break-word;        /* long words wrap */
        overflow: hidden;    
    }}
    .ppw-card .ppw-text{{
        flex: 1 1 auto;                /* take remaining space */
        min-height: 0;                 /* IMPORTANT: allow shrink in flex container */
        overflow-y: auto;              /* scroll when too long */
        padding-right: 6px;            /* room for scrollbar */
        overscroll-behavior: contain;  /* prevent parent scrolling */
        -webkit-overflow-scrolling: touch; /* iOS momentum scroll */
        padding-top: 20px;  
    }}

    .ppw-card p{{ margin: 0 0 .6em; }}
    .ppw-card p:last-child{{ margin-bottom: 0; }}

    .ppw-card .translate-btn {{
        position: absolute; right: 12px; top: 12px; z-index: 2;
        background-color: #c8a18f; color: #fff; border: none;
        border-radius: 8px; padding: 4px 10px; font-size: 13px;
        cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        transition: transform .15s ease, background .2s ease;
    }}
    .ppw-card .translate-btn:hover {{ background-color: #b58c7c; transform: translateY(-1px); }}

    .ppw-card .friends-wrap{{ 
        flex: 0 0 auto;                
        margin-top: 8px;
        padding-top: 10px;
        border-top: 1px dashed rgba(200,161,143,.45); 
    }}

    .ppw-card .friends-title{{
        font-weight: 700;
        font-size: 14px;
        opacity: .9;
        margin: 0 0 8px;                /* tighten spacing since we added a divider */
    }}

    .ppw-card .chips-row{{ display: flex; flex-wrap: wrap; gap: 8px 10px; }}
    .ppw-card .chip{{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 6px 10px; border-radius: 9999px;
      background: rgba(200,161,143,.18); color:#5a3b2e;
      font-weight: 600; font-size: 13px; cursor: pointer; user-select: none;
      transition: transform .08s ease, box-shadow .2s ease, background .2s ease;
    }}
    .ppw-card .chip:hover{{ transform: translateY(-1px); box-shadow: 0 4px 10px rgba(200,161,143,.28); }}
    .ppw-card .chip img{{
      width: 36px;                   /* ← 从 24px 调到 36px */
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #fff;        /* 边框稍厚一点更显干净 */
        box-shadow: 0 1px 4px rgba(0,0,0,.12);
        background:#ffeada;
    }}

    @media (max-width: 600px){{
      .ppw-card{{ width: 85%; padding: 16px 14px 16px; font-size: 16px; line-height: 1.65; height: {card_height_mobile}px;}}
      .ppw-card .translate-btn{{ font-size: 12px; padding: 4px 8px; right: 10px; top: 10px; }}
      .ppw-card .chip{{ padding: 5px 9px; font-size: 12px; }}
      .ppw-card .chip img{{ width: 30px; height: 30px; }}
    }}
    </style>

    <div class="ppw-card" id="{root_id}">
        <!-- Scrollable text region inside a fixed-height card -->
        <div class="ppw-text">
            <div id="{en_id}" style="display:none;">{en_html}</div>
            <div id="{zh_id}">{zh_html}</div>
        </div>

        {friends_block}

        <!-- Toggle button (absolute in the corner) -->
        <button class="translate-btn" id="{btn_id}">EN / 中文</button>
    </div>


    <script>
    (function(){{
      // --- auto-resize the Streamlit iframe to remove bottom whitespace
      function _resize() {{
        try {{
          var h = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
          );
          if (window.frameElement) {{
            window.frameElement.style.height = h + 'px';
          }}
        }} catch (e) {{}}
      }}

      var root = document.getElementById('{root_id}');
      var en  = root && root.querySelector('#{en_id}');
      var zh  = root && root.querySelector('#{zh_id}');
      var btn = root && root.querySelector('#{btn_id}');

      if (btn && en && zh) {{
        btn.addEventListener('click', function(){{
          var showEN = (en.style.display === 'none');
          en.style.display = showEN ? 'block' : 'none';
          zh.style.display = showEN ? 'none'  : 'block';
          btn.textContent  = showEN ? '中文 / EN' : 'EN / 中文';
          setTimeout(_resize, 0);    // resize after toggle
        }});
      }}

      new ResizeObserver(_resize).observe(document.body);
      window.addEventListener('load', _resize);
      setTimeout(_resize, 0);
    }})();
    {nav_js}
    </script>
    """


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
    root_prefix: str,
    title_text: str,
    page_param: str,
    back_page: str,
    story_getter: Optional[Callable[[str], str]] = None,
    friends_getter: Optional[Callable[[str], List[str]]] = None,  # ← 新增
    max_photos: int = 10,
) -> None:

    """One-liner detail page renderer for Dog/Cat/Shelter detail pages."""

    # Title
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    st.title(title_text)
    # --- Story (bilingual ppw-card) ---    
    en_text = None
    zh_text = None
    if story_getter:
        try:
            story_val = story_getter(person_name)
            if isinstance(story_val, dict):
                en_text = story_val.get("en") or story_val.get("EN")
                zh_text = story_val.get("zh") or story_val.get("ZH") or story_val.get("cn") or story_val.get("CN")
            elif isinstance(story_val, str):
                en_text = story_val
        except Exception:
            pass

    # Safe defaults if missing
    if not en_text:
        en_text = "<p><em>This friend's story is still being written. Stay tuned!</em></p>"
    if not zh_text:
        zh_text = "<p><em>这个小朋友的故事还在写作中，敬请期待～</em></p>"

    # Wrap plain paragraphs if the provided text isn't HTML-ish
    def _ensure_paragraphs(s: str) -> str:
        if "<p" in s or "<br" in s or "<div" in s:
            return s
        # convert newlines to paragraphs
        ps = [f"<p>{line.strip()}</p>" for line in s.split("\n") if line.strip()]
        return "".join(ps) or "<p></p>"

    en_html = _ensure_paragraphs(en_text)
    zh_html = _ensure_paragraphs(zh_text)
    friends_list: List[str] = []
    if friends_getter:
        try:
            friends_list = friends_getter(person_name) or []
        except Exception:
            friends_list = []

    card_id = _slug(person_name) + "-story"

    CARD_H = 400            # desktop/tablet px
    CARD_H_MOBILE = 400     # mobile px

    card_html = _bilingual_card_html(
        card_id,
        en_html,
        zh_html,
        friends=friends_list,
        page_param=None,
        card_height=CARD_H,
        card_height_mobile=CARD_H_MOBILE,
    )

    # Give iframe headroom; pick the larger (mobile) height + margin
    iframe_h = max(CARD_H, CARD_H_MOBILE)+40   # 420 + 60 = 480
    html(card_html, height=iframe_h)


    # Ensure some breathing room under the card regardless of iframe quirks
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

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
        height=90,
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
        // ↓ NEW: smaller radius on mobile so the ring is tighter
        const isMobile = window.matchMedia("(max-width: 768px)").matches;
        const baseRadius = isMobile ? 90 : 120;    // was 120
        const perImage   = isMobile ? 24 : 32;     // was 32
        const maxRadius  = isMobile ? 300 : 420;   // was 420
        const radius     = Math.min(maxRadius, baseRadius + count * perImage);

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
            max-height: 620px;
            width: 100%;
            padding: 0;
            background: transparent;
            box-sizing: border-box;
            position: relative;
            margin: 0 auto 0 auto;
        }}

        .scope {{
            width: min(240px, 70vw);
            height: min(300px, 44vh);
            transform-style: preserve-3d;
            position: relative;
            transition: transform 0.08s ease;
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
        /* shorter overall frame */
        .gallery-container {{
            height: 55vh;        /* was 56vh */
        }}

        /* narrower & shorter stage; a little less vertical offset */
        .scope {{
            width:  min(170px, 66vw);   /* was min(200px, 76vw) */
            height: min(220px, 38vh);   /* was min(280px, 40vh) */

        }}

        /* slimmer borders/shadows so small images feel lighter */
        .scope span img {{
            border: 3px solid #c18c5d;  /* was 5px */
            border-radius: 12px;        /* was 14px */
            box-shadow: 0 8px 16px rgba(0,0,0,0.16); /* was 0 12px 24px 0.18 */
        }}
        }}
        
        
        </style>
        """,
        height=680,
    )

