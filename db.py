import pg8000.native
import ssl
import streamlit as st

def get_conn():
    s = st.secrets["supabase"]
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return pg8000.native.Connection(
        host=s["host"],
        port=int(s.get("port", 5432)),
        database=s.get("dbname", "postgres"),
        user=s.get("user", "postgres"),
        password=s["password"],
        ssl_context=ctx
    )

def _to_dicts(conn, rows):
    if not rows:
        return []
    cols = [c["name"] for c in conn.columns]
    return [dict(zip(cols, row)) for row in rows]

def _build(sql, params):
    if not params:
        return sql, {}
    new_sql = sql
    kw = {}
    for i, v in enumerate(params, 1):
        new_sql = new_sql.replace("%s", f":{i}", 1)
        kw[str(i)] = v
    return new_sql, kw

def query(sql, params=None):
    conn = get_conn()
    try:
        s, kw = _build(sql, params)
        rows = conn.run(s, **kw)
        return _to_dicts(conn, rows)
    finally:
        conn.close()

def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None

def execute(sql, params=None):
    conn = get_conn()
    try:
        s, kw = _build(sql, params)
        rows = conn.run(s, **kw)
        cols = [c["name"] for c in conn.columns] if conn.columns else []
        if rows and cols:
            return dict(zip(cols, rows[0]))
        return None
    finally:
        conn.close()
