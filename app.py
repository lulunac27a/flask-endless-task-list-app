import calendar
from datetime import datetime, timedelta
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
    original_due_date = db.Column(
        db.Date, default=datetime.now().date(), nullable=False
    )  # task due date
    due_date = db.Column(
        db.Date, default=datetime.now().date(), nullable=False
    )  # task due date
    priority = db.Column(db.Integer, default=1,
                         nullable=False)  # task priority
    difficulty = db.Column(db.Integer, default=1,
                           nullable=False)  # task difficulty
    repeat_interval = db.Column(
        db.Integer, default=1, nullable=False
    )  # task repeat interval
    repeat_often = db.Column(db.Integer, default=5,
                             nullable=False)  # task repeat often
    times_completed = db.Column(
        db.Integer, default=0, nullable=False
    )  # number if times task has completed
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
    difficulty = int(request.form.get("difficulty"))  # get difficulty
    repeat_interval = int(
        request.form.get("repeat_interval")
    )  # get task repeat interval
    repeat_often = int(request.form.get("repeat_often")
                       )  # get task repeat often
    user = User.query.first()  # get first user
    if user:
        new_task = Task(
            name=name,
            user_id=user.id,
            priority=priority,
            difficulty=difficulty,
            repeat_interval=repeat_interval,
            repeat_often=repeat_often,
            original_due_date=datetime.strptime(due_date, "%Y-%m-%d"),
            due_date=datetime.strptime(due_date, "%Y-%m-%d"),
        )  # create new task with input parameters
        db.session.add(new_task)  # add new task to task list
        db.session.commit()  # commit database changes
    return redirect(url_for("index"))  # redirect to index page template


@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):  # complete task from task id
    task = Task.query.get(task_id)  # get task by task id
    if task:
        if task.repeat_often == 5:  # if task is one-time task
            task.completed = True  # complete the task
        else:  # if task is repeatable
            task.times_completed += 1  # increase times task completed by 1
        task.due_date = calculate_next_recurring_event(
            task.original_due_date,
            task.times_completed,
            task.repeat_interval,
            task.repeat_often,
        )  # calculate next task due date
        if task.repeat_often == 1:  # if the task repetition interval is daily
            if task.repeat_interval < 7:  # 7 days is 1 week
                repeat_multiplier = 1 + (task.repeat_interval - 1) / (
                    7 - 1
                )  # 1x XP multiplier for daily tasks (1 day) to 2x XP multiplier for weekly tasks (7 days)
            elif task.repeat_interval < 30:  # approximately 30 days is 1 month
                repeat_multiplier = 2 + (task.repeat_interval - 7) / (
                    30 - 7
                )  # 2x XP multiplier for weekly tasks (7 days) to 3x XP multiplier for monthly tasks (approximately 30 days)
            elif task.repeat_interval < 365:  # approximately 365 days is 1 year
                repeat_multiplier = 3 + (task.repeat_interval - 30) / (
                    365 - 30
                )  # 3x XP multiplier for monthly tasks (approximately 30 days) to 4x XP multiplier for yearly tasks (approximately 365 days)
            else:
                repeat_multiplier = (
                    5 - 365 / task.repeat_interval
                )  # 4x XP multiplier for yearly tasks (approximately 365 days) to 5x XP multiplier for one-time tasks
        elif task.repeat_often == 2:  # if the task repetition interval is weekly
            if task.repeat_interval < 4:  # approximately 4 weeks is 1 month
                repeat_multiplier = 2 + (task.repeat_interval - 1) / (
                    4 - 1
                )  # 2x XP multiplier for weekly tasks (1 week) to 3x XP multiplier for monthly tasks (approximately 4 weeks)
            elif task.repeat_interval < 52:  # approximately 52 weeks is 1 year
                repeat_multiplier = 3 + (task.repeat_interval - 4) / (
                    52 - 4
                )  # 3x XP multiplier for monthly tasks (approximately 4 weeks) to 4x XP multiplier for yearly tasks (approximately 52 weeks)
            else:
                repeat_multiplier = (
                    5 - 52 / task.repeat_interval
                )  # 4x XP multiplier for yearly tasks (approximately 52 weeks) to 5x XP multiplier for one-time tasks
        elif task.repeat_often == 3:  # if the task repetition interval is monthly
            if task.repeat_interval < 12:  # 12 months is 1 year
                repeat_multiplier = 3 + (task.repeat_interval - 1) / (
                    12 - 1
                )  # 3x XP multiplier for monthly tasks (1 month) to 4x XP multiplier for yearly tasks (12 months)
            else:
                repeat_multiplier = (
                    5 - 12 / task.repeat_interval
                )  # 4x XP multiplier for yearly tasks (12 months) to 5x XP multiplier for one-time tasks
        elif task.repeat_often == 4:  # if the task repetition interval is yearly
            repeat_multiplier = (
                5 - 1 / task.repeat_interval
            )  # 4x XP multiplier for yearly tasks (1 year) to 5x XP multiplier for one-time tasks
        else:  # if the task repetition interval is one-time
            repeat_multiplier = 5  # get 5x XP multiplier for one-time tasks
        user = User.query.first()  # get first user
        if user:
            user.add_xp(
                round(
                    task.priority
                    * task.difficulty
                    * task.repeat_often
                    * repeat_multiplier
                    * (1 + math.log(max(task.times_completed, 1)))
                )
            )  # add XP
            db.session.commit()  # commit database changes
    return redirect(url_for("index"))  # redirect to index page template


