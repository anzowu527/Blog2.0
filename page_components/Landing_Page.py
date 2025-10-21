import streamlit as st
import streamlit.components.v1 as components
from image_config import BASE_IMAGE_URL
from get_s3_images import _safe_join_url  # uses URL-safe join with proper quoting

def main():
    # S3 keys for your assets
    PROFILE_KEY = "images/landing/anqi1.webp"
    QR_KEY      = "images/landing/vx.webp"

    # Public HTTPS URLs (e.g., https://<cloudfront-or-bucket-site>/<key>)
    profile_url = _safe_join_url(BASE_IMAGE_URL, PROFILE_KEY)
    qr_url = _safe_join_url(BASE_IMAGE_URL, QR_KEY)

    # Make Streamlit's outer page match your landing bg
    st.markdown("""
    <style>
    /* App background (main area) */
    .stApp, [data-testid="stAppViewContainer"], 
    [data-testid="stAppViewContainer"] > .main {
      background: #ffeada !important;
    }
    /* Remove Streamlit’s default page padding so the card sits centered */
    [data-testid="block-container"]{
      padding-top: 0 !important;
      padding-bottom: 0 !important;
    }
    /* Remove the little status bar gradient at very top (optional) */
    header[data-testid="stHeader"] { background: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.empty():
        components.html(
            f"""
            <style>
            @import url('https://fonts.googleapis.com/css?family=American+Typewriter&display=swap');

            html, body {{
                height: 100%;
                margin: 0;
                padding: 0;
                background-color: #ffeada;
            }}
            .container {{
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: visible !important; /* allow the arc to show */
            }}

            .card-wrap {{
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: visible !important; /* <--- add this line */
            }}

            .stApp {{
                overflow: visible !important; /* make Streamlit’s main area allow overflow */
            }}

            /* The curved title SVG sits above the card */
            .arc-title {{
                position: absolute;
                /* Push it above the top edge of the card */
                top: -50px;
                left: 50%;
                transform: translateX(-50%);
                width: min(88vw, 640px);
                height: auto;
                pointer-events: none; /* clicks pass through to the card */
            }}

            .card {{
                background: #c8a18f;
                border: 4px solid #ffeada;
                box-shadow: 0 6px 10px #f4cbba;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                font-family: 'American Typewriter', serif;
                color: white;
                max-width: 320px;
            }}
            .avatar {{
                width: 180px;
                height: 180px;
                border-radius: 50%;
                border: 5px solid white;
                object-fit: cover;
            }}
            .name {{
                font-size: 28px;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 18px;
                color: #ffeada;
                margin-bottom: 10px;
            }}
            .divider {{
                border: none;
                height: 2px;
                background-color: #ffeada;
                margin: 20px auto;
                width: 60%;
                opacity: 0.7;
            }}
            .social-icons {{
                margin-top: 15px;
            }}
            .social-icons a {{
                margin: 0 15px;
                font-size: 30px;
                color: white;
                text-decoration: none;
            }}
            .social-icons a:hover {{
                color: #ffd5a4;
            }}
            .wechat-popup {{
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 9999;
                background: white;
                border-radius: 10px;
                padding: 20px 20px 30px 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                text-align: center;
            }}
            .wechat-popup img {{
                width: 200px;
                height: auto;
                display: block;
                margin: 0 auto 15px auto;
            }}
            .wechat-popup button {{
                background-color: #c87b57;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 18px;
                font-weight: bold;
                width: 100%;
            }}
            .overlay {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9998;
            }}
            /* --- helper hint under the card --- */
            .hint {{
            margin-top: -100px;
            font-family: 'American Typewriter', serif;
            text-align: center;
            color: #7a5a4b;          /* warm cocoa */
            opacity: .95;
            }}
            .hint small {{
            display: block;
            margin-top: 4px;
            font-size: 13px;
            color: #a27763;
            }}

            /* Desktop vs mobile phrasing */
            .desktop-hint {{ display: block; }}
            .mobile-hint  {{ display: none; }}
          

            /* Small screens: bring the arc a little closer and shrink text slightly */
            @media (max-width: 480px) {{
                .arc-title {{ top: -90px; }}
            }}
            </style>

            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

            <div class="container">
                <div class="card-wrap">
                    <!-- Curved themed title (flatter + full text visible) -->
                    <svg class="arc-title"
                        viewBox="0 -40 600 240"
                        preserveAspectRatio="xMidYMid meet"
                        aria-hidden="true"
                        style="overflow:visible"
                        xmlns="http://www.w3.org/2000/svg"
                        xmlns:xlink="http://www.w3.org/1999/xlink">
                    <defs>

                        <!-- Flatter arc: higher y value = gentler curve -->
                        <path id="arcPath" d="M-100 100 A 350 280 0 0 1 600 100" />

                        <!-- Pawpaw gradient -->
                        <linearGradient id="pawpaw" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%"   stop-color="#f4cbba"/>
                        <stop offset="35%"  stop-color="#c8a18f"/>
                        <stop offset="70%"  stop-color="#a27763"/>
                        <stop offset="100%" stop-color="#5a3b2e"/>
                        </linearGradient>

                        <!-- Glow outline -->
                        <filter id="glow" filterUnits="userSpaceOnUse" x="-150" y="-150" width="900" height="400">
                        <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur"/>
                        <feMerge>
                            <feMergeNode in="blur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                        </filter>
                    </defs>
                    <g transform="translate(40,85)">
                        <text font-family="'American Typewriter', serif" font-size="52" font-weight="800" letter-spacing="2" filter="url(#glow)">
                        <textPath href="#arcPath" xlink:href="#arcPath" startOffset="50%" text-anchor="middle"
                                    stroke="#ffeada" stroke-width="3" fill="none">
                            Welcome to Paw🐾Paw Homestay
                        </textPath>
                        </text>

                        <text font-family="'American Typewriter', serif" font-size="52" font-weight="800" letter-spacing="2">
                        <textPath href="#arcPath" xlink:href="#arcPath" startOffset="50%" text-anchor="middle" fill="url(#pawpaw)">
                            Welcome to Paw🐾Paw Homestay
                        </textPath>
                        </text>
                    </g>
                    
                    </svg>

                    <div class="card">
                        <img src="{profile_url}" class="avatar" alt="Profile" />
                        <div class="name">AnQi Wu</div>
                        <div class="title">Pawpaw 🫧 CEO</div>
                        <hr class="divider">
                        <div class="social-icons">
                            <a href="https://www.youtube.com/@anzowoo/videos" target="_blank" title="YouTube"><i class="fab fa-youtube"></i></a>
                            <a href="#" id="wechat-icon" title="WeChat"><i class="fab fa-weixin"></i></a>
                            <a href="https://www.linkedin.com/in/anqi-wu-6a2991236/" target="_blank" title="LinkedIn"><i class="fab fa-linkedin"></i></a>
                            <a href="https://github.com/anzowu527" target="_blank" title="GitHub"><i class="fab fa-github"></i></a>
                        </div>
                    </div>
                </div>
            </div>

            <div class="hint desktop-hint">⬅︎ Click the tabs on the left to explore
                <small>Kingdom Stats · Dogtopia · Catopia · Sheltopia · Members</small>
                </div>
                <div class="hint mobile-hint">☰ Open the menu to explore
                <small>Use the sidebar button to navigate</small>
            </div>

            <div class="overlay" id="overlay"></div>
            <div class="wechat-popup" id="wechat-popup">
                <img src="{qr_url}" alt="WeChat QR Code" />
                <button id="close-btn">Close</button>
            </div>

            <script>
            window.addEventListener("DOMContentLoaded", function () {{
                const wechatIcon = document.getElementById("wechat-icon");
                const popup = document.getElementById("wechat-popup");
                const overlay = document.getElementById("overlay");
                const closeBtn = document.getElementById("close-btn");

                function showWechatQR() {{
                    popup.style.display = "block";
                    overlay.style.display = "block";
                    document.body.style.overflow = "hidden";
                }}

                function hideWechatQR() {{
                    popup.style.display = "none";
                    overlay.style.display = "none";
                    document.body.style.overflow = "auto";
                }}

                if (wechatIcon) {{
                    wechatIcon.addEventListener("click", function (e) {{
                        e.preventDefault();
                        showWechatQR();
                    }});
                }}
                if (overlay) {{
                    overlay.addEventListener("click", hideWechatQR);
                }}
                if (closeBtn) {{
                    closeBtn.addEventListener("click", hideWechatQR);
                }}
            }});
            </script>
            """,
            height=750,
            scrolling=True
        )


if __name__ == "__main__":
    main()
