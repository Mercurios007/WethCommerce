from flask import Flask, flash, render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import time
import mysql.connector
from mysql.connector import errorcode
from mysql.connector import pooling
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


status = os.system("docker ps | grep Backend")
if status != 0:
	print("Iniciando o container Backend...")
	os.system("docker start Backend")


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.secret_key = 'Madara'
db_config = {
	'user': 'root',
	'password': 'Mercurios',
	'host': '127.0.0.1',
	'port': '3308',
	'database': 'WethCommerce',
}

db_pool = pooling.MySQLConnectionPool(
	pool_name="mypool",
	pool_size=5,
	**db_config
)

def get_db_connection():
	try:
		connection = mysql.connector.connect(**db_config)
		if connection.is_connected():
			return connection
	except Error as e:
		print("Erro ao conectar ao MySQL", e)
		return None

@app.route('/')
def home():
	return (render_template('home.html'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM vendedor WHERE name = %s AND password = %s", (username, password))
		user = cursor.fetchone()
		if user:
			session['id'] = user[0]
			return redirect('/loja_data')
		else:
			return render_template('login.html')
	return render_template('login.html')
	cursor.close()
	conn.close

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		password = request.form['password']
		phone_number_1 = request.form['phone_number_1']
		phone_number_2 = request.form['phone_number_2']
		address = request.form['address']
		status = 'active'
		store_name = request.form['store_name']
		bi_passaporte = request.form['bi_passaporte']
		store_logo = None
		if 'store_logo' in request.files:
			file = request.files['store_logo']
			if file and allowed_file(file.filename):
				file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
				file.save(file_path)
				store_logo = file.filename
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		cursor.execute("""INSERT INTO vendedor (name, email, password, phone_number_1, phone_number_2, address, status, bi_passaporte) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (name, email, password, phone_number_1, phone_number_2, address, status, bi_passaporte))
		conn.commit()
		vendedor_id = cursor.lastrowid
		if store_logo:
			cursor.execute("""INSERT INTO lojas (vendedor_id, nome, imagem_url) VALUES (%s, %s, %s)""", (vendedor_id, store_name, store_logo))
		else:
			cursor.execute("""INSERT INTO lojas (vendedor_id, nome) VALUES (%s, %s)""", (vendedor_id, store_name))
		conn.commit()
		return render_template('home.html')
	return render_template('cadastro.html')
	cursor.close()
	conn.close()
        	

@app.route('/perfil', methods=['GET'])
def perfil():
	vendedor_id = session['id']
	if request.method == 'GET':
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		try:
			cursor.execute("SELECT * FROM vendedor WHERE id = %s", (vendedor_id,))
			vendedor = cursor.fetchone()
			if vendedor:
				profile_data = {
				'id': vendedor[0],
				'name': vendedor[1],
				'email': vendedor[2],
				'phone_number_1': vendedor[4],
				'phone_number_2': vendedor[5],
				'address': vendedor[6]	
				}
				return render_template('perfil.html', profile_data=profile_data)
			else:
				return jsonify({'error': 'Vendedor não encontrado'}), 404
		finally:
			cursor.close()
			conn.close()
			
@app.route('/logout')
def logout():
	#session.pop('id', None)
	session.clear()
	return redirect('/')

@app.route('/perfil_data', methods=['GET', 'POST'])
def perfil_data():
	if 'id' not in session:
		flash("Por favor, faça login para acessar seu perfil.")	
		return redirect('/')
	vendedor_id = session['id']
	if request.method == 'GET':
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		try:
			cursor.execute("SELECT * FROM vendedor WHERE id = %s", (vendedor_id,))
			vendedor = cursor.fetchone()
			if vendedor:
				profile_data = {
				'name': vendedor[1],
				'email': vendedor[2],
				'phone_number_1': vendedor[4],
				'phone_number_2': vendedor[5],
				'address': vendedor[6]	
				}
				return render_template('perfil_data.html', profile_data=profile_data, active_page='perfil')
			else:
				return jsonify({'error': 'Vendedor não encontrado'}), 404
		finally:
			cursor.close()
			conn.close()

@app.route('/loja_data', methods=['GET', 'POST'])
def loja_data():
	if request.method == 'GET':
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		vendedor_id = session['id']
		print(type(vendedor_id))
		vendedor_id = session['id']
		print(f"vendedor_id: {vendedor_id}")  # Para verificar o valor do vendedor_id

		query = "SELECT * FROM produtos WHERE vendedor_id = %s"
		cursor.execute(query, (vendedor_id,))
		produtos = cursor.fetchall()
		query = "SELECT nome, imagem_url FROM lojas WHERE vendedor_id = %s"
		cursor.execute(query, (vendedor_id,))
		loja = cursor.fetchone()
		cursor.close()
		conn.close()
		loja_name = loja[0]
		logo_filename = loja[1]
		print(f"Logo filename: {logo_filename}")
		return render_template('loja_data.html', produtos=produtos, loja=loja_name, logo_filename=logo_filename, active_page='loja')

@app.route('/adicionar_produto', methods=['GET', 'POST'])
def adicionar_produto():
	if request.method == 'POST':
		nome = request.form['nome']
		preco = request.form['preco']
		quantidade_estoque = request.form['quantidade_estoque']
		descricao = request.form['descricao']
		categoria = request.form['categoria']
		vendedor_id = session['id']
	
		if 'imagem' not in request.files:
			return "Erro: Nenhuma imagem enviada."

		imagem = request.files['imagem']

		if imagem.filename == '':
			return "Error: Nenhum arquivo selecionado."

		if imagem and allowed_file(imagem.filename):
			filename = secure_filename(imagem.filename)
			filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			imagem.save(filepath)

			conn = mysql.connector.connect(**db_config)
			cursor  = conn.cursor()
			try:
				cursor.execute("SELECT id FROM lojas WHERE vendedor_id = %s", (vendedor_id,))
				loja = cursor.fetchone()
				if loja:
					loja_id = loja[0]
				else:
					return "Erro: Loja não encontrada para o vendedor."
				cursor.execute("SELECT id FROM produtos WHERE nome = %s AND loja_id = %s", (nome, loja_id))
				produto_existente = cursor.fetchone()
				if produto_existente:
					return redirect(url_for('adicionar_produto', erro="Produto com esse nome já existe na loja."))
				query = "INSERT INTO produtos (nome, preco, quantidade_estoque, vendedor_id, loja_id, descricao, imagem, categoria) VALUES (%s, %s, %s, %s, %s ,%s, %s, %s)"
				cursor.execute(query, (nome, preco, quantidade_estoque, vendedor_id, loja_id, descricao, filename, categoria))
				conn.commit()
				return redirect(url_for('loja_data'))
			finally:
				cursor.close()
				conn.close()
		else:
			return "Erro: Formato de arquivo inválido. Envie uma imagem válida."
	return render_template('adicionar_produto.html')


@app.route('/deletar_produto', methods=['GET', 'POST'])
def deletar_produto():
	if request.method == 'POST':
		nome = request.form['nome']
		vendedor_id = session['id']
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		try:
			query = "DELETE FROM produtos WHERE nome = %s AND vendedor_id = %s"
			cursor.execute(query, (nome, vendedor_id))
			conn.commit()
			cursor.execute("SET @count = 0;")
			cursor.execute("UPDATE produtos SET id = @count:= @count + 1;")
			cursor.execute("ALTER TABLE produtos AUTO_INCREMENT = 1;")
			conn.commit()
		finally:
			cursor.close()
			conn.close()
		return redirect(url_for('loja_data'))
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	vendedor_id = session['id']
	query = "SELECT nome FROM produtos WHERE vendedor_id = %s"
	cursor.execute(query, (vendedor_id,))
	produtos = cursor.fetchall()
	cursor.close()
	conn.close()
	return render_template('deletar_produto.html', produtos=produtos)


@app.route('/editar_produto', methods=['GET', 'POST'])
def editar_produto():
	if request.method == 'POST':
		nome_produto = request.form['nome_produto']
		vendedor_id = session['id']
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		cursor.execute("SELECT id FROM produtos WHERE nome = %s AND vendedor_id = %s", (nome_produto, vendedor_id))
		result = cursor.fetchone()
		if result:
			id_produto = result[0]
			if 'editar_nome' in request.form:
				novo_nome = request.form['novo_nome']
				cursor.execute("UPDATE produtos SET nome = %s WHERE id = %s AND vendedor_id = %s", (novo_nome, id_produto, vendedor_id))
			if 'editar_preco' in request.form:
				novo_preco = request.form['novo_preco']
				cursor.execute("UPDATE produtos SET preco = %s WHERE id = %s AND vendedor_id = %s", (novo_preco, id_produto, vendedor_id))
			if 'editar_quantidade' in request.form:
				nova_quantidade = request.form['nova_quantidade']
				cursor.execute("UPDATE produtos SET quantidade_estoque = %s WHERE id = %s AND vendedor_id = %s", (nova_quantidade, id_produto, vendedor_id))
			if 'editar_descricao' in request.form:
				nova_descricao = request.form['nova_descricao']
				cursor.execute("UPDATE produtos SET descricao = %s WHERE id = %s AND vendedor_id = %s", (nova_descricao, id_produto, vendedor_id))
			if 'editar_categoria' in request.form:
				nova_categoria = request.form['nova_categoria']
				cursor.execute("UPDATE produtos SET categoria = %s WHERE id = %s AND vendedor_id = %s", (nova_categoria, id_produto, vendedor_id))
			if 'nova_imagem' in request.files:
				imagem = request.files['nova_imagem']
				print(f"Imagem carregado com sucesso: {imagem.filename}")
				if imagem and allowed_file(imagem.filename):
					filename = secure_filename(imagem.filename)
					filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
					imagem.save(filepath)
					cursor.execute("UPDATE produtos SET imagem = %s WHERE id = %s AND vendedor_id = %s", (filename, id_produto, vendedor_id))
			conn.commit()
		cursor.close()
		conn.close()
		return redirect(url_for('loja_data'))
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	vendedor_id = session['id']
	query = "SELECT id, nome, preco, quantidade_estoque FROM produtos WHERE vendedor_id = %s"
	cursor.execute(query, (vendedor_id,))
	produtos = cursor.fetchall()
	cursor.close()
	conn.close()
	return render_template('editar_produto.html', produtos=produtos)


@app.route('/historico_vendas', methods=['GET'])
def historico_vendas():
	vendedor_id = session['id']
	if not vendedor_id:
		return jsonify({"error": "Vendedor ID é necessário"}), 400
	try:
		conn = get_db_connection()
		cursor = conn.cursor(dictionary=True)
		query = """SELECT id, produto_id, quantidade, preco_unitario, total, estado, data FROM vendas WHERE vendedor_id = %s ORDER BY data DESC"""
		cursor.execute(query, (vendedor_id,))
		vendas = cursor.fetchall()
		cursor.close()
		conn.close()
		if vendas:
			return jsonify(vendas)
		else:
			return ("Error")
	except mysql.connector.Error as err:
		return jsonify({"error": f"Erro ao acessar o banco de dados: {err}"}), 500

@app.route('/analise_de_vendas', methods=['GET'])
def analise_de_vendas():
	vendedor_id = session['id']
	if not vendedor_id:
		return jsonify({"error": "Vendedor ID é necessário"}), 400
	try:
		conn = get_db_connection()
		cursor = conn.cursor(dictionary=True)
		query = """SELECT id, produto_id, quantidade, preco_unitario, total, estado, data 
			FROM vendas WHERE vendedor_id = %s ORDER BY data DESC"""
		cursor.execute(query, (vendedor_id,))
		vendas = cursor.fetchall()
		cursor.close()
		conn.close()
		if vendas:
			return render_template('analise_de_vendas.html', vendas=vendas)
		else:
			return render_template('analise_de_vendas.html', vendas=[])
	except mysql.connector.Error as err:
		return jsonify({"error": f"Erro ao acessar o banco de dados: {err}"}), 500


@app.route('/loja/<int:loja_id>')
def loja(loja_id):
	 return render_template('loja.html', loja_id=loja_id)

@app.route('/shopping')
def shopping():
	conn =  mysql.connector.connect(**db_config)
	cursor = conn.cursor(dictionary=True)
	try:
		cursor.execute("SELECT p.id, p.nome, p.preco, p.quantidade_estoque, p.vendedor_id, p.loja_id, p.descricao, p.imagem, p.categoria, l.nome AS loja_nome FROM produtos p JOIN lojas l ON p.loja_id = l.id ORDER BY categoria")
		produtos = cursor.fetchall()
		produtos_por_categoria = {}
		for produto in produtos:
			categoria = produto['categoria']
			if categoria not in produtos_por_categoria:
				produtos_por_categoria[categoria] = []
			produtos_por_categoria[categoria].append(produto)
	finally:
		cursor.close()
		conn.close()
	return render_template('shopping.html', produtos_por_categoria=produtos_por_categoria)


@app.route('/adicionar_ao_carrinho/<int:produto_id>', methods=['POST'])
def adicionar_ao_carrinho(produto_id):
	if 'carrinho' not in session:
		session['carrinho'] = {}
	carrinho = session['carrinho']
	produto_id = str(produto_id)
	if produto_id in carrinho:
		carrinho[produto_id] += 1
	else:
		carrinho[produto_id] = 1
	session['carrinho'] = carrinho
	session.modified = True
	total_itens = sum(carrinho.values())
	print(f"Produto {produto_id} adicionado ao carrinho. Carrinho atual: {session['carrinho']}")
	return redirect(url_for('shopping'))


@app.route('/carrinho')
def carrinho():
	if 'carrinho' in session and session['carrinho']:
		carrinho_ids = session['carrinho']
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		format_strings = ','.join(['%s'] * len(carrinho_ids))
		cursor.execute(f"""
			SELECT id, nome, preco, quantidade_estoque, descricao, imagem
			FROM produtos
			WHERE id IN ({format_strings})
		""", tuple(carrinho_ids.keys()))
		produtos_carrinho = cursor.fetchall()
		cursor.close()
		conn.close()
		total = 0
		produtos_resultado = []
		for produto in produtos_carrinho:
			quantidade = carrinho_ids.get(str(produto[0]), 0)
			subtotal = produto[2] * quantidade
			total += subtotal
			produtos_resultado.append({
			'id': produto[0],
			'nome': produto[1],
			'preco': produto[2],
			'quantidade': quantidade,
			'subtotal': subtotal,
			'imagem': produto[5]
		})
		return render_template('carrinho.html', produtos=produtos_resultado, total=total)
	return render_template('carrinho.html', produtos=[], total=0)


@app.route('/remover_produto_carrinho/<int:produto_id>', methods=['POST'])
def remover_produto_carrinho(produto_id):
	carrinho = session.get('carrinho', {})
	produto_id_str = str(produto_id)
	if produto_id_str not in carrinho:
		print("O produto nao esta no carrinho")
		print(f"Id enviado no formulario: {produto_id}")
		print(f"Os id disponiveis no carrinho {carrinho}")
		return redirect(url_for('carrinho'))
	if request.method == 'POST':
		acao = request.form['acao']
		if acao == 'remover':
			del carrinho[str(produto_id_str)]
			print(carrinho)
		elif acao == 'diminuir':
			if carrinho[str(produto_id_str)] > 1:
				carrinho[str(produto_id_str)] -= 1
			else:
				del carrinho[str(produto_id_str)]
		session['carrinho'] = carrinho
		session.modified = True
		return redirect(url_for('carrinho'))
	return redirect(url_for('carrinho'))


@app.route('/finalizar_compra')
def finalizar_compra():
	return render_template('finalizar_compra.html')




@app.route('/configuracoes')
def configuracoes():
	return render_template('configuracoes.html')


@app.route('/alterar_dados', methods=['POST'])
def alterar_dados():
	if 'id' not in session:
		return ("Usuario nao autenticado.", 401)
	vendedor_id = session['id']
	conn = mysql.connector.connect(**db_config)
	cursor  = conn.cursor()
	try:
		cursor.execute("SELECT name, email, phone_number_1, phone_number_2, address FROM vendedor WHERE id = %s", (vendedor_id,))
		dados_atual = cursor.fetchone()
		if not dados_atual:
			return ("Vendedor nao encontrado. ", 404)
		nome_atual, email_atual, telefone1_atual, telefone2_atual, endereco_atual = dados_atual
		campo = request.form.get('campo')
		novo_valor = request.form.get('novo_valor')
		if campo == "nome" and novo_valor != nome_atual:
			cursor.execute("UPDATE vendedor SET name = %s WHERE id = %s", (novo_valor, vendedor_id))
		elif campo == "email" and novo_valor != email_atual:
			cursor.execute("UPDATE vendedor SET email = %s WHERE id = %s", (novo_valor, vendedor_id))
		elif campo == "telefone1" and novo_valor != telefone1_atual:
			cursor.execute("UPDATE vendedor SET phone_number_1 = %s WHERE id = %s", (novo_valor, vendedor_id))
		elif campo == "telefone2" and novo_valor != telefone2_atual:
			cursor.execute("UPDATE vendedor SET phone_number_2 = %s WHERE id = %s", (novo_valor, vendedor_id))
		elif campo == "endereco" and novo_valor != endereco_atual:
			cursor.execute("UPDATE vendedor SET address = %s WHERE id = %s", (novo_valor, vendedor_id))
		conn.commit()
	except mysql.connector.Error as err:
		conn.rollback()
		return (f"Erro ao utilizar os dados: {err}", 5000)
	finally:
		cursor.close()
		conn.close()
	return redirect(url_for('loja_data'))


@app.route('/alterar_senha', methods=['POST'])
def alterar_senha():
	if 'id' not in session:
		return ("Usuario nao autenticado.", 401)
	vendedor_id = session['id']
	conn = mysql.connector.connect(**db_config)
	cursor  = conn.cursor()
	try:
		senha_atual = request.form['senha_atual']
		nova_senha = request.form['nova_senha']
		confirmar_senha = request.form['confirmar_senha']
		if not senha_atual or not nova_senha or not confirmar_senha:
			return "Por favor, preencha todos os campos.", 400
		if nova_senha != confirmar_senha:
			return ("As senhas nao coincidem. Tente novamente.", 400)
		cursor.execute("SELECT password FROM vendedor WHERE id = %s", (vendedor_id,))
		resultado = cursor.fetchone()
		if resultado is None or resultado[0] != senha_atual:
			return "Senha Actual incorreta.", 400
		cursor.execute("UPDATE vendedor SET password = %s WHERE id = %s", (nova_senha, vendedor_id))
		conn.commit()
	except mysql.connector.Error as err:
		conn.rollback()
		return (f"Erro ao utilizar os dados: {err}", 5000)
	finally:
		cursor.close()
		conn.close()
	return redirect(url_for('loja_data'))


@app.route('/excluir_conta', methods=['POST'])
def excluir_conta():
	if 'id' not in session:
		return ("Usuário não autenticado.", 401)
	vendedor_id = session['id']
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	try:
		senha_atual = request.form.get('senha_atual', '')
		if not senha_atual:
			return ("Insira a Senha para comfirmar!")
		cursor.execute("SELECT password FROM vendedor WHERE id = %s", (vendedor_id,))
		resultado = cursor.fetchone()
		if resultado is None or resultado[0] != senha_atual:
			return "Senha atual incorreta. Não foi possível excluir a conta.", 400
		cursor.execute("DELETE FROM vendedor WHERE id = %s", (vendedor_id,))
		conn.commit()
		session.pop('id', None)
	except mysql.connector.Error as err:
		conn.rollback()
		return (f"Error ao excluir a conta: {err}", 500)
	finally:
		cursor.close()
		conn.close()
	return redirect(url_for('home'))


@app.route('/ajuda')
def ajuda():
	return render_template('ajuda.html')


if __name__ == '__main__':
    app.run(debug=True, port=5005)
		
