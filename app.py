import os
import csv
from datetime import datetime
from io import StringIO

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque_essa_chave_em_producao")

database_url = os.environ.get("DATABASE_URL")
if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")
else:
    database_url = "sqlite:///leads.db"  # só para rodar localmente

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    descricao_problema = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def init_db():
    with app.app_context():
        db.create_all()


init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login realizado com sucesso!")
            return redirect(url_for("dashboard"))

        flash("Credenciais inválidas. Tente novamente.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("Usuário já existe. Faça login.")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Registro realizado com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    categoria = request.args.get("categoria")

    if categoria:
        leads = Lead.query.filter_by(categoria=categoria).order_by(Lead.data.desc()).all()
    else:
        leads = Lead.query.order_by(Lead.data.desc()).all()

    return render_template("dashboard.html", leads=leads)


@app.route("/submit_lead", methods=["POST"])
def submit_lead():
    nome = request.form["nome"]
    email = request.form["email"]
    descricao = request.form["descricao"]
    categoria = request.form["categoria"]

    lead = Lead(
        nome=nome,
        email=email,
        descricao_problema=descricao,
        categoria=categoria
    )

    db.session.add(lead)
    db.session.commit()

    flash("Lead capturado com sucesso! Entraremos em contato.")
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout realizado.")
    return redirect(url_for("index"))


@app.route("/export_csv")
@login_required
def export_csv():
    leads = Lead.query.order_by(Lead.data.desc()).all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Nome", "Email", "Categoria", "Descrição", "Data"])

    for lead in leads:
        cw.writerow([
            lead.id,
            lead.nome,
            lead.email,
            lead.categoria,
            lead.descricao_problema,
            lead.data.strftime("%Y-%m-%d %H:%M:%S")
        ])

    output = si.getvalue()
    return app.response_class(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )


if __name__ == "__main__":
    app.run(debug=True)