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

st.markdown(
    """
    <style>
    :root{
        --navy:#082f5f;
        --navy2:#0d4478;
        --green:#0b8a49;
        --light-green:#eef9f1;
        --light-blue:#edf6fc;
        --border:#d7e6f2;
        --text:#0b2942;
        --muted:#607387;
        --danger:#e5383b;
    }

    html, body, [class*="css"] {
        font-family: "Segoe UI", Arial, sans-serif;
    }

    .stApp {
        background:#f6fbff;
        color:var(--text);
    }

    /* top app spacing */
    .block-container {
        max-width: 1550px;
        padding-top: 1.1rem;
        padding-bottom: 1rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background:#f8fbfe;
        border-right:1px solid var(--border);
    }
    [data-testid="stSidebar"] > div:first-child{
        padding-top:1rem;
    }

    /* Hero */
    .hero {
        background:linear-gradient(100deg,#072d59 0%,#06386f 70%,#0a4779 100%);
        border-radius:0;
        padding:18px 24px;
        color:#fff;
        margin:-1.1rem -1rem 1rem -1rem;
        box-shadow:0 4px 14px rgba(6,47,95,.18);
    }
    .hero-inner{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:20px;
    }
    .hero-title{
        font-size:2rem;
        font-weight:800;
        line-height:1.05;
        margin:0;
    }
    .hero-sub{
        margin:.35rem 0 0;
        font-size:1rem;
        opacity:.95;
    }
    .hero-logo{
        height:74px;
        background:#fff;
        padding:6px 10px;
        border-radius:8px;
        box-shadow:0 2px 8px rgba(0,0,0,.12);
    }

    /* Generic cards */
    .dash-card{
        background:#fff;
        border:1px solid var(--border);
        border-radius:12px;
        padding:14px 16px;
        box-shadow:0 2px 10px rgba(8,47,95,.045);
        margin-bottom:12px;
    }
    .dash-card h3{
        margin:0 0 10px;
        font-size:1.05rem;
        color:var(--navy);
        font-weight:800;
    }
    .green-card{
        background:var(--light-green);
        border:1px solid #cfe9d6;
        border-radius:12px;
        padding:14px 16px;
    }
    .blue-card{
        background:var(--light-blue);
        border:1px solid #cddff0;
        border-radius:12px;
        padding:14px 16px;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background:#f4fff6;
        border:1px solid #cfe9d6;
        border-radius:10px;
        padding:12px 10px;
        text-align:center;
    }
    div[data-testid="stMetric"] label{
        color:#22384e !important;
        font-size:.86rem !important;
    }
    div[data-testid="stMetricValue"]{
        font-size:1.55rem !important;
        font-weight:800 !important;
        color:#111 !important;
    }

    /* Headings */
    h1,h2,h3{
        color:var(--navy);
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stDateInput input{
        border-radius:7px !important;
        border:1px solid #cbd9e5 !important;
        background:#fff !important;
    }

    /* Buttons */
    .stButton button, .stDownloadButton button {
        border-radius:7px !important;
        font-weight:700 !important;
        min-height:2.5rem;
    }
    .stDownloadButton button{
        background:var(--navy) !important;
        color:white !important;
        border:0 !important;
    }
    .stButton button[kind="primary"]{
        background:#0d8f45 !important;
        border-color:#0d8f45 !important;
    }

    /* Data editor */
    [data-testid="stDataFrame"]{
        border:1px solid var(--border);
        border-radius:10px;
        overflow:hidden;
        background:#fff;
    }

    /* uploader */
    [data-testid="stFileUploader"]{
        background:white;
        border:1px dashed #7aa9d3;
        border-radius:10px;
        padding:10px;
    }

    /* sidebar fake nav */
    .nav-item{
        display:flex;
        align-items:center;
        gap:10px;
        padding:10px 12px;
        border-radius:8px;
        color:#0b2f59;
        margin:4px 0;
        font-weight:600;
        background:transparent;
    }
    .nav-item.active{
        color:#fff;
        background:linear-gradient(90deg,#06366d,#0a4b84);
    }
    .side-section-title{
        font-size:.85rem;
        font-weight:800;
        color:#173b61;
        margin:12px 0 5px;
    }
    .uploaded-file{
        background:#fff;
        border-bottom:1px solid #edf2f6;
        padding:7px 4px;
        font-size:.83rem;
    }
    .success-box{
        background:#effcf2;
        border:1px solid #bde9c5;
        color:#14632d;
        border-radius:9px;
        padding:10px 12px;
        margin-top:10px;
        font-size:.84rem;
        font-weight:600;
    }

    /* feature strip */
    .feature-strip{
        display:none;
    }

    /* hide Streamlit chrome */
    #MainMenu{visibility:hidden;}
    footer{visibility:hidden;}
    header[data-testid="stHeader"]{background:transparent;}
    </style>
    """,
    unsafe_allow_html=True,
)
APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "assets" / "agnvet_rural_logo.png"

