import os
import sqlite3
import pandas as pd
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from db_setup import init_database, DB_NAME

# Load environment variables from .env file
load_dotenv()

# System Prompt instructing Gemini to produce raw executable SQL
SYSTEM_PROMPT = """
You are an expert SQL query generator specializing in SQLite.
Given an input question in natural language, convert it into a syntactically correct SQLite query.

The database contains two tables:

1. EMPLOYEE:
   - ID (INTEGER, PRIMARY KEY)
   - NAME (VARCHAR(50))
   - DEPARTMENT (VARCHAR(50))
   - SALARY (INT)
   - JOIN_DATE (DATE)

2. STUDENT:
   - NAME (VARCHAR(25))
   - CLASS (VARCHAR(25))
   - SECTION (VARCHAR(25))
   - MARKS (INT)

RULES FOR OUTPUT:
1. Return ONLY the raw executable SQL query string.
2. Do NOT use markdown code blocks (such as ```sql or ```).
3. Do NOT include any explanations, introduction, comments, or extra text.
4. Ensure exact column names and table names match the schema described above.
"""

def clean_sql_query(raw_query: str) -> str:
    """Strips markdown code blocks, sql tags, and trailing spaces from the LLM output."""
    query = raw_query.strip()
    if query.startswith("```"):
        lines = query.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        query = "\n".join(lines).strip()
    # Strip any residual 'sql' prefix if present at start
    if query.lower().startswith("sql\n"):
        query = query[4:].strip()
    return query

