# Skill areas we want to ensure coverage
SKILL_AREAS = [
    "Formulas",
    "Pivot Tables",
    "Data Cleaning",
    "Productivity/Protection"
]

# Control interview length
MIN_QUESTIONS = 4
MAX_QUESTIONS = 4 

# (Optional) fallback static pool if API call fails
FALLBACK_QUESTIONS = [
    {
        "id": 1,
        "question": "What are absolute and relative cell references in Excel? Give an example where you would use each.",
        "level": "basic",
        "skill_area": "Formulas",
        "ideal": "Relative references (A1)... absolute ($A$1)..."
    },
    {
        "id": 2,
        "question": "How do you create a pivot table to summarize sales data by region?",
        "level": "advanced",
        "skill_area": "Pivot Tables",
        "ideal": "Insert > PivotTable, put Region into rows..."
    }
]
