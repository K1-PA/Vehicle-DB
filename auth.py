from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import functools

auth_bp = Blueprint('auth', _name_)

def get_db():
    conn = sqlite3.connect('bookings.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        error = None
        
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        
        conn.close()
        
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        
        if error is None:
            # Clear the session and start fresh
            session.clear()
            # Store user info in session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            # Redirect to dashboard after login
            return redirect(url_for('index'))
        
        flash(error)
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/users')
@login_required
def users():
    # Only admin can see the users page
    if session.get('role') != 'admin':
        flash('You do not have permission to view this page.')
        return redirect(url_for('index'))
    
    conn = get_db()
    users = conn.execute('SELECT id, username, role FROM users').fetchall()
    conn.close()
    
    return render_template('users.html', users=users)

@auth_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    # Only admin can add users
    if session.get('role') != 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db()
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = f"User {username} is already registered."
        
        if error is None:
            conn.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), role)
            )
            conn.commit()
            conn.close()
            flash(f'User {username} created successfully.')
            return redirect(url_for('auth.users'))
        
        flash(error)
        conn.close()
    
    return render_template('add_user.html')

def init_db():
    conn = get_db()
    
    # Create users table if it doesn't exist
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    
    # Check if admin user exists, create if not
    admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if admin is None:
        conn.execute(
            'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
            ('admin', generate_password_hash('admin123'), 'admin')
        )
        conn.commit()
        print('Created default admin user: admin/admin123')
    
    conn.close()
