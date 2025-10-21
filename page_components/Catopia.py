# page_components/Catopia.py
from topia_common import render_topia_page

DATA_PATH = "data/combined.csv"

def main():
    render_topia_page(
        data_path=DATA_PATH,
        bucket="annablog",
        root_prefix="images/catopia/",
        species="Cat",
        route_param="cat",
        title_text="🐱 Welcome to Catopia",
        title_css_class="catopia-title",
    )

if __name__ == "__main__":
    main()
