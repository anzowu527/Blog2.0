# streamlit_app.py
import os
import streamlit as st
import logging

st.set_page_config(
    page_title="Zoolotopia Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Env + feature flags (NEW) ---
ENV = os.getenv("APP_ENV", st.secrets.get("ENV", "prod")).lower()
# If you ever want to test admin on a remote box, set this to true in secrets or env.
ADMIN_ALLOW_REMOTE = bool(
    str(os.getenv("ADMIN_ALLOW_REMOTE", st.secrets.get("ADMIN_ALLOW_REMOTE", "false"))).lower()
    in {"1","true","yes","on"}
)

# --- Global CSS theme ---
st.markdown("""
<style>
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
.main, .block-container {
  background: #ffeada !important;
}
.main .block-container, [data-testid="block-container"] {
  max-width: 100% !important;
  width: 100% !important;
  padding-left: 12px !important;
  padding-right: 12px !important;
}
header[data-testid="stHeader"] {
  background-color: #ffeada !important;
  box-shadow: none !important;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
  background-color: #c8a18f !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
  color: white !important;
}
section[data-testid="stSidebar"] button {
  background-color: #ffeada !important;
  color: #5a3b2e !important;
  border-radius: 8px !important;
  border: none !important;
  font-weight: bold !important;
}
section[data-testid="stSidebar"] button:hover {
  background-color: #f4cbba !important;
  color: #3a251c !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- Auth ----------
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def set_params(**updates):
    """Merge-style setter for query params. Pass None to remove a key."""
    qp = st.query_params

    for k, v in updates.items():
        if v is None:
            qp.pop(k, None)
        else:
            qp[k] = str(v)

    st.query_params = qp

def go(target: str, **extra):
    set_params(page=target, **extra)

# --- Session flags ---
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False
if "auth_error" not in st.session_state:
    st.session_state.auth_error = ""

# In production, unless explicitly allowed, ensure the admin flag is OFF (defense-in-depth).
if ENV != "local" and not ADMIN_ALLOW_REMOTE:
    st.session_state.admin_authed = False

# ---------- Sidebar ----------
with st.sidebar:
    # Environment ribbon (NEW)
    if ENV == "local":
        st.caption("🛠️ Local dev mode — admin pages enabled")

    st.button("🏠 Main", use_container_width=True, on_click=go, args=("landing",))
    st.markdown("---")

    st.markdown("## Information")

    if st.button("📖 About Pawpaw", use_container_width=True):
        set_params(page="about", dog=None, cat=None, shelter=None); st.rerun()

    if st.button("🛎️ Services", use_container_width=True):
        set_params(page="service_info", dog=None, cat=None, shelter=None); st.rerun()

    if st.button("📈 Kingdom Stats", use_container_width=True):
        set_params(page="kingdom_stats", dog=None, cat=None, shelter=None); st.rerun()
    
    st.markdown("## Pawpaw Clients")

    if st.button("🐶 Dogtopia", use_container_width=True):
        set_params(page="dogtopia", dog=None, cat=None, shelter=None); st.rerun()
    if st.button("🐱 Catopia", use_container_width=True):
        set_params(page="catopia", dog=None, cat=None, shelter=None); st.rerun()
    if st.button("🏡 Sheltopia", use_container_width=True):
        set_params(page="sheltopia", dog=None, cat=None, shelter=None); st.rerun()
    if st.button("🧑‍🤝‍🧑 Members", use_container_width=True):
        set_params(page="members", dog=None, cat=None, shelter=None); st.rerun()

    st.markdown("---")

    # Show Admin section ONLY when allowed
    admin_section_allowed = (ENV == "local") or ADMIN_ALLOW_REMOTE

    if admin_section_allowed:
        st.markdown("## 🔐 Admin")
        if st.session_state.admin_authed or ENV == "local":
            # In local, auto-allow admin to make dev easy
            st.session_state.admin_authed = True

            st.button("📊 Data Visualization", use_container_width=True, on_click=go, args=("data_visualization",))
            st.button("📝 Data Editor", use_container_width=True, on_click=go, args=("data_editor",))
            st.button("📅 Calendar", use_container_width=True, on_click=go, args=("calendar",))
            st.button("💰 Earnings and Expenses", use_container_width=True, on_click=go, args=("earnings_and_expenses",))
            st.button("🔓 Log out Admin", use_container_width=True, on_click=lambda: st.session_state.update(admin_authed=False))
        else:
            pwd = st.text_input("Admin password", type="password", key="admin_pwd")
            def try_unlock():
                if ADMIN_PASSWORD and pwd == ADMIN_PASSWORD:
                    st.session_state.admin_authed = True
                    st.session_state.auth_error = ""
                else:
                    st.session_state.auth_error = "Incorrect password."
            st.button("Unlock Admin", use_container_width=True, on_click=try_unlock)
            if st.session_state.auth_error:
                st.error(st.session_state.auth_error)

# ---------- Router helpers ----------
def qp_get(name, default=None):
    """Robustly get a single query param value across Streamlit versions."""
    val = None
    try:
        val = st.query_params.get(name)
    except Exception:
        pass
    if val is None:
        try:
            val = st.query_params.get(name)
        except Exception:
            val = None
    if isinstance(val, list):
        val = val[0] if val else None
    return default if val in (None, "") else val

# ---------- Router ----------
page = (qp_get("page", "landing") or "landing").lower()
dog  = qp_get("dog", "")
cat  = qp_get("cat", "")
shelter = qp_get("shelter", "")

# Deep-link override: if a specific animal/page is requested, force that detail page
if dog and page != "dog":
    page = "dog"
elif cat and page != "cat":
    page = "cat"
elif shelter and page != "shelter":
    page = "shelter"

# --- Helper: admin page guard (NEW) ---
def guard_admin_page():
    # If not local AND not explicitly allowed, block hard.
    if ENV != "local" and not ADMIN_ALLOW_REMOTE:
        st.warning("Admin area is disabled in production.")
        from page_components import Landing_Page
        Landing_Page.main()
        return False
    # If remote but allowed, still require session auth (unless local)
    if not st.session_state.admin_authed and ENV != "local":
        st.warning("Admin area is locked.")
        from page_components import Landing_Page
        Landing_Page.main()
        return False
    return True

# --- Routes ---
if page == "landing":
    from page_components import Landing_Page
    Landing_Page.main()

elif page == "dogtopia":
    from page_components import Dogtopia
    Dogtopia.main()

elif page == "catopia":
    from page_components import Catopia
    Catopia.main()

elif page == "sheltopia":
    from page_components import Sheltopia
    Sheltopia.main()

elif page == "kingdom_stats":
    from page_components import Kingdom_Stats
    Kingdom_Stats.main()

elif page == "about":
    from page_components import About_Pawpaw
    About_Pawpaw.main()

elif page == "service_info":
    from page_components import Service_Info
    Service_Info.main()


elif page == "members":
    from page_components import Members
    Members.main()

elif page == "data_visualization":
    if guard_admin_page():
        from page_components import Data_Visualization
        Data_Visualization.main()

elif page == "data_editor":
    if guard_admin_page():
        from page_components import Data_Editor
        Data_Editor.main()

elif page == "calendar":
    if guard_admin_page():
        from page_components import Calendar
        Calendar.main()

elif page == "earnings_and_expenses":
    if guard_admin_page():
        from page_components import Earnings_and_Expenses
        Earnings_and_Expenses.main()

elif page == "dog":
    from page_components import Dog_Page as Dog_Page_Module
    dog_param = qp_get("dog", None)
    if not dog_param:
        st.warning("No dog specified. Add ?page=dog&dog=Name to the URL.")
    else:
        Dog_Page_Module.main(dog_param)

elif page == "cat":
    from page_components import Cat_Page as Cat_Page_Module
    cat_param = qp_get("cat", None)
    if not cat_param:
        st.warning("No cat specified. Add ?page=cat&cat=Name to the URL.")
    else:
        Cat_Page_Module.main(cat_param)

elif page == "shelter":
    from page_components import Shelter_Page as Shelter_Page_Module
    shelter_param = qp_get("shelter", None)
    if not shelter_param:
        st.warning("No shelter pet specified. Add ?page=shelter&shelter=Name to the URL.")
    else:
        Shelter_Page_Module.main(shelter_param)

else:
    from page_components import Landing_Page
    Landing_Page.main()
