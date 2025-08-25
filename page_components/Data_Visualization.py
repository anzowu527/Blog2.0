# data_visualization1.py
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
import numpy as np
from matplotlib import cm
import matplotlib.colors as mcolors
from streamlit_echarts import st_echarts
from datetime import datetime, timedelta, date
import base64
import os


def revenue_chart(df, selected_month=None, color_scheme="blues", height=360):
    df = df.copy()
    df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')
    df['Departure Date'] = pd.to_datetime(df['Departure Date'], errors='coerce')
    df['daily price'] = pd.to_numeric(df['daily price'], errors='coerce')
    df = df.dropna(subset=['Arrival Date', 'Departure Date', 'daily price'])

    # Only valid stays
    df = df[df['Departure Date'] > df['Arrival Date']]

    def _expand_row(r):
        arr = r['Arrival Date'].normalize()
        dep = r['Departure Date'].normalize()
        p   = r['daily price']
        if pd.isna(arr) or pd.isna(dep) or pd.isna(p) or dep < arr:
            return pd.DataFrame(columns=['date', 'daily_price'])

        # Same-day stay: count the day once
        if dep == arr:
            return pd.DataFrame({'date': [arr], 'daily_price': [p]})

        # Multi-day: exclude arrival and checkout -> [arr+1, dep-1]
        start = arr + pd.Timedelta(days=1)
        end   = dep - pd.Timedelta(days=1)
        if end < start:
            return pd.DataFrame(columns=['date', 'daily_price'])

        return pd.DataFrame({'date': pd.date_range(start, end), 'daily_price': p})

    expanded = df.apply(_expand_row, axis=1)
    df_revenue = pd.concat(expanded.to_list(), ignore_index=True) if len(expanded) else pd.DataFrame(columns=['date','daily_price'])

    # Optional month filter
    if selected_month and selected_month != "Show All":
        m, y = map(int, selected_month.split('/'))
        start_date = pd.Timestamp(year=y, month=m, day=1)
        end_date = start_date + pd.offsets.MonthEnd(0)
        df_revenue = df_revenue[(df_revenue['date'] >= start_date) & (df_revenue['date'] <= end_date)]

    if df_revenue.empty:
        return alt.Chart(pd.DataFrame({'date': [], 'daily_price': []})).mark_line().properties(width='container', height=height)

    daily_revenue = df_revenue.groupby('date', as_index=False)['daily_price'].sum()
    daily_revenue['color_key'] = 'Revenue'

    chart = (
        alt.Chart(daily_revenue)
        .mark_line(point=True)
        .encode(
            x=alt.X('date:T', title='Date', axis=alt.Axis(format='%b %Y', tickCount='month', labelAngle=0)),
            y=alt.Y('daily_price:Q', title='Daily Revenue ($)', scale=alt.Scale(zero=False)),
            color=alt.Color('color_key:N', scale=alt.Scale(scheme=color_scheme), legend=None),
            tooltip=[alt.Tooltip('date:T'), alt.Tooltip('daily_price:Q', format=",.2f")]
        )
        .properties(
            title=f"Daily Revenue for {selected_month}" if selected_month and selected_month != "Show All" else "Daily Revenue (All Time)",
            width='container',
            height=height
        )
        .configure(background="transparent")
        .configure_view(fill="transparent")
    )
    return chart
