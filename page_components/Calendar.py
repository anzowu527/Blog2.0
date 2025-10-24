# page_components/Calendar.py
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from streamlit_calendar import calendar

def main():
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    st.title("📅 Pet Stays Calendar")


    # ---------- Settings ----------
    DATA_PATH = Path("data/combined.csv")  # adjust if needed
    DATE_COLS = ["Arrival Date", "Departure Date"]

    # ---------- Load & clean ----------
    @st.cache_data
    def load_data(path: Path, mtime: float) -> pd.DataFrame:
        df = pd.read_csv(path)
        for c in DATE_COLS:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce")
        if "Name" in df.columns:
            df["Name"] = df["Name"].astype(str).str.strip()
        if "Type" in df.columns:
            df["Type"] = df["Type"].astype(str).str.strip().str.title()
        if "daily price" in df.columns:
            df["daily price"] = pd.to_numeric(df["daily price"], errors="coerce")
        df = df.dropna(subset=["Arrival Date", "Departure Date"])
        df = df[df["Departure Date"] >= df["Arrival Date"]]
        return df

    if not DATA_PATH.exists():
        st.error(f"CSV not found at {DATA_PATH}. Update DATA_PATH or add your file.")
        st.stop()

    data_mtime = DATA_PATH.stat().st_mtime  # changes when file is updated
    df = load_data(DATA_PATH, data_mtime)

        
    st.markdown("""
    <style>
    /* TEXT INPUTS */
    div[data-testid="stTextInput"] input {
    background: #c8a18f !important;     /* dark brown */
    color: #ffffff !important;
    border: 1px solid #c8a18f !important;
    border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
    color: #f4cbba !important;           /* soft peach */
    }

    /* MULTISELECT (closed control) */
    div[data-testid="stMultiSelect"] > div > div {
    background: #5a3b2e !important;
    color: #ffffff !important;
    border: 1px solid #c8a18f !important;
    border-radius: 8px !important;
    }

    /* MULTISELECT tags */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: #c8a18f !important;
    color: #ffffff !important;
    border: none !important;
    }

    /* MULTISELECT dropdown menu */
    div[data-testid="stMultiSelect"] div[role="listbox"] {
    background: #5a3b2e !important;
    color: #ffffff !important;
    border: 1px solid #c8a18f !important;
    }
    div[data-testid="stMultiSelect"] div[role="option"] {
    color: #ffffff !important;
    }

    /* FOCUS STATES */
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stMultiSelect"] > div > div:focus-within {
    outline: 2px solid #a77d6c !important;
    box-shadow: 0 0 0 1px #a77d6c !important;
    border-color: #a77d6c !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- Filters (ON PAGE) ----------
    with st.container():
        st.subheader("🔎 Filters")
        c1, c2, c3 = st.columns([1.2, 1, 1.2])

        with c1:
            month_str = st.text_input(
                "Jump to month (YYYY-MM)",
                value=datetime.today().strftime("%Y-%m"),
                help="Sets the initial month shown in the calendar."
            )
        with c2:
            types_available = sorted(df["Type"].dropna().unique()) if "Type" in df.columns else []
            type_filter = st.multiselect("Type", options=types_available, default=types_available)
        with c3:
            name_query = st.text_input("Search by name (contains)", "")

    filtered = df.copy()
    if "Type" in filtered.columns and type_filter:
        filtered = filtered[filtered["Type"].isin(type_filter)]
    if name_query:
        filtered = filtered[filtered["Name"].str.contains(name_query, case=False, na=False)]

    # ---------- Event colors ----------
    def color_for_kind(kind: str) -> str:
        """Arrival vs Departure highlight colors."""
        if kind == "Arrival":
            return "#a9dfba"    # green
        if kind == "Departure":
            return "#ffadad"  # red
        return "#3f3f46"

    def emoji_for_species(row) -> str:
        """Dog vs Cat emoji."""
        t = str(row.get("Species", "")).lower()
        if t == "dog":
            return "🐶"
        if t == "cat":
            return "🐱"
        return "🐾"

    # ---------- Build events ----------
    events = []
    for _, r in filtered.iterrows():
        name = r.get("Name", "Unknown")
        arr = r["Arrival Date"].date()
        dep = r["Departure Date"].date()
        nights = (dep - arr).days
        price = r.get("daily price", None)
        price_str = f" • ${float(price):.0f}/d" if pd.notna(price) else ""
        title = f"{emoji_for_species(r)} {name} ({nights}d){price_str}"

        # Arrival (green highlight)
        events.append({
            "title": title,
            "start": arr.isoformat(),
            "end": (arr + timedelta(days=1)).isoformat(),
            "allDay": True,
            "color": color_for_kind("Arrival"),
            "extendedProps": {"Name": name, "Kind": "Arrival", "Nights": nights},
        })

        # Departure (red highlight)
        events.append({
            "title": title,
            "start": dep.isoformat(),
            "end": (dep + timedelta(days=1)).isoformat(),
            "allDay": True,
            "color": color_for_kind("Departure"),
            "extendedProps": {"Name": name, "Kind": "Departure", "Nights": nights},
        })



    # ----- FullCalendar options -----
    options = {
        "initialView": "dayGridMonth",
        "initialDate": pd.Timestamp.today().date().isoformat(),  # or month_str + "-01"
        "height": "auto",
        "contentHeight": "auto",
        "fixedWeekCount": False,
        "expandRows": True,

        # Show a "+ more" link instead of clipping when a day is crowded
        "dayMaxEvents": True,
        "dayMaxEventRows": True,
        "moreLinkClick": "popover",

        # Built-in toolbar with prev/next/today and view switches
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay,listMonth"
        },
    }

    # ----- CSS inside the iframe -----
    custom_css = """
    /* Let month rows expand freely */
    .fc-view-harness, .fc-scroller-harness, .fc-scroller, .fc-daygrid-body {
    height: auto !important;
    max-height: none !important;
    }
    /* Don’t clip lists inside day cells */
    .fc-daygrid-day-events { max-height: none !important; }
    /* Allow multi-line event titles */
    .fc-event-title { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }
    /* Event wrapper overflow */
    .fc-daygrid-event-harness { overflow: visible !important; }

    /* Match page background + thicker warm-brown grid lines */
    .fc, .fc-theme-standard, .fc-theme-standard td, .fc-theme-standard th { background-color: #ffeada !important; }
    .fc-theme-standard td, .fc-theme-standard th { border-color: #c8a18f !important; border-width: 5px !important; }

    /* Toolbar / today (title color) */
    .fc-toolbar-title { color: #5a3b2e !important; }

    /* ---------- STRONG "TODAY" HIGHLIGHT ---------- */
    /* Month view: highlight entire day cell, keep your palette */
    .fc-daygrid-day.fc-day-today .fc-daygrid-day-frame {
    background: #f4cbba !important;          /* peach fill for today */
    border-radius: 10px !important;
    box-shadow:
        inset 0 0 0 3px #5a3b2e,               /* inner dark-brown ring */
        0 0 0 1px #5a3b2e;                      /* outer hairline */
    }
    .fc-daygrid-day.fc-day-today .fc-daygrid-day-number {
    color: #5a3b2e !important;
    font-weight: 800 !important;
    }

    /* Week/Day time-grid views: highlight today's column */
    .fc-timegrid-col.fc-day-today,
    .fc-timeGridWeek-view .fc-timegrid-col.fc-day-today,
    .fc-timeGridDay-view .fc-timegrid-col.fc-day-today {
    background: rgba(244, 203, 186, 0.55) !important;  /* translucent peach */
    }

    /* List views: highlight today's header row */
    .fc-list-day.fc-day-today > .fc-list-day-cushion {
    background: #f4cbba !important;
    color: #5a3b2e !important;
    font-weight: 700 !important;
    }
    """


    # IMPORTANT: include mtime so a CSV save remounts iframe even within same month
    state = calendar(
        events=events,
        options=options,
        custom_css=custom_css,
        key=f"calendar-{int(data_mtime)}"   # still remounts when CSV updates
    )

    if state and state.get("callbackTriggered") == "eventClick":
        evt = state.get("event", {})
        kind = evt.get("extendedProps", {}).get("Kind", "")
        st.success(f"Clicked: {evt.get('title','')} ({kind})")

   # ---------- Upcoming arrivals (table) ----------
    today = pd.Timestamp.today().normalize()

    def species_emoji_from_row(r):
        t = str(r.get("Species") or r.get("Type") or "").lower()
        return "🐶" if t == "dog" else ("🐱" if t == "cat" else "🐾")

    upcoming = filtered[filtered["Arrival Date"].dt.normalize() >= today].copy()

    if not upcoming.empty:
        # Ensure numeric types present in the data
        for col in ["Duration", "daily price", "Price", "Payment Received"]:
            if col in upcoming.columns:
                upcoming[col] = pd.to_numeric(upcoming[col], errors="coerce")

        # If total Price is missing, compute from data only (daily price × Duration)
        if "Price" not in upcoming.columns and {"daily price", "Duration"}.issubset(upcoming.columns):
            upcoming["Price"] = upcoming["daily price"] * upcoming["Duration"]

        display = pd.DataFrame({
            "Pet": upcoming.apply(lambda r: f"{species_emoji_from_row(r)} {r['Name']}", axis=1),
            "Arrival": upcoming["Arrival Date"].dt.strftime("%Y-%m-%d"),
            "Departure": upcoming["Departure Date"].dt.strftime("%Y-%m-%d"),
        })

        if "Duration" in upcoming.columns:
            display["Duration"] = upcoming["Duration"].astype("Int64")
        if "Price" in upcoming.columns:
            display["Price (total)"] = upcoming["Price"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
        if "daily price" in upcoming.columns:
            display["Price/day"] = upcoming["daily price"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "")
        if "Payment Received" in upcoming.columns:
            display["Payment Received"] = upcoming["Payment Received"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")

        # Sort soonest first
        display = display.sort_values(["Arrival", "Pet"], kind="mergesort")

        # ---- Dynamically size dataframe so it doesn't scroll ----
        # approximate row + header heights (tweak if needed for your theme)
        ROW_PX = 34
        HEADER_PX = 38
        PADDING_PX = 12
        df_height = HEADER_PX + ROW_PX * len(display) + PADDING_PX

        st.subheader("📅 Upcoming Arrivals")
        st.dataframe(display, use_container_width=True, hide_index=True, height=int(df_height))
    else:
        st.subheader("📅 Upcoming Arrivals")
        st.info("No upcoming arrivals with the current filters.")


    # ---------- Arrived but NOT fully paid ----------
    st.subheader("💸 Arrived — Outstanding Balance")

    arrears = filtered.copy()

    # Ensure types
    for col in ["Duration", "daily price", "Price", "Payment Received"]:
        if col in arrears.columns:
            arrears[col] = pd.to_numeric(arrears[col], errors="coerce")

    # If total Price is missing, compute from available data (daily price × Duration)
    if "Price" not in arrears.columns and {"daily price", "Duration"}.issubset(arrears.columns):
        arrears["Price"] = arrears["daily price"] * arrears["Duration"]

    # Fallback: if Price column exists but some rows are NaN and we have inputs, fill them
    if "Price" in arrears.columns and {"daily price", "Duration"}.issubset(arrears.columns):
        mask_price_na = arrears["Price"].isna() & arrears["daily price"].notna() & arrears["Duration"].notna()
        arrears.loc[mask_price_na, "Price"] = arrears.loc[mask_price_na, "daily price"] * arrears.loc[mask_price_na, "Duration"]

    # Define "already arrived" = Arrival Date <= today (normalize to midnight)
    today = pd.Timestamp.today().normalize()
    arrived_mask = arrears["Arrival Date"].dt.normalize() <= today

    # Define "not fully paid" (treat missing Payment Received as 0 for comparison)
    pay_recv = arrears["Payment Received"] if "Payment Received" in arrears.columns else pd.Series([0] * len(arrears), index=arrears.index, dtype="float")
    price    = arrears["Price"] if "Price" in arrears.columns else pd.Series([pd.NA] * len(arrears), index=arrears.index, dtype="float")

    not_fully_paid_mask = price.notna() & (pay_recv.fillna(0) < price)

    dues = arrears[arrived_mask & not_fully_paid_mask].copy()

    if dues.empty:
        st.info("No arrived pets with outstanding balance.")
    else:
        # Compute Balance Due
        dues["Balance Due"] = (dues["Price"] - pay_recv).clip(lower=0)

        # Build display dataframe
        display_dues = pd.DataFrame({
            "Pet": dues.apply(lambda r: f"{species_emoji_from_row(r)} {r['Name']}", axis=1),
            "Arrival": dues["Arrival Date"].dt.strftime("%Y-%m-%d"),
            "Departure": dues["Departure Date"].dt.strftime("%Y-%m-%d"),
        })

        if "Duration" in dues.columns:
            display_dues["Duration"] = dues["Duration"].astype("Int64")

        display_dues["Price (total)"] = dues["Price"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
        if "Payment Received" in dues.columns:
            display_dues["Payment Received"] = dues["Payment Received"].fillna(0).apply(lambda x: f"${x:,.2f}")
        else:
            display_dues["Payment Received"] = "$0.00"

        display_dues["Balance Due"] = dues["Balance Due"].apply(lambda x: f"${x:,.2f}")

        # Sort: highest balance first, then earliest arrival
        display_dues = display_dues.sort_values(
            by=["Balance Due", "Arrival"],
            key=lambda s: pd.to_numeric(s.str.replace(r"[$,]", "", regex=True), errors="coerce") if s.name in ["Balance Due"] else pd.to_datetime(s, errors="coerce"),
            ascending=[False, True]
        )

        # Auto-height (no scroll)
        ROW_PX = 34
        HEADER_PX = 38
        PADDING_PX = 12
        df_height = HEADER_PX + ROW_PX * len(display_dues) + PADDING_PX

        st.dataframe(display_dues, use_container_width=True, hide_index=True, height=int(df_height))

