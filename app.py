import math
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    xp = db.Column(db.Float, default=0)
    xp_required = db.Column(db.Float, default=1)
    total_xp = db.Column(db.Float, default=0)
    level = db.Column(db.Integer, default=1)
    def add_xp(self, amount):
        self.xp += amount
        self.check_level_up()
    
    def check_level_up(self):
        while self.xp >= self.xp_required:
            self.xp -= self.xp_required
            self.xp_required = round(self.xp_required + self.xp_required * 1 / math.sqrt(self.level))
            self.level += 1
    
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(80))
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + '.id'))
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

@app.route('/')
def index():
    tasks = Task.query.all()
    user = User.query.first()
    return render_template('index.html', tasks=tasks, user=user)

@app.route('/add', methods=['POST'])
def add_task():
    name = request.form.get('name')
    new_task = Task(name=name)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        task.completed = True
        user = User.query.first()
        if user:
            user.add_xp(1)
            
    db.session.commit()
    return redirect(url_for('index'))
    
def init_db():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            new_user = User(username='Player')
            db.session.add(new_user)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8081)