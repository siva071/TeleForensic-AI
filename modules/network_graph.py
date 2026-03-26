def build_graph(df, scores):
    try:
        from pyvis.network import Network

        # -------------------------------
        # STEP 1: COLUMN DETECTION
        # -------------------------------
        caller_col = df.columns[0]
        receiver_col = df.columns[1]

        # -------------------------------
        # STEP 2: CLEAN FUNCTION
        # -------------------------------
        def normalize(num):
            digits = ''.join(filter(str.isdigit, str(num)))
            return digits[-10:] if len(digits) >= 10 else digits

        # -------------------------------
        # STEP 3: BUILD CONNECTIONS
        # -------------------------------
        call_frequencies = {}

        for _, row in df.iterrows():
            c = normalize(row[caller_col])
            r = normalize(row[receiver_col])

            if c and r:
                pair = (c, r)
                call_frequencies[pair] = call_frequencies.get(pair, 0) + 1

        if not call_frequencies:
            return None

        # -------------------------------
        # STEP 4: CREATE NETWORK
        # -------------------------------
        net = Network(height='600px', width='100%', directed=True)

        # -------------------------------
        # STEP 5: SCORE LOOKUP
        # -------------------------------
        score_lookup = {}

        if isinstance(scores, list):
            for s in scores:
                if 'number' in s:
                    clean = normalize(s['number'])
                    score_lookup[clean] = s

        # -------------------------------
        # STEP 6: COLLECT ALL NUMBERS
        # -------------------------------
        all_numbers = set()

        for c, r in call_frequencies.keys():
            all_numbers.add(c)
            all_numbers.add(r)

        # -------------------------------
        # STEP 7: ADD NODES
        # -------------------------------
        for number in all_numbers:

            freq = sum(
                v for (c, r), v in call_frequencies.items()
                if c == number or r == number
            )

            score_data = score_lookup.get(number, {})

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
                label=number,
                size=size,
                color=color,
                title=f"Number: {number}\nRisk: {label_text}\nCalls: {freq}"
            )

        # -------------------------------
        # STEP 8: ADD EDGES
        # -------------------------------
        for (c, r), freq in call_frequencies.items():
            net.add_edge(c, r, value=freq)

        # -------------------------------
        # STEP 9: SAVE
        # -------------------------------
        net.save_graph("network.html")

        return "network.html"

    except Exception as e:
        print("Error:", e)
        return None
