def detect_same_tower_meetings(tower_df, time_window_minutes=15):
    """
    Detect instances where multiple phones were at the same tower within a time window.
    
    Args:
        tower_df: DataFrame with tower dump data
        time_window_minutes: Time window in minutes to consider as co-location (default: 15)
    
    Returns:
        List of co-location events with details
    """
    if tower_df is None:
        return []
    
    try:
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Convert to DataFrame if not already
        if not isinstance(tower_df, pd.DataFrame):
            tower_df = pd.DataFrame(tower_df)
        
        # Find datetime column
        datetime_col = None
        for col in tower_df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                datetime_col = col
                break
        
        if datetime_col is None:
            print("No datetime column found in tower data")
            return []
        
        # Find phone and tower columns
        phone_col = None
        tower_col = None
        for col in tower_df.columns:
            col_lower = col.lower()
            if 'phone' in col_lower or 'number' in col_lower:
                phone_col = col
            elif 'tower' in col_lower or 'bts' in col_lower:
                tower_col = col
        
        if not phone_col or not tower_col:
            print("Phone or tower column not found")
            return []
        
        # Convert datetime column to datetime objects
        tower_df[datetime_col] = pd.to_datetime(tower_df[datetime_col])
        
        # Sort by tower and datetime
        tower_df = tower_df.sort_values([tower_col, datetime_col])
        
        co_locations = []
        
        # Group by tower
        for tower_id, tower_group in tower_df.groupby(tower_col):
            # Get all connections to this tower
            connections = tower_group.to_dict('records')
            
            # Check for co-locations within time window
            for i, conn1 in enumerate(connections):
                for j, conn2 in enumerate(connections[i+1:], i+1):
                    # Skip if same phone number
                    if conn1[phone_col] == conn2[phone_col]:
                        continue
                    
                    # Calculate time difference
                    time_diff = conn2[datetime_col] - conn1[datetime_col]
                    
                    # Check if within time window (positive and negative)
                    if abs(time_diff.total_seconds()) <= time_window_minutes * 60:
                        co_location = {
                            'tower_id': tower_id,
                            'datetime1': conn1[datetime_col],
                            'datetime2': conn2[datetime_col],
                            'phone1': conn1[phone_col],
                            'phone2': conn2[phone_col],
                            'time_diff_minutes': abs(time_diff.total_seconds() / 60),
                            'event_type': 'SAME_TOWER_COLOCATION'
                        }
                        
                        # Add location info if available
                        for col in tower_df.columns:
                            if 'lat' in col.lower():
                                co_location['latitude'] = conn1[col]
                            elif 'lon' in col.lower() or 'lng' in col.lower():
                                co_location['longitude'] = conn1[col]
                            elif 'area' in col.lower():
                                co_location['area'] = conn1[col]
                        
                        co_locations.append(co_location)
        
        return co_locations
        
    except Exception as e:
        print(f"Error detecting same tower meetings: {e}")
        return []

def analyze_meeting_patterns(co_locations, scores=None):
    """
    Analyze patterns in co-location events.
    
    Args:
        co_locations: List of co-location events
        scores: Suspicion scores for phone numbers
    
    Returns:
        Dictionary with pattern analysis
    """
    if not co_locations:
        return {"message": "No co-location events found"}
    
    try:
        import pandas as pd
        from collections import defaultdict, Counter
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(co_locations)
        
        # Build scores lookup
        scores_lookup = {}
        if scores:
            for s in scores:
                scores_lookup[str(s.get('number', ''))] = s
        
        analysis = {
            'total_co_locations': len(co_locations),
            'unique_towers': df['tower_id'].nunique(),
            'unique_phones': len(set(df['phone1'].tolist() + df['phone2'].tolist())),
            'most_active_towers': df['tower_id'].value_counts().head(5).to_dict(),
            'time_distribution': {
                'under_5_min': len(df[df['time_diff_minutes'] <= 5]),
                '5_to_15_min': len(df[(df['time_diff_minutes'] > 5) & (df['time_diff_minutes'] <= 15)]),
                'over_15_min': len(df[df['time_diff_minutes'] > 15])
            }
        }
        
        # Analyze high-risk phone involvement
        high_risk_meetings = []
        for _, event in df.iterrows():
            phone1_risk = 'unknown'
            phone2_risk = 'unknown'
            
            if str(event['phone1']) in scores_lookup:
                phone1_risk = scores_lookup[str(event['phone1'])].get('label', 'unknown')
            
            if str(event['phone2']) in scores_lookup:
                phone2_risk = scores_lookup[str(event['phone2'])].get('label', 'unknown')
            
            if 'HIGH' in phone1_risk.upper() or 'HIGH' in phone2_risk.upper():
                high_risk_meetings.append({
                    'tower_id': event['tower_id'],
                    'phone1': event['phone1'],
                    'phone2': event['phone2'],
                    'phone1_risk': phone1_risk,
                    'phone2_risk': phone2_risk,
                    'datetime': event['datetime1'],
                    'time_diff': event['time_diff_minutes']
                })
        
        analysis['high_risk_meetings'] = high_risk_meetings
        analysis['high_risk_meeting_count'] = len(high_risk_meetings)
        
        # Find most frequent meeting pairs
        meeting_pairs = []
        for _, event in df.iterrows():
            pair = tuple(sorted([event['phone1'], event['phone2']]))
            meeting_pairs.append(pair)
        
        pair_counts = Counter(meeting_pairs)
        analysis['frequent_meeting_pairs'] = [
            {'phones': list(pair), 'count': count}
            for pair, count in pair_counts.most_common(5)
        ]
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing meeting patterns: {e}")
        return {"error": str(e)}

