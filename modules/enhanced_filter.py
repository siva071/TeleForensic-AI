def filter_high_risk_patterns(data_df, scores, filters=None):
    """
    Enhanced filtering for high-risk number patterns and suspicious activities.
    
    Args:
        data_df: DataFrame with CDR or tower data
        scores: List of suspicion scores
        filters: Dictionary of filter criteria
    
    Returns:
        Dictionary with filtered results and analysis
    """
    if data_df is None:
        return {}
    
    try:
        import pandas as pd
        import re
        from datetime import datetime, timedelta
        
        # Convert to DataFrame if not already
        if not isinstance(data_df, pd.DataFrame):
            data_df = pd.DataFrame(data_df)
        
        # Build scores lookup
        scores_lookup = {}
        if scores:
            for s in scores:
                scores_lookup[str(s.get('number', ''))] = s
        
        # Default filters
        default_filters = {
            'min_score': 50,
            'risk_levels': ['HIGH RISK', 'HIGH'],
            'time_patterns': ['night', 'weekend', 'early_morning'],
            'call_patterns': ['short_duration', 'high_frequency', 'missed_calls'],
            'sequential_numbers': True,
            'same_prefix': True,
            'geographic_clustering': True
        }
        
        if filters:
            default_filters.update(filters)
        
        filters = default_filters
        
        # Find phone number column
        phone_col = None
        for col in data_df.columns:
            if 'phone' in col.lower() or 'number' in col.lower():
                phone_col = col
                break
        
        if not phone_col:
            return {"error": "No phone number column found"}
        
        results = {
            'high_risk_numbers': [],
            'suspicious_patterns': [],
            'sequential_series': [],
            'geographic_clusters': [],
            'time_based_suspicion': [],
            'filtered_data': data_df.copy()
        }
        
        # Filter by high suspicion scores
        high_risk_phones = []
        for phone, score_data in scores_lookup.items():
            score = score_data.get('score', 0)
            label = score_data.get('label', '').upper()
            
            if score >= filters['min_score'] or any(risk in label for risk in filters['risk_levels']):
                high_risk_phones.append({
                    'phone': phone,
                    'score': score,
                    'label': label,
                    'reason': f"Score: {score}, Label: {label}"
                })
        
        results['high_risk_numbers'] = high_risk_phones
        
        # Filter data for high-risk numbers only
        if high_risk_phones:
            high_risk_phone_list = [item['phone'] for item in high_risk_phones]
            high_risk_data = data_df[data_df[phone_col].isin(high_risk_phone_list)]
            results['filtered_data'] = high_risk_data
        else:
            high_risk_data = data_df
        
        # Detect sequential number series
        if filters['sequential_numbers']:
            sequential_series = detect_sequential_numbers(high_risk_phones)
            results['sequential_series'] = sequential_series
        
        # Detect same prefix patterns
        if filters['same_prefix']:
            same_prefix_groups = detect_same_prefix_patterns(high_risk_phones)
            results['same_prefix_groups'] = same_prefix_groups
        
        # Analyze time-based patterns
        time_patterns = analyze_time_patterns(high_risk_data, phone_col, filters['time_patterns'])
        results['time_based_suspicion'] = time_patterns
        
        # Analyze call patterns if CDR data
        if 'duration' in data_df.columns or 'call_type' in data_df.columns:
            call_patterns = analyze_call_patterns(high_risk_data, phone_col, filters['call_patterns'])
            results['call_patterns'] = call_patterns
        
        # Geographic clustering if location data available
        if filters['geographic_clustering']:
            geo_clusters = detect_geographic_clustering(high_risk_data)
            results['geographic_clusters'] = geo_clusters
        
        # Generate summary statistics
        summary = {
            'total_numbers_analyzed': len(data_df[phone_col].unique()),
            'high_risk_count': len(high_risk_phones),
            'sequential_series_count': len(results.get('sequential_series', [])),
            'time_pattern_matches': len(results.get('time_based_suspicion', [])),
            'geographic_clusters': len(results.get('geographic_clusters', []))
        }
        
        results['summary'] = summary
        
        return results
        
    except Exception as e:
        print(f"Error in enhanced filtering: {e}")
        return {"error": str(e)}

