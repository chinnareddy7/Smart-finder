from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, LostItem, FoundItem, Match, ContactRequest, Notification

student_bp = Blueprint('student', __name__)

@student_bp.route('/')
def index():
    # Public home page
    # Live stats
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()
    total_recovered = LostItem.query.filter_by(status='Recovered').count()
    total_matches = Match.query.filter(Match.similarity_score >= 35.0).count()
    
    # Recent items
    recent_lost = LostItem.query.order_by(LostItem.created_at.desc()).limit(6).all()
    recent_found = FoundItem.query.order_by(FoundItem.created_at.desc()).limit(6).all()
    
    stats = {
        'total_lost': total_lost,
        'total_found': total_found,
        'total_recovered': total_recovered,
        'total_matches': total_matches,
        'recovery_rate': round((total_recovered / total_lost * 100), 1) if total_lost > 0 else 0.0
    }
    
    return render_template('index.html', stats=stats, recent_lost=recent_lost, recent_found=recent_found)


@student_bp.route('/dashboard')
@login_required
def dashboard():
    # Student specific stats
    my_lost_count = current_user.lost_items.count()
    my_found_count = current_user.found_items.count()
    my_recovered_count = current_user.lost_items.filter_by(status='Recovered').count()
    
    # Overall campus counters
    campus_lost_count = LostItem.query.count()
    campus_found_count = FoundItem.query.count()
    campus_recovered_count = LostItem.query.filter_by(status='Recovered').count()
    
    # AI suggested matches for the student's lost items
    my_lost_ids = [item.id for item in current_user.lost_items.all()]
    ai_matches = []
    if my_lost_ids:
        ai_matches = Match.query.filter(
            Match.lost_item_id.in_(my_lost_ids),
            Match.status != 'Dismissed'
        ).order_by(Match.similarity_score.desc()).limit(6).all()
        
    # Pending contact requests received
    pending_incoming_requests = ContactRequest.query.filter_by(
        receiver_id=current_user.id,
        status='Pending'
    ).order_by(ContactRequest.created_at.desc()).all()
    
    # Recent notifications
    recent_notifications = current_user.notifications.limit(5).all()
    
    # Student's recent reports
    recent_lost = current_user.lost_items.order_by(LostItem.created_at.desc()).limit(3).all()
    recent_found = current_user.found_items.order_by(FoundItem.created_at.desc()).limit(3).all()
    
    return render_template(
        'dashboard.html',
        my_lost_count=my_lost_count,
        my_found_count=my_found_count,
        my_recovered_count=my_recovered_count,
        campus_lost_count=campus_lost_count,
        campus_found_count=campus_found_count,
        campus_recovered_count=campus_recovered_count,
        ai_matches=ai_matches,
        pending_requests=pending_incoming_requests,
        notifications=recent_notifications,
        recent_lost=recent_lost,
        recent_found=recent_found
    )


@student_bp.route('/my-reports')
@login_required
def my_reports():
    tab = request.args.get('tab', 'lost')
    
    my_lost_items = current_user.lost_items.order_by(LostItem.created_at.desc()).all()
    my_found_items = current_user.found_items.order_by(FoundItem.created_at.desc()).all()
    
    # Contact requests
    incoming_requests = ContactRequest.query.filter_by(receiver_id=current_user.id).order_by(ContactRequest.created_at.desc()).all()
    outgoing_requests = ContactRequest.query.filter_by(sender_id=current_user.id).order_by(ContactRequest.created_at.desc()).all()
    
    return render_template(
        'my_reports.html',
        tab=tab,
        my_lost_items=my_lost_items,
        my_found_items=my_found_items,
        incoming_requests=incoming_requests,
        outgoing_requests=outgoing_requests
    )
