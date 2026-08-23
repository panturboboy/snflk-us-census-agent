# Streamlit Chat App Setup

## Prerequisites

- Python 3.9+
- Snowflake account with Cortex access
- Deployed semantic view `CENSUS_DEMOGRAPHICS_MODEL` in your Snowflake database

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Snowflake credentials
   ```

   Required variables:
   - `SNOWFLAKE_ACCOUNT`: Your Snowflake account identifier
   - `SNOWFLAKE_USER`: Username
   - `SNOWFLAKE_PASSWORD`: Password
   - `SNOWFLAKE_DATABASE`: Database name
   - `SNOWFLAKE_SCHEMA`: Schema name (e.g., `public`)
   - `SNOWFLAKE_WAREHOUSE`: Warehouse name

## Running Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Architecture

```
app.py                          # Main Streamlit interface
├── src/config.py             # Snowflake configuration
├── src/snowflake_client.py    # Database connection & queries
└── src/cortex_analyst.py      # Cortex Analyst integration
```

## Features

- **Chat Interface**: Natural language Q&A about Census demographics
- **Conversation History**: Full context preserved across messages
- **Data Visualization**: Results displayed as tables
- **Example Questions**: Quick-start suggestions in sidebar
- **Clear Button**: Reset conversation anytime

## Example Queries

- "What is the population of California?"
- "Show me population by age group"
- "Compare Texas and New York populations"
- "What is the sex breakdown for Florida?"

## Troubleshooting

### Connection Error
```
ConfigurationError: Missing Snowflake configuration
```
→ Check .env file has all required variables

### Cortex Error
```
Error: Semantic view not found
```
→ Ensure `CENSUS_DEMOGRAPHICS_MODEL` is deployed:
```sql
SELECT * FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';
```

### Slow Responses
→ Check Snowflake warehouse is running and has sufficient credits

## Deployment

### Streamlit Cloud
```bash
git push  # Push to GitHub
# Then deploy via Streamlit Cloud dashboard
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

## Notes

- Conversation context limited to last 5 messages for cost efficiency
- Queries timeout after 55 seconds
- All data is read-only (no modifications to source data)