def detect_sequential_numbers(phone_list):
    """
    Detect sequential number series in phone numbers.
    
    Args:
        phone_list: List of phone dictionaries with 'phone' key
    
    Returns:
        List of sequential series found
    """
    try:
        import re
        
        # Extract clean phone numbers (last 10 digits)
        clean_phones = []
        for item in phone_list:
            phone = str(item.get('phone', ''))
            digits = re.sub(r'\D', '', phone)
            if len(digits) >= 10:
                clean_phones.append(digits[-10:])
        
        series = []
        
        # Group by prefix (first 6 digits)
        prefix_groups = {}
        for phone in clean_phones:
            prefix = phone[:6]
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append(phone)
        
        # Find sequential patterns within each prefix group
        for prefix, phones in prefix_groups.items():
            if len(phones) >= 3:  # At least 3 numbers to form a series
                # Sort numerically
                phones_sorted = sorted(phones)
                
                # Look for consecutive sequences
                current_series = [phones_sorted[0]]
                
                for i in range(1, len(phones_sorted)):
                    current_num = int(phones_sorted[i])
                    prev_num = int(current_series[-1])
                    
                    if current_num == prev_num + 1:
                        current_series.append(phones_sorted[i])
                    else:
                        if len(current_series) >= 3:
                            series.append({
                                'prefix': prefix,
                                'series': current_series,
                                'count': len(current_series),
                                'start': current_series[0],
                                'end': current_series[-1]
                            })
                        current_series = [phones_sorted[i]]
                
                # Check the last series
                if len(current_series) >= 3:
                    series.append({
                        'prefix': prefix,
                        'series': current_series,
                        'count': len(current_series),
                        'start': current_series[0],
                        'end': current_series[-1]
                    })
        
        return series
        
    except Exception as e:
        print(f"Error detecting sequential numbers: {e}")
        return []

def detect_same_prefix_patterns(phone_list):
    """
    Detect phone numbers sharing the same prefix.
    
    Args:
        phone_list: List of phone dictionaries with 'phone' key
    
    Returns:
        List of prefix groups
    """
    try:
        import re
        
        # Extract clean phone numbers
        clean_phones = []
        for item in phone_list:
            phone = str(item.get('phone', ''))
            digits = re.sub(r'\D', '', phone)
            if len(digits) >= 6:
                clean_phones.append({
                    'original': phone,
                    'clean': digits[-10:],
                    'prefix': digits[-10:][:6]  # First 6 of last 10
                })
        
        # Group by prefix
        prefix_groups = {}
        for phone_data in clean_phones:
            prefix = phone_data['prefix']
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append(phone_data)
        
        # Filter for groups with 3+ numbers
        significant_groups = []
        for prefix, group in prefix_groups.items():
            if len(group) >= 3:
                significant_groups.append({
                    'prefix': prefix,
                    'count': len(group),
                    'phones': [item['original'] for item in group],
                    'pattern_type': 'SAME_PREFIX_SERIES'
                })
        
        # Sort by count (descending)
        significant_groups.sort(key=lambda x: x['count'], reverse=True)
        
        return significant_groups
        
    except Exception as e:
        print(f"Error detecting same prefix patterns: {e}")
        return []