def get_gemini_response(question: str, api_key: str, model_name: str = "gemini-1.5-flash") -> str:
    """Invokes Google Gemini Pro API to translate natural language question to SQL."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content([SYSTEM_PROMPT, question])
    return response.text

def read_sql_query(sql_query: str, db_path: str = DB_NAME):
    """Executes SQL query against SQLite database using sqlite3 and returns Pandas DataFrame & error msg if any."""
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

def run_streamlit_app():
    """Main Streamlit Application UI and Logic."""
    # Ensure database exists
    init_database(DB_NAME)

    # Page Configuration
    st.set_page_config(
        page_title="Text to SQL LLM App",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for Modern Aesthetic UI
    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: #e0e6ed;
        }
        
        .main-header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        .main-title {
            font-family: 'Inter', sans-serif;
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        .sub-title {
            color: #94a3b8;
            font-size: 1.05rem;
            margin-bottom: 0px;
        }

        .stButton>button {
            background: linear-gradient(90deg, #2563eb, #3b82f6);
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #1d4ed8, #2563eb);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
            transform: translateY(-1px);
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar Configuration
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/sql.png", width=64)
        st.title("Settings & DB Info")
        
        # API Key Handling
        env_api_key = os.getenv("GEMINI_API_KEY", "")
        if env_api_key == "your_api_key_here":
            env_api_key = ""
            
        api_key_input = st.text_input(
            "Gemini API Key",
            value=env_api_key,
            type="password",
            help="Get your key from Google AI Studio (https://aistudio.google.com/)"
        )
        
        selected_model = st.selectbox(
            "Gemini Model",
            ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"],
            index=0,
            help="Select Gemini model version"
        )
        
        st.divider()
        
        # Database Schema Inspection
        st.subheader("📊 Database Schema Browser")
        db_table = st.radio("Select Table to View Schema", ["EMPLOYEE", "STUDENT"])
        
        conn = sqlite3.connect(DB_NAME)
        if db_table == "EMPLOYEE":
            st.markdown("**Table:** `EMPLOYEE`")
            schema_df = pd.read_sql_query("PRAGMA table_info(EMPLOYEE);", conn)[['name', 'type']]
            st.dataframe(schema_df, use_container_width=True, hide_index=True)
            if st.checkbox("Preview EMPLOYEE Data", value=True):
                sample_data = pd.read_sql_query("SELECT * FROM EMPLOYEE LIMIT 5;", conn)
                st.dataframe(sample_data, use_container_width=True, hide_index=True)
        else:
            st.markdown("**Table:** `STUDENT`")
            schema_df = pd.read_sql_query("PRAGMA table_info(STUDENT);", conn)[['name', 'type']]
            st.dataframe(schema_df, use_container_width=True, hide_index=True)
            if st.checkbox("Preview STUDENT Data", value=True):
                sample_data = pd.read_sql_query("SELECT * FROM STUDENT LIMIT 5;", conn)
                st.dataframe(sample_data, use_container_width=True, hide_index=True)
        conn.close()
        
        st.divider()
        if st.button("🔄 Reset Sample Database"):
            if os.path.exists(DB_NAME):
                os.remove(DB_NAME)
            init_database(DB_NAME)
            st.success("Database re-initialized successfully!")
            st.rerun()

    # Main Header
    st.markdown("""
        <div class="main-header">
            <div class="main-title">Text to SQL LLM App powered by Gemini Pro 🤖⚡</div>
            <div class="sub-title">Convert your natural language questions into accurate SQL queries & execute them instantly against SQLite.</div>
        </div>
    """, unsafe_allow_html=True)

    # Quick Example Prompts
    st.markdown("##### 💡 Example Questions (Click to use):")
    col_e1, col_e2, col_e3 = st.columns(3)
    example_query = ""

    if col_e1.button("💼 Employees in Sales > 50000"):
        example_query = "Show all employees in the Sales department earning more than 50000"
    if col_e2.button("🎓 Students in Data Science Section A"):
        example_query = "List all students in Data Science class and Section A with marks above 80"
    if col_e3.button("💰 Dept Salary Breakdown"):
        example_query = "What is the average salary and total count of employees in each department?"

    # Question Input
    default_val = example_query if example_query else "Show all employees in the Sales department earning more than 50000"

    user_prompt = st.text_area(
        "Enter your question in natural language:",
        value=default_val,
        height=100,
        placeholder="e.g. List all students in Data Science class with marks greater than 80"
    )

    col_submit, _ = st.columns([1, 4])
    submit_clicked = col_submit.button("🚀 Ask Question", use_container_width=True)

    # Execution Flow
    if submit_clicked or example_query:
        active_api_key = api_key_input.strip()
        
        if not active_api_key:
            st.error("🔑 Please provide a valid Gemini API Key in the sidebar or `.env` file to continue.")
        elif not user_prompt.strip():
            st.warning("⚠️ Please enter a question to generate a SQL query.")
        else:
            with st.spinner("🧠 Thinking & generating SQL query via Gemini..."):
                try:
                    # 1. Fetch raw response from Gemini
                    raw_response = get_gemini_response(user_prompt, active_api_key, selected_model)
                    cleaned_sql = clean_sql_query(raw_response)
                    
                    # 2. Display Generated SQL Query
                    st.markdown("### 📜 Generated SQL Command")
                    st.code(cleaned_sql, language="sql")
                    
                    # 3. Execute SQL Query against SQLite
                    with st.spinner("⚡ Executing query against database..."):
                        df_result, err = read_sql_query(cleaned_sql, DB_NAME)
                        
                    st.markdown("### 📊 Database Query Results")
                    if err:
                        st.error(f"❌ SQL Execution Error: {err}")
                    else:
                        if df_result is not None and not df_result.empty:
                            st.success(f"Successfully retrieved **{len(df_result)}** record(s).")
                            st.dataframe(
                                df_result,
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # CSV Export
                            csv_data = df_result.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download CSV Results",
                                data=csv_data,
                                file_name="query_results.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("ℹ️ Query executed successfully, but returned 0 records.")
                            
                except Exception as e:
                    st.error(f"❌ Failed to generate SQL from LLM: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
        "Built with Python, Streamlit, Google Gemini Pro & SQLite."
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    run_streamlit_app()
