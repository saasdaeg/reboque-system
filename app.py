import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash
import db, datetime

st.set_page_config(
    page_title="CarreRebok – Sistema de Gestão",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS customizado ──────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1a3a5c; }
[data-testid="stSidebar"] * { color: #fff !important; }
[data-testid="stSidebar"] .stSelectbox label { color: #fff !important; }
div[data-testid="metric-container"] {
    background: #fff; border-radius: 10px;
    padding: 16px; border-left: 4px solid #2563a8;
    box-shadow: 0 1px 3px rgba(0,0,0,.07);
}
.stButton > button {
    border-radius: 7px; font-weight: 500;
}
.stDataFrame { border-radius: 8px; }
h1,h2,h3 { color: #1a3a5c; }
</style>
""", unsafe_allow_html=True)

# ── Sessão ───────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

# ════════════════════════════════════════════════════════════
#  LOGIN
# ════════════════════════════════════════════════════════════
def pagina_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🚛 CarreRebok")
        st.markdown("**Sistema de Gestão de Carretinhas e Reboques**")
        st.markdown("---")
        email = st.text_input("E-mail", placeholder="admin@reboque.com")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
            if email and senha:
                row = db.query_one(
                    "SELECT * FROM usuarios WHERE email=%s AND ativo=1 AND D_E_L_E_T=0",
                    (email.strip().lower(),)
                )
                if row and check_password_hash(row["senha_hash"], senha):
                    st.session_state.usuario = dict(row)
                    st.session_state.pagina  = "dashboard"
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
            else:
                st.warning("Preencha e-mail e senha.")

# ════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════
def sidebar():
    u = st.session_state.usuario
    with st.sidebar:
        st.markdown(f"### 🚛 CarreRebok")
        st.markdown(f"👤 **{u['nome'].split()[0]}** | {u['perfil']}")
        st.markdown("---")
        opcoes = {
            "📊 Dashboard":  "dashboard",
            "💰 Vendas":     "vendas",
            "👥 Clientes":   "clientes",
            "📦 Estoque":    "estoque",
        }
        for label, key in opcoes.items():
            ativo = "**→** " if st.session_state.pagina == key else ""
            if st.button(f"{ativo}{label}", key=f"nav_{key}", use_container_width=True):
                st.session_state.pagina = key
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.pagina  = "dashboard"
            st.rerun()

# ════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════
def pagina_dashboard():
    st.title("📊 Dashboard")

    total_cli  = db.query_one("SELECT COUNT(*) AS t FROM clientes WHERE D_E_L_E_T=0")["t"]
    total_prod = db.query_one("SELECT COUNT(*) AS t FROM produtos WHERE D_E_L_E_T=0")["t"]
    total_vnd  = db.query_one("SELECT COUNT(*) AS t FROM vendas WHERE D_E_L_E_T=0 AND status!='cancelada'")["t"]
    fatur      = db.query_one("SELECT COALESCE(SUM(total),0) AS t FROM vendas WHERE D_E_L_E_T=0 AND status IN ('confirmada','entregue')")["t"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Clientes",         total_cli)
    c2.metric("📦 Produtos",          total_prod)
    c3.metric("💰 Vendas Realizadas", total_vnd)
    c4.metric("📈 Faturamento",       f"R$ {float(fatur):,.2f}")

    st.markdown("---")
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.subheader("Últimas Vendas")
        vendas = db.query("""
            SELECT v.numero_venda, c.nome as cliente, v.status, v.total, v.data_venda
            FROM vendas v LEFT JOIN clientes c ON c.id=v.id_cliente
            WHERE v.D_E_L_E_T=0 ORDER BY v.datestamp_insert DESC LIMIT 8
        """)
        if vendas:
            import pandas as pd
            df = pd.DataFrame(vendas)
            df["total"] = df["total"].apply(lambda x: f"R$ {float(x):,.2f}")
            df.columns = ["Nº Venda","Cliente","Status","Total","Data"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma venda ainda.")

    with col_b:
        st.subheader("⚠️ Estoque Baixo")
        baixo = db.query("SELECT nome, estoque_atual, estoque_minimo FROM produtos WHERE D_E_L_E_T=0 AND estoque_atual <= estoque_minimo")
        if baixo:
            for p in baixo:
                cor = "🔴" if p["estoque_atual"] == 0 else "🟡"
                st.write(f"{cor} **{p['nome']}** — {p['estoque_atual']} un (mín: {p['estoque_minimo']})")
        else:
            st.success("✅ Estoque OK!")

    st.markdown("---")
    st.subheader("Ações Rápidas")
    q1, q2, q3 = st.columns(3)
    if q1.button("💰 Nova Venda",    use_container_width=True, type="primary"):
        st.session_state.pagina = "nova_venda"
        st.rerun()
    if q2.button("👤 Novo Cliente",  use_container_width=True):
        st.session_state.pagina = "novo_cliente"
        st.rerun()
    if q3.button("📦 Novo Produto",  use_container_width=True):
        st.session_state.pagina = "novo_produto"
        st.rerun()

# ════════════════════════════════════════════════════════════
#  CLIENTES
# ════════════════════════════════════════════════════════════
def pagina_clientes():
    st.title("👥 Clientes")
    c1, c2 = st.columns([4,1])
    with c1:
        busca = st.text_input("🔍 Buscar por nome, CPF/CNPJ ou telefone", label_visibility="collapsed", placeholder="Buscar...")
    with c2:
        if st.button("➕ Novo Cliente", use_container_width=True, type="primary"):
            st.session_state.pagina = "novo_cliente"
            st.rerun()

    if busca:
        clientes = db.query(
            "SELECT * FROM clientes WHERE D_E_L_E_T=0 AND (nome ILIKE %s OR cpf_cnpj ILIKE %s OR telefone ILIKE %s) ORDER BY nome",
            (f"%{busca}%",f"%{busca}%",f"%{busca}%")
        )
    else:
        clientes = db.query("SELECT * FROM clientes WHERE D_E_L_E_T=0 ORDER BY nome")

    if clientes:
        import pandas as pd
        for c in clientes:
            with st.expander(f"👤 {c['nome']}  |  {c['telefone'] or '—'}  |  {c['cidade'] or '—'}/{c['estado'] or '—'}"):
                col1, col2 = st.columns(2)
                col1.write(f"**CPF/CNPJ:** {c['cpf_cnpj'] or '—'}")
                col1.write(f"**Telefone:** {c['telefone'] or '—'}")
                col1.write(f"**E-mail:** {c['email'] or '—'}")
                col2.write(f"**Endereço:** {c['endereco'] or '—'}")
                col2.write(f"**Cidade/UF:** {c['cidade'] or '—'}/{c['estado'] or '—'}")
                if c['observacoes']:
                    st.write(f"**Obs:** {c['observacoes']}")
                ea, eb = st.columns(2)
                if ea.button("✏️ Editar", key=f"edit_cli_{c['id']}"):
                    st.session_state["editar_cliente_id"] = c["id"]
                    st.session_state.pagina = "novo_cliente"
                    st.rerun()
                if eb.button("🗑️ Excluir", key=f"del_cli_{c['id']}"):
                    db.execute("UPDATE clientes SET D_E_L_E_T=1 WHERE id=%s", (c['id'],))
                    st.success("Cliente removido.")
                    st.rerun()
    else:
        st.info("Nenhum cliente encontrado.")

def pagina_novo_cliente():
    edit_id = st.session_state.get("editar_cliente_id")
    c = None
    if edit_id:
        c = db.query_one("SELECT * FROM clientes WHERE id=%s", (edit_id,))

    st.title("✏️ Editar Cliente" if c else "👤 Novo Cliente")
    if st.button("← Voltar"):
        st.session_state.pop("editar_cliente_id", None)
        st.session_state.pagina = "clientes"
        st.rerun()

    with st.form("form_cliente"):
        nome     = st.text_input("Nome Completo *", value=c["nome"] if c else "")
        col1,col2 = st.columns(2)
        cpf      = col1.text_input("CPF / CNPJ", value=c["cpf_cnpj"] if c else "")
        tel      = col2.text_input("Telefone / WhatsApp", value=c["telefone"] if c else "")
        email    = st.text_input("E-mail", value=c["email"] if c else "")
        endereco = st.text_input("Endereço", value=c["endereco"] if c else "")
        col3,col4 = st.columns([3,1])
        cidade   = col3.text_input("Cidade", value=c["cidade"] if c else "")
        ufs = ['','AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
        estado   = col4.selectbox("UF", ufs, index=ufs.index(c["estado"]) if c and c["estado"] in ufs else 0)
        obs      = st.text_area("Observações", value=c["observacoes"] if c else "")

        if st.form_submit_button("💾 Salvar Cliente", type="primary", use_container_width=True):
            if not nome.strip():
                st.error("Nome é obrigatório.")
            else:
                uid = st.session_state.usuario["id"]
                if c:
                    db.execute("""
                        UPDATE clientes SET nome=%s,cpf_cnpj=%s,telefone=%s,email=%s,
                        endereco=%s,cidade=%s,estado=%s,observacoes=%s,
                        usuario_update=%s,datestamp_update=NOW() WHERE id=%s
                    """, (nome,cpf,tel,email,endereco,cidade,estado,obs,uid,edit_id))
                    st.success("Cliente atualizado!")
                else:
                    db.execute("""
                        INSERT INTO clientes(nome,cpf_cnpj,telefone,email,endereco,cidade,estado,observacoes,usuario_insert)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (nome,cpf,tel,email,endereco,cidade,estado,obs,uid))
                    st.success("Cliente cadastrado!")
                st.session_state.pop("editar_cliente_id", None)
                st.session_state.pagina = "clientes"
                st.rerun()

# ════════════════════════════════════════════════════════════
#  ESTOQUE
# ════════════════════════════════════════════════════════════
def pagina_estoque():
    st.title("📦 Estoque")
    c1, c2 = st.columns([4,1])
    with c1:
        busca = st.text_input("🔍 Buscar produto", label_visibility="collapsed", placeholder="Buscar por nome, código ou categoria...")
    with c2:
        if st.button("➕ Novo Produto", use_container_width=True, type="primary"):
            st.session_state.pagina = "novo_produto"
            st.rerun()

    if busca:
        produtos = db.query(
            "SELECT * FROM produtos WHERE D_E_L_E_T=0 AND (nome ILIKE %s OR codigo ILIKE %s OR categoria ILIKE %s) ORDER BY categoria,nome",
            (f"%{busca}%",f"%{busca}%",f"%{busca}%")
        )
    else:
        produtos = db.query("SELECT * FROM produtos WHERE D_E_L_E_T=0 ORDER BY categoria,nome")

    if produtos:
        for p in produtos:
            est = p["estoque_atual"]
            mn  = p["estoque_minimo"]
            if est == 0:    icone = "🔴"
            elif est <= mn: icone = "🟡"
            else:           icone = "🟢"
            with st.expander(f"{icone} [{p['codigo'] or '—'}] {p['nome']}  |  Estoque: **{est} {p['unidade']}**  |  R$ {float(p['preco_venda']):,.2f}"):
                col1,col2,col3 = st.columns(3)
                col1.write(f"**Categoria:** {p['categoria'] or '—'}")
                col1.write(f"**Código:** {p['codigo'] or '—'}")
                col2.write(f"**Preço Custo:** R$ {float(p['preco_custo']):,.2f}")
                col2.write(f"**Preço Venda:** R$ {float(p['preco_venda']):,.2f}")
                col3.write(f"**Estoque Atual:** {est} {p['unidade']}")
                col3.write(f"**Estoque Mínimo:** {mn} {p['unidade']}")
                if p["descricao"]:
                    st.write(f"**Descrição:** {p['descricao']}")
                ba, bb, bc = st.columns(3)
                if ba.button("± Movimentar", key=f"mov_{p['id']}"):
                    st.session_state["mov_produto_id"] = p["id"]
                    st.session_state.pagina = "movimentar"
                    st.rerun()
                if bb.button("✏️ Editar", key=f"edit_prod_{p['id']}"):
                    st.session_state["editar_produto_id"] = p["id"]
                    st.session_state.pagina = "novo_produto"
                    st.rerun()
                if bc.button("🗑️ Excluir", key=f"del_prod_{p['id']}"):
                    db.execute("UPDATE produtos SET D_E_L_E_T=1 WHERE id=%s", (p['id'],))
                    st.success("Produto removido.")
                    st.rerun()
    else:
        st.info("Nenhum produto encontrado.")

def pagina_novo_produto():
    edit_id = st.session_state.get("editar_produto_id")
    p = None
    if edit_id:
        p = db.query_one("SELECT * FROM produtos WHERE id=%s", (edit_id,))

    st.title("✏️ Editar Produto" if p else "📦 Novo Produto")
    if st.button("← Voltar"):
        st.session_state.pop("editar_produto_id", None)
        st.session_state.pagina = "estoque"
        st.rerun()

    with st.form("form_produto"):
        col1,col2 = st.columns(2)
        codigo   = col1.text_input("Código", value=p["codigo"] if p else "")
        categorias = ["Reboques","Carretinhas","Acessórios","Peças","Outros"]
        cat_idx  = categorias.index(p["categoria"]) if p and p["categoria"] in categorias else 0
        categoria = col2.selectbox("Categoria", categorias, index=cat_idx)
        nome     = st.text_input("Nome do Produto *", value=p["nome"] if p else "")
        descricao = st.text_area("Descrição / Especificação", value=p["descricao"] if p else "")
        col3,col4,col5,col6 = st.columns(4)
        p_custo  = col3.number_input("Preço Custo (R$)", min_value=0.0, step=0.01, value=float(p["preco_custo"]) if p else 0.0)
        p_venda  = col4.number_input("Preço Venda (R$)", min_value=0.0, step=0.01, value=float(p["preco_venda"]) if p else 0.0)
        est_min  = col5.number_input("Estoque Mínimo", min_value=0, step=1, value=int(p["estoque_minimo"]) if p else 2)
        unidades = ["UN","PC","KG","M","PAR"]
        un_idx   = unidades.index(p["unidade"]) if p and p["unidade"] in unidades else 0
        unidade  = col6.selectbox("Unidade", unidades, index=un_idx)
        if not p:
            est_ini = st.number_input("Estoque Inicial", min_value=0, step=1, value=0)

        if st.form_submit_button("💾 Salvar Produto", type="primary", use_container_width=True):
            if not nome.strip():
                st.error("Nome é obrigatório.")
            else:
                uid = st.session_state.usuario["id"]
                if p:
                    db.execute("""
                        UPDATE produtos SET codigo=%s,nome=%s,descricao=%s,categoria=%s,
                        preco_custo=%s,preco_venda=%s,estoque_minimo=%s,unidade=%s,
                        usuario_update=%s,datestamp_update=NOW() WHERE id=%s
                    """, (codigo,nome,descricao,categoria,p_custo,p_venda,est_min,unidade,uid,edit_id))
                    st.success("Produto atualizado!")
                else:
                    db.execute("""
                        INSERT INTO produtos(codigo,nome,descricao,categoria,preco_custo,preco_venda,
                        estoque_atual,estoque_minimo,unidade,usuario_insert)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (codigo,nome,descricao,categoria,p_custo,p_venda,est_ini,est_min,unidade,uid))
                    st.success("Produto cadastrado!")
                st.session_state.pop("editar_produto_id", None)
                st.session_state.pagina = "estoque"
                st.rerun()

def pagina_movimentar():
    pid = st.session_state.get("mov_produto_id")
    p   = db.query_one("SELECT * FROM produtos WHERE id=%s", (pid,))
    st.title(f"± Movimentar: {p['nome']}")
    if st.button("← Voltar"):
        st.session_state.pop("mov_produto_id", None)
        st.session_state.pagina = "estoque"
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Estoque Atual", f"{p['estoque_atual']} {p['unidade']}")
        with st.form("form_mov"):
            tipo   = st.selectbox("Tipo", ["entrada","saida"], format_func=lambda x: "📥 Entrada" if x=="entrada" else "📤 Saída")
            qtd    = st.number_input("Quantidade", min_value=1, step=1)
            motivo = st.text_input("Motivo", placeholder="Ex: Compra NF 001, Ajuste inventário...")
            if st.form_submit_button("✅ Confirmar", type="primary", use_container_width=True):
                if tipo == "entrada":
                    db.execute("UPDATE produtos SET estoque_atual=estoque_atual+%s WHERE id=%s", (qtd, pid))
                else:
                    if p["estoque_atual"] < qtd:
                        st.error("Estoque insuficiente!")
                        st.stop()
                    db.execute("UPDATE produtos SET estoque_atual=estoque_atual-%s WHERE id=%s", (qtd, pid))
                db.execute("""
                    INSERT INTO movimentos_estoque(id_produto,tipo,quantidade,motivo,usuario_insert)
                    VALUES(%s,%s,%s,%s,%s)
                """, (pid, tipo, qtd, motivo, st.session_state.usuario["id"]))
                st.success(f"Movimentação de {tipo} registrada!")
                st.rerun()

    with col2:
        st.subheader("Histórico Recente")
        hist = db.query("""
            SELECT tipo, quantidade, motivo, datestamp_insert
            FROM movimentos_estoque WHERE id_produto=%s
            ORDER BY datestamp_insert DESC LIMIT 15
        """, (pid,))
        if hist:
            for h in hist:
                ic = "📥" if h["tipo"] == "entrada" else "📤"
                dt = h["datestamp_insert"].strftime("%d/%m/%y %H:%M") if h["datestamp_insert"] else "—"
                st.write(f"{ic} **{h['quantidade']}** — {h['motivo'] or '—'} _{dt}_")
        else:
            st.info("Sem movimentações.")

# ════════════════════════════════════════════════════════════
#  VENDAS
# ════════════════════════════════════════════════════════════
def pagina_vendas():
    st.title("💰 Vendas")
    c1, c2 = st.columns([4,1])
    with c1:
        busca = st.text_input("🔍 Buscar venda", label_visibility="collapsed", placeholder="Buscar por nº da venda ou cliente...")
    with c2:
        if st.button("➕ Nova Venda", use_container_width=True, type="primary"):
            st.session_state.pagina = "nova_venda"
            st.rerun()

    status_filtro = st.selectbox("Filtrar por status", ["Todos","orcamento","confirmada","entregue","cancelada"])

    sql = """SELECT v.*, c.nome as cliente FROM vendas v
             LEFT JOIN clientes c ON c.id=v.id_cliente
             WHERE v.D_E_L_E_T=0"""
    params = []
    if status_filtro != "Todos":
        sql += " AND v.status=%s"; params.append(status_filtro)
    if busca:
        sql += " AND (v.numero_venda ILIKE %s OR c.nome ILIKE %s)"
        params += [f"%{busca}%", f"%{busca}%"]
    sql += " ORDER BY v.datestamp_insert DESC"
    vendas = db.query(sql, params)

    status_icon = {"orcamento":"📝","confirmada":"✅","entregue":"📦","cancelada":"❌"}
    if vendas:
        for v in vendas:
            ic = status_icon.get(v["status"],"•")
            dt = v["data_venda"].strftime("%d/%m/%Y") if v["data_venda"] else "—"
            with st.expander(f"{ic} {v['numero_venda']}  |  {v['cliente'] or 'Balcão'}  |  R$ {float(v['total']):,.2f}  |  {dt}"):
                col1,col2 = st.columns(2)
                col1.write(f"**Status:** {v['status']}")
                col1.write(f"**Pagamento:** {v['forma_pagamento'] or '—'}")
                col2.write(f"**Total:** R$ {float(v['total']):,.2f}")
                col2.write(f"**Data:** {dt}")
                if v["observacoes"]:
                    st.write(f"**Obs:** {v['observacoes']}")
                # Itens
                itens = db.query("""
                    SELECT p.nome, vi.quantidade, vi.preco_unitario, vi.subtotal
                    FROM venda_itens vi JOIN produtos p ON p.id=vi.id_produto
                    WHERE vi.id_venda=%s AND vi.D_E_L_E_T=0
                """, (v["id"],))
                if itens:
                    st.write("**Itens:**")
                    for it in itens:
                        st.write(f"  • {it['nome']} × {it['quantidade']} = R$ {float(it['subtotal']):,.2f}")
                ba, bb = st.columns(2)
                if v["status"] not in ["cancelada","entregue"]:
                    if ba.button("✏️ Editar", key=f"edit_vnd_{v['id']}"):
                        st.session_state["editar_venda_id"] = v["id"]
                        st.session_state.pagina = "nova_venda"
                        st.rerun()
                    if bb.button("❌ Cancelar", key=f"can_vnd_{v['id']}"):
                        # Reverter estoque se confirmada
                        if v["status"] == "confirmada":
                            its = db.query("SELECT * FROM venda_itens WHERE id_venda=%s AND D_E_L_E_T=0", (v["id"],))
                            for it in its:
                                db.execute("UPDATE produtos SET estoque_atual=estoque_atual+%s WHERE id=%s", (it["quantidade"], it["id_produto"]))
                        db.execute("UPDATE vendas SET status='cancelada' WHERE id=%s", (v["id"],))
                        st.success("Venda cancelada.")
                        st.rerun()
    else:
        st.info("Nenhuma venda encontrada.")

def pagina_nova_venda():
    edit_id = st.session_state.get("editar_venda_id")
    v = None
    if edit_id:
        v = db.query_one("SELECT * FROM vendas WHERE id=%s", (edit_id,))

    st.title("✏️ Editar Venda" if v else "💰 Nova Venda")
    if st.button("← Voltar"):
        st.session_state.pop("editar_venda_id", None)
        st.session_state.pagina = "vendas"
        st.rerun()

    clientes = db.query("SELECT id, nome FROM clientes WHERE D_E_L_E_T=0 ORDER BY nome")
    produtos  = db.query("SELECT id, codigo, nome, preco_venda, estoque_atual FROM produtos WHERE D_E_L_E_T=0 ORDER BY nome")

    cli_opts  = {c["nome"]: c["id"] for c in clientes}
    cli_opts  = {"— Sem cliente (balcão) —": None} | cli_opts
    prod_opts = {f"[{p['codigo'] or '—'}] {p['nome']} (R$ {float(p['preco_venda']):,.2f}) | Est: {p['estoque_atual']}": p for p in produtos}

    with st.form("form_venda"):
        col1,col2,col3 = st.columns(3)
        cli_sel = col1.selectbox("Cliente", list(cli_opts.keys()))
        status_opts = ["orcamento","confirmada","entregue","cancelada"]
        status_default = status_opts.index(v["status"]) if v and v["status"] in status_opts else 0
        status = col2.selectbox("Status", status_opts, index=status_default,
                                format_func=lambda x: {"orcamento":"📝 Orçamento","confirmada":"✅ Confirmada","entregue":"📦 Entregue","cancelada":"❌ Cancelada"}[x])
        formas = ["","Dinheiro","PIX","Cartão de Débito","Cartão de Crédito","Boleto","Financiamento","Parcelado"]
        forma_default = formas.index(v["forma_pagamento"]) if v and v["forma_pagamento"] in formas else 0
        forma = col3.selectbox("Forma de Pagamento", formas, index=forma_default)
        obs   = st.text_area("Observações", value=v["observacoes"] if v else "")

        st.markdown("**🛒 Itens da Venda**")
        n_itens = st.number_input("Quantos itens?", min_value=1, max_value=20, step=1, value=1)

        itens_existentes = []
        if edit_id:
            itens_existentes = db.query("""
                SELECT vi.*, p.nome as pnome FROM venda_itens vi
                JOIN produtos p ON p.id=vi.id_produto
                WHERE vi.id_venda=%s AND vi.D_E_L_E_T=0
            """, (edit_id,))

        itens_form = []
        total = 0.0
        for i in range(int(n_itens)):
            st.markdown(f"**Item {i+1}**")
            ic1,ic2,ic3 = st.columns([3,1,1])
            prod_key = ic1.selectbox("Produto", list(prod_opts.keys()), key=f"prod_{i}",
                                     index=0)
            prod_obj = prod_opts[prod_key]
            qtd  = ic2.number_input("Qtd", min_value=1, step=1, value=1, key=f"qtd_{i}")
            preco = ic3.number_input("Preço Unit.", min_value=0.0, step=0.01,
                                     value=float(prod_obj["preco_venda"]), key=f"preco_{i}")
            sub  = qtd * preco
            total += sub
            st.caption(f"Subtotal: R$ {sub:,.2f}")
            itens_form.append({"id_produto": prod_obj["id"], "qtd": qtd, "preco": preco, "sub": sub})

        st.markdown(f"### 💰 Total: R$ {total:,.2f}")

        if st.form_submit_button("💾 Salvar Venda", type="primary", use_container_width=True):
            uid = st.session_state.usuario["id"]
            id_cliente = cli_opts[cli_sel]

            def gerar_numero():
                hoje = datetime.date.today()
                row  = db.query_one("SELECT COUNT(*) as t FROM vendas WHERE DATE(datestamp_insert)=%s", (hoje,))
                seq  = (row["t"] or 0) + 1
                return f"V{hoje.strftime('%Y%m%d')}-{seq:04d}"

            if edit_id:
                venda_antiga = db.query_one("SELECT status FROM vendas WHERE id=%s", (edit_id,))
                db.execute("""
                    UPDATE vendas SET id_cliente=%s,status=%s,forma_pagamento=%s,
                    observacoes=%s,total=%s,usuario_update=%s,datestamp_update=NOW() WHERE id=%s
                """, (id_cliente,status,forma,obs,total,uid,edit_id))
                if venda_antiga and venda_antiga["status"] == "confirmada":
                    ants = db.query("SELECT * FROM venda_itens WHERE id_venda=%s AND D_E_L_E_T=0", (edit_id,))
                    for it in ants:
                        db.execute("UPDATE produtos SET estoque_atual=estoque_atual+%s WHERE id=%s", (it["quantidade"],it["id_produto"]))
                db.execute("UPDATE venda_itens SET D_E_L_E_T=1 WHERE id_venda=%s", (edit_id,))
                vid = edit_id
            else:
                row = db.execute("""
                    INSERT INTO vendas(numero_venda,id_cliente,status,forma_pagamento,observacoes,total,usuario_insert)
                    VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id
                """, (gerar_numero(),id_cliente,status,forma,obs,total,uid))
                vid = row["id"]

            for it in itens_form:
                db.execute("""
                    INSERT INTO venda_itens(id_venda,id_produto,quantidade,preco_unitario,subtotal)
                    VALUES(%s,%s,%s,%s,%s)
                """, (vid,it["id_produto"],it["qtd"],it["preco"],it["sub"]))

            if status == "confirmada":
                for it in itens_form:
                    db.execute("UPDATE produtos SET estoque_atual=estoque_atual-%s WHERE id=%s", (it["qtd"],it["id_produto"]))
                    db.execute("""
                        INSERT INTO movimentos_estoque(id_produto,tipo,quantidade,motivo,id_venda,usuario_insert)
                        VALUES(%s,'saida',%s,'Venda confirmada',%s,%s)
                    """, (it["id_produto"],it["qtd"],vid,uid))

            st.success("Venda salva com sucesso!")
            st.session_state.pop("editar_venda_id", None)
            st.session_state.pagina = "vendas"
            st.rerun()

# ════════════════════════════════════════════════════════════
#  ROTEADOR
# ════════════════════════════════════════════════════════════
if not st.session_state.usuario:
    pagina_login()
else:
    sidebar()
    pag = st.session_state.pagina
    if   pag == "dashboard":   pagina_dashboard()
    elif pag == "clientes":    pagina_clientes()
    elif pag == "novo_cliente":pagina_novo_cliente()
    elif pag == "estoque":     pagina_estoque()
    elif pag == "novo_produto":pagina_novo_produto()
    elif pag == "movimentar":  pagina_movimentar()
    elif pag == "vendas":      pagina_vendas()
    elif pag == "nova_venda":  pagina_nova_venda()
    else:                      pagina_dashboard()
