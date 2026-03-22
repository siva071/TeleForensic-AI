def generate_report(patterns, scores, correlation, filename):
    import pandas as pd
    from datetime import datetime
    
    report_filename = f'TeleForensic_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    with pd.ExcelWriter(report_filename, engine='openpyxl') as writer:
        
        # Sheet 1: Suspicion Scores
        scores_df = pd.DataFrame(scores)
        scores_df.to_excel(
            writer, 
            sheet_name='Suspicion Scores',
            index=False)
        
        # Sheet 2: High Risk Numbers
        high_risk = scores_df[scores_df['label']=='HIGH RISK']
        high_risk.to_excel(
            writer,
            sheet_name='HIGH RISK Numbers',
            index=False)
        
        # Sheet 3: Pattern Summary
        summary_data = []
        if 'frequent' in patterns:
            for col, counts in patterns['frequent'].items():
                if counts:
                    top_number = list(counts.keys())[0]
                    top_count = list(counts.values())[0]
                    summary_data.append({
                        'Pattern': f'Most Frequent Caller ({col})',
                        'Number': top_number,
                        'Count': top_count
                    })
        
        if 'sequential' in patterns:
            for i, series in enumerate(patterns['sequential']):
                summary_data.append({
                    'Pattern': f'Sequential Series {i+1}',
                    'Number': ' → '.join(map(str, series)),
                    'Count': len(series)
                })
        
        if summary_data:
            pd.DataFrame(summary_data).to_excel(
                writer,
                sheet_name='Pattern Summary',
                index=False)
        
        # Sheet 4: Investigation Leads
        leads = []
        for score in scores[:5]:
            if score['score'] > 40:
                leads.append({
                    'Priority': 'HIGH' if score['score']>60 else 'MEDIUM',
                    'Number': score['number'],
                    'Score': score['score'],
                    'Action': 'Immediate investigation required' if score['score']>60 else 'Monitor activity'
                })
        
        if leads:
            pd.DataFrame(leads).to_excel(
                writer,
                sheet_name='Investigation Leads',
                index=False)
    
    return report_filename
