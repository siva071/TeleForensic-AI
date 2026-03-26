def build_graph(df, scores):
    """Build network graph from call data"""
    try:
        # Find caller and receiver columns
        caller_col = None
        receiver_col = None

        for col in df.columns:
            col_lower = col.lower().strip()

            if caller_col is None and any(keyword in col_lower for keyword in 
                ['caller', 'from', 'calling', 'dial', 'a party', 'a_number', 'source']):
                caller_col = col

            elif receiver_col is None and any(keyword in col_lower for keyword in 
                ['receiver', 'to', 'called', 'receive', 'b party', 'b_number', 'destination']):
                receiver_col = col

        print("Caller:", caller_col)
        print("Receiver:", receiver_col)

        if not caller_col or not receiver_col:
            print("Could not find caller and receiver columns")
            return None

        # Import libraries
        from pyvis.network import Network

        # Create network
        net = Network(
            height='600px',
            width='100%',
            bgcolor='#1a1a2e',
            font_color='white',
            directed=True
        )

        # Score lookup
        score_lookup = {}
        if scores:
            for score_data in scores:
                score_lookup[score_data['number']] = score_data

        # Clean number function
        def clean_number(num):
            num = str(num)
            digits = ''.join(filter(str.isdigit, num))
            if len(digits) >= 10:
                return digits[-10:]
            return None

        # Count frequencies
        call_frequencies = {}

        for _, row in df.iterrows():
            caller_clean = clean_number(row[caller_col])
            receiver_clean = clean_number(row[receiver_col])

            if caller_clean and receiver_clean:
                pair = (caller_clean, receiver_clean)
                call_frequencies[pair] = call_frequencies.get(pair, 0) + 1

        if not call_frequencies:
            print("No valid call data found")
            return None

        # Collect all numbers
        all_numbers = set()
        for caller, receiver in call_frequencies.keys():
            all_numbers.add(caller)
            all_numbers.add(receiver)

        # Add nodes
        for number in all_numbers:
            score_data = score_lookup.get(number, {
                'score': 0,
                'label': 'Unknown',
                'color': '#888888'
            })

            frequency = sum(
                freq for (c, r), freq in call_frequencies.items()
                if c == number or r == number
            )

            size = min(10 + frequency * 2, 50)
            color = score_data.get('color', '#888888')

            net.add_node(
                number,
                label=f"{number}\n({score_data.get('label', 'Unknown')})",
                color=color,
                size=size,
                title=f"Number: {number}\nScore: {score_data.get('score', 0)}\nCalls: {frequency}"
            )

        # Add edges
        for (caller, receiver), frequency in call_frequencies.items():
            width = min(1 + frequency / 5, 10)

            net.add_edge(
                caller,
                receiver,
                width=width,
                title=f"Calls: {frequency}",
                color='#ffffff'
            )

        # Physics config
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

        # Save graph
        net.save_graph('network.html')

        return 'network.html'

    except Exception as e:
        print("Error building network graph:", e)
        return None
