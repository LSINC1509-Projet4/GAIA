from flask import Blueprint, render_template, request, flash, redirect, url_for 
from app.db import get_db
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    print(f"DEBUG: User is authenticated: {current_user.is_authenticated}")
    return render_template('index.html')

@main_bp.route('/register.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        age = request.form.get('age')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') 
        db = get_db()
        # 1. Vérifier si l'utilisateur existe déjà
        user_exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user_exists:
            flash("Ce nom d'utilisateur est déjà pris.")
            return redirect(url_for('main.register'))    
        # 2. Insérer le nouvel utilisateur
        db.execute(
            "INSERT INTO users (username, age, email, password, role) VALUES (?, ?, ?, ?, ?)",
            (username, age, email, password, role)
        )
        db.commit() 
        flash("Compte créé ! Vous pouvez vous connecter.")
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

