def correlate_datasets(dfs_dict):
    """Correlate phone numbers across multiple datasets"""
    try:
        profiles = []
        
        # Get all datasets that exist
        available_datasets = {key: df for key, df in dfs_dict.items() if df is not None}
        
        if not available_datasets:
            return profiles
        
        # Collect all phone numbers from all datasets
        all_phone_numbers = set()
        dataset_phone_columns = {}
        
        for dataset_name, df in available_datasets.items():
            phone_columns = []
            
            # Find phone number columns in this dataset
            for col in df.columns:
                sample_values = df[col].dropna().astype(str)
                # Check if column contains 10-digit numbers
                if sample_values.str.match(r'^\d{10}$').sum() > len(sample_values) * 0.3:
                    phone_columns.append(col)
            
            dataset_phone_columns[dataset_name] = phone_columns
            
            # Collect phone numbers from this dataset
            for col in phone_columns:
                numbers = df[col].dropna().astype(str)
                numbers = numbers[numbers.str.match(r'^\d{10}$')]
                all_phone_numbers.update(numbers.tolist())
        
        # Build profile for each phone number
        for number in all_phone_numbers:
            profile = {
                'number': number,
                'found_in': [],
                'total_calls': 0,
                'locations': [],
                'websites': [],
                'call_details': {}
            }
            
            # Check each dataset for this number
            for dataset_name, df in available_datasets.items():
                phone_columns = dataset_phone_columns[dataset_name]
                
                # Check if number exists in this dataset
                number_found = False
                
                for col in phone_columns:
                    mask = df[col].astype(str) == number
                    if mask.any():
                        number_found = True
                        profile['found_in'].append(dataset_name)
                        
                        # Count occurrences
                        count = mask.sum()
                        profile['total_calls'] += count
                        
                        # Collect dataset-specific information
                        if dataset_name == 'cdr':
                            # Call detail records
                            profile['call_details'] = {
                                'total_calls': count,
                                'avg_duration': df.loc[mask, 'duration'].mean() if 'duration' in df.columns else 0,
                                'night_calls': 0,  # Could be calculated if datetime available
                                'missed_calls': 0   # Could be calculated if call_type available
                            }
                        elif dataset_name == 'tower':
                            # Tower location data
                            if 'lat' in df.columns and 'lon' in df.columns:
                                locations = df.loc[mask, ['lat', 'lon']].drop_duplicates().values.tolist()
                                profile['locations'].extend([f"{lat:.4f},{lon:.4f}" for lat, lon in locations])
                            if 'area' in df.columns:
                                areas = df.loc[mask, 'area'].unique().tolist()
                                profile['locations'].extend(areas)
                        elif dataset_name == 'ipdr':
                            # IP detail records
                            if 'url' in df.columns:
                                urls = df.loc[mask, 'url'].unique().tolist()
                                profile['websites'].extend(urls[:10])  # Limit to 10 websites
                            if 'website' in df.columns:
                                websites = df.loc[mask, 'website'].unique().tolist()
                                profile['websites'].extend(websites[:10])
                
                if number_found:
                    break  # Found in at least one column of this dataset
            
            # Only add profile if number was found in multiple datasets or has interesting data
            if len(profile['found_in']) > 1 or profile['total_calls'] > 10 or profile['locations'] or profile['websites']:
                # Remove duplicates and sort
                profile['found_in'] = list(set(profile['found_in']))
                profile['locations'] = list(set(profile['locations']))[:5]  # Limit to 5 locations
                profile['websites'] = list(set(profile['websites']))[:10]  # Limit to 10 websites
                
                profiles.append(profile)
        
        # Sort profiles by total calls (most active first)
        profiles.sort(key=lambda x: x['total_calls'], reverse=True)
        
        return profiles
        
    except Exception as e:
        print(f"Error in correlation analysis: {e}")
        return []

