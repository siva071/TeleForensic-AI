def build_graph(df, scores):
    """Build network graph from call data"""
    try:
        # Find caller and receiver columns
        caller_col = None
        receiver_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if caller_col is None and any(keyword in col_lower for keyword in ['caller', 'from', 'calling', 'dial']):
                caller_col = col
            elif receiver_col is None and any(keyword in col_lower for keyword in ['receiver', 'to', 'called', 'receive']):
                receiver_col = col
        
        if not caller_col or not receiver_col:
            print("Could not find caller and receiver columns")
            return None
        
        # Import required libraries
        try:
            from pyvis.network import Network
            import networkx as nx
        except ImportError:
            print("pyvis or networkx not installed")
            return None
        
        # Create network
        net = Network(
            height='600px', 
            width='100%',
            bgcolor='#1a1a2e',
            font_color='white',
            directed=True
        )
        
        # Build score lookup dict
        score_lookup = {}
        for score_data in scores:
            score_lookup[score_data['number']] = score_data
        
        # Count call frequencies
        call_frequencies = {}
        for _, row in df.iterrows():
            caller = str(row[caller_col])
            receiver = str(row[receiver_col])
            
            # Clean numbers (keep only digits)
            caller_clean = ''.join(filter(str.isdigit, caller))
            receiver_clean = ''.join(filter(str.isdigit, receiver))
            
            if len(caller_clean) >= 10 and len(receiver_clean) >= 10:
                caller_clean = caller_clean[-10:]
                receiver_clean = receiver_clean[-10:]
                
                pair = (caller_clean, receiver_clean)
                call_frequencies[pair] = call_frequencies.get(pair, 0) + 1
        
        # Add nodes and edges
        all_numbers = set()
        for caller, receiver in call_frequencies.keys():
            all_numbers.add(caller)
            all_numbers.add(receiver)
        
        # Add nodes
        for number in all_numbers:
            score_data = score_lookup.get(number, {'score': 0, 'label': 'Unknown', 'color': '#888888'})
            frequency = sum(freq for (c, r), freq in call_frequencies.items() if c == number or r == number)
            
            # Node size based on frequency
            size = min(10 + frequency * 2, 50)  # Cap at 50
            
            # Node color based on risk level
            color = score_data.get('color', '#888888')
            
            net.add_node(
                number,
                label=f"{number}\n({score_data.get('label', 'Unknown')})",
                color=color,
                size=size,
                title=f"Number: {number}\nRisk Level: {score_data.get('label', 'Unknown')}\nScore: {score_data.get('score', 0)}\nTotal Calls: {frequency}"
            )
        
        # Add edges
        for (caller, receiver), frequency in call_frequencies.items():
            # Edge width based on frequency
            width = min(1 + frequency / 5, 10)  # Cap at 10
            
            net.add_edge(
                caller, 
                receiver,
                width=width,
                title=f"Calls: {frequency}",
                color='#ffffff'
            )
        
        # Configure physics
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200
          }
        }
        """)
        
        # Save the graph
        net.save_graph('network.html')
        
        return 'network.html'
        
    except Exception as e:
        print(f"Error building network graph: {e}")
        return None

print("Caller col:", caller_col)
print("Receiver col:", receiver_col)
print("Call freq len:", len(call_frequencies))
