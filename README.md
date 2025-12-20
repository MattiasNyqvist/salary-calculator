# 💰 Salary Analyzer

AI-powered salary analysis tool with natural language queries and interactive visualizations.

![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.29+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 Features

- **Natural Language Queries**: Ask questions in plain Swedish
  - "Vem tjänar mest på IT?"
  - "Alla med lön över 50000"
  - "Hur många jobbar på Finance?"

- **File Upload**: Analyze your own salary data (CSV/Excel)

- **Interactive Dashboards**: 
  - Salary distribution charts
  - Department comparisons
  - Outlier detection
  - Statistical insights

- **Smart Filtering**: Filter by department, salary range

## 🚀 Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/DITT-USERNAME/salary-calculator.git
cd salary-calculator

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
```

### Usage

1. Choose data source (sample or upload your own)
2. Ask questions using natural language
3. Explore interactive dashboards
4. Filter and analyze

## 📊 Sample Data Format

Your CSV/Excel should have these columns:
```csv
name,department,role,salary,employment_date
Anna Andersson,HR,HR Manager,52000,2020-03-15
Erik Nilsson,Finance,Controller,58000,2019-06-01
```

## 🛠️ Tech Stack

- **Python 3.13+**
- **Streamlit** - Web UI
- **Pandas** - Data analysis
- **Plotly** - Interactive charts
- **Regex** - Natural language parsing

## 📈 Roadmap

- [ ] Add AI-powered query understanding (Claude/GPT)
- [ ] Export reports to PDF
- [ ] Historical trend analysis
- [ ] Salary benchmarking
- [ ] Multi-language support

## 🤝 Use Cases

Perfect for:
- HR departments analyzing compensation
- Managers reviewing team salaries
- Finance teams tracking costs
- Consultants demonstrating AI capabilities

## 📝 License

MIT License - feel free to use for your projects!

## 👤 Author

Built as part of AI transformation consulting portfolio.

**Contact:** [Your LinkedIn]

---

**⭐ If you find this useful, please star the repo!**