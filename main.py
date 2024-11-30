from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
import sqlite3
from flask_cors import CORS
import os
from barcode import Code128
from barcode.writer import ImageWriter

app = Flask(__name__)
CORS(app)

DB_PATH = './produtos.db'
UPLOAD_FOLDER = './imagens'
BARCODE_FOLDER = './barcodes'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(BARCODE_FOLDER):
    os.makedirs(BARCODE_FOLDER)

def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS produtos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        codigo INTEGER NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        data_cadastro DATE NOT NULL,
        imagem TEXT)'''
    )
    conn.commit()
    conn.close()


create_table()

def gerar_codigo_barras(produto_id, nome,codigo, descricao):
    barcode_filename = f"{produto_id}_{nome}_{codigo}_{descricao}.png".replace(" ", "_")
    barcode_path = os.path.join(BARCODE_FOLDER, barcode_filename)
    barcode = Code128(str(produto_id), writer=ImageWriter())
    barcode.save(barcode_path)
    return barcode_filename

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

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
    return jsonify(produtos)

@app.route('/api/add-produtos', methods=['POST'])
def add_produtos():
    nome = request.form['nome']
    codigo = request.form['codigo']
    descricao = request.form['descricao']
    preco = request.form['preco']
    data_cadastro = datetime.now().strftime('%Y-%m-%d')
    imagem = request.files.get('imagem')

    if imagem:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        imagem.save(filepath)
    else:
        filename = "no_image.png"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO produtos (nome, codigo, descricao, preco, data_cadastro, imagem) VALUES (?, ?, ?, ?, ?, ?)",
                   (nome, codigo, descricao, preco, data_cadastro, filename))
    produto_id = cursor.lastrowid
    conn.commit()
    conn.close()

    barcode_filename = gerar_codigo_barras(produto_id, nome, codigo, descricao)

    return jsonify({'status': 'sucesso', 'mensagem': 'Produto cadastrado com sucesso!', 'codigo_barras': barcode_filename})


@app.route('/imagens/<path:patch>')
def send_image(patch):
    return send_from_directory(UPLOAD_FOLDER, patch)

@app.route('/barcodes/<path:patch>')
def send_barcode(patch):
    return send_from_directory(BARCODE_FOLDER, patch)

@app.route('/api/delete-produtos/<int:id>', methods=['DELETE'])
def delete_produto(id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({'mensagem': 'Produto excluído com sucesso!'})
    except Exception as e:
        print(f"Erro ao excluir o produto: {e}")
        return jsonify({'mensagem': 'Erro ao excluir o produto.'}), 500

if __name__ == '__main__':
    app.run()
