CropCheck Report Generator — photo-matched GUI.
This version uses a three-column layout matching the supplied reference image more closely while retaining all PDF extraction and reporting features.


Boll count update:
- Adds a separate `Bolls / m` column.
- Extracts explicit boll-per-metre counts from uploaded CropCheck reports.
- Converts counts over a stated distance to bolls per metre where supported.
- Does not treat fruiting-position counts as boll counts.
- Leaves the field blank when the report does not contain a supported boll count.
