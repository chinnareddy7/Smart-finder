from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, Match, LostItem, FoundItem
from utils import validate_csrf
from ai_engine.matching import recalculate_all_matches

matches_bp = Blueprint('matches', __name__)

@matches_bp.route('/matches')
@login_required
def index():
    filter_tier = request.args.get('tier', 'all')
    
    if current_user.is_admin:
        # Admin can view all matches
        query = Match.query.join(LostItem).join(FoundItem)
    else:
        # Student views matches for their lost or found items
        my_lost_ids = [l.id for l in current_user.lost_items]
        my_found_ids = [f.id for f in current_user.found_items]
        
        query = Match.query.filter(
            (Match.lost_item_id.in_(my_lost_ids)) | (Match.found_item_id.in_(my_found_ids)),
            Match.status != 'Dismissed'
        )
        
    if filter_tier == 'high':
        query = query.filter(Match.similarity_score >= 70.0)
    elif filter_tier == 'moderate':
        query = query.filter(Match.similarity_score >= 45.0, Match.similarity_score < 70.0)
        
    matches = query.order_by(Match.similarity_score.desc()).all()
    
    return render_template(
        'matches.html',
        matches=matches,
        filter_tier=filter_tier
    )


@matches_bp.route('/matches/<int:match_id>/dismiss', methods=['POST'])
@login_required
def dismiss(match_id):
    match = db.get_or_404(Match, match_id)
    
    # Verify permission
    is_authorized = (
        current_user.is_admin or
        match.lost_item.user_id == current_user.id or
        match.found_item.user_id == current_user.id
    )
    if not is_authorized:
        abort(403)
        
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('matches.index'))
        
    match.status = 'Dismissed'
    db.session.commit()
    
    flash('Match recommendation dismissed.', 'info')
    return redirect(url_for('matches.index'))


@matches_bp.route('/matches/recalculate', methods=['POST'])
@login_required
def recalculate():
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('matches.index'))
        
    updated_count = recalculate_all_matches(db)
    flash(f'AI Matching Engine executed successfully. Updated/computed {updated_count} comparison pairs.', 'success')
    return redirect(url_for('matches.index'))
