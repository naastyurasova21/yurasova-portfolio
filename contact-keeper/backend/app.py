import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from database import db
from models import (
    ALL_GROUPS_LABEL,
    CONTACT_GROUPS,
    ContactGroup,
    Contact,
    ContactRepository,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
contact_repo = ContactRepository(db)

@app.context_processor
def utility_processor():
    return dict(groups=CONTACT_GROUPS)

def build_contact_from_form(form_data, contact_id=None, created_at=None, default_group=ContactGroup.GENERAL):
    return Contact(
        id=contact_id,
        last_name=form_data['last_name'].strip(),
        first_name=form_data['first_name'].strip(),
        middle_name=form_data.get('middle_name', '').strip(),
        phone_number=Contact.normalize_phone_number(form_data.get('phone_number', '')),
        note=form_data.get('note', '').strip(),
        contact_group=ContactGroup.parse(form_data.get('contact_group', default_group.value)),
        is_favorite='is_favorite' in form_data,
        created_at=created_at,
        updated_at=None
    )

def get_contact_form_error_message(error, action):
    error_text = str(error)

    if isinstance(error, ValueError):
        return error_text

    if 'duplicate key value violates unique constraint' in error_text and 'phone_number' in error_text:
        return 'Contact already exist'

    return f'Error when {action}: {error_text}'

@app.route('/')
def index():
    group = request.args.get('group', ALL_GROUPS_LABEL)
    search = request.args.get('search', '')
    
    contacts = contact_repo.get_all(group=group, search=search)
    groups = contact_repo.get_groups()
    
    return render_template(
        'index.html',
        contacts=contacts,
        current_group=group,
        search_query=search,
        groups=groups,
        total=len(contacts)
    )

@app.route('/contact/<int:contact_id>')
def view_contact(contact_id):
    contact = contact_repo.get_by_id(contact_id)
    if not contact:
        flash('Contact was not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('view.html', contact=contact)

@app.route('/contact/add', methods=['GET', 'POST'])
def add_contact():
    if request.method == 'POST':
        try:
            contact = build_contact_from_form(request.form)
            contact_id = contact_repo.create(contact)
            flash(f'Contact successfully added', 'success')
            return redirect(url_for('view_contact', contact_id=contact_id))
        
        except Exception as e:
            flash(get_contact_form_error_message(e, 'добавлении'), 'error')
    
    return render_template('add.html', groups=CONTACT_GROUPS)

@app.route('/contact/<int:contact_id>/edit', methods=['GET', 'POST'])
def edit_contact(contact_id):
    contact = contact_repo.get_by_id(contact_id)
    if not contact:
        flash('Contact was not found', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            updated_contact = build_contact_from_form(
                request.form,
                contact_id=contact_id,
                created_at=contact.created_at,
                default_group=contact.contact_group
            )
            contact_repo.update(contact_id, updated_contact)
            flash('Contact was successfully updated', 'success')
            return redirect(url_for('view_contact', contact_id=contact_id))
        
        except Exception as e:
            flash(get_contact_form_error_message(e, 'update'), 'error')
    
    return render_template('edit.html', contact=contact, groups=CONTACT_GROUPS)

@app.route('/contact/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    try:
        contact_repo.delete(contact_id)
        flash('Contact deleted', 'success')
    except Exception as e:
        flash(f'Error when deleting: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/contact/<int:contact_id>/favorite', methods=['POST'])
def toggle_favorite(contact_id):
    try:
        updated = contact_repo.toggle_favorite(contact_id)
        if not updated:
            message = 'Contact was not found'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': message}), 404
            flash(message, 'error')
            return redirect(request.referrer or url_for('index'))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return redirect(request.referrer or url_for('index'))

@app.route('/api/contacts')
def api_contacts():
    group = request.args.get('group', ALL_GROUPS_LABEL)
    search = request.args.get('search', '')
    
    contacts = contact_repo.get_all(group=group, search=search)
    return jsonify([{
        'id': c.id,
        'full_name': c.full_name,
        'phone': c.formatted_phone,
        'note': c.note,
        'group': c.contact_group.value,
        'is_favorite': c.is_favorite
    } for c in contacts])

@app.errorhandler(404)
def not_found_error(error):
    return render_template(
        'error.html',
        error_code=404,
        title='Page was not found',
        message='Page does not exist or has been moved',
        action_url=url_for('index'),
        action_text='Return to the main page'
    ), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template(
        'error.html',
        error_code=500,
        title='Server error',
        message='Internal error. Try again later',
        action_url=url_for('index'),
        action_text='Open the main page'
    ), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
