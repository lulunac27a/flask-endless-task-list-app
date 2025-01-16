import calendar
from datetime import datetime, timedelta, date
import math
import os
from typing import Union
from flask import Flask, flash, render_template, request, redirect, url_for
from flask_migrate import Migrate as MigrateClass
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from sqlalchemy.orm import Mapped
from werkzeug.wrappers import Response


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ['SECRET_KEY']
db = SQLAlchemy(app)
migrate_instance = MigrateClass(app, db)


class User(db.Model):
    id: int = db.Column(db.Integer, primary_key=True,
                        unique=True, nullable=False)  # user id
    username: str = db.Column(
        db.String(80), unique=True, nullable=False)  # username
    xp: float = db.Column(db.Float, default=0, server_default=text(
        '0'), nullable=False)  # user XP
    xp_required: float = db.Column(db.Float, default=1, server_default=text(
        '1'), nullable=False)  # user XP required
    total_xp: float = db.Column(db.Float, default=0, server_default=text(
        '0'), nullable=False)  # user total XP
    level: int = db.Column(db.Integer, default=1, server_default=text(
        '1'), nullable=False)  # user level
    tasks_completed: int = db.Column(db.Integer, default=0, server_default=text(
        '0'), nullable=False)  # number of times tasks has completed
    last_completion_date: date = db.Column(db.Date, default=func.current_date(
    ), server_default=func.current_date(), nullable=False)  # user last task completion date
    daily_streak: int = db.Column(db.Integer, default=0, server_default=text(
        '0'), nullable=False)  # user daily task streak
    daily_tasks_completed: int = db.Column(db.Integer, default=0, server_default=text(
        '0'), nullable=False)  # user number of tasks completed in a day
    days_completed: int = db.Column(db.Integer, default=0, server_default=text(
        '0'), nullable=False)  # user days completed with tasks
    combo_multiplier: int = db.Column(db.Integer, default=0, server_default=text(
        '0'), nullable=False)  # user XP multiplier for combo
    last_task_completed: int = db.Column(
        db.Integer, default=-1, server_default=text('-1'), nullable=False)  # user last task completion ID

    def add_xp(self, amount: float) -> None:  # add XP
        self.xp += amount  # add XP by amount
        self.total_xp += amount  # add total XP by amount
        # display message with the amount of XP earned
        flash('Task completed! You gained ' +
              short_numeric_filter(amount) + ' XP!')
        self.check_level_up()  # check if user has leveled up

    def check_level_up(self) -> None:  # check if user has leveled up
        while self.xp >= self.xp_required:  # if user XP is greater than or equal to XP required
            self.xp -= self.xp_required
            # increase XP required exponentially with slower growth at higher levels
            self.xp_required = max(1.0, round(
                self.xp_required + max(1.0, self.xp_required * 1.0 / math.sqrt(self.level))))
            self.level += 1  # increase level


class Task(db.Model):
    id: int = db.Column(db.Integer, primary_key=True,
                        unique=True, nullable=False)  # task id
    name: str = db.Column(db.String(80), nullable=False)  # task name
    original_due_date: date = db.Column(db.Date, default=func.current_date(
    ), server_default=func.current_date(), nullable=False)  # task due date
    due_date: date = db.Column(db.Date, default=func.current_date(
    ), server_default=func.current_date(), nullable=False)  # task due date
    priority: int = db.Column(db.Integer, default=1, server_default=text(
        '1'), nullable=False)  # task priority
    difficulty: int = db.Column(db.Integer, default=1, server_default=text(
        '1'), nullable=False)  # task difficulty
    repeat_interval: int = db.Column(db.Integer, default=1, server_default=text(
        '1'), nullable=False)  # task repeat interval
    repeat_often: int = db.Column(db.Integer, default=5, server_default=text(
        '5'), nullable=False)  # task repeat often
    times_completed: int = db.Column(db.Integer, default=0, server_default=text(
        '0'), nullable=False)  # number of times tasks has completed
    streak: int = db.Column(db.Integer, default=0, server_default=text(
        '0'), nullable=False)  # task streak
    completed: bool = db.Column(db.Boolean, default=False, server_default=text(
        '0'), nullable=False)  # is task completed
    user_id: int = db.Column(db.Integer, db.ForeignKey(
        User.__tablename__ + '.id'))  # user id
    user: Mapped['User'] = db.relationship(
        'User', backref=db.backref('tasks', lazy=True))  # user relationship


