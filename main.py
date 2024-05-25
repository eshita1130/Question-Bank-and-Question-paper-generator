from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For session management
client = MongoClient('localhost', 27017)
db = client['questionbank']
users_collection = db['users']
questions_collection = db['questions']


def check_pass(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    if not name or not email or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for("index"))

    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        flash('Email already exists. Please choose a different email.', 'error')
        return redirect(url_for('index'))

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = {
        'name': name,
        'email': email,
        'password': hashed_password
    }
    users_collection.insert_one(new_user)

    flash('Account created successfully. Please log in.', 'success')
    session['user'] = email
    return redirect(url_for('home'))


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash('Email and password are required.', 'error')
        return redirect(url_for('index'))

    user = users_collection.find_one({'email': email})
    if user and check_pass(user['password'], password):
        session['user'] = user['email']
        return redirect(url_for('home'))
    else:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('index'))


@app.route('/home')
def home():
    if 'user' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('index'))
    return render_template('home.html')


@app.route('/question_bank')
def question_bank():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('question_bank.html')


@app.route('/question_paper')
def question_paper():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('question_paper.html')


@app.route('/generated_question_paper')
def generated_question_paper():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('generated_question_paper.html')


@app.route('/api/questions', methods=['POST'])
def add_question():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized access"})

    question_data = request.json
    questions_collection.insert_one(question_data)
    return jsonify({"message": "Question added successfully!"})


@app.route('/api/questions', methods=['GET'])
def get_questions():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized access"})

    questions = questions_collection.find()
    question_list = []
    for question in questions:
        question_list.append({
            "questionText": question.get("questionText"),
            "answerOptions": question.get("answerOptions"),
            "correctAnswer": question.get("correctAnswer")
        })
    return jsonify(question_list)


if __name__ == '__main__':
    app.run(debug=True)
