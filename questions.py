# questions.py
SKILL_AREAS = [
    "Formulas",
    "Pivot Tables",
    "Data Cleaning",
    "Productivity/Protection",
    "Reporting"
]

MIN_QUESTIONS = 3
MAX_QUESTIONS = 5

# fallback pool for cold start / API failure
FALLBACK_QUESTIONS = [
    {"id": 1, "question": "What are absolute and relative cell references in Excel? Give an example.", "level": "basic", "skill_area": "Formulas", "ideal": "Relative references (A1) change when copied; absolute ($A$1) stays fixed."},
    {"id": 2, "question": "Write an Excel formula to calculate the average of values in column A, ignoring blanks.", "level": "basic", "skill_area": "Formulas", "ideal": "Use =AVERAGEIF(A:A, \"<>\") or =AVERAGE(IF(A:A<>\"\",A:A)) as array."},
    {"id": 3, "question": "How would you clean a dataset in Excel that has duplicate rows and missing values?", "level": "intermediate", "skill_area": "Data Cleaning", "ideal": "Use Remove Duplicates, Filter blanks, Fill/IFERROR, or Power Query to transform and dedupe."},
    {"id": 4, "question": "How do you create a pivot table to summarize sales data by region?", "level": "advanced", "skill_area": "Pivot Tables", "ideal": "Insert > PivotTable; put Region into Rows and Sales into Values (choose Average if needed)."},
    {"id": 5, "question": "How can you prevent accidental changes to formulas in a worksheet while allowing edits to some cells?", "level": "basic", "skill_area": "Productivity/Protection", "ideal": "Unlock editable cells, then Protect Sheet to enforce locked cells (and optionally add a password)."}
]
