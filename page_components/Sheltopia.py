# page_components/Sheltopia.py
from topia_common import render_topia_page

DATA_PATH = "data/combined.csv"

def main():
    render_topia_page(
        data_path=DATA_PATH,
        bucket="annablog",
        root_prefix="images/shelter/",
        species="Dog",                    
        platforms=("shelter",),         
        route_param="shelter",
        title_text="🏠 Welcome to Sheltopia",
        title_css_class="sheltopia-title",
    )

if __name__ == "__main__":
    main()
