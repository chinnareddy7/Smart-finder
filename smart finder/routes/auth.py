from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from utils import validate_csrf

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        # CSRF check
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf(csrf_token):
            flash('Security validation expired. Please submit the form again.', 'danger')
            return redirect(url_for('auth.register'))
            
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([student_id, name, email, phone, department, password]):
            flash('All fields are required.', 'warning')
            return render_template('register.html', form_data=request.form)
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('register.html', form_data=request.form)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', form_data=request.form)
            
        # Check uniqueness
        if User.query.filter_by(student_id=student_id).first():
            flash('A student with this Student Roll ID is already registered.', 'danger')
            return render_template('register.html', form_data=request.form)
            
        if User.query.filter_by(email=email).first():
            flash('This email address is already associated with an account.', 'danger')
            return render_template('register.html', form_data=request.form)
            
        # Create User
        new_user = User(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            department=department,
            is_admin=False,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash(f'Welcome to Smart Lost & Found, {name}! Your account has been created.', 'success')
        return redirect(url_for('student.dashboard'))
        
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf(csrf_token):
            flash('Security validation token mismatch. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not identifier or not password:
            flash('Please enter your Student ID or Email and password.', 'warning')
            return render_template('login.html', identifier=identifier)
            
        # Check by email or student_id
        user = User.query.filter(
            (User.email == identifier.lower()) | (User.student_id == identifier)
        ).first()
        
        if not user or not user.check_password(password):
            flash('Invalid credentials. Please verify your Student ID / Email and password.', 'danger')
            return render_template('login.html', identifier=identifier)
            
        if not user.is_active:
            flash('Your account has been deactivated. Please contact campus administration.', 'danger')
            return render_template('login.html', identifier=identifier)
            
        login_user(user, remember=remember)
        flash(f'Welcome back, {user.name}!', 'success')
        
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
            
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('student.index'))
