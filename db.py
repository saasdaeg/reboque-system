import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_client() -> Client:
    s = st.secrets["supabase"]
    return create_client(s["url"], s["key"])

def _sb():
    return get_client()

# ── Helpers que imitam a interface antiga ──────────────────────

def query(table_or_sql, filters=None, order=None, limit=None, search=None):
    """SELECT na tabela com filtros opcionais"""
    q = _sb().table(table_or_sql).select("*")
    if filters:
        for col, val in filters.items():
            q = q.eq(col, val)
    if order:
        q = q.order(order)
    if limit:
        q = q.limit(limit)
    return q.execute().data or []

def query_one(table, filters):
    rows = query(table, filters)
    return rows[0] if rows else None

def insert(table, data):
    return (_sb().table(table).insert(data).execute().data or [None])[0]

def update(table, data, filters):
    q = _sb().table(table).update(data)
    for col, val in filters.items():
        q = q.eq(col, val)
    return q.execute().data

def soft_delete(table, id):
    return update(table, {"D_E_L_E_T": 1}, {"id": id})

def count(table, filters=None):
    q = _sb().table(table).select("id", count="exact")
    if filters:
        for col, val in filters.items():
            q = q.eq(col, val)
    return q.execute().count or 0

def rpc(func_name, params=None):
    return _sb().rpc(func_name, params or {}).execute().data
