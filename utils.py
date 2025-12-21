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


def create_excel_report(df, stats):
    """
    Create comprehensive Excel report with multiple sheets.
    Returns BytesIO object for download.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Get workbook and add formats
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
        
        # Format summary sheet
        worksheet = writer.sheets['Summary']
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 20)
        
        # Sheet 2: All Data
        df.to_excel(writer, sheet_name='All Data', index=False)
        
        # Format all data sheet
        worksheet = writer.sheets['All Data']
        worksheet.set_column('A:A', 20)  # Name
        worksheet.set_column('B:B', 15)  # Department
        worksheet.set_column('C:C', 20)  # Role
        worksheet.set_column('D:D', 15)  # Salary
        
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
        
        # Auto-adjust columns
        worksheet = writer.sheets['Data']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.set_column(idx, idx, max_length + 2)
    
    output.seek(0)
    return output