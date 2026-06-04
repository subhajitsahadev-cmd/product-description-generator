import os
import sys
import pandas as pd
from dotenv import load_dotenv
from generator import build_pipeline, generate_for_product

# --- settings you can change ---
OUTPUT_FILE = "output.xlsx"   # where results are saved
LIMIT = 10                    # process this many products at once
 
 
def get_input_path() -> str:
    """
    Decide which file to read.
    - If you typed a file name after 'python main.py', use that.
    - Otherwise, ask you to type/paste the path.
    """
    if len(sys.argv) > 1:
        # sys.argv[1] is the first thing you typed after the script name
        path = sys.argv[1]
    else:
        path = input("Enter path to your CSV/Excel file: ").strip().strip('"')
 
    # Make sure the file actually exists before we go further
    if not path:
        raise SystemExit("No file given. Run: python main.py yourfile.csv")
    if not os.path.exists(path):
        raise SystemExit(f"File not found: {path}")
    if not path.lower().endswith((".csv", ".xlsx", ".xls")):
        raise SystemExit("File must be a .csv, .xlsx, or .xls file.")
    return path
 
 
# def read_table(path: str) -> pd.DataFrame:
#     """Read either a CSV or an Excel file into a table."""
#     if path.lower().endswith(".csv"):
#         return pd.read_csv(path)
#     return pd.read_excel(path)

def read_table(path: str) -> pd.DataFrame:
    """Read either a CSV or an Excel file. Try UTF-8, fall back to Windows encoding."""
    if path.lower().endswith(".csv"):
        try:
            return pd.read_csv(path)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin-1")
    return pd.read_excel(path)
 
 
def flatten(sku, content, result) -> dict:
    """Turn 3 nested variants into one flat row of columns."""
    row = {"id": sku, "content": content}
    variants = result.variants if result else []
    for i in range(3):              # we want exactly 3 sets
        n = i + 1
        if i < len(variants):
            v = variants[i]
            row[f"title{n}"] = v.title
            row[f"description{n}"] = v.description
            row[f"meta title{n}"] = v.meta_title
            row[f"meta description{n}"] = v.meta_description
        else:                       # safety net if AI returned fewer than 3
            row[f"title{n}"] = ""
            row[f"description{n}"] = ""
            row[f"meta title{n}"] = ""
            row[f"meta description{n}"] = ""
    return row
 
 
def main():
    # STEP 1: load the key from .env into the environment
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("No OPENAI_API_KEY found. Put it in your .env file.")
 
    # STEP 2: figure out which file to read, then read it
    input_path = get_input_path()
    print(f"Reading: {input_path}")
    df = read_table(input_path)
 
    # make column names lowercase so 'ID' or 'Content' still work
    df.columns = [c.strip().lower() for c in df.columns]
    if "id" not in df.columns or "content" not in df.columns:
        raise SystemExit("Input must have columns named 'id' and 'content'.")
 
    df = df.head(LIMIT)              # only first 10
 
    # STEP 3: build the pipeline ONCE, then reuse it for every product
    pipeline = build_pipeline()
 
    rows = []
    for _, product in df.iterrows():
        sku, content = product["id"], product["content"]
        try:
            result = generate_for_product(pipeline, sku, content)
            print(f"  done: {sku}")
        except Exception as e:
            print(f"  FAILED: {sku} -> {e}")
            result = None
        rows.append(flatten(sku, content, result))
 
    # STEP 4: build the output table with columns in the exact order you want
    columns = ["id", "content"]
    for n in (1, 2, 3):
        columns += [f"title{n}", f"description{n}", f"meta title{n}", f"meta description{n}"]
    out = pd.DataFrame(rows)[columns]
 
    # STEP 5: save it
    out.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(out)} products to {OUTPUT_FILE}")
 
 
if __name__ == "__main__":
    main()