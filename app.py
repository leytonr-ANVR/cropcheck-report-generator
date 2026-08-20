import base64
import io
import re
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

st.set_page_config(page_title="CropCheck Report Generator", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")
APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "agnvet_rural_logo.png"

COLUMNS = ["Location","Paddock","Variety","Area (ha)","First Position Retention","NAWF","Insect observations","Other observations"]
SAMPLE_ROWS = [
    ["Woodbine", "WB P1", "Siokra 253B3XF", 18.22, "86–89%", "7.0", "1 MN / 20 m beat sheet; Per metre: MN: 0.05/m", "Good growth; clean for weeds"],
    ["Donview", "P34 #02", "CSX1320B3XF", 1.50, "89–91%", "5.9–6.7", "5 MN / 20 m beat sheet; Per metre: MN: 0.25/m", "P34 combined inspection; Roundup spray noted as ordinary"],
    ["Donview", "P34 #03", "Sicot 606B3F", 3.22, "89–91%*", "5.9–6.7*", "5 MN*; Per metre: MN: 0.25/m", "P34 combined inspection"],
    ["Donview", "P34 #04", "Sicot 619B3XF", 1.63, "89–91%*", "5.9–6.7*", "5 MN*; Per metre: MN: 0.25/m", "P34 combined inspection"],
    ["Donview", "P34 #05", "Sicot 606B3F", 13.37, "89–91%*", "5.9–6.7*", "5 MN*; Per metre: MN: 0.25/m", "P34 combined inspection"],
    ["Donview", "VP2", "Sicot 606B3F", 11.97, "85–86%", "6.2–6.8", "2 MN / 20 m beat sheet; Per metre: MN: 0.1/m", "Some small boll loss; good plant height in areas"],
    ["Kearneys", "CP1", "Sicot 606B3F", 20.38, "86–88%", "5.4–5.5", "1 MA / 20 m beat sheet; Per metre: MA: 0.05/m", "Eastern side getting leggy; bellvine present"],
    ["Kearneys", "KP1", "Sicot 606B3F", 28.10, "79–81%", "5.5–6.0", "1 CS + 1 GVBN / 20 m beat sheet; Per metre: CS: 0.05/m; GVBN: 0.05/m", "Early bottom fruit loss in places; newer positions compensating"],
]
DEFAULT_ASSESSMENT = ("Cotton crops were generally progressing well. First-position retention ranged from 79–91%. KP1 recorded the lowest retention range and had early bottom fruit loss in places. Continued monitoring of fruit retention, crop maturity, weed control and insect activity is recommended.")
DEFAULT_RECOMMENDATIONS = ("1. Continue monitoring paddocks with lower first-position retention.\n2. Monitor boll loss and changes in NAWF at subsequent CropChecks.\n3. Follow up weed control where weeds remain present.\n4. Continue monitoring insect levels and crop maturity.")

st.markdown("""
<style>
:root {--navy:#06385f;--green:#00805f;--orange:#ef7d00;--light-blue:#edf6fc;--light-green:#eef9f1;}
.stApp {background:#f7fbfe;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#f2f8fd 0%,#ffffff 100%);border-right:1px solid #dceaf5;}
.hero {background:linear-gradient(100deg,#06385f 0%,#084b78 100%);border-radius:16px;padding:20px 26px;color:white;margin-bottom:14px;box-shadow:0 8px 22px rgba(6,56,95,.12);}
.hero h1 {margin:0;font-size:2rem}.hero p {margin:.3rem 0 0;opacity:.9}
div[data-testid="stMetric"] {background:white;border:1px solid #d7e7f3;border-radius:14px;padding:12px 14px;}
.stButton > button,.stDownloadButton > button {border-radius:10px;font-weight:700;}
</style>
""", unsafe_allow_html=True)

def logo_base64():
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii") if LOGO_PATH.exists() else ""

def extract_range(text):
    nums = re.findall(r"\d+(?:\.\d+)?", str(text))
    if not nums: return None
    vals = [float(n) for n in nums[:2]]
    return (vals[0], vals[0]) if len(vals)==1 else (min(vals), max(vals))

def retention_bounds(df):
    lows, highs = [], []
    for v in df.get("First Position Retention", []):
        rng = extract_range(v)
        if rng: lows.append(rng[0]); highs.append(rng[1])
    return (min(lows), max(highs)) if lows and highs else (None, None)

def lowest_retention_rows(df):
    scored=[]
    for _, row in df.iterrows():
        rng=extract_range(row.get("First Position Retention",""))
        if rng: scored.append((rng[0],row))
    if not scored: return []
    low=min(x[0] for x in scored)
    return [r for s,r in scored if s==low]

def clean_comments(text):
    return re.sub(r"\s+"," ",text or "").strip()

def _format_per_metre(value):
    """Format per-metre values neatly without unnecessary trailing zeros."""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    if value >= 1:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.3f}".rstrip("0").rstrip(".")

