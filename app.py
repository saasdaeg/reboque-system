import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

st.set_page_config(page_title="CarreRebok", page_icon="🚛", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1a3a5c; }
[data-testid="stSidebar"] * { color: #fff !important; }
div[data-testid="metric-container"] {
    background:#fff;border-radius:10px;padding:16px;
    border-left:4px solid #2563a8;box-shadow:0 1px 3px rgba(0,0,0,.07);
}
h1,h2,h3{color:#1a3a5c;}
</style>
""", unsafe_allow_html=True)

# ── Lazy import do db (precisa de secrets) ───────────────────
import db

# ── Sessão ───────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

# ════════════════════════════════════════════════════════════
#  LOGIN
# ════════════════════════════════════════════════════════════
def pagina_login():
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🚛 CarreRebok")
        st.markdown("**Sistema de Gestão de Carretinhas e Reboques**")
        st.markdown("---")
        email = st.text_input("E-mail", placeholder="admin@reboque.com")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if email and senha:
                rows = db.query("usuarios", filters={"email": email.strip().lower(), "ativo": 1, "d_e_l_e_t": 0})
                if rows and check_password_hash(rows[0]["senha_hash"], senha):
                    st.session_state.usuario = rows[0]
                    st.session_state.pagina = "dashboard"
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
        st.markdown(f"👤 **{u['nome'].split()[0]}**")
        st.markdown("---")
        menus = [("📊 Dashboard","dashboard"),("💰 Vendas","vendas"),
                 ("👥 Clientes","clientes"),("📦 Estoque","estoque")]
        for label, key in menus:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.pagina = key
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.usuario = None
            st.rerun()

# ════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════
def pagina_dashboard():
    st.title("📊 Dashboard")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 Clientes",  db.count("clientes", {"d_e_l_e_t":0}))
    c2.metric("📦 Produtos",  db.count("produtos",  {"d_e_l_e_t":0}))

    vendas_all = db.query("vendas", filters={"d_e_l_e_t":0})
    total_vnd  = sum(1 for v in vendas_all if v["status"] != "cancelada")
    fatur      = sum(float(v["total"] or 0) for v in vendas_all if v["status"] in ("confirmada","entregue"))
    c3.metric("💰 Vendas",     total_vnd)
    c4.metric("📈 Faturamento", f"R$ {fatur:,.2f}")

    st.markdown("---")
    col_a, col_b = st.columns([2,1])
    with col_a:
        st.subheader("Últimas Vendas")
        vendas = sorted(vendas_all, key=lambda x: x["datestamp_insert"] or "", reverse=True)[:8]
        clientes_map = {c["id"]: c["nome"] for c in db.query("clientes", filters={"d_e_l_e_t":0})}
        for v in vendas:
            st.write(f"**{v['numero_venda']}** | {clientes_map.get(v['id_cliente'],'Balcão')} | {v['status']} | R$ {float(v['total'] or 0):,.2f}")
    with col_b:
        st.subheader("⚠️ Estoque Baixo")
        prods = db.query("produtos", filters={"d_e_l_e_t":0})
        baixo = [p for p in prods if p["estoque_atual"] <= p["estoque_minimo"]]
        if baixo:
            for p in baixo:
                ic = "🔴" if p["estoque_atual"]==0 else "🟡"
                st.write(f"{ic} **{p['nome']}** — {p['estoque_atual']} un")
        else:
            st.success("✅ Estoque OK!")
    st.markdown("---")
    q1,q2,q3 = st.columns(3)
    if q1.button("💰 Nova Venda",   use_container_width=True, type="primary"):
        st.session_state.pagina="nova_venda"; st.rerun()
    if q2.button("👤 Novo Cliente", use_container_width=True):
        st.session_state.pagina="novo_cliente"; st.rerun()
    if q3.button("📦 Novo Produto", use_container_width=True):
        st.session_state.pagina="novo_produto"; st.rerun()

# ════════════════════════════════════════════════════════════
#  CLIENTES
# ════════════════════════════════════════════════════════════
def pagina_clientes():
    st.title("👥 Clientes")
    c1,c2 = st.columns([4,1])
    busca = c1.text_input("Buscar", placeholder="Nome, CPF/CNPJ ou telefone...", label_visibility="collapsed")
    if c2.button("➕ Novo", use_container_width=True, type="primary"):
        st.session_state.pagina="novo_cliente"; st.rerun()
    clientes = db.query("clientes", filters={"d_e_l_e_t":0})
    if busca:
        b = busca.lower()
        clientes = [c for c in clientes if b in (c["nome"] or "").lower()
                    or b in (c["cpf_cnpj"] or "").lower()
                    or b in (c["telefone"] or "").lower()]
    for c in clientes:
        with st.expander(f"👤 {c['nome']}  |  {c['telefone'] or '—'}  |  {c['cidade'] or '—'}"):
            col1,col2 = st.columns(2)
            col1.write(f"**CPF/CNPJ:** {c['cpf_cnpj'] or '—'}")
            col1.write(f"**Telefone:** {c['telefone'] or '—'}")
            col2.write(f"**Cidade/UF:** {c['cidade'] or '—'}/{c['estado'] or '—'}")
            col2.write(f"**E-mail:** {c['email'] or '—'}")
            ea,eb = st.columns(2)
            if ea.button("✏️ Editar", key=f"ec{c['id']}"):
                st.session_state["editar_cliente_id"]=c["id"]; st.session_state.pagina="novo_cliente"; st.rerun()
            if eb.button("🗑️ Excluir", key=f"dc{c['id']}"):
                db.soft_delete("clientes", c["id"]); st.rerun()

def pagina_novo_cliente():
    eid = st.session_state.get("editar_cliente_id")
    c = next((x for x in db.query("clientes",{"d_e_l_e_t":0}) if x["id"]==eid), None) if eid else None
    st.title("✏️ Editar Cliente" if c else "👤 Novo Cliente")
    if st.button("← Voltar"):
        st.session_state.pop("editar_cliente_id",None); st.session_state.pagina="clientes"; st.rerun()
    with st.form("fc"):
        nome    = st.text_input("Nome *", value=c["nome"] if c else "")
        col1,col2 = st.columns(2)
        cpf     = col1.text_input("CPF/CNPJ", value=c["cpf_cnpj"] if c else "")
        tel     = col2.text_input("Telefone", value=c["telefone"] if c else "")
        email   = st.text_input("E-mail", value=c["email"] if c else "")
        end     = st.text_input("Endereço", value=c["endereco"] if c else "")
        col3,col4 = st.columns([3,1])
        cidade  = col3.text_input("Cidade", value=c["cidade"] if c else "")
        ufs     = ['','AC','AL','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
        estado  = col4.selectbox("UF", ufs, index=ufs.index(c["estado"]) if c and c["estado"] in ufs else 0)
        obs     = st.text_area("Observações", value=c["observacoes"] if c else "")
        if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
            if not nome.strip():
                st.error("Nome obrigatório.")
            else:
                data = dict(nome=nome,cpf_cnpj=cpf,telefone=tel,email=email,
                            endereco=end,cidade=cidade,estado=estado,observacoes=obs,d_e_l_e_t=0)
                if c:
                    db.update("clientes", data, {"id":eid})
                    st.success("Atualizado!")
                else:
                    db.insert("clientes", data)
                    st.success("Cadastrado!")
                st.session_state.pop("editar_cliente_id",None)
                st.session_state.pagina="clientes"; st.rerun()

# ════════════════════════════════════════════════════════════
#  ESTOQUE
# ════════════════════════════════════════════════════════════
def pagina_estoque():
    st.title("📦 Estoque")
    c1,c2 = st.columns([4,1])
    busca = c1.text_input("Buscar", placeholder="Nome, código ou categoria...", label_visibility="collapsed")
    if c2.button("➕ Novo", use_container_width=True, type="primary"):
        st.session_state.pagina="novo_produto"; st.rerun()
    prods = db.query("produtos", filters={"d_e_l_e_t":0})
    if busca:
        b = busca.lower()
        prods = [p for p in prods if b in (p["nome"] or "").lower()
                 or b in (p["codigo"] or "").lower()
                 or b in (p["categoria"] or "").lower()]
    for p in prods:
        ic = "🔴" if p["estoque_atual"]==0 else ("🟡" if p["estoque_atual"]<=p["estoque_minimo"] else "🟢")
        with st.expander(f"{ic} [{p['codigo'] or '—'}] {p['nome']}  |  {p['estoque_atual']} {p['unidade']}  |  R$ {float(p['preco_venda'] or 0):,.2f}"):
            col1,col2,col3 = st.columns(3)
            col1.write(f"**Categoria:** {p['categoria'] or '—'}")
            col2.write(f"**Custo:** R$ {float(p['preco_custo'] or 0):,.2f}")
            col2.write(f"**Venda:** R$ {float(p['preco_venda'] or 0):,.2f}")
            reservado = p.get("estoque_reservado") or 0
            disponivel = p["estoque_atual"] - reservado
            col3.write(f"**Total:** {p['estoque_atual']} {p['unidade']}")
            col3.write(f"**Reservado:** {reservado} | **Disponível:** {disponivel}")
            ba,bb,bc = st.columns(3)
            if ba.button("± Mover", key=f"mv{p['id']}"):
                st.session_state["mov_produto_id"]=p["id"]; st.session_state.pagina="movimentar"; st.rerun()
            if bb.button("✏️ Editar", key=f"ep{p['id']}"):
                st.session_state["editar_produto_id"]=p["id"]; st.session_state.pagina="novo_produto"; st.rerun()
            if bc.button("🗑️ Excluir", key=f"dp{p['id']}"):
                db.soft_delete("produtos", p["id"]); st.rerun()

def pagina_novo_produto():
    eid = st.session_state.get("editar_produto_id")
    p = next((x for x in db.query("produtos",{"d_e_l_e_t":0}) if x["id"]==eid), None) if eid else None
    st.title("✏️ Editar Produto" if p else "📦 Novo Produto")
    if st.button("← Voltar"):
        st.session_state.pop("editar_produto_id",None); st.session_state.pagina="estoque"; st.rerun()
    with st.form("fp"):
        col1,col2 = st.columns(2)
        codigo   = col1.text_input("Código", value=p["codigo"] if p else "")
        cats     = ["Reboques","Carretinhas","Acessórios","Peças","Outros"]
        cat_i    = cats.index(p["categoria"]) if p and p["categoria"] in cats else 0
        categoria= col2.selectbox("Categoria", cats, index=cat_i)
        nome     = st.text_input("Nome *", value=p["nome"] if p else "")
        desc     = st.text_area("Descrição", value=p["descricao"] if p else "")
        col3,col4,col5,col6 = st.columns(4)
        p_custo  = col3.number_input("Custo R$",  min_value=0.0, step=0.01, value=float(p["preco_custo"] or 0) if p else 0.0)
        p_venda  = col4.number_input("Venda R$",  min_value=0.0, step=0.01, value=float(p["preco_venda"] or 0) if p else 0.0)
        est_min  = col5.number_input("Est. Mínimo", min_value=0, step=1, value=int(p["estoque_minimo"] or 0) if p else 2)
        uns      = ["UN","PC","KG","M","PAR"]
        un_i     = uns.index(p["unidade"]) if p and p["unidade"] in uns else 0
        unidade  = col6.selectbox("Unidade", uns, index=un_i)
        est_ini  = 0
        if not p:
            est_ini = st.number_input("Estoque Inicial", min_value=0, step=1, value=0)
        if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
            if not nome.strip():
                st.error("Nome obrigatório.")
            else:
                data = dict(codigo=codigo,nome=nome,descricao=desc,categoria=categoria,
                            preco_custo=p_custo,preco_venda=p_venda,
                            estoque_minimo=est_min,unidade=unidade,d_e_l_e_t=0)
                if p:
                    db.update("produtos", data, {"id":eid})
                    st.success("Atualizado!")
                else:
                    data["estoque_atual"] = est_ini
                    db.insert("produtos", data)
                    st.success("Cadastrado!")
                st.session_state.pop("editar_produto_id",None)
                st.session_state.pagina="estoque"; st.rerun()

def pagina_movimentar():
    pid = st.session_state.get("mov_produto_id")
    prods = db.query("produtos", filters={"d_e_l_e_t":0})
    p = next((x for x in prods if x["id"]==pid), None)
    if not p:
        st.session_state.pagina="estoque"; st.rerun()
    st.title(f"± {p['nome']}")
    if st.button("← Voltar"):
        st.session_state.pop("mov_produto_id",None); st.session_state.pagina="estoque"; st.rerun()
    col1,col2 = st.columns(2)
    with col1:
        st.metric("Estoque Atual", f"{p['estoque_atual']} {p['unidade']}")
        with st.form("fmov"):
            tipo   = st.selectbox("Tipo", ["entrada","saida"], format_func=lambda x:"📥 Entrada" if x=="entrada" else "📤 Saída")
            qtd    = st.number_input("Quantidade", min_value=1, step=1)
            motivo = st.text_input("Motivo")
            if st.form_submit_button("✅ Confirmar", type="primary", use_container_width=True):
                novo = p["estoque_atual"] + qtd if tipo=="entrada" else p["estoque_atual"] - qtd
                if novo < 0:
                    st.error("Estoque insuficiente!")
                else:
                    db.update("produtos", {"estoque_atual": novo}, {"id": pid})
                    db.insert("movimentos_estoque", dict(
                        id_produto=pid, tipo=tipo, quantidade=qtd,
                        motivo=motivo, usuario_insert=st.session_state.usuario["id"]
                    ))
                    st.success("Movimentação registrada!"); st.rerun()
    with col2:
        st.subheader("Histórico")
        movs = db.query("movimentos_estoque", filters={"id_produto":pid})
        movs = sorted(movs, key=lambda x: x["datestamp_insert"] or "", reverse=True)[:15]
        for m in movs:
            ic = "📥" if m["tipo"]=="entrada" else "📤"
            st.write(f"{ic} **{m['quantidade']}** — {m['motivo'] or '—'}")

# ════════════════════════════════════════════════════════════
#  VENDAS
# ════════════════════════════════════════════════════════════
def pagina_vendas():
    st.title("💰 Vendas")
    c1,c2 = st.columns([4,1])
    busca = c1.text_input("Buscar", placeholder="Nº da venda ou cliente...", label_visibility="collapsed")
    if c2.button("➕ Nova", use_container_width=True, type="primary"):
        st.session_state.pagina="nova_venda"; st.rerun()
    status_f = st.selectbox("Status", ["Todos","orcamento","confirmada","entregue","cancelada"])
    vendas   = db.query("vendas", filters={"d_e_l_e_t":0})
    clientes_map = {c["id"]: c["nome"] for c in db.query("clientes", filters={"d_e_l_e_t":0})}
    if status_f != "Todos":
        vendas = [v for v in vendas if v["status"]==status_f]
    if busca:
        b = busca.lower()
        vendas = [v for v in vendas if b in (v["numero_venda"] or "").lower()
                  or b in clientes_map.get(v["id_cliente"],"").lower()]
    vendas = sorted(vendas, key=lambda x: x["datestamp_insert"] or "", reverse=True)
    icons = {"orcamento":"📝","confirmada":"✅","entregue":"📦","cancelada":"❌"}
    for v in vendas:
        ic  = icons.get(v["status"],"•")
        cli = clientes_map.get(v["id_cliente"],"Balcão")
        with st.expander(f"{ic} {v['numero_venda']}  |  {cli}  |  R$ {float(v['total'] or 0):,.2f}"):
            col1,col2 = st.columns(2)
            col1.write(f"**Status:** {v['status']}")
            col1.write(f"**Pagamento:** {v['forma_pagamento'] or '—'}")
            col2.write(f"**Total:** R$ {float(v['total'] or 0):,.2f}")
            itens = db.query("venda_itens", filters={"id_venda":v["id"],"d_e_l_e_t":0})
            prods_map = {p["id"]: p["nome"] for p in db.query("produtos",{"d_e_l_e_t":0})}
            for it in itens:
                st.write(f"  • {prods_map.get(it['id_produto'],'?')} × {it['quantidade']} = R$ {float(it['subtotal'] or 0):,.2f}")
            # Botões fora do loop de itens
            ba,bb,bc = st.columns(3)
            if ba.button("✏️ Editar", key=f"ev{v['id']}"):
                st.session_state["editar_venda_id"]=v["id"]; st.session_state.pagina="nova_venda"; st.rerun()
            if v["status"] not in ["cancelada","entregue"]:
                if bb.button("❌ Cancelar Venda", key=f"cv{v['id']}"):
                    if v["status"] == "confirmada":
                        # Liberar reserva
                        for it in itens:
                            p = next((x for x in db.query("produtos",{"d_e_l_e_t":0}) if x["id"]==it["id_produto"]),None)
                            if p:
                                novo_res = max(0, (p.get("estoque_reservado") or 0) - it["quantidade"])
                                db.update("produtos",{"estoque_reservado": novo_res},{"id":p["id"]})
                    db.update("vendas",{"status":"cancelada"},{"id":v["id"]})
                    st.success("Venda cancelada!" + (" Reserva liberada." if v["status"]=="confirmada" else ""))
                    st.rerun()
            if v["status"] == "orcamento":
                if bc.button("✅ Confirmar Venda", key=f"conf{v['id']}"):
                    # RESERVAR estoque (não baixa ainda)
                    for it in itens:
                        p = next((x for x in db.query("produtos",{"d_e_l_e_t":0}) if x["id"]==it["id_produto"]),None)
                        if p:
                            novo_res = (p.get("estoque_reservado") or 0) + it["quantidade"]
                            db.update("produtos",{"estoque_reservado": novo_res},{"id":p["id"]})
                    db.update("vendas",{"status":"confirmada"},{"id":v["id"]})
                    st.success("✅ Venda confirmada! Estoque reservado.")
                    st.rerun()
            if v["status"] == "confirmada":
                if bc.button("📦 Marcar Entregue", key=f"entr{v['id']}"):
                    # BAIXAR estoque e liberar reserva
                    for it in itens:
                        p = next((x for x in db.query("produtos",{"d_e_l_e_t":0}) if x["id"]==it["id_produto"]),None)
                        if p:
                            novo_est = max(0, p["estoque_atual"] - it["quantidade"])
                            novo_res = max(0, (p.get("estoque_reservado") or 0) - it["quantidade"])
                            db.update("produtos",{"estoque_atual": novo_est, "estoque_reservado": novo_res},{"id":p["id"]})
                            db.insert("movimentos_estoque", dict(
                                id_produto=it["id_produto"], tipo="saida",
                                quantidade=it["quantidade"],
                                motivo=f"Entrega venda {v['numero_venda']}",
                                usuario_insert=st.session_state.usuario["id"]
                            ))
                    db.update("vendas",{"status":"entregue"},{"id":v["id"]})
                    st.success("📦 Entregue! Estoque baixado.")
                    st.rerun()

def pagina_nova_venda():
    eid = st.session_state.get("editar_venda_id")
    v   = next((x for x in db.query("vendas",{"d_e_l_e_t":0}) if x["id"]==eid), None) if eid else None
    st.title("✏️ Editar Venda" if v else "💰 Nova Venda")
    if st.button("← Voltar"):
        st.session_state.pop("editar_venda_id",None); st.session_state.pagina="vendas"; st.rerun()
    clientes = db.query("clientes", filters={"d_e_l_e_t":0})
    produtos  = db.query("produtos",  filters={"d_e_l_e_t":0})
    cli_opts  = {"— Balcão —": None} | {c["nome"]: c["id"] for c in clientes}
    prod_opts = {f"[{p['codigo'] or '—'}] {p['nome']} — R$ {float(p['preco_venda'] or 0):,.2f} | Disp: {p['estoque_atual']-(p.get('estoque_reservado') or 0)} un": p for p in produtos}
    with st.form("fv"):
        col1,col2,col3 = st.columns(3)
        cli_sel = col1.selectbox("Cliente", list(cli_opts.keys()))
        sts_ops = ["orcamento","confirmada","entregue","cancelada"]
        sts_def = sts_ops.index(v["status"]) if v and v["status"] in sts_ops else 0
        status  = col2.selectbox("Status", sts_ops, index=sts_def,
                    format_func=lambda x:{"orcamento":"📝 Orçamento","confirmada":"✅ Confirmada","entregue":"📦 Entregue","cancelada":"❌ Cancelada"}[x])
        formas  = ["","Dinheiro","PIX","Cartão Débito","Cartão Crédito","Boleto","Financiamento","Parcelado"]
        f_def   = formas.index(v["forma_pagamento"]) if v and v["forma_pagamento"] in formas else 0
        forma   = col3.selectbox("Pagamento", formas, index=f_def)
        obs     = st.text_area("Observações", value=v["observacoes"] if v else "")
        st.markdown("**🛒 Itens**")
        n = st.number_input("Qtd de itens", min_value=1, max_value=20, step=1, value=1)
        itens_form = []
        total = 0.0
        for i in range(int(n)):
            st.markdown(f"**Item {i+1}**")
            ic1,ic2,ic3 = st.columns([3,1,1])
            pk   = ic1.selectbox("Produto", list(prod_opts.keys()), key=f"p{i}")
            pobj = prod_opts[pk]
            qtd  = ic2.number_input("Qtd", min_value=1, step=1, value=1, key=f"q{i}")
            preco= ic3.number_input("Preço", min_value=0.0, step=0.01, value=float(pobj["preco_venda"] or 0), key=f"pr{i}")
            sub  = qtd * preco
            total += sub
            st.caption(f"Subtotal: R$ {sub:,.2f}")
            itens_form.append({"id_produto":pobj["id"],"qtd":qtd,"preco":preco,"sub":sub})
        st.markdown(f"### 💰 Total: R$ {total:,.2f}")
        if st.form_submit_button("💾 Salvar Venda", type="primary", use_container_width=True):
            uid = st.session_state.usuario["id"]
            id_cliente = cli_opts[cli_sel]
            if eid:
                vant = v
                db.update("vendas",dict(id_cliente=id_cliente,status=status,
                          forma_pagamento=forma,observacoes=obs,total=total),{"id":eid})
                if vant and vant["status"]=="confirmada":
                    for it in db.query("venda_itens",{"id_venda":eid,"d_e_l_e_t":0}):
                        p = next((x for x in produtos if x["id"]==it["id_produto"]),None)
                        if p: db.update("produtos",{"estoque_atual":p["estoque_atual"]+it["quantidade"]},{"id":p["id"]})
                db.update("venda_itens",{"d_e_l_e_t":1},{"id_venda":eid})
                vid = eid
            else:
                hoje = datetime.date.today()
                vends_hoje = db.query("vendas", filters={"d_e_l_e_t":0})
                seq  = sum(1 for x in vends_hoje if (x["datestamp_insert"] or "")[:10] == str(hoje)) + 1
                num  = f"V{hoje.strftime('%Y%m%d')}-{seq:04d}"
                row  = db.insert("vendas", dict(numero_venda=num,id_cliente=id_cliente,
                                 status=status,forma_pagamento=forma,observacoes=obs,
                                 total=total,usuario_insert=uid,d_e_l_e_t=0))
                vid  = row["id"]
            for it in itens_form:
                db.insert("venda_itens", dict(id_venda=vid,id_produto=it["id_produto"],
                          quantidade=it["qtd"],preco_unitario=it["preco"],subtotal=it["sub"],d_e_l_e_t=0))
            if status in ("confirmada", "entregue"):
                for it in itens_form:
                    p = next((x for x in produtos if x["id"]==it["id_produto"]),None)
                    if p:
                        db.update("produtos",{"estoque_atual":max(0,p["estoque_atual"]-it["qtd"])},{"id":p["id"]})
                        db.insert("movimentos_estoque",dict(id_produto=it["id_produto"],tipo="saida",
                                  quantidade=it["qtd"],motivo="Venda confirmada",
                                  id_venda=vid,usuario_insert=uid))
            st.success("Venda salva!")
            st.session_state.pop("editar_venda_id",None)
            st.session_state.pagina="vendas"; st.rerun()

# ════════════════════════════════════════════════════════════
#  ROTEADOR
# ════════════════════════════════════════════════════════════
if not st.session_state.usuario:
    pagina_login()
else:
    sidebar()
    pag = st.session_state.pagina
    if   pag=="dashboard":    pagina_dashboard()
    elif pag=="clientes":     pagina_clientes()
    elif pag=="novo_cliente": pagina_novo_cliente()
    elif pag=="estoque":      pagina_estoque()
    elif pag=="novo_produto": pagina_novo_produto()
    elif pag=="movimentar":   pagina_movimentar()
    elif pag=="vendas":       pagina_vendas()
    elif pag=="nova_venda":   pagina_nova_venda()
    else:                     pagina_dashboard()
