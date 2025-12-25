"""
utils.py Utility functions for salary data analysis and reporting.

Copyright (c) 2025 Mattias Nyqvist
Licensed under the MIT License - see LICENSE file for details
"""

import pandas as pd
import re
import io
from datetime import datetime

def parse_salary_query(query, df):
    """
    Parse natural language queries about salary data.
    Returns filtered dataframe and explanation.
    """
    query = query.lower().strip()
    
    # Pattern: "who earns most in/at [department]"
    if match := re.search(r'(?:vem tjänar mest|who earns most) (?:på|i|in|at) (\w+)', query):
        dept = match.group(1).capitalize()
        result = df[df['department'].str.lower() == dept.lower()]
        if not result.empty:
            top_earner = result.nlargest(1, 'salary').iloc[0]
            explanation = f"Highest salary in {dept}: {top_earner['name']} ({top_earner['role']}) - {top_earner['salary']:,.0f} kr"
            return result.nlargest(5, 'salary'), explanation
        return pd.DataFrame(), f"No department found: '{dept}'"
    
    # Pattern: "who earns most" (overall)
    if 'vem tjänar mest' in query or 'who earns most' in query:
        if 'på' not in query and 'i' not in query and 'in' not in query and 'at' not in query:
            top_earner = df.nlargest(1, 'salary').iloc[0]
            explanation = f"Highest salary: {top_earner['name']} ({top_earner['department']}, {top_earner['role']}) - {top_earner['salary']:,.0f} kr"
            return df.nlargest(5, 'salary'), explanation
    
    # Pattern: "all with salary over/under [amount]"
    if match := re.search(r'(?:lön över|salary over|över|over) (\d+)', query):
        amount = int(match.group(1))
        result = df[df['salary'] > amount]
        explanation = f"Found {len(result)} people with salary over {amount:,.0f} kr"
        return result, explanation
    
    if match := re.search(r'(?:lön under|salary under|under) (\d+)', query):
        amount = int(match.group(1))
        result = df[df['salary'] < amount]
        explanation = f"Found {len(result)} people with salary under {amount:,.0f} kr"
        return result, explanation
    
    # Pattern: "how many in/at [department]"
    if match := re.search(r'(?:hur många|how many) (?:på|i|in|at|work in|work at) (\w+)', query):
        dept = match.group(1).capitalize()
        result = df[df['department'].str.lower() == dept.lower()]
        explanation = f"{len(result)} people work in {dept}"
        return result, explanation
    
    # Pattern: "average [department]"
    if match := re.search(r'(?:genomsnitt|average)(?:slön)? (?:på|i|in|at|for)? ?(\w+)?', query):
        if match.group(1):
            dept = match.group(1).capitalize()
            result = df[df['department'].str.lower() == dept.lower()]
            if not result.empty:
                avg = result['salary'].mean()
                explanation = f"Average salary in {dept}: {avg:,.0f} kr"
                return result, explanation
        else:
            avg = df['salary'].mean()
            explanation = f"Total average salary: {avg:,.0f} kr"
            return df, explanation
    
    # Pattern: "show all [department]"
    if match := re.search(r'(?:visa alla|show all) (?:på|i|in|at|from)? ?(\w+)', query):
        dept = match.group(1).capitalize()
        result = df[df['department'].str.lower() == dept.lower()]
        explanation = f"Showing all ({len(result)}) from {dept}"
        return result, explanation
    
    # Default: no match
    return pd.DataFrame(), "Could not understand question. Try: 'Who earns most?', 'All with salary over 50000', 'How many in IT?'"


def calculate_stats(df):
    """Calculate comprehensive statistics from dataframe."""
    stats = {
        'total_employees': len(df),
        'avg_salary': df['salary'].mean(),
        'median_salary': df['salary'].median(),
        'min_salary': df['salary'].min(),
        'max_salary': df['salary'].max(),
        'total_cost': df['salary'].sum(),
        'departments': df['department'].nunique(),
    }
    return stats


