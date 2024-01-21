from flask import Flask, render_template, request, flash, url_for, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from nltk.tokenize import sent_tokenize, word_tokenize
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from secrets import token_hex
from sqlalchemy import UniqueConstraint
import nltk

# Initialize the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# Move secret key generation outside the app instantiation
app.config['SECRET_KEY'] = token_hex(24)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
nltk.download('punkt')


# Define the User and StudySession models
class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(80), nullable=False, unique=True)
  grade = db.Column(db.String(10), nullable=False)
  learning_style = db.Column(db.String(20))
  hashed_password = db.Column(db.String(128))
  study_sessions = db.relationship('StudySession', backref='user', lazy=True)

  __table_args__ = (UniqueConstraint('name', name='_user_name_uc'), )


class StudySession(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  subject = db.Column(db.String(80), nullable=False)
  study_time = db.Column(db.Integer, nullable=False)
  date = db.Column(db.DateTime, default=datetime.utcnow)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Uncomment db.create_all() for database initialization
with app.app_context():
  db.create_all()


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


@app.route('/')
def home():
  students = User.query.all()
  return render_template('index.html', students=students)


@app.route('/add_student', methods=['POST'])
def add_student():
  if request.method == 'POST':
    student_data = request.form.to_dict()
    if not student_data.get('password'):
      flash('الرجاء إدخال كلمة مرور', 'error')
      return redirect(url_for('home'))

    student_data['hashed_password'] = generate_password_hash(
        student_data['password'], method='sha256')
    del student_data['password']

    new_student = User(**student_data)
    try:
      db.session.add(new_student)
      db.session.commit()
      flash('تمت إضافة الطالب بنجاح', 'success')
    except IntegrityError:
      db.session.rollback()
      flash('عذرًا، اسم المستخدم مستخدم بالفعل. الرجاء اختيار اسم مستخدم آخر.',
            'error')
    except Exception as e:
      db.session.rollback()
      flash(f'حدث خطأ: {str(e)}', 'error')

  return redirect(url_for('home'))


# ... (Existing code)

if __name__ == '__main__':
  app.run(debug=True)
