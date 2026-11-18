
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from models import db, FoundItem, LostItem, Match, ContactRequest
from utils import ImageUploadError, save_uploaded_image, validate_csrf
from ai_engine.matching import sync_matches_for_found_item

found_bp = Blueprint('found', __name__)


@found_bp.route('/found-items')
def browse():
    query_text = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    location = request.args.get('location', '').strip()
    status = request.args.get('status', 'All').strip()

    query = FoundItem.query

    if query_text:
        query = query.filter(
            (FoundItem.item_name.ilike(f'%{query_text}%')) |
            (FoundItem.description.ilike(f'%{query_text}%')) |
            (FoundItem.additional_details.ilike(f'%{query_text}%')) |
            (FoundItem.storage_location.ilike(f'%{query_text}%'))
        )

    if category and category != 'All':
        query = query.filter_by(category=category)

    if location and location != 'All':
        query = query.filter_by(location=location)

    if status and status != 'All':
        query = query.filter_by(status=status)
    else:
        query = query.order_by(FoundItem.status.asc())

    items = query.order_by(FoundItem.created_at.desc()).all()

    return render_template(
        'found_items.html',
        items=items,
        search_query=query_text,
        selected_category=category,
        selected_location=location,
        selected_status=status
    )


@found_bp.route('/found/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf(csrf_token):
            flash('Security validation token mismatch. Please try again.', 'danger')
            return redirect(url_for('found.report'))

        item_name = request.form.get('item_name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        found_date_str = request.form.get('found_date', '').strip()
        storage_location = request.form.get('storage_location', '').strip()
        additional_details = request.form.get('additional_details', '').strip()

        # Validation
        if not all([item_name, category, description, location, found_date_str]):
            flash('Please fill in all mandatory fields.', 'warning')
            return render_template('report_found.html', form_data=request.form)

        try:
            found_date = datetime.strptime(found_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
            return render_template('report_found.html', form_data=request.form)

        # Image upload
        image_file = request.files.get('image')
        image_filename = None

        if image_file and image_file.filename != '':
            try:
                image_filename = save_uploaded_image(image_file)
            except ImageUploadError as e:
                flash(str(e), 'danger')
                return render_template(
                    'report_found.html',
                    form_data=request.form
                )

        # Save found item
        found_item = FoundItem(
            user_id=current_user.id,
            item_name=item_name,
            category=category,
            description=description,
            location=location,
            found_date=found_date,
            storage_location=storage_location or 'With Finder / Reach out via platform',
            additional_details=additional_details,
            image_filename=image_filename,
            status='Found'
        )
        db.session.add(found_item)
        db.session.commit()

        # Run AI matching against active lost items
        matches = sync_matches_for_found_item(
            db,
            found_item,
            threshold=current_app.config['AI_MATCH_THRESHOLD'],
            top_limit=current_app.config['AI_TOP_MATCHES_LIMIT']
        )

        if matches:
            best_match = matches[0]
            flash(
                f"Found item recorded! AI Engine identified {len(matches)} student lost report(s) matching this item (Top match: {best_match.similarity_score}%). Notification sent to the possible owner!",
                'success'
            )
        else:
            flash("Found item registered successfully! Thank you for being a responsible campus citizen.", 'success')

        return redirect(url_for('found.details', item_id=found_item.id))

    return render_template('report_found.html')


@found_bp.route('/found/<int:item_id>')
def details(item_id):
    item = db.get_or_404(FoundItem, item_id)

    is_owner = current_user.is_authenticated and (
        current_user.id == item.user_id or current_user.is_admin
    )

    matches = []
    if is_owner:
        matches = item.matches.filter(
            Match.status != 'Dismissed'
        ).order_by(Match.similarity_score.desc()).all()

    user_request = None
    if current_user.is_authenticated and current_user.id != item.user_id:
        user_request = ContactRequest.query.filter_by(
            sender_id=current_user.id,
            found_item_id=item.id
        ).first()

    return render_template(
        'item_details.html',
        item=item,
        item_type='found',
        is_owner=is_owner,
        matches=matches,
        user_request=user_request
    )


@found_bp.route('/found/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    item = db.get_or_404(FoundItem, item_id)

    if item.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf(csrf_token):
            flash('Security validation token mismatch.', 'danger')
            return redirect(url_for('found.edit', item_id=item.id))

        item.item_name = request.form.get('item_name', '').strip()
        item.category = request.form.get('category', '').strip()
        item.description = request.form.get('description', '').strip()
        item.location = request.form.get('location', '').strip()
        found_date_str = request.form.get('found_date', '').strip()
        item.storage_location = request.form.get('storage_location', '').strip()
        item.additional_details = request.form.get('additional_details', '').strip()

        if found_date_str:
            try:
                item.found_date = datetime.strptime(
                    found_date_str, '%Y-%m-%d'
                ).date()
            except ValueError:
                pass

        # Optional image update
        image_file = request.files.get('image')

        if image_file and image_file.filename != '':
            try:
                new_filename = save_uploaded_image(image_file)
            except ImageUploadError as e:
                db.session.rollback()
                flash(str(e), 'danger')
                return redirect(url_for('found.edit', item_id=item_id))

            item.image_filename = new_filename

        db.session.commit()

        sync_matches_for_found_item(
            db,
            item,
            threshold=current_app.config['AI_MATCH_THRESHOLD']
        )

        flash('Found item report updated and AI matches updated.', 'success')
        return redirect(url_for('found.details', item_id=item.id))

    return render_template('edit_report.html', item=item, item_type='found')


@found_bp.route('/found/<int:item_id>/delete', methods=['POST'])
@login_required
def delete(item_id):
    item = db.get_or_404(FoundItem, item_id)

    if item.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security validation token mismatch.', 'danger')
        return redirect(url_for('student.my_reports'))

    item_name = item.item_name
    db.session.delete(item)
    db.session.commit()

    flash(f"Found report for '{item_name}' removed.", 'info')
    return redirect(url_for('student.my_reports', tab='found'))


@found_bp.route('/found/<int:item_id>/claim-status', methods=['POST'])
@login_required
def mark_claimed(item_id):
    item = db.get_or_404(FoundItem, item_id)

    if item.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    csrf_token = request.form.get('csrf_token')
    if not validate_csrf(csrf_token):
        flash('Security token invalid.', 'danger')
        return redirect(url_for('found.details', item_id=item.id))

    new_status = request.form.get('status', 'Claimed')

    if new_status in ['Found', 'Claimed', 'Handed Over']:
        item.status = new_status
        db.session.commit()
        flash(f"Status updated to '{new_status}'.", 'success')

    return redirect(url_for('found.details', item_id=item.id))
