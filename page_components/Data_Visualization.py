#######################
# Import libraries
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from matplotlib import cm
import matplotlib.colors as mcolors
import altair as alt
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO
import base64
import os
from calendar import monthrange
from plotly.colors import sample_colorscale

# ✅ Make page wide & sidebar expanded for better responsiveness
st.set_page_config(page_title="Kingdom Data Dashboard", layout="wide", initial_sidebar_state="expanded")

#######################
def main():
    alt.themes.enable("dark")

    # Reset only when returning to this page
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Data_Visualization"

    if st.session_state.current_page != "Data_Visualization":
        st.session_state.offset_days = 0

    st.session_state.current_page = "Data_Visualization"

    #######################
    # Responsive CSS
    st.markdown("""
    <style>
    /* Make the main container truly full width and stable on reruns */
    [data-testid="stAppViewContainer"] > .main .block-container {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: 0;             /* <- was -7rem */
    max-width: 100% !important;   /* <- ensure full width */
    }

    /* Mobile padding tweak */
    @media (max-width: 900px) {
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    h1, h2, h3 { line-height: 1.2; }
    }

    /* Add horizontal gap between columns so content doesn’t collapse */
    [data-testid="stHorizontalBlock"] {
    gap: 1rem;
    }

    /* Metrics + button nowrap (unchanged) */
    [data-testid="stMetric"]{ background-color:#393939;text-align:center;padding:12px 0;border-radius:10px;}
    [data-testid="stMetricLabel"]{ display:flex;justify-content:center;align-items:center;}
    button[kind="primary"] > div[data-testid="stMarkdownContainer"] p { white-space: nowrap; margin: 0; }
    </style>
    """, unsafe_allow_html=True)


    #######################
    # Load data
    df = pd.read_csv('data/combined.csv')

    #######################
    # Sidebar
    with st.sidebar:
        st.title('🐶 Zoolotopia 🐱')

        month_lists = df['months_active'].dropna().apply(lambda x: [m.strip() for m in x.split(',')])
        unique_months = set(m for sublist in month_lists for m in sublist)
        month_dt_sorted = sorted(pd.to_datetime(list(unique_months), format="%m/%Y"))
        sorted_month_strings = [dt.strftime("%m/%Y") for dt in sorted(month_dt_sorted, reverse=True)]
        month_options = ["Show All"] + sorted_month_strings

        selected_month = st.selectbox("Select a month", month_options)

        if selected_month == "Show All":
            df_selected_month = df.copy()
        else:
            df_selected_month = df[df['months_active'].str.contains(selected_month, na=False)]

        color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
        selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

    ########################
    st.title("Kingdom Data Dashboard")
    st.markdown("---")

    if selected_month == "Show All":
        st.markdown("### 📈 Revenue Trend - All Months")
    else:
        formatted_month = pd.to_datetime(selected_month, format="%m/%Y").strftime("%B %Y")
        st.markdown(f"### 📈 Revenue Trend – {formatted_month}", unsafe_allow_html=True)

    #######################
    # Plots
    def revenue_chart(df, selected_month=None, color_scheme="blues", height=360):
        df = df.copy()
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], errors='coerce')
        df['Departure Date'] = pd.to_datetime(df['Departure Date'], errors='coerce')
        df = df.dropna(subset=['Arrival Date', 'Departure Date', 'daily price'])

        expanded = df.apply(
            lambda row: pd.DataFrame({
                'date': pd.date_range(row['Arrival Date'], row['Departure Date']),
                'daily_price': row['daily price']
            }),
            axis=1
        )
        df_revenue = pd.concat(expanded.to_list(), ignore_index=True)

        if selected_month and selected_month != "Show All":
            month, year = map(int, selected_month.split('/'))
            start_date = pd.Timestamp(year=year, month=month, day=1)
            end_day = monthrange(year, month)[1]
            end_date = pd.Timestamp(year=year, month=month, day=end_day)
            df_revenue = df_revenue[(df_revenue['date'] >= start_date) & (df_revenue['date'] <= end_date)]

        if df_revenue.empty:
            return alt.Chart(pd.DataFrame({'date': [], 'daily_price': []})).mark_line().properties(width='container', height=height)

        daily_revenue = df_revenue.groupby('date')['daily_price'].sum().reset_index()
        daily_revenue['color_key'] = 'Revenue'

        chart = (
            alt.Chart(daily_revenue)
            .mark_line(point=True)
            .encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('daily_price:Q', title='Daily Revenue ($)', scale=alt.Scale(zero=False)),
                color=alt.Color('color_key:N', scale=alt.Scale(scheme=color_scheme), legend=None),
                tooltip=[alt.Tooltip('date:T'), alt.Tooltip('daily_price:Q', format=",.2f")]
            )
            .properties(
                title=f'Daily Revenue for {selected_month}' if selected_month and selected_month != "Show All" else "Daily Revenue (All Time)",
                width='container',
                height=height
            )
        )
        return chart

    def make_donut_chart(data, value_col, category_col, title, show_legend=True, color_scheme="blues", height=360):
        total_value = data[value_col].sum()
        label = f"${total_value:,.0f}" if value_col == "Revenue" else f"{total_value} bookings"

        legend_config = alt.Legend(
            orient="bottom",
            title=None,
            labelLimit=140,
            labelFontSize=13,
            symbolSize=180,
            padding=8
        ) if show_legend else None

        base = alt.Chart(data).encode(
            theta=alt.Theta(f"{value_col}:Q"),
            color=alt.Color(f"{category_col}:N", scale=alt.Scale(scheme=color_scheme), legend=legend_config),
            tooltip=[f"{category_col}:N", alt.Tooltip(f"{value_col}:Q", format=",.2f")]
        )

        donut = base.mark_arc(innerRadius=60)

        return donut.properties(
            width='container',
            height=height,
            title=f"{title} - {label}"
        )

    st.altair_chart(
        revenue_chart(df, selected_month=selected_month, color_scheme=selected_color_theme, height=360),
        use_container_width=True
    )

    #######################
    st.markdown("---")

    if selected_month == "Show All":
        st.markdown("### 🐶🐱 Species Snapshot - All Months")
    else:
        formatted_month = pd.to_datetime(selected_month, format="%m/%Y").strftime("%B %Y")
        st.markdown(f"### 🐶🐱 Species Snapshot – {formatted_month}", unsafe_allow_html=True)

    #######################
    # Revenue by species (filtered by month)
    df_rev_species = df_selected_month.dropna(subset=['Species', 'Payment Received'])
    revenue_by_species = df_rev_species.groupby('Species')['Payment Received'].sum().reset_index()
    revenue_by_species.rename(columns={'Payment Received': 'Revenue'}, inplace=True)

    # Bookings by species per platform
    df_grouped = df_selected_month.dropna(subset=["Platform", "Species"])
    bookings_by_platform_species = (
        df_grouped.groupby(["Platform", "Species"])
        .size()
        .reset_index(name="Bookings")
    )

    species_color_scheme = alt.Scale(scheme=selected_color_theme)

    # Duration prep (global, all months for range)
    df_duration_all = df.dropna(subset=["Duration", "Species"]).copy()
    df_duration_all["Duration"] = pd.to_numeric(df_duration_all["Duration"], errors="coerce")
    df_duration_all = df_duration_all.dropna(subset=["Duration"])

    #######################
    # Layout Row: Donut - Histogram - Bar
    col1, col2, col3 = st.columns(3)

    with col1:
        revenue_donut_chart = make_donut_chart(
            revenue_by_species, 'Revenue', 'Species', 'Total Revenue by Species',
            show_legend=True, color_scheme=selected_color_theme
        )
        st.altair_chart(revenue_donut_chart, use_container_width=True)

    with col2:
        # Month-filtered duration
        df_duration_month = df_selected_month.dropna(subset=["Duration", "Species"]).copy()
        df_duration_month["Duration"] = pd.to_numeric(df_duration_month["Duration"], errors="coerce")
        df_duration_month = df_duration_month.dropna(subset=["Duration"])

        duration_chart = (
            alt.Chart(df_duration_month)
            .mark_bar()
            .encode(
                x=alt.X("Duration:Q", bin=alt.Bin(maxbins=30), title="Length of Stay (Days)"),
                y=alt.Y("count():Q", title="Number of Bookings"),
                color=alt.Color("Species:N", title="Species", scale=species_color_scheme, legend=None),
                tooltip=["Species:N", "count():Q"]
            )
            .properties(title="Length of Stay Distribution by Species", width='container')
        )
        st.altair_chart(duration_chart, use_container_width=True)

    with col3:
        bar_chart = (
            alt.Chart(bookings_by_platform_species)
            .mark_bar()
            .encode(
                x=alt.X("Platform:N", title="Platform"),
                y=alt.Y("Bookings:Q", title="Number of Bookings"),
                color=alt.Color("Species:N", scale=species_color_scheme, legend=None),
                tooltip=["Platform", "Species", "Bookings"]
            )
            .properties(title="Bookings by Species within Each Platform", width='container')
        )
        st.altair_chart(bar_chart, use_container_width=True)

    #######################
    # Monthly stacked + Scatter + Violin
    st.markdown("---")
    col4, col5, col6 = st.columns(3)

    with col4:
        exploded = df.dropna(subset=["months_active", "Species"]).copy()
        exploded["months_active"] = exploded["months_active"].str.split(", ")
        exploded = exploded.explode("months_active")
        exploded["Month_Year"] = pd.to_datetime(exploded["months_active"], format="%m/%Y", errors="coerce")
        exploded = exploded.dropna(subset=["Month_Year"])
        exploded["Month"] = exploded["Month_Year"].dt.strftime("%b")
        exploded["Month_Num"] = exploded["Month_Year"].dt.month
        exploded["Year"] = exploded["Month_Year"].dt.year.astype(str)

        species_opacity_map = {"Dog": 1.0, "Cat": 0.8}
        exploded["Species_Opacity"] = exploded["Species"].map(species_opacity_map)

        grouped = (
            exploded.groupby(["Month", "Month_Num", "Year", "Species", "Species_Opacity"])
            .size()
            .reset_index(name="Count")
        )

        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        grouped = grouped.sort_values("Month_Num")

        stacked_chart = (
            alt.Chart(grouped)
            .mark_bar()
            .encode(
                x=alt.X("Month:N", sort=month_order, title="Month"),
                y=alt.Y("Count:Q", title="Number of Bookings"),
                xOffset=alt.XOffset("Year:N"),
                color=alt.Color("Year:N", title="Year", scale=alt.Scale(scheme=selected_color_theme)),
                opacity=alt.Opacity("Species_Opacity:Q", legend=None),
                tooltip=["Month:N", "Year:N", "Species:N", "Count:Q"]
            )
            .properties(title="📅 Monthly Bookings by Year (Cat/Dog Stacked via Opacity)", width='container')
        )
        st.altair_chart(stacked_chart, use_container_width=True)

    with col5:
        scatter_df = df_selected_month.dropna(subset=["daily price","Price","Species","Platform","Name","Duration"]).copy()
        scatter_df["daily price"] = pd.to_numeric(scatter_df["daily price"], errors="coerce")
        scatter_df["Price"] = pd.to_numeric(scatter_df["Price"], errors="coerce")
        scatter_df["Duration"] = pd.to_numeric(scatter_df["Duration"], errors="coerce")
        scatter_df = scatter_df.dropna(subset=["daily price","Price","Duration"])
        scatter_df = scatter_df[(scatter_df["daily price"] > 0) & (scatter_df["Price"] > 0)]

        scatter = (
            alt.Chart(scatter_df)
            .mark_circle(size=80, opacity=0.7)
            .encode(
                x=alt.X("daily price:Q", title="Daily Price ($)"),
                y=alt.Y("Price:Q", title="Total Price ($)"),
                color=alt.Color("Platform:N", title="Platform", scale=alt.Scale(scheme="category20")),
                tooltip=[
                    alt.Tooltip("Name:N"),
                    alt.Tooltip("Platform:N"),
                    alt.Tooltip("Species:N"),
                    alt.Tooltip("Duration:Q"),
                    alt.Tooltip("daily price:Q"),
                    alt.Tooltip("Price:Q")
                ]
            )
            .properties(title="💵 Daily Price vs. Total Price by Platform", width='container')
        )
        st.altair_chart(scatter, use_container_width=True)

    def get_discrete_colors_from_continuous(colorscale_name, num_colors):
        try:
            return sample_colorscale(colorscale_name, [i / max(1,(num_colors - 1)) for i in range(num_colors)])
        except Exception:
            return px.colors.qualitative.Set2

    with col6:
        violin_df = df_selected_month.dropna(subset=["daily price", "Platform", "Species"]).copy()
        violin_df["daily price"] = pd.to_numeric(violin_df["daily price"], errors="coerce")
        violin_df = violin_df[violin_df["daily price"] > 0]

        if not violin_df.empty:
            platforms = violin_df["Platform"].unique()
            color_sequence = get_discrete_colors_from_continuous(selected_color_theme, len(platforms))

            fig = px.violin(
                violin_df,
                x="Platform",
                y="daily price",
                color="Platform",
                facet_col="Species",
                box=True,
                points=False,
                title="🧮 Daily Price Distribution by Platform (Faceted by Species)"
            )
            fig.update_layout(autosize=True, margin=dict(t=40, b=0, l=0, r=0), legend_title_text="Platform")
            fig.update_traces(selector=dict(type='violin'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid data available for violin plot in this month.")

    # Kingdom Header
    st.markdown("---")
    if selected_month == "Show All":
        st.markdown("### 🐾 Kingdom Citizens Summary - All Months")
    else:
        formatted_month = pd.to_datetime(selected_month, format="%m/%Y").strftime("%B %Y")
        st.markdown(f"### 🐾 Kingdom Citizens Summary – {formatted_month}", unsafe_allow_html=True)

    # Filters
    st.markdown("### 📦 Select Platform")
    available_platforms = ["All Platforms"] + sorted(df_selected_month["Platform"].dropna().unique()) if "Platform" in df_selected_month.columns else ["All Platforms"]
    selected_platform = st.radio("Choose a Platform", available_platforms, horizontal=True)

    selected_species = st.radio("Select Species", ["🐶 Dog", "🐱 Cat"], horizontal=True)
    species_filter = "Dog" if selected_species == "🐶 Dog" else "Cat"
    species_emoji = "🐶" if species_filter == "Dog" else "🐱"

    if selected_platform == "All Platforms":
        df_filtered = df_selected_month[df_selected_month["Species"] == species_filter]
    else:
        df_filtered = df_selected_month[(df_selected_month["Species"] == species_filter) & (df_selected_month["Platform"] == selected_platform)]

    df_visits = df_filtered[df_filtered["Type"] != "Drop In"]
    visits_grouped = df_visits.groupby(["Name", "Species"], as_index=False).size().rename(columns={"size": "Visits"})
    visits_grouped = visits_grouped[visits_grouped["Species"] == species_filter].nlargest(10, "Visits")
    visits_grouped["Visits"] = visits_grouped["Visits"].apply(lambda x: species_emoji * x)

    df_duration = df_filtered.dropna(subset=["Name", "Duration"]).copy()
    df_duration["Duration"] = pd.to_numeric(df_duration["Duration"], errors="coerce")
    df_duration = df_duration.dropna(subset=["Duration"])
    duration_grouped = df_duration.groupby(["Name", "Species"], as_index=False)["Duration"].max()
    top_duration = duration_grouped[duration_grouped["Species"] == species_filter].nlargest(10, "Duration")
    top_duration["Species"] = species_emoji

    df_breed = df_filtered
    breed_grouped = df_breed.groupby(["Breed"], as_index=False).size().rename(columns={"size": "Count"})
    top_breeds = breed_grouped.nlargest(10, "Count")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**Top Returning {selected_species}s**")
        st.dataframe(
            visits_grouped[["Name", "Visits"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name": st.column_config.TextColumn("Pet Name"),
                "Visits": st.column_config.TextColumn("Visits")
            }
        )

    with col2:
        st.markdown(f"**Longest Stays – {selected_species}s**")
        st.dataframe(
            top_duration[["Name", "Duration"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name": st.column_config.TextColumn("Pet Name"),
                "Duration": st.column_config.ProgressColumn(
                    "Duration (Days)",
                    format="%d",
                    min_value=0,
                    max_value=int(top_duration["Duration"].max()) if not top_duration.empty else 0
                ),
            }
        )

    with col3:
        st.markdown(f"**Top {selected_species}s Breeds**")
        st.dataframe(
            top_breeds,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Breed": st.column_config.TextColumn("Breed"),
                "Count": st.column_config.ProgressColumn(
                    "Count",
                    format="%d",
                    min_value=0,
                    max_value=int(top_breeds["Count"].max()) if not top_breeds.empty else 0,
                )
            }
        )

if __name__ == "__main__":
    main()
