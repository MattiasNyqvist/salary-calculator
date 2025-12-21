import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils import (
    parse_salary_query, 
    calculate_stats, 
    create_excel_report, 
    create_simple_excel,
    load_benchmarks,
    calculate_benchmark_comparison,
    generate_benchmark_insights
)
from ai_query import query_with_ai

# Page config
st.set_page_config(
    page_title="Salary Analyzer Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4472C4;
        color: white;
    }
    h1 {
        color: #1e3a8a;
        font-weight: 700;
    }
    h2 {
        color: #2563eb;
        font-weight: 600;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 8px;
    }
    h3 {
        color: #3b82f6;
        font-weight: 600;
    }
    .stMetric {
        background-color: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stDataFrame {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("Salary Analyzer Pro")
st.markdown("AI-powered salary analysis and benchmarking platform")

# Sidebar - Data Source
st.sidebar.header("Data Source")

data_source = st.sidebar.radio(
    "Choose data source:",
    ["Sample data", "Upload file"]
)

# Load data
@st.cache_data
def load_sample_data():
    df = pd.read_csv('data/sample_salaries.csv')
    df['employment_date'] = pd.to_datetime(df['employment_date'])
    return df

@st.cache_data
def load_uploaded_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return None
        
        if 'employment_date' in df.columns:
            df['employment_date'] = pd.to_datetime(df['employment_date'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# Get data based on source
if data_source == "Sample data":
    df = load_sample_data()
    st.sidebar.success("Sample data loaded")
else:
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV or Excel",
        type=['csv', 'xlsx', 'xls'],
        help="File must contain columns: name, department, role, salary"
    )
    
    if uploaded_file:
        df = load_uploaded_data(uploaded_file)
        if df is not None:
            st.sidebar.success(f"{uploaded_file.name} loaded")
            
            required_cols = ['name', 'department', 'role', 'salary']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.sidebar.error(f"Missing columns: {', '.join(missing_cols)}")
                st.stop()
        else:
            st.info("Upload a file to begin")
            st.stop()
    else:
        st.info("Upload a file to begin")
        st.stop()

# Sidebar filters
st.sidebar.header("Filters")
departments = st.sidebar.multiselect(
    "Select departments:",
    options=sorted(df['department'].unique()),
    default=df['department'].unique()
)

salary_range = st.sidebar.slider(
    "Salary range (kr):",
    min_value=int(df['salary'].min()),
    max_value=int(df['salary'].max()),
    value=(int(df['salary'].min()), int(df['salary'].max()))
)

# Filter data
filtered_df = df[
    (df['department'].isin(departments)) &
    (df['salary'] >= salary_range[0]) &
    (df['salary'] <= salary_range[1])
]

# Load benchmarks
benchmarks = load_benchmarks()
benchmark_comparison = None
if benchmarks is not None:
    benchmark_comparison = calculate_benchmark_comparison(filtered_df, benchmarks)

# Export section
st.sidebar.markdown("---")
st.sidebar.header("Export")

stats = calculate_stats(filtered_df)

col1, col2 = st.sidebar.columns(2)

with col1:
    simple_excel = create_simple_excel(filtered_df)
    st.download_button(
        label="Data",
        data=simple_excel,
        file_name=f"salary_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col2:
    report_excel = create_excel_report(filtered_df, stats)
    st.download_button(
        label="Report",
        data=report_excel,
        file_name=f"salary_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# Natural Language Query
st.header("Ask Questions")

query_mode = st.radio(
    "Query Mode:",
    ["AI Mode (Smart)", "Regex Mode (Fast)"],
    horizontal=True,
    help="AI Mode: Understands complex questions | Regex Mode: Faster but simpler pattern matching"
)

col1, col2 = st.columns([3, 1])

with col1:
    if query_mode == "AI Mode (Smart)":
        query = st.text_input(
            "Ask a question:",
            placeholder="e.g., 'Who in IT earns more than average?', 'Who worked longest?', 'Top 3 departments by cost'",
            label_visibility="collapsed",
            key="ai_query"
        )
    else:
        query = st.text_input(
            "Ask a question:",
            placeholder="e.g., 'Who earns most in IT?', 'All with salary over 50000', 'How many in Finance?'",
            label_visibility="collapsed",
            key="regex_query"
        )

with col2:
    search_button = st.button("Search", use_container_width=True, type="primary")

if query and search_button:
    if query_mode == "AI Mode (Smart)":
        with st.spinner("AI processing..."):
            try:
                result_df, explanation, generated_code = query_with_ai(query, filtered_df)
                
                st.success(f"**AI Answer:** {explanation}")
                
                if not result_df.empty:
                    st.dataframe(result_df, use_container_width=True)
                
                with st.expander("View generated code"):
                    st.code(generated_code, language='python')
                    
            except Exception as e:
                st.error(f"AI error: {str(e)}")
                st.info("Try Regex Mode for simpler questions, or rephrase your question.")
    else:
        result_df, explanation = parse_salary_query(query, filtered_df)
        
        st.info(f"**Answer:** {explanation}")
        
        if not result_df.empty:
            st.dataframe(result_df, use_container_width=True)
    
    st.markdown("---")

# Example queries
with st.expander("Example questions"):
    if query_mode == "AI Mode (Smart)":
        st.markdown("""
        **AI Mode can answer complex questions:**
        - Who in IT earns more than the Finance average?
        - Who has worked longest and how much do they earn?
        - Show top 3 departments by total salary cost
        - What percentage of HR earns over 45000?
        - Which roles have the highest median salary?
        - Compare my salary (50000) with department averages
        """)
    else:
        st.markdown("""
        **Regex Mode - simple, fast questions:**
        - Who earns most?
        - Who earns most in IT?
        - All with salary over 50000
        - All with salary under 40000
        - How many in Finance?
        - Average salary IT
        - Show all in HR
        """)

# Main content - Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", 
    "By Department", 
    "Analysis",
    "Benchmarking",
    "Search Employees"
])

with tab1:
    st.header("Overview")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Employees", len(filtered_df))
    
    with col2:
        avg_salary = filtered_df['salary'].mean()
        st.metric("Average Salary", f"{avg_salary:,.0f} kr")
    
    with col3:
        median_salary = filtered_df['salary'].median()
        st.metric("Median Salary", f"{median_salary:,.0f} kr")
    
    with col4:
        total_cost = filtered_df['salary'].sum()
        st.metric("Total Monthly Cost", f"{total_cost:,.0f} kr")
    
    # Salary distribution
    st.subheader("Salary Distribution")
    fig = px.histogram(
        filtered_df, 
        x='salary',
        nbins=20,
        title="Distribution of Salaries",
        labels={'salary': 'Salary (kr)', 'count': 'Count'},
        color_discrete_sequence=['#4472C4']
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Box plot by department
    st.subheader("Salary Range by Department")
    fig_box = px.box(
        filtered_df,
        x='department',
        y='salary',
        title="Box Plot of Salaries by Department",
        labels={'department': 'Department', 'salary': 'Salary (kr)'},
        color='department'
    )
    fig_box.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    st.header("Analysis by Department")
    
    dept_stats = filtered_df.groupby('department').agg({
        'salary': ['mean', 'median', 'min', 'max', 'count']
    }).round(0)
    
    dept_stats.columns = ['Average', 'Median', 'Min', 'Max', 'Count']
    st.dataframe(dept_stats, use_container_width=True)
    
    # Bar chart
    avg_by_dept = filtered_df.groupby('department')['salary'].mean().reset_index()
    fig = px.bar(
        avg_by_dept,
        x='department',
        y='salary',
        title="Average Salary by Department",
        labels={'department': 'Department', 'salary': 'Average Salary (kr)'},
        color='salary',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Salary Analysis & Insights")
    
    # Find outliers
    mean = filtered_df['salary'].mean()
    std = filtered_df['salary'].std()
    outliers = filtered_df[
        (filtered_df['salary'] > mean + 2*std) | 
        (filtered_df['salary'] < mean - 2*std)
    ]
    
    if len(outliers) > 0:
        st.subheader("Salaries Outside Normal Range (±2 std)")
        st.dataframe(
            outliers[['name', 'department', 'role', 'salary']],
            use_container_width=True
        )
    else:
        st.success("No outliers found")
    
    # Salary by role
    st.subheader("Salary by Role")
    role_stats = filtered_df.groupby('role')['salary'].agg(['mean', 'count']).round(0)
    role_stats.columns = ['Average', 'Count']
    role_stats = role_stats.sort_values('Average', ascending=False)
    st.dataframe(role_stats, use_container_width=True)
    
    # Salary percentiles
    st.subheader("Salary Percentiles")
    percentiles = filtered_df['salary'].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(0)
    perc_df = pd.DataFrame({
        'Percentile': ['10%', '25%', '50% (Median)', '75%', '90%'],
        'Salary (kr)': percentiles.values
    })
    st.dataframe(perc_df, use_container_width=True)

with tab4:
    st.header("Salary Benchmarking")
    
    if benchmarks is None:
        st.warning("No benchmark data available")
        st.info("Add data/salary_benchmarks.csv to enable benchmarking")
    else:
        # Show insights
        st.subheader("Insights")
        insights = generate_benchmark_insights(benchmark_comparison)
        for insight in insights:
            if insight.startswith("WARNING"):
                st.warning(insight)
            elif insight.startswith("INFO"):
                st.info(insight)
            elif insight.startswith("STAT"):
                st.info(insight)
            elif insight.startswith("TOP"):
                st.success(insight)
            else:
                st.markdown(insight)
        
        st.markdown("---")
        
        # Comparison table
        st.subheader("Detailed Comparison")
        
        if benchmark_comparison is not None:
            display_cols = [
                'name', 'role', 'salary', 'industry_avg', 
                'diff_from_avg', 'diff_pct', 'market_position'
            ]
            
            display_df = benchmark_comparison[display_cols].copy()
            display_df.columns = [
                'Name', 'Role', 'Salary', 'Industry Avg', 
                'Diff (kr)', 'Diff (%)', 'Position'
            ]
            
            # Color code based on position
            def highlight_position(row):
                if row['Position'] == 'Below market':
                    return ['background-color: #fee2e2'] * len(row)
                elif row['Position'] == 'Above market':
                    return ['background-color: #dcfce7'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = display_df.style.apply(highlight_position, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        
        st.markdown("---")
        
        # Visualization
        st.subheader("Visualization")
        
        if benchmark_comparison is not None:
            # Scatter plot: Actual vs Benchmark
            fig = px.scatter(
                benchmark_comparison,
                x='industry_avg',
                y='salary',
                color='market_position',
                hover_data=['name', 'role'],
                title="Salary vs Industry Benchmark",
                labels={
                    'industry_avg': 'Industry Average (kr)',
                    'salary': 'Actual Salary (kr)',
                    'market_position': 'Position'
                },
                color_discrete_map={
                    'Below market': '#ef4444',
                    'Below average': '#f97316',
                    'Above average': '#3b82f6',
                    'Above market': '#22c55e',
                    'No benchmark': '#9ca3af'
                }
            )
            
            # Add diagonal line
            max_val = max(
                benchmark_comparison['salary'].max(),
                benchmark_comparison['industry_avg'].max()
            )
            fig.add_shape(
                type="line",
                x0=0, y0=0, x1=max_val, y1=max_val,
                line=dict(color="gray", dash="dash", width=2)
            )
            
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Bar chart: Department average vs benchmark
            dept_comparison = benchmark_comparison.groupby('department').agg({
                'salary': 'mean',
                'industry_avg': 'mean'
            }).round(0).reset_index()
            
            dept_comparison_melted = dept_comparison.melt(
                id_vars='department',
                value_vars=['salary', 'industry_avg'],
                var_name='type',
                value_name='amount'
            )
            
            fig2 = px.bar(
                dept_comparison_melted,
                x='department',
                y='amount',
                color='type',
                barmode='group',
                title="Average Salary by Department vs Industry",
                labels={
                    'department': 'Department',
                    'amount': 'Salary (kr)',
                    'type': 'Type'
                },
                color_discrete_map={
                    'salary': '#4472C4',
                    'industry_avg': '#ED7D31'
                }
            )
            
            fig2.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif"),
                legend=dict(
                    title="",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Rename legend
            fig2.for_each_trace(lambda t: t.update(
                name='Company' if t.name == 'salary' else 'Industry Benchmark'
            ))
            
            st.plotly_chart(fig2, use_container_width=True)

with tab5:
    st.header("Search Employees")
    
    search = st.text_input("Search by name, department or role:")
    
    if search:
        mask = (
            filtered_df['name'].str.contains(search, case=False) |
            filtered_df['department'].str.contains(search, case=False) |
            filtered_df['role'].str.contains(search, case=False)
        )
        results = filtered_df[mask]
        
        if len(results) > 0:
            st.success(f"Found {len(results)} results")
            st.dataframe(results, use_container_width=True)
        else:
            st.warning("No results found")
    else:
        st.info("Type to search")

# Footer
st.markdown("---")
st.markdown("""
**Tips:** 
- **AI Mode**: Ask complex questions - AI understands and generates code
- **Regex Mode**: Faster for simple, common questions
- **Benchmarking**: Compare salaries against industry standards
- Filter data using the sidebar
- Export to Excel for further analysis
""")