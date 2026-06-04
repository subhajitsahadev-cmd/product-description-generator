"""
app.py
======
The browser UI for the product generator, built with Streamlit.

It reuses the SAME code you already wrote:
  - build_pipeline / generate_for_product  -> from generator.py
  - flatten                                -> from main.py
So nothing is duplicated. The UI is just a friendly front door.

Run it like this (NOT with "python"):
    streamlit run app.py

A browser tab opens automatically. You upload a file, click Generate,
watch the progress bar, preview the results, and download the Excel.
"""

import io
import pandas as pd
import streamlit as st
# from dotenv import load_dotenv

from generator import build_pipeline, generate_for_product
from main import flatten          # reuse the exact same flatten() from main.py

# Load the OPENAI_API_KEY from your .env file
# load_dotenv()

import os
from dotenv import load_dotenv

# Local: read .env file. Cloud: read Streamlit secrets.
load_dotenv()
if "MISTRAL_API_KEY" in st.secrets:
    os.environ["MISTRAL_API_KEY"] = st.secrets["MISTRAL_API_KEY"]

# Fail loudly with a clear message instead of a blank crash
if not os.getenv("MISTRAL_API_KEY"):
    st.error("MISTRAL_API_KEY is missing. Add it in Settings → Secrets.")
    st.stop()

# ---------- page setup ----------
st.set_page_config(page_title="AI Product Description Generator", page_icon="🛍️")
st.title("🛍️ AI Product Description Generator")
st.write("Upload a CSV or Excel file with two columns: **id** and **content**.")

# ---------- the upload box ----------
# This is the real drag-and-drop / browse button you wanted.
uploaded = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])

# How many products to process this run
limit = st.number_input("How many products to process", min_value=1, max_value=50, value=10)


# def read_uploaded(file) -> pd.DataFrame:
#     """Read the uploaded file (Streamlit hands us the file in memory)."""
#     if file.name.lower().endswith(".csv"):
#         return pd.read_csv(file)
#     return pd.read_excel(file)

def read_uploaded(file) -> pd.DataFrame:
    """Read the uploaded file. Try UTF-8, fall back to Windows encoding."""
    if file.name.lower().endswith(".csv"):
        try:
            return pd.read_csv(file)
        except UnicodeDecodeError:
            file.seek(0)                         # rewind the file to the start
            return pd.read_csv(file, encoding="latin-1")
    return pd.read_excel(file)

# ---------- run when the button is clicked ----------
# st.button(...) is True only on the click, so everything indented under
# this 'if' runs once when the user presses Generate.
if uploaded is not None and st.button("Generate"):

    # 1) Read and check the file
    df = read_uploaded(uploaded)
    df.columns = [c.strip().lower() for c in df.columns]

    if "id" not in df.columns or "content" not in df.columns:
        st.error("Your file must have columns named 'id' and 'content'.")
        st.stop()   # stop here, don't run the rest

    df = df.head(limit)

    # 2) Build the pipeline once
    pipeline = build_pipeline()

    # 3) Loop over products, showing a progress bar
    rows = []
    progress = st.progress(0, text="Starting...")
    for i, (_, product) in enumerate(df.iterrows()):
        sku, content = product["id"], product["content"]
        try:
            result = generate_for_product(pipeline, sku, content)
        except Exception as e:
            st.warning(f"SKU {sku} failed: {e}")
            result = None
        rows.append(flatten(sku, content, result))
        # update the bar (value must be between 0.0 and 1.0)
        progress.progress((i + 1) / len(df), text=f"Done {i + 1} of {len(df)}")

    # 4) Build the output table in the exact column order
    columns = ["id", "content"]
    for n in (1, 2, 3):
        columns += [f"title{n}", f"description{n}", f"meta title{n}", f"meta description{n}"]
    out = pd.DataFrame(rows)[columns]

    st.success(f"Generated copy for {len(out)} products!")
    st.dataframe(out)   # show the table in the browser

    # 5) Make a download button.
    # We write the Excel into memory (a buffer) instead of to disk,
    # because the browser downloads the bytes directly.
    buffer = io.BytesIO()
    out.to_excel(buffer, index=False)
    st.download_button(
        label="⬇️ Download Excel",
        data=buffer.getvalue(),
        file_name="product_descriptions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )