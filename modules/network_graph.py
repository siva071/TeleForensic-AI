# -------------------------------
# ADD NODES WITH REAL RISK COLORS
# -------------------------------
for number in all_numbers:

    freq = sum(
        v for (c, r), v in call_frequencies.items()
        if c == number or r == number
    )

    score_data = score_lookup.get(number, {})

    # Default values
    label_text = "Unknown"
    color = "#888888"

    if score_data:
        label = score_data.get("label", "").lower()

        if label == "high":
            color = "red"
            label_text = "HIGH RISK"
        elif label == "medium":
            color = "orange"
            label_text = "MEDIUM"
        elif label == "low":
            color = "green"
            label_text = "LOW"

    size = min(10 + freq * 3, 60)

    net.add_node(
        number,
        label=f"{number}",
        size=size,
        color=color,
        title=f"""
Number: {number}
Risk: {label_text}
Total Calls: {freq}
"""
    )
