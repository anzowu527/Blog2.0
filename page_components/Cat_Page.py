# page_components/Cat_Page.py
import streamlit as st
from pet_pages_common import render_pet_detail_page

def _get_cat_story(name: str) -> str:
    try:
        import importlib
        from .stories import cat_stories
        importlib.reload(cat_stories)  # hot-reload while developing
        return cat_stories.get_story(name)
    except Exception:
        return ""

def main(cat_name: str):
    render_pet_detail_page(
        person_name=cat_name,
        bucket="annablog",
        root_prefix="images/catopia",
        title_text=f"🐱 Story of {cat_name.capitalize()}",
        page_param="cat",
        back_page="catopia",
        story_getter=_get_cat_story,  # <-- now cats have stories too
    )

if __name__ == "__main__":
    q = st.query_params.get("cat") if hasattr(st, "query_params") else None
    val = q[0] if isinstance(q, list) else (q if isinstance(q, str) else None)
    if val:
        main(val)
    else:
        st.info("Pass ?page=cat&cat=Name in the URL.")
