from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import os

app = Flask(__name__)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']

        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET password=? WHERE username=?",
            (new_password, request.form['username']))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('forgot_password.html')


def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "student.db")
    conn = sqlite3.connect(db_path)
    return conn


app.secret_key ="student_secret_key"

@app.route("/")
def home():
  error = session.pop("error", None)
  return render_template("login.html",error=error)

#  Login Form Submit Route
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT register_number FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session["register_number"] = user[0] 
        session["user"] = username
        return redirect(url_for("dashboard"))
    else:
      session["error"] = "❌ Invalid Username or Password"
    # return render_template("login.html", error=error,username=username)
    return redirect(url_for("home"))
    
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")   

@app.route("/dashboard")
def dashboard():

    if "register_number" not in session:
        return redirect("/")

    reg_no = session["register_number"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔹 Get student name
    cursor.execute(
        "SELECT name FROM users WHERE register_number=?",
        (reg_no,)
    )
    user = cursor.fetchone()
    name = user[0] if user else "Student"

    # 🔹 Get subject + marks
    cursor.execute(
        "SELECT subject, marks FROM marks WHERE register_number=?",
        (reg_no,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return render_template("dashboard.html", name=name, reg=reg_no)

    subjects = [row[0] for row in rows]
    marks = [row[1] for row in rows]


    avg = round(sum(marks) / len(marks), 2)

    # 🔹 Grade Logic
    if avg >= 75:
        grade = "A"
        level = "Advanced"
        result = "Pass"
    elif avg >= 60:
        grade = "B"
        level = "Intermediate"
        result = "Pass"
    elif avg >= 50:
        grade = "C"
        level = "Beginner"
        result = "Pass"
    else:
        grade = "D"
        level = "Needs Improvement"
        result = "Fail"

    # 🔹 Weak Subject
    weak_subject = subjects[marks.index(min(marks))]

    suggestion ="Focus on improving your understanding of important concepts and practice regularly. Consistent effort and revision will help strengthen your overall performance."

            
    # suggestion = suggestions.get(weak_subject, "Keep improving.")

    return render_template(
        "dashboard.html",
        name=name,
        reg=reg_no,
        subjects=subjects,
        marks=marks,
        avg=avg,
        grade=grade,
        level=level,
        result=result,
        weak_subject=weak_subject,
        suggestion=suggestion,
    )    
    
  
#Flask Connection
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        reg = request.form.get("registerNumber")
        name = request.form.get("studentName")
        dept = request.form.get("department")
        year = request.form.get("year")
        sem = request.form.get("semister")
        user = request.form.get("username")
        password = request.form.get("password")

        print(reg, name, dept, year, sem, user, password)

        # 🔥 DATABASE INSERT START
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (register_number, name, username, password, department, year, semister)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (reg, name, user, password, dept, year, sem))

        conn.commit()
        conn.close()
        # 🔥 DATABASE INSERT END

        session["registered"] = True
        session["step"] = "success"
        session["name"] = name
        session["register_number"] = reg
        session["department"] = dept
        session["year"] = year
        session["semister"] = sem

        return redirect("/success")

    return render_template("registration.html")

@app.route("/success", methods=["GET","POST"])
def success():
  if session.get("step")!="success":
    return redirect("/")   
  session["step"]="marks"
  return render_template("success.html")

@app.route("/marks" , methods=["GET","POST"])
def marks():

    if session.get("step") != "marks":
        return redirect("/")

    dept = session.get("department")
    year =int(session.get("year"))
    sem =int(session.get("semister"))

    print("Department:",dept)
    print("year:",year)
    print("Sem:",sem)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject_name 
        FROM subjects
        WHERE department=? AND year=? AND semister=?
    """,(dept,year,sem))

    subjects = cursor.fetchall()

    print("Subjects from DB:", subjects)

    conn.close()

    subject_list = [row[0] for row in subjects]

    return render_template(
        "marks.html",
        name=session.get("name"),
        reg=session.get("register_number"),
        subjects=subject_list
    )


# Load trained model
model = pickle.load(open("student_model.pkl", "rb"))

@app.route('/predict', methods=['POST'])
def predict():

    if session.get("step") != "marks":
        return redirect("/")

    session["step"] = "dashboard"

    name = session.get("name")
    reg = session.get("register_number")

    print("FORM DATA:", dict(request.form))

    # 🔹 Fetch subjects dynamically from DB
    dept = session.get("department")
    year = session.get("year")
    sem = session.get("semister")


    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject_name
        FROM subjects
        WHERE department=? AND year=? AND semister=?
    """,(dept,year,sem))

    subjects = [row[0] for row in cursor.fetchall()]

    # 🔹 Read marks dynamically
    marks = []
    for subject in subjects:
        mark = int(request.form.get(subject))
        marks.append(mark)

    # 🔹 Average
    avg = round(sum(marks) / len(marks), 2)

    # 🔹 Grade
    if avg >= 75:
        grade = "A"
        level = "Advanced"
        result = "Pass"
    elif avg >= 60:
        grade = "B"
        level = "Intermediate"
        result = "Pass"
    elif avg >= 50:
        grade = "C"
        level = "Beginner"
        result = "Pass"
    else:
        grade = "D"
        level = "Needs Improvement"
        result = "Fail"

    # 🔹 Weak subject
    weak_subject = subjects[marks.index(min(marks))]

    suggestion = "Focus on improving your understanding of important concepts and practice regularly. Consistent effort and revision will help strengthen your overall performance."
       
       
    # suggestion = suggestions.get(weak_subject, "Keep improving.")

    # 🔹 Delete old marks
    reg_no = session["register_number"]

    cursor.execute(
        "DELETE FROM marks WHERE register_number=?",
        (reg_no,)
    )

    # 🔹 Insert new marks dynamically
    marks_data = []
    for subject, mark in zip(subjects, marks):
        marks_data.append((reg_no, subject, mark))

    cursor.executemany(
        "INSERT INTO marks (register_number, subject, marks) VALUES (?, ?, ?)",
        marks_data
    )

    conn.commit()
    conn.close()

    return render_template(
        "dashboard.html",
        name=name,
        reg=reg,
        subjects=subjects,
        marks=marks,
        avg=avg,
        grade=grade,
        level=level,
        result=result,
        weak_subject=weak_subject,
        suggestion=suggestion
    )
@app.errorhandler(404)
def page_not_found(e):
   return redirect("/")

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT,
        department TEXT,
        year INTEGER,
        semister INTEGER           
                   
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        register_number TEXT PRIMARY key,
        name TEXT,
        username TEXT UNIQUE,
        password TEXT,
        department TEXT,
        year INTEGER,
        semister INTEGER       
                              
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        register_number TEXT,
        subject TEXT,
        marks INTEGER                      
    )
    """)

    conn.commit()
    conn.close()

create_tables()  

def insert_subjects():
    conn = get_db_connection()
    cursor = conn.cursor()

    subjects_data = [
        
       ('C Programming','CSE',1,1),
       ('Engineering Mathematics','CSE',1,1),
       ('Engineering Physics','CSE',1,1),
       ('Basic Electrical Engineering','CSE',1,1),
       ('English','CSE',1,1),
       ('Engineering Drawing','CSE',1,1),

       ('Python Programming','CSE',1,2),
       ('Discrete Mathematics','CSE',1,2),
       ('Digital Logic','CSE',1,2),
       ('Data Structures','CSE',1,2),
       ('Environmental Science','CSE',1,2),
       ('Statistics','CSE',1,2),

       ('Data Structures','CSE',2,3),
       ('Computer Organization','CSE',2,3),
       ('Object Oriented Programming','CSE',2,3),
       ('Operating Systems','CSE',2,3),
       ('Probability','CSE',2,3),
       ('Software Engineering','CSE',2,3),

       ('Database Management Systems','CSE',2,4),
       ('Operating Systems','CSE',2,4),
       ('Software Engineering','CSE',2,4),
('Computer Networks','CSE',2,4),
('Theory of Computation','CSE',2,4),
('Web Technologies','CSE',2,4),

('Artificial Intelligence','CSE',3,5),
('Machine Learning','CSE',3,5),
('Cloud Computing','CSE',3,5),
('Cyber Security','CSE',3,5),
('Data Mining','CSE',3,5),
('Mobile Computing','CSE',3,5),

('Big Data','CSE',3,6),
('Deep Learning','CSE',3,6),
('Internet of Things','CSE',3,6),
('Software Testing','CSE',3,6),
('Compiler Design','CSE',3,6),
('Distributed Systems','CSE',3,6),

('Machine Learning','CSE',4,7),
('Cloud Computing','CSE',4,7),
('Cyber Security','CSE',4,7),
('Blockchain','CSE',4,7),
('Natural Language Processing','CSE',4,7),
('Project','CSE',4,7),

# ECE
('Engineering Mathematics','ECE',1,1),
('Engineering Physics','ECE',1,1),
('Basic Electronics','ECE',1,1),
('Electrical Circuits','ECE',1,1),
('English','ECE',1,1),
('Engineering Drawing','ECE',1,1),

('Digital Logic Design','ECE',1,2),
('Network Analysis','ECE',1,2),
('Electronic Devices','ECE',1,2),
('Signals and Systems','ECE',1,2),
('Mathematics II','ECE',1,2),
('Environmental Science','ECE',1,2),

('Signals and Systems','ECE',2,3),
('Electronic Devices','ECE',2,3),
('Analog Electronics','ECE',2,3),
('Control Systems','ECE',2,3),
('Communication Systems','ECE',2,3),
('Probability','ECE',2,3),

('Analog Electronics','ECE',2,4),
('Microprocessors','ECE',2,4),
('Digital Signal Processing','ECE',2,4),
('Linear IC Applications','ECE',2,4),
('Communication Systems','ECE',2,4),
('Electromagnetic Theory','ECE',2,4),

('Digital Signal Processing','ECE',3,5),
('VLSI Design','ECE',3,5),
('Embedded Systems','ECE',3,5),
('Microwave Engineering','ECE',3,5),
('Wireless Communication','ECE',3,5),
('Digital Communication','ECE',3,5),

('VLSI Design','ECE',3,6),
('Embedded Systems','ECE',3,6),
('Satellite Communication','ECE',3,6),
('Radar Systems','ECE',3,6),
('Optical Communication','ECE',3,6),
('Control Systems','ECE',3,6),

('Embedded Systems','ECE',4,7),
('Wireless Communication','ECE',4,7),
('IoT','ECE',4,7),
('5G Communication','ECE',4,7),
('Signal Processing','ECE',4,7),
('Project','ECE',4,7),


# ----- B.Tech EEE SEM 1 -----
("Mathematics-I", "EEE", 1, 1),
("Engineering Physics", "EEE", 1, 1),
("Basic Electrical Engineering", "EEE", 1, 1),
("Engineering Graphics", "EEE", 1, 1),
("Programming in C", "EEE", 1, 1),
("Environmental Science", "EEE", 1, 1),

# ----- B.Tech EEE SEM 2 -----
("Mathematics-II", "EEE", 1, 2),
("Engineering Chemistry", "EEE", 1, 2),
("Electronic Devices", "EEE", 1, 2),
("Data Structures", "EEE", 1, 2),
("Electrical Circuits", "EEE", 1, 2),
("Communication Skills", "EEE", 1, 2),

# ----- B.Tech EEE SEM 3 -----
("Mathematics-III", "EEE", 2, 3),
("Signals and Systems", "EEE", 2, 3),
("Electrical Machines-I", "EEE", 2, 3),
("Analog Electronics", "EEE", 2, 3),
("Control Systems", "EEE", 2, 3),
("Digital Electronics", "EEE", 2, 3),

# ----- B.Tech EEE SEM 4 -----
("Electrical Machines-II", "EEE", 2, 4),
("Power Systems-I", "EEE", 2, 4),
("Microprocessors", "EEE", 2, 4),
("Power Electronics", "EEE", 2, 4),
("Measurements and Instrumentation", "EEE", 2, 4),
("Engineering Economics", "EEE", 2, 4),

# ----- B.Tech EEE SEM 5 -----
("Power Systems-II", "EEE", 3, 5),
("Electric Drives", "EEE", 3, 5),
("Renewable Energy Systems", "EEE", 3, 5),
("Control Systems-II", "EEE", 3, 5),
("Digital Signal Processing", "EEE", 3, 5),
("Open Elective-I", "EEE", 3, 5),

# ----- B.Tech EEE SEM 6 -----
("High Voltage Engineering", "EEE", 3, 6),
("Smart Grid Technology", "EEE", 3, 6),
("Industrial Automation", "EEE", 3, 6),
("Embedded Systems", "EEE", 3, 6),
("Power System Protection", "EEE", 3, 6),
("Open Elective-II", "EEE", 3, 6),

# ----- B.Tech EEE SEM 7 -----
("Advanced Power Electronics", "EEE", 4, 7),
("Energy Management", "EEE", 4, 7),
("Electric Vehicles Technology", "EEE", 4, 7),
("Project Work", "EEE", 4, 7),
("Seminar", "EEE", 4, 7),
("Professional Ethics", "EEE", 4, 7),


# BCA
('Programming in C','BCA',1,1),
('Computer Fundamentals','BCA',1,1),
('Mathematics','BCA',1,1),
('Digital Electronics','BCA',1,1),
('English','BCA',1,1),
('Office Automation','BCA',1,1),

('Data Structures','BCA',1,2),
('Database Management Systems','BCA',1,2),
('Operating Systems','BCA',1,2),
('Computer Networks','BCA',1,2),
('Statistics','BCA',1,2),
('Web Technologies','BCA',1,2),

('Java Programming','BCA',2,3),
('Python Programming','BCA',2,3),
('Software Engineering','BCA',2,3),
('Computer Graphics','BCA',2,3),
('Web Development','BCA',2,3),
('E-Commerce','BCA',2,3),

('Python Programming','BCA',2,4),
('Operating Systems','BCA',2,4),
('Computer Networks','BCA',2,4),
('Web Development','BCA',2,4),
('Mobile App Development','BCA',2,4),
('Software Testing','BCA',2,4),

('Machine Learning','BCA',3,5),
('Artificial Intelligence','BCA',3,5),
('Cloud Computing','BCA',3,5),
('Data Mining','BCA',3,5),
('Cyber Security','BCA',3,5),
('Project','BCA',3,5),


# BSC
('Programming in C','BSC',1,1),
('Computer Fundamentals','BSC',1,1),
('Mathematics','BSC',1,1),
('Physics','BSC',1,1),
('English','BSC',1,1),
('Digital Electronics','BSC',1,1),

('Data Structures','BSC',1,2),
('Database Management Systems','BSC',1,2),
('Operating Systems','BSC',1,2),
('Computer Networks','BSC',1,2),
('Statistics','BSC',1,2),
('Java Programming','BSC',1,2),

('Java Programming','BSC',2,3),
('Python Programming','BSC',2,3),
('Web Technologies','BSC',2,3),
('Software Engineering','BSC',2,3),
('Computer Graphics','BSC',2,3),
('Data Mining','BSC',2,3),

('Python Programming','BSC',2,4),
('Operating Systems','BSC',2,4),
('Computer Networks','BSC',2,4),
('Web Development','BSC',2,4),
('Machine Learning','BSC',2,4),
('Cloud Computing','BSC',2,4),

('Artificial Intelligence','BSC',3,5),
('Cyber Security','BSC',3,5),
('Data Science','BSC',3,5),
('Big Data','BSC',3,5),
('IoT','BSC',3,5),
('Project','BSC',3,5),

]


    cursor.executemany(
        "INSERT INTO subjects (subject_name, department, year, semister) VALUES (?, ?, ?, ?)",
        subjects_data
    )

    conn.commit()
    conn.close()

           
if __name__ == "__main__":
    create_tables()
    # insert_subjects()

    app.run(host="0.0.0.0", port=5000)
