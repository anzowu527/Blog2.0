# streamlit_app.py
import os
import streamlit as st

st.set_page_config(
    page_title="Zoolotopia Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
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

def set_params(**updates):
    # Merge, don't overwrite (supports both new and legacy APIs)
    try:
        qp = dict(st.query_params)
    except Exception:
        qp = st.experimental_get_query_params()

    for k, v in updates.items():
        if v is None:
            # REMOVE the key if caller passes None
            qp.pop(k, None)
            continue
        qp[k] = str(v)

    try:
        st.query_params = qp
    except Exception:
        st.experimental_set_query_params(**qp)


def go(target: str, **extra):
    set_params(page=target, **extra)

if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False
if "auth_error" not in st.session_state:
    st.session_state.auth_error = ""

# ---------- Sidebar ----------
with st.sidebar:
    st.button("🏠 Landing", use_container_width=True, on_click=go, args=("landing",))
    st.markdown("---")

    st.markdown("## 🌐 Public")
    if st.button("🐶 Dogtopia", use_container_width=True):
        set_params(page="dogtopia", dog=None); st.rerun()    
    st.button("🐱 Catopia",    use_container_width=True, on_click=go, args=("catopia",))
    st.button("🏡 Sheltopia",  use_container_width=True, on_click=go, args=("sheltopia",))
    st.markdown("---")

    st.markdown("## 🔐 Admin")
    if st.session_state.admin_authed:
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
            val = st.experimental_get_query_params().get(name)
        except Exception:
            val = None
    if isinstance(val, list):
        val = val[0] if val else None
    return default if val in (None, "") else val


# ---------- Router ----------
page = (qp_get("page", "landing") or "landing").lower()
dog  = qp_get("dog", "")

if dog and page != "dog":
    page = "dog"

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

elif page == "data_visualization":
    if st.session_state.admin_authed:
        from page_components import Data_Visualization1
        Data_Visualization1.main()
    else:
        st.warning("Admin area is locked.")
        from page_components import Landing_Page
        Landing_Page.main()

elif page == "data_editor":
    if st.session_state.admin_authed:
        from page_components import Data_Editor
        Data_Editor.main()
    else:
        st.warning("Admin area is locked.")
        from page_components import Landing_Page
        Landing_Page.main()

elif page == "calendar":
    if st.session_state.admin_authed:
        from page_components import Calendar
        Calendar.main()
    else:
        st.warning("Admin area is locked.")
        from page_components import Landing_Page
        Landing_Page.main()

elif page == "earnings_and_expenses":
    if st.session_state.admin_authed:
        from page_components import Earnings_and_Expenses
        Earnings_and_Expenses.main()
    else:
        st.warning("Admin area is locked.")
        from page_components import Landing_Page
        Landing_Page.main()

elif page == "dog":
    from page_components import Dog_Page as Dog_Page_Module
    dog_param = qp_get("dog", None)  # <-- use the helper you already defined
    if not dog_param:
        st.warning("No dog specified. Add ?page=dog&dog=Name to the URL.")
    else:
        Dog_Page_Module.main(dog_param)

else:
    from page_components import Landing_Page
    Landing_Page.main()
