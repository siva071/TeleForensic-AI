def build_graph(df, scores):
    """Build network graph from call data"""
    try:
        from pyvis.network import Network

        print("==== DEBUG START ====")
        print("Columns:", df.columns)
        print("Total Rows:", len(df))
        print(df.head())

        # -------------------------------
        # STEP 1: FORCE COLUMN DETECTION
        # -------------------------------
        caller_col = None
        receiver_col = None

        for col in df.columns:
            col_clean = col.lower().strip()

            if 'a' in col_clean and 'party' in col_clean:
                caller_col = col
            elif 'b' in col_clean and 'party' in col_clean:
                receiver_col = col

        # Fallback (VERY IMPORTANT)
        if not caller_col or not receiver_col:
            caller_col = df.columns[0]
            receiver_col = df.columns[1]

        print("Caller Column:", caller_col)
        print("Receiver Column:", receiver_col)

        # -------------------------------
        # STEP 2: CLEAN NUMBER FUNCTION
        # -------------------------------
        def clean_number(num):
            num = str(num)
            digits = ''.join(filter(str.isdigit, num))

            if len(digits) >= 5:   # relaxed condition
                return digits[-10:] if len(digits) >= 10 else digits

            return None

        # -------------------------------
        # STEP 3: BUILD FREQUENCY MAP
        # -------------------------------
        call_frequencies = {}

        for _, row in df.iterrows():
            caller = clean_number(row[caller_col])
            receiver = clean_number(row[receiver_col])

            if caller and receiver:
                pair = (caller, receiver)
                call_frequencies[pair] = call_frequencies.get(pair, 0) + 1

        print("Total Connections:", len(call_frequencies))

        if not call_frequencies:
            print("❌ No valid call data found")
            return None

        # -------------------------------
        # STEP 4: CREATE NETWORK
        # -------------------------------
        net = Network(
            height='600px',
            width='100%',
            bgcolor='#1a1a2e',
            font_color='white',
            directed=True
        )

        # -------------------------------
        # STEP 5: SCORE LOOKUP
        # -------------------------------
        score_lookup = {}
        if scores:
            for s in scores:
                score_lookup[s.get('number')] = s

        # -------------------------------
        # STEP 6: ADD NODES
        # -------------------------------
        all_numbers = set()
        for c, r in call_frequencies.keys():
            all_numbers.add(c)
            all_numbers.add(r)

        for number in all_numbers:
            freq = sum(
                v for (c, r), v in call_frequencies.items()
                if c == number or r == number
            )

            score_data = score_lookup.get(number, {})

            color = score_data.get('color', '#00ffcc')

            size = min(10 + freq * 2, 50)

            net.add_node(
                number,
                label=number,
                size=size,
                color=color,
                title=f"Number: {number}\nCalls: {freq}"
            )

        # -------------------------------
        # STEP 7: ADD EDGES
        # -------------------------------
        for (c, r), freq in call_frequencies.items():
            net.add_edge(
                c,
                r,
                value=freq,
                title=f"Calls: {freq}"
            )

        # -------------------------------
        # STEP 8: SETTINGS
        # -------------------------------
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true
          },
          "interaction": {
            "hover": true
          }
        }
        """)

        # -------------------------------
        # STEP 9: SAVE GRAPH
        # -------------------------------
        net.save_graph("network.html")

        print("✅ Graph generated successfully")

        return "network.html"

    except Exception as e:
        print("❌ ERROR:", e)
        return None
