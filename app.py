from flask import Flask, flash, render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import time
import hashlib
import stripe
import paypalrestsdk
import mysql.connector
from mysql.connector import errorcode
from mysql.connector import pooling
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer
import random
import smtplib
import os

app = Flask(__name__)
app.secret_key = 'Madara'
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configuração do PayPal
app.config['AfM4pF6qRAsjI_irqFeb5oPqT12OIErII-w5NOYXpymz8KghV-jU57375PxmEoa8xzC8O-MHpL7Lcb3A'] = os.getenv('AfM4pF6qRAsjI_irqFeb5oPqT12OIErII-w5NOYXpymz8KghV-jU57375PxmEoa8xzC8O-MHpL7Lcb3A')
app.config['ENQx0E7yHD26A99f8FvfkquYV-OX1KJO9JDGH6hRgzpgKv9evHsl6-BMcUWHc0M6ldh53LidTDw21nzy'] = os.getenv('ENQx0E7yHD26A99f8FvfkquYV-OX1KJO9JDGH6hRgzpgKv9evHsl6-BMcUWHc0M6ldh53LidTDw21nzy')

import paypalrestsdk

paypalrestsdk.configure({
    "mode": "live",  # Altere para "sandbox" se estiver usando para testes
    "client_id": "AfM4pF6qRAsjI_irqFeb5oPqT12OIErII-w5NOYXpymz8KghV-jU57375PxmEoa8xzC8O-MHpL7Lcb3A",
    "client_secret": "ENQx0E7yHD26A99f8FvfkquYV-OX1KJO9JDGH6hRgzpgKv9evHsl6-BMcUWHc0M6ldh53LidTDw21nzy"  # Substitua com seu Client Secret
})

stripe.api_key="sk_test_51QTOxKG8y4lkVkcj0VSZbqB0XnXRf8n8KTVN2ejV8h89eFVLN2n6DpqBcQGsxwVmAIZIXr8r7IyXT8ixgrQQVrhB003sgHXSHV"
serializer = URLSafeTimedSerializer(app.secret_key)
DOMINIO = "http://127.0.0.1:5005"

status = os.system("docker ps | grep Backend")
if status != 0:
	print("Iniciando o container Backend...")
	os.system("docker start Backend")


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


email_de = "wethcommerce@gmail.com"
senha = "ctwz khlo pdbu znvg"


