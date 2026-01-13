# Employee_List_Formatter.py
# Streamlit app: paste raw JSON -> renders "department_employees" as an Employee Phone Number Directory

import json
import re
import streamlit as st


def digits_only(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def format_us_phone(raw: str) -> str:
    d = digits_only(raw)
    if len(d) == 10:
        return f"({d[0:3]}) {d[3:6]}-{d[6:10]}"
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
        return f"({d[0:3]}) {d[3:6]}-{d[6:10]}"
    return (raw or "").strip()


def normalize(s: str) -> str:
    return (s or "").strip()


def to_entries(payload: dict) -> list[dict]:
    dept_emps = payload.get("department_employees", []) or []
    entries = []

    for block in dept_emps:
        employees = (block or {}).get("employees", []) or []
        for emp in employees:
            name = normalize(emp.get("contact_name", ""))
            if not name:
                continue

            position = normalize(emp.get("employee_position", ""))
            office_raw = normalize(emp.get("office_number", ""))
            email = normalize(emp.get("email_address", ""))

            entries.append(
                {
                    "name": name,
                    "position": position,
                    "office_raw": office_raw,
                    "office_fmt": format_us_phone(office_raw),
                    "email": email,
                }
            )

    # Deduplicate exact duplicates while preserving order
    seen = set()
    deduped = []
    for e in entries:
        key = (e["name"], e["position"], e["office_raw"], e["email"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    return deduped


def render_directory(entries: list[dict]) -> str:
    lines = []
    lines.append("## Employee Phone Number Directory")
    lines.append("")

    for e in entries:
        lines.append("    " + e["name"])
        if e["position"]:
            lines.append(e["position"])
        if e["office_fmt"]:
            lines.append("Office: " + e["office_fmt"])
        if e["email"]:
            lines.append("Email: " + e["email"])
        lines.append("")  # blank line between employees

    # collapse any accidental 3+ blank lines
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out).rstrip() + "\n"
    return out


st.set_page_config(page_title="Employee Directory Builder", layout="wide")
st.title("Employee Directory Builder")
st.caption("Paste the raw JSON payload, then the app extracts `department_employees` and formats a directory.")

raw = st.text_area("Raw JSON", value="", height=280, placeholder="Paste the full JSON here...")

col1, col2 = st.columns(2)
with col1:
    pretty = st.checkbox("Pretty-print JSON on parse", value=False)
with col2:
    show_table = st.checkbox("Show parsed table", value=True)

if st.button("Generate Directory", type="primary"):
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        st.error("Invalid JSON: " + str(e))
        st.stop()

    if pretty:
        st.subheader("Parsed JSON (pretty)")
        st.code(json.dumps(payload, indent=2), language="json")

    entries = to_entries(payload)
    if not entries:
        st.warning("No employees found under `department_employees`.")
        st.stop()

    directory_md = render_directory(entries)

    st.subheader("Directory Output")
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

st.markdown("Run locally:\n\n- pip install streamlit\n- streamlit run Employee_List_Formatter.py")

