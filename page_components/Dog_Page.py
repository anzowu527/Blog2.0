# page_components/Dog_Page.py
import streamlit as st
from typing import List, Dict
from pet_pages_common import render_pet_detail_page

# ---------- Inline data for "best friends" ----------
# Use lowercase keys; we'll normalize incoming names.
_FRIENDS: Dict[str, List[str]] = {
    "ace": ["Brody","豆包","噗噗","屁屁","皮卡丘","Chippy","Brody","可乐1","Papaya","Madi"],
    "appa": ["shyshy"],
    "angus": ["kylie"],
    "archie": ["brownie","luna"],
    "baggie": ["archie","luna"],
    "beanie": ["奶油"],
    "bentley": ["歇歇"],
    "boston": [],
    "brody": ["ace"],
    "brownie": ["luna","archie"],
    "buster": ["kylie"],
    "chippy": ["ace"],
    "coco": ["tora"],
    "coco1": ["cola"],
    "cocoa": [],
    "coconut": [],
    "cola": ["coco1","momo"],
    "cookie": ["opao"],
    "cotton": ["kylie","屁屁"],
    "debby": [],
    "dobby": ["athena"],
    "donny": ["kylie","summer","oliver1","rusty"],
    "dutch": ["opao","mocha1"],
    "easton": [],
    "eddie": [],
    "emily": ["椰椰"],
    "gogo": [],
    "jemma": ["pi"],
    "kendrick": [],
    "kia": ["果果","shyshy"],
    "kylie": ["donny","oliver1","madi"],
    "laffy": [],
    "liberty": [],
    "lulu": ["oliver1"],
    "luna": ["archie","brownie"],
    "madi": ["kylie","dutch","ace","豆包"],
    "mason": ["turbo"],
    "melo": [],
    "migo": ["indigo","draco"],
    "millie": ["rolie"],
    "milo": [],
    "milo2": [],
    "mocha": ["布丁1"],
    "mocha1": ["opao","dutch","辛巴"],
    "molly": ["penny","motley","nyxey"],
    "momo": ["rocket","bubble"],
    "money": ["椰椰"],
    "motley": ["molly","penny","nyxey"],
    "murphy": [],
    "nato": ["shyshy"],
    "oliver": [],
    "oliver1": ["donny","kylie","lulu"],
    "onami": [],
    "opao": ["cookie","mocha1","辛巴"],
    "pangda": ["pangky"],
    "pangky": ["pangda"],
    "papaya": ["ace"],
    "penny": ["nyxey","motley","molly"],
    "pi": ["jemma"],
    "rolie": ["millie"],
    "romeo": [],
    "rosie": [],
    "rusty": ["donny","summer"],
    "shyshy": ["appa","kia","nato"],
    "summer": ["summer","rusty","拉拉"],
    "toffee": ["kylie"],
    "turbo": ["mason"],
    "uni": [],
    "wolfie": ["胖虎"],
    "wuhu": [],
    "依依": ["kylie"],
    "可乐": [],
    "可乐1": ["kylie"],
    "咪豆": [],
    "噗噗": ["ace"],
    "外包腊肠": [],
    "奶油": ["beanie","皮卡丘"],
    "安安": [],
    "屁屁": ["皮卡丘","cotton"],
    "布丁": ["dobby"],
    "布丁1": ["mocha","椰椰","歇歇"],
    "帅哥": [],
    "拉拉": ["summer"],
    "曲奇": ["胖虎"],
    "条条": ["kylie"],
    "果果": ["kia"],
    "栗子": [],
    "栗子1": ["kylie","donny"],
    "椰椰": ["歇歇"],
    "歇歇": ["椰椰"],
    "泡菜": [],
    "波妞": ["summer","madi"],
    "派派": [],
    "百亿": ["ace"],
    "皮卡丘": ["屁屁","cotton","奶油"],
    "胖虎": ["曲奇","wolfie"],
    "豆包": ["madi","donny"],
    "辛巴": ["opao","mocha1"],
    "雪哈": [],
    "麻薯": ["小七","福来"],
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