def analyze_time_patterns(data_df, phone_col, time_patterns):
    """
    Analyze time-based suspicious patterns.
    
    Args:
        data_df: DataFrame with time data
        phone_col: Phone number column name
        time_patterns: List of time patterns to check
    
    Returns:
        List of time-based suspicious activities
    """
    try:
        import pandas as pd
        from datetime import datetime
        
        suspicious_activities = []
        
        # Find datetime column
        datetime_col = None
        for col in data_df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                datetime_col = col
                break
        
        if datetime_col is None:
            return []
        
        # Convert datetime
        data_df[datetime_col] = pd.to_datetime(data_df[datetime_col])
        data_df['hour'] = data_df[datetime_col].dt.hour
        data_df['weekday'] = data_df[datetime_col].dt.dayofweek  # 0=Monday, 6=Sunday
        
        # Check each time pattern
        for pattern in time_patterns:
            if pattern == 'night':
                # Night activity (11 PM - 5 AM)
                night_data = data_df[(data_df['hour'] >= 23) | (data_df['hour'] <= 5)]
                if not night_data.empty:
                    phone_night_counts = night_data[phone_col].value_counts()
                    for phone, count in phone_night_counts.items():
                        if count >= 5:  # 5+ night calls
                            suspicious_activities.append({
                                'phone': phone,
                                'pattern': 'EXCESSIVE_NIGHT_ACTIVITY',
                                'count': count,
                                'hours': '23:00-05:00',
                                'severity': 'HIGH' if count >= 10 else 'MEDIUM'
                            })
            
            elif pattern == 'weekend':
                # Weekend activity (Saturday, Sunday)
                weekend_data = data_df[data_df['weekday'] >= 5]
                if not weekend_data.empty:
                    phone_weekend_counts = weekend_data[phone_col].value_counts()
                    for phone, count in phone_weekend_counts.items():
                        if count >= 10:  # 10+ weekend calls
                            suspicious_activities.append({
                                'phone': phone,
                                'pattern': 'EXCESSIVE_WEEKEND_ACTIVITY',
                                'count': count,
                                'days': 'Saturday-Sunday',
                                'severity': 'MEDIUM'
                            })
            
            elif pattern == 'early_morning':
                # Early morning activity (5 AM - 8 AM)
                early_data = data_df[(data_df['hour'] >= 5) & (data_df['hour'] <= 8)]
                if not early_data.empty:
                    phone_early_counts = early_data[phone_col].value_counts()
                    for phone, count in phone_early_counts.items():
                        if count >= 7:  # 7+ early morning calls
                            suspicious_activities.append({
                                'phone': phone,
                                'pattern': 'EXCESSIVE_EARLY_MORNING_ACTIVITY',
                                'count': count,
                                'hours': '05:00-08:00',
                                'severity': 'MEDIUM'
                            })
        
        return suspicious_activities
        
    except Exception as e:
        print(f"Error analyzing time patterns: {e}")
        return []

def analyze_call_patterns(data_df, phone_col, call_patterns):
    """
    Analyze call-based suspicious patterns.
    
    Args:
        data_df: DataFrame with call data
        phone_col: Phone number column name
        call_patterns: List of call patterns to check
    
    Returns:
        List of call-based suspicious activities
    """
    try:
        import pandas as pd
        
        suspicious_calls = []
        
        # Check each call pattern
        for pattern in call_patterns:
            if pattern == 'short_duration' and 'duration' in data_df.columns:
                # Very short calls (potentially test calls or threats)
                short_calls = data_df[data_df['duration'] <= 10]  # 10 seconds or less
                if not short_calls.empty:
                    phone_short_counts = short_calls[phone_col].value_counts()
                    for phone, count in phone_short_counts.items():
                        if count >= 10:  # 10+ short calls
                            suspicious_calls.append({
                                'phone': phone,
                                'pattern': 'EXCESSIVE_SHORT_CALLS',
                                'count': count,
                                'avg_duration': short_calls[short_calls[phone_col] == phone]['duration'].mean(),
                                'severity': 'HIGH' if count >= 20 else 'MEDIUM'
                            })
            
            elif pattern == 'high_frequency' and phone_col in data_df.columns:
                # High frequency calling
                phone_counts = data_df[phone_col].value_counts()
                avg_calls = phone_counts.mean()
                
                for phone, count in phone_counts.items():
                    if count >= avg_calls * 3:  # 3x more than average
                        suspicious_calls.append({
                            'phone': phone,
                            'pattern': 'HIGH_FREQUENCY_CALLING',
                            'count': count,
                            'average': avg_calls,
                            'multiplier': count / avg_calls,
                            'severity': 'HIGH' if count >= avg_calls * 5 else 'MEDIUM'
                        })
            
            elif pattern == 'missed_calls' and 'call_type' in data_df.columns:
                # High number of missed calls
                missed_calls = data_df[data_df['call_type'].str.lower() == 'missed']
                if not missed_calls.empty:
                    phone_missed_counts = missed_calls[phone_col].value_counts()
                    for phone, count in phone_missed_counts.items():
                        if count >= 15:  # 15+ missed calls
                            suspicious_calls.append({
                                'phone': phone,
                                'pattern': 'EXCESSIVE_MISSED_CALLS',
                                'count': count,
                                'severity': 'MEDIUM'
                            })
        
        return suspicious_calls
        
    except Exception as e:
        print(f"Error analyzing call patterns: {e}")
        return []

