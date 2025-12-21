import anthropic
import os
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

def query_with_ai(question, df):
    """
    Use Claude AI to answer questions about salary data.
    Returns tuple: (result_df, explanation, generated_code)
    """
    
    # Initialize Claude client
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    # Get dataframe info
    df_info = f"""
Dataframe columns: {list(df.columns)}
Dataframe shape: {df.shape}
Sample data (first 3 rows):
{df.head(3).to_string()}

Data types:
{df.dtypes.to_string()}
"""
    
    # Create prompt
    prompt = f"""Du är en expert på Pandas och data-analys. Jag har en lönedata dataframe och vill att du genererar Python-kod för att svara på frågan.

VIKTIGT: 
- Dataframen heter 'df' och finns redan i minnet
- Svara ENDAST med Python-kod, ingen förklaring
- Koden ska returnera antingen en DataFrame eller en sträng med svaret
- Använd variabler 'result' för slutresultatet
- För siffror: formatera med tusentalsavgränsare (f"{{value:,}} kr")

Dataframe info:
{df_info}

Användarens fråga: {question}

Generera Python-kod som svarar på frågan:"""

    try:
        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract code from response
        generated_code = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if generated_code.startswith('```python'):
            generated_code = generated_code.split('```python')[1].split('```')[0].strip()
        elif generated_code.startswith('```'):
            generated_code = generated_code.split('```')[1].split('```')[0].strip()
        
        # Execute code safely
        result = execute_code_safely(generated_code, df)
        
        # Generate explanation
        if isinstance(result, pd.DataFrame):
            explanation = f"AI svarade med {len(result)} rader data"
            return result, explanation, generated_code
        else:
            explanation = str(result)
            return pd.DataFrame(), explanation, generated_code
            
    except Exception as e:
        error_msg = f"AI-fel: {str(e)}"
        return pd.DataFrame(), error_msg, ""


def execute_code_safely(code, df):
    """
    Execute generated code safely with the dataframe in scope.
    Returns the result or raises exception.
    """
    # Create safe execution environment
    local_vars = {
        'df': df.copy(),
        'pd': pd,
        'result': None
    }
    
    try:
        # Execute the code
        exec(code, {'pd': pd, '__builtins__': __builtins__}, local_vars)
        
        # Get result
        result = local_vars.get('result')
        
        if result is None:
            # If no result variable, try to get last expression value
            # This is a simple fallback
            return "Kod kördes men inget resultat returnerades"
        
        return result
        
    except Exception as e:
        raise Exception(f"Kod-exekveringsfel: {str(e)}")