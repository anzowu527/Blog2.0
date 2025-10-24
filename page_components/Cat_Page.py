# page_components/Cat_Page.py
from __future__ import annotations
import streamlit as st
from typing import Dict, List
from pet_pages_common import render_pet_detail_page

# ---------- Inline "best friends" (fill the lists on the right) ----------
# Keys are LOWERCASED for robust lookup; Chinese names stay as-is.
_FRIENDS: Dict[str, List[str]] = {
    "abby": ["bruce","mimi"],
    "athena": [],
    "bella": [],
    "boba": [],
    "bruce": [],
    "bubble": [],
    "chewy": [],
    "clarice": [],
    "delia": [],
    "dio": [],
    "django": [],
    "draco": [],
    "gigi": [],
    "indigo": [],
    "ivy": [],
    "joey": [],
    "lily": [],
    "mars": [],
    "marty": [],
    "melody": [],
    "mia": [],
    "milo1": [],
    "mimi": [],
    "moomoo": [],
    "nacho": [],
    "noel": [],
    "nyxey": [],
    "oreo": [],
    "pico": [],
    "pika": [],
    "riceball": [],
    "rocket": [],
    "sophie": [],
    "tobi": [],
    "tora": [],
    "丸丸": [],
    "多多": [],
    "奶茶": [],
    "小七": [],
    "小佐": [],
    "小鱼": [],
    "巴士": [],
    "布丁2": [],
    "弟弟": [],
    "挖泥": [],
    "旮豆": [],
    "柚柚": [],
    "牛牛": [],
    "皮皮": [],
    "福来": [],
    "米浆": [],
    "米米": [],
    "蛋黄": [],
    "豆豆": [],
}

def _get_cat_story(name: str) -> str:
    try:
        import importlib
        from .stories import cat_stories
        importlib.reload(cat_stories)  # hot-reload while developing
        return cat_stories.get_story(name)
    except Exception:
        return ""

def _get_cat_friends(name: str) -> List[str]:
    """Return best-friend names for avatar chips (case-insensitive)."""
    if not name:
        return []
    key = name.strip().lower()
    return _FRIENDS.get(key, [])

def main(cat_name: str):
    render_pet_detail_page(
        person_name=cat_name,
        bucket="annablog",
        root_prefix="images/catopia",
        title_text=f"🐱 Story of {cat_name.capitalize()}",
        page_param="cat",
        back_page="catopia",
        story_getter=_get_cat_story,
        friends_getter=_get_cat_friends,   # ← enable chips below the card
        # If you later parameterized card height in pet_pages_common, you can pass:
        # max_photos=10,
    )

if __name__ == "__main__":
    q = st.query_params.get("cat") if hasattr(st, "query_params") else None
    val = q[0] if isinstance(q, list) else (q if isinstance(q, str) else None)
    if val:
        main(val)
    else:
        st.info("Pass ?page=cat&cat=Name in the URL.")
