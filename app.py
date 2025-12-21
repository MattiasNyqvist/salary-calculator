import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
from recommendations import generate_ai_recommendations, get_priority_color

# Page config
st.set_page_config(
    page_title="Salary Analyzer Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

col1, col2 = st.columns([4, 1])

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
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                
                with st.expander("View generated code"):
                    st.code(generated_code, language='python')
                    
            except Exception as e:
                st.error(f"AI error: {str(e)}")
                st.info("Try Regex Mode for simpler questions, or rephrase your question.")
    else:
        result_df, explanation = parse_salary_query(query, filtered_df)
        
        st.info(f"**Answer:** {explanation}")
        
        if not result_df.empty:
            st.dataframe(result_df, use_container_width=True, hide_index=True)
    
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview", 
    "By Department", 
    "Analysis",
    "Benchmarking",
    "AI Recommendations",
    "Search Employees"
])

with tab1:
    st.header("Overview")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Employees", f"{len(filtered_df):,}")
    
    with col2:
        avg_salary = filtered_df['salary'].mean()
        st.metric("Average Salary", f"{avg_salary:,.0f} kr")
    
    with col3:
        median_salary = filtered_df['salary'].median()
        st.metric("Median Salary", f"{median_salary:,.0f} kr")
    
    with col4:
        total_cost = filtered_df['salary'].sum()
        st.metric("Total Monthly Cost", f"{total_cost:,.0f} kr")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Salary distribution
    st.subheader("Salary Distribution")
    fig = px.histogram(
        filtered_df, 
        x='salary',
        nbins=20,
        labels={'salary': 'Salary (kr)', 'count': 'Count'}
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Box plot by department
    st.subheader("Salary Range by Department")
    fig_box = px.box(
        filtered_df,
        x='department',
        y='salary',
        labels={'department': 'Department', 'salary': 'Salary (kr)'}
    )
    fig_box.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    st.header("Analysis by Department")
    
    dept_stats = filtered_df.groupby('department').agg({
        'salary': ['mean', 'median', 'min', 'max', 'count']
    }).round(0)
    
    dept_stats.columns = ['Average', 'Median', 'Min', 'Max', 'Count']
    st.dataframe(dept_stats, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bar chart
    avg_by_dept = filtered_df.groupby('department')['salary'].mean().reset_index()
    avg_by_dept = avg_by_dept.sort_values('salary', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=avg_by_dept['salary'],
        y=avg_by_dept['department'],
        orientation='h',
        text=avg_by_dept['salary'].apply(lambda x: f'{x:,.0f} kr'),
        textposition='outside'
    ))
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#e5e5e5', title='Average Salary (kr)'),
        yaxis=dict(showgrid=False, title='Department'),
        margin=dict(l=0, r=0, t=10, b=0),
        height=400
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
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("No outliers found")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Salary by role
    st.subheader("Salary by Role")
    role_stats = filtered_df.groupby('role')['salary'].agg(['mean', 'count']).round(0)
    role_stats.columns = ['Average', 'Count']
    role_stats = role_stats.sort_values('Average', ascending=False)
    st.dataframe(role_stats, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Salary percentiles
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Salary Percentiles")
        percentiles = filtered_df['salary'].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(0)
        perc_df = pd.DataFrame({
            'Percentile': ['10%', '25%', '50% (Median)', '75%', '90%'],
            'Salary (kr)': percentiles.values
        })
        st.dataframe(perc_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Department Distribution")
        dept_count = filtered_df.groupby('department').size().reset_index(name='Employees')
        dept_count = dept_count.sort_values('Employees', ascending=False)
        
        fig_pie = px.pie(
            dept_count,
            values='Employees',
            names='department'
        )
        fig_pie.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            showlegend=True
        )
        st.plotly_chart(fig_pie, use_container_width=True)

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
            
            def highlight_position(row):
                if row['Position'] == 'Below market':
                    return ['background-color: #fee2e2'] * len(row)
                elif row['Position'] == 'Above market':
                    return ['background-color: #d1fae5'] * len(row)
                elif row['Position'] == 'Below average':
                    return ['background-color: #fef3c7'] * len(row)
                elif row['Position'] == 'Above average':
                    return ['background-color: #dbeafe'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = display_df.style.apply(highlight_position, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Visualization
        st.subheader("Visualization")
        
        if benchmark_comparison is not None:
            # Scatter plot
            fig = px.scatter(
                benchmark_comparison,
                x='industry_avg',
                y='salary',
                color='market_position',
                hover_data=['name', 'role'],
                labels={
                    'industry_avg': 'Industry Average (kr)',
                    'salary': 'Actual Salary (kr)',
                    'market_position': 'Position'
                }
            )
            
            max_val = max(
                benchmark_comparison['salary'].max(),
                benchmark_comparison['industry_avg'].max()
            )
            fig.add_shape(
                type="line",
                x0=0, y0=0, x1=max_val, y1=max_val,
                line=dict(color="#94a3b8", dash="dash", width=2)
            )
            
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=0, r=0, t=10, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Bar chart
            dept_comparison = benchmark_comparison.groupby('department').agg({
                'salary': 'mean',
                'industry_avg': 'mean'
            }).round(0).reset_index()
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                name='Company',
                x=dept_comparison['department'],
                y=dept_comparison['salary'],
                text=dept_comparison['salary'].apply(lambda x: f'{x:,.0f}'),
                textposition='outside'
            ))
            
            fig2.add_trace(go.Bar(
                name='Industry Benchmark',
                x=dept_comparison['department'],
                y=dept_comparison['industry_avg'],
                text=dept_comparison['industry_avg'].apply(lambda x: f'{x:,.0f}'),
                textposition='outside'
            ))
            
            fig2.update_layout(
                barmode='group',
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(showgrid=False, title='Department'),
                yaxis=dict(showgrid=True, gridcolor='#e5e5e5', title='Average Salary (kr)'),
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig2, use_container_width=True)

with tab5:
    st.header("AI Recommendations")
    
    st.markdown("""
    AI-powered analysis of your salary data with actionable recommendations 
    to improve retention, manage costs, and ensure market competitiveness.
    """)
    
    if st.button("Generate AI Recommendations", type="primary"):
        with st.spinner("AI analyzing salary data..."):
            recommendations = generate_ai_recommendations(filtered_df, benchmark_comparison)
            
            if recommendations:
                st.success(f"Generated {len(recommendations)} recommendations")
                
                # Group by priority
                high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
                medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
                low_priority = [r for r in recommendations if r['priority'] == 'LOW']
                
                # Display HIGH priority first
                if high_priority:
                    st.subheader("High Priority")
                    for rec in high_priority:
                        color = get_priority_color(rec['priority'])
                        
                        st.markdown(f"""
                        <div style='background-color: #fee2e2; padding: 1rem; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 1rem;'>
                            <div style='margin-bottom: 0.5rem;'>
                                <span style='background-color: {color}; color: white; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; margin-right: 0.5rem;'>{rec['priority']}</span>
                                <span style='background-color: #f3f4f6; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 500; font-size: 0.75rem;'>{rec['category']}</span>
                            </div>
                            <p style='margin: 0; color: #1f2937; line-height: 1.6;'>{rec['recommendation']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display MEDIUM priority
                if medium_priority:
                    st.subheader("Medium Priority")
                    for rec in medium_priority:
                        color = get_priority_color(rec['priority'])
                        
                        st.markdown(f"""
                        <div style='background-color: #fef3c7; padding: 1rem; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 1rem;'>
                            <div style='margin-bottom: 0.5rem;'>
                                <span style='background-color: {color}; color: white; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; margin-right: 0.5rem;'>{rec['priority']}</span>
                                <span style='background-color: #f3f4f6; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 500; font-size: 0.75rem;'>{rec['category']}</span>
                            </div>
                            <p style='margin: 0; color: #1f2937; line-height: 1.6;'>{rec['recommendation']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display LOW priority
                if low_priority:
                    st.subheader("Low Priority")
                    for rec in low_priority:
                        color = get_priority_color(rec['priority'])
                        
                        st.markdown(f"""
                        <div style='background-color: #d1fae5; padding: 1rem; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 1rem;'>
                            <div style='margin-bottom: 0.5rem;'>
                                <span style='background-color: {color}; color: white; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; margin-right: 0.5rem;'>{rec['priority']}</span>
                                <span style='background-color: #f3f4f6; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 500; font-size: 0.75rem;'>{rec['category']}</span>
                            </div>
                            <p style='margin: 0; color: #1f2937; line-height: 1.6;'>{rec['recommendation']}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("Could not generate recommendations. Check API key configuration.")
    
    st.markdown("---")
    st.info("Tip: AI recommendations are generated based on current salary data and benchmark comparisons. Run this analysis monthly to track progress.")

with tab6:
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
            st.dataframe(results, use_container_width=True, hide_index=True)
        else:
            st.warning("No results found")
    else:
        st.info("Type to search")

# Footer
st.markdown("---")
st.markdown("**Salary Analyzer Pro** | AI-powered salary analysis platform")