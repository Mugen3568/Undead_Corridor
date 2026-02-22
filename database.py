import sqlite3
from resource_helper import get_persistent_path

class Database:
    def __init__(self, db_name=None):
        if db_name is None:
            self.db_name = get_persistent_path("scores.db")
        else:
            self.db_name = db_name
        self.create_table()

    def create_table(self):
        """ Creates the table if it doesn't exist """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                level INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def add_score(self, name, score, level):
        """ Saves a new score """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO leaderboard (name, score, level) VALUES (?, ?, ?)", (name, score, level))
        conn.commit()
        conn.close()

    def get_top_scores(self, level=None, limit=10):
        """ Returns the top scores, optionally filtered by level """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if level is not None:
            cursor.execute("SELECT name, score FROM leaderboard WHERE level = ? ORDER BY score DESC LIMIT ?", (level, limit))
        else:
            cursor.execute("SELECT name, score, level FROM leaderboard ORDER BY score DESC LIMIT ?", (limit,))
        data = cursor.fetchall()
        conn.close()
        return data
