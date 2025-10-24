# page_components/Dog_Page.py
import streamlit as st
from typing import List, Dict
from pet_pages_common import render_pet_detail_page

# ---------- Inline data for "best friends" ----------
# Use lowercase keys; we'll normalize incoming names.
_FRIENDS: Dict[str, List[str]] = {
    "ace": ["shyshy","appa"],
    "appa": ["shyshy"],
    "angus": [],
    "archie": [],
    "baggie": [],
    "beanie": [],
    "bentley": [],
    "boston": [],
    "brody": [],
    "brownie": [],
    "buster": [],
    "chippy": [],
    "coco": [],
    "coco1": [],
    "cocoa": [],
    "coconut": [],
    "cola": [],
    "cookie": [],
    "cotton": [],
    "debby": [],
    "dobby": [],
    "donny": [],
    "dutch": [],
    "easton": [],
    "eddie": [],
    "emily": [],
    "gogo": [],
    "jemma": [],
    "kendrick": [],
    "kia": [],
    "kylie": [],
    "laffy": [],
    "liberty": [],
    "lulu": [],
    "luna": [],
    "madi": [],
    "mason": [],
    "melo": [],
    "migo": [],
    "millie": [],
    "milo": [],
    "milo2": [],
    "mocha": [],
    "mocha1": [],
    "molly": [],
    "momo": [],
    "money": [],
    "motley": [],
    "murphy": [],
    "nato": [],
    "oliver": [],
    "oliver1": [],
    "onami": [],
    "opao": [],
    "pangda": [],
    "pangky": [],
    "papaya": [],
    "penny": [],
    "pi": [],
    "rolie": [],
    "romeo": [],
    "rosie": [],
    "rusty": [],
    "shyshy": [],
    "summer": [],
    "toffee": [],
    "turbo": [],
    "uni": [],
    "wolfie": [],
    "wuhu": [],
    "依依": [],
    "可乐": [],
    "可乐1": [],
    "咪豆": [],
    "噗噗": [],
    "外包腊肠": [],
    "奶油": [],
    "安安": [],
    "屁屁": [],
    "布丁": [],
    "布丁1": [],
    "帅哥": [],
    "拉拉": [],
    "曲奇": [],
    "条条": [],
    "果果": [],
    "栗子": [],
    "栗子1": [],
    "椰椰": [],
    "歇歇": [],
    "泡菜": [],
    "波妞": [],
    "派派": [],
    "百亿": [],
    "皮卡丘": [],
    "胖虎": [],
    "豆包": [],
    "辛巴": [],
    "雪哈": [],
    "麻薯": [],
}

def _get_dog_story(name: str) -> str:
    """Return EN/ZH story HTML or plaintext (handled by pet_pages_common)."""
    try:
        import importlib
        from .stories import dog_stories  # keep stories external if you like
        importlib.reload(dog_stories)
        return dog_stories.get_story(name)
    except Exception:
        return ""  # fallback handled upstream

def _get_dog_friends(name: str) -> List[str]:
    """Return a list of friend names shown as avatar chips under the card."""
    key = (name or "").strip().lower()
    return _FRIENDS.get(key, [])

def main(dog_name: str):
    render_pet_detail_page(
        person_name=dog_name,
        bucket="annablog",
        root_prefix="images/dogtopia",
        title_text=f"🐶 Story of {dog_name.capitalize()}",
        page_param="dog",
        back_page="dogtopia",
        story_getter=_get_dog_story,
        friends_getter=_get_dog_friends,  # ← chips below the scrollable text box
        # (optional) if you parameterized card heights:
        # max_photos=10,
    )

if __name__ == "__main__":
    q = st.query_params.get("dog") if hasattr(st, "query_params") else None
    val = q[0] if isinstance(q, list) else (q if isinstance(q, str) else None)
    if val:
        main(val)
    else:
        st.info("Pass ?page=dog&dog=Name in the URL.")
