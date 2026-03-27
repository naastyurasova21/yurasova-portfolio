import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import time
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'postgres'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'contactdb'),
            'user': os.getenv('DB_USER', 'contactuser'),
            'password': os.getenv('DB_PASSWORD', 'SecurePass123')
        }
        self.max_retries = 3
        self.retry_delay = 2

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            cur = conn.cursor(cursor_factory=cursor_factory)
            yield cur
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False,
            return_rowcount=False):
        for attempt in range(self.max_retries):
            try:
                with self.get_cursor() as cur:
                    cur.execute(query, params or ())

                    if fetch_one:
                        return cur.fetchone()
                    elif fetch_all:
                        return cur.fetchall()
                    elif return_rowcount:
                        return cur.rowcount
                    else:
                        return None
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(self.retry_delay)


db = DatabaseConnection()