def create_excel_report(df, stats):
    """
    Create comprehensive Excel report with multiple sheets.
    Returns BytesIO object for download.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        currency_format = workbook.add_format({
            'num_format': '#,##0 kr',
            'border': 1
        })
        
        number_format = workbook.add_format({
            'num_format': '#,##0',
            'border': 1
        })
        
        # Sheet 1: Summary Stats
        summary_df = pd.DataFrame({
            'Metric': [
                'Total Employees',
                'Average Salary',
                'Median Salary',
                'Min Salary',
                'Max Salary',
                'Total Monthly Cost',
                'Number of Departments'
            ],
            'Value': [
                stats['total_employees'],
                f"{stats['avg_salary']:,.0f} kr",
                f"{stats['median_salary']:,.0f} kr",
                f"{stats['min_salary']:,.0f} kr",
                f"{stats['max_salary']:,.0f} kr",
                f"{stats['total_cost']:,.0f} kr",
                stats['departments']
            ]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        worksheet = writer.sheets['Summary']
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 20)
        
        # Sheet 2: All Data
        df.to_excel(writer, sheet_name='All Data', index=False)
        
        worksheet = writer.sheets['All Data']
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        
        # Sheet 3: Department Stats
        dept_stats = df.groupby('department').agg({
            'salary': ['mean', 'median', 'min', 'max', 'count']
        }).round(0)
        dept_stats.columns = ['Average', 'Median', 'Min', 'Max', 'Count']
        dept_stats.to_excel(writer, sheet_name='By Department')
        
        # Sheet 4: Role Stats
        role_stats = df.groupby('role').agg({
            'salary': ['mean', 'count']
        }).round(0)
        role_stats.columns = ['Average Salary', 'Count']
        role_stats = role_stats.sort_values('Average Salary', ascending=False)
        role_stats.to_excel(writer, sheet_name='By Role')
        
        # Sheet 5: Outliers
        mean = df['salary'].mean()
        std = df['salary'].std()
        outliers = df[
            (df['salary'] > mean + 2*std) | 
            (df['salary'] < mean - 2*std)
        ]
        outliers.to_excel(writer, sheet_name='Outliers', index=False)
    
    output.seek(0)
    return output


def create_simple_excel(df):
    """Create simple Excel file from dataframe."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
        
        worksheet = writer.sheets['Data']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.set_column(idx, idx, max_length + 2)
    
    output.seek(0)
    return output


def load_benchmarks():
    """Load salary benchmark data."""
    try:
        benchmarks = pd.read_csv('data/salary_benchmarks.csv')
        return benchmarks
    except FileNotFoundError:
        return None


def calculate_benchmark_comparison(df, benchmarks):
    """
    Compare salaries against industry benchmarks.
    Returns dataframe with comparison metrics.
    """
    if benchmarks is None:
        return None
    
    comparison = df.merge(
        benchmarks[['role', 'industry_avg', 'industry_min', 'industry_max']],
        on='role',
        how='left'
    )
    
    comparison['diff_from_avg'] = comparison['salary'] - comparison['industry_avg']
    comparison['diff_pct'] = ((comparison['salary'] - comparison['industry_avg']) / comparison['industry_avg'] * 100).round(1)
    
    def categorize_salary(row):
        if pd.isna(row['industry_avg']):
            return 'No benchmark'
        elif row['salary'] < row['industry_min']:
            return 'Below market'
        elif row['salary'] > row['industry_max']:
            return 'Above market'
        elif row['salary'] < row['industry_avg']:
            return 'Below average'
        else:
            return 'Above average'
    
    comparison['market_position'] = comparison.apply(categorize_salary, axis=1)
    
    return comparison


def generate_benchmark_insights(comparison_df):
    """Generate insights from benchmark comparison."""
    insights = []
    
    if comparison_df is None or comparison_df.empty:
        return ["No benchmark data available"]
    
    below_market = len(comparison_df[comparison_df['market_position'] == 'Below market'])
    above_market = len(comparison_df[comparison_df['market_position'] == 'Above market'])
    
    if below_market > 0:
        insights.append(f"WARNING: {below_market} people below market level (turnover risk)")
    
    if above_market > 0:
        insights.append(f"INFO: {above_market} people above market level (higher cost)")
    
    avg_diff = comparison_df['diff_from_avg'].mean()
    if not pd.isna(avg_diff):
        if avg_diff > 0:
            insights.append(f"STAT: Company pays average {abs(avg_diff):,.0f} kr ABOVE market")
        else:
            insights.append(f"STAT: Company pays average {abs(avg_diff):,.0f} kr BELOW market")
    
    biggest_gaps = comparison_df.nlargest(3, 'diff_from_avg')[['name', 'role', 'diff_from_avg']]
    if not biggest_gaps.empty:
        insights.append("TOP: Biggest positive deviations:")
        for _, row in biggest_gaps.iterrows():
            insights.append(f"  - {row['name']} ({row['role']}): +{row['diff_from_avg']:,.0f} kr")
    
    return insights