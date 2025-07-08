import streamlit as st
import os
import glob
import frontmatter
import markdown

RECIPE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recipes"))

def load_recipes():
    files = glob.glob(os.path.join(RECIPE_DIR, "*.md"))
    recipes = []
    for path in files:
        post = frontmatter.load(path)
        recipes.append({
            "title": post.get("title", os.path.basename(path)),
            "tags": post.get("tags", []),
            "content": post.content,
            "filename": os.path.basename(path)
        })
    return recipes

st.title("🍲 Rezeptdatenbank")
recipes = load_recipes()
all_tags = sorted({tag for recipe in recipes for tag in recipe["tags"]})

selected_tags = st.multiselect("Nach Tags filtern", options=all_tags)

filtered = [
    r for r in recipes
    if all(tag in r["tags"] for tag in selected_tags)
]

for recipe in filtered:
    with st.expander(recipe["title"]):
        st.markdown(f"**Tags:** {', '.join(recipe['tags'])}")
        st.markdown(recipe["content"])

if not filtered:
    st.info("Keine Rezepte gefunden.")