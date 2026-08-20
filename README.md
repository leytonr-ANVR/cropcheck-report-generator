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