@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):  # delete task from task id
    task = Task.query.get(task_id)  # get task by task id
    if task:
        db.session.delete(task)  # delete task from task list
        db.session.commit()  # commit database changes
    return redirect(url_for("index"))  # redirect to index page template


def calculate_next_recurring_event(
    original_date, times_completed, repeat_interval, repeat_often
):  # calculate next recurring event date
    if repeat_often == 1:  # if task repeat often is daily
        return original_date + timedelta(
            days=repeat_interval * times_completed
        )  # add days to original date
    elif repeat_often == 2:  # if task repeat often is weekly
        return original_date + timedelta(
            weeks=repeat_interval * times_completed
        )  # add weeks to original date
    elif repeat_often == 3:  # if task repeat often is monthly
        new_month = (
            original_date.month + repeat_interval * times_completed
        )  # get new month
        new_year = original_date.year + (new_month - 1) // 12  # get new year
        new_month = (
            new_month - 1
        ) % 12  # clamp month from 1 (January) to 12 (December)
        max_days_in_month = calendar.monthrange(new_year, new_month)[
            1
        ]  # get number of days in month
        return datetime(
            new_year, new_month, min(original_date.day, max_days_in_month)
        )  # add months to original date
    elif repeat_often == 4:  # if task repeat often is yearly
        new_year = original_date.year + repeat_interval * times_completed
        max_days_in_month = calendar.monthrange(new_year, original_date.month)[
            1
        ]  # get number of days in month
        return datetime(
            new_year, original_date.month, min(
                original_date.day, max_days_in_month)
        )  # add years in original date
    else:
        return None


def init_db():  # initialize database
    with app.app_context():
        db.create_all()  # create tables if they don't exist
        today = datetime.now().strftime(
            "%Y-%m-%d"
        )  # get today's date in YYYY-MM-DD format
        if User.query.count() == 0:  # if there is no users
            new_user = User(username="Player")  # create new user
            db.session.add(new_user)  # add new user to database
            db.session.commit()  # commit database changes
        if "original_due_date" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if original due date column is not in task table
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN original_due_date DATE")
            )  # create original due date column
            db.session.execute(
                text("UPDATE task SET original_due_date = ?"), (today)
            )  # update existing rows
            db.session.commit()  # commit database changes
            db.session.execute(
                text("ALTER TABLE task ALTER COLUMN original_due_date SET NOT NULL")
            )  # set column to not null
            db.session.commit()  # commit database changes
        if "due_date" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if due date column is not in task table
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN due_date DATE")
            )  # create due date column
            db.session.execute(
                text("UPDATE task SET due_date = ?"), (today)
            )  # update existing rows
            db.session.commit()  # commit database changes
            db.session.execute(
                text("ALTER TABLE task ALTER COLUMN due_date SET NOT NULL")
            )  # set column to not null
            db.session.commit()  # commit database changes
        if "priority" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if priority column is not in task table
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN priority INT NOT NULL DEFAULT 1")
            )  # create priority column
        if "difficulty" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if difficulty column is not in task table
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN difficulty INT NOT NULL DEFAULT 1")
            )  # create difficulty column
        if "repeat_interval" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if repeat interval column is not in task table
            db.session.execute(
                text(
                    "ALTER TABLE task ADD COLUMN repeat_interval INT NOT NULL DEFAULT 1"
                )
            )  # create repeat interval column
        if "repeat_often" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if repeat often column is not in task table
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN repeat_often INT NOT NULL DEFAULT 5")
            )  # create repeat often column
        if "times_completed" not in [
            column["name"] for column in db.inspect(db.engine).get_columns("task")
        ]:  # check if times completed column is not in task table
            db.session.execute(
                text(
                    "ALTER TABLE task ADD COLUMN times_completed INT NOT NULL DEFAULT 0"
                )
            )  # create times completed column
        tasks = Task.query.all()  # get list of tasks
        for task in tasks:  # repeat for each task
            if (
                task.original_due_date is None
            ):  # check if task original due date is none
                task.original_due_date = (
                    datetime.now().date()
                )  # set task original due date to today's date
            if task.due_date is None:  # check if task due date is none
                task.due_date = (
                    datetime.now().date()
                )  # set task due date to today's date
            if task.priority is None:  # check if task priority is none
                task.priority = 1  # set task priority to low
            if task.difficulty is None:  # check if task difficulty is none
                task.difficulty = 1  # set task difficulty to low
            if task.repeat_interval is None:  # check if repeat interval is none
                task.repeat_interval = 1  # set repeat interval to 1
            if task.repeat_often is None:  # check if repeat often is none
                task.repeat_often = 1  # set repeat often to once
        db.session.commit()  # commit database changes


if __name__ == "__main__":
    init_db()  # initialize database
    app.run(debug=True, port=8081)  # run the server at port 8081
