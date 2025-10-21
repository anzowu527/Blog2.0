# page_components/stories/dog_stories.py
SHELTER_STORIES = {
    "annabelle": """
**annabelle** is our fluffy cloud of joy. Ever since his first visit, he's captured hearts...
""",
    "baron": """
**Archie** is an explorer at heart. He's always the first to investigate new toys...
""",
    "bart": """
**Milo** is the quiet charmer. With those deep eyes and gentle paws...
""",
    # add more...
}

DEFAULT_STORY = "*This dog's story is still being written. Stay tuned!*"

def get_story(name: str) -> str:
    return SHELTER_STORIES.get((name or "").lower(), DEFAULT_STORY)
