#!/usr/bin/env python3
"""
patient_ui_research_enhanced.py

Researcher-themed UI with enhanced visuals and sequential numeric IDs.
"""

import re
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process
from io import BytesIO
from collections import defaultdict
import numpy as np
import time

# -------------------------
# Config
# -------------------------
NAME_SIMILARITY_THRESHOLD = 65
OUTPUT_PROCESSED = "Processed_Patients.xlsx"
OUTPUT_DUPLICATES = "Duplicates_For_Review.xlsx"

# -------------------------
# Helpers
# -------------------------
def normalize_name(name: str) -> str:
    if pd.isna(name): return ""
    s = str(name).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def normalize_gender(g: str) -> str:
    if pd.isna(g): return ""
    s = str(g).strip().lower()
    if s in ("m", "male", "man"): return "male"
    if s in ("f", "female", "woman"): return "female"
    if s in ("o", "other", "non-binary", "nb"): return "other"
    return s

def soundex(name: str) -> str:
    if not name: return ""
    name = name.upper()
    codes = {"BFPV":"1","CGJKQSXZ":"2","DT":"3","L":"4","MN":"5","R":"6"}
    sndx = name[0]
    for char in name[1:]:
        for key, val in codes.items():
            if char in key:
                code = val
                if code != sndx[-1]:
                    sndx += code
                break
        else:
            sndx += "0"
    sndx = sndx.replace("0", "")
    return (sndx + "000")[:4]

class DSU:
    def __init__(self, n): self.parent, self.size = list(range(n)), [1]*n
    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a
    def union(self, a, b):
        pa, pb = self.find(a), self.find(b)
        if pa == pb: return
        if self.size[pa] < self.size[pb]: pa, pb = pb, pa
        self.parent[pb], self.size[pa] = pa, self.size[pa]+self.size[pb]

def detect_duplicates(df: pd.DataFrame) -> pd.Series:
    names, dobs, genders, sdx = df["Name_norm"], df["DOB_parsed"], df["Gender_norm"], df["Soundex"]
    blocks = defaultdict(list)
    for idx, (d, g, sx) in enumerate(zip(dobs, genders, sdx)):
        dob_key = pd.NaT if pd.isna(d) else d.isoformat()
        blocks[(dob_key, g, sx[:2])].append(idx)

    dsu = DSU(len(df))
    for _, indices in blocks.items():
        if len(indices) < 2: continue
        block_names = [names[i] for i in indices]
        matrix = process.cdist(block_names, block_names, scorer=fuzz.partial_ratio)
        for i in range(len(block_names)):
            for j in range(i+1, len(block_names)):
                if matrix[i][j] >= NAME_SIMILARITY_THRESHOLD:
                    dsu.union(indices[i], indices[j])

    cluster_map, cluster_ids, cluster_counter, counts = {}, [-1]*len(df), 0, {}
    for i in range(len(df)): counts[dsu.find(i)] = counts.get(dsu.find(i), 0)+1
    for i in range(len(df)):
        root = dsu.find(i)
        if counts[root] > 1:
            if root not in cluster_map:
                cluster_map[root] = cluster_counter
                cluster_counter += 1
            cluster_ids[i] = cluster_map[root]
    return pd.Series(cluster_ids, index=df.index, dtype="Int64")

