# SafeWork EPIs - Loja virtual de Equipamentos de Proteção

Projeto de e-commerce desenvolvido para praticar back-end e banco de dados.

## Funcionalidades
- Catálogo de produtos com filtro por categoria
- Carrinho de compras
- Finalização de pedido com nome e e-mail
- Banco de dados SQLite

## Tecnologias
Python, Flask, SQLite, HTML e CSS

## Como rodar

1. Crie e ative o ambiente virtual:
   `python -m venv venv` e `venv\Scripts\activate`
2. Instale as dependências:
   `python -m pip install -r requirements.txt`
3. Crie um arquivo `.env` na raiz do projeto com:
   `SECRET_KEY=` seguido de uma chave aleatória (gere com
   `python -c "import secrets; print(secrets.token_hex(32))"`)
   e `FLASK_DEBUG=1` (apenas para uso local)
4. Execute: `python app.py`
5. Abra http://127.0.0.1:5000

## Segurança

- Chave secreta e modo debug configurados por variáveis de ambiente
- Proteção CSRF nos formulários (Flask-WTF)
- Validação de nome e e-mail no servidor
- Consultas SQL parametrizadas