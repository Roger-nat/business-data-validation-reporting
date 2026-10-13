import io
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="DataSure | Validation & Reporting", page_icon="📊", layout="wide")

REQUIRED_COLUMNS = ["record_id", "name", "email", "amount", "date", "status"]

st.title("📊 DataSure")
st.caption("Business Data Validation & Reporting Automation")
st.write("Upload a CSV or Excel file to validate records, identify data-quality issues, and generate a clean report.")

with st.sidebar:
    st.header("Validation rules")
    check_duplicates = st.checkbox("Check duplicate records / IDs", value=True)
    check_email = st.checkbox("Validate email format", value=True)
    check_amount = st.checkbox("Flag negative amounts", value=True)
    check_date = st.checkbox("Validate dates", value=True)
    check_missing = st.checkbox("Flag missing required values", value=True)
    st.divider()
    st.caption("Privacy note: this demo processes files in the current app session. Do not upload sensitive or confidential data to an untrusted deployment.")

uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])

def load_file(file):
    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    aliases = {
        "id": "record_id", "customer_id": "record_id", "transaction_id": "record_id",
        "full_name": "name", "customer_name": "name",
        "e_mail": "email", "email_address": "email",
        "value": "amount", "total": "amount", "transaction_amount": "amount",
        "created_at": "date", "transaction_date": "date",
        "state": "status", "record_status": "status"
    }
    df = df.rename(columns={c: aliases[c] for c in df.columns if c in aliases})
    return df

def validate_data(df):
    result = df.copy()
    issues = [[] for _ in range(len(result))]
    available = set(result.columns)

    if check_missing:
        required_present = [c for c in REQUIRED_COLUMNS if c in available]
        for idx in range(len(result)):
            for col in required_present:
                val = result.iloc[idx][col]
                if pd.isna(val) or (isinstance(val, str) and not val.strip()):
                    issues[idx].append(f"Missing {col}")

    if check_duplicates and "record_id" in available:
        dup = result["record_id"].notna() & result["record_id"].astype(str).duplicated(keep=False)
        for idx in result.index[dup]:
            issues[result.index.get_loc(idx)].append("Duplicate record_id")
    elif check_duplicates:
        st.warning("Duplicate ID check skipped: no `record_id` column found.")

    if check_email and "email" in available:
        email = result["email"].fillna("").astype(str).str.strip()
        valid = email.str.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        for pos, is_valid in enumerate(valid):
            if email.iloc[pos] and not is_valid:
                issues[pos].append("Invalid email format")

    if check_amount and "amount" in available:
        numeric_amount = pd.to_numeric(result["amount"], errors="coerce")
        for pos, (raw, num) in enumerate(zip(result["amount"], numeric_amount)):
            if pd.notna(raw) and str(raw).strip() and pd.isna(num):
                issues[pos].append("Amount is not numeric")
            elif pd.notna(num) and num < 0:
                issues[pos].append("Negative amount")
        result["amount"] = numeric_amount

    if check_date and "date" in available:
        parsed = pd.to_datetime(result["date"], errors="coerce")
        for pos, (raw, parsed_date) in enumerate(zip(result["date"], parsed)):
            if pd.notna(raw) and str(raw).strip() and pd.isna(parsed_date):
                issues[pos].append("Invalid date")
        result["date"] = parsed

    result["validation_issues"] = ["; ".join(row) for row in issues]
    result["is_valid"] = result["validation_issues"].eq("")
    return result

def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")

if uploaded:
    try:
        raw_df = load_file(uploaded)
        df = normalize_columns(raw_df)
    except Exception as exc:
        st.error(f"Could not read this file: {exc}")
        st.stop()

    if df.empty:
        st.warning("The uploaded file has no data rows.")
        st.stop()

    st.subheader("1. Source data")
    st.caption(f"Loaded {len(df):,} rows and {len(df.columns):,} columns.")
    st.dataframe(df.head(100), use_container_width=True)

    st.subheader("2. Validation results")
    checked = validate_data(df)
    valid_count = int(checked["is_valid"].sum())
    invalid_count = int((~checked["is_valid"]).sum())
    quality = round((valid_count / len(checked)) * 100, 1) if len(checked) else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total records", f"{len(checked):,}")
    c2.metric("Valid records", f"{valid_count:,}")
    c3.metric("Records with issues", f"{invalid_count:,}")
    c4.metric("Quality score", f"{quality}%")

    tab1, tab2, tab3 = st.tabs(["All records", "Issues only", "Summary"])
    with tab1:
        st.dataframe(checked, use_container_width=True)
    with tab2:
        issues_df = checked.loc[~checked["is_valid"]].copy()
        if issues_df.empty:
            st.success("No validation issues found under the selected rules.")
        else:
            st.dataframe(issues_df, use_container_width=True)
    with tab3:
        issue_counts = {}
        for text in checked["validation_issues"]:
            if text:
                for issue in text.split("; "):
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
        if issue_counts:
            summary = pd.DataFrame([{"issue_type": k, "occurrences": v} for k, v in sorted(issue_counts.items())])
            st.dataframe(summary, use_container_width=True)
            st.bar_chart(summary.set_index("issue_type"))
        else:
            st.info("No issues to summarize.")

    st.subheader("3. Export reports")
    clean_df = checked.loc[checked["is_valid"]].drop(columns=["validation_issues", "is_valid"])
    issue_df = checked.loc[~checked["is_valid"]]
    summary_df = pd.DataFrame([
        {"metric": "total_records", "value": len(checked)},
        {"metric": "valid_records", "value": valid_count},
        {"metric": "records_with_issues", "value": invalid_count},
        {"metric": "quality_score_percent", "value": quality},
        {"metric": "generated_at", "value": datetime.now().isoformat(timespec="seconds")}
    ])
    col1, col2, col3 = st.columns(3)
    col1.download_button("⬇️ Download full validation report", csv_bytes(checked), "validation_report.csv", "text/csv", use_container_width=True)
    col2.download_button("⬇️ Download clean records", csv_bytes(clean_df), "clean_records.csv", "text/csv", "text/csv", use_container_width=True)
    col3.download_button("⬇️ Download issues report", csv_bytes(issue_df), "data_quality_issues.csv", "text/csv", "text/csv", use_container_width=True)
    st.download_button("⬇️ Download summary metrics", csv_bytes(summary_df), "validation_summary.csv", "text/csv")

    with st.expander("Expected columns and behavior"):
        st.markdown("""
        The validator recognizes these common fields: `record_id`, `name`, `email`, `amount`, `date`, and `status`.
        Some common aliases are normalized automatically (for example `customer_id` → `record_id`).
        Checks only run when the relevant column is present. The app reports issues; it does not silently delete or alter invalid rows.
        """)
else:
    st.info("Upload a CSV or Excel file to begin, or download the sample dataset to try the app.")
    sample = pd.DataFrame([
        {"record_id": "TXN-1001", "name": "Aarav Sharma", "email": "aarav@example.com", "amount": 1250.50, "date": "2026-09-01", "status": "Completed"},
        {"record_id": "TXN-1002", "name": "Meera Verma", "email": "meera@example.com", "amount": 799, "date": "2026-09-02", "status": "Pending"},
        {"record_id": "TXN-1003", "name": "Kabir Singh", "email": "not-an-email", "amount": -25, "date": "2026-09-03", "status": "Review"},
        {"record_id": "TXN-1003", "name": "Riya Das", "email": "riya@example.com", "amount": "unknown", "date": "31/31/2026", "status": "Pending"},
        {"record_id": "TXN-1005", "name": "", "email": "dev@example.com", "amount": 410, "date": "2026-09-05", "status": "Completed"},
    ])
    st.dataframe(sample, use_container_width=True)
    st.download_button("Download sample CSV", sample.to_csv(index=False).encode("utf-8"), "sample_business_data.csv", "text/csv")