@app.template_filter('short_numeric')  # short numeric filter
# get number in short numeric form with abbreviations
def short_numeric_filter(value: Union[int, float]) -> str:
    '''
    Get the abbreviated numeric value.
    value - the numeric value to convert.
    '''
    units: list[str] = ['', 'K', 'M', 'B', 'T', 'Qa', 'Qi', 'Sx', 'Sp', 'O', 'N', 'D', 'UD',
                        'DD', 'TD', 'QaD', 'QiD', 'SxD', 'SpD', 'OD', 'ND', 'V']  # list of units with abbreviations
    exponent = 0
    mantissa: Union[int, float] = value  # mantissa value from 1 to 999
    while mantissa >= 1000:  # repeat until mantissa is within 1 to 999
        mantissa /= 1000
        exponent += 1
    # print abbreviated output
    return f'{mantissa:.3g}{units[exponent]}' if value >= 1000 else f'{value:.0f}'


# add filter to Jinja
app.jinja_env.filters['short_numeric'] = short_numeric_filter


@app.route('/')
def index() -> str:  # get index page template
    # get the list of tasks sorted by due date
    tasks: list = Task.query.order_by(Task.due_date).all()
    user: Union[User, None] = User.query.first()  # get first user
    # get today's date in YYYY-MM-DD format
    today: str = datetime.now().strftime('%Y-%m-%d')
    # redirect to index page template
    return render_template('index.html', tasks=tasks, user=user, today=today)


@app.route('/add', methods=['POST'])
def add_task() -> Response:  # add the task to the task list
    name: str = request.form.get('name')  # get name from request form
    due_date: str = request.form.get('due_date')  # get due date
    priority = int(request.form.get('priority'))  # get priority
    difficulty = int(request.form.get('difficulty'))  # get difficulty
    # get task repeat interval
    repeat_interval = int(request.form.get('repeat_interval'))
    repeat_often = int(request.form.get('repeat_often')
                       )  # get task repeat often
    user: Union[User, None] = User.query.first()  # get first user
    if user:
        new_task = Task(name=name, user_id=user.id, priority=priority, difficulty=difficulty, repeat_interval=repeat_interval, repeat_often=repeat_often, original_due_date=datetime.strptime(
            due_date, '%Y-%m-%d').date(), due_date=datetime.strptime(due_date, '%Y-%m-%d').date())  # create the new task with input parameters
        db.session.add(new_task)  # add the new task to task list
        db.session.commit()  # commit database changes
    return redirect(url_for('index'))  # redirect to index page template


