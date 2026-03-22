def create_timeline_analysis(tower_df, cdr_df=None, time_grouping='hour'):
    """
    Create timeline analysis of tower connections and calls.
    
    Args:
        tower_df: DataFrame with tower dump data
        cdr_df: DataFrame with call detail records (optional)
        time_grouping: 'hour', 'day', or 'week' for grouping intervals
    
    Returns:
        Dictionary with timeline data
    """
    if tower_df is None:
        return {}
    
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
            return {}
        
        # Convert datetime column
        tower_df[datetime_col] = pd.to_datetime(tower_df[datetime_col])
        
        # Extract time components
        tower_df['hour'] = tower_df[datetime_col].dt.hour
        tower_df['day'] = tower_df[datetime_col].dt.day
        tower_df['date'] = tower_df[datetime_col].dt.date
        tower_df['weekday'] = tower_df[datetime_col].dt.day_name()
        
        # Find phone column
        phone_col = None
        tower_col = None
        for col in tower_df.columns:
            col_lower = col.lower()
            if 'phone' in col_lower or 'number' in col_lower:
                phone_col = col
            elif 'tower' in col_lower or 'bts' in col_lower:
                tower_col = col
        
        timeline_data = {}
        
        if time_grouping == 'hour':
            # Hourly activity
            hourly_activity = tower_df.groupby('hour').size().to_dict()
            timeline_data['hourly_activity'] = hourly_activity
            
            # Peak hours
            peak_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
            timeline_data['peak_hours'] = peak_hours
            
            # Night activity (11 PM - 5 AM)
            night_activity = tower_df[(tower_df['hour'] >= 23) | (tower_df['hour'] <= 5)]
            timeline_data['night_activity'] = {
                'count': len(night_activity),
                'percentage': (len(night_activity) / len(tower_df)) * 100
            }
            
        elif time_grouping == 'day':
            # Daily activity
            daily_activity = tower_df.groupby('date').size().to_dict()
            timeline_data['daily_activity'] = {str(k): v for k, v in daily_activity.items()}
            
            # Most active days
            most_active_days = sorted(daily_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            timeline_data['most_active_days'] = [(str(k), v) for k, v in most_active_days]
            
        elif time_grouping == 'week':
            # Weekly activity (by weekday)
            weekly_activity = tower_df.groupby('weekday').size().to_dict()
            timeline_data['weekly_activity'] = weekly_activity
            
            # Most active weekdays
            most_active_weekdays = sorted(weekly_activity.items(), key=lambda x: x[1], reverse=True)
            timeline_data['most_active_weekdays'] = most_active_weekdays
        
        # Phone-specific timeline
        if phone_col:
            phone_timeline = tower_df.groupby([phone_col, 'hour']).size().reset_index(name='count')
            timeline_data['phone_hourly_activity'] = phone_timeline.to_dict('records')
            
            # Most active phones per hour
            most_active_phones = tower_df.groupby(phone_col).size().sort_values(ascending=False).head(10)
            timeline_data['most_active_phones'] = most_active_phones.to_dict()
        
        # Tower-specific timeline
        if tower_col:
            tower_timeline = tower_df.groupby([tower_col, 'hour']).size().reset_index(name='count')
            timeline_data['tower_hourly_activity'] = tower_timeline.to_dict('records')
            
            # Most active towers
            most_active_towers = tower_df.groupby(tower_col).size().sort_values(ascending=False).head(10)
            timeline_data['most_active_towers'] = most_active_towers.to_dict()
        
        return timeline_data
        
    except Exception as e:
        print(f"Error creating timeline analysis: {e}")
        return {}

def create_timeline_visualization(timeline_data, output_file='timeline.html'):
    """
    Create interactive HTML timeline visualization.
    
    Args:
        timeline_data: Dictionary with timeline analysis results
        output_file: Output filename
    
    Returns:
        Path to generated visualization
    """
    try:
        import json
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TeleForensic AI - Timeline Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            margin-bottom: 20px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .stats {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-item {{
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            text-align: center;
        }}
        canvas {{
            max-height: 400px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕐 TeleForensic AI</h1>
        <h2>Timeline Analysis</h2>
        <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <h3>📊 Key Statistics</h3>
"""
        
        # Add statistics
        if 'night_activity' in timeline_data:
            night_data = timeline_data['night_activity']
            html_content += f"""
        <div class="stat-item">
            <h4>Night Activity</h4>
            <p>{night_data['count']} connections</p>
            <p>{night_data['percentage']:.1f}% of total</p>
        </div>
"""
        
        if 'peak_hours' in timeline_data:
            html_content += "<div class='stat-item'><h4>Peak Hours</h4><ul>"
            for hour, count in timeline_data['peak_hours']:
                html_content += f"<li>{hour:02d}:00 - {count} connections</li>"
            html_content += "</ul></div>"
        
        html_content += """
    </div>
    
    <div class="chart-grid">
"""
        
        # Hourly activity chart
        if 'hourly_activity' in timeline_data:
            hourly_data = timeline_data['hourly_activity']
            hours = list(range(24))
            counts = [hourly_data.get(h, 0) for h in hours]
            
            html_content += f"""
        <div class="chart-container">
            <h3>Hourly Activity Pattern</h3>
            <canvas id="hourlyChart"></canvas>
        </div>
"""
        
        # Weekly activity chart
        if 'weekly_activity' in timeline_data:
            weekly_data = timeline_data['weekly_activity']
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            counts = [weekly_data.get(day, 0) for day in weekdays]
            
            html_content += f"""
        <div class="chart-container">
            <h3>Weekly Activity Pattern</h3>
            <canvas id="weeklyChart"></canvas>
        </div>
"""
        
        html_content += """
    </div>
    
    <script>
"""
        
        # Add chart JavaScript
        if 'hourly_activity' in timeline_data:
            hourly_data = timeline_data['hourly_activity']
            hours = list(range(24))
            counts = [hourly_data.get(h, 0) for h in hours]
            
            html_content += f"""
        // Hourly Activity Chart
        const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
        new Chart(hourlyCtx, {{
            type: 'line',
            data: {{
                labels: {hours},
                datasets: [{{
                    label: 'Connections per Hour',
                    data: {counts},
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Tower Connections by Hour'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
"""
        
        if 'weekly_activity' in timeline_data:
            weekly_data = timeline_data['weekly_activity']
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            counts = [weekly_data.get(day, 0) for day in weekdays]
            
            html_content += f"""
        // Weekly Activity Chart
        const weeklyCtx = document.getElementById('weeklyChart').getContext('2d');
        new Chart(weeklyCtx, {{
            type: 'bar',
            data: {{
                labels: {weekdays},
                datasets: [{{
                    label: 'Connections per Day',
                    data: {counts},
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(199, 199, 199, 0.8)'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Tower Connections by Weekday'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
"""
        
        html_content += """
    </script>
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
        
    except Exception as e:
        print(f"Error creating timeline visualization: {e}")
        return None

def analyze_temporal_patterns(tower_df, scores=None):
    """
    Analyze temporal patterns in tower connections.
    
    Args:
        tower_df: DataFrame with tower dump data
        scores: Suspicion scores for phone numbers
    
    Returns:
        Dictionary with temporal pattern analysis
    """
    if tower_df is None:
        return {}
    
    try:
        import pandas as pd
        
        # Get timeline data
        timeline_data = create_timeline_analysis(tower_df)
        
        # Build scores lookup
        scores_lookup = {}
        if scores:
            for s in scores:
                scores_lookup[str(s.get('number', ''))] = s
        
        patterns = {
            'anomaly_detection': [],
            'high_risk_patterns': [],
            'suspicious_time_windows': []
        }
        
        # Detect anomalies in hourly patterns
        if 'hourly_activity' in timeline_data:
            hourly_activity = timeline_data['hourly_activity']
            
            # Find unusual peaks (more than 2x average)
            avg_activity = sum(hourly_activity.values()) / len(hourly_activity) if hourly_activity else 0
            for hour, count in hourly_activity.items():
                if count > avg_activity * 2:
                    patterns['anomaly_detection'].append({
                        'type': 'UNUSUAL_PEAK',
                        'hour': hour,
                        'count': count,
                        'average': avg_activity,
                        'severity': 'HIGH' if count > avg_activity * 3 else 'MEDIUM'
                    })
        
        # Analyze high-risk phone patterns
        if 'phone_hourly_activity' in timeline_data and scores:
            phone_activity = timeline_data['phone_hourly_activity']
            
            for activity in phone_activity:
                phone = str(activity.get('phone', ''))
                if phone in scores_lookup:
                    risk_level = scores_lookup[phone].get('label', '').upper()
                    if 'HIGH' in risk_level:
                        patterns['high_risk_patterns'].append({
                            'phone': phone,
                            'hour': activity.get('hour'),
                            'count': activity.get('count'),
                            'risk_level': risk_level,
                            'pattern': 'HIGH_RISK_ACTIVITY'
                        })
        
        # Identify suspicious time windows
        if 'night_activity' in timeline_data:
            night_data = timeline_data['night_activity']
            if night_data['percentage'] > 30:  # More than 30% activity at night
                patterns['suspicious_time_windows'].append({
                    'type': 'EXCESSIVE_NIGHT_ACTIVITY',
                    'percentage': night_data['percentage'],
                    'count': night_data['count'],
                    'severity': 'HIGH' if night_data['percentage'] > 50 else 'MEDIUM'
                })
        
        return patterns
        
    except Exception as e:
        print(f"Error analyzing temporal patterns: {e}")
        return {}
