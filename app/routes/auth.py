#Code d'authification à la base données (de connexion au site ) pour un utilisateurs 
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.db import get_db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        user_row = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user_row and user_row['password'] == password:
            user = User(user_row['id'], user_row['username'], user_row['email'], user_row['role'])
            login_user(user)
            return redirect(url_for('main.index'))
        
        flash('Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