@app.route('/complete_task/<int:task_id>')
def complete_task(task_id) -> Response:  # complete task from task id
    task = Task.query.get(task_id)  # get task by task id
    if task:
        due_multiplier: float = 1.0  # set default due multiplier to 1
        if task.repeat_often == 5:  # if the task is a one-time task
            task.completed = True  # complete the task
        else:  # if task is repeatable
            task.times_completed += 1  # increase times task completed by 1
            task.due_date = calculate_next_recurring_event(
                task.original_due_date, task.times_completed, task.repeat_interval, task.repeat_often)  # calculate the next task due date
            # calculate the number of days until the task is due
            days_to_due: int = (task.due_date - date.today()).days
            if days_to_due > 0:  # if task due date is after today
                # set due multiplier that increases over time when the task is closer to due date
                due_multiplier: float = 1 + 1 / (days_to_due + 1)
            # if the task is overdue (current date is after task due date)
            elif days_to_due < 0:
                # set due multiplier that decreases over time when the task is overdue
                due_multiplier = -2 / (days_to_due - 1)
            elif days_to_due == 0:  # if task due date is today
                next_midnight: datetime = datetime.combine(
                    datetime.now().date() + timedelta(days=1), datetime.min.time())
                # set due multiplier to 2 and increases over time to 4 at midnight
                due_multiplier = 4 / \
                    (1 + (next_midnight - datetime.now()) / timedelta(days=1))
            if date.today() > task.due_date:  # check if the task is overdue (current date is after task due date)
                task.streak = 0  # reset streak to 0
            else:
                task.streak += 1  # increase streak by 1
        if task.repeat_often == 1:  # if the task repetition interval is daily
            if task.repeat_interval < 7:  # 7 days is 1 week
                # 1x XP multiplier for daily tasks (1 day) to 2x XP multiplier for weekly tasks (7 days)
                repeat_multiplier: float = 1 + \
                    (task.repeat_interval - 1) / (7 - 1)
            elif task.repeat_interval < 30:  # approximately 30 days is 1 month
                # 2x XP multiplier for weekly tasks (7 days) to 3x XP multiplier for monthly tasks (approximately 30 days)
                repeat_multiplier = 2 + (task.repeat_interval - 7) / (30 - 7)
            elif task.repeat_interval < 365:  # approximately 365 days is 1 year
                # 3x XP multiplier for monthly tasks (approximately 30 days) to 4x XP multiplier for yearly tasks (approximately 365 days)
                repeat_multiplier = 3 + \
                    (task.repeat_interval - 30) / (365 - 30)
            else:
                # 4x XP multiplier for yearly tasks (approximately 365 days) to 5x XP multiplier for one-time tasks
                repeat_multiplier = 5 - 365 / task.repeat_interval
        elif task.repeat_often == 2:  # if the task repetition interval is weekly
            if task.repeat_interval < 4:  # approximately 4 weeks is 1 month
                # 2x XP multiplier for weekly tasks (1 week) to 3x XP multiplier for monthly tasks (approximately 4 weeks)
                repeat_multiplier = 2 + (task.repeat_interval - 1) / (4 - 1)
            elif task.repeat_interval < 52:  # approximately 52 weeks is 1 year
                # 3x XP multiplier for monthly tasks (approximately 4 weeks) to 4x XP multiplier for yearly tasks (approximately 52 weeks)
                repeat_multiplier = 3 + (task.repeat_interval - 4) / (52 - 4)
            else:
                # 4x XP multiplier for yearly tasks (approximately 52 weeks) to 5x XP multiplier for one-time tasks
                repeat_multiplier = 5 - 52 / task.repeat_interval
        elif task.repeat_often == 3:  # if the task repetition interval is monthly
            if task.repeat_interval < 12:  # 12 months is 1 year
                # 3x XP multiplier for monthly tasks (1 month) to 4x XP multiplier for yearly tasks (12 months)
                repeat_multiplier = 3 + (task.repeat_interval - 1) / (12 - 1)
            else:
                # 4x XP multiplier for yearly tasks (12 months) to 5x XP multiplier for one-time tasks
                repeat_multiplier = 5 - 12 / task.repeat_interval
        elif task.repeat_often == 4:  # if the task repetition interval is yearly
            # 4x XP multiplier for yearly tasks (1 year) to 5x XP multiplier for one-time tasks
            repeat_multiplier = 5 - 1 / task.repeat_interval
        else:  # if the task repetition interval is one-time
            repeat_multiplier = 5  # get 5x XP multiplier for one-time tasks
        user: Union[User, None] = User.query.first()  # get first user
        # get number of active tasks (tasks that are not completed)
        active_tasks: int = Task.query.filter_by(completed=False).count()
        if user:
            user.tasks_completed += 1  # increase the number of tasks completed by 1
            day_difference = datetime.now() - datetime(user.last_completion_date.year,
                                                       user.last_completion_date.month, user.last_completion_date.day)  # calculate difference in days
            if (day_difference.days == 1):  # if a new day has passed
                user.daily_streak += 1  # increase the daily streak by 1
                user.daily_tasks_completed = 1  # reset the number of tasks completed in a day to 1
                user.days_completed += 1  # increase days completed by 1
            elif (day_difference.days > 1):  # if more than a day has passed
                user.daily_streak = 1  # reset the daily streak to 1
                user.daily_tasks_completed = 1  # reset the number of tasks completed in a day to 1
                user.days_completed += 1  # increase days completed by 1
            else:
                # increase the number of tasks completed in a day by 1
                user.daily_tasks_completed += 1
            # set user last completion date to today
            user.last_completion_date = datetime.now()
            if task.id == user.last_task_completed:  # if the task is the last task completed
                user.combo_multiplier += 1  # increase combo multipler by 1
            else:
                user.combo_multiplier = 0  # reset combo multiplier to 0
            user.last_task_completed = task.id  # set user last task completed to task id
            user.add_xp(round(task.priority * task.difficulty * task.repeat_often * repeat_multiplier * (1 + math.log(max(task.times_completed, 1))) * (1 + math.log(max(user.tasks_completed, 1))) * (1 + math.log(max(active_tasks, 1))) * (
                1 + user.daily_streak / 10) * (1 + user.daily_tasks_completed / 10) * (1 + math.log(max(user.days_completed, 1))) * (1 + task.streak / 10) * due_multiplier * (1 + user.combo_multiplier / 10)) + user.combo_multiplier)  # add XP
            db.session.commit()  # commit database changes
    return redirect(url_for('index'))  # redirect to index page template


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id) -> Response:  # delete task from task id
    task: Union[Task, None] = Task.query.get(task_id)  # get task by task id
    if task:
        db.session.delete(task)  # delete task from task list
        db.session.commit()  # commit database changes
    return redirect(url_for('index'))  # redirect to index page template