def correlation_to_text(profiles):
    """Convert correlation profiles to readable text"""
    try:
        text_parts = []
        
        text_parts.append("CROSS-DATASET CORRELATION ANALYSIS")
        text_parts.append("=" * 50)
        
        if not profiles:
            text_parts.append("No cross-dataset correlations found.")
            return "\n".join(text_parts)
        
        text_parts.append(f"\nFound {len(profiles)} phone numbers with cross-dataset activity:")
        text_parts.append("-" * 50)
        
        # Top profiles
        for i, profile in enumerate(profiles[:10]):  # Show top 10
            text_parts.append(f"\n{i+1}. Phone: {profile['number']}")
            text_parts.append(f"   Found in: {', '.join(profile['found_in'])}")
            text_parts.append(f"   Total calls: {profile['total_calls']}")
            
            if profile['locations']:
                text_parts.append(f"   Locations: {', '.join(profile['locations'][:3])}")
            
            if profile['websites']:
                text_parts.append(f"   Websites: {', '.join(profile['websites'][:3])}")
            
            if profile['call_details']:
                details = profile['call_details']
                text_parts.append(f"   Call Details:")
                if 'avg_duration' in details and details['avg_duration'] > 0:
                    text_parts.append(f"     Average duration: {details['avg_duration']:.1f} seconds")
                if 'night_calls' in details and details['night_calls'] > 0:
                    text_parts.append(f"     Night calls: {details['night_calls']}")
                if 'missed_calls' in details and details['missed_calls'] > 0:
                    text_parts.append(f"     Missed calls: {details['missed_calls']}")
        
        # Summary statistics
        multi_dataset_count = sum(1 for p in profiles if len(p['found_in']) > 1)
        with_locations_count = sum(1 for p in profiles if p['locations'])
        with_websites_count = sum(1 for p in profiles if p['websites'])
        
        text_parts.append(f"\n\nSUMMARY:")
        text_parts.append(f"Numbers found in multiple datasets: {multi_dataset_count}")
        text_parts.append(f"Numbers with location data: {with_locations_count}")
        text_parts.append(f"Numbers with website activity: {with_websites_count}")
        
        # High correlation indicators
        high_correlation = [p for p in profiles if len(p['found_in']) >= 3 and p['total_calls'] > 50]
        if high_correlation:
            text_parts.append(f"\n\nHIGH CORRELATION NUMBERS:")
            text_parts.append("-" * 30)
            for profile in high_correlation[:5]:
                text_parts.append(f"{profile['number']}: {profile['total_calls']} calls across {len(profile['found_in'])} datasets")
        
    except Exception as e:
        text_parts.append(f"Error converting correlation to text: {e}")
    
    return "\n".join(text_parts)

def find_suspicious_correlations(profiles):
    """Find highly suspicious cross-dataset patterns"""
    try:
        suspicious = []
        
        for profile in profiles:
            suspicion_score = 0
            reasons = []
            
            # High activity across multiple datasets
            if len(profile['found_in']) >= 3:
                suspicion_score += 30
                reasons.append(f"Active in {len(profile['found_in'])} different datasets")
            
            # High call volume
            if profile['total_calls'] > 100:
                suspicion_score += 25
                reasons.append(f"High call volume: {profile['total_calls']} calls")
            
            # Multiple locations
            if len(profile['locations']) >= 3:
                suspicion_score += 20
                reasons.append(f"Multiple locations: {len(profile['locations'])}")
            
            # Website activity + call activity
            if profile['websites'] and profile['total_calls'] > 20:
                suspicion_score += 15
                reasons.append("Both call and internet activity")
            
            # Found in CDR + Tower + IPDR (all three)
            if all(dataset in profile['found_in'] for dataset in ['cdr', 'tower', 'ipdr']):
                suspicion_score += 35
                reasons.append("Complete digital footprint across all datasets")
            
            if suspicion_score >= 40:  # Threshold for suspicious
                suspicious.append({
                    'number': profile['number'],
                    'score': suspicion_score,
                    'reasons': reasons,
                    'profile': profile
                })
        
        # Sort by suspicion score
        suspicious.sort(key=lambda x: x['score'], reverse=True)
        
        return suspicious
        
    except Exception as e:
        print(f"Error finding suspicious correlations: {e}")
        return []