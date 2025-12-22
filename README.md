# Salary Analyzer Pro

AI-powered salary analysis and benchmarking platform that transforms HR compensation data into actionable insights.

![Overview](overview.png)

## Features

### Natural Language Queries
Ask questions in plain English and get instant answers:
- "Who in IT earns more than the Finance average?"
- "Show top 3 departments by total cost"
- "Which roles have the highest median salary?"

Powered by Claude AI with fallback to regex-based pattern matching for fast, simple queries.

![AI Query](ai_query.png)

### Salary Benchmarking
Compare your company's salaries against industry standards:
- Identify employees below/above market rate
- Department-level comparisons
- Visual scatter plots and bar charts
- Automatic market position categorization

![Benchmarking](benchmarking.png)

### AI-Powered Recommendations
Generate concrete, actionable recommendations with one click:
- **Retention risks**: Employees at risk of leaving due to below-market pay
- **Cost optimization**: Departments with above-market compensation
- **Equity analysis**: Pay gaps and fairness issues
- **Compliance**: Salary practice improvements
- **Market positioning**: Strategic salary adjustments

Recommendations are prioritized (HIGH/MEDIUM/LOW) and categorized by type.

![AI Recommendations](ai_recommendations.png)

### Data Analysis & Visualization
- Interactive dashboards with salary distributions
- Department breakdowns and comparisons
- Outlier detection (±2 standard deviations)
- Salary percentiles and role-based analysis
- Export to Excel (simple data or full reports)

## Tech Stack

- **Python 3.11+**
- **Streamlit** - Web application framework
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive visualizations
- **Claude AI (Anthropic)** - Natural language processing and recommendations
- **OpenPyXL/XlsxWriter** - Excel report generation

## Installation

### Prerequisites
- Python 3.11 or higher
- Anthropic API key (for AI features)

### Setup

1. **Clone the repository:**
```bash