# calculate the next recurring event date
def calculate_next_recurring_event(original_date: date, times_completed: int, repeat_interval: int, repeat_often: int) -> date:
    if repeat_often == 1:  # if task repeat often is daily
        # add days to the original date
        return original_date + timedelta(days=repeat_interval * times_completed)
    elif repeat_often == 2:  # if task repeat often is weekly
        # add weeks to the original date
        return original_date + timedelta(weeks=repeat_interval * times_completed)
    elif repeat_often == 3:  # if task repeat often is monthly
        new_month: int = original_date.month + \
            repeat_interval * times_completed  # get new month
        new_year: int = original_date.year + \
            (new_month - 1) // 12  # get new year
        # clamp month from 1 (January) to 12 (December)
        new_month = (new_month - 1) % 12 + 1
        max_days_in_month = calendar.monthrange(new_year, new_month)[
            1]  # get number of days in month
        # add months to the original date
        return date(new_year, new_month, min(original_date.day, max_days_in_month))
    elif repeat_often == 4:  # if task repeat often is yearly
        new_year = original_date.year + repeat_interval * times_completed
        max_days_in_month = calendar.monthrange(new_year, original_date.month)[
            1]  # get number of days in month
        # add years in original date
        return date(new_year, original_date.month, min(original_date.day, max_days_in_month))
    else:
        # return original task due date
        return date(original_date.year, original_date.month, original_date.day)


