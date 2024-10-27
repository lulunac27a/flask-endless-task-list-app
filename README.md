# Flask Endless Task List Application with Levels and Experience Points (XP)

This app is an endless task list application with levels and experience points (XP). It uses SQLAlchemy to store user and task list data to the database.

## Getting Started

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Set `SECRET_KEY` environment variable. On Windows: use `setx` command in Command Prompt like `setx SECRET_KEY "your_secret_key"`. On macOS and Linux: use `export` command in terminal like `export SECRET_KEY="your_secret_key"`.
4. Run the app: `python app.py`.
5. Open `localhost:8081` on your web browser.