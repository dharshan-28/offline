from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os

# Flask app
app = Flask(__name__, static_folder="frontend")

# ---------------- DB ----------------
def connect_db():
    return sqlite3.connect("database.db")


def create_table():
    conn = connect_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        score INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS students (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        completed INTEGER DEFAULT 0
    )''')

    conn.commit()
    conn.close()


# ---------------- DEFAULT ADMIN ----------------
def insert_admin():
    conn = connect_db()
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO students VALUES (?, ?, ?, ?)",
              ("admin", "admin123", "admin", 0))

    conn.commit()
    conn.close()


# ---------------- QUESTIONS ----------------
def insert_questions():
    conn = connect_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM questions")
    if c.fetchone()[0] == 0:
        questions = [
            ("What is JavaScript?", "Programming Language", "Scripting language", "Human language", "High level language", "Programming Language"),
            ("HTML stands for?", "Hyper Trainer Marking Language", "Hyper Text Markup Language", "High Text Machine Language", "None", "Hyper Text Markup Language"),
            ("CSS is used for?", "Styling", "Programming", "Database", "Networking", "Styling"),
            ("Which is database?", "MySQL", "HTML", "CSS", "JS", "MySQL"),
            ("JS stands for?", "Java Style", "JavaScript", "Just Script", "None", "JavaScript"),
            ("Which is backend language?", "Python", "HTML", "CSS", "Bootstrap", "Python"),
            ("Which is frontend?", "HTML", "Python", "SQL", "Java", "HTML"),
            ("Which is not programming language?", "Python", "Java", "HTML", "C++", "HTML"),
            ("Flask is?", "Framework", "Language", "Database", "IDE", "Framework"),
            ("SQLite is?", "Database", "Language", "Tool", "Editor", "Database")
        ]

        c.executemany("INSERT INTO questions VALUES (NULL,?,?,?,?,?,?)", questions)
        conn.commit()

    conn.close()


# Initialize DB
create_table()
insert_admin()
insert_questions()


# ---------------- ROUTES ----------------
@app.route('/')
def login_page():
    return send_from_directory(app.static_folder, "login.html")


@app.route('/admin')
def admin_page():
    return send_from_directory(app.static_folder, "admin.html")


@app.route('/exam')
def exam_page():
    return send_from_directory(app.static_folder, "exam.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    conn = connect_db()
    c = conn.cursor()

    c.execute("SELECT username, password, role, completed FROM students WHERE username=?",
              (data["username"],))
    user = c.fetchone()

    conn.close()

    if user and user[1] == data["password"]:

        if user[3] == 1:
            return jsonify({
                "error": "You have already completed the exam. Contact admin."
            }), 403

        return jsonify({
            "role": user[2],
            "username": user[0]
        })

    return jsonify({"error": "Invalid username or password"}), 401


# ---------------- CREATE USER ----------------
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json

    conn = connect_db()
    c = conn.cursor()

    try:
        c.execute("INSERT INTO students (username, password, role) VALUES (?, ?, ?)",
                  (data["username"], data["password"], data["role"]))
        conn.commit()
        msg = "User created successfully"
    except:
        msg = "User already exists"

    conn.close()
    return jsonify({"message": msg})


# ---------------- ADD QUESTION ----------------
@app.route('/add_question', methods=['POST'])
def add_question():
    data = request.json

    conn = connect_db()
    c = conn.cursor()

    c.execute("INSERT INTO questions VALUES (NULL,?,?,?,?,?,?)",
              (data['question'], data['option1'], data['option2'],
               data['option3'], data['option4'], data['answer']))

    conn.commit()
    conn.close()

    return jsonify({"message": "Question added"})


# ---------------- GET QUESTIONS ----------------
@app.route('/get_questions')
def get_questions():
    conn = connect_db()
    c = conn.cursor()

    c.execute("SELECT id, question, option1, option2, option3, option4 FROM questions")
    data = c.fetchall()

    conn.close()
    return jsonify(data)


# ---------------- SUBMIT ----------------
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    answers = data["answers"]
    username = data["username"]

    conn = connect_db()
    c = conn.cursor()

    c.execute("SELECT id, answer FROM questions")
    correct = c.fetchall()

    score = 0
    for q in correct:
        if str(q[0]) in answers and answers[str(q[0])] == q[1]:
            score += 1

    c.execute("INSERT INTO results (username, score) VALUES (?, ?)", (username, score))
    c.execute("UPDATE students SET completed=1 WHERE username=?", (username,))

    conn.commit()
    conn.close()

    return jsonify({"score": score})


# ---------------- RESULTS ----------------
@app.route('/results')
def results():
    conn = connect_db()
    c = conn.cursor()

    c.execute("SELECT username, score FROM results ORDER BY score DESC")
    data = c.fetchall()

    conn.close()
    return jsonify(data)


# ---------------- RESET ----------------
@app.route('/reset_student', methods=['POST'])
def reset_student():
    data = request.json

    conn = connect_db()
    c = conn.cursor()

    c.execute("UPDATE students SET completed=0 WHERE username=?", (data["username"],))

    conn.commit()
    conn.close()

    return jsonify({"message": "Student access restored"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))