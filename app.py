import os
import re
import sqlite3

from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, request, redirect, url_for, session, g, flash

load_dotenv()  # lê o arquivo .env

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "chave-so-para-desenvolvimento")

csrf = CSRFProtect(app)

DATABASE = "loja.db"
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# ---------- Banco de dados ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            preco REAL NOT NULL,
            descricao TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            email TEXT NOT NULL,
            total REAL NOT NULL,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Só insere os produtos de exemplo se a tabela estiver vazia
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO produtos (nome, categoria, preco, descricao) VALUES (?, ?, ?, ?)",
            [
                ("Capacete de Segurança", "Cabeça", 24.90, "Aba frontal, com carneira e jugular."),
                ("Óculos de Proteção", "Olhos", 12.50, "Lente incolor antirrisco e antiembaçante."),
                ("Protetor Auricular Plug", "Audição", 3.90, "Silicone, reutilizável, com cordão."),
                ("Luva de Raspa", "Mãos", 18.00, "Cano curto, ideal para soldagem leve."),
                ("Bota de Segurança", "Pés", 89.90, "Bico de composite, solado antiderrapante."),
                ("Máscara PFF2", "Respiratória", 4.50, "Proteção contra poeiras e névoas."),
                ("Colete Refletivo", "Corpo", 29.90, "Alta visibilidade, fechamento em velcro."),
                ("Cinto Paraquedista", "Altura", 159.90, "Para trabalho em altura, 3 pontos de ancoragem."),
            ],
        )
    db.commit()
    db.close()


# ---------- Utilidades ----------
@app.template_filter("brl")
def brl(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


@app.context_processor
def info_carrinho():
    carrinho = session.get("carrinho", {})
    return {"qtd_carrinho": sum(carrinho.values())}


# ---------- Rotas ----------
@app.route("/")
def index():
    db = get_db()
    categoria = request.args.get("categoria")
    if categoria:
        produtos = db.execute(
            "SELECT * FROM produtos WHERE categoria = ?", (categoria,)
        ).fetchall()
    else:
        produtos = db.execute("SELECT * FROM produtos").fetchall()
    categorias = db.execute(
        "SELECT DISTINCT categoria FROM produtos ORDER BY categoria"
    ).fetchall()
    return render_template(
        "index.html", produtos=produtos, categorias=categorias, ativa=categoria
    )


@app.route("/adicionar/<int:produto_id>", methods=["POST"])
def adicionar(produto_id):
    carrinho = session.get("carrinho", {})
    chave = str(produto_id)
    carrinho[chave] = carrinho.get(chave, 0) + 1
    session["carrinho"] = carrinho
    return redirect(request.referrer or url_for("index"))


@app.route("/carrinho")
def ver_carrinho():
    db = get_db()
    carrinho = session.get("carrinho", {})
    itens = []
    total = 0
    for pid, qtd in carrinho.items():
        produto = db.execute("SELECT * FROM produtos WHERE id = ?", (pid,)).fetchone()
        if produto:
            subtotal = produto["preco"] * qtd
            total += subtotal
            itens.append({"produto": produto, "qtd": qtd, "subtotal": subtotal})
    return render_template("carrinho.html", itens=itens, total=total)


@app.route("/remover/<int:produto_id>", methods=["POST"])
def remover(produto_id):
    carrinho = session.get("carrinho", {})
    carrinho.pop(str(produto_id), None)
    session["carrinho"] = carrinho
    return redirect(url_for("ver_carrinho"))


@app.route("/finalizar", methods=["POST"])
def finalizar():
    db = get_db()
    carrinho = session.get("carrinho", {})
    if not carrinho:
        return redirect(url_for("index"))

    # strip() tira espaços das pontas; lower() deixa o e-mail em minúsculas
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()

    if len(nome) < 3 or len(nome) > 100:
        flash("Informe seu nome completo (entre 3 e 100 caracteres).")
        return redirect(url_for("ver_carrinho"))

    if len(email) > 120 or not EMAIL_REGEX.match(email):
        flash("Informe um e-mail válido, por exemplo: nome@exemplo.com.")
        return redirect(url_for("ver_carrinho"))

    total = 0
    for pid, qtd in carrinho.items():
        produto = db.execute("SELECT preco FROM produtos WHERE id = ?", (pid,)).fetchone()
        if produto:
            total += produto["preco"] * qtd

    cursor = db.execute(
        "INSERT INTO pedidos (cliente, email, total) VALUES (?, ?, ?)",
        (nome, email, total),
    )
    db.commit()
    session.pop("carrinho", None)
    return redirect(url_for("sucesso", pedido_id=cursor.lastrowid))


@app.route("/sucesso/<int:pedido_id>")
def sucesso(pedido_id):
    return render_template("sucesso.html", pedido_id=pedido_id)


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")