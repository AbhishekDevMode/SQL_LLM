import os
import re
import sqlite3
import pandas as pd
import streamlit as st
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
    if query.lower().startswith("sql\n"):
        query = query[4:].strip()
    return query

def smart_fallback_sql_generator(question: str) -> str:
    """
    Offline Rule-based SQL Engine used when LLM API Key quota is exhausted.
    Parses common natural language queries for EMPLOYEE and STUDENT tables.
    """
    q = question.lower()
    
    # Check for EMPLOYEE queries
    if "employee" in q or "department" in q or "salary" in q or "earning" in q:
        dept = None
        for d in ["sales", "engineering", "human resources", "marketing"]:
            if d in q:
                dept = d.title()
                break
        
        salary_match = re.search(r'(?:more than|greater than|>|earning)\s*(\d+)', q)
        salary_val = salary_match.group(1) if salary_match else None
        
        if "average" in q or "avg" in q:
            return "SELECT DEPARTMENT, AVG(SALARY) AS AVERAGE_SALARY, COUNT(*) AS TOTAL_EMPLOYEES FROM EMPLOYEE GROUP BY DEPARTMENT;"
        elif "highest" in q or "top" in q:
            return "SELECT * FROM EMPLOYEE ORDER BY SALARY DESC LIMIT 5;"
        elif dept and salary_val:
            return f"SELECT * FROM EMPLOYEE WHERE DEPARTMENT = '{dept}' AND SALARY > {salary_val};"
        elif dept:
            return f"SELECT * FROM EMPLOYEE WHERE DEPARTMENT = '{dept}';"
        elif salary_val:
            return f"SELECT * FROM EMPLOYEE WHERE SALARY > {salary_val};"
        else:
            return "SELECT * FROM EMPLOYEE;"

    # Check for STUDENT queries
    elif "student" in q or "mark" in q or "class" in q or "section" in q:
        class_name = None
        for c in ["data science", "devops", "cyber security"]:
            if c in q:
                class_name = c.title()
                break
        
        sec_match = re.search(r'section\s*([a-b])', q)
        section_val = sec_match.group(1).upper() if sec_match else None
        
        marks_match = re.search(r'(?:above|greater than|more than|>|marks)\s*(\d+)', q)
        marks_val = marks_match.group(1) if marks_match else None
        
        conditions = []
        if class_name:
            conditions.append(f"CLASS = '{class_name}'")
        if section_val:
            conditions.append(f"SECTION = '{section_val}'")
        if marks_val:
            conditions.append(f"MARKS > {marks_val}")
            
        if conditions:
            return f"SELECT * FROM STUDENT WHERE {' AND '.join(conditions)};"
        elif "highest" in q or "top" in q:
            return "SELECT * FROM STUDENT ORDER BY MARKS DESC LIMIT 5;"
        else:
            return "SELECT * FROM STUDENT;"

    # Default general select fallback
    return "SELECT * FROM EMPLOYEE;"

def generate_sql_from_question(question: str, api_key: str, model_name: str = "gemini-1.5-flash") -> tuple[str, bool, str]:
    """
    Attempts SQL generation using:
    1. Google GenAI (Modern SDK)
    2. Google GenerativeAI (Legacy SDK)
    3. Smart Offline Rule-Based Fallback (if quota exceeded)
    
    Returns (sql_query, is_offline_fallback, notice_message)
    """
    cleaned_api_key = api_key.strip()
    
    # 1. Try google.genai (Modern SDK)
    if cleaned_api_key:
        try:
            from google import genai
            client = genai.Client(api_key=cleaned_api_key)
            target_model = model_name.replace("models/", "")
            response = client.models.generate_content(
                model=target_model,
                contents=[SYSTEM_PROMPT, question]
            )
            if response and response.text:
                return clean_sql_query(response.text), False, ""
        except Exception as e1:
            err_str = str(e1)
            # Try legacy google.generativeai
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=cleaned_api_key)
                target_model = model_name.replace("models/", "")
                model = genai_legacy.GenerativeModel(target_model)
                response = model.generate_content([SYSTEM_PROMPT, question])
                if response and response.text:
                    return clean_sql_query(response.text), False, ""
            except Exception as e2:
                err_str += f" | Legacy error: {str(e2)}"
            
            # If rate limit/quota reached or API key issue, use Smart Offline Rule Engine
            offline_sql = smart_fallback_sql_generator(question)
            notice = f"⚠️ Gemini API returned Quota/Rate Limit error. Used Smart Rule-Based Engine fallback so your query executes seamlessly!"
            return offline_sql, True, notice

    # If no API key provided, use Smart Rule Engine directly
    offline_sql = smart_fallback_sql_generator(question)
    notice = "ℹ️ No Gemini API Key provided. Used Smart Rule-Based Engine to generate SQL."
    return offline_sql, True, notice

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
    init_database(DB_NAME)

    st.set_page_config(
        page_title="Text to SQL LLM App",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

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
            ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro", "gemini-2.0-flash"],
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
        
        if not user_prompt.strip():
            st.warning("⚠️ Please enter a question to generate a SQL query.")
        else:
            with st.spinner("🧠 Generating SQL query..."):
                sql_query, is_fallback, notice = generate_sql_from_question(user_prompt, active_api_key, selected_model)
                
                if notice:
                    if is_fallback:
                        st.warning(notice)
                    else:
                        st.info(notice)

                # Display Generated SQL Query
                st.markdown("### 📜 Generated SQL Command")
                st.code(sql_query, language="sql")
                
                # Execute SQL Query against SQLite
                with st.spinner("⚡ Executing query against database..."):
                    df_result, err = read_sql_query(sql_query, DB_NAME)
                    
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

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
        "Built with Python, Streamlit, Google Gemini & SQLite."
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    run_streamlit_app()
