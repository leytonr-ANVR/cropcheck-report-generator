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


PDF wrapping fix:
- Long table text is now wrapped using ReportLab Paragraph objects.
- Insect observations and Notes columns receive more width.
- Cell padding and vertical alignment were improved.
- Semicolon-separated observations are broken across lines for readability.
- The table can split cleanly across pages without text spilling into adjacent columns.


Nodes update:
- Adds a separate Nodes column.
- Converts CropCheck notation such as `20-22n` to `20–22` under Nodes.
- Supports single node counts such as `20n`.
- Supports wording such as `Nodes 20-22` or `node count 20-22`.
- Nodes automatically hide when no node data is present.
- Nodes are included in the generated PDF only when data exists.


Aphid reporting update:
- Single Aphids and Cluster Aphids are now reported separately in Insect Observations.
- Supports counts and percentages for each when explicitly stated in the CropCheck report.
- Generic `Aphids` is only used when the source does not specify single vs cluster.
- WF / Whitefly counts and percentages remain supported.


Node parser error fix:
- Fixed NameError: parse_nodes is now always defined before PDF parsing.
- Added a defensive fallback so PDF uploads won't crash if node parsing is unavailable.
- Existing Nodes, Single Aphids, Cluster Aphids, WF, NACB, Bolls/m and PDF wrapping features remain enabled.


Dashboard averages update:
- Adds Average NAWF when NAWF data is present.
- Adds Average NACB when NACB data is present.
- Single values are averaged directly.
- For ranges such as 5.9–6.7, the midpoint is used before calculating the overall paddock average.
- Metrics are hidden automatically when no valid data is present.


Average retention update:
- Adds Average Retention to the dashboard when retention data is present.
- For retention ranges such as 86–89%, the midpoint is used for that paddock.
- The dashboard then averages those paddock midpoint values.
- The metric automatically hides when no retention data is available.


PDF dashboard measurements update:
- Adds dashboard measurements below the paddock table in the PDF.
- Includes Total Cotton Area, Paddocks, Highest Retention, Lowest Retention.
- Includes Average Retention, Average NAWF and Average NACB when data is present.


PDF To Do List Summary:
- Adds a separate page to the generated PDF.
- Extracts action items from each uploaded check when wording such as `Will suggest`, `Recommend`, `Recommended`, `Recommendation`, `Suggest` or `Suggested` is present.
- Shows the source check/report beside each action.
- Adds a checkbox column so the page can be used as a practical to-do list.
- Does not invent recommendations when none are present in the source check.


To Do PDF page fix:
- Fixed NameError caused by the undefined `h1` style.
- The To Do List Summary page now uses the existing PDF title style.
- All previous dashboard, PDF, recommendation, and CropCheck extraction features remain enabled.


To Do title style fix:
- Fixed the remaining NameError caused by `title_style` not existing in create_pdf().
- Added a dedicated `todo_title_style` inside create_pdf() before the To Do page is built.
- Verified that the style is defined before use.


To Do parser upload fix:
- Fixed UnboundLocalError caused by using `text` before page text had been extracted.
- Recommendations are now extracted after each PDF page is read.
- Duplicate recommendations are removed while preserving their original order.
- PDF upload and To Do Summary features remain enabled.


NAWF Cutout update:
- The app now recognises `cutout`, `Cutout`, or `cut out` as valid NAWF information.
- When cutout is stated without a numeric NAWF value, the NAWF column shows `Cutout`.
- Numeric NAWF values still take priority if both a number and cutout wording are present.
- Average NAWF ignores the text value `Cutout` because it is not a numeric measurement.


Bolls per metre range update:
- Recognises `B/m`, `b/m`, `boll/m`, `bolls/m`, and `bolls per metre`.
- If more than one boll-per-metre value is present in the same check, the app reports the lowest-to-highest range.
- Example: `10 B/m` and `14 B/m` becomes `10–14` in the Bolls / m column.
- Duplicate repeated values are collapsed to one value.


Squares per metre update:
- Adds a separate `Squares / m` column.
- Recognises `S/m`, `s/m`, `square/m`, `squares/m`, and `squares per metre`.
- If multiple square-per-metre values are present in one check, the app reports the lowest-to-highest range.
- Example: `8 S/m` and `12 S/m` becomes `8–12`.
- The column automatically hides when no square-per-metre data is present.
- The generated PDF includes the column only when data exists.

Boll metrics update:
- Dashboard now shows Low Bolls / m, Average Bolls / m and High Bolls / m when data is present.
- PDF Dashboard Measurements includes the same three boll metrics when present.
- For a range like 10–14, low=10, high=14, average contribution=12.


Relevant To Do actions fix:
- Recommendation extraction is now line-based instead of flattening the whole PDF.
- Only genuine actionable recommendations are added to the To Do page.
- Measurements, observations, descriptive crop notes and report fields are excluded.
- Empty Recommendation/Will Suggest headings no longer pull unrelated table data into the To Do list.
- Direct actions such as Monitor, Recheck, Apply, Spray, Irrigate, Review and Follow up are supported.
- Duplicate actions are removed.

Retention typo support:
- Retention data is now captured even when `retention` has common spelling/OCR errors.
- Supports variants such as Retension, Retantion, Retenion, Retentin and Retetion.
- A fuzzy fallback accepts minor spelling errors within two character edits of `retention`.
- `1st position` or `First position` followed directly by a percentage is also recognised.


To Do extraction fix:
- Recommendation phrases are now detected anywhere in a line, not only at the beginning.
- Handles `Will suggest`, `Will recommend`, `Recommend`, `Recommended`, `Suggested`, and `Suggestion`.
- Handles headings on one line with the action on the next line.
- Direct actions such as Spread, Monitor, Recheck, Apply, Spray, Irrigate and Follow up are also captured.
- Measurements and descriptive crop notes remain excluded.

To Do paddock source update:
- The To Do Summary now uses the paddock name instead of the uploaded PDF filename where a reliable match can be made.
- Actions are matched back to each paddock's Other observations text.
- Shared recommendations can show multiple paddock names.
- The uploaded filename is used only as a fallback if the paddock cannot be determined reliably.
- The PDF column heading is now `Paddock`.

Beat-sheet /m fix:
- Recognises `20m beatsheet`, `20m beat sheet`, and `20m beat-sheet`.
- Keeps the checked distance in Insect Observations.
- Converts compact counts such as `8MN`, `16mn`, `1MA`, and `1GVB` to per-metre values.
- Example: `20m beatsheet found 8MN` -> `8MN / 20 m beat sheet; MN: 0.4/m`.