def _calculate_beat_sheet_per_metre(count_text, metres):
    """
    Convert counts such as:
      '5MN mostly 1st instar' -> 'MN: 0.25/m'
      '1CS and 1GVBN'        -> 'CS: 0.05/m; GVBN: 0.05/m'
      '2 MN'                 -> 'MN: 0.1/m'
    Only clearly countable count + pest-code pairs are calculated.
    """
    if not metres or metres <= 0:
        return []

    # Pest names/codes can be compact (5MN) or spaced (5 MN).
    # Avoid interpreting instar numbers or percentages as pest counts.
    pairs = re.findall(
        r"(?<![\d.])(\d+(?:\.\d+)?)\s*"
        r"(MN|MA|CS|GVBN|mirids?|aphids?|aph|WF|white\s*flies|whiteflies|whitefly)"
        r"\b",
        count_text,
        flags=re.I,
    )

    results = []
    for raw_count, raw_pest in pairs:
        count = float(raw_count)
        pest = re.sub(r"\s+", "", raw_pest.upper())
        pest_map = {
            "MIRID": "MN",
            "MIRIDS": "MN",
            "APHID": "Aphids",
            "APHIDS": "Aphids",
            "APH": "Aphids",
            "WHITEFLIES": "WF",
            "WHITEFLY": "WF",
        }
        pest = pest_map.get(pest, pest)
        per_m = count / float(metres)
        results.append(f"{pest}: {_format_per_metre(per_m)}/m")

    # Deduplicate in source order.
    return list(dict.fromkeys(results))

def parse_insects(comments):
    """Extract insect counts and automatically calculate beat-sheet insects per metre."""
    observations = []

    # General beat-sheet count. Works with 20 m, 10m etc.
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*m\s+beat\s+sheet\s+found\s+(.+?)"
        r"(?:\.|1st\s+pos|1st\s+position|$)",
        comments,
        flags=re.I,
    )
    if m:
        metres = float(m.group(1))
        value = clean_comments(m.group(2))
        if value:
            metre_label = _format_per_metre(metres)
            observations.append(f"{value} / {metre_label} m beat sheet")

            per_metre = _calculate_beat_sheet_per_metre(value, metres)
            if per_metre:
                observations.append("Per metre: " + "; ".join(per_metre))

    # Aphids: supports "3 aphids", "Aphids 3", "Aphid count 3", "3 Aph".
    aphid_patterns = [
        r"\b(\d+(?:\.\d+)?)\s*(?:aphids?|aph)\b",
        r"\baphids?\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
        r"\baph\s*[:=-]?\s*(\d+(?:\.\d+)?)\b",
    ]
    for pat in aphid_patterns:
        m = re.search(pat, comments, flags=re.I)
        if m:
            observations.append(f"Aphids: {m.group(1)}")
            break

    # Whitefly / WF counts.
    wf_patterns = [
        r"\b(\d+(?:\.\d+)?)\s*(?:WF|white\s*flies|whiteflies|whitefly)\b",
        r"\bWF\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
        r"\bwhite\s*fly\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
        r"\bwhitefly\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
    ]
    for pat in wf_patterns:
        m = re.search(pat, comments, flags=re.I)
        if m:
            observations.append(f"WF: {m.group(1)}")
            break

    # Fallback when no structured insect observations were found.
    if not observations:
        m = re.search(r"found\s+([^\.]{1,45})", comments, flags=re.I)
        if m:
            observations.append(clean_comments(m.group(1)))

    return "; ".join(dict.fromkeys(o for o in observations if o))

