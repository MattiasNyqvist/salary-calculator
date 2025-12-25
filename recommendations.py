"""
recommendations.py Recommendation engine using Claude AI for salary data analysis.

Copyright (c) 2025 Mattias Nyqvist
Licensed under the MIT License - see LICENSE file for details
"""


import anthropic
import os
import streamlit as st
from datetime import datetime
import pandas as pd

def generate_ai_recommendations(df, benchmark_comparison=None):
    """
    Use Claude AI to analyze salary data and generate actionable recommendations.
    Returns list of recommendation dictionaries with priority, category, and action.
    """
    
    # Initialize Claude client
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    except:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        return []
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Prepare data summary for AI
    data_summary = generate_data_summary(df, benchmark_comparison)
    
    # Create prompt
    prompt = f"""You are an HR analytics expert. Analyze this salary data and provide 5-7 concrete, actionable recommendations.

DATA SUMMARY:
{data_summary}

Provide recommendations in this EXACT format (one per line):
PRIORITY|CATEGORY|RECOMMENDATION

Where:
- PRIORITY: HIGH, MEDIUM, or LOW
- CATEGORY: RETENTION, COST, EQUITY, COMPLIANCE, or MARKET
- RECOMMENDATION: One clear, specific action (max 100 words)

Example:
HIGH|RETENTION|IT department salaries are 12% below market average. Recommend immediate 8-10% salary adjustment for developers to prevent turnover.

Provide 5-7 recommendations now:"""

    try:
        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        response_text = message.content[0].text.strip()
        recommendations = parse_recommendations(response_text)
        
        return recommendations
        
    except Exception as e:
        print(f"AI recommendation error: {e}")
        return []


def generate_data_summary(df, benchmark_comparison=None):
    """Generate concise data summary for AI analysis."""
    
    summary = f"""
OVERALL METRICS:
- Total Employees: {len(df)}
- Average Salary: {df['salary'].mean():,.0f} kr
- Median Salary: {df['salary'].median():,.0f} kr
- Salary Range: {df['salary'].min():,.0f} - {df['salary'].max():,.0f} kr
- Total Monthly Cost: {df['salary'].sum():,.0f} kr

DEPARTMENT BREAKDOWN:
"""
    
    dept_stats = df.groupby('department').agg({
        'salary': ['mean', 'count']
    }).round(0)
    
    for dept in dept_stats.index:
        avg = dept_stats.loc[dept, ('salary', 'mean')]
        count = dept_stats.loc[dept, ('salary', 'count')]
        summary += f"- {dept}: {count} employees, avg {avg:,.0f} kr\n"
    
    # Add benchmark info if available
    if benchmark_comparison is not None:
        summary += "\nBENCHMARK COMPARISON:\n"
        
        below_market = len(benchmark_comparison[benchmark_comparison['market_position'] == 'Below market'])
        above_market = len(benchmark_comparison[benchmark_comparison['market_position'] == 'Above market'])
        
        if below_market > 0:
            summary += f"- {below_market} employees below market rate\n"
        if above_market > 0:
            summary += f"- {above_market} employees above market rate\n"
        
        avg_diff = benchmark_comparison['diff_from_avg'].mean()
        if not pd.isna(avg_diff):
            if avg_diff > 0:
                summary += f"- Company pays average {abs(avg_diff):,.0f} kr ABOVE market\n"
            else:
                summary += f"- Company pays average {abs(avg_diff):,.0f} kr BELOW market\n"
    
    # Add outlier info
    mean = df['salary'].mean()
    std = df['salary'].std()
    outliers = df[
        (df['salary'] > mean + 2*std) | 
        (df['salary'] < mean - 2*std)
    ]
    
    if len(outliers) > 0:
        summary += f"\nOUTLIERS:\n- {len(outliers)} salaries outside normal range (±2 std)\n"
    
    return summary


def parse_recommendations(response_text):
    """Parse AI response into structured recommendations."""
    
    recommendations = []
    lines = response_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or '|' not in line:
            continue
        
        parts = line.split('|')
        if len(parts) >= 3:
            priority = parts[0].strip().upper()
            category = parts[1].strip().upper()
            recommendation = '|'.join(parts[2:]).strip()
            
            # Validate priority
            if priority not in ['HIGH', 'MEDIUM', 'LOW']:
                priority = 'MEDIUM'
            
            # Validate category
            if category not in ['RETENTION', 'COST', 'EQUITY', 'COMPLIANCE', 'MARKET']:
                category = 'GENERAL'
            
            recommendations.append({
                'priority': priority,
                'category': category,
                'recommendation': recommendation
            })
    
    return recommendations


def get_priority_color(priority):
    """Get color for priority badge."""
    colors = {
        'HIGH': '#dc2626',
        'MEDIUM': '#f59e0b',
        'LOW': '#059669'
    }
    return colors.get(priority, '#6b7280')