def detect_geographic_clustering(data_df):
    """
    Detect geographic clustering of phone activity.
    
    Args:
        data_df: DataFrame with location data
    
    Returns:
        List of geographic clusters
    """
    try:
        import pandas as pd
        
        clusters = []
        
        # Find location columns
        lat_col = None
        lon_col = None
        area_col = None
        tower_col = None
        
        for col in data_df.columns:
            col_lower = col.lower()
            if 'lat' in col_lower:
                lat_col = col
            elif 'lon' in col_lower or 'lng' in col_lower:
                lon_col = col
            elif 'area' in col_lower:
                area_col = col
            elif 'tower' in col_lower or 'bts' in col_lower:
                tower_col = col
        
        if not any([lat_col, lon_col, area_col, tower_col]):
            return []
        
        # Group by location (area or tower)
        if area_col:
            location_groups = data_df.groupby(area_col)
        elif tower_col:
            location_groups = data_df.groupby(tower_col)
        else:
            return []
        
        for location_id, group in location_groups:
            if len(group) >= 5:  # 5+ connections to same location
                clusters.append({
                    'location_id': location_id,
                    'location_type': 'area' if area_col else 'tower',
                    'connection_count': len(group),
                    'unique_phones': group.select_dtypes(include=['object']).iloc[:, 0].nunique(),
                    'suspicion_level': 'HIGH' if len(group) >= 10 else 'MEDIUM'
                })
        
        # Sort by connection count
        clusters.sort(key=lambda x: x['connection_count'], reverse=True)
        
        return clusters
        
    except Exception as e:
        print(f"Error detecting geographic clustering: {e}")
        return []

def generate_enhanced_report(filter_results, output_file='enhanced_filter_report.html'):
    """
    Generate comprehensive HTML report for enhanced filtering results.
    
    Args:
        filter_results: Dictionary with filtering results
        output_file: Output filename
    
    Returns:
        Path to generated report
    """
    try:
        summary = filter_results.get('summary', {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TeleForensic AI - Enhanced Pattern Analysis</title>
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
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .metric h3 {{
            margin: 0 0 10px 0;
            color: #495057;
        }}
        .metric .value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
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
        .severity-high {{
            color: #dc3545;
            font-weight: bold;
        }}
        .severity-medium {{
            color: #fd7e14;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 TeleForensic AI</h1>
        <h2>Enhanced Pattern Analysis Report</h2>
        <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Numbers</h3>
            <div class="value">{summary.get('total_numbers_analyzed', 0)}</div>
        </div>
        <div class="metric">
            <h3>High Risk</h3>
            <div class="value">{summary.get('high_risk_count', 0)}</div>
        </div>
        <div class="metric">
            <h3>Sequential Series</h3>
            <div class="value">{summary.get('sequential_series_count', 0)}</div>
        </div>
        <div class="metric">
            <h3>Time Patterns</h3>
            <div class="value">{summary.get('time_pattern_matches', 0)}</div>
        </div>
    </div>
"""
        
        # Add high-risk numbers section
        high_risk_numbers = filter_results.get('high_risk_numbers', [])
        if high_risk_numbers:
            html_content += """
    <div class="section high-risk">
        <h3>⚠️ High-Risk Numbers</h3>
        <table>
            <tr><th>Phone Number</th><th>Suspicion Score</th><th>Risk Label</th><th>Reason</th></tr>
"""
            for item in high_risk_numbers:
                html_content += f"""
            <tr>
                <td>{item.get('phone', 'N/A')}</td>
                <td>{item.get('score', 'N/A')}</td>
                <td class="severity-high">{item.get('label', 'N/A')}</td>
                <td>{item.get('reason', 'N/A')}</td>
            </tr>
"""
            html_content += "        </table>\n    </div>\n"
        
        # Add sequential series section
        sequential_series = filter_results.get('sequential_series', [])
        if sequential_series:
            html_content += """
    <div class="section">
        <h3>🔢 Sequential Number Series</h3>
        <table>
            <tr><th>Prefix</th><th>Count</th><th>Start</th><th>End</th><th>Series</th></tr>
"""
            for series in sequential_series:
                series_str = " → ".join(series['series'])
                html_content += f"""
            <tr>
                <td>{series.get('prefix', 'N/A')}</td>
                <td>{series.get('count', 'N/A')}</td>
                <td>{series.get('start', 'N/A')}</td>
                <td>{series.get('end', 'N/A')}</td>
                <td>{series_str}</td>
            </tr>
"""
            html_content += "        </table>\n    </div>\n"
        
        html_content += """
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
        
    except Exception as e:
        print(f"Error generating enhanced report: {e}")
        return None