def init_db() -> None:  # initialize database
    with app.app_context():
        db.create_all()  # create tables if they don't exist
        # check if tasks completed column is not in the user table
        if 'tasks_completed' not in [column['name'] for column in db.inspect(db.engine).get_columns('user')]:
            # create tasks completed column
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN tasks_completed INT NOT NULL DEFAULT 0"))
        # check if the last completion date column is not in the user table
        if 'last_completion_date' not in [column['name'] for column in db.inspect(db.engine).get_columns('user')]:
            # create last completion date column
            db.session.execute(text(
                "ALTER TABLE user ADD COLUMN last_completion_date DATE NOT NULL DEFAULT CURRENT_DATE"))
            db.session.commit()  # commit database changes
        # check if tasks completed column is not in the user table
        if 'daily_streak' not in [column['name'] for column in db.inspect(db.engine).get_columns('user')]:
            # create tasks completed column
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN daily_streak INT NOT NULL DEFAULT 1"))
        # check if daily tasks completed column is not in the user table
        if 'daily_tasks_completed' not in [column['name'] for column in db.inspect(db.engine).get_columns('user')]:
            # create daily tasks completed column
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN daily_tasks_completed INT NOT NULL DEFAULT 0"))
        # check if days completed column is not in the user table
        if 'days_completed' not in [column['name'] for column in db.inspect(db.engine).get_columns('user')]:
            # create days completed column
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN days_completed INT NOT NULL DEFAULT 1"))
        # check if combo multiplier column is not in the user table
        if 'combo_multiplier' not in [column['name'] for column in db.inspect(db.engine).get_columns('user')]:
            # create combo multiplier column
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN combo_multiplier INT NOT NULL DEFAULT 0"))
        # check if last task completed column is not in the user table
        if 'last_task_completed' not in [column['name'] for column in db.inspect(db.engine).get_columns('user')]:
            # create last task completed column
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN last_task_completed INT NOT NULL DEFAULT -1"))
        if User.query.count() == 0:  # if there are no users
            new_user = User(username='Player')  # create new user
            db.session.add(new_user)  # add new user to the database
            db.session.commit()  # commit database changes
        # check if the original due date column is not in the task table
        if 'original_due_date' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create original due date column
            db.session.execute(text(
                "ALTER TABLE task ADD COLUMN original_due_date DATE NOT NULL DEFAULT CURRENT_DATE"))
            db.session.commit()  # commit database changes
        # check if due date column is not in the task table
        if 'due_date' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create due date column
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN due_date DATE NOT NULL DEFAULT CURRENT_DATE"))
            db.session.commit()  # commit database changes
        # check if priority column is not in the task table
        if 'priority' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create priority column
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN priority INT NOT NULL DEFAULT 1"))
        # check if difficulty column is not in the task table
        if 'difficulty' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create difficulty column
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN difficulty INT NOT NULL DEFAULT 1"))
        # check if repeat interval column is not in the task table
        if 'repeat_interval' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create repeat interval column
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN repeat_interval INT NOT NULL DEFAULT 1"))
        # check if repeat often column is not in the task table
        if 'repeat_often' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create repeat often column
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN repeat_often INT NOT NULL DEFAULT 5"))
        # check if times completed column is not in the task table
        if 'times_completed' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create times completed column
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN times_completed INT NOT NULL DEFAULT 0"))
        # check if streak column is not in the task table
        if 'streak' not in [column['name'] for column in db.inspect(db.engine).get_columns('task')]:
            # create streak column
            db.session.execute(
                text("ALTER TABLE task ADD COLUMN streak INT NOT NULL DEFAULT 0"))
        tasks: list = Task.query.all()  # get the list of tasks
        for task in tasks:  # repeat for each task
            if task.original_due_date is None:  # check if task original due date is none
                # set task original due date to today's date
                task.original_due_date = date.today()
            if task.due_date is None:  # check if task due date is none
                task.due_date = date.today()  # set task due date to today's date
            if task.priority is None:  # check if task priority is none
                task.priority = 1  # set task priority to low
            if task.difficulty is None:  # check if task difficulty is none
                task.difficulty = 1  # set task difficulty to low
            if task.repeat_interval is None:  # check if the repeat interval is none
                task.repeat_interval = 1  # set repeat interval to 1
            if task.repeat_often is None:  # check if repeat often is none
                task.repeat_often = 1  # set repeat often to once
        db.session.commit()  # commit database changes


if __name__ == '__main__':
    init_db()  # initialize database
    app.run(debug=True, port=8081)  # run the server at port 8081