db_config = {
	'user': 'root',
	'password': 'Alquimia',
	'host': '127.0.0.1',
	'port': '3306',
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
		codigo_verificacao = str(random.randint(100000, 999999))
		session['cadastrar_dados'] = {
			'name': name,
			'email': email,
			'password': password,		
			'phone_number_1': phone_number_1,
			'phone_number_2': phone_number_2,
			'address': address,
			'status': status,
			'store_name': store_name,
			'bi_passaporte': bi_passaporte,
			'store_logo': store_logo,
			'codigo_verificacao': codigo_verificacao
		}

		token = serializer.dumps(email, salt='email-confirmation-salt')
		session['token'] = token
		corpo = """
		<!DOCTYPE html>
		<html lang="pt-br">
		<head>
			<meta charset="UTF-8">
			<style>
				body {{
					font-family: Arial, sans-serif;
					margin: 0;
					padding: 0;
					background-color: #f5f5f5;
        			}}
				.email-container {{
					max-width: 600px;
					margin: 20px auto;
					background: white;
					border: 1px solid #ddd;
					border-radius: 8px;
					padding: 20px;
					box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
				}}
				.header {{
					text-align: center;
					padding: 10px 0;
					background-color: #4CAF50;
					color: white;
					border-radius: 8px 8px 0 0;
				}}
				.header h1 {{
					margin: 0;
					font-size: 24px;
				}}
				.body {{
					padding: 20px;
					text-align: center;
					color: #333;
				}}
				.body p {{
					font-size: 18px;
					margin: 10px 0;
				}}
				.code {{
					font-size: 24px;
					font-weight: bold;
					color: #4CAF50;
					margin: 20px 0;
				}}
				.footer {{
					text-align: center;
					padding: 10px;
					font-size: 12px;
					color: #777;
				}}
			</style>
		</head>
		<body>
			<div class="email-container">
				<div class="header">
					<h1>Confirmação de Identidade</h1>
				</div>
				<div class="body">
					<p>Olá, {name}</p>
						<p>Estamos enviando este e-mail para confirmar sua identidade.</p>
						<p>O seu código de verificação é:</p>
						<div class="code">{codigo_verificacao}</div>
						<p>Por favor, insira este código no campo indicado para continuar.</p>
				</div>
				<div class="footer">
					<p>Se você não solicitou esta verificação, ignore este e-mail.</p>
					<p>&copy; 2025 WethCommerce. Todos os direitos reservados.</p>
				</div>
			</div>
		</body>
		</html>
		""".format(name=name, codigo_verificacao=codigo_verificacao)
		email_de = "wethcommerce@gmail.com"
		senha = "ctwz khlo pdbu znvg"

		mensagem = MIMEMultipart()
		mensagem["From"] = email_de
		mensagem["To"] = email
		mensagem["Subject"] = "Solicitação de Confirmação de Identidade"
		mensagem.attach(MIMEText(corpo, "html"))

		try:
			servidor = smtplib.SMTP("smtp.gmail.com", 587)
			servidor.starttls()
			servidor.login(email_de, senha)
			servidor.sendmail(email_de, email, mensagem.as_string())
			servidor.close()
			flash('Um e-mail foi enviado para a verificação. Por favor, verifique seu e-mail.')
			print('Um e-mail foi enviado para a verificação. Por favor, verifique seu e-mail.')
			return render_template('verificar_codigo.html', token=token)
		except Exception as e:
			print(f"Falha ao enviar o e-mail: {e}")
			flash(f"Falha ao enviar o e-mail: {e}")
			return redirect(url_for('cadastro'))
	return render_template('cadastro.html')
	
        	

@app.route('/verificar_codigo/<token>', methods=['GET', 'POST'])
def verificar_codigo(token):
	try:
		email = serializer.loads(token, salt='email-confirmation-salt', max_age=120)
	except:
		flash('O código de verificação expirou ou é inválido. Por favor, solicite um novo código.')
		return redirect(url_for('cadastro'))
	if request.method == 'POST':
		if 'cadastrar_dados' in session:
			codigo_inserido = request.form['verification_code']
			cadastro_dados = session['cadastrar_dados']
			if codigo_inserido == cadastro_dados['codigo_verificacao']:
				name = cadastro_dados['name']
				email = cadastro_dados['email']
				password = cadastro_dados['password']
				phone_number_1 = cadastro_dados['phone_number_1']
				phone_number_2 = cadastro_dados['phone_number_2']
				address = cadastro_dados['address']
				status = cadastro_dados['status']
				store_name = cadastro_dados['store_name']
				bi_passaporte = cadastro_dados['bi_passaporte']
				store_logo = cadastro_dados['store_logo']

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
				cursor.close()
				conn.close()
				session.pop('cadastrar_dados', None)
				flash('Código verificado e cadastro realizado com sucesso!')
				return redirect(url_for('login'))
			else:
				flash('Dados de cadastro não encontrados na sessão. Por favor, tente novamente.')
				return redirect(url_for('verificar_codigo', token=token))
		else:
			flash('Dados de cadastro não encontrados na sessão. Por favor, tente novamente.')
			print('Dados de cadastro não encontrados na sessão. Por favor, tente novamente.')
			return redirect(url_for('home'))
			
	return render_template('verificar_codigo.html')


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
		loja_name = loja[0]
		logo_filename = loja[1]
		query = "SELECT DATE_FORMAT(created_at, '%d/%m/%Y') AS created_at FROM produtos WHERE vendedor_id = %s"
		cursor.execute(query, (vendedor_id,))
		data_criacao = cursor.fetchall()
		cursor.close()
		conn.close()
		print(f"Logo filename: {logo_filename}")
		return render_template('loja_data.html', produtos=produtos, loja=loja_name, logo_filename=logo_filename, active_page='loja', vendedor_id=vendedor_id, data_criacao=data_criacao)

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
				cursor.execute("SELECT id FROM categoria WHERE nome = %s", (categoria,))
				categoria_id = cursor.fetchone()
				if categoria_id:
					categoria_id = categoria_id[0]
				query = "INSERT INTO produtos (nome, preco, quantidade_estoque, vendedor_id, loja_id, descricao, imagem, categoria_id) VALUES (%s, %s, %s, %s, %s ,%s, %s, %s)"
				cursor.execute(query, (nome, preco, quantidade_estoque, vendedor_id, loja_id, descricao, filename, categoria_id))
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
	print("Entrou na rota /editar_produto")
	if request.method == 'POST':
		nome_produto = request.form['nome_produto']
		vendedor_id = session.get('id')
		print(f"Nome do produto recebido do formulário: {request.form.get('nome_produto')}")
		print(f"Vendedor ID na sessão: {vendedor_id}")
		if not vendedor_id:
			print("Erro: ID do vendedor não encontrado na sessão")
			return "Erro: ID do vendedor não encontrado", 400
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		cursor.execute("SELECT id FROM produtos WHERE nome = %s AND vendedor_id = %s", (nome_produto, vendedor_id))
		result = cursor.fetchone()
		if result:
			print(f"Nome do produto enviado: {request.form.get('nome_produto')}")
			print(f"Novo nome: {request.form.get('novo_nome')}")
			print(f"Novo preço: {request.form.get('novo_preco')}")
			print(f"Nova quantidade: {request.form.get('nova_quantidade')}")
			print(f"Nova descrição: {request.form.get('nova_descricao')}")
			print(f"Nova categoria: {request.form.get('nova_categoria')}")
			print(f"Nova subcategoria: {request.form.get('nova_subcategoria')}")
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
				categoria = request.form['nova_categoria']
				cursor.execute("SELECT id FROM categoria WHERE nome = %s", (categoria,))
				categoria_id = cursor.fetchone()
				print(categoria_id)
				if categoria_id:
					cursor.execute("UPDATE produtos SET categoria_id = %s WHERE id = %s AND vendedor_id = %s", (categoria_id[0], id_produto, vendedor_id))
					print(f"Linhas afetadas: {cursor.rowcount}")
				else:
					return ("Categoria ID é NULO")
			if 'editar_subcategoria' in request.form:
				nova_subcategoria = request.form['nova_subcategoria']
				cursor.execute("SELECT id FROM subcategorias WHERE nome = %s", (nova_subcategoria,))
				subcategoria_id = cursor.fetchone()
				print("Subcategoria_id: {categoria_id}")
				cursor.fetchall()
				if subcategoria_id:
					#print("Subcategoria_id: {categoria_id}")
					cursor.execute("UPDATE produtos SET subcategoria_id = %s WHERE id = %s AND vendedor_id = %s", (subcategoria_id[0], id_produto, vendedor_id))
					print(f"Linhas afetadas: {cursor.rowcount}")
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
	print("Conectado ao banco de dados com sucesso")
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
		cursor.execute("""
			SELECT p.id, p.nome, p.preco, p.quantidade_estoque, p.vendedor_id, p.loja_id, p.descricao, p.imagem, 
			c.nome AS categoria_nome, l.nome AS loja_nome 
			FROM produtos p
			JOIN lojas l ON p.loja_id = l.id
			JOIN categoria c ON p.categoria_id = c.id
			ORDER BY c.nome
		""")
		produtos = cursor.fetchall()
		produtos_por_categoria = {}
		for produto in produtos:
			print(produto)
			categoria = produto.get('categoria_nome')
			if categoria is None:
				categoria = 'Sem Categoria'
			if categoria not in produtos_por_categoria:
				produtos_por_categoria[categoria] = []
			produto['categoria'] = categoria
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
	"""return redirect(url_for('shopping'))"""
	return jsonify({'total_itens': total_itens})


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


@app.route('/ver_detalhes/<int:produto_id>', methods=['GET'])
def ver_detalhes(produto_id):
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	
	cursor.execute("""
		SELECT p.id, p.nome, p.descricao, p.preco, p.quantidade_estoque, p.imagem, l.nome AS loja_nome
		FROM produtos p
		JOIN lojas l ON p.loja_id = l.id
		WHERE p.id = %s
	""", (produto_id,))
	produto = cursor.fetchone()
	cursor.close()
	conn.close()

	if produto is None:
		return ("Produto não encontrado", 401)
	return render_template('ver_detalhe.html', produto=produto)

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


@app.route('/finalizar_compra', methods=['GET', 'POST'])
def finalizar_compra():
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
		for produto in produtos_carrinho:
			quantidade = carrinho_ids.get(str(produto[0]), 0)
			total += produto[2] * quantidade

		# Criar o pagamento no PayPal
		payment_method = request.form.get('payment_method')
		if payment_method == 'paypal':
			payment = paypalrestsdk.Payment({
				"intent": "sale",
				"payer": {
					"payment_method": "paypal"
				},
				"transactions": [{
					"amount": {
						"total": str(total),  # Total do carrinho
						"currency": "USD"
               				},
					"description": "Compra no site"
				}],
				"redirect_urls": {
					"return_url": url_for('pagamento_aprovado', _external=True),
					"cancel_url": url_for('pagamento_cancelado', _external=True)
				}
			})
	
			if payment.create():
				print(f"Pagamento criado {payment}")
				for link in payment.links:
					payment = paypalrestsdk.Payment.find(payment.id)
					if link.rel == "approval_url":
						return redirect(link.href)
			else:
				return redirect(url_for('carrinho'))
		elif payment_method == 'stripe':
			print(f"Total calculado: {total}")
			return redirect(url_for('pagamento_stripe', total=total))
	print(f"Esse outro total: {total}")
	return render_template('finalizar_compra.html', total=total)


@app.route('/stripe_pagamento_aprovado')
def stripe_pagamento_aprovado():
    session.pop('carrinho', None)
    return "Pagamento via Stripe aprovado com sucesso!"

@app.route('/pagamento_stripe', methods=['GET', 'POST'])
def pagamento_stripe():
	total = request.form.get('total') if request.method == 'POST' else request.args.get('total')
	print(f"Total Recebido: {total}")
	print(total)
	if total is None:
		return "Erro: Total não fornecido", 400
	total = float(total)
	stripe_public_key="sk_test_51QTOxKG8y4lkVkcj0VSZbqB0XnXRf8n8KTVN2ejV8h89eFVLN2n6DpqBcQGsxwVmAIZIXr8r7IyXT8ixgrQQVrhB003sgHXSHV"
	if request.method == 'POST':
		token = request.form['stripeToken']
		try:
			charge = stripe.Charge.create(
				amount=int(float(total) * 100),  # Converte para centavos
				currency='aoa',
				description='Compra no site',
				source=token
			)
			return redirect(url_for('stripe_pagamento_aprovado'))
		except stripe.error.StripeError as e:
			print(f"Error: {e}")
			return str(e), 500
	return render_template('stripe_payment.html', total=total, stripe_public_key=stripe_public_key)
		 	

@app.route('/pagamento_aprovado')
def pagamento_aprovado():
	payer_id = request.args.get('PayerID')
	payment_id = request.args.get('paymentId')
	# Localiza o pagamento
	payment = paypalrestsdk.Payment.find(payment_id)
    
	# Executa o pagamento
	if payment.execute({"payer_id": payer_id}):
		session.pop('carrinho', None)
		return "Pagamento aprovado com sucesso!"
	else:
		return "Erro ao capturar pagamento", 500



@app.route('/pagamento_cancelado')
def pagamento_cancelado():
	return "O pagamento foi cancelado."




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

@app.route('/ver_loja/<int:vendedor_id>')
def ver_loja(vendedor_id):
	try:
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor(dictionary=True)
		cursor.execute("""
				SELECT l.id, l.nome, l.imagem_url, l.descricao AS descricao_loja
				FROM lojas l
				WHERE l.vendedor_id = %s
		""", (vendedor_id, ))
		print("Conectado")
		loja = cursor.fetchone()
		if not loja:
			return "Loja não encontrada para o vendedor especificado.", 404
		cursor.execute("""
			SELECT p.id, p.nome, p.preco, p.quantidade_estoque, p.imagem, p.descricao, p.categoria
			FROM produtos p
			WHERE p.loja_id = %s
		""", (loja['id'], ))
		produtos = cursor.fetchall()
		cursor.close()
		conn.close()
		return render_template('ver_loja.html', loja=loja, produtos=produtos)
	except mysql.connector.Error as e:
		print(f"Erro no banco de dados: {e}")
		return "Erro interno no WethServer. Tente novamente mais tarde.", 500
	except Exception as e:
		print(f"Erro geral: {e}")
		return ("Erro inesperado. Tenta novamente mais tarde.", 500)




@app.route('/cadastro_afiliado', methods=['GET', 'POST'])
def cadastro_afiliado():
	if request.method == 'POST':
		name = request.form['nome']
		email = request.form['email']
		senha = request.form['senha']
		confirmar_senha = request.form['confirmar_senha']
		if senha == confirmar_senha:
			conn = mysql.connector.connect(**db_config)
			cursor = conn.cursor()
			cursor.execute("SELECT * FROM afiliados WHERE email = %s", (email,))
			afiliado = cursor.fetchone()
			if afiliado:
				flash('E-mail já cadastrado. Tente outro.', 'error')
				return redirect('/cadastrar')
			senha_hash = generate_password_hash(senha)
			cursor.execute("""
				INSERT INTO afiliados (nome, email, senha)
				VALUES (%s, %s, %s)
			""", (name, email, senha_hash))
			conn.commit()
			cursor.close()
			conn.close()
			flash('Afiliado cadastrado com sucesso! Verifique seu e-mail para o código de verificação.', 'success')
			return render_template('codigo_verificacao.html')
		else:
			flash('As senhas não coincidem. Tente novamente.', 'error')
			return redirect(url_for('cadastro_afiliado'))
	return render_template('cadastro_afiliado.html')
			
@app.route('/gerar_link_vendas', methods=['GET', 'POST'])
def gerar_link_vendas():
	if request.method == 'POST':
		produto_id = request.form.get('produto_id')
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM produtos WHERE id = %s", (produto_id,))
		produto = cursor.fetchone()
		hash_obj = hashlib.md5(str(produto_id).encode('utf-8'))
		url_hash = hash_obj.hexdigest()
		cursor.execute("UPDATE produtos SET url_hash = %s WHERE id = %s", (url_hash, produto_id))
		conn.commit()
		cursor.close()
		conn.close()
		link = f"{DOMINIO}/produto?produto={produto[1]}&url_hash={url_hash}"
		return render_template('gerar_link_vendas.html', produtos=[], link=link)
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	cursor.execute("SELECT id, nome FROM produtos")
	produtos = cursor.fetchall()
	cursor.close()
	conn.close()
	return render_template('gerar_link_vendas.html', produtos=produtos)


app.route('/gerar_link_vendas', methods=['GET'])
def exibir_formulario():
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
    
    # Selecionar os produtos disponíveis
	cursor.execute("SELECT id, nome FROM produtos")
	produtos = cursor.fetchall()

	cursor.close()
	conn.close()

    # Exibir o formulário para seleção de produto
	return render_template('gerar_link_vendas.html', produtos=produtos)


@app.route('/produto', methods=['GET'])
def produto():
	if request.method == 'GET':
		produto = request.args.get('produto')
		url_hash = request.args.get('url_hash')
		if not produto or not url_hash:
			return "Produto ou hash nao encontrados", 400
		conn = None
		cursor = None
		try:
			conn = mysql.connector.connect(**db_config)
			cursor = conn.cursor()
			cursor.execute("""
				SELECT p.*, l.nome AS loja_nome, l.descricao AS loja_descricao, l.imagem_url AS loja_imagem
				FROM produtos p
				JOIN lojas l ON p.loja_id = l.id
				WHERE p.url_hash = %s
			""", (url_hash,))
			produto = cursor.fetchone()
			if produto:
				produto_info = {
					'id': produto[0],
					'nome': produto[1],
					'preco': produto[2],
					'quantidade_estoque': produto[3],
					'vendedor_id': produto[4],
					'loja_id': produto[5],
					'descricao': produto[6],
					'imagem': produto[7],
					'categoria': produto[8],
					'created_at': produto[9],
					'url_hash': produto[10],
					'loja_name': produto[11],
					'loja_descricao': produto[12],
					'loja_imagem': produto[13]
				}
				produtos = []
				cursor.execute("SELECT id, nome, preco, descricao, imagem FROM produtos WHERE loja_id = %s", (produto[5],))
				for p in cursor.fetchall():
					produtos.append({
						'id': p[0],
						'nome': p[1],
						'preco': p[2],
						'descricao': p[3],
						'imagem': p[4]
					})
					
				return render_template('produto.html', produto=produto_info, produtos=produtos)
			else:
				return "Produto não encontrado", 404
		finally:
			if cursor:
				cursor.close()
			if conn:
				conn.close()
	return render_template('produto.html')

"""
KILL 372;
KILL 373;
KILL 374;
KILL 375;
KILL 376;
KILL 441;
KILL 442;
KILL 443;
KILL 444;
KILL 445;
KILL 447;
"""
if __name__ == '__main__':
    app.run(debug=True, port=5005)
		
