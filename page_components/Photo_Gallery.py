# page_components/Photo_Gallery.py
import time, random, re
from pathlib import Path
import streamlit as st

from image_config import BASE_IMAGE_URL
from get_s3_images import get_index, _safe_join_url, _placeholder_for
# --- ADD near the top ---
import html
from streamlit.components.v1 import html as components_html
import math
from typing import Dict, Optional

def number_from_key(key: str) -> Optional[int]:
    """Filename (without extension) is the number."""
    try:
        return int(Path(key).stem)
    except Exception:
        return None
    
def _sort_keys_numerically(keys):
    def keyfunc(k: str):
        n = number_from_key(k)
        return (n if n is not None else float("inf"))
    return sorted(keys, key=keyfunc)

BUCKET       = "annablog"
ABOUT_ROOT1  = "images/Gallery/"       # s3://annablog/images/info/about/
IMAGE_EXT_RE = re.compile(r"\.(webp|avif|jpe?g|png|gif|bmp)$", re.I)

# ---------- session cache-buster (same pattern as Members) ----------
def _cache_rev():
    if "about_img_rev" not in st.session_state:
        st.session_state.about_img_rev = int(time.time())
    return st.session_state.about_img_rev

def _bust(url: str) -> str:
    return f"{url}?rev={_cache_rev()}"

# ---------- URL builder for a FULL S3 key ----------
def url_for_key(key: str) -> str:
    """Key is the full 'images/info/about/xxx.webp' path from get_index."""
    if not key:
        return _placeholder_for("About")
    return _bust(_safe_join_url(BASE_IMAGE_URL, key))

# ---------- discovery via the SAME indexer you use on About_Pawpaw ----------
def discover_keys(prefix: str):
    idx = get_index(BUCKET, prefix)
    keys = []
    if isinstance(idx, dict):
        for _, arr in idx.items():
            keys.extend(arr or [])
    elif isinstance(idx, (list, tuple)):
        keys = list(idx)

    keys = [k for k in keys
            if not Path(k).name.startswith(("._", "."))
            and IMAGE_EXT_RE.search(k)]
    keys = list(dict.fromkeys(keys))
    keys = _sort_keys_numerically(keys)   # strict 1..N order
    return keys

CAPTIONS: Dict[int, str] = {
    1: "小白 & 小黑，Appa & Shyshy",
    2: "Turbo冲我大叫因为要吃饭，Mason盯着Turbo因为他想叨他屁股。",
    3: "小Dutch出门不愿意栓绳儿",
    4: "Tobi & Gigi 姐弟俩",
    5: "两只博美，双倍可爱！",
    6: "Mimi & Bruce 欢喜冤家",
    7: "Summer & Donny是最好的朋友",
    8: "旮豆 & 挖泥合伙孤立小佐",
    9: "Kylie & Angus两只一样一样的澳拉贵",
    10: "一家三口和和睦睦",
    11: "Kylie占可乐巢",
    12: "Jemma & Pi是相爱相杀的兄妹俩",
    13: "拉拉 & Summer沙发咬嘴嘴",
    14: "巴士 & 布丁共享猫条",
    15: "三只橘色生物面基",
    16: "Toffee小寿星一岁生日快乐！",
    17: "波妞 & Summer 是好朋友",
    18: "两只小猫在密谋些什么呢",
    19: "这个饭吃的我压力有点儿大",
    20: "Pika & 柚柚真的很团结了",
    21: "复制粘贴约克夏Opao & Mocha",
    22: "黄金搭档在想什么时候开饭",
    23: "三方会晤闻闻闻",
    24: "Rolie & Millie有雪糕吃！",
    25: "哇哦！好多好多小白狗",
    26: "胖虎最喜欢和Wolfie玩球了",
    27: "Ky占Don巢",
    28: "Pico要回家了，在和Boba说再见",
    29: "二弟在被Bubble & Rocket两兄弟夹击",
    30: "今天是Donny一岁生日！",
    31: "弟弟 & 蛋黄同步抬头",
    32: "牛牛 & 豆豆各自有各自的窝",
    33: "阿奇是邦邦的枕头",
    34: "真假腊肠jellycat",
    35: "是两只雪纳瑞！",
    36: "Rocket & Bubble的兄弟时光",
    37: "桌子上长小手办了",
    38: "栗子姐姐也想加入小狗游戏",
    39: "牛牛是Tora姐姐的跟屁虫",
    40: "Noel 社交进行中......",
    41: "椰椰 & Opao是两只萌物",
    42: "生气小猫在看小猫片",
    43: "Dondon小社恐，不喜欢和别人玩儿",
    44: "比熊马尔泰傻傻分不清",
    45: "小眼睛和大舌头！",
    46: "歇歇 & Bentley是好朋狗",
    47: "奥利和喜欢的女生一起遛遛",
    48: "肌肉噗噗很喜欢给Ace秀他的肱二头",
    49: "Drop in visit了一家四口",
    50: "缅因寿司猫消消乐",
    51: "哈士奇教育大会",
    52: "赛级Pangda & Pangky兄妹柴",
    53: "小鱼 & Boba，黑珍珠 & 白珍珠",

}

