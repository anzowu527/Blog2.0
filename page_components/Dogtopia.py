# page_components/Dogtopia.py
from topia_common import render_topia_page

DATA_PATH = "data/combined.csv"

def main():
    render_topia_page(
        data_path=DATA_PATH,
        bucket="annablog",
        root_prefix="images/dogtopia/",
        species="Dog",
        platforms=("xhs","rover"),
        route_param="dog",
        title_text="🐶 Welcome to Dogtopia",
        title_css_class="dogtopia-title",
    )

if __name__ == "__main__":
    main()