COLUMNS = ["Location","Paddock","Variety","Area (ha)","First Position Retention","NAWF","NACB","Bolls / m","Insect observations","Other observations"]
SAMPLE_ROWS = [
    ["Woodbine", "WB P1", "Siokra 253B3XF", 18.22, "86–89%", "7.0", "", "", "1 MN / 20 m beat sheet; Per metre: MN: 0.05/m", "Good growth; clean for weeds"],
    ["Donview", "P34 #02", "CSX1320B3XF", 1.50, "89–91%", "5.9–6.7", "", "", "5 MN / 20 m beat sheet; Per metre: MN: 0.25/m", "P34 combined inspection; Roundup spray noted as ordinary"],
    ["Donview", "P34 #03", "Sicot 606B3F", 3.22, "89–91%*", "5.9–6.7*", "", "", "5 MN*; Per metre: MN: 0.25/m", "P34 combined inspection"],
    ["Donview", "P34 #04", "Sicot 619B3XF", 1.63, "89–91%*", "5.9–6.7*", "", "", "5 MN*; Per metre: MN: 0.25/m", "P34 combined inspection"],
    ["Donview", "P34 #05", "Sicot 606B3F", 13.37, "89–91%*", "5.9–6.7*", "", "", "5 MN*; Per metre: MN: 0.25/m", "P34 combined inspection"],
    ["Donview", "VP2", "Sicot 606B3F", 11.97, "85–86%", "6.2–6.8", "", "", "2 MN / 20 m beat sheet; Per metre: MN: 0.1/m", "Some small boll loss; good plant height in areas"],
    ["Kearneys", "CP1", "Sicot 606B3F", 20.38, "86–88%", "5.4–5.5", "", "", "1 MA / 20 m beat sheet; Per metre: MA: 0.05/m", "Eastern side getting leggy; bellvine present"],
    ["Kearneys", "KP1", "Sicot 606B3F", 28.10, "79–81%", "5.5–6.0", "", "", "1 CS + 1 GVBN / 20 m beat sheet; Per metre: CS: 0.05/m; GVBN: 0.05/m", "Early bottom fruit loss in places; newer positions compensating"],
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
    """Return the bundled AGnVET Rural logo as base64 for reliable web display."""
    try:
        path = LOGO_PATH.resolve()
        if not path.exists():
            return ""
        return base64.b64encode(path.read_bytes()).decode("ascii")
    except Exception:
        return ""

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
    """
    Extract insect observations including:
    - beat-sheet counts and insects per metre
    - Aphid counts
    - WF / Whitefly counts
    - Aphid percentages
    - WF / Whitefly percentages

    Percentages are only added when they are explicitly present in the source text.
    """
    observations = []

    # Beat-sheet counts
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
            observations.append(f"{value} / {_format_per_metre(metres)} m beat sheet")
            per_metre = _calculate_beat_sheet_per_metre(value, metres)
            if per_metre:
                observations.append("Per metre: " + "; ".join(per_metre))

    # Aphid count
    aphid_count_patterns = [
        r"\b(\d+(?:\.\d+)?)\s*(?:aphids?|aph)\b",
        r"\baphids?\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
        r"\baph\s*[:=-]?\s*(\d+(?:\.\d+)?)\b",
    ]
    for pat in aphid_count_patterns:
        m = re.search(pat, comments, flags=re.I)
        if m:
            observations.append(f"Aphids: {m.group(1)}")
            break

    # Whitefly / WF count
    wf_count_patterns = [
        r"\b(\d+(?:\.\d+)?)\s*(?:WF|white\s*flies|whiteflies|whitefly)\b",
        r"\bWF\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
        r"\bwhite\s*fly\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
        r"\bwhitefly\s*(?:count\s*)?[:=-]?\s*(\d+(?:\.\d+)?)\b",
    ]
    for pat in wf_count_patterns:
        m = re.search(pat, comments, flags=re.I)
        if m:
            observations.append(f"WF: {m.group(1)}")
            break

    # Aphid percentage
    aphid_pct_patterns = [
        r"\baphids?\s*(?:incidence|infestation|plants?|leaves?|count)?\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*%",
        r"\b(\d+(?:\.\d+)?)\s*%\s*(?:aphids?|aphid\s+incidence|aphid\s+infestation)\b",
        r"\baph\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*%",
    ]
    for pat in aphid_pct_patterns:
        m = re.search(pat, comments, flags=re.I)
        if m:
            observations.append(f"Aphids: {m.group(1)}%")
            break

    # Whitefly / WF percentage
    wf_pct_patterns = [
        r"\b(?:WF|white\s*fly|whitefly|whiteflies)\s*(?:incidence|infestation|plants?|leaves?|count)?\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*%",
        r"\b(\d+(?:\.\d+)?)\s*%\s*(?:WF|white\s*fly|whitefly|whiteflies)\b",
    ]
    for pat in wf_pct_patterns:
        m = re.search(pat, comments, flags=re.I)
        if m:
            observations.append(f"WF: {m.group(1)}%")
            break

    # Fallback
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

def parse_nacb(comments):
    m=re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*NACB",comments,re.I)
    if m: return f"{m.group(1)}–{m.group(2)}"
    m=re.search(r"(\d+(?:\.\d+)?)\s*NACB",comments,re.I)
    if m: return m.group(1)
    m=re.search(r"NACB\s*(\d+(?:\.\d+)?)(?:\s*[-–]\s*(\d+(?:\.\d+)?))?",comments,re.I)
    if m: return f"{m.group(1)}–{m.group(2)}" if m.group(2) else m.group(1)
    return ""

def parse_bolls_per_metre(comments):
    """
    Extract boll counts per metre only when the report explicitly supports the value.

    Supported examples:
      "12 bolls/m"
      "12 bolls per metre"
      "12 bolls per meter"
      "1m counted 12 bolls"
      "12 bolls in 1m"
      "2m counted 24 bolls" -> 12 bolls/m
      "24 bolls in 2 m"     -> 12 bolls/m

    Counts of fruiting positions are not treated as boll counts.
    """
    if not comments:
        return ""

    # Already expressed per metre.
    patterns_direct = [
        r"\b(\d+(?:\.\d+)?)\s*bolls?\s*/\s*m\b",
        r"\b(\d+(?:\.\d+)?)\s*bolls?\s+per\s+met(?:re|er)\b",
    ]
    for pat in patterns_direct:
        m = re.search(pat, comments, re.I)
        if m:
            value = float(m.group(1))
            return f"{value:g}"

    # Distance first: "2m counted 24 bolls"
    m = re.search(
        r"\b(\d+(?:\.\d+)?)\s*m\b[^\.]{0,60}?\b(?:counted|found|had)\s+"
        r"(\d+(?:\.\d+)?)\s+bolls?\b",
        comments,
        re.I,
    )
    if m:
        metres = float(m.group(1))
        count = float(m.group(2))
        if metres > 0:
            return f"{count/metres:.2f}".rstrip("0").rstrip(".")

    # Count first: "24 bolls in 2 m"
    m = re.search(
        r"\b(\d+(?:\.\d+)?)\s+bolls?\b[^\.]{0,40}?\b(?:in|over|across)\s+"
        r"(\d+(?:\.\d+)?)\s*m\b",
        comments,
        re.I,
    )
    if m:
        count = float(m.group(1))
        metres = float(m.group(2))
        if metres > 0:
            return f"{count/metres:.2f}".rstrip("0").rstrip(".")

    return ""

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
        r"\d+(?:\.\d+)?\s*bolls?\s*/\s*m\b\.?",
        r"\d+(?:\.\d+)?\s*bolls?\s+per\s+met(?:re|er)\b\.?",
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
        retention=parse_retention(comments); nawf=parse_nawf(comments); nacb=parse_nacb(comments); bolls_per_m=parse_bolls_per_metre(comments); insects=parse_insects(comments); other=extract_other_observations(comments)
        shared=len(entries)>1
        for location,paddock,variety,area in entries:
            rows.append({"Location":location,"Paddock":paddock,"Variety":variety,"Area (ha)":area,
                         "First Position Retention":retention+("*" if shared and retention else ""),
                         "NAWF":nawf+("*" if shared and nawf else ""),
                         "NACB":nacb+("*" if shared and nacb else ""),
                         "Bolls / m":bolls_per_m+("*" if shared and bolls_per_m else ""),
                         "Insect observations":insects+("*" if shared and insects else ""),
                         "Other observations":(other+(" Shared paddock inspection figures." if shared else "")).strip()})
    return rows,meta

def merge_uploaded_reports(files):
    rows=[]; metas=[]; comments=[]
    for f in files:
        r,m=parse_cropcheck_pdf(f.getvalue(),f.name)
        rows.extend(r)
        metas.append(m)
    if not rows:
        return pd.DataFrame(columns=COLUMNS), metas, comments
    df=pd.DataFrame(rows)
    # Ensure every expected column exists even if a field was absent in the PDF.
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df=df.drop_duplicates(
        subset=["Location","Paddock","Variety","Area (ha)","First Position Retention","NAWF","NACB","Bolls / m"],
        keep="last"
    )
    return df[COLUMNS].reset_index(drop=True), metas, comments

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
    # Only include columns that contain meaningful data.
    pdf_cols = visible_crop_columns(df)
    if not pdf_cols:
        pdf_cols = [c for c in COLUMNS if c in df.columns]

    pdf_df = df.reindex(columns=pdf_cols, fill_value="").copy()

    # Wrap every table cell in a Paragraph so long notes stay inside their column.
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=6.4,
        leading=7.4,
        textColor=colors.white,
        alignment=0,
        wordWrap="CJK",
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=6.2,
        leading=7.3,
        textColor=colors.black,
        alignment=0,
        wordWrap="CJK",
    )

    def _pdf_safe(value):
        if pd.isna(value):
            return ""
        value = str(value)
        # Escape basic XML characters used by ReportLab Paragraph.
        value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Encourage wrapping of slash/semicolon-heavy agronomy observations.
        value = value.replace("; ", ";<br/>")
        return value

    data = [[Paragraph(_pdf_safe(col), table_header_style) for col in pdf_cols]]
    for _, row in pdf_df.iterrows():
        data.append([Paragraph(_pdf_safe(row[col]), table_cell_style) for col in pdf_cols])

    # Calculate widths dynamically so hidden/visible columns always fit.
    available_width = landscape(A4)[0] - 20*mm
    weight_map = {
        "Location": 0.95,
        "Paddock": 0.95,
        "Variety": 1.35,
        "Area (ha)": 0.75,
        "First Position Retention": 1.15,
        "NAWF": 0.70,
        "NACB": 0.70,
        "Bolls / m": 0.75,
        "Insect observations": 2.35,
        "Other observations": 3.10,
    }
    weights = [weight_map.get(col, 1.0) for col in pdf_cols]
    total_weight = sum(weights) or 1.0
    col_widths = [available_width * weight / total_weight for weight in weights]

    t = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#06385f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#a9bbc8")),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f6fafc")]),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    total=pd.to_numeric(df["Area (ha)"],errors="coerce").fillna(0).sum()
    story += [t,Spacer(1,3*mm),Paragraph(f"<b>Total cotton area:</b> {total:.2f} ha",h2),Paragraph("Overall Assessment",h2),Paragraph((assessment or "-").replace("\n","<br/>"),body),Paragraph("Recommendations",h2),Paragraph((recommendations or "-").replace("\n","<br/>"),body)]
    if any("*" in str(v) for v in df["First Position Retention"].tolist()+df["NAWF"].tolist()): story += [Spacer(1,2*mm),Paragraph("* Asterisked measurements were reported as combined figures for multiple paddocks/varieties on the same CropCheck inspection page.",small)]
    doc.build(story); return buf.getvalue()