def parse_retention(comments):
    m=re.search(r"(?:1st|first)\s+(?:pos|position)(?:ition)?\s+retention\s+(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*%",comments,re.I)
    return f"{m.group(1)}–{m.group(2)}%" if m else ""

def parse_nawf(comments):
    m=re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*NAWF",comments,re.I)
    if m: return f"{m.group(1)}–{m.group(2)}"
    m=re.search(r"(\d+(?:\.\d+)?)\s*NAWF",comments,re.I)
    return m.group(1) if m else ""

def extract_other_observations(comments):
    c=clean_comments(comments)
    c=re.sub(r"^\d+\s*[-–]\s*\d+\s*n\.\s*","",c,flags=re.I)
    patterns=[
        r"20\s*m\s+beat\s+sheet\s+found\s+.+?(?:\.|$)",
        r"(?:1st|first)\s+(?:pos|position)(?:ition)?\s+retention\s+\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*%\.?",
        r"\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*NAWF[^\.]*\.?",
        r"\d+(?:\.\d+)?\s*NAWF[^\.]*\.?",
        r"\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?\s*NACB[^\.]*\.?",
        r"\d+(?:\.\d+)?\s*NACB[^\.]*\.?",
        r"NACB\s*\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?[^\.]*\.?",
    ]
    for pat in patterns: c=re.sub(pat,"",c,flags=re.I)
    return re.sub(r"\s+"," ",c).strip(" .")

def parse_cropcheck_pdf(file_bytes, filename):
    reader=PdfReader(io.BytesIO(file_bytes))
    rows=[]; meta={"grower":"","date":"","observation":"","filename":filename}
    for page in reader.pages:
        text=page.extract_text() or ""
        if not text.strip(): continue
        gm=re.search(r"Grower:\s*\n([^\n]+)",text,re.I)
        if gm and not meta["grower"]: meta["grower"]=gm.group(1).strip()
        om=re.search(r"Observation:\s*([^\n]+)",text,re.I)
        if om and not meta["observation"]: meta["observation"]=om.group(1).strip()
        dm=re.search(r"Assigned:\s*([^\n]+)",text,re.I)
        if dm and not meta["date"]: meta["date"]=dm.group(1).strip()
        if "Cotton -" not in text: continue
        before,_,after=text.partition("COMMENTS")
        comments=after.split("Signature",1)[0].strip() if after else ""
        lines=[ln.strip() for ln in before.splitlines() if ln.strip()]
        location=""; entries=[]
        for ln in lines:
            if ln.startswith("FIELD Crop & Variety"): continue
            m=re.match(r"(.+?)\s+Cotton\s*-\s*(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$",ln,re.I)
            if m:
                entries.append((location,m.group(1).strip(),m.group(2).strip(),float(m.group(3))))
            elif not re.search(r"\d+(?:\.\d+)?\s+\d+(?:\.\d+)?$",ln) and "Cotton" not in ln:
                location=ln
        retention=parse_retention(comments); nawf=parse_nawf(comments); insects=parse_insects(comments); other=extract_other_observations(comments)
        shared=len(entries)>1
        for location,paddock,variety,area in entries:
            rows.append({"Location":location,"Paddock":paddock,"Variety":variety,"Area (ha)":area,
                         "First Position Retention":retention+("*" if shared and retention else ""),
                         "NAWF":nawf+("*" if shared and nawf else ""),
                         "Insect observations":insects+("*" if shared and insects else ""),
                         "Other observations":(other+(" Shared paddock inspection figures." if shared else "")).strip()})
    return rows,meta

