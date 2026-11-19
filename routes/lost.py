
from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, abort
)
from flask_login import login_required, current_user

from models import db, LostItem, Match, ContactRequest
from utils import ImageUploadError, save_uploaded_image, validate_csrf
from ai_engine.matching import sync_matches_for_lost_item


lost_bp = Blueprint('lost', __name__)


@lost_bp.route('/lost-items')
def browse():
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    location = request.args.get('location', '').strip()
    status = request.args.get('status', 'All').strip()

    query = LostItem.query

    if query_text:
        query = query.filter(
            (LostItem.item_name.ilike(f'%{query_text}%')) |
            (LostItem.description.ilike(f'%{query_text}%')) |
            (LostItem.additional_details.ilike(f'%{query_text}%'))
        )

    if category and category != 'All':
        query = query.filter_by(category=category)

    if location and location != 'All':
        query = query.filter_by(location=location)

    if status and status != 'All':
        query = query.filter_by(status=status)
    else:
        # By default show Lost items first
        query = query.order_by(LostItem.status.asc())

    items = query.order_by(LostItem.created_at.desc()).all()

    return render_template(
        'lost_items.html',
        items=items,
        search_query=query_text,
        selected_category=category,
        selected_location=location,
        selected_status=status
    )


@lost_bp.route('/lost/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')

        if not validate_csrf(csrf_token):
            flash(
                'Security validation token mismatch. Please try again.',
                'danger'
            )
            return redirect(url_for('lost.report'))

        item_name = request.form.get('item_name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        lost_date_str = request.form.get('lost_date', '').strip()

        additional_details = request.form.get(
            'additional_details', ''
        ).strip()

        # Contact Details
        contact_name = request.form.get('contact_name', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_public = request.form.get('contact_public') == 'on'

        # Validate Required Fields
        if not all([
            item_name, category, description, location, lost_date_str
        ]):
            flash('Please fill in all mandatory fields.', 'warning')
            return render_template(
                'report_lost.html',
                form_data=request.form
            )

        try:
            lost_date = datetime.strptime(
                lost_date_str, '%Y-%m-%d'
            ).date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
            return render_template(
                'report_lost.html',
                form_data=request.form
            )

        # Image Upload
        image_file = request.files.get('image')
        image_filename = None

        if image_file and image_file.filename != '':
            try:
                image_filename = save_uploaded_image(image_file)
            except ImageUploadError as e:
                flash(str(e), 'danger')
                return render_template(
                    'report_lost.html',
                    form_data=request.form
                )

        # Save Lost Item
        lost_item = LostItem(
            user_id=current_user.id,
            item_name=item_name,
            category=category,
            description=description,
            location=location,
            lost_date=lost_date,
            additional_details=additional_details,
            contact_name=contact_name,
            contact_phone=contact_phone,
            contact_email=contact_email,
            contact_public=contact_public,
            image_filename=image_filename,
            status='Lost'
        )

        db.session.add(lost_item)
        db.session.commit()

        # Run AI Matching Engine
        matches = sync_matches_for_lost_item(
            db,
            lost_item,
            threshold=current_app.config['AI_MATCH_THRESHOLD'],
            top_limit=current_app.config['AI_TOP_MATCHES_LIMIT']
        )

        if matches:
            best_match = matches[0]

            flash(
                f"Lost item reported successfully! AI Engine "
                f"detected {len(matches)} potential match(es) "
                f"(Top score: {best_match.similarity_score}%). "
                f"Check your dashboard!",
                'success'
            )
        else:
            flash(
                "Lost item reported successfully! Our AI is "
                "actively monitoring incoming reports for matches.",
                'success'
            )

        return redirect(
            url_for('lost.details', item_id=lost_item.id)
        )

    return render_template('report_lost.html')


@lost_bp.route('/lost/<int:item_id>')
def details(item_id):
    item = db.get_or_404(LostItem, item_id)

    # Check if current user is owner or admin
    is_owner = current_user.is_authenticated and (
        current_user.id == item.user_id or current_user.is_admin
    )

    # Matches Associated With This Item
    matches = []

    if is_owner:
        matches = item.matches.filter(
            Match.status != 'Dismissed'
        ).order_by(
            Match.similarity_score.desc()
        ).all()

    # Check Existing Contact Request
    user_request = None

    if (
        current_user.is_authenticated
        and current_user.id != item.user_id
    ):
        user_request = ContactRequest.query.filter_by(
            sender_id=current_user.id,
            lost_item_id=item.id
        ).first()

    return render_template(
        'item_details.html',
        item=item,
        item_type='lost',
        is_owner=is_owner,
        matches=matches,
        user_request=user_request
    )


@lost_bp.route('/lost/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    item = db.get_or_404(LostItem, item_id)

    if item.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')

        if not validate_csrf(csrf_token):
            flash('Security validation token mismatch.', 'danger')
            return redirect(
                url_for('lost.edit', item_id=item.id)
            )

        item.item_name = request.form.get(
            'item_name', ''
        ).strip()

        item.category = request.form.get(
            'category', ''
        ).strip()

        item.description = request.form.get(
            'description', ''
        ).strip()

        item.location = request.form.get(
            'location', ''
        ).strip()

        lost_date_str = request.form.get(
            'lost_date', ''
        ).strip()

        item.additional_details = request.form.get(
            'additional_details', ''
        ).strip()

        # Update Contact Details
        item.contact_name = request.form.get(
            'contact_name', ''
        ).strip()

        item.contact_phone = request.form.get(
            'contact_phone', ''
        ).strip()

        item.contact_email = request.form.get(
            'contact_email', ''
        ).strip()

        item.contact_public = (
            request.form.get('contact_public') == 'on'
        )

        # Update Lost Date
        if lost_date_str:
            try:
                item.lost_date = datetime.strptime(
                    lost_date_str, '%Y-%m-%d'
                ).date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(
                    url_for('lost.edit', item_id=item.id)
                )

        # Optional Image Update
        image_file = request.files.get('image')

        if image_file and image_file.filename != '':
            try:
                new_filename = save_uploaded_image(image_file)
            except ImageUploadError as e:
                db.session.rollback()
                flash(str(e), 'danger')
                return redirect(
                    url_for('lost.edit', item_id=item_id)
                )

            item.image_filename = new_filename

        db.session.commit()

        # Refresh AI Matches
        sync_matches_for_lost_item(
            db,
            item,
            threshold=current_app.config['AI_MATCH_THRESHOLD']
        )

        flash(
            'Lost item report successfully updated and AI matches refreshed.',
            'success'
        )

        return redirect(
            url_for('lost.details', item_id=item.id)
        )

    return render_template(
        'edit_report.html',
        item=item,
        item_type='lost'
    )


@lost_bp.route('/lost/<int:item_id>/delete', methods=['POST'])
@login_required
def delete(item_id):
    item = db.get_or_404(LostItem, item_id)

    if item.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    csrf_token = request.form.get('csrf_token')

    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('student.my_reports'))

    item_name = item.item_name

    db.session.delete(item)
    db.session.commit()

    flash(f"Report for '{item_name}' has been deleted.", 'info')

    return redirect(
        url_for('student.my_reports', tab='lost')
    )


@lost_bp.route('/lost/<int:item_id>/recover', methods=['POST'])
@login_required
def mark_recovered(item_id):
    item = db.get_or_404(LostItem, item_id)

    if item.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    csrf_token = request.form.get('csrf_token')

    if not validate_csrf(csrf_token):
        flash('Security token invalid.', 'danger')
        return redirect(
            url_for('lost.details', item_id=item.id)
        )

    item.status = 'Recovered'
    db.session.commit()

    flash(
        f"Congratulations! '{item.item_name}' is marked as recovered.",
        'success'
    )

    return redirect(
        url_for('lost.details', item_id=item.id)
    )