def revenue_stacked_line_options_by_year(df, stack=True, focus_year=None, color_palette=None):
    import pandas as pd
    x = df.copy()
    x['Arrival Date']  = pd.to_datetime(x['Arrival Date'], errors='coerce')
    x['Departure Date'] = pd.to_datetime(x['Departure Date'], errors='coerce')
    x['daily price']   = pd.to_numeric(x.get('daily price'), errors='coerce')
    x = x.dropna(subset=['Arrival Date', 'Departure Date', 'daily price'])
    x = x[x['Departure Date'] > x['Arrival Date']]

    def _expand_row(r):
        arr, dep, p = r['Arrival Date'].normalize(), r['Departure Date'].normalize(), r['daily price']
        if dep == arr:
            return pd.DataFrame({'date':[arr], 'daily_price':[p]})
        start, end = arr + pd.Timedelta(days=1), dep - pd.Timedelta(days=1)
        if end < start: return pd.DataFrame(columns=['date','daily_price'])
        return pd.DataFrame({'date': pd.date_range(start, end), 'daily_price': p})

    expanded = x.apply(_expand_row, axis=1)
    df_rev = pd.concat(expanded.to_list(), ignore_index=True) if len(expanded) else pd.DataFrame(columns=['date','daily_price'])
    if df_rev.empty:
        return {"title":{"text":"Monthly Revenue by Year (Stacked Line)"},"series":[]}

    df_rev['year']  = df_rev['date'].dt.year.astype(int)
    df_rev['month'] = df_rev['date'].dt.month.astype(int)
    monthly = (df_rev.groupby(['year','month'], as_index=False)['daily_price']
                     .sum().rename(columns={'daily_price':'revenue'}))

    months = list(range(1,13))
    month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    years = sorted(monthly['year'].unique())

    # Put the focus (latest) year at the BOTTOM of the stack
    target = focus_year if focus_year is not None else max(years)
    ordered_years = [target] + [y for y in years if y != target]

    series = []
    for yr in ordered_years:
        ydat = (monthly[monthly['year']==yr].set_index('month').reindex(months)['revenue']
                .fillna(0.0).round(2).tolist())
        s = {
            "name": str(yr),
            "type": "line",
            "data": ydat,
            "smooth": False,            # no curve smoothing
            "symbol": "circle",
            "symbolSize": 8,
            "showSymbol": True,
            "showAllSymbol": True,
            "lineStyle": {"width": 2},
            "emphasis": {"focus": "series"},
        }
        if stack:
            s["stack"] = "total"
        series.append(s)

    options = {
        "title": {"text": "Monthly Revenue by Year (Stacked Line)", "left": "center"},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [str(y) for y in ordered_years], "top": 28},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "boundaryGap": False, "data": month_labels, "axisLabel": {"interval": 0}},
        "yAxis": {"type": "value"},
        "series": series,
        "backgroundColor": "rgba(0,0,0,0)",
    }
    if color_palette:
        options["color"] = color_palette
    return options



