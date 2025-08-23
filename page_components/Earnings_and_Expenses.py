# Earnings_and_Expenses.py
import os
import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

st.set_page_config(page_title="💰 Earnings & Expenses", layout="wide")

# ---------- Helpers ----------
def read_df_safe(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    
def compute_price_plus_tips_total(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return 0.0

    x = df.copy()
    x["Price"] = pd.to_numeric(x.get("Price"), errors="coerce")
    x["Tips"]  = pd.to_numeric(x.get("Tips"),  errors="coerce")
    # drop rows where both are NaN
    x = x.dropna(subset=["Price", "Tips"], how="all")

    total_price = x["Price"].sum()
    total_tips  = x["Tips"].sum()

    if pd.isna(total_price): total_price = 0.0
    if pd.isna(total_tips):  total_tips  = 0.0

    total = total_price + total_tips
    return round(float(total))   # 👈 round to integer


def donut_options(title: str, data_pairs, colors=None, height_px=360):
    # Build a legend.selected map where every item starts as selected = True
    legend_selected = {d["name"]: True for d in data_pairs}

    opt = {
        "title": {"text": title, "left": "center", "top": 0},
        "tooltip": {"trigger": "item"},
        "legend": {
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "selected": legend_selected,         # ✅ explicit selection state
            "selectedMode": True,                # multiple selection enabled
        },
        "series": [{
            "name": title,
            "type": "pie",
            "radius": ["45%", "72%"],
            "avoidLabelOverlap": True,
            "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": False},
            "emphasis": {"label": {"show": False}},
            "labelLine": {"show": False},
            "data": data_pairs,
        }],
        "graphic": [{
            "id": "centerText",
            "type": "text",
            "left": "center",
            "top": "middle",
            "style": {
                "text": f"Total\n${sum(d['value'] for d in data_pairs):,.0f}",
                "textAlign": "center",
                "fill": "#333",
                "fontSize": 22,
                "fontWeight": "bold",
            }
        }],
    }
    if colors:
        opt["color"] = colors
    return opt, height_px


def get_col(df, name):
    lower_map = {c.lower(): c for c in df.columns}
    return lower_map.get(name.lower())

# palettes
BROWN = ["#603D35", "#92695F", "#AE928B"]  # 3 distinct browns
ORANGES = ["#F5A623", "#E6951F", "#D7841B", "#C77418", "#B96514", "#A95710"]
AUTUMN = [
    "#D35400",  # pumpkin orange
    "#E67E22",  # tangerine
    "#F39C12",  # golden yellow
    "#A04000",  # deep rust
    "#BA4A00",  # burnt orange
    "#CA6F1E",  # amber
    "#DC7633",  # light pumpkin
    "#F5B041",  # harvest gold
]

# ---------- Main ----------
def main():
    EARNINGS_PATH = "data/combined.csv"
    EXPENSES_PATH = "data/expenses.csv"

    earn_df = read_df_safe(EARNINGS_PATH)
    exp_df = read_df_safe(EXPENSES_PATH)

    # ---------- Earnings donut ----------
    earn_pairs = []
    colors = []

    if not earn_df.empty:
        price_col = get_col(earn_df, "Price")
        pay_col   = get_col(earn_df, "Payment Received")
        plat_col  = get_col(earn_df, "Platform") or get_col(earn_df, "Source") or get_col(earn_df, "Channel")

        if price_col and pay_col:
            df = earn_df.copy()
            df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
            df[pay_col]   = pd.to_numeric(df[pay_col], errors="coerce").fillna(0)

            if not plat_col:
                plat_col = "__Platform__"
                df[plat_col] = "Unknown"

            # Use non-negative payments for slice math
            df["pay_pos"] = df[pay_col].clip(lower=0)
            df["incoming_pos"] = (df[price_col] - df["pay_pos"]).clip(lower=0)

            platforms = df[plat_col].astype(str).str.strip().replace({"": "Unknown"}).unique().tolist()
            platforms.sort()

            # RECEIVED (browns)
            for i, p in enumerate(platforms):
                sub = df[df[plat_col] == p]
                received = sub["pay_pos"].sum()
                if received > 0:
                    earn_pairs.append({"value": round(received, 2), "name": f"{p} - Received"})
                    colors.append(BROWN[i % len(BROWN)])

            # INCOMING (oranges)
            for i, p in enumerate(platforms):
                sub = df[df[plat_col] == p]
                incoming = sub["incoming_pos"].sum()
                if incoming > 0:
                    earn_pairs.append({"value": round(incoming, 2), "name": f"{p} - Incoming"})
                    colors.append(ORANGES[i % len(ORANGES)])


    earn_title = "Earnings Breakdown by Platform"
    earn_options, earn_h = donut_options(earn_title, earn_pairs, colors=colors)

    # Center = match Visualization page: all-time Price + Tips (with same row inclusion rules)
    total_revenue = compute_price_plus_tips_total(earn_df)

    if isinstance(earn_options.get("graphic"), list) and earn_options["graphic"]:
        earn_options["graphic"][0]["style"]["text"] = f"Total\n${total_revenue:,.0f}"



    # ---------- Expenses donut ----------
    exp_pairs = []
    if not exp_df.empty:
        cat_col = get_col(exp_df, "category")
        amt_col = get_col(exp_df, "amount")
        if cat_col and amt_col:
            tmp = exp_df[[cat_col, amt_col]].copy()
            tmp[amt_col] = pd.to_numeric(tmp[amt_col], errors="coerce").fillna(0)  # <- fix
            by_cat = tmp.groupby(cat_col, as_index=False)[amt_col].sum().sort_values(amt_col, ascending=False)
            exp_pairs = [{"value": float(v), "name": str(n)} for n, v in zip(by_cat[cat_col], by_cat[amt_col])]

    exp_title = "Total Expenses by Category"
    exp_options, exp_h = donut_options(exp_title, exp_pairs, colors=AUTUMN)

    # ---------- One shared event for both charts ----------
    legend_total_events = {
        "legendselectchanged": """
            function(params) {
                var chart = this;
                var option = chart.getOption();

                // Prefer the full, current selection map from params
                var selected = params.selected || {};
                // Fallback: if for some reason it's empty, use legend[0].selected
                if (Object.keys(selected).length === 0 && option.legend && option.legend.length) {
                    selected = option.legend[0].selected || {};
                }

                var data = (option.series && option.series[0] && option.series[0].data) ? option.series[0].data : [];
                var total = 0;

                for (var i = 0; i < data.length; i++) {
                    var name = data[i].name;
                    // Default to true if item missing from the selected map
                    var isOn = (selected.hasOwnProperty(name)) ? selected[name] : true;
                    if (isOn) total += data[i].value;
                }

                var fmt = new Intl.NumberFormat('en-US', {maximumFractionDigits: 0});
                chart.setOption({
                    graphic: [{
                        id: 'centerText',
                        style: { text: "Total\\n$" + fmt.format(total) }
                    }]
                });
            }
        """
    }


    # ---------- Layout ----------
    st.markdown("## 💵 Earnings & Expenses Overview")
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        # Earnings donut: fixed center total (Price + Tips), no legend-total event
        st_echarts(options=earn_options, height=f"{earn_h}px")

    with col2:
        # Expenses donut: keep dynamic total on legend selection
        st_echarts(options=exp_options, events=legend_total_events, height=f"{exp_h}px")


    # ---------- Net Saving line (centered) ----------
    # Sum only the "Received" slices from the earnings donut
    total_received = sum(
        (item.get("value") or 0)
        for item in earn_pairs
        if isinstance(item.get("name"), str) and "received" in item["name"].lower()
    )

    # Sum all expense slices
    total_expenses = sum((item.get("value") or 0) for item in exp_pairs)

    net_saving = total_received - total_expenses

    st.markdown(
        f"""
        <div style='text-align:center; margin-top:20px;'>
            <h2 style='color:#603D35;'>💡 Net Saving: ${net_saving:,.2f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------- Expenses Management (no full refresh + correct dtypes) ----------
    st.markdown("### ➕ Add New Expense")

    # Helper: enforce canonical schema and dtypes for the in-memory DF
    def normalize_expenses_df(df: pd.DataFrame) -> pd.DataFrame:
        req = ["category", "date", "amount", "description"]
        if df is None or df.empty:
            return pd.DataFrame(columns=req).astype({
                "category": "string",
                "date": "datetime64[ns]",
                "amount": "float",
                "description": "string",
            })

        # Ensure required columns exist
        for c in req:
            if c not in df.columns:
                df[c] = pd.NA

        # Dtypes (very important for st.data_editor)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")              # datetime64[ns]
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")           # float
        df["category"] = df["category"].astype("string").fillna("")
        df["description"] = df["description"].astype("string").fillna("")

        # Column order
        return df[req]

    # Initialize session state with normalized DF once
    if "exp_df" not in st.session_state:
        st.session_state.exp_df = normalize_expenses_df(exp_df.copy())
    else:
        # Always keep it normalized (protect against earlier string dates)
        st.session_state.exp_df = normalize_expenses_df(st.session_state.exp_df)

    # --- Add Expense Form (no page reset) ---
    # Build category options and ensure "Other" is available exactly once, at the end
    base_categories = sorted([c for c in st.session_state.exp_df["category"].unique().tolist() if c])
    options_categories = [c for c in base_categories if c.lower() != "other"] + ["Other"]

    with st.form("add_expense_form", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 3])

        with c1:
            selected_category = st.selectbox("Category", options=options_categories, index=0 if base_categories else len(options_categories) - 1)
            # When "Other" is chosen, we just keep it as "Other"
            final_category = selected_category

        with c2:
            new_date = st.date_input("Date")
        with c3:
            new_amount = st.number_input("Amount ($)", min_value=0.0, step=1.0, format="%.2f")
        with c4:
            new_description = st.text_input("Description", placeholder="e.g., Dog food or vet visit")

        submitted = st.form_submit_button("Add Expense")

    if submitted:
        # final_category will always be set (including "Other")
        row = {
            "category": final_category,
            "date": pd.to_datetime(new_date),
            "amount": float(new_amount),
            "description": (new_description or "").strip()
        }
        st.session_state.exp_df = pd.concat(
            [st.session_state.exp_df, pd.DataFrame([row])],
            ignore_index=True
        )
        # Save to CSV (format date as string ONLY in the file)
        out = st.session_state.exp_df.copy()
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        out.to_csv(EXPENSES_PATH, index=False)
        st.success("✅ New expense added!")


    # ---------- Expenses Table ----------
    st.markdown("### 📋 Manage Expenses")

    # Sort newest → oldest using true datetime
    table_df = st.session_state.exp_df.sort_values("date", ascending=False).reset_index(drop=True)

    edited_df = st.data_editor(
        table_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "category": st.column_config.TextColumn("Category"),
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),  # OK now; dtype is datetime
            "amount": st.column_config.NumberColumn("Amount ($)", step=1.0, format="%.2f"),
            "description": st.column_config.TextColumn("Description"),
        },
        key="expenses_editor",
    )

    # Save edited table
    if st.button("💾 Save Expenses"):
        # Normalize again (if user edited types)
        edited_df = normalize_expenses_df(edited_df)
        # Keep changes in memory
        st.session_state.exp_df = edited_df.copy()
        # Persist (dates as strings in file)
        out = edited_df.copy()
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        out.to_csv(EXPENSES_PATH, index=False)
        st.success("✅ Expenses saved successfully!")

if __name__ == "__main__":
    main()
