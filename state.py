nurses = [
    {
        "name": f"Nurse{i}",
        "fte": "full",
        "group": "leadership" if i <= 3 else "bedside",
        "available_shifts": ["D", "E", "N", "LD", "LN"],
    }
    for i in range(1, 21)
]
rules = []