def _render_exact_figure_style(
    keys,
    height_px: int = 720,
    col_min_px: int = 280,      # still used for grid mode
    max_fig_px: int = 520,
    *,
    captions_by_num: Optional[Dict[int, str]] = None,
    show_captions: bool = True,
    masonry: bool = True,       # waterfall fill mode
    # ---- luxe frame colors ----
    frame_bg="#f8f6f3",
    outer_top="#bfb6ae",
    outer_right="#d9d1ca",
    outer_bottom="#eae2db",
    outer_left="#d1c8c0",
    mat_color="#f2e9e3",
    # ---- photo shadows (no border) ----
    photo_shadow_main="0 10px 24px rgba(90,60,45,.20)",
    photo_shadow_soft="0 3px 8px rgba(90,60,45,.10)",
    photo_shadow_ring="0 0 0 2px rgba(180,160,140,.08)",
    photo_edge_highlight: str = "0 1px 0 rgba(255,255,255,.35) inset",
):
    def _cap_html(k: str) -> str:
        if not show_captions:
            return ""
        n = number_from_key(k)
        if n is None:
            return ""
        txt = (captions_by_num or {}).get(n, "")
        return f'<div class="pg-caption">{html.escape(str(txt))}</div>' if txt else ""

    # --- build figures once (caption outside the frame) ---
    figures = []
    for k in keys:
        n   = number_from_key(k)
        src = url_for_key(k)
        title = f"Photo #{n}" if n is not None else "Photo"
        # Prefer caption text as alt when available
        cap_text = (captions_by_num or {}).get(n, "") if n is not None else ""
        alt = cap_text or (f"photo {n}" if n is not None else "photo")
        figures.append(
            f"""
            <a class="pg-item" href="{src}" target="_blank" rel="noopener">
              <div class="pg-card">
                <figure title="{html.escape(title)}">
                  <img src="{src}" alt="{html.escape(alt)}" loading="lazy" decoding="async"/>
                </figure>
                {_cap_html(k)}
              </div>
            </a>
            """
        )
    figures_html = "\n".join(figures)

    # ===== layout + size rules (define BEFORE using in css) =====
    layout_css = f"""
      /* GRID (even rows) */
      .gallery-wrap.grid {{
        display: grid;
        gap: 18px;
        grid-template-columns: repeat(auto-fit, minmax({col_min_px}px, 1fr));
        align-items: start;
        justify-items: center;
        padding: 24px 20px 40px;
        overflow: hidden;
      }}

      /* MASONRY (waterfall fill) */
      .gallery-wrap.masonry {{
        column-count: 4;
        column-gap: 18px;
        padding: 24px 20px 40px;
      }}
      .gallery-wrap.masonry .pg-item {{
        break-inside: avoid;
        display: inline-block;
        width: 100%;
        margin: 0 0 18px;
      }}
      .gallery-wrap.masonry .pg-card {{ display:block; }}

      @media (max-width: 1200px) {{ .gallery-wrap.masonry {{ column-count: 3; }} }}
      @media (max-width: 900px)  {{ .gallery-wrap.masonry {{ column-count: 3; }} }}
      @media (max-width: 700px)  {{ .gallery-wrap.masonry {{ column-count: 2; }} }}
      @media (max-width: 520px)  {{ .gallery-wrap.masonry {{ column-count: 2; }} }}
    """

    img_size_rules = """
      /* default (grid): keep tall images reasonable */
      .gallery-wrap.grid figure img { max-height: 65vh; }
      /* masonry: let them flow naturally for better packing */
      .gallery-wrap.masonry figure img { max-height: none; }
    """

    # ===== single, final CSS block =====
    css = f"""
    <style>
      {layout_css}

      .pg-item {{ width:100%; text-decoration:none; }}
      .pg-card {{ width:100%; max-width:{max_fig_px}px; margin:0 auto; }}

      /* Framed figure with bottom gap for the outside caption */
      figure {{
        display:block; width:100%; margin:0 auto 18px;
        position:relative; vertical-align:middle;

        border-width:10px; border-style:solid;
        border-top-color:{outer_top};
        border-right-color:{outer_right};
        border-bottom-color:{outer_bottom};
        border-left-color:{outer_left};

        padding:20px;
        box-shadow:0 0 5px rgba(0,0,0,.5) inset, 0 5px 20px rgba(0,0,0,.5);
        overflow:hidden;
        background:{frame_bg};
      }}
      figure::before, figure::after {{ content:''; display:block; position:absolute; inset:0; }}

      figure::before {{
        box-shadow:0 0 5px black inset;
        border:30px solid {mat_color};
        z-index:0;
      }}

      figure::after {{
        z-index:2; pointer-events:none;
        background:
          radial-gradient(120% 80% at 0% 0%, rgba(255,255,255,.08), transparent 50%),
          linear-gradient(180deg, rgba(255,255,255,.02), transparent 40%);
        box-shadow:-20px -20px 80px rgba(255,255,255,.25);
      }}

      figure img {{
        display:block;
        width:100%;
        height:auto;
        object-fit:contain;
        position:relative;
        z-index:1;
        vertical-align:bottom;
        box-shadow: 
          {photo_shadow_ring},
          0 8px 18px rgba(80,60,50,.18),
          0 3px 8px rgba(90,60,45,.10),
          inset 0 1px 0 rgba(255,255,255,.25);
        background:transparent;
        border-radius:4px;
      }}

      /* GREY caption outside the frame */
      .pg-caption {{
        margin: 0 4px 6px;
        font-size: 13px; line-height: 1.35;
        color: #777;              /* grey */
        text-align: center;
        word-break: break-word;
      }}
      .gallery-wrap.masonry .pg-item {{
        margin: 0 0 10px;         /* was 18px; ↓ tighter stack */
      }}

      {img_size_rules}

      /* mobile tweaks */
      @media (max-width:600px){{
        .gallery-wrap.grid {{
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          padding:14px 10px 26px; gap:10px;
        }}
        figure {{ padding:12px; border-width:8px; }}
        figure::before {{ border-width:22px; }}
      }}

      html, body {{ margin:0; padding:0; text-align:center; box-sizing:border-box; }}
      *, *::before, *::after {{ box-sizing:inherit; }}
    </style>
    """

    layout_class = "masonry" if masonry else "grid"

    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">{css}</head>
<body>
  <div class="gallery-wrap {layout_class}">
    {figures_html}
  </div>
</body></html>
"""
    components_html(html_doc, height=height_px, scrolling=True)


# ---------- page ----------
def main():
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    st.title("🖼️ Photo Gallery")
    st.caption("Captured moments from Pawpaw Homestay!")

    keys = discover_keys(ABOUT_ROOT1)
    if not keys:
        st.warning(f"No images found under s3://{BUCKET}/{ABOUT_ROOT1}")
        return
    
    _render_exact_figure_style(
        keys,
        height_px=720,
        captions_by_num=CAPTIONS,  # or load from JSON if you want
        show_captions=True,
        masonry=True
    )


if __name__ == "__main__":
    main()