def process_file(file) -> tuple:
    xls = pd.ExcelFile(file)
    frames = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, dtype=object)
        df["_source_sheet"], df["_source_row"] = sheet, df.index+1
        frames.append(df)
    df = pd.concat(frames, ignore_index=True, sort=False)

    # Normalization
    df["Name_norm"] = df["Name"].fillna("").astype(str).apply(normalize_name)
    df["Gender_norm"] = df["Gender"].fillna("").astype(str).apply(normalize_gender)
    df["DOB_parsed"] = pd.to_datetime(df["DOB"], errors="coerce").dt.normalize()
    df["Soundex"] = df["Name_norm"].apply(lambda n: soundex(n.split(" ")[0] if n else ""))

    # Ordered numeric Unique IDs
    df["Unique_ID"] = range(1, len(df) + 1)

    # Detect duplicates
    df["Cluster_ID"] = detect_duplicates(df)
    df["Is_Duplicate"] = df["Cluster_ID"].notna() & (df["Cluster_ID"] >= 0)

    # Select output columns
    out_cols = ["Unique_ID","Cluster_ID","Is_Duplicate",
                "Name","DOB","Gender","Nationality","Disease","Symptoms",
                "_source_sheet","_source_row"]
    df_out = df[out_cols].copy()

    # Write outputs
    processed_buf, duplicates_buf = BytesIO(), BytesIO()
    with pd.ExcelWriter(processed_buf, engine="openpyxl") as writer:
        df_out.to_excel(writer, sheet_name="All_Patients", index=False)
        summary = {
            "Total_Records":[len(df)],
            "Duplicate_Records":[df["Is_Duplicate"].sum()],
            "Duplicate_Clusters":[df["Cluster_ID"].dropna().nunique()]
        }
        pd.DataFrame(summary).to_excel(writer, sheet_name="Summary", index=False)
    with pd.ExcelWriter(duplicates_buf, engine="openpyxl") as writer:
        df[df["Is_Duplicate"]].sort_values(["Cluster_ID","_source_sheet","_source_row"]).to_excel(
            writer, sheet_name="Duplicates_All", index=False)

    processed_buf.seek(0), duplicates_buf.seek(0)
    return processed_buf, duplicates_buf, df_out, df[df["Is_Duplicate"]]

# -------------------------
# Streamlit Research UI
# -------------------------
def main():
    st.set_page_config(page_title="Research Patient Processor", layout="wide")

    # Custom CSS
    st.markdown("""
    <style>
        .main {background-color: #f8fbfd;}
        h1, h2, h3 {color: #1f3c88;}
        .banner {
            background: linear-gradient(90deg, #1f3c88, #2c5282);
            color: white;
            padding: 1rem 2rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .metric-card {
            background: white; 
            padding: 1rem; 
            border-radius: 12px; 
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header banner
    st.markdown("<div class='banner'><h1>🔬 Hospital Patient Data Processor</h1><p>Researcher Edition — Clean IDs, Smart Duplicates</p></div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])
    if uploaded_file:
        progress = st.progress(0)
        status = st.empty()
        with st.spinner("⏳ Analyzing patient records..."):
            for pct, msg in zip(range(0, 100, 20),
                                ["Loading data...", "Normalizing entries...", "Detecting duplicates...", "Compiling clusters...", "Finalizing report..."]):
                time.sleep(0.4)
                progress.progress(pct+20)
                status.text(msg)

            processed_buf, duplicates_buf, df_out, df_dupes = process_file(uploaded_file)
            progress.progress(100)
            status.text("✅ Processing complete!")

        # Summary metrics
        total = len(df_out)
        dupes = df_out["Is_Duplicate"].sum()
        clusters = df_out["Cluster_ID"].dropna().nunique()

        st.markdown("## 📊 Research Summary")
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"<div class='metric-card'><h2>{total}</h2><p>Total Patients</p></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='metric-card'><h2>{dupes}</h2><p>Duplicates Detected</p></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='metric-card'><h2>{clusters}</h2><p>Duplicate Clusters</p></div>", unsafe_allow_html=True)

        # Tabs for better navigation
        tab1, tab2, tab3 = st.tabs(["📥 Downloads", "📋 Processed Data", "⚠️ Duplicates"])
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download Processed Patients",
                                   data=processed_buf,
                                   file_name=OUTPUT_PROCESSED,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col2:
                st.download_button("⬇️ Download Duplicates for Review",
                                   data=duplicates_buf,
                                   file_name=OUTPUT_DUPLICATES,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with tab2:
            st.dataframe(df_out.head(15))
        with tab3:
            st.dataframe(df_dupes.head(15))

if __name__ == "__main__":
    main()