def merge_uploaded_reports(files):
    rows=[]; metas=[]
    for f in files:
        r,m=parse_cropcheck_pdf(f.getvalue(),f.name); rows.extend(r); metas.append(m)
    if not rows: return pd.DataFrame(columns=COLUMNS),metas
    df=pd.DataFrame(rows).drop_duplicates(subset=["Location","Paddock","Variety","Area (ha)","First Position Retention","NAWF"],keep="last")
    return df[COLUMNS].reset_index(drop=True),metas

def auto_assessment(df):
    if df.empty: return DEFAULT_ASSESSMENT
    total=pd.to_numeric(df["Area (ha)"],errors="coerce").fillna(0).sum(); lo,hi=retention_bounds(df)
    parts=[f"The uploaded CropCheck data contains {len(df)} cotton paddock entries covering {total:.2f} ha."]
    if lo is not None: parts.append(f"Reported first-position retention ranges from {lo:g}% to {hi:g}%.")
    lows=lowest_retention_rows(df)
    if lows: parts.append("The lowest reported retention is in "+", ".join(str(r["Paddock"]) for r in lows[:3])+".")
    notes=" ".join(df["Other observations"].astype(str)).lower(); issues=[]
    for key,label in [("boll","boll/fruit loss"),("bottom fruit","early fruit loss"),("bellvine","bellvine"),("nutgrass","nutgrass"),("leggy","leggy growth"),("roundup","weed-control performance")]:
        if key in notes and label not in issues: issues.append(label)
    if issues: parts.append("Key areas to continue monitoring include "+", ".join(issues[:5])+".")
    return " ".join(parts)

def auto_recommendations(df):
    rec=[]; lows=lowest_retention_rows(df)
    if lows: rec.append("Continue monitoring "+", ".join(str(r["Paddock"]) for r in lows[:3])+" for fruit retention and crop maturity.")
    text=" ".join(df["Other observations"].astype(str)).lower() if not df.empty else ""
    if any(k in text for k in ["bellvine","nutgrass","weed","roundup"]): rec.append("Follow up weed control where weed pressure or reduced spray performance was noted.")
    if any(k in text for k in ["boll","fruit loss","bottom fruit"]): rec.append("Monitor boll and fruit retention at the next CropCheck.")
    rec += ["Continue regular insect monitoring and record any change in pest pressure.","Track NAWF and crop maturity at subsequent inspections."]
    return "\n".join(f"{i+1}. {x}" for i,x in enumerate(rec))

