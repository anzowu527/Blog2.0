# page_components/Shelter_Page.py
import streamlit as st
from pet_pages_common import render_pet_detail_page  # same common component Dog/Cat use

def _get_shelter_story(name: str) -> str:
    try:
        import importlib
        from .stories import shelter_stories
        importlib.reload(shelter_stories)  # hot reload while developing
        return shelter_stories.get_story(name)
    except Exception:
        return ""  # fall back to default message in the common renderer

def main(shelter_name: str):
    render_pet_detail_page(
        person_name=shelter_name,
        bucket="annablog",
        root_prefix="images/shelter",   # S3 folder for shelter images
        title_text=f"🏠 Story of {shelter_name.capitalize()}",
        page_param="shelter",           # query param name used in URLs
        back_page="sheltopia",          # where the Back button should go
        story_getter=_get_shelter_story # <-- wire shelter stories
    )

if __name__ == "__main__":
    q = st.query_params.get("shelter") if hasattr(st, "query_params") else None
    val = q[0] if isinstance(q, list) else (q if isinstance(q, str) else None)
    if val:
        main(val)
    else:
        st.info("Pass ?page=shelter&shelter=Name in the URL.")
