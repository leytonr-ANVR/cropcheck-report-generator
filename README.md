# CropCheck Report Generator

A Streamlit web app for converting Agworld CropCheck PDF reports into an editable consolidated cotton report.

## Features
- Upload one or multiple CropCheck PDFs
- Automatically extract cotton paddock rows
- Extract area, retention, NAWF, NACB, insect observations, automatically calculated insects per metre, Aphid counts, WF counts and comments
- Edit extracted data before generating the report
- Automatic total hectares and retention summary
- Editable crop assessment and recommendations
- AGnVET Rural logo included in the generated PDF
- PDF preview and download
- Preloaded Luck Farming cotton example data

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload all files in this folder.
3. In Streamlit Community Cloud choose the repository.
4. Set the app file to `app.py`.
5. Deploy.

PDF extraction is designed for the Agworld CropCheck structure used by the supplied example reports. Review extracted figures before issuing a final report.

- Beat-sheet counts are automatically converted to insects per metre when the checked distance is stated (for example, 5 MN over 20 m = 0.25 MN/m).
