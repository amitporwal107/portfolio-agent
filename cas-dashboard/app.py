import streamlit as st
import subprocess
import json
import tempfile
import pandas as pd
import os
import shutil
from datetime import datetime

st.set_page_config(layout="wide")

# ==============================
# DIR SETUP
# ==============================
UPLOAD_DIR = "uploads"
ARCHIVE_DIR = "archive"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# ==============================
# STATE
# ==============================
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None

if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None

if "show_password" not in st.session_state:
    st.session_state.show_password = False

# ==============================
# ARCHIVE FUNCTION
# ==============================
def archive_existing(filename):
    pdf = os.path.join(UPLOAD_DIR, filename)
    jsn = pdf.replace(".pdf", ".json")

    if os.path.exists(pdf):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = os.path.join(ARCHIVE_DIR, ts)
        os.makedirs(folder, exist_ok=True)

        shutil.move(pdf, os.path.join(folder, filename))

        if os.path.exists(jsn):
            shutil.move(jsn, os.path.join(folder, filename.replace(".pdf", ".json")))

# ==============================
# MCP CALL (FINAL FIXED)
# ==============================
def call_mcp(pdf_bytes, password):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        path = tmp.name

    # ✅ CRITICAL FIX (Windows safe)
    path_js = json.dumps(path)

    script = f"""
import fs from 'fs';
import {{ Client }} from '@modelcontextprotocol/sdk/client/index.js';
import {{ StdioClientTransport }} from '@modelcontextprotocol/sdk/client/stdio.js';

const run = async () => {{
  try {{
    const transport = new StdioClientTransport({{
      command: "node",
      args: ["../cas-mcp-server/server.js"],
      env: {{ CAS_PARSER_API_KEY: "sandbox-with-json-responses" }}
    }});

    const client = new Client({{ name: "ui", version: "1.0.0" }});
    await client.connect(transport);

    const fileBuffer = fs.readFileSync({path_js});
    const base64PDF = fileBuffer.toString("base64");

    const result = await client.callTool({{
      name: "smart_parse",
      arguments: {{
        pdf_file: base64PDF,
        password: "{password}"
      }}
    }});

    console.log(JSON.stringify(result));
  }} catch (err) {{
    console.error(err);
    process.exit(1);
  }}
}};

run();
"""

    script_path = path + ".mjs"

    with open(script_path, "w") as f:
        f.write(script)

    result = subprocess.run(
        ["node", "--no-warnings", script_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(result.stderr)

    return json.loads(result.stdout)

# ==============================
# DATA EXTRACTION
# ==============================
def extract_data(data):
    mf, eq = [], []

    for f in data.get("folios", []):
        for s in f.get("schemes", []):
            if isinstance(s, dict):
                invested = s.get("invested_value", 0)
                current = s.get("current_value", 0)

                mf.append({
                    "Scheme": s.get("scheme_name"),
                    "Invested": invested,
                    "Current": current,
                    "Gain": current - invested,
                    "Return %": ((current - invested) / invested * 100) if invested else 0
                })

    for a in data.get("demat_accounts", []):
        for h in a.get("holdings", []):
            if isinstance(h, dict):
                eq.append({
                    "Stock": h.get("company_name"),
                    "Current": h.get("current_value", 0)
                })

    return pd.DataFrame(mf), pd.DataFrame(eq)

# ==============================
# UI
# ==============================
st.title("📊 Portfolio Dashboard")

uploaded = st.file_uploader("Upload CAS PDF", type=["pdf"])

if uploaded and uploaded.name != st.session_state.last_uploaded:

    archive_existing(uploaded.name)

    st.session_state.pdf_bytes = uploaded.getvalue()
    st.session_state.parsed_data = None
    st.session_state.show_password = True
    st.session_state.last_uploaded = uploaded.name

    st.rerun()

# ==============================
# PASSWORD INPUT
# ==============================
if st.session_state.show_password:
    pwd = st.text_input("Enter CAS Password", type="password")

    if st.button("Parse"):
        with st.spinner("Parsing..."):
            data = call_mcp(st.session_state.pdf_bytes, pwd)

        if "error" in data:
            st.error("❌ Invalid password")
        else:
            st.session_state.parsed_data = data
            st.session_state.show_password = False
            st.success("✅ Parsed successfully")
            st.rerun()

# ==============================
# DISPLAY
# ==============================
if st.session_state.parsed_data:

    data = st.session_state.parsed_data
    mf_df, eq_df = extract_data(data)

    total_mf = mf_df["Current"].sum() if not mf_df.empty else 0
    total_eq = eq_df["Current"].sum() if not eq_df.empty else 0
    total = total_mf + total_eq

    # Summary
    c1, c2, c3 = st.columns(3)
    c1.metric("Mutual Funds", f"₹{total_mf:,.0f}")
    c2.metric("Equity", f"₹{total_eq:,.0f}")
    c3.metric("Total", f"₹{total:,.0f}")

    # Tabs
    tab1, tab2 = st.tabs(["Mutual Funds", "Equity"])

    with tab1:
        st.subheader(f"{len(mf_df)} Schemes")
        if not mf_df.empty:
            st.dataframe(
                mf_df.sort_values("Current", ascending=False),
                use_container_width=True
            )

    with tab2:
        st.subheader(f"{len(eq_df)} Holdings")
        if not eq_df.empty:
            st.dataframe(
                eq_df.sort_values("Current", ascending=False),
                use_container_width=True
            )

