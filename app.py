import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from io import StringIO
from werkzeug.security import generate_password_hash, check_password_hash  # Para segurança
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'sua_chave_secreta_super_forte_2026'  # Gere uma forte!
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///leads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelos do banco de dados
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)  # Agora com hash

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    descricao_problema = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota para página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para login (com hash)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login realizado com sucesso!')
            return redirect(url_for('dashboard'))
        flash('Credenciais inválidas. Tente novamente.')
    return render_template('login.html')

# Rota para registro (com hash)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe. Faça login.')
        else:
            hashed_password = generate_password_hash(password)  # Hash seguro
            user = User(username=username, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Registro realizado! Bem-vinda ao dashboard.')
            return redirect(url_for('dashboard'))
    return render_template('register.html')

# Rota para dashboard (protegido)
@app.route('/dashboard')
@login_required
def dashboard():
    categoria = request.args.get('categoria')
    if categoria:
        leads = Lead.query.filter_by(categoria=categoria).all()
    else:
        leads = Lead.query.order_by(Lead.data.desc()).all()
    return render_template('dashboard.html', leads=leads)

# Rota para submeter lead
@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    nome = request.form['nome']
    email = request.form['email']
    descricao = request.form['descricao']
    categoria = request.form['categoria']
    lead = Lead(nome=nome, email=email, descricao_problema=descricao, categoria=categoria)
    db.session.add(lead)
    db.session.commit()
    flash('Lead capturado com sucesso! Entraremos em contato.')
    return redirect(url_for('index'))

# Rota para logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado.')
    return redirect(url_for('index'))

# Rota para exportar CSV
@app.route('/export_csv')
@login_required
def export_csv():
    leads = Lead.query.order_by(Lead.data.desc()).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Nome', 'Email', 'Categoria', 'Descrição', 'Data'])
    for lead in leads:
        cw.writerow([lead.id, lead.nome, lead.email, lead.categoria, lead.descricao_problema, lead.data.strftime('%Y-%m-%d %H:%M:%S')])
    output = si.getvalue()
    return app.response_class(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=leads.csv'}
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)  # debug=False para produção