def create_pdf(df,grower,advisor,observation,inspection_date,assessment,recommendations):
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=landscape(A4),rightMargin=10*mm,leftMargin=10*mm,topMargin=9*mm,bottomMargin=9*mm)
    styles=getSampleStyleSheet()
    title=ParagraphStyle("TitleCustom",parent=styles["Title"],fontSize=18,leading=21,textColor=colors.HexColor("#06385f"),alignment=TA_CENTER)
    h2=ParagraphStyle("H2Custom",parent=styles["Heading2"],fontSize=11,leading=14,textColor=colors.HexColor("#06385f"),spaceBefore=4,spaceAfter=4)
    small=ParagraphStyle("Small",parent=styles["Normal"],fontSize=7,leading=8.5); body=ParagraphStyle("Body",parent=styles["Normal"],fontSize=9,leading=12)
    story=[]
    if LOGO_PATH.exists():
        img=Image(str(LOGO_PATH),width=55*mm,height=23.7*mm); lt=Table([[img]],colWidths=[landscape(A4)[0]-20*mm]); lt.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER")]))
        story += [lt,Spacer(1,1.5*mm)]
    story += [Paragraph("Consolidated Cotton CropCheck Report",title),Spacer(1,3*mm)]
    details=[[Paragraph("<b>Grower</b>",small),Paragraph(grower or "-",small),Paragraph("<b>Advisor</b>",small),Paragraph(advisor or "-",small)],
             [Paragraph("<b>Observation</b>",small),Paragraph(observation or "-",small),Paragraph("<b>Inspection Date</b>",small),Paragraph(inspection_date or "-",small)]]
    dt=Table(details,colWidths=[25*mm,80*mm,30*mm,90*mm]); dt.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#eef6fb")),("BACKGROUND",(2,0),(2,-1),colors.HexColor("#eef6fb")),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#ccdbe6")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story += [dt,Spacer(1,4*mm)]
    data=[[Paragraph(f"<b>{h}</b>",small) for h in COLUMNS]]
    for _,r in df.iterrows(): data.append([Paragraph(str(r[h]),small) for h in COLUMNS])
    t=Table(data,colWidths=[22*mm,20*mm,31*mm,16*mm,28*mm,16*mm,38*mm,73*mm],repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#06385f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#a9bbc8")),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f6fafc")]),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    total=pd.to_numeric(df["Area (ha)"],errors="coerce").fillna(0).sum()
    story += [t,Spacer(1,3*mm),Paragraph(f"<b>Total cotton area:</b> {total:.2f} ha",h2),Paragraph("Overall Assessment",h2),Paragraph((assessment or "-").replace("\n","<br/>"),body),Paragraph("Recommendations",h2),Paragraph((recommendations or "-").replace("\n","<br/>"),body)]
    if any("*" in str(v) for v in df["First Position Retention"].tolist()+df["NAWF"].tolist()): story += [Spacer(1,2*mm),Paragraph("* Asterisked measurements were reported as combined figures for multiple paddocks/varieties on the same CropCheck inspection page.",small)]
    doc.build(story); return buf.getvalue()

def preview_pdf(pdf_bytes):
    b64=base64.b64encode(pdf_bytes).decode("ascii")
    components.html(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="560" style="border:1px solid #d7e7f3;border-radius:12px;"></iframe>',height=575,scrolling=False)

if "crop_data" not in st.session_state: st.session_state.crop_data=pd.DataFrame(SAMPLE_ROWS,columns=COLUMNS)
if "assessment" not in st.session_state: st.session_state.assessment=DEFAULT_ASSESSMENT
if "recommendations" not in st.session_state: st.session_state.recommendations=DEFAULT_RECOMMENDATIONS
if "uploaded_names" not in st.session_state: st.session_state.uploaded_names=[]

logo64=logo_base64(); logo_html=f'<img src="data:image/png;base64,{logo64}" style="height:76px;background:white;padding:4px 8px;border-radius:8px;">' if logo64 else ""
st.markdown(f'<div class="hero"><div style="display:flex;align-items:center;justify-content:space-between;gap:18px;"><div><h1>🌱 CropCheck Report Generator</h1><p>Upload • Analyse • Edit • Generate professional reports</p></div><div>{logo_html}</div></div></div>',unsafe_allow_html=True)

with st.sidebar:
    if LOGO_PATH.exists(): st.image(str(LOGO_PATH),use_container_width=True)
    st.header("Upload PDF Reports")
    st.caption("Upload one or more Agworld CropCheck PDFs. Cotton paddock data will be extracted automatically, including beat-sheet insect counts converted to insects per metre.")
    uploads=st.file_uploader("Choose CropCheck PDF files",type=["pdf"],accept_multiple_files=True)
    if uploads:
        names=[u.name for u in uploads]
        if names != st.session_state.uploaded_names:
            with st.spinner("Reading CropCheck PDFs…"): parsed,metas=merge_uploaded_reports(uploads)
            if parsed.empty: st.error("I couldn't find cotton paddock rows in the uploaded PDF(s). You can still enter data manually.")
            else:
                st.session_state.crop_data=parsed; st.session_state.uploaded_names=names; st.session_state.assessment=auto_assessment(parsed); st.session_state.recommendations=auto_recommendations(parsed)
                first=next((m for m in metas if m.get("grower") or m.get("date")),{})
                if first.get("grower"): st.session_state.grower_value=first["grower"]
                if first.get("date"): st.session_state.date_value=first["date"]
                if first.get("observation"): st.session_state.obs_value=first["observation"]
                st.success(f"Loaded {len(parsed)} cotton paddock entries.")
    if st.button("Load example cotton data",use_container_width=True):
        st.session_state.crop_data=pd.DataFrame(SAMPLE_ROWS,columns=COLUMNS); st.session_state.assessment=DEFAULT_ASSESSMENT; st.session_state.recommendations=DEFAULT_RECOMMENDATIONS; st.session_state.uploaded_names=[]; st.rerun()
    st.divider(); st.markdown("**Uploaded reports**")
    if st.session_state.uploaded_names:
        for n in st.session_state.uploaded_names: st.write("📄",n)
    else: st.caption("No PDFs uploaded yet.")

top_left,top_right=st.columns([2.25,1],gap="large")
with top_right:
    st.markdown("### ⚙️ Report Details")
    grower=st.text_input("Grower",value=st.session_state.get("grower_value","Luck Farming P/L"))
    advisor=st.text_input("Advisor",value="AGnVET Rural – Biloela")
    observation=st.text_input("Observation",value=st.session_state.get("obs_value","20–22n"))
    inspection_date=st.text_input("Inspection Date",value=st.session_state.get("date_value","6 February 2026"))
with top_left:
    df=st.session_state.crop_data; total=pd.to_numeric(df["Area (ha)"],errors="coerce").fillna(0).sum(); lo,hi=retention_bounds(df)
    st.markdown("### 📊 Report Summary")
    a,b,c,d=st.columns(4); a.metric("Total Cotton Area",f"{total:.2f} ha"); b.metric("Paddocks",len(df)); c.metric("Highest Retention",f"{hi:g}%" if hi is not None else "—"); d.metric("Lowest Retention",f"{lo:g}%" if lo is not None else "—")

st.markdown("### 🧰 Cotton Paddocks")
edited=st.data_editor(st.session_state.crop_data,num_rows="dynamic",use_container_width=True,hide_index=True,column_config={"Area (ha)":st.column_config.NumberColumn("Area (ha)",min_value=0.0,step=0.01,format="%.2f"),"First Position Retention":st.column_config.TextColumn("Retention (%)"),"Insect observations":st.column_config.TextColumn("Insects",width="medium"),"Other observations":st.column_config.TextColumn("Other observations",width="large")})
st.session_state.crop_data=edited

left,right=st.columns([1.45,1],gap="large")
with left:
    st.markdown("### 🌿 Crop Assessment"); assessment=st.text_area("Overall assessment",value=st.session_state.assessment,height=180,label_visibility="collapsed"); st.session_state.assessment=assessment
with right:
    st.markdown("### 💡 Recommendations"); recommendations=st.text_area("Recommendations",value=st.session_state.recommendations,height=180,label_visibility="collapsed"); st.session_state.recommendations=recommendations

st.markdown("### 📄 Generate Report")
st.caption("The generated report includes the AGnVET Rural logo, editable paddock data, NAWF, NACB, insect observations, Aphids, WF, insects per metre, total hectares, assessment and recommendations.")
if not edited.empty:
    pdf=create_pdf(edited,grower,advisor,observation,inspection_date,assessment,recommendations)
    b1,b2=st.columns(2)
    with b1: st.download_button("⬇️ Download PDF Report",data=pdf,file_name="CropCheck_Consolidated_Cotton_Report.pdf",mime="application/pdf",use_container_width=True,type="primary")
    with b2: show=st.toggle("Show report preview",value=False)
    if show: preview_pdf(pdf)
else: st.info("Upload a CropCheck PDF or add paddock rows to generate a report.")

st.caption("PDF extraction is designed for the Agworld CropCheck layout used in the supplied reports. Always review the extracted table before issuing the final report.")
