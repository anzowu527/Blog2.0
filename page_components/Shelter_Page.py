# page_components/Shelter_Page.py
from __future__ import annotations
import streamlit as st
from typing import Dict, List
from pet_pages_common import render_pet_detail_page  # shared renderer

# ---------- Inline "best friends" for shelters (fill right-hand lists) ----------
# Keys are LOWERCASED for robust lookup.
_FRIENDS: Dict[str, List[str]] = {
    "annabelle": ["willow","chloe"],
    "baron": [],
    "bart": [],
    "bonnie": [],
    "booberry": [],
    "brotherpup": [],
    "canada": ["obi","stitch"],
    "cassian": ["fury"],
    "chloe": ["willow","annabelle"],
    "conrad": [],
    "daisy": ["nessa","lauryn","valentina","emma"],
    "dax": [],
    "duke": ["tommy"],
    "emma": ["nessa","lauryn","valentina","daisy"],
    "eva": ["naomi"],
    "fury": ["cassian","suki"],
    "honeydew": [],
    "jafar": [],
    "kelce": ["tapi"],
    "king": [],
    "lady": [],
    "lauryn": ["nessa","emma","valentina","daisy"],
    "lilac": [],
    "naomi": ["eva"],
    "nessa": ["lauryn","emma","valentina","daisy"],
    "obi": ["canada"],
    "penny1": [],
    "rex": [],
    "stitch": ["canada"],
    "suki": ["fury"],
    "tapi": ["keice"],
    "tennessee": [],
    "tommy": ["duke"],
    "valentina": ["nessa","emma","lauryn","daisy"],
    "willow": ["chloe","annabelle"],
    "zoe": [],
}

def _get_shelter_story(name: str) -> str:
    try:
        import importlib
        from .stories import shelter_stories
        importlib.reload(shelter_stories)  # hot reload while developing
        return shelter_stories.get_story(name)
    except Exception:
        return ""  # fall back to default message in the common renderer

def _get_shelter_friends(name: str) -> List[str]:
    """Return best-friend names for avatar chips (case-insensitive)."""
    if not name:
        return []
    return _FRIENDS.get(name.strip().lower(), [])

def main(shelter_name: str):
    render_pet_detail_page(
        person_name=shelter_name,
        bucket="annablog",
        root_prefix="images/shelter",   # S3 folder for shelter images
        title_text=f"🏠 Story of {shelter_name}",  # keep original casing
        page_param="shelter",
        back_page="sheltopia",
        story_getter=_get_shelter_story,
        friends_getter=_get_shelter_friends,  # ← enable chips under the card
        # max_photos=10,  # optional tweak
    )

if __name__ == "__main__":
    q = st.query_params.get("shelter") if hasattr(st, "query_params") else None
    val = q[0] if isinstance(q, list) else (q if isinstance(q, str) else None)
    if val:
        main(val)
    else:
        st.info("Pass ?page=shelter&shelter=Name in the URL.")
