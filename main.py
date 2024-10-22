from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
import sqlite3
from flask_cors import CORS
import os

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

# banco de dados
DB_PATH = './produtos.db'

# Cria a tabela, caso não exista
def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS produtos
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        data_cadastro DATE NOT NULL,
        data_validade DATE NOT NULL,
        imagem TEXT)''')
    conn.commit()
    conn.close()

create_table()

# página inicial (index.html)
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# buscar todos os produtos cadastrados
@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    rows = cursor.fetchall()

    produtos = []
    columns = [col[0] for col in cursor.description]
    for row in rows:
        produto = {}
        for i, column in enumerate(columns):
            produto[column] = row[i]
        produtos.append(produto)
    conn.close()
    if len(produtos) == 0:
        return jsonify({'status': 'erro', 'mensagem': 'Nenhum produto cadastrado'})
    else:
        return jsonify(produtos)

# adicionar um novo produto
@app.route('/api/add-produtos', methods=['POST'])
def add_produtos():
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']
    data_cadastro = datetime.now().strftime('%Y-%m-%d')
    data_validade = request.form['data_validade']
    imagem = request.files.get('imagem')
    
    if not imagem:
        filename = "no_image.png"
    else:
        upload_dir = os.path.join(app.root_path, './imagens')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg"
        filepath = os.path.join(upload_dir, filename)
        imagem.save(filepath)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO produtos (nome, descricao, preco, data_cadastro, data_validade, imagem) VALUES (?, ?, ?, ?, ?, ?)",
                   (nome, descricao, preco, data_cadastro, data_validade, filename))
    rows = cursor.rowcount
    conn.commit()
    conn.close()

    if rows == 1:
        return jsonify({'status': 'sucesso', 'mensagem': 'Produto cadastrado com sucesso!'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Ocorreu um erro ao cadastrar!'})

# atualizar um produto existente
@app.route('/api/update-produtos/<int:id>', methods=['PUT'])
def update_produtos(id):
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']
    data_cadastro = request.form['data_cadastro']
    data_validade = request.form['data_validade']
    imagem = request.files.get('imagem', None)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if imagem is None: 
        produto = get_produto_by_id(id)
        filename = produto['imagem']
    else:
        upload_dir = os.path.join(app.root_path, './imagens')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg"
        filepath = os.path.join(upload_dir, filename)
        imagem.save(filepath)
        
    cursor.execute("UPDATE produtos SET nome=?, descricao=?, preco=?, data_cadastro=?, data_validade=?, imagem=? WHERE id=?",
                   (nome, descricao, preco, data_cadastro, data_validade, filename, id))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    if rows == 1:
        return jsonify({'status': 'sucesso', 'mensagem': 'Produto atualizado com sucesso!'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Ocorreu um erro ao atualizar o produto!'})

# deletar um produto pelo ID
@app.route('/api/delete-produtos/<int:id>', methods=['DELETE'])
def delete_produtos(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id=?", (id,))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    if rows == 1:
        return jsonify({'status': 'sucesso', 'mensagem': 'Produto deletado com sucesso'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Ocorreu um erro ao deletar o produto'})

# buscar os detalhes de um produto pelo ID
@app.route('/api/detalhe-produto/<int:id>', methods=['GET'])
def get_produto_by_id(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id=?", (id,))
    produto = cursor.fetchone()
    conn.close()
    
    if produto:
        produto_dict = {
            'id': produto[0],
            'nome': produto[1],
            'descricao': produto[2],
            'preco': produto[3],
            'data_cadastro': produto[4],
            'data_validade': produto[5],
            'imagem': produto[6]
        }
        return produto_dict
    else:
        return None

# enviar imagens
@app.route('/imagens/<path:path>')
def send_image(path):
    return send_from_directory(os.path.join(app.root_path, 'imagens'), path)

if __name__ == '__main__':
    app.run()
