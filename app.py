from datetime import datetime
import math
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True,
                   unique=True, nullable=False)  # user id
    username = db.Column(db.String(80), unique=True,
                         nullable=False)  # username
    xp = db.Column(db.Float, default=0, nullable=False)  # user XP
    xp_required = db.Column(db.Float, default=1,
                            nullable=False)  # user XP required
    total_xp = db.Column(db.Float, default=0, nullable=False)  # user total XP
    level = db.Column(db.Integer, default=1, nullable=False)  # user level

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
    id = db.Column(db.Integer, primary_key=True,
                   unique=True, nullable=False)  # task id
    name = db.Column(db.String(80), nullable=False)  # task name
    due_date = db.Column(
        db.Date, default=datetime.now().date(), nullable=False
    )  # task due date
    priority = db.Column(db.Integer, default=1,
                         nullable=False)  # task priority
    completed = db.Column(
        db.Boolean, default=False, nullable=False
    )  # is task completed
    user_id = db.Column(
        db.Integer, db.ForeignKey(User.__tablename__ + ".id")
    )  # user id
    user = db.relationship(
        "User", backref=db.backref("tasks", lazy=True))  # user


@app.template_filter("short_numeric")  # short numeric filter
# get number in short numeric form with abbreviations
def short_numeric_filter(value):
    """
    Get the abbreviated numeric value.
    value - the numeric value to convert.
    """
    units = [
        "",
        "K",
        "M",
        "B",
        "T",
        "Qa",
        "Qi",
        "Sx",
        "Sp",
        "O",
        "N",
        "D",
        "UD",
        "DD",
        "TD",
        "QaD",
        "QiD",
        "SxD",
        "SpD",
        "OD",
        "ND",
        "V",
    ]  # list of units with abbreviations
    exponent = 0
    mantissa = value  # mantissa value from 1 to 999
    while mantissa >= 1000:  # repeat until mantissa is within 1 to 999
        mantissa /= 1000
        exponent += 1
    return (
        f"{mantissa:.3g}{units[exponent]}" if value >= 1000 else f"{value:.0f}"
    )  # print abbreviated output


# add filter to Jinja
app.jinja_env.filters["short_numeric"] = short_numeric_filter


@app.route("/")
def index():  # get index page template
    tasks = Task.query.order_by(
        Task.due_date
    ).all()  # get list of tasks sorted by due date
    user = User.query.first()  # get first user
    # get today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        "index.html", tasks=tasks, user=user, today=today
    )  # redirect to index page template


@app.route("/add", methods=["POST"])
def add_task():  # add task to task list
    name = request.form.get("name")  # get name from request form
    due_date = request.form.get("due_date")  # get due date
    priority = int(request.form.get("priority"))  # get priority
    user = User.query.first()  # get first user
    if user:
        new_task = Task(
            name=name,
            user_id=user.id,
            priority=priority,
            due_date=datetime.strptime(due_date, "%Y-%m-%d"),
        )
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
            user.add_xp(round(task.priority))  # add XP
            db.session.commit()  # commit database changes
    return redirect(url_for("index"))  # redirect to index page template


def init_db():  # initialize database
    with app.app_context():
        db.create_all()  # create tables if they don't exist
        if User.query.count() == 0:  # if there is no users
            new_user = User(username="Player")  # create new user
            db.session.add(new_user)  # add new user to database
            db.session.commit()  # commit database changes
        if "due_date" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if due date column is not in task table
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN due_date DATE NOT NULL")
            )  # create due date column
        if "priority" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if priority column is not in task table
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN priority INT NOT NULL")
            )  # create priority column
        tasks = Task.query.all()  # get list of tasks
        for task in tasks:  # repeat for each task
            if task.due_date is None:  # check if task due date is none
                task.due_date = (
                    datetime.now().date()
                )  # set task due date to today's date
            if task.priority is None:  # check if task priority is none
                task.priority = 1  # set task priority to low
        db.session.commit()  # commit database changes


if __name__ == "__main__":
    init_db()  # initialize database
    app.run(debug=True, port=8081)  # run the server at port 8081
