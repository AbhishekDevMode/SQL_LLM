# Text to SQL LLM App powered by Gemini Pro 🤖⚡

A production-ready Streamlit application in Python that converts natural language user questions into executable SQL queries using Google Gemini Pro and runs them directly against an SQLite database (`student.db`).

---

## 🌟 Features

- **Natural Language to SQL Translation**: Uses Google Gemini Pro to dynamically translate English questions into valid SQLite code.
- **Strict SQL Output Enforcement**: System prompt ensures Gemini outputs raw SQL without markdown wrappers or conversational fluff.
- **Direct Database Execution**: Integrated `sqlite3` execution engine fetches query results and renders them cleanly using Pandas DataFrames.
- **Interactive Database Explorer**: View table schemas and live previews for `EMPLOYEES` and `STUDENTS` tables directly in the sidebar.
- **Flexible API Key Configuration**: Load key automatically from `.env` or input/override via sidebar interface.
- **One-Click Example Queries**: Includes preset prompts for instant testing.
- **CSV Data Export**: Easily download SQL query results as a CSV file.

---

## 📂 Project Structure

```text
SQLLLM/
├── app.py              # Main Streamlit application
├── db_setup.py         # SQLite database creation & seed data script
├── student.db          # SQLite database (auto-generated)
├── requirements.txt    # Project dependencies
├── .env                # Environment file for Gemini API Key
├── .env.example        # Environment variable template
└── README.md           # Project documentation
```

---

## 📋 Database Schema

The database (`student.db`) comes pre-populated with two tables:

### 1. `EMPLOYEE` Table
| Column Name | Data Type | Description |
|---|---|---|
| `ID` | INTEGER (PK) | Unique employee identifier |
| `NAME` | VARCHAR(50) | Full name of the employee |
| `DEPARTMENT` | VARCHAR(50) | Department name (e.g., Sales, Engineering, Marketing) |
| `SALARY` | INT | Annual salary |
| `JOIN_DATE` | DATE | Date of joining (YYYY-MM-DD) |

### 2. `STUDENT` Table
| Column Name | Data Type | Description |
|---|---|---|
| `NAME` | VARCHAR(25) | Student full name |
| `CLASS` | VARCHAR(25) | Enrolled course/subject |
| `SECTION` | VARCHAR(25) | Class section (A/B) |
| `MARKS` | INT | Test score/marks |

---

## 🚀 Quick Start Guide

### 1. Clone & Navigate to Project
```bash
cd SQLLLM
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Gemini API Key
Obtain your Gemini API key from [Google AI Studio](https://aistudio.google.com/).

Create a `.env` file from the provided template:
```bash
cp .env.example .env
```
Open `.env` and insert your API key:
```env
GEMINI_API_KEY=AIzaSy...your_actual_key...
```

### 4. Initialize Database
Initialize and seed the sample SQLite database:
```bash
python db_setup.py
```

### 5. Launch the Streamlit App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 💡 Example Natural Language Queries to Try

- `"Show all employees in the Sales department earning more than 50000"`
- `"List all students in Data Science class and Section A with marks above 80"`
- `"What is the total salary budget and average salary for the Engineering department?"`
- `"Who is the highest paid employee in Marketing?"`
- `"Count the total number of students in each class"`

---

## 🛠️ Technology Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **LLM**: [Google Gemini Pro](https://ai.google.dev/) via `google-generativeai`
- **Database**: [SQLite3](https://sqlite.org/)
- **Data Manipulation**: [Pandas](https://pandas.pydata.org/)
- **Environment Management**: [python-dotenv](https://github.com/theskumar/python-dotenv)