def preview_pdf(pdf_bytes):
    b64=base64.b64encode(pdf_bytes).decode("ascii")
    components.html(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="560" style="border:1px solid #d7e7f3;border-radius:12px;"></iframe>',height=575,scrolling=False)


def column_has_data(series):
    cleaned = series.astype(str).str.strip().str.lower()
    return (~cleaned.isin(["", "nan", "none", "n/a", "na", "-", "—"])).any()

def visible_crop_columns(df):
    core = ["Location", "Paddock", "Variety", "Area (ha)"]
    optional = ["First Position Retention", "NAWF", "NACB", "Bolls / m",
                "Insect observations", "Other observations"]
    return ([c for c in core if c in df.columns] +
            [c for c in optional if c in df.columns and column_has_data(df[c])])

if "crop_data" not in st.session_state: st.session_state.crop_data=pd.DataFrame(SAMPLE_ROWS,columns=COLUMNS)
if "assessment" not in st.session_state: st.session_state.assessment=DEFAULT_ASSESSMENT
if "recommendations" not in st.session_state: st.session_state.recommendations=DEFAULT_RECOMMENDATIONS
if "uploaded_names" not in st.session_state: st.session_state.uploaded_names=[]

# Upgrade older session data to the current schema without crashing.
if "crop_data" in st.session_state:
    for _col in COLUMNS:
        if _col not in st.session_state.crop_data.columns:
            st.session_state.crop_data[_col] = ""
    st.session_state.crop_data = st.session_state.crop_data.reindex(columns=COLUMNS, fill_value="")


logo64 = logo_base64()
if not logo64:
    st.warning("AGnVET Rural logo file could not be loaded. Check that assets/agnvet_rural_logo.png is included with the app.")
logo_html = f'<img class="top-logo" src="data:image/png;base64,{logo64}">' if logo64 else ""

st.markdown("<style>\
:root{--navy:#062f61;--navy2:#0b4a84;--green:#0b8d47;--border:#d7e4ef;--greenbg:#effaf1;--bluebg:#eef6fd;}\
.stApp{background:#fff}.block-container{max-width:1600px;padding:0 14px 18px}header[data-testid='stHeader']{display:none}#MainMenu,footer{visibility:hidden}\
.topbar{margin:0 -14px 16px;background:linear-gradient(100deg,#062e60,#073e79);min-height:100px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.12)}\
.top-title{font-size:2rem;font-weight:800}.top-sub{font-size:1rem;margin-top:6px}.top-logo{height:76px;background:#fff;padding:6px 10px;border-radius:6px}\
.panel,.table-shell,.report-card{border:1px solid var(--border);background:#fff;border-radius:12px;padding:14px;box-shadow:0 1px 6px rgba(7,48,92,.04);margin-bottom:12px}\
.panel-title,.card-head,.section-title{color:var(--navy);font-size:1.08rem;font-weight:800;margin-bottom:10px}.upload-hero{text-align:center}.upload-icon{font-size:2.4rem}.smalltext{font-size:.82rem;color:#52697e;line-height:1.35}\
.navbox{border:1px solid var(--border);border-radius:12px;overflow:hidden;background:#fff;margin-top:12px}.navitem{padding:11px 14px;font-weight:650;color:#12365e;display:flex;gap:10px;border-bottom:1px solid #edf2f6}.navitem.active{background:linear-gradient(90deg,#06336b,#0b4b85);color:#fff}\
.successbox{background:#effaf1;border:1px solid #bfe8c8;color:#16632f;border-radius:9px;padding:10px 12px;font-size:.82rem;margin-top:10px}.green-card{background:var(--greenbg);border:1px solid #cce8d2;border-radius:11px;padding:12px 14px;margin-bottom:12px}.blue-card{background:var(--bluebg);border:1px solid #cbdff2;border-radius:11px;padding:12px 14px;margin-bottom:12px}\
.metric-wrap{border:1px solid #cce8d2;background:#f3fff5;border-radius:11px;padding:8px}.stTextInput input,.stTextArea textarea{border:1px solid #ccd9e5!important;border-radius:6px!important;background:#fff!important}[data-testid='stFileUploader']{border:1px dashed #80a9d0;border-radius:10px;padding:8px;background:#fff}[data-testid='stDataFrame']{border:1px solid var(--border);border-radius:9px;overflow:hidden}\
div[data-testid='stMetric']{background:transparent;border:none;padding:7px 8px;text-align:center}div[data-testid='stMetricValue']{font-size:1.45rem!important;font-weight:800!important;color:#111!important}div[data-testid='stMetricLabel']{justify-content:center;font-size:.8rem!important}.stDownloadButton>button{background:#06366e!important;color:#fff!important;border:0!important;border-radius:7px!important;font-weight:750!important}.stButton>button{border-radius:7px!important;font-weight:750!important}.preview-shell{border:1px solid var(--border);border-radius:10px;background:#fff;padding:8px}\
</style>", unsafe_allow_html=True)

st.markdown(f"<div class='topbar'><div><div class='top-title'>☁ CropCheck Report Generator</div><div class='top-sub'>Upload • Analyse • Generate Professional Reports</div></div><div>{logo_html}</div></div>", unsafe_allow_html=True)

left_col, center_col, right_col = st.columns([1.0, 3.1, 1.2], gap="medium")

with left_col:
    st.markdown("<div class='panel upload-hero'><div class='upload-icon'>☁️</div><div class='panel-title'>Upload PDF Report</div><div class='smalltext'>Upload your CropCheck PDF reports to extract and manage the data.</div></div>", unsafe_allow_html=True)
    uploads = st.file_uploader("Drag and drop PDF files here or click to browse", type=["pdf"], accept_multiple_files=True)
    if uploads:
        upload_names = [u.name for u in uploads]
        if upload_names != st.session_state.uploaded_names:
            with st.spinner("Reading CropCheck PDFs…"):
                parsed_df, metas, comments = merge_uploaded_reports(uploads)
            if parsed_df.empty:
                st.error("No cotton paddock rows were found in the uploaded PDF(s).")
            else:
                st.session_state.crop_data = parsed_df
                st.session_state.uploaded_names = upload_names
                st.session_state.assessment = auto_assessment(parsed_df)
                st.session_state.recommendations = auto_recommendations(parsed_df)
                first_meta = next((m for m in metas if m.get("grower") or m.get("date")), {})
                if first_meta.get("grower"): st.session_state["grower_field"] = first_meta["grower"]
                if first_meta.get("date"): st.session_state["date_field"] = first_meta["date"]
                if first_meta.get("observation"): st.session_state["obs_field"] = first_meta["observation"]
                st.rerun()
    st.markdown("<div class='panel-title' style='font-size:.9rem;margin-top:8px'>Uploaded Reports</div>", unsafe_allow_html=True)
    if st.session_state.uploaded_names:
        for name in st.session_state.uploaded_names:
            st.markdown(f"<div class='smalltext' style='padding:6px 2px;border-bottom:1px solid #edf2f6'>📄 {name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='successbox'>✓ Reports uploaded successfully!<br>{len(st.session_state.uploaded_names)} report(s) processed.</div>", unsafe_allow_html=True)
    else:
        st.caption("No reports uploaded yet.")
    st.markdown("<div class='navbox'><div class='navitem active'>⌂ Dashboard</div><div class='navitem'>▣ Paddock Data</div><div class='navitem'>◒ Crop Assessment</div><div class='navitem'>💡 Recommendations</div><div class='navitem'>📄 Generate Report</div></div>", unsafe_allow_html=True)
    if st.button("Load example cotton data", use_container_width=True):
        st.session_state.crop_data = pd.DataFrame(SAMPLE_ROWS, columns=COLUMNS)
        st.session_state.assessment = DEFAULT_ASSESSMENT
        st.session_state.recommendations = DEFAULT_RECOMMENDATIONS
        st.session_state.uploaded_names = []
        st.rerun()

with center_col:
    df = st.session_state.crop_data
    total_area = pd.to_numeric(df["Area (ha)"], errors="coerce").fillna(0).sum()
    low_ret, high_ret = retention_bounds(df)
    st.markdown("<div class='panel'><div class='panel-title'>▥ Report Summary</div><div class='metric-wrap'>", unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    a.metric("Total Cotton Area", f"{total_area:.2f} ha")
    b.metric("Paddocks", len(df))
    c.metric("Highest Retention", f"{high_ret:g}%" if high_ret is not None else "—")
    d.metric("Lowest Retention", f"{low_ret:g}%" if low_ret is not None else "—")
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='table-shell'><div class='panel-title'>🧰 Cotton Paddocks</div>", unsafe_allow_html=True)
    _visible_cols = visible_crop_columns(st.session_state.crop_data)
    _display_df = st.session_state.crop_data[_visible_cols].copy()
    edited = st.data_editor(
        _display_df, num_rows="dynamic", use_container_width=True, hide_index=True, height=510,
        column_config={
            "Location": st.column_config.TextColumn("Location", width="small"),
            "Paddock": st.column_config.TextColumn("Paddock", width="small"),
            "Variety": st.column_config.TextColumn("Variety", width="medium"),
            "Area (ha)": st.column_config.NumberColumn("Area (ha)", min_value=0.0, step=0.01, format="%.2f", width="small"),
            "First Position Retention": st.column_config.TextColumn("Retention (%)", width="small"),
            "NAWF": st.column_config.TextColumn("NAWF", width="small"),
            "NACB": st.column_config.TextColumn("NACB", width="small"),
            "Bolls / m": st.column_config.TextColumn("Bolls / m", width="small"),
            "Insect observations": st.column_config.TextColumn("Insects / m / Aphids % / WF %", width="large"),
            "Other observations": st.column_config.TextColumn("Notes", width="medium"),
        },
        key="crop_editor_photo"
    )
    _full_df = st.session_state.crop_data.reindex(index=edited.index, columns=COLUMNS, fill_value="").copy()
    for _col in edited.columns:
        _full_df[_col] = edited[_col]
    st.session_state.crop_data = _full_df
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='report-card'><div class='card-head'>📄 Upload and Generate Report</div><div class='smalltext'>Once your PDF reports are uploaded, the app automatically extracts the data. You can edit or add notes, then generate a professional PDF report with the AGnVET Rural logo.</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Crop Assessment</div>", unsafe_allow_html=True)
    assessment = st.text_area("Overall assessment", value=st.session_state.assessment, height=125, label_visibility="collapsed")
    st.session_state.assessment = assessment
    st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
    recommendations = st.text_area("Recommendations", value=st.session_state.recommendations, height=125, label_visibility="collapsed")
    st.session_state.recommendations = recommendations

with right_col:
    st.markdown("<div class='report-card'><div class='card-head'>⚙ Report Details</div>", unsafe_allow_html=True)
    grower = st.text_input("Grower", value=st.session_state.get("grower_field","Luck Farming P/L"), key="grower_photo")
    advisor = st.text_input("Advisor", value="AGnVET Rural – Biloela", key="advisor_photo")
    observation = st.text_input("Observation", value=st.session_state.get("obs_field","20–22n"), key="obs_photo")
    inspection_date = st.text_input("Inspection Date", value=st.session_state.get("date_field","6 February 2026"), key="date_photo")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='green-card'><div class='card-head' style='color:#16652e'>🌿 Key Observations</div>", unsafe_allow_html=True)
    items = []
    for _, row in st.session_state.crop_data.iterrows():
        note = str(row.get("Other observations","")).strip()
        if note and note.lower() not in ("nan","none"):
            items.append(f"<li><b>{row.get('Paddock','')}</b> – {note}</li>")
        if len(items) >= 4: break
    if not items: items = ["<li>No key observations extracted yet.</li>"]
    st.markdown("<ul style='padding-left:18px;margin:0'>" + "".join(items) + "</ul></div>", unsafe_allow_html=True)

    st.markdown("<div class='blue-card'><div class='card-head'>💡 Recommendations</div>", unsafe_allow_html=True)
    rec_lines = [re.sub(r"^\d+\.\s*","",line).strip() for line in st.session_state.recommendations.splitlines() if line.strip()]
    st.markdown("<ul style='padding-left:18px;margin:0'>" + "".join(f"<li>{r}</li>" for r in rec_lines[:5]) + "</ul></div>", unsafe_allow_html=True)

    pdf_bytes = create_pdf(st.session_state.crop_data, grower, advisor, observation, inspection_date, st.session_state.assessment, st.session_state.recommendations)
    st.markdown("<div class='preview-shell'><div class='card-head'>Report Preview</div>", unsafe_allow_html=True)
    preview_pdf(pdf_bytes)
    st.markdown("</div>", unsafe_allow_html=True)
    st.download_button("⬇ Download PDF Report", data=pdf_bytes, file_name="CropCheck_Consolidated_Cotton_Report.pdf", mime="application/pdf", use_container_width=True)

st.caption("PDF extraction is designed for the Agworld CropCheck layout used in the supplied reports. Review extracted figures before issuing the final report.")
