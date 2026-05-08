import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid
import re
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans
from langchain_groq import ChatGroq
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import re
import os
import uuid
from django.conf import settings
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
llm=ChatGroq(
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant"
)


STATIC_PLOT_DIR = 'dashboard/static/dashboard/plots'

'''def save_plot():
    os.makedirs(STATIC_PLOT_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(STATIC_PLOT_DIR, filename)
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()
    return f"dashboard/plots/{filename}"'''
def save_plot():
    filename = f"{uuid.uuid4().hex}.png"
    
    # Save in static/dashboard/plots
    plots_dir = os.path.join(settings.BASE_DIR, 'static', 'dashboard', 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    file_path = os.path.join(plots_dir, filename)
    plt.savefig(file_path, bbox_inches='tight')
    plt.close()

    # Return path relative to static folder
    return f"dashboard/plots/{filename}"

'''def query_data(df, query):
    prompt = f"""
    Analyze the DataFrame 'df' and answer the query: {query} in form of code of python to generate visual representation.
    Columns: {df.columns.tolist()}
    Return only valid Python code using matplotlib/seaborn.
    """
    response = llm.invoke(prompt)
    code = re.sub(r"```(?:python)?|```", "", response.content).strip()
    try:
        exec(code, {"df": df, "sns": sns, "plt": plt, "pd": pd})
        return save_plot()
    except Exception as e:
        return str(e)'''


def query_data(df, query):
    import warnings
    import re
    warnings.filterwarnings("ignore")

    # Step 1: Ask the LLM to generate Python code
    prompt = f"""
    You are a Python data analyst. Write **only Python code** (no explanation) using matplotlib or seaborn
    to visualize the following query: "{query}" using the dataframe 'df'.
    Do not use pairplot. The DataFrame has columns: {df.columns.tolist()}.
    Only return Python code, no text or comments.
    """

    try:
        response = llm.invoke(prompt)
        code = re.sub(r"```(?:python)?|```", "", response.content).strip()
        local_env = {"df": df.copy(), "sns": sns, "plt": plt, "pd": pd}

        # Step 2: Execute the generated code
        exec(code, local_env)
        plot_path = save_plot()

        # Step 3: Get explanation of the generated code
        explanation_prompt = f"Explain what the following Python code is doing step-by-step:\n\n{code}"
        explanation_response = llm.invoke(explanation_prompt)
        explanation = explanation_response.content.strip()

        # Step 4: Return both plot and explanation
        return {
            "plot_path": plot_path,
            "explanation": explanation,
            "code": code
        }

    except Exception as e:
        # Fallback visualization
        plt.clf()
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include='object').columns.tolist()

        try:
            if len(numeric_cols) >= 2:
                sns.scatterplot(data=df, x=numeric_cols[0], y=numeric_cols[1])
                plt.title(f"Scatter Plot of {numeric_cols[0]} vs {numeric_cols[1]}")
            elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                sns.boxplot(x=categorical_cols[0], y=numeric_cols[0], data=df)
                plt.title(f"Boxplot of {numeric_cols[0]} by {categorical_cols[0]}")
            elif len(numeric_cols) >= 1:
                df[numeric_cols].hist(bins=20, figsize=(10, 5))
                plt.tight_layout()
                plt.suptitle("Histogram of Numeric Columns", y=1.02)
            else:
                sns.countplot(y=categorical_cols[0], data=df)
                plt.title(f"Count Plot of {categorical_cols[0]}")
            
            return {
                "plot_path": save_plot(),
                "explanation": "Fallback visualization due to an error in generated code.",
                "code": "Fallback visualization code was used."
            }

        except Exception as fallback_error:
            return {
                "plot_path": None,
                "explanation": f"Error generating plot: {str(fallback_error)}",
                "code": ""
            }


def analyze_data_with_ai_and_visualize(df):
    columns = df.columns.tolist()
    response = llm.invoke(f"Choose best target column for ML: {columns} and only return the column name that you choose")
    target_column = response.content.strip().replace('"', '').replace("'", "")
    
    #X = df.drop(columns=[target_column])
    #y = df[target_column]

    
    return {
        "target_column": target_column,
        
    }

def get_insights_from_llm_with_visualization(insights, df, query):
    prompt = f"""
    Based on dataset columns: {df.columns.tolist()} and analysis:
    -sample data: {df.head()}
    Answer the query: {query}
    you have to utilize the data and use your knowledge to generate an analysis in the response also come up with some intelligently devised contenet for anomalies, clusters and feature importances dont try to generate graphs
    """
    response = llm.invoke(prompt)
    return response.content

def perform_analysis(df, query, analysis_type):
    prompt = f"Perform {analysis_type} analysis on columns {df.columns.tolist()}.\nQuery: {query} dont try to generate any visualizations and also if you need a python code dont do it on this machine, do it using your servers just give a brief of your work process and generate analysis. dont give any python code in output."
    response = llm.invoke(prompt)
    return response.content
