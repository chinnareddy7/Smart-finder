from flask import Blueprint, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, ContactRequest, LostItem, FoundItem, Notification
from utils import validate_csrf

requests_bp = Blueprint('requests', __name__)

@requests_bp.route('/request/send', methods=['POST'])
@login_required
def send_request():
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(request.referrer or url_for('student.dashboard'))
        
    item_type = request.form.get('item_type')  # 'lost' or 'found'
    item_id = request.form.get('item_id', type=int)
    message = request.form.get('message', '').strip()
    
    if not message:
        flash('Please provide a message or proof description for your claim/inquiry.', 'warning')
        return redirect(request.referrer or url_for('student.dashboard'))
        
    lost_item = None
    found_item = None
    receiver_id = None
    item_title = ""
    
    if item_type == 'lost':
        lost_item = db.get_or_404(LostItem, item_id)
        receiver_id = lost_item.user_id
        item_title = lost_item.item_name
        if receiver_id == current_user.id:
            flash('You cannot send a contact request for your own reported item.', 'warning')
            return redirect(url_for('lost.details', item_id=lost_item.id))
            
        # Check if already sent
        existing = ContactRequest.query.filter_by(
            sender_id=current_user.id,
            lost_item_id=lost_item.id
        ).first()
        if existing:
            flash(f"You have already submitted a request for '{item_title}' (Status: {existing.status}).", 'info')
            return redirect(url_for('lost.details', item_id=lost_item.id))
            
    elif item_type == 'found':
        found_item = db.get_or_404(FoundItem, item_id)
        receiver_id = found_item.user_id
        item_title = found_item.item_name
        if receiver_id == current_user.id:
            flash('You cannot send a claim request for your own reported found item.', 'warning')
            return redirect(url_for('found.details', item_id=found_item.id))
            
        existing = ContactRequest.query.filter_by(
            sender_id=current_user.id,
            found_item_id=found_item.id
        ).first()
        if existing:
            flash(f"You have already submitted a claim request for '{item_title}' (Status: {existing.status}).", 'info')
            return redirect(url_for('found.details', item_id=found_item.id))
    else:
        abort(400)
        
    # Create request
    contact_req = ContactRequest(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        item_type=item_type,
        lost_item_id=lost_item.id if lost_item else None,
        found_item_id=found_item.id if found_item else None,
        message=message,
        status='Pending'
    )
    db.session.add(contact_req)
    
    # Create Notification for receiver
    req_type_label = "Claim Request" if item_type == 'found' else "Contact Inquiry"
    notif = Notification(
        user_id=receiver_id,
        title=f"New {req_type_label} on '{item_title}'",
        message=f"Student {current_user.name} ({current_user.department}) sent a {req_type_label.lower()}: '{message[:60]}...'",
        notification_type='contact_request',
        link=url_for('student.my_reports', tab='incoming')
    )
    db.session.add(notif)
    db.session.commit()
    
    flash(f"Your request regarding '{item_title}' has been submitted to the reporter.", 'success')
    return redirect(request.referrer or url_for('student.dashboard'))


@requests_bp.route('/request/<int:req_id>/respond', methods=['POST'])
@login_required
def respond_request(req_id):
    contact_req = db.get_or_404(ContactRequest, req_id)
    if contact_req.receiver_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('student.my_reports', tab='incoming'))
        
    action = request.form.get('action')  # 'accept' or 'reject'
    response_note = request.form.get('response_note', '').strip()
    
    if action == 'accept':
        contact_req.status = 'Accepted'
        contact_req.response_note = response_note or 'Request accepted. You can now view each other\'s direct contact details.'
        
        # Send Notification to requester
        item_name = contact_req.lost_item.item_name if contact_req.lost_item else contact_req.found_item.item_name
        notif = Notification(
            user_id=contact_req.sender_id,
            title=f"Request Accepted for '{item_name}'!",
            message=f"Reporter {current_user.name} accepted your request! Contact details are now unlocked in 'My Reports'.",
            notification_type='request_accepted',
            link=url_for('student.my_reports', tab='outgoing')
        )
        db.session.add(notif)
        flash('Contact request accepted. Private student contact details have been shared with the requester.', 'success')
        
    elif action == 'reject':
        contact_req.status = 'Rejected'
        contact_req.response_note = response_note or 'Claim details could not be verified.'
        
        item_name = contact_req.lost_item.item_name if contact_req.lost_item else contact_req.found_item.item_name
        notif = Notification(
            user_id=contact_req.sender_id,
            title=f"Request Declined for '{item_name}'",
            message=f"Your request was declined by the reporter. Note: {contact_req.response_note}",
            notification_type='request_rejected',
            link=url_for('student.my_reports', tab='outgoing')
        )
        db.session.add(notif)
        flash('Contact request declined.', 'info')
        
    db.session.commit()
    return redirect(url_for('student.my_reports', tab='incoming'))