def main():
    st.set_page_config(page_title="📈 Kingdom Revenue", layout="wide")

    # Match landing page theme
    st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #ffeada !important; }
    [data-testid="stHeader"] { background-color: #ffeada !important; }
    [data-testid="stSidebar"] { background-color: #c8a18f !important; }
    .stMetric { background: #c8a18f20; padding: 0.5rem; border-radius: 8px; }
                
    /* Custom navigation buttons */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        background-color: #c8a18f !important;  /* dark brown */
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 8px 18px !important;
        font-weight: bold !important;
        font-size: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
        background-color: #3a251c !important;  /* darker brown */
        transform: translateY(-2px);
    }
    div[data-testid="stHorizontalBlock"] div.stButton > button:active {
        background-color: #2a1912 !important;
        transform: translateY(0);
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📈 Kingdom Revenue")
    st.caption("Daily total revenue; x-axis labeled by month")

    # --- Operation date: default to today on fresh session ---
    if "op_date" not in st.session_state:
        st.session_state.op_date = date.today()

    # Compute selected op day/timestamp (used by charts below)
    op_day = st.session_state.op_date
    op_ts  = pd.to_datetime(op_day)

    st.markdown(
        f"<div style='margin:8px 0 16px 0; color:#603D35;'>"
        f"<strong>Viewing date:</strong> {op_day.strftime('%A, %b %d, %Y')}</div>",
        unsafe_allow_html=True
    )

    # Load CSV
    csv_path = Path("data/combined.csv")
    if not csv_path.exists():
        st.error("Could not find `data/combined.csv`. Please place the file in the `data/` folder.")
        st.stop()
    df = pd.read_csv(csv_path)

    # Old:
    # st.altair_chart(
    #     revenue_chart(df, selected_month=selected, color_scheme="blues", height=420),
    #     use_container_width=True
    # )

    # New: stacked line by year (ECharts)
    options = revenue_stacked_line_options_by_year(df, stack=False)
    options["color"] = [
        "#0B3C5D","#60A5FA","#BBD6FE", "#145DA0", "#A7C5EB",  "#1E6091", "#93C5FD", "#2563EB", "#7CB5FB", "#3B82F6"
        
    ]
    for s in options.get("series", []):
        s.update({
            "smooth": False,
            "symbol": "circle",
            "symbolSize": 8,
            "showSymbol": True,
            "showAllSymbol": True,
            "lineStyle": {"width": 2},
        })
    st_echarts(options=options, height="420px")


    # Totals under the chart — Price + Tips
    try:
        d = df.copy()
        d["Price"] = pd.to_numeric(d.get("Price"), errors="coerce")
        d["Tips"]  = pd.to_numeric(d.get("Tips"), errors="coerce")
        d = d.dropna(subset=["Price", "Tips"], how="all")

        total_price = d["Price"].sum(min_count=1)
        total_tips  = d["Tips"].sum(min_count=1)
        revenue_total = (total_price if pd.notna(total_price) else 0) + (total_tips if pd.notna(total_tips) else 0)

        st.metric("Revenue Total", f"${revenue_total:,.2f}", help="Sum of Price + Tips.")
    except Exception as e:
        st.warning(f"Could not compute Revenue Total: {e}")

    # ------------------ Operation (Donut + Current Week) ------------------
    try:
        tdf = df.copy()
        tdf["Arrival Date"] = pd.to_datetime(tdf["Arrival Date"], errors="coerce")
        tdf["Departure Date"] = pd.to_datetime(tdf["Departure Date"], errors="coerce")
        tdf["daily price"]   = pd.to_numeric(tdf.get("daily price"), errors="coerce")
        tdf["Species"]       = tdf.get("Species", "").astype(str).str.title().str.strip()
        tdf["Name"]          = tdf.get("Name", "").astype(str).str.strip()

        # In house on op_ts: arrival < op_ts, departure >= op_ts
        in_house = tdf[(tdf["Arrival Date"] < op_ts) & (tdf["Departure Date"] >= op_ts)]

        # Per‑pet earnings for op_day
        pet_earnings = (
            in_house.groupby(["Name", "Species"], as_index=False)["daily price"]
            .sum()
            .rename(columns={"daily price": "Earning"})
        )

        if pet_earnings.empty or pet_earnings["Earning"].sum() <= 0:
            st.info("No pets in house (or no earnings) on this day.")
        else:
            # Sort: Cats first, then Dogs; high → low
            species_priority = {"Cat": 0, "Dog": 1}
            pet_earnings["SpeciesOrder"] = pet_earnings["Species"].map(species_priority).fillna(9).astype(int)
            pet_earnings = pet_earnings.sort_values(
                by=["SpeciesOrder", "Earning"], ascending=[True, False]
            ).reset_index(drop=True)

            # Colors
            def get_palette(palette_name, n, vmin=0.35, vmax=0.95):
                cmap = cm.get_cmap(palette_name)
                if n <= 0: return []
                return [mcolors.to_hex(cmap(vmin + (vmax - vmin) * i / max(n - 1, 1))) for i in range(n)]

            num_cats = (pet_earnings["Species"] == "Cat").sum()
            num_dogs = (pet_earnings["Species"] == "Dog").sum()
            cat_colors = get_palette("Greens", num_cats)
            dog_colors = get_palette("Blues",  num_dogs)
            color_array = cat_colors + dog_colors

            series_data = [
                {"value": float(row["Earning"]), "name": row["Name"]}
                for _, row in pet_earnings.iterrows()
            ]

            total_earning = float(pet_earnings["Earning"].sum())
            title_txt = f"💰 Earnings Breakdown • {op_day.strftime('%b %d, %Y')}"

            options = {
                "backgroundColor": "rgba(0,0,0,0)",
                "title": {"text": title_txt, "left": "center", "textStyle": {"color": "#603D35", "fontSize": 16}},
                "tooltip": {"trigger": "item", "formatter": "{b}: ${c} ({d}%)"},
                "color": color_array,
                "series": [{
                    "name": "Earnings",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "avoidLabelOverlap": False,
                    "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
                    "label": {"show": False, "position": "center"},
                    "emphasis": {"label": {"show": False}},
                    "labelLine": {"show": False},
                    "data": series_data,
                }],
            }
            options["graphic"] = [{
                "id": "centerText",
                "type": "text",
                "left": "center",
                "top": "middle",
                "silent": True,
                "style": {
                    "text": f"Total: ${total_earning:,.0f}",
                    "textAlign": "center",
                    "fill": "#603D35",
                    "fontSize": 22,
                    "fontWeight": "bold",
                    "lineHeight": 26
                }
            }]

            st.markdown("---")
            st.subheader(f"📊 Operation — {op_day.strftime('%b %d, %Y')}")
            st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

            left, right, spacer = st.columns([1, 1, 0.1], gap="large")

            with left:
                st_echarts(options=options, height="500px")

            # -------- Right: CURRENT WEEK ONLY (Sun→Sat) --------
            def _build_daily_revenue(df_: pd.DataFrame) -> pd.DataFrame:
                if df_ is None or df_.empty:
                    return pd.DataFrame(columns=['date', 'daily_price'])

                x = df_.copy()
                x['Arrival Date'] = pd.to_datetime(x['Arrival Date'], errors='coerce').dt.normalize()
                x['Departure Date'] = pd.to_datetime(x['Departure Date'], errors='coerce').dt.normalize()
                x['daily price']   = pd.to_numeric(x.get('daily price'), errors='coerce')
                x = x.dropna(subset=['Arrival Date', 'Departure Date', 'daily price'])

                if x.empty:
                    return pd.DataFrame(columns=['date', 'daily_price'])

                start_ = x['Arrival Date'].min()
                end_   = x['Departure Date'].max()
                all_days = pd.date_range(start_, end_, freq='D')

                records = []
                for d_ in all_days:
                    mask = (x['Arrival Date'] < d_) & (x['Departure Date'] >= d_)
                    total_ = x.loc[mask, 'daily price'].sum()
                    records.append({'date': d_, 'daily_price': float(total_)})
                return pd.DataFrame(records)

            with right:
                daily_rev = _build_daily_revenue(df)
                if daily_rev.empty:
                    st.info("No revenue data available for the current week.")
                else:
                    # Base week on selected op date
                    today = op_ts
                    days_since_sun = (today.weekday() + 1) % 7   # Sun=0, Mon=1, ...
                    week_start = (today - pd.Timedelta(days=days_since_sun)).normalize()
                    week_end   = week_start + pd.Timedelta(days=6)

                    week_frame = pd.DataFrame({'date': pd.date_range(week_start, week_end, freq='D')})
                    week_data = (
                        week_frame.merge(daily_rev, on='date', how='left')
                                  .fillna({'daily_price': 0})
                    )
                    week_total = float(week_data['daily_price'].sum())

                    current_week_chart = (
                        alt.Chart(week_data)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X(
                                'date:T',
                                title='Date',
                                axis=alt.Axis(format='%A'),
                                scale=alt.Scale(domain=[week_start.to_pydatetime(), week_end.to_pydatetime()])
                            ),
                            y=alt.Y('daily_price:Q', title='Revenue ($)', scale=alt.Scale(zero=True)),
                            tooltip=[
                                alt.Tooltip('date:T', title='Date'),
                                alt.Tooltip('daily_price:Q', title='Revenue', format=",.0f")
                            ]
                        )
                        .properties(
                            title=f"Current Week (Sun–Sat): {week_start.strftime('%b %d')} – {week_end.strftime('%b %d')} • Total ${week_total:,.0f}",
                            width='container',
                            height=420
                        )
                        .configure(background="transparent")
                        .configure_view(fill="transparent")
                    )
                    st.altair_chart(current_week_chart, use_container_width=True)

            # -------- Controls: Prev / Today / Next (UNDER charts, ABOVE avatars) --------
            c1, c2, c3, c4, c5 = st.columns([1.5,1.2,1,2,2])  # adjust ratios

            with c1:
                if st.button("← Previous Day", key="op_prev_day"):
                    st.session_state.op_date = st.session_state.op_date - timedelta(days=1)
                    st.rerun()
            with c2:
                if st.button("Today", key="op_today"):
                    st.session_state.op_date = date.today()
                    st.rerun()
            with c3:
                if st.button("Next Day →", key="op_next_day"):
                    st.session_state.op_date = st.session_state.op_date + timedelta(days=1)
                    st.rerun()

            # -------- Under the graphs: Avatars of pets on op_day --------
            st.markdown(
                "<h3 style='text-align:left; color:#603D35; margin:0 0 18px 0;'>🐾 Pets in House</h3>",
                unsafe_allow_html=True
            )

            def _find_avatar_path(name: str):
                base_dir = "images/avatar"
                if not name:
                    return None
                exts = [".webp", ".png", ".jpg", ".jpeg"]
                for ext in exts:
                    p = os.path.join(base_dir, f"{name}{ext}")
                    if os.path.exists(p):
                        return p
                return None

            def _img_b64(path: str):
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")

            pets_today = (
                tdf[
                    (tdf["Arrival Date"] <= op_ts) &
                    (tdf["Departure Date"] >= op_ts)
                ][["Name", "Species", "Arrival Date", "Departure Date"]]
                .dropna(subset=["Name"])
                .drop_duplicates()
                .sort_values(["Species", "Name"])
                .reset_index(drop=True)
            )

            if pets_today.empty:
                st.info("No pets in house on this day.")
            else:
                AVATAR_SIZE = 72
                COL_GAP = 16
                ROW_GAP = 22
                cards_html = []

                for _, r in pets_today.iterrows():
                    name = str(r["Name"]).strip()
                    arr_today = pd.to_datetime(r["Arrival Date"]).normalize() == op_ts
                    dep_today = pd.to_datetime(r["Departure Date"]).normalize() == op_ts

                    if arr_today:
                        shadow = "0 0 10px 3px rgba(0, 200, 0, 0.55)"   # green glow
                    elif dep_today:
                        shadow = "0 0 10px 3px rgba(220, 0, 0, 0.55)"   # red glow
                    else:
                        shadow = "0 2px 6px rgba(0,0,0,.15)"            # neutral

                    path = _find_avatar_path(name)
                    if path:
                        img_tag = f'<img src="data:image/*;base64,{_img_b64(path)}" ' \
                                  f'style="width:{AVATAR_SIZE}px;height:{AVATAR_SIZE}px;object-fit:cover;' \
                                  f'border-radius:50%;box-shadow:{shadow};border:3px solid white;" />'
                    else:
                        initials = (name[:2].upper() or "🐾")
                        img_tag = (
                            f'<div style="width:{AVATAR_SIZE}px;height:{AVATAR_SIZE}px;border-radius:50%;'
                            f'background:#c8a18f;display:flex;align-items:center;justify-content:center;'
                            f'color:white;font-weight:700;font-size:22px;box-shadow:{shadow};border:3px solid white;">'
                            f'{initials}</div>'
                        )

                    card = (
                        f'<div class="pet-card" '
                        f'style="display:flex;flex-direction:column;align-items:center;row-gap:6px;">'
                        f'{img_tag}'
                        f'<div style="color:#603D35;font-weight:600;font-size:12px;text-align:center;max-width:{AVATAR_SIZE}px;'
                        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>'
                        f'</div>'
                    )
                    cards_html.append(card)

                container_html = (
                    f'<div style="display:flex;flex-wrap:wrap;column-gap:{COL_GAP}px;row-gap:{ROW_GAP}px;'
                    f'justify-content:flex-start;align-items:flex-start;">'
                    + "".join(cards_html) +
                    '</div>'
                )
                st.markdown(container_html, unsafe_allow_html=True)
                st.markdown("---")

    except Exception as e:
        st.warning(f"Could not render daily operation charts: {e}")


if __name__ == "__main__":
    main()
