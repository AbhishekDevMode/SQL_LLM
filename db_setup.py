import sqlite3
import os

DB_NAME = "student.db"

def init_database(db_path=DB_NAME):
    """Initializes the SQLite database with sample tables and records if not already populated."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create STUDENT table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS STUDENT (
            NAME VARCHAR(25),
            CLASS VARCHAR(25),
            SECTION VARCHAR(25),
            MARKS INT
        );
    """)

    # 2. Create EMPLOYEE table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EMPLOYEE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME VARCHAR(50),
            DEPARTMENT VARCHAR(50),
            SALARY INT,
            JOIN_DATE DATE
        );
    """)

    # Insert sample records into STUDENT if empty
    cursor.execute("SELECT COUNT(*) FROM STUDENT;")
    if cursor.fetchone()[0] == 0:
        students = [
            ('Aarav Sharma', 'Data Science', 'A', 92),
            ('Ananya Roy', 'Data Science', 'B', 85),
            ('Rohan Verma', 'DevOps', 'A', 78),
            ('Priya Patel', 'Data Science', 'A', 95),
            ('Kabir Singh', 'DevOps', 'B', 64),
            ('Sneha Gupta', 'Cyber Security', 'A', 88),
            ('Vikram Das', 'Cyber Security', 'B', 72),
            ('Ishaan Malhotra', 'Data Science', 'A', 90),
            ('Meera Nair', 'DevOps', 'A', 82),
            ('Tanya Kapoor', 'Cyber Security', 'A', 96)
        ]
        cursor.executemany("INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES (?, ?, ?, ?);", students)

    # Insert sample records into EMPLOYEE if empty
    cursor.execute("SELECT COUNT(*) FROM EMPLOYEE;")
    if cursor.fetchone()[0] == 0:
        employees = [
            ('Alice Smith', 'Sales', 65000, '2021-03-15'),
            ('Bob Johnson', 'Sales', 48000, '2022-06-01'),
            ('Charlie Brown', 'Engineering', 95000, '2020-01-10'),
            ('Diana Prince', 'Engineering', 105000, '2019-11-20'),
            ('Ethan Hunt', 'Sales', 58000, '2023-02-01'),
            ('Fiona Gallagher', 'Human Resources', 52000, '2021-08-12'),
            ('George Clark', 'Human Resources', 49000, '2022-04-18'),
            ('Hannah Abbott', 'Engineering', 88000, '2021-10-05'),
            ('Ian Wright', 'Marketing', 60000, '2022-09-30'),
            ('Julia Roberts', 'Marketing', 72000, '2020-05-14')
        ]
        cursor.executemany("INSERT INTO EMPLOYEE (NAME, DEPARTMENT, SALARY, JOIN_DATE) VALUES (?, ?, ?, ?);", employees)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print(f"Database successfully initialized at '{DB_NAME}'.")
