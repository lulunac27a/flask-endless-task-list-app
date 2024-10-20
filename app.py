import math
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)  # user id
    username = db.Column(db.String(80), unique=True, nullable=False)  # username
    xp = db.Column(db.Float, default=0)  # user XP
    xp_required = db.Column(db.Float, default=1)  # user XP required
    total_xp = db.Column(db.Float, default=0)  # user total XP
    level = db.Column(db.Integer, default=1)  # user level

    def add_xp(self, amount):  # add XP
        self.xp += amount  # add XP by amount
        self.total_xp += amount  # add total XP by amount
        self.check_level_up()  # check if user has leveled up

    def check_level_up(self):  # check if user has leveled up
        while (
            self.xp >= self.xp_required
        ):  # if user XP is greater than or equal to XP required
            self.xp -= self.xp_required
            self.xp_required = round(
                self.xp_required + self.xp_required * 1 / math.sqrt(self.level)
            )  # increase XP required exponentially with slower growth at higher levels
            self.level += 1  # increase level


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)  # task id
    name = db.Column(db.String(80))  # task name
    completed = db.Column(db.Boolean, default=False)  # is task completed
    user_id = db.Column(
        db.Integer, db.ForeignKey(User.__tablename__ + ".id")
    )  # user id
    user = db.relationship("User", backref=db.backref("tasks", lazy=True))  # user


@app.route("/")
def index():  # get index page template
    tasks = Task.query.all()  # get list of tasks
    user = User.query.first()  # get first user
    return render_template(
        "index.html", tasks=tasks, user=user
    )  # redirect to index page template


@app.route("/add", methods=["POST"])
def add_task():  # add task to task list
    name = request.form.get("name")  # get name from request form
    user = User.query.first()  # get first user
    if user:
        new_task = Task(name=name, user_id=user.id)
        db.session.add(new_task)  # add new task to task list
        db.session.commit()  # commit database changes
    return redirect(url_for("index"))  # redirect to index page template


@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):  # complete task from task id
    task = Task.query.get(task_id)  # get task by task id
    if task:
        task.completed = True  # complete the task
        user = User.query.first()  # get first user
        if user:
            user.add_xp(1)  # add XP
            db.session.commit()  # commit database changes
    return redirect(url_for("index"))  # redirect to index page template


def init_db():  # initialize database
    with app.app_context():
        db.create_all()  # create tables if they don't exist
        if User.query.count() == 0:  # if there is no users
            new_user = User(username="Player")  # create new user
            db.session.add(new_user)  # add new user to database
            db.session.commit()  # commit database changes


if __name__ == "__main__":
    init_db()  # initialize database
    app.run(debug=True, port=8081)  # run the server at port 8081
