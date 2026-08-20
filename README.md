CropCheck Report Generator — photo-matched GUI.
This version uses a three-column layout matching the supplied reference image more closely while retaining all PDF extraction and reporting features.


Boll count update:
- Adds a separate `Bolls / m` column.
- Extracts explicit boll-per-metre counts from uploaded CropCheck reports.
- Converts counts over a stated distance to bolls per metre where supported.
- Does not treat fruiting-position counts as boll counts.
- Leaves the field blank when the report does not contain a supported boll count.


Automatic column hiding:
- Location, Paddock, Variety and Area always remain visible.
- Retention, NAWF, NACB, Bolls / m, Insect observations and Other observations hide when completely blank.
- A hidden column automatically appears when uploaded report data contains a value.
- The generated PDF also omits empty optional columns.


Aphid and WF percentage update:
- Insect Observations now captures Aphid percentages when explicitly stated in the uploaded CropCheck PDF.
- It also captures WF / Whitefly percentages when explicitly stated.
- Existing insect counts and per-metre calculations remain unchanged.
- The app does not invent percentages when the source report only provides counts.


PDF error fix:
- Fixed NameError: `pdf_cols` is now defined inside create_pdf() before adaptive column widths are calculated.
- Automatic empty-column hiding remains enabled in the app and generated PDF.
- Aphid % and WF % extraction remains enabled.
