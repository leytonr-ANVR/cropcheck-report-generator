# CropCheck Report Generator — All-in-One

This version combines all requested features into one Streamlit web app.

## Included features
- Upload one or multiple Agworld CropCheck PDF reports
- Automatically extract cotton paddock data
- Location
- Paddock
- Variety
- Area (ha)
- First-position retention
- NAWF
- NACB
- General insect observations
- Aphid counts
- WF / Whitefly counts
- Automatic beat-sheet insect-per-metre calculation
- Editable extracted data
- Add or delete paddock rows
- Automatic total cotton hectares
- Automatic highest and lowest retention summary
- Automatic crop assessment
- Automatic recommendations
- Preloaded Luck Farming cotton example data
- AGnVET Rural logo in the web app
- AGnVET Rural logo in generated PDF reports
- PDF report preview
- PDF report download
- Mobile/browser friendly Streamlit layout

## Insect calculation example
If a CropCheck report states:
`20 m beat sheet found 5 MN`

the app displays:
`5 MN / 20 m beat sheet; Per metre: MN: 0.25/m`

If multiple insect types are stated, each recognised count is converted separately.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload all files from this folder.
3. Open Streamlit Community Cloud.
4. Select the repository and `app.py`.
5. Deploy.

## Important
The PDF parser is tailored to the Agworld CropCheck format used in the supplied reports.
Always review extracted figures before issuing the final report.
