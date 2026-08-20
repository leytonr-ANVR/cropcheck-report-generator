
import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

st.set_page_config(page_title="CropCheck Report Generator", page_icon="🌱", layout="wide")

DEFAULT_DATA = [
    ["Woodbine", "WB P1", "Siokra 253B3XF", 18.22, "86–89%", "7.0", "1 MN / 20 m beat sheet", "Good growth; clean for weeds"],
    ["Donview", "P34 #02", "CSX1320B3XF", 1.50, "89–91%", "5.9–6.7", "5 MN / 20 m beat sheet", "P34 combined inspection; Roundup spray noted as ordinary"],
    ["Donview", "P34 #03", "Sicot 606B3F", 3.22, "89–91%*", "5.9–6.7*", "5 MN*", "P34 combined inspection"],
    ["Donview", "P34 #04", "Sicot 619B3XF", 1.63, "89–91%*", "5.9–6.7*", "5 MN*", "P34 combined inspection"],
    ["Donview", "P34 #05", "Sicot 606B3F", 13.37, "89–91%*", "5.9–6.7*", "5 MN*", "P34 combined inspection"],
    ["Donview", "VP2", "Sicot 606B3F", 11.97, "85–86%", "6.2–6.8", "2 MN / 20 m beat sheet", "Some small boll loss; good plant height in areas"],
    ["Kearneys", "CP1", "Sicot 606B3F", 20.38, "86–88%", "5.4–5.5", "1 MA / 20 m beat sheet", "Eastern side getting leggy; bellvine present"],
    ["Kearneys", "KP1", "Sicot 606B3F", 28.10, "79–81%", "5.5–6.0", "1 CS + 1 GVBN / 20 m beat sheet", "Early bottom fruit loss in places; newer positions compensating"],
]
COLUMNS = ["Location","Paddock","Variety","Area (ha)","First Position Retention","NAWF","Insect observations","Other observations"]

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(DEFAULT_DATA, columns=COLUMNS)

st.title("🌱 CropCheck Report Generator")
st.caption("Luck Farming — Cotton CropCheck example")

with st.sidebar:
    st.header("Report details")
    grower = st.text_input("Grower", "Luck Farming P/L")
    advisor = st.text_input("Advisor", "AGnVET Rural – Biloela")
    observation = st.text_input("Observation", "20–22n")
    date = st.text_input("Inspection date", "6 February 2026")
    st.divider()
    if st.button("Reset example data", use_container_width=True):
        st.session_state.data = pd.DataFrame(DEFAULT_DATA, columns=COLUMNS)
        st.rerun()

st.subheader("Paddock data")
edited = st.data_editor(
    st.session_state.data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Area (ha)": st.column_config.NumberColumn("Area (ha)", min_value=0, step=0.01, format="%.2f"),
    },
)
st.session_state.data = edited

area = pd.to_numeric(edited["Area (ha)"], errors="coerce").fillna(0)
total = float(area.sum())
retention_text = edited["First Position Retention"].astype(str).tolist()
nafw_text = edited["NAWF"].astype(str).tolist()

c1, c2, c3 = st.columns(3)
c1.metric("Total cotton", f"{total:.2f} ha")
c2.metric("Paddocks", len(edited))
c3.metric("Lowest reported retention", "79–81%")

st.subheader("Farm assessment")
assessment = st.text_area(
    "Overall assessment",
    "Cotton crops were generally progressing well. First-position retention ranged from 79–91%. "
    "KP1 recorded the lowest retention range and had early bottom fruit loss in places. "
    "The CropCheck observations support continued monitoring of fruit retention, crop maturity, "
    "weed control and insect activity.",
    height=120,
)

recommendations = st.text_area(
    "Follow-up recommendations",
    "1. Continue monitoring KP1 for fruit retention, maturity and compensation from newer fruiting positions.\n"
    "2. Monitor cotton paddocks for further boll loss and changes in NAWF.\n"
    "3. Follow up weed control where bellvine or other weeds were observed.\n"
    "4. Continue monitoring insect levels at subsequent CropCheck inspections.",
    height=120,
)

def make_pdf(df):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=8*mm, leftMargin=8*mm, topMargin=8*mm, bottomMargin=8*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=17, leading=20)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=6.8, leading=8)
    story = [
        Paragraph("Luck Farming P/L — Consolidated Cotton CropCheck Report", title),
        Spacer(1, 2*mm),
        Paragraph(f"<b>Grower:</b> {grower} &nbsp;&nbsp; <b>Advisor:</b> {advisor} &nbsp;&nbsp; "
                  f"<b>Observation:</b> {observation} &nbsp;&nbsp; <b>Date:</b> {date}", small),
        Spacer(1, 4*mm)
    ]
    table_data = [[Paragraph(f"<b>{c}</b>", small) for c in COLUMNS]]
    for _, row in df.iterrows():
        table_data.append([Paragraph(str(row[c]), small) for c in COLUMNS])
    widths = [22*mm, 20*mm, 29*mm, 16*mm, 28*mm, 16*mm, 35*mm, 76*mm]
    t = Table(table_data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.35,colors.grey),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),2),
        ("RIGHTPADDING",(0,0),(-1,-1),2),("TOPPADDING",(0,0),(-1,-1),2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2)
    ]))
    story += [
        t, Spacer(1, 4*mm),
        Paragraph(f"<b>Total cotton area:</b> {total:.2f} ha", styles["Heading2"]),
        Paragraph("<b>Overall assessment</b>", styles["Heading2"]),
        Paragraph(assessment.replace("\n","<br/>"), small),
        Spacer(1, 2*mm),
        Paragraph("<b>Follow-up recommendations</b>", styles["Heading2"]),
        Paragraph(recommendations.replace("\n","<br/>"), small),
        Spacer(1, 2*mm),
        Paragraph("Note: P34 retention, NAWF and insect figures are combined inspection figures and are not separately measured for each P34 variety.", small)
    ]
    doc.build(story)
    buf.seek(0)
    return buf

st.divider()
if st.button("Generate PDF report", type="primary", use_container_width=True):
    pdf = make_pdf(edited)
    st.download_button(
        "⬇️ Download PDF",
        pdf,
        "Luck_Farming_CropCheck_Cotton_Report.pdf",
        "application/pdf",
        use_container_width=True
    )

st.caption("Example data is based on the supplied CropCheck report. P34 measurements marked * are combined P34 inspection figures.")
