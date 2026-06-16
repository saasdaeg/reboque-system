import psycopg2
import psycopg2.extras
import streamlit as st
from contextlib import contextmanager

def get_conn():
    s = st.secrets["supabase"]
    return psycopg2.connect(
        host=s["host"],
        port=s.get("port", 5432),
        dbname=s.get("dbname", "postgres"),
        user=s.get("user", "postgres"),
        password=s["password"],
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )

@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def query(sql, params=None):
    with db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        return cur.fetchall()

def query_one(sql, params=None):
    with db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        return cur.fetchone()

def execute(sql, params=None):
    with db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        try:
            return cur.fetchone()
        except Exception:
            return None
