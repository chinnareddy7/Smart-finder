from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, User, LostItem, FoundItem, Match, ContactRequest, Notification
from utils import admin_required, validate_csrf
from ai_engine.matching import recalculate_all_matches

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def ensure_admin():
    if not current_user.is_admin:
        flash('Unauthorized: Administrator credentials required.', 'danger')
        return redirect(url_for('student.dashboard'))


@admin_bp.route('/')
def dashboard():
    total_users = User.query.filter_by(is_admin=False).count()
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()
    total_recovered = LostItem.query.filter_by(status='Recovered').count()
    total_claimed = FoundItem.query.filter_by(status='Claimed').count()
    total_matches = Match.query.count()
    high_confidence_matches = Match.query.filter(Match.similarity_score >= 70.0).count()
    
    # Calculate recovery rate
    recovery_rate = round((total_recovered / total_lost * 100), 1) if total_lost > 0 else 0.0
    
    recent_lost = LostItem.query.order_by(LostItem.created_at.desc()).limit(5).all()
    recent_found = FoundItem.query.order_by(FoundItem.created_at.desc()).limit(5).all()
    recent_matches = Match.query.order_by(Match.similarity_score.desc()).limit(6).all()
    recent_users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).limit(5).all()
    
    stats = {
        'total_users': total_users,
        'total_lost': total_lost,
        'total_found': total_found,
        'total_recovered': total_recovered,
        'total_claimed': total_claimed,
        'total_matches': total_matches,
        'high_confidence_matches': high_confidence_matches,
        'recovery_rate': recovery_rate
    }
    
    return render_template(
        'admin_dashboard.html',
        stats=stats,
        recent_lost=recent_lost,
        recent_found=recent_found,
        recent_matches=recent_matches,
        recent_users=recent_users
    )


@admin_bp.route('/students')
def students():
    search_q = request.args.get('q', '').strip()
    query = User.query.filter_by(is_admin=False)
    
    if search_q:
        query = query.filter(
            (User.name.ilike(f'%{search_q}%')) |
            (User.email.ilike(f'%{search_q}%')) |
            (User.student_id.ilike(f'%{search_q}%')) |
            (User.department.ilike(f'%{search_q}%'))
        )
        
    students_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin_students.html', students=students_list, search_q=search_q)


@admin_bp.route('/students/<int:user_id>/toggle-status', methods=['POST'])
def toggle_student_status(user_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('admin.students'))
        
    user = db.get_or_404(User, user_id)
    if user.is_admin:
        flash('Cannot deactivate an administrator account.', 'danger')
        return redirect(url_for('admin.students'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status_str = "activated" if user.is_active else "deactivated"
    flash(f"Student {user.name} ({user.student_id}) has been {status_str}.", 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/matches')
def matches():
    all_matches = Match.query.order_by(Match.similarity_score.desc()).all()
    
    high_count = sum(1 for m in all_matches if m.similarity_score >= 70.0)
    moderate_count = sum(1 for m in all_matches if 45.0 <= m.similarity_score < 70.0)
    low_count = sum(1 for m in all_matches if m.similarity_score < 45.0)
    
    match_analytics = {
        'total': len(all_matches),
        'high': high_count,
        'moderate': moderate_count,
        'low': low_count
    }
    
    return render_template('admin_matches.html', matches=all_matches, analytics=match_analytics)


@admin_bp.route('/reports/lost/<int:item_id>/delete', methods=['POST'])
def delete_lost_report(item_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    item = db.get_or_404(LostItem, item_id)
    name = item.item_name
    db.session.delete(item)
    db.session.commit()
    
    flash(f"Moderation action: Lost report '{name}' removed by administrator.", 'warning')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reports/found/<int:item_id>/delete', methods=['POST'])
def delete_found_report(item_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    item = db.get_or_404(FoundItem, item_id)
    name = item.item_name
    db.session.delete(item)
    db.session.commit()
    
    flash(f"Moderation action: Found report '{name}' removed by administrator.", 'warning')
    return redirect(url_for('admin.dashboard'))