def generate_colocation_report(co_locations, analysis, output_file='colocation_report.html'):
    """
    Generate HTML report for co-location analysis.
    
    Args:
        co_locations: List of co-location events
        analysis: Pattern analysis results
        output_file: Output filename
    
    Returns:
        Path to generated report
    """
    try:
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TeleForensic AI - Co-Location Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section {{
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .high-risk {{
            border-left: 4px solid #dc3545;
            background-color: #fff5f5;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .risk-high {{
            color: #dc3545;
            font-weight: bold;
        }}
        .risk-medium {{
            color: #fd7e14;
            font-weight: bold;
        }}
        .risk-low {{
            color: #28a745;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 TeleForensic AI</h1>
        <h2>Co-Location Analysis Report</h2>
        <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h3>📊 Summary</h3>
        <p><strong>Total Co-Locations:</strong> {analysis.get('total_co_locations', 0)}</p>
        <p><strong>Unique Towers:</strong> {analysis.get('unique_towers', 0)}</p>
        <p><strong>Unique Phones:</strong> {analysis.get('unique_phones', 0)}</p>
        <p><strong>High-Risk Meetings:</strong> {analysis.get('high_risk_meeting_count', 0)}</p>
    </div>
    
    <div class="section">
        <h3>⏰ Time Distribution</h3>
        <ul>
            <li>Within 5 minutes: {analysis.get('time_distribution', {}).get('under_5_min', 0)}</li>
            <li>5-15 minutes: {analysis.get('time_distribution', {}).get('5_to_15_min', 0)}</li>
            <li>Over 15 minutes: {analysis.get('time_distribution', {}).get('over_15_min', 0)}</li>
        </ul>
    </div>
    
    <div class="section">
        <h3>🏆 Most Active Towers</h3>
        <table>
            <tr><th>Tower ID</th><th>Co-Location Count</th></tr>
"""
        
        # Add most active towers
        for tower_id, count in analysis.get('most_active_towers', {}).items():
            html_content += f"<tr><td>{tower_id}</td><td>{count}</td></tr>"
        
        html_content += """
        </table>
    </div>
"""
        
        # Add high-risk meetings if any
        if analysis.get('high_risk_meetings'):
            html_content += """
    <div class="section high-risk">
        <h3>⚠️ High-Risk Co-Locations</h3>
        <table>
            <tr>
                <th>Tower ID</th>
                <th>Phone 1</th>
                <th>Phone 2</th>
                <th>Risk Level</th>
                <th>Date/Time</th>
                <th>Time Diff</th>
            </tr>
"""
            
            for meeting in analysis['high_risk_meetings']:
                risk_class = 'risk-high' if 'HIGH' in str(meeting.get('phone1_risk', '')).upper() or 'HIGH' in str(meeting.get('phone2_risk', '')).upper() else 'risk-medium'
                html_content += f"""
            <tr>
                <td>{meeting.get('tower_id', 'N/A')}</td>
                <td>{meeting.get('phone1', 'N/A')}</td>
                <td>{meeting.get('phone2', 'N/A')}</td>
                <td class="{risk_class}">{meeting.get('phone1_risk', 'N/A')} / {meeting.get('phone2_risk', 'N/A')}</td>
                <td>{meeting.get('datetime', 'N/A')}</td>
                <td>{meeting.get('time_diff', 'N/A')} min</td>
            </tr>
"""
            
            html_content += """
        </table>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
        
    except Exception as e:
        print(f"Error generating colocation report: {e}")
        return None
