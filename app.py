from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ================= MODELS =================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    date = db.Column(db.Date, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= ROUTES =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('register.html', error='Username and password required')
        
        hashed = generate_password_hash(password)
        user = User(
            username=username,
            password=hashed
        )
        try:
            db.session.add(user)
            db.session.commit()
            return redirect('/')
        except Exception:
            db.session.rollback()
            return render_template('register.html', error='Username already exists')
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    total = sum(e.amount for e in expenses) if expenses else 0
    return render_template('dashboard.html', expenses=expenses, total=total)

@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', '').strip()
    category = request.form.get('category', '').strip()

    if not title or not amount:
        return redirect('/dashboard')

    try:
        expense = Expense(
            title=title,
            amount=float(amount),
            category=category,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
    except ValueError:
        pass
    
    return redirect('/dashboard')

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first()
    if expense:
        db.session.delete(expense)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)