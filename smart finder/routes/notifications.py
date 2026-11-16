from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Notification
from utils import validate_csrf

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications')
@login_required
def index():
    filter_type = request.args.get('filter', 'all')
    
    query = current_user.notifications
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
        
    notifications_list = query.all()
    
    return render_template(
        'notifications.html',
        notifications=notifications_list,
        filter_type=filter_type
    )


@notifications_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security token invalid.', 'danger')
        return redirect(url_for('notifications.index'))
        
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    
    next_url = request.form.get('next') or notif.link or url_for('notifications.index')
    return redirect(next_url)


@notifications_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security token invalid.', 'danger')
        return redirect(url_for('notifications.index'))
        
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))
