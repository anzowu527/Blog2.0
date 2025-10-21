# page_components/Dog_Page.py
import streamlit as st
from pet_pages_common import render_pet_detail_page

def _get_dog_story(name: str) -> str:
    try:
        import importlib
        from .stories import dog_stories
        importlib.reload(dog_stories)
        return dog_stories.get_story(name)
    except Exception:
        return ""

def main(dog_name: str):
    render_pet_detail_page(
        person_name=dog_name,
        bucket="annablog",
        root_prefix="images/dogtopia",
        title_text=f"🐶 Story of {dog_name.capitalize()}",
        page_param="dog",
        back_page="dogtopia",
        story_getter=_get_dog_story,
    )

if __name__ == "__main__":
    q = st.query_params.get("dog") if hasattr(st, "query_params") else None
    val = q[0] if isinstance(q, list) else (q if isinstance(q, str) else None)
    if val:
        main(val)
    else:
        st.info("Pass ?page=dog&dog=Name in the URL.")
