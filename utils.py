import pandas as pd
import re

def parse_salary_query(query, df):
    """
    Parse natural language queries about salary data.
    Returns filtered dataframe and explanation.
    """
    query = query.lower().strip()
    
    # Pattern: "vem tjänar mest på/i [department]"
    if match := re.search(r'vem tjänar mest (?:på|i) (\w+)', query):
        dept = match.group(1).capitalize()
        result = df[df['department'].str.lower() == dept.lower()]
        if not result.empty:
            top_earner = result.nlargest(1, 'salary').iloc[0]
            explanation = f"Högst lön på {dept}: {top_earner['name']} ({top_earner['role']}) - {top_earner['salary']:,.0f} kr"
            return result.nlargest(5, 'salary'), explanation
        return pd.DataFrame(), f"Hittade ingen avdelning '{dept}'"
    
    # Pattern: "vem tjänar mest" (overall)
    if 'vem tjänar mest' in query and 'på' not in query and 'i' not in query:
        top_earner = df.nlargest(1, 'salary').iloc[0]
        explanation = f"Högst lön: {top_earner['name']} ({top_earner['department']}, {top_earner['role']}) - {top_earner['salary']:,.0f} kr"
        return df.nlargest(5, 'salary'), explanation
    
    # Pattern: "alla med lön över/under [amount]"
    if match := re.search(r'lön över (\d+)', query):
        amount = int(match.group(1))
        result = df[df['salary'] > amount]
        explanation = f"Hittade {len(result)} personer med lön över {amount:,.0f} kr"
        return result, explanation
    
    if match := re.search(r'lön under (\d+)', query):
        amount = int(match.group(1))
        result = df[df['salary'] < amount]
        explanation = f"Hittade {len(result)} personer med lön under {amount:,.0f} kr"
        return result, explanation
    
    # Pattern: "hur många på/i [department]"
    if match := re.search(r'hur många (?:på|i|jobbar på|jobbar i) (\w+)', query):
        dept = match.group(1).capitalize()
        result = df[df['department'].str.lower() == dept.lower()]
        explanation = f"{len(result)} personer jobbar på {dept}"
        return result, explanation
    
    # Pattern: "genomsnitt [department]"
    if match := re.search(r'genomsnitt(?:slön)? (?:på|i|för)? ?(\w+)?', query):
        if match.group(1):
            dept = match.group(1).capitalize()
            result = df[df['department'].str.lower() == dept.lower()]
            if not result.empty:
                avg = result['salary'].mean()
                explanation = f"Genomsnittslön på {dept}: {avg:,.0f} kr"
                return result, explanation
        else:
            avg = df['salary'].mean()
            explanation = f"Genomsnittslön totalt: {avg:,.0f} kr"
            return df, explanation
    
    # Pattern: "visa alla [department]"
    if match := re.search(r'visa alla (?:på|i|från)? ?(\w+)', query):
        dept = match.group(1).capitalize()
        result = df[df['department'].str.lower() == dept.lower()]
        explanation = f"Visar alla ({len(result)}) från {dept}"
        return result, explanation
    
    # Default: no match
    return pd.DataFrame(), "Förstod inte frågan. Prova: 'Vem tjänar mest?', 'Alla med lön över 50000', 'Hur många på IT?'"


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