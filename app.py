import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils import parse_salary_query, calculate_stats, create_excel_report, create_simple_excel
from ai_query import query_with_ai

# Page config
st.set_page_config(
    page_title="Salary Analyzer Pro",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("💰 Salary Analyzer Pro")
st.markdown("Analysera lönedata med AI-powered natural language queries")

# Sidebar - Data Source
st.sidebar.header("📂 Datakälla")

data_source = st.sidebar.radio(
    "Välj datakälla:",
    ["Sample data", "Ladda upp egen fil"]
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
        
        # Try to parse employment_date if it exists
        if 'employment_date' in df.columns:
            df['employment_date'] = pd.to_datetime(df['employment_date'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Fel vid inläsning: {e}")
        return None

# Get data based on source
if data_source == "Sample data":
    df = load_sample_data()
    st.sidebar.success("✅ Sample data laddad")
else:
    uploaded_file = st.sidebar.file_uploader(
        "Ladda upp CSV eller Excel",
        type=['csv', 'xlsx', 'xls'],
        help="Filen måste innehålla kolumner: name, department, role, salary"
    )
    
    if uploaded_file:
        df = load_uploaded_data(uploaded_file)
        if df is not None:
            st.sidebar.success(f"✅ {uploaded_file.name} laddad")
            
            # Show required columns
            required_cols = ['name', 'department', 'role', 'salary']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.sidebar.error(f"⚠️ Saknade kolumner: {', '.join(missing_cols)}")
                st.stop()
        else:
            st.info("👈 Ladda upp en fil för att börja")
            st.stop()
    else:
        st.info("👈 Ladda upp en fil för att börja")
        st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filters")
departments = st.sidebar.multiselect(
    "Välj avdelningar:",
    options=sorted(df['department'].unique()),
    default=df['department'].unique()
)

salary_range = st.sidebar.slider(
    "Löneintervall (kr):",
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

# Export section
st.sidebar.markdown("---")
st.sidebar.header("📥 Export")

stats = calculate_stats(filtered_df)

col1, col2 = st.sidebar.columns(2)

with col1:
    # Simple export
    simple_excel = create_simple_excel(filtered_df)
    st.download_button(
        label="📊 Data",
        data=simple_excel,
        file_name=f"salary_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col2:
    # Full report
    report_excel = create_excel_report(filtered_df, stats)
    st.download_button(
        label="📈 Rapport",
        data=report_excel,
        file_name=f"salary_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# Natural Language Query (TOP OF PAGE)
st.header("🤖 Fråga om löner")

# AI Mode Toggle
query_mode = st.radio(
    "Query Mode:",
    ["🧠 AI Mode (Smart)", "⚡ Regex Mode (Snabb)"],
    horizontal=True,
    help="AI Mode: Förstår komplexa frågor med Claude AI | Regex Mode: Snabbare men enklare pattern matching"
)

col1, col2 = st.columns([3, 1])

with col1:
    if query_mode == "🧠 AI Mode (Smart)":
        query = st.text_input(
            "Ställ en fråga:",
            placeholder="T.ex: 'Vilka på IT tjänar mer än genomsnittet?', 'Vem har jobbat längst?', 'Topp 3 avdelningar efter kostnad'",
            label_visibility="collapsed",
            key="ai_query"
        )
    else:
        query = st.text_input(
            "Ställ en fråga:",
            placeholder="T.ex: 'Vem tjänar mest på IT?', 'Alla med lön över 50000', 'Hur många på Finance?'",
            label_visibility="collapsed",
            key="regex_query"
        )

with col2:
    search_button = st.button("🔍 Sök", use_container_width=True)

if query and search_button:
    if query_mode == "🧠 AI Mode (Smart)":
        # AI-powered query
        with st.spinner("AI tänker..."):
            try:
                result_df, explanation, generated_code = query_with_ai(query, filtered_df)
                
                st.success(f"**AI Svar:** {explanation}")
                
                if not result_df.empty:
                    st.dataframe(result_df, use_container_width=True)
                
                # Show generated code in expander
                with st.expander("🔍 Visa genererad kod"):
                    st.code(generated_code, language='python')
                    
            except Exception as e:
                st.error(f"AI-fel: {str(e)}")
                st.info("💡 Prova Regex Mode för enklare frågor, eller omformulera frågan.")
    else:
        # Regex-based query (original)
        result_df, explanation = parse_salary_query(query, filtered_df)
        
        st.info(f"**Svar:** {explanation}")
        
        if not result_df.empty:
            st.dataframe(result_df, use_container_width=True)
    
    st.markdown("---")

# Example queries
with st.expander("💡 Exempel på frågor du kan ställa"):
    if query_mode == "🧠 AI Mode (Smart)":
        st.markdown("""
        **AI Mode kan svara på komplexa frågor:**
        - **Vilka på IT tjänar mer än genomsnittet i Finance?**
        - **Vem har jobbat längst och hur mycket tjänar hen?**
        - **Visa topp 3 avdelningar efter total lönekostnad**
        - **Hur många procent av HR tjänar över 45000?**
        - **Vilka roller har högst medianlön?**
        - **Jämför min lön (50000) med genomsnittet per avdelning**
        """)
    else:
        st.markdown("""
        **Regex Mode - enkla, snabba frågor:**
        - **Vem tjänar mest?**
        - **Vem tjänar mest på IT?**
        - **Alla med lön över 50000**
        - **Alla med lön under 40000**
        - **Hur många på Finance?**
        - **Genomsnittslön IT**
        - **Visa alla på HR**
        """)

# Main content - Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", 
    "💼 Per Avdelning", 
    "📈 Analys", 
    "🔍 Sök Anställda"
])

with tab1:
    st.header("Översikt")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Totalt Anställda", len(filtered_df))
    
    with col2:
        avg_salary = filtered_df['salary'].mean()
        st.metric("Genomsnittslön", f"{avg_salary:,.0f} kr")
    
    with col3:
        median_salary = filtered_df['salary'].median()
        st.metric("Medianlön", f"{median_salary:,.0f} kr")
    
    with col4:
        total_cost = filtered_df['salary'].sum()
        st.metric("Total Lönekostnad/mån", f"{total_cost:,.0f} kr")
    
    # Salary distribution
    st.subheader("Lönefördelning")
    fig = px.histogram(
        filtered_df, 
        x='salary',
        nbins=20,
        title="Distribution av löner",
        labels={'salary': 'Lön (kr)', 'count': 'Antal'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Box plot by department
    st.subheader("Lönespridning per Avdelning")
    fig_box = px.box(
        filtered_df,
        x='department',
        y='salary',
        title="Box plot av löner per avdelning",
        labels={'department': 'Avdelning', 'salary': 'Lön (kr)'}
    )
    st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    st.header("Analys per Avdelning")
    
    dept_stats = filtered_df.groupby('department').agg({
        'salary': ['mean', 'median', 'min', 'max', 'count']
    }).round(0)
    
    dept_stats.columns = ['Genomsnitt', 'Median', 'Min', 'Max', 'Antal']
    st.dataframe(dept_stats, use_container_width=True)
    
    # Bar chart
    avg_by_dept = filtered_df.groupby('department')['salary'].mean().reset_index()
    fig = px.bar(
        avg_by_dept,
        x='department',
        y='salary',
        title="Genomsnittslön per Avdelning",
        labels={'department': 'Avdelning', 'salary': 'Genomsnittslön (kr)'}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Löneanalys & Insights")
    
    # Find outliers (simple method)
    mean = filtered_df['salary'].mean()
    std = filtered_df['salary'].std()
    outliers = filtered_df[
        (filtered_df['salary'] > mean + 2*std) | 
        (filtered_df['salary'] < mean - 2*std)
    ]
    
    if len(outliers) > 0:
        st.subheader("⚠️ Löner utanför normalintervallet (±2 std)")
        st.dataframe(
            outliers[['name', 'department', 'role', 'salary']],
            use_container_width=True
        )
    else:
        st.success("✅ Inga outliers hittade")
    
    # Salary by role
    st.subheader("Lön per Roll")
    role_stats = filtered_df.groupby('role')['salary'].agg(['mean', 'count']).round(0)
    role_stats.columns = ['Genomsnitt', 'Antal']
    role_stats = role_stats.sort_values('Genomsnitt', ascending=False)
    st.dataframe(role_stats, use_container_width=True)
    
    # Salary percentiles
    st.subheader("Lönepercentiler")
    percentiles = filtered_df['salary'].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(0)
    perc_df = pd.DataFrame({
        'Percentil': ['10%', '25%', '50% (Median)', '75%', '90%'],
        'Lön (kr)': percentiles.values
    })
    st.dataframe(perc_df, use_container_width=True)

with tab4:
    st.header("Sök Anställda")
    
    search = st.text_input("Sök på namn, avdelning eller roll:")
    
    if search:
        mask = (
            filtered_df['name'].str.contains(search, case=False) |
            filtered_df['department'].str.contains(search, case=False) |
            filtered_df['role'].str.contains(search, case=False)
        )
        results = filtered_df[mask]
        
        if len(results) > 0:
            st.success(f"Hittade {len(results)} resultat")
            st.dataframe(results, use_container_width=True)
        else:
            st.warning("Inga resultat hittade")
    else:
        st.info("Skriv något för att söka")

# Footer
st.markdown("---")
st.markdown("""
**💡 Tips:** 
- **AI Mode**: Ställ komplexa frågor - AI förstår och genererar kod
- **Regex Mode**: Snabbare för enkla, vanliga frågor
- Filtrera data med sidomenyn
- Exportera till Excel för vidare analys
""")