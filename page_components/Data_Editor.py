# Data_Editor.py
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
import io
import re

st.set_page_config(page_title="📝 Data Editor", layout="wide")

# ---------- paths & helpers ----------
DEFAULT_PATH = Path("data/combined.csv")
BACKUP_DIR = Path("data/backups")

RETAIN_BACKUPS = 10  # how many backups to keep (most recent first)

def prune_backups(original: Path, keep: int = RETAIN_BACKUPS):
    """Delete older backups beyond 'keep' most recent for the given original file."""
    try:
        files = list_backups(original)  # already sorted newest->oldest
        for p in files[keep:]:
            try:
                p.unlink()
            except Exception:
                pass  # ignore deletion errors
    except Exception:
        pass

def parse_dates_safely(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def load_csv(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        df = parse_dates_safely(df, ["Arrival Date", "Departure Date", "Date"])
        return df
    except Exception as e:
        st.error(f"Failed to read {path}: {e}")
        return pd.DataFrame()

def save_csv(path: Path, df: pd.DataFrame) -> bool:
    try:
        out = df.copy()
        # stringify datetimes
        for c in out.columns:
            if pd.api.types.is_datetime64_any_dtype(out[c]):
                out[c] = out[c].dt.strftime("%Y-%m-%d")
        path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(path, index=False)
        return True
    except Exception as e:
        st.error(f"Failed to save to {path}: {e}")
        return False

def ensure_backup_dir(): BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def make_backup(original: Path, df: pd.DataFrame):
    ensure_backup_dir()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bp = BACKUP_DIR / f"{original.stem}__backup__{ts}.csv"
    ok = save_csv(bp, df.copy())
    if ok:
        prune_backups(original, keep=RETAIN_BACKUPS)  # 👈 prune here
        return bp
    return None


def list_backups(original: Path):
    ensure_backup_dir()
    return sorted(BACKUP_DIR.glob(f"{original.stem}__backup__*.csv"), reverse=True)

def df_download_bytes(df: pd.DataFrame) -> bytes:
    buff = io.StringIO()
    tmp = df.copy()
    for c in tmp.columns:
        if pd.api.types.is_datetime64_any_dtype(tmp[c]):
            tmp[c] = tmp[c].dt.strftime("%Y-%m-%d")
    tmp.to_csv(buff, index=False)
    return buff.getvalue().encode("utf-8")

def nights_between(arrival: date, departure: date) -> int:
    """Half-open [arrival, departure)."""
    return max((departure - arrival).days, 0)

def months_active_inclusive(arrival: date, departure: date) -> int:
    """
    Count distinct calendar months touched by the stay.
    Departure is checkout day (not included), so use (departure - 1 day) if duration>0; else arrival.
    """
    if departure <= arrival:
        d = arrival
    else:
        d = departure - timedelta(days=1)
    return (d.year * 12 + d.month) - (arrival.year * 12 + arrival.month) + 1

def months_active_labels(arrival: date, departure: date, fmt: str = "%m/%Y") -> str:
    """
    Return a comma-separated list of Month/Year labels touched by the stay,
    counting months in the half-open interval [arrival, departure).
    """
    if not isinstance(arrival, date) or not isinstance(departure, date):
        return ""
    # if same-day or invalid, still count arrival's month
    last = arrival if departure <= arrival else (departure - timedelta(days=1))
    # iterate months from arrival's first of month to last's first of month
    y, m = arrival.year, arrival.month
    labels = []
    while (y, m) <= (last.year, last.month):
        labels.append(f"{m:02d}/{y}") if fmt == "%m/%Y" else labels.append(date(y, m, 1).strftime(fmt))
        # increment month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return ", ".join(labels)

def last_known_attrs(df: pd.DataFrame, name: str):
    """Most recent attributes for returning pet (also returns Platform)."""
    if "Name" not in df.columns or df.empty:
        return {}
    sub = df[df["Name"].astype(str).str.strip().str.lower() == str(name).strip().lower()].copy()
    if sub.empty:
        return {}
    if "Arrival Date" in sub.columns:
        sub = sub.sort_values("Arrival Date", ascending=False)
    row = sub.iloc[0].to_dict()
    return {
        "Platform": row.get("Platform", ""),
        "Breed": row.get("Breed", ""),
        "Sex": row.get("Sex", ""),
        "Species": row.get("Species", ""),
        "Spray/Neuter": row.get("Spray/Neuter", row.get("Spay/Neuter", "")),
        "Type": row.get("Type", ""),
        "Family Members": row.get("Family Members", ""),
    }

def recompute_tips_and_months(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # tips = max(Payment Received - Price, 0)
    if "Price" in out.columns:
        out["Price"] = pd.to_numeric(out["Price"], errors="coerce").fillna(0.0)
    if "Payment Received" in out.columns:
        out["Payment Received"] = pd.to_numeric(out["Payment Received"], errors="coerce").fillna(0.0)
    if {"Payment Received", "Price"}.issubset(out.columns):
        out["tips"] = (out["Payment Received"] - out["Price"]).clip(lower=0).round(2)

    # months_active = "MM/YYYY, MM/YYYY, ..."
    if {"Arrival Date", "Departure Date"}.issubset(out.columns):
        out["Arrival Date"] = pd.to_datetime(out["Arrival Date"], errors="coerce")
        out["Departure Date"] = pd.to_datetime(out["Departure Date"], errors="coerce")

        def _labels(row):
            a, d = row.get("Arrival Date"), row.get("Departure Date")
            if pd.isna(a) or pd.isna(d):
                return row.get("months_active", "")
            return months_active_labels(a.date(), d.date(), fmt="%m/%Y")

        out["months_active"] = out.apply(_labels, axis=1)

    return out

# ---------- page ----------
def main():
    st.session_state.current_page = "Data_Editor"
    st.title("📝 Kingdom Data Editor")

    # Theme inputs to dark-brown (matches your app palette)
    st.markdown("""
    <style>
    /* --- Text inputs --- */
    div[data-testid="stTextInput"] input {
    background: #c8a18f !important;   /* dark brown */
    color: #ffffff !important;
    border: 1px solid #c8a18f !important; /* warm brown */
    border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
    color: #f4cbba !important;         /* soft peach placeholder */
    }

    /* --- Selectbox --- */
    div[data-testid="stSelectbox"] > div > div {
    background: #c8a18f !important;
    color: #ffffff !important;
    border: 1px solid #c8a18f !important;
    border-radius: 8px !important;
    }
    div[data-testid="stSelectbox"] svg { color: #ffffff !important; }
    /* dropdown menu */
    div[data-testid="stSelectbox"] div[role="listbox"] {
    background: #c8a18f !important;
    color: #ffffff !important;
    border: 1px solid #c8a18f !important;
    }
    div[data-testid="stSelectbox"] div[role="option"] { color: #ffffff !important; }

    /* --- Date inputs --- */
    div[data-testid="stDateInput"] input {
    background: #c8a18f !important;
    color: #ffffff !important;
    border: 1px solid #c8a18f !important;
    border-radius: 8px !important;
    }
    div[data-testid="stDateInput"] button { color: #ffffff !important; }

    /* --- Number inputs (if you switch to st.number_input later) --- */
    div[data-testid="stNumberInput"] input[type="number"] {
    background: #5a3b2e !important;
    color: #ffffff !important;
    border: 1px solid #c8a18f !important;
    border-radius: 8px !important;
    }

    /* --- Buttons --- */
    .stButton > button {
    background: #5a3b2e !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    }
    .stButton > button:hover { background: #a77d6c !important; }

    /* --- Data editor surface (best effort) --- */
    div[data-testid="stDataEditor"] {
    background: #ffeada !important; /* page peach */
    border-radius: 12px !important;
    }
    div[data-testid="stDataEditor"] thead th {
    background: #c8a18f !important;
    color: #ffffff !important;
    }
    div[data-testid="stDataEditor"] tbody td {
    background: #ffeada !important;
    color: #5a3b2e !important;
    }

    /* --- Focus rings --- */
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stSelectbox"] > div > div:focus-within,
    div[data-testid="stDateInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus {
    outline: 2px solid #a77d6c !important;
    box-shadow: 0 0 0 1px #a77d6c !important;
    border-color: #a77d6c !important;
    }
    </style>
    """, unsafe_allow_html=True)

    save_target = DEFAULT_PATH
    if not save_target.exists():
        st.error(f"Expected CSV not found at **{save_target}**.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # Load (and keep a stable hidden row id in session for safe merging)
    if "_full_df" not in st.session_state:
        full = load_csv(save_target)
        if full.empty:
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()
        full = full.copy()
        full["Name"] = full.get("Name", "").astype(str)

        # ✅ add this
        full = recompute_tips_and_months(full)

        if "Arrival Date" in full.columns:
            full = full.sort_values("Arrival Date", ascending=False).reset_index(drop=True)

        full["_rid"] = range(len(full))
        st.session_state._next_rid = len(full)
        st.session_state._full_df = full
    else:
        full = st.session_state._full_df



    # ========= ADD BOOKING (TOP) =========
    st.subheader("➕ Add a Booking")

    
    # ===== 3 rows × 4 entries (Add a Booking) =====

    # Initialize date defaults for reliable Duration
    if "ab_arr_date" not in st.session_state:
        st.session_state.ab_arr_date = date.today()
    if "ab_dep_date" not in st.session_state:
        st.session_state.ab_dep_date = date.today() + timedelta(days=1)
    if "ab_duration" not in st.session_state:
        st.session_state.ab_duration = str(nights_between(st.session_state.ab_arr_date,
                                                        st.session_state.ab_dep_date))

    def _sync_duration():
        ad = st.session_state.get("ab_arr_date", date.today())
        dd = st.session_state.get("ab_dep_date", ad + timedelta(days=1))
        st.session_state["ab_duration"] = str(nights_between(ad, dd))

    # --- Row 1: Name / Platform / Type / Species ---
    default_name = st.session_state.get("ab_name", "")
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        name = st.text_input("Name", value=default_name, key="ab_name")
    prior = last_known_attrs(st.session_state._full_df, name) if name else {}
    with r1c2:
        platform = st.text_input("Platform", value=str(prior.get("Platform", "")))
    with r1c3:
        btype = st.text_input("Type", value=str(prior.get("Type", "Boarding")))
    with r1c4:
        species_default = str(prior.get("Species", "Dog")).title()
        species = st.selectbox(
            "Species", ["Dog", "Cat", "Other"],
            index=(["Dog","Cat","Other"].index(species_default)
                if species_default in ["Dog","Cat","Other"] else 0)
        )

    # --- Row 2: Breed / Sex / Spay-Neuter / Duration ---
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        breed = st.text_input("Breed", value=str(prior.get("Breed", "")))
    with r2c2:
        sex_default = str(prior.get("Sex", "Unknown")).title()
        sex = st.selectbox(
            "Sex", ["Male", "Female", "Unknown"],
            index=(["Male","Female","Unknown"].index(sex_default)
                if sex_default in ["Male","Female","Unknown"] else 2)
        )
    with r2c3:
        spay_default = str(prior.get("Spray/Neuter", "unknown")).lower()
        spay = st.selectbox(
            "Spay/Neuter", ["yes", "no", "unknown"],
            index=(["yes","no","unknown"].index(spay_default)
                if spay_default in ["yes","no","unknown"] else 2)
        )
    with r2c4:
        # Duration auto-updates when either date changes (below), but you can override manually
        duration_str = st.text_input(
            "Duration (nights)",
            value=st.session_state.get("ab_duration", "1"),
            key="ab_duration",
            help="Auto-updates from dates; you can override manually."
        )

    # --- Row 3: Arrival / Departure / Price / Payment ---
    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    with r3c1:
        arr_date = st.date_input(
            "Arrival Date",
            value=st.session_state.get("ab_arr_date", date.today()),
            key="ab_arr_date",
            on_change=_sync_duration
        )
    with r3c2:
        dep_date = st.date_input(
            "Departure Date",
            value=st.session_state.get("ab_dep_date", date.today() + timedelta(days=1)),
            key="ab_dep_date",
            on_change=_sync_duration
        )
    with r3c3:
        price = st.text_input("Price (total)", value="0")
    with r3c4:
        payment = st.text_input("Payment Received", value="0")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Add booking button (wider first column to avoid wrap if layout gets tight)
    add_col1, add_col2, add_col3, add_col4 = st.columns([2,1,1,6])
    with add_col4:
        if st.button("Add booking", type="primary", key="btn_add_booking"):
            if not name.strip():
                st.error("Name is required.")
            elif dep_date <= arr_date:
                st.error("Departure Date must be AFTER Arrival Date.")
            else:
                # Convert text inputs to numeric safely
                try:
                    price_val = float(price)
                except Exception:
                    price_val = 0.0
                try:
                    duration_val = int(duration_str)
                except Exception:
                    duration_val = nights_between(arr_date, dep_date)
                try:
                    payment_val = float(payment)
                except Exception:
                    payment_val = 0.0

                # Derived values (leave duration as entered/derived above)
                derived_daily = round(price_val / duration_val, 2) if duration_val > 0 else 0.0
                derived_tips = round(max(payment_val - price_val, 0.0), 2)
                derived_months_active = months_active_labels(arr_date, dep_date, fmt="%m/%Y")
                family_members = str(prior.get("Family Members", ""))  # <- add this line

                new_row = {
                    "Platform": platform,
                    "Type": btype,
                    "Name": name.strip(),
                    "Breed": breed,
                    "Sex": sex,
                    "Species": species,
                    "Spray/Neuter": spay,
                    "Family Members": family_members,
                    "Arrival Date": pd.to_datetime(arr_date),
                    "Departure Date": pd.to_datetime(dep_date),
                    "Duration": duration_val,
                    "Price": round(price_val, 2),
                    "Payment Received": round(payment_val, 2),
                    "daily price": derived_daily,
                    "tips": derived_tips,
                    "months_active": derived_months_active
                }

                # Assign _rid and append
                rid = st.session_state._next_rid
                st.session_state._next_rid += 1
                new_row["_rid"] = rid

                full = st.session_state._full_df
                full = pd.concat([full, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state._full_df = full

                # Backup + save to disk (without _rid)
                disk_df = load_csv(DEFAULT_PATH)
                if not disk_df.empty:
                    make_backup(DEFAULT_PATH, disk_df)
                if save_csv(DEFAULT_PATH, full.drop(columns=["_rid"], errors="ignore")):
                    st.success(f"Added booking for {name} and saved to {DEFAULT_PATH}")

    st.markdown("---")

    # ========= SEARCH =========
    q = st.text_input("🔎 Search pet by name", placeholder="e.g. luna, appa, mil",
                      help="Partial matches allowed; separate multiple names with commas.")
    terms = [t.strip() for t in q.split(",") if t.strip()] if q else []
    if terms:
        safe_terms = [re.escape(t) for t in terms]
        pat = re.compile("|".join(safe_terms), flags=re.IGNORECASE)
        mask = full["Name"].astype(str).str.contains(pat, na=False)
        view = full.loc[mask].copy()
    else:
        view = full.copy()

    # ✅ Keep view sorted too
    if "Arrival Date" in view.columns:
        view = view.sort_values("Arrival Date", ascending=False).reset_index(drop=True)
    st.caption(f"Showing {len(view)} of {len(full)} rows")

    # ========= EDITOR =========
    # Keep _rid as index; hide some columns from UI via column_order
    show = view.set_index("_rid")
    all_cols = list(show.columns)

    # Hide ONLY in the table (they remain in the data)
    hidden_cols = {"months_active", "Family Members", "Spray/Neuter", "Type"}
    column_order = [c for c in all_cols if c not in hidden_cols]

    column_config = {}
    if "Arrival Date" in show.columns:
        column_config["Arrival Date"] = st.column_config.DateColumn("Arrival Date", format="YYYY-MM-DD")
    if "Departure Date" in show.columns:
        column_config["Departure Date"] = st.column_config.DateColumn("Departure Date", format="YYYY-MM-DD")
    if "daily price" in show.columns:
        column_config["daily price"] = st.column_config.NumberColumn("daily price", step=0.01)
    if "tips" in show.columns:
        column_config["tips"] = st.column_config.NumberColumn("tips", step=0.01, format="%.2f")

    st.subheader("🔧 Edit Table")
    edited = st.data_editor(
        show,
        num_rows="dynamic",          # allow add/delete inline
        use_container_width=True,
        hide_index=True,             # hides the _rid from UI
        column_config=column_config,
        column_order=column_order,   # hides specified columns
        height=700,
        key="data_editor_main",
    )

    st.divider()
    left, mid, right = st.columns(3)

    with left:
        if st.button("💾 Save Changes", type="primary", key="save_btn"):
            # Merge edits back into the full df
            edited = edited.copy()
            edited.index.name = "_rid"
            edited.reset_index(inplace=True)

            view_rids = set(show.index.tolist())

            # Split edited rows into existing and new
            existing_mask = edited["_rid"].isin(view_rids)
            edited_existing = edited.loc[existing_mask].copy()
            edited_new = edited.loc[~existing_mask].copy()

            # Update existing rows in the full df (by _rid)
            cols_to_update = [c for c in full.columns if c != "_rid"]
            full_indexed = full.set_index("_rid")
            full_indexed.update(edited_existing.set_index("_rid")[cols_to_update])
            full = full_indexed.reset_index()

            # Handle deletions
            edited_rids = set(edited_existing["_rid"].tolist())
            deleted_rids = view_rids - edited_rids
            if deleted_rids:
                full = full[~full["_rid"].isin(deleted_rids)].copy()

            # Handle newly added rows from the editor UI
            if not edited_new.empty:
                start = st.session_state._next_rid
                edited_new["_rid"] = range(start, start + len(edited_new))
                st.session_state._next_rid = start + len(edited_new)

                if "Arrival Date" in edited_new.columns and "Departure Date" in edited_new.columns:
                    for i, r in edited_new.iterrows():
                        try:
                            ad = pd.to_datetime(r.get("Arrival Date"))
                            dd = pd.to_datetime(r.get("Departure Date"))

                            # Only backfill Duration if empty/missing; DO NOT recompute globally
                            dur_field = r.get("Duration")
                            if pd.isna(dur_field) or str(dur_field).strip() == "":
                                edited_new.at[i, "Duration"] = nights_between(ad.date(), dd.date())

                            # numeric fields
                            prc = float(r.get("Price", 0) or 0)
                            pay = float(r.get("Payment Received", 0) or 0)
                            try:
                                dur_val = int(edited_new.at[i, "Duration"] or 0)
                            except Exception:
                                dur_val = 0

                            if dur_val > 0:
                                edited_new.at[i, "daily price"] = round(prc / dur_val, 2)

                            edited_new.at[i, "tips"] = round(max(pay - prc, 0.0), 2)
                            edited_new.at[i, "months_active"] = months_active_labels(ad.date(), dd.date(), fmt="%m/%Y")
                        except Exception:
                            pass

                full = pd.concat([full, edited_new], ignore_index=True)

            # Recompute daily price for ALL rows from Price & Duration (no duration recompute)
            if {"Price", "Duration"}.issubset(full.columns):
                full["Price"] = pd.to_numeric(full["Price"], errors="coerce")
                full["Duration"] = pd.to_numeric(full["Duration"], errors="coerce")
                # Avoid division by zero; NaN if Duration <= 0 or missing
                dur = full["Duration"].where(full["Duration"] > 0)
                full["daily price"] = (full["Price"] / dur).round(2)

            # Save back (recompute tips & months only)
            full = recompute_tips_and_months(full)
            st.session_state._full_df = full

            to_save = full.drop(columns=["_rid"], errors="ignore")

            # ✅ Persist sorted order in CSV
            if "Arrival Date" in to_save.columns:
                to_save = to_save.sort_values("Arrival Date", ascending=False).reset_index(drop=True)

            disk_df = load_csv(DEFAULT_PATH)
            if not disk_df.empty:
                make_backup(DEFAULT_PATH, disk_df)
            if save_csv(DEFAULT_PATH, to_save):
                st.success(f"Saved changes to {DEFAULT_PATH}")

    with right:
        backups = list_backups(DEFAULT_PATH)
        if backups:
            # Button on top
            restore_clicked = st.button(
                "↩️ Restore Selected Backup",
                key="restore_btn",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.get("restore_select") is None
            )

            # Dropdown below (no label, with placeholder)
            chosen = st.selectbox(
                "",
                backups,
                format_func=lambda p: p.name,
                key="restore_select",
                label_visibility="collapsed",
                index=None,
                placeholder="Select a backup…"
            )

            if restore_clicked:
                selected = st.session_state.get("restore_select")
                if selected is None:
                    st.warning("Please select a backup first.")
                else:
                    backup_df = load_csv(selected)
                    if not backup_df.empty:
                        backup_df = backup_df.copy()
                        backup_df["Name"] = backup_df.get("Name", "").astype(str)
                        backup_df["_rid"] = range(len(backup_df))
                        st.session_state._next_rid = len(backup_df)
                        st.session_state._full_df = backup_df
                        if save_csv(DEFAULT_PATH, backup_df.drop(columns=["_rid"], errors="ignore")):
                            st.success(f"Restored {selected.name} to {DEFAULT_PATH}")
        else:
            st.info("No backups yet. A backup is created automatically when you save.")



    '''with right:
        # Download current view (what you see) as CSV (only visible cols)
        def bytes_for(df):
            buff = io.StringIO()
            tmp = df.copy()
            for c in tmp.columns:
                if pd.api.types.is_datetime64_any_dtype(tmp[c]):
                    tmp[c] = tmp[c].dt.strftime("%Y-%m-%d")
            tmp.to_csv(buff, index=False)
            return buff.getvalue().encode("utf-8")

        view_to_download = edited[column_order]
        st.download_button(
            "⬇️ Download current view (CSV)",
            data=bytes_for(view_to_download),
            file_name=f"data_editor_view__{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv",
            mime="text/csv",
            key="download_btn",
        )'''

    # Close scoped container
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
