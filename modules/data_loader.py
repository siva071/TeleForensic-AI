import pandas as pd
import numpy as np
from datetime import datetime
import re

def load_excel(file):
    """Read xlsx or csv file using pandas"""
    try:
        if file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return None
        return df
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def clean_dataframe(df):
    if df is None:
        return None
    
    import pandas as pd
    
    # Clean column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Identify phone number columns FIRST
    # before any datetime parsing
    phone_keywords = [
        'caller', 'receiver', 'phone',
        'number', 'mobile', 'msisdn',
        'calling', 'called', 'a_number',
        'b_number', 'from', 'to']
    
    phone_cols = []
    for col in df.columns:
        for keyword in phone_keywords:
            if keyword in col.lower():
                phone_cols.append(col)
                break
    
    # Identify datetime columns
    # EXCLUDE phone columns from datetime parsing
    date_keywords = [
        'datetime', 'date', 'time',
        'timestamp', 'when', 'start', 'end']
    
    date_cols = []
    for col in df.columns:
        if col in phone_cols:
            continue  # skip phone cols
        for keyword in date_keywords:
            if keyword in col.lower():
                date_cols.append(col)
                break
    
    # Clean phone number columns
    for col in phone_cols:
        df[col] = df[col].astype(str)
        df[col] = df[col].str.replace(
            r'[\+\-\s\(\)\.]', '', regex=True)
        df[col] = df[col].str.replace(
            r'^(91|0)', '', regex=True)
        df[col] = df[col].str.strip()
        df[col] = df[col].apply(
            lambda x: x[-10:] 
            if len(x) >= 10 else x)
        df[col] = df[col].replace(
            ['nan', 'none', 'null', 
             'nat', '', 'NaT'], None)
    
    # Parse datetime columns
    for col in date_cols:
        try:
            df[col] = pd.to_datetime(
                df[col],
                infer_datetime_format=True,
                errors='coerce')
        except Exception:
            pass
    
    # Strip whitespace from other string cols
    for col in df.columns:
        if col not in phone_cols and \
           col not in date_cols:
            if df[col].dtype == object:
                df[col] = df[col].astype(
                    str).str.strip()
    
    # Fill numeric NaN with 0
    for col in df.columns:
        if df[col].dtype in ['float64','int64']:
            df[col] = df[col].fillna(0)
    
    # Drop completely empty rows
    df = df.dropna(how='all')
    
    return df

def detect_file_type(df):
    """Detect file type based on column names"""
    try:
        columns = [col.lower() for col in df.columns]
        
        # CDR keywords
        cdr_keywords = ['caller', 'receiver', 'duration', 'call', 'called', 'dialled', 'dialed']
        # Tower keywords  
        tower_keywords = ['tower', 'bts', 'lat', 'lon', 'latitude', 'longitude', 'area', 'location']
        # IPDR keywords
        ipdr_keywords = ['ip', 'url', 'protocol', 'data', 'website', 'domain']
        
        cdr_score = sum(1 for keyword in cdr_keywords if keyword in ' '.join(columns))
        tower_score = sum(1 for keyword in tower_keywords if keyword in ' '.join(columns))
        ipdr_score = sum(1 for keyword in ipdr_keywords if keyword in ' '.join(columns))
        
        if cdr_score >= 2:
            return 'cdr'
        elif tower_score >= 2:
            return 'tower'
        elif ipdr_score >= 2:
            return 'ipdr'
        else:
            return 'unknown'
    except Exception as e:
        print(f"Error detecting file type: {e}")
        return 'unknown'

def get_file_summary(df, filename):
    """Generate file summary"""
    try:
        summary = f"""File: {filename}
Rows: {len(df)}
Columns: {list(df.columns)}
Data preview:
{df.head(3).to_string()}"""
        return summary
    except Exception as e:
        print(f"Error generating file summary: {e}")
        return f"Error generating summary for {filename}"
