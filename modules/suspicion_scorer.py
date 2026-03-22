def calculate_scores(findings):
    """Calculate suspicion scores for phone numbers"""
    scores = []
    
    try:
        # Collect all unique phone numbers from findings
        all_numbers = set()
        
        # From frequent numbers
        if 'frequent' in findings:
            for col, counts in findings['frequent'].items():
                all_numbers.update(counts.keys())
        
        # From short calls
        if 'short_calls' in findings:
            for col, counts in findings['short_calls'].items():
                all_numbers.update(counts.keys())
        
        # From night calls
        if 'night_calls' in findings:
            for col, counts in findings['night_calls'].items():
                all_numbers.update(counts.keys())
        
        # From missed calls
        if 'missed_calls' in findings:
            for col, counts in findings['missed_calls'].items():
                all_numbers.update(counts.keys())
        
        # From sequential numbers
        sequential_numbers = set()
        if 'sequential' in findings:
            for group in findings['sequential']:
                sequential_numbers.update(group)
        all_numbers.update(sequential_numbers)
        
        # Score each number
        for number in all_numbers:
            score = 0
            reasons = []
            
            # +30 if appears in frequent (top callers)
            if 'frequent' in findings:
                for col, counts in findings['frequent'].items():
                    if number in counts and counts[number] > 5:  # Threshold for being "frequent"
                        score += 30
                        reasons.append(f"Frequent caller ({counts[number]} times)")
                        break
            
            # +20 if night calls > 5
            if 'night_calls' in findings:
                total_night_calls = 0
                for col, counts in findings['night_calls'].items():
                    if number in counts:
                        total_night_calls += counts[number]
                if total_night_calls > 5:
                    score += 20
                    reasons.append(f"Night calls ({total_night_calls} times)")
            
            # +20 if short calls > 10
            if 'short_calls' in findings:
                total_short_calls = 0
                for col, counts in findings['short_calls'].items():
                    if number in counts:
                        total_short_calls += counts[number]
                if total_short_calls > 10:
                    score += 20
                    reasons.append(f"Short calls ({total_short_calls} times)")
            
            # +15 if missed calls > 15
            if 'missed_calls' in findings:
                total_missed_calls = 0
                for col, counts in findings['missed_calls'].items():
                    if number in counts:
                        total_missed_calls += counts[number]
                if total_missed_calls > 15:
                    score += 15
                    reasons.append(f"Missed calls ({total_missed_calls} times)")
            
            # +20 if part of sequential series
            if number in sequential_numbers:
                score += 20
                reasons.append("Part of sequential number series")
            
            # Cap at 100
            score = min(score, 100)
            
            # Determine label
            if score <= 30:
                label = "Low"
                color = "green"
            elif score <= 60:
                label = "Medium"
                color = "orange"
            else:
                label = "HIGH RISK"
                color = "red"
            
            scores.append({
                'number': number,
                'score': score,
                'label': label,
                'color': color,
                'reasons': reasons
            })
        
        # Sort by score (highest first)
        scores.sort(key=lambda x: x['score'], reverse=True)
        
    except Exception as e:
        print(f"Error calculating scores: {e}")
        scores.append({
            'number': 'ERROR',
            'score': 0,
            'label': 'Error',
            'color': 'gray',
            'reasons': [str(e)]
        })
    
    return scores

def scores_to_text(scores):
    """Convert scores to readable text"""
    text_parts = []
    
    try:
        text_parts.append("SUSPICION SCORES REPORT")
        text_parts.append("=" * 50)
        
        if not scores:
            text_parts.append("No phone numbers found for scoring.")
            return "\n".join(text_parts)
        
        # Count by category
        high_risk = [s for s in scores if s['label'] == 'HIGH RISK']
        medium_risk = [s for s in scores if s['label'] == 'Medium']
        low_risk = [s for s in scores if s['label'] == 'Low']
        
        text_parts.append(f"\nSUMMARY:")
        text_parts.append(f"High Risk: {len(high_risk)} numbers")
        text_parts.append(f"Medium Risk: {len(medium_risk)} numbers")
        text_parts.append(f"Low Risk: {len(low_risk)} numbers")
        
        # Top 10 high risk numbers
        if high_risk:
            text_parts.append(f"\n\nHIGH RISK NUMBERS:")
            text_parts.append("-" * 30)
            for i, score_data in enumerate(high_risk[:10]):
                text_parts.append(f"\n{i+1}. {score_data['number']} - Score: {score_data['score']}")
                if score_data['reasons']:
                    text_parts.append(f"   Reasons: {', '.join(score_data['reasons'])}")
        
        # Top 5 medium risk numbers
        if medium_risk:
            text_parts.append(f"\n\nMEDIUM RISK NUMBERS:")
            text_parts.append("-" * 30)
            for i, score_data in enumerate(medium_risk[:5]):
                text_parts.append(f"\n{i+1}. {score_data['number']} - Score: {score_data['score']}")
                if score_data['reasons']:
                    text_parts.append(f"   Reasons: {', '.join(score_data['reasons'])}")
        
        # Sample low risk numbers
        if low_risk:
            text_parts.append(f"\n\nLOW RISK NUMBERS (Sample):")
            text_parts.append("-" * 30)
            for i, score_data in enumerate(low_risk[:3]):
                text_parts.append(f"\n{i+1}. {score_data['number']} - Score: {score_data['score']}")
        
    except Exception as e:
        text_parts.append(f"Error converting scores to text: {e}")
    
    return "\n".join(text_parts)