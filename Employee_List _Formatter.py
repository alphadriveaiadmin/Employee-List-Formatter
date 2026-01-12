# app.py
# Streamlit app: paste raw JSON -> renders "department_employees" as an Employee Phone Number Directory

import json
import re
from collections import OrderedDict
import streamlit as st


# ---------- helpers ----------
def digits_only(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def format_us_phone(raw: str) -> str:
    d = digits_only(raw)
    if len(d) == 10:
        return f"({d[0:3]}) {d[3:6]}-{d[6:10]}"
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
        return f"({d[0:3]}) {d[3:6]}-{d[6:10]}"
    return raw or ""


def normalize_name(name: str) -> str:
    return (name or "").strip()


def normalize_position(pos: str) -> str:
    return (pos or "").strip()


def normalize_email(email: str) -> str:
    e = (email or "").strip()
    return e if e else ""


def to_directory_entries(payload: dict) -> list[dict]:
    """
    Flattens payload['department_employees'] into a list of employees, deduping/merging if needed.
    Returns list of dicts: {name, position, office, email}
    """
    dept_emps = payload.get("department_employees", []) or []

    # Preserve input order (department_employees is already ordered)
    entries: list[dict] = []
    for block in dept_emps:
        employees = (block or {}).get("employees", []) or []
        for e in employees:
            name = normalize_name(e.get("contact_name", ""))
            position = normalize_position(e.get("employee_position", ""))
            office = (e.get("office_number", "") or "").strip()
            email = normalize_email(e.get("email_address", ""))

            if not name:
                continue

            entries.append(
                {
                    "name": name,
                    "position": position,
                    "office_raw": office,
                    "office_fmt": format_us_phone(office),
                    "email": email,
                }
            )

    # Optional: dedupe exact duplicates while preserving first occurrence
    seen = set()
    deduped = []
    for x in entries:
        key = (x["name"], x["position"], x["office_raw"], x["email"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(x)

    return deduped


def render_directory_markdown(entries: list[dict]) -> str:
    """
    Renders entries in the exact requested format.
    """
    lines = []
    lines.append("## Employee Phone Number Directory\n")
    for e in entries:
        lines.append(f"    {e['name']}")
        lines.append(f"{e['position']}" if e["position"] else "")
        if e["office_fmt"]:
            lines.append(f"Office: {e['office_fmt']}")
        if e["email"]:
            lines.append(f"Email: {e['email']}")
        lines.append("")  # blank line between employees

    # Remove accidental extra blank lines caused by missing position
    out = "\n".join([ln for ln in lines if ln is not None])
    # Clean up doubled blank lines a bit (keeps the separation you want)
    out = re.sub(r"\n{3,}", "\n\n", out).rstrip() + "\n"
    return out


# ---------- streamlit UI ----------
st.set_page_config(page_title="Employee Directory Builder", layout="wide")
st.title("Employee Directory Builder")
st.caption('Paste the raw JSON payload, then this app extracts `department_employees` and formats a directory.')

default_json = ""  # leave blank; you can paste your payload
raw = st.text_area("Raw JSON", value=default_json, height=280, placeholder="Paste the full JSON here...")

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    pretty = st.checkbox("Pretty-print JSON on parse", value=False)
with col2:
    show_table = st.checkbox("Show parsed table", value=True)

if st.button("Generate Directory", type="primary"):
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")
        st.stop()

    if pretty:
        st.subheader("Parsed JSON (pretty)")
        st.code(json.dumps(payload, indent=2), language="json")

    entries = to_directory_entries(payload)
    if not entries:
        st.warning("No employees found under `department_employees`.")
        st.stop()

    directory_md = render_directory_markdown(entries)

    st.subheader("Directory Output")
    # Use code block so spacing is preserved exactly
    st.code(directory_md, language="markdown")

    st.download_button(
        "Download directory.md",
        data=directory_md.encode("utf-8"),
        file_name="directory.md",
        mime="text/markdown",
    )

    if show_table:
        st.subheader("Parsed Employees")
        st.dataframe(
            [
                {
                    "Name": e["name"],
                    "Position": e["position"],
                    "Office": e["office_fmt"],
                    "Email": e["email"],
                }
                for e in entries
            ],
            use_container_width=True,
            hide_index=True,
        )

st.markdown(
    """
**Run locally**
```bash
pip install streamlit
streamlit run app.py
