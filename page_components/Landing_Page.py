import streamlit as st
import streamlit.components.v1 as components
from image_config import BASE_IMAGE_URL
from get_s3_images import _safe_join_url  # uses URL-safe join with proper quoting

def main():
    PROFILE_KEY = "images/landing/anqi1.webp"
    QR_KEY      = "images/landing/vx.webp"

    profile_url = _safe_join_url(BASE_IMAGE_URL, PROFILE_KEY)
    qr_url = _safe_join_url(BASE_IMAGE_URL, QR_KEY)
    st.markdown("""
    <style>
    /* kill the default Streamlit chrome spacing */
    header[data-testid="stHeader"]{height:0; min-height:0; visibility:hidden;}
    [data-testid="stToolbar"]{display:none;}
    #MainMenu, footer {visibility:hidden;}
    [data-testid="stAppViewContainer"] > .main, 
    [data-testid="block-container"]{
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    components.html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css?family=American+Typewriter&display=swap');

        :root {{
        /* controls vertical space between curved title and card */
        /* keep gap legal (>= 0) */
        --title-card-gap: clamp(0px, 4vw, 72px);
        /* use this for controlled overlap */
        --title-card-overlap: clamp(-80px, -8vw, -70px);
        }}
        
        html, body {{
          height: 100%;
          margin: 0; padding: 0;
          background-color: #ffeada;
          overflow:hidden;
        }}

        /* === PAGE CONTAINER === */
        .page {{
          width: 100%;
          max-width: 1000px;
          margin: 0 auto;
          min-height: 100vh;
          padding: 0px 0px 0px 0px;
          display: grid;
          grid-template-rows: 1fr auto;
          align-items: center;
          overflow: visible;
        }}

        .center-wrap {{
          position: relative;
          display: flex;
          align-items: top;
          justify-content: top;
          overflow: hidden;
          min-height: 720px;
          padding-top: 0; 
        }}

        /* Stack = title (SVG) above card with fixed-scale gap */
        .stack {{
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--title-card-gap);
          width: 100%;
        }}

        /* Curved title now sits in normal flow */
        .arc-title {{
          width: min(92vw, 640px);
          height: auto;
          pointer-events: none;
          overflow: visible;
        }}

        /* Make arc text responsive without touching your look on desktop */
        .arc-title .arc-text {{
          font-family: 'American Typewriter', serif;
          font-weight: 800;
          letter-spacing: 2px;
          font-size: clamp(28px, 6vw, 52px);
        }}

        /* Card wrapper no longer nudged */
        .card-wrap {{ transform: none; margin-top: var(--title-card-overlap);}}

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
        .social-icons {{ margin-top: 15px; }}
        .social-icons a {{
          margin: 0 15px;
          font-size: 30px;
          color: white;
          text-decoration: none;
        }}
        .social-icons a:hover {{ color: #ffd5a4; }}

        /* Hints */
        .hint {{
          transform: translateY 5px;
          font-family: 'American Typewriter', serif;
          text-align: center;
          color: #7a5a4b;
          opacity: .95;
        }}
        .hint small {{
          display: block;
          margin-top: 4px;
          font-size: 13px;
          color: #a27763;
        }}
        .desktop-hint {{ display: none; }}
        .mobile-hint  {{ display: block; }}

        /* Mobile tweaks: keep everything inside, give a bit more top room */
        @media (max-width: 720px) {{
          .center-wrap {{ min-height: 680px; }}
          .arc-title   {{ width: min(96vw, 600px); }}
          body{{ padding-top: max(0px, env(safe-area-inset-top)); }}
          .page{{ transform: translateY(-60px); }}
          .card-wrap{{ transform: scale(.68); transform-origin: top center; }}
          .hint{{ transform: translateY(-280px); }}

        }}
        @media (max-width: 480px) {{
          .center-wrap {{ min-height: 640px; }}
          .arc-title   {{ width: 96vw; }}
          body{{ padding-top: max(0px, env(safe-area-inset-top)); }}
        }}

        /* Safety for very short screens */
        @media (max-height: 640px) {{
          .center-wrap {{ min-height: 680px; }}
        }}

        /* WeChat modal */
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
          width: 340px;
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
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 9998;
        }}
        </style>

        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

        <div class="page">
          <div class="center-wrap">
            <div class="stack">
              <!-- Curved title (now in flow, not absolutely positioned) -->
              <svg class="arc-title"
                   viewBox="0 -40 600 240"
                   preserveAspectRatio="xMidYMid meet"
                   aria-hidden="true"
                   xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <path id="arcPath" d="M-100 100 A 350 280 0 0 1 600 100" />
                  <linearGradient id="pawpaw" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%"   stop-color="#f4cbba"/>
                    <stop offset="35%"  stop-color="#c8a18f"/>
                    <stop offset="70%"  stop-color="#a27763"/>
                    <stop offset="100%" stop-color="#5a3b2e"/>
                  </linearGradient>
                  <filter id="glow" filterUnits="userSpaceOnUse" x="-150" y="-150" width="900" height="400">
                    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur"/>
                    <feMerge>
                      <feMergeNode in="blur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                <g transform="translate(40,190)">
                  <text class="arc-text" filter="url(#glow)">
                    <textPath href="#arcPath" startOffset="50%" text-anchor="middle"
                              stroke="#ffeada" stroke-width="3" fill="none">
                      Welcome to Paw🐾Paw Homestay
                    </textPath>
                  </text>
                  <text class="arc-text">
                    <textPath href="#arcPath" startOffset="50%" text-anchor="middle" fill="url(#pawpaw)">
                      Welcome to Paw🐾Paw Homestay
                    </textPath>
                  </text>
                </g>
              </svg>

              <!-- Card -->
              <div class="card-wrap">
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
          </div>

          <!-- Hints -->
          <div class="hint desktop-hint">⬅︎ Click the tabs on the left to explore
            <small>Kingdom Stats · Dogtopia · Catopia · Sheltopia · Members</small>
          </div>
          <div class="hint mobile-hint">☰ Open the menu to explore
            <small>Use the sidebar button to navigate</small>
          </div>
        </div>

        <!-- Modal -->
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
          if (overlay) overlay.addEventListener("click", hideWechatQR);
          if (closeBtn) closeBtn.addEventListener("click", hideWechatQR);
        }});
        </script>
        """,
        height=780,   # a tiny bit taller helps short devices, but not required
        scrolling=True
    )

if __name__ == "__main__":
    main()
