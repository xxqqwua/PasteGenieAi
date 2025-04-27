import sqlite3

import logging
import logging_config

logger = logging.getLogger(__name__)


class DBManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None

    def connect(self):
        logger.debug(f"Connecting to database {self.db_name}")
        self.conn = sqlite3.connect(self.db_name)

    # --------- User Staff ---------
    def create_user(self, user_discord_id, user_discord_name):
        logger.info(f"Creating user '{user_discord_id}' in database")
        cursor = self.conn.cursor()
        cursor.execute("INSERT into users (user_discord_id, name) VALUES (?, ?)", (user_discord_id, user_discord_name))
        self.conn.commit()

    def is_exist(self, user_discord_id):
        logger.info(f"Checking if user '{user_discord_id}' exists in database")
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_discord_id = ?", (user_discord_id,))
        exists = cursor.fetchone()
        logger.debug(f"User '{user_discord_id}' exists {exists is not None}")
        return exists is not None

    def get_user_database_id(self, user_discord_id):
        logger.info(f"Getting user id from '{user_discord_id}' in database")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE user_discord_id = ?", (user_discord_id,))
        user_database_id = cursor.fetchone()
        logger.debug(f"User '{user_discord_id}' has id {user_database_id}")
        return user_database_id

    def get_user_name(self, user_database_id):
        logger.info(f"Getting user name from '{user_database_id}' in database")
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM users WHERE id = ?", (user_database_id,))
        user_name = cursor.fetchone()
        logger.debug(f"User '{user_database_id}' has name {user_name}")
        return user_name

    def search_user_by_name(self, name_to_search):
        # logger
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE name = ?", (name_to_search,))
        user_database_id = cursor.fetchone()
        return user_database_id

    # --------- paste staff ---------
    def uniqueness_check(self, paste_content, is_ai=True):
        logger.info(f"Checking if paste with content {paste_content[:100]} exists in database")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute("SELECT 1 FROM pastes WHERE content = ?", (paste_content,))
        else:
            cursor.execute("SELECT 1 FROM custom_pastes WHERE content = ?", (paste_content,))
        exists = cursor.fetchone()
        logger.debug(f"Paste with content {paste_content[:100]} exists {exists is not None}")
        return exists is not None

    def create_paste(self, user_id, paste_content, idea, is_ai=True):
        logger.info(f"Creating paste for user {user_id} with content {paste_content[:99]}")
        cursor = self.conn.cursor()
        if is_ai or idea is not None:
            cursor.execute(
                "INSERT INTO pastes (user_database_id, content, idea) VALUES (?, ?, ?)", (user_id, paste_content, idea))
        else:
            cursor.execute(
                "INSERT INTO custom_pastes (user_database_id, content) VALUES (?, ?)", (user_id, paste_content))
        self.conn.commit()
        return cursor.lastrowid

    def update_paste(self, paste_id, new_content):
        logger.info(f"Updating paste {paste_id} with new content {new_content[:100]}")
        cursor = self.conn.cursor()
        cursor.execute("UPDATE pastes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                       (new_content, paste_id))
        self.conn.commit()

    def get_last_paste_id(self, is_ai=True):
        logger.info(f"Getting last paste id from database")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute("SELECT id FROM pastes ORDER BY id DESC LIMIT 1")
        else:
            cursor.execute("SELECT id FROM custom_pastes ORDER BY id DESC LIMIT 1")
        last_paste_id = cursor.fetchone()
        logger.debug(f"Last paste id is {last_paste_id}")
        return last_paste_id

    def get_paste_info(self, paste_id, is_ai=True):
        logger.info(f"Getting info of paste {paste_id} from database")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views, idea FROM pastes WHERE id = ?",
                (paste_id,))
        else:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views FROM custom_pastes WHERE id = ?",
                (paste_id,))
        paste_info = cursor.fetchone()
        logger.debug(f"Info of paste {paste_id} is {paste_info}")
        return paste_info

    def get_users_pastes(self, user_database_id, is_ai=True):
        # logger
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views, idea FROM pastes WHERE user_database_id = ?",
                (user_database_id,))
        else:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views FROM custom_pastes WHERE user_database_id = ?",
                (user_database_id,))
        users_pastes = cursor.fetchall()
        return users_pastes

    # --------- Get users stats ---------
    def get_users_stats(self, user_database_id):
        """Returns tuple with amount of pastes, total views and total likes for user"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT (SELECT COUNT(*) FROM pastes WHERE user_database_id = ?) + (SELECT COUNT(*) FROM custom_pastes WHERE user_database_id = ?) AS paste_amount,
                   (SELECT SUM(views) FROM pastes WHERE user_database_id = ?) + (SELECT SUM(views) FROM custom_pastes WHERE user_database_id = ?) AS total_views,
                   (SELECT SUM(rating) FROM pastes WHERE user_database_id = ?) + (SELECT SUM(rating) FROM custom_pastes WHERE user_database_id = ?) AS total_likes
            """, (user_database_id, user_database_id, user_database_id, user_database_id, user_database_id, user_database_id))
        stats = cursor.fetchone()
        logger.debug(f"Stats for user {user_database_id} are {stats}")
        return stats

        # Example of output: (5, 100, 15) - user has 5 pastes, 100 views in total and 15 likes in total

    # --------- Rating staff ---------
    def add_like_to_paste(self, paste_id, user_discord_id, is_ai=True):
        logger.info(f"Adding like to paste {paste_id} from user '{user_discord_id}'")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute("UPDATE pastes SET rating = rating + 1 WHERE id = ?", (paste_id,))
            cursor.execute("INSERT INTO pastes_like (user_id, paste_id) VALUES (?, ?)", (user_discord_id, paste_id))
        else:
            cursor.execute("UPDATE custom_pastes SET rating = rating + 1 WHERE id = ?", (paste_id,))
            cursor.execute("INSERT INTO custom_pastes_likes (user_id, paste_id) VALUES (?, ?)",
                           (user_discord_id, paste_id))
        self.conn.commit()

    def add_view_to_paste(self, paste_id, is_ai=True):
        logger.info(f"Adding view to paste {paste_id}")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute("UPDATE pastes SET views = views + 1 WHERE id = ?", (paste_id,))
        else:
            cursor.execute("UPDATE custom_pastes SET views = views + 1 WHERE id = ?", (paste_id,))
        self.conn.commit()

    def get_who_likes_the_paste(self, paste_id, is_ai=True):
        logger.info(f"Getting who likes the paste {paste_id} from database")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute("SELECT user_id FROM pastes_like WHERE paste_id = ?", (paste_id,))
        else:
            cursor.execute("SELECT user_id FROM custom_pastes_likes WHERE paste_id = ?", (paste_id,))
        who_likes_the_paste = cursor.fetchall()
        logger.debug(f"Who likes the paste {paste_id} is {who_likes_the_paste}")
        return who_likes_the_paste

    def get_top_10_pastes_by_rating(self, is_ai=True):  # rating = likes
        logger.info(f"Getting top 10 pastes by rating from database")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views, idea FROM pastes ORDER BY rating DESC LIMIT 10")
        else:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views FROM custom_pastes ORDER BY rating DESC LIMIT 10")
        pastes_info = cursor.fetchall()
        logger.debug(f"Top 10 pastes by rating are {pastes_info}")
        return pastes_info

    def get_top_10_pastes_by_views(self, is_ai=True):
        logger.info(f"Getting top 10 pastes by views from database")
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views, idea FROM pastes ORDER BY views DESC LIMIT 10")
        else:
            cursor.execute(
                "SELECT id, user_database_id, content, updated_at, rating, views FROM custom_pastes ORDER BY views DESC LIMIT 10")
        pastes_info = cursor.fetchall()
        logger.debug(f"Top 10 pastes by views are {pastes_info}")
        return pastes_info

    def get_top_10_users_by_amount_pastes(self, is_ai=True):
        cursor = self.conn.cursor()
        if is_ai:
            cursor.execute("""
                        SELECT user_database_id, COUNT(*) AS paste_count
                        FROM pastes
                        GROUP BY user_database_id
                        ORDER BY paste_count DESC
                        LIMIT 10
                    """)
        else:
            cursor.execute("""
                        SELECT user_database_id, COUNT(*) AS paste_count
                        FROM custom_pastes
                        GROUP BY user_database_id
                        ORDER BY paste_count DESC
                        LIMIT 10
                    """)
        top_users = cursor.fetchall()
        return top_users


    def close(self):
        if self.conn:
            logger.debug(f"Closing connection to database {self.db_name}")
            self.conn.close()
