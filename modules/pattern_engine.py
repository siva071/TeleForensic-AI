import pandas as pd
import numpy as np
from datetime import datetime
import re

def analyze_patterns(df):
    """Analyze patterns in the dataframe"""
    findings = {}
    
    try:
        # Find phone number columns
        phone_columns = []
        for col in df.columns:
            sample_values = df[col].dropna().astype(str)
            # Check if column contains 10-digit numbers
            if sample_values.str.match(r'^\d{10}$').sum() > len(sample_values) * 0.3:  # At least 30% are 10-digit numbers
                phone_columns.append(col)
        
        if phone_columns:
            # 1. FREQUENT NUMBERS
            frequent_data = {}
            for col in phone_columns:
                value_counts = df[col].value_counts().head(10)
                frequent_data[col] = value_counts.to_dict()
            findings['frequent'] = frequent_data
            
            # 2. SHORT CALLS
            if 'duration' in df.columns:
                short_calls = df[df['duration'] < 30]
                short_call_counts = {}
                for col in phone_columns:
                    short_call_counts[col] = short_calls[col].value_counts().to_dict()
                findings['short_calls'] = short_call_counts
            
            # 3. NIGHT CALLS
            datetime_cols = []
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]' or 'date' in col.lower() or 'time' in col.lower():
                    datetime_cols.append(col)
            
            if datetime_cols:
                night_calls_data = {}
                for dt_col in datetime_cols:
                    # Extract hour from datetime
                    df_temp = df.copy()
                    df_temp['hour'] = pd.to_datetime(df_temp[dt_col]).dt.hour
                    night_calls = df_temp[(df_temp['hour'] >= 20) | (df_temp['hour'] <= 5)]
                    
                    for col in phone_columns:
                        night_calls_data[f"{col}_night"] = night_calls[col].value_counts().to_dict()
                
                findings['night_calls'] = night_calls_data
            
            # 4. MISSED CALLS
            if 'call_type' in df.columns:
                missed_calls = df[df['call_type'].str.lower().isin(['missed', 'missed call', 'unanswered'])]
                missed_call_counts = {}
                for col in phone_columns:
                    missed_call_counts[col] = missed_calls[col].value_counts().to_dict()
                findings['missed_calls'] = missed_call_counts
            
            # 5. SEQUENTIAL NUMBERS
            all_numbers = set()
            for col in phone_columns:
                numbers = df[col].dropna().astype(str)
                numbers = numbers[numbers.str.match(r'^\d{10}$')]
                all_numbers.update(numbers.tolist())
            
            # Sort numerically and find sequential groups
            sorted_numbers = sorted([int(num) for num in all_numbers])
            sequential_groups = []
            
            i = 0
            while i < len(sorted_numbers):
                group = [sorted_numbers[i]]
                j = i + 1
                
                while j < len(sorted_numbers) and sorted_numbers[j] - sorted_numbers[j-1] <= 3:
                    group.append(sorted_numbers[j])
                    j += 1
                
                if len(group) >= 3:
                    sequential_groups.append([str(num) for num in group])
                
                i = j if j > i else i + 1
            
            findings['sequential'] = sequential_groups
        
        # 6. GENERAL STATS for non-phone data
        general_stats = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                value_counts = df[col].value_counts().head(10)
                general_stats[col] = value_counts.to_dict()
            elif df[col].dtype in ['int64', 'float64']:
                general_stats[col] = {
                    'mean': df[col].mean(),
                    'max': df[col].max(),
                    'min': df[col].min(),
                    'count': df[col].count()
                }
        
        findings['general_stats'] = general_stats
        
    except Exception as e:
        print(f"Error in pattern analysis: {e}")
        findings['error'] = str(e)
    
    return findings

def findings_to_text(findings, df):
    """Convert findings to readable text"""
    text_parts = []
    
    try:
        text_parts.append("PATTERN ANALYSIS REPORT")
        text_parts.append("=" * 50)
        
        # Frequent numbers
        if 'frequent' in findings:
            text_parts.append("\n1. FREQUENT NUMBERS (Top 10):")
            text_parts.append("-" * 30)
            for col, counts in findings['frequent'].items():
                text_parts.append(f"\n{col}:")
                for number, count in list(counts.items())[:5]:
                    text_parts.append(f"  {number}: {count} times")
        
        # Short calls
        if 'short_calls' in findings:
            text_parts.append("\n\n2. SHORT CALLS (< 30 seconds):")
            text_parts.append("-" * 30)
            for col, counts in findings['short_calls'].items():
                if counts:
                    text_parts.append(f"\n{col}:")
                    for number, count in list(counts.items())[:5]:
                        text_parts.append(f"  {number}: {count} short calls")
        
        # Night calls
        if 'night_calls' in findings:
            text_parts.append("\n\n3. NIGHT CALLS (11 PM - 5 AM):")
            text_parts.append("-" * 30)
            for col, counts in findings['night_calls'].items():
                if counts:
                    text_parts.append(f"\n{col}:")
                    for number, count in list(counts.items())[:5]:
                        text_parts.append(f"  {number}: {count} night calls")
        
        # Missed calls
        if 'missed_calls' in findings:
            text_parts.append("\n\n4. MISSED CALLS:")
            text_parts.append("-" * 30)
            for col, counts in findings['missed_calls'].items():
                if counts:
                    text_parts.append(f"\n{col}:")
                    for number, count in list(counts.items())[:5]:
                        text_parts.append(f"  {number}: {count} missed calls")
        
        # Sequential numbers
        if 'sequential' in findings:
            text_parts.append("\n\n5. SEQUENTIAL NUMBER SERIES:")
            text_parts.append("-" * 30)
            for i, group in enumerate(findings['sequential'][:5]):
                text_parts.append(f"Series {i+1}: {' → '.join(group[:5])}")
        
        # General statistics
        if 'general_stats' in findings:
            text_parts.append("\n\n6. GENERAL STATISTICS:")
            text_parts.append("-" * 30)
            for col, stats in findings['general_stats'].items():
                text_parts.append(f"\n{col}:")
                if isinstance(stats, dict):
                    if 'mean' in stats:  # Numeric column
                        text_parts.append(f"  Mean: {stats['mean']:.2f}")
                        text_parts.append(f"  Max: {stats['max']}")
                        text_parts.append(f"  Min: {stats['min']}")
                    else:  # Categorical column
                        for value, count in list(stats.items())[:3]:
                            text_parts.append(f"  {value}: {count} times")
        
        # Error handling
        if 'error' in findings:
            text_parts.append(f"\n\nERROR: {findings['error']}")
    
    except Exception as e:
        text_parts.append(f"Error converting findings to text: {e}")
    
    return "\n".join(text_parts)