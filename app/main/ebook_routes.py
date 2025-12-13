from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.main import bp
from app.extensions import db
from app.models import EBook
import os
from werkzeug.utils import secure_filename
from datetime import datetime

ALLOWED_EXTENSIONS = {'pdf', 'mp3', 'wav'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_audio_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mp3', 'wav'}

def is_pdf_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == 'pdf'

@bp.route('/ebooks')
def ebook_list():
    ebooks = EBook.query.order_by(EBook.uploaded_at.desc()).all()
    return render_template('ebooks/list.html', ebooks=ebooks)

@bp.route('/ebooks/upload', methods=['GET', 'POST'])
@login_required
def ebook_upload():
    if not current_user.is_admin():
        flash('You are not authorized to upload E-books.', 'danger')
        return redirect(url_for('main.ebook_list'))

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        cover_image = request.files.get('cover_image')
        audio_file = request.files.get('audio_file')

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and is_pdf_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'ebooks')
            audio_folder = os.path.join(current_app.root_path, 'static', 'ebooks', 'audio')
            
            # Ensure directories exist
            os.makedirs(upload_folder, exist_ok=True)
            os.makedirs(audio_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # Handle Audio File
            audio_filename_str = None
            if audio_file and audio_file.filename != '' and is_audio_file(audio_file.filename):
                audio_filename = secure_filename(audio_file.filename)
                audio_path = os.path.join(audio_folder, audio_filename)
                audio_file.save(audio_path)
                audio_filename_str = audio_filename # Store purely filename, path relative to static/ebooks/audio
            
            # Handle Cover Image
            cover_image_url = None
            if cover_image and cover_image.filename != '':
                cover_filename = secure_filename(cover_image.filename)
                cover_path = os.path.join(current_app.root_path, 'static', 'ebooks', 'covers')
                os.makedirs(cover_path, exist_ok=True)
                cover_image.save(os.path.join(cover_path, cover_filename))
                cover_image_url = url_for('static', filename=f'ebooks/covers/{cover_filename}')
            
            new_ebook = EBook(
                title=title,
                author=author,
                description=description,
                file_path=filename, # Store filename relative to static/ebooks
                audio_path=audio_filename_str,
                cover_image_url=cover_image_url if cover_image_url else 'https://placehold.co/200x300?text=No+Cover'
            )
            
            db.session.add(new_ebook)
            db.session.commit()
            
            flash('E-book uploaded successfully!', 'success')
            return redirect(url_for('main.ebook_list'))
        else:
            flash('Invalid file type. Only PDF allowed.', 'danger')

    return render_template('ebooks/upload.html')

@bp.route('/ebooks/read/<int:id>')
@login_required
def ebook_read(id):
    ebook = EBook.query.get_or_404(id)
    return render_template('ebooks/read.html', ebook=ebook)

@bp.route('/ebooks/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def ebook_edit(id):
    if not current_user.is_admin():
        flash('You are not authorized to edit E-books.', 'danger')
        return redirect(url_for('main.ebook_list'))
    
    ebook = EBook.query.get_or_404(id)

    if request.method == 'POST':
        ebook.title = request.form.get('title')
        ebook.author = request.form.get('author')
        ebook.description = request.form.get('description')

        # Handle File Update
        file = request.files.get('file')
        if file and file.filename != '' and is_pdf_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'ebooks')
            
            # Remove old file
            if ebook.file_path:
                old_file_path = os.path.join(upload_folder, ebook.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Save new file
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            ebook.file_path = filename

        # Handle Audio Update
        audio_file = request.files.get('audio_file')
        if audio_file:
            # Check if user uploaded a file
            if audio_file.filename != '' and is_audio_file(audio_file.filename):
                audio_filename = secure_filename(audio_file.filename)
                audio_folder = os.path.join(current_app.root_path, 'static', 'ebooks', 'audio')
                os.makedirs(audio_folder, exist_ok=True)

                # Remove old audio
                if ebook.audio_path:
                    old_audio_path = os.path.join(audio_folder, ebook.audio_path)
                    if os.path.exists(old_audio_path):
                        os.remove(old_audio_path)
                
                # Save new audio
                new_audio_path = os.path.join(audio_folder, audio_filename)
                audio_file.save(new_audio_path)
                ebook.audio_path = audio_filename

        # Handle Cover Update
        cover_image = request.files.get('cover_image')
        if cover_image and cover_image.filename != '':
            cover_filename = secure_filename(cover_image.filename)
            cover_path = os.path.join(current_app.root_path, 'static', 'ebooks', 'covers')
            
            # Remove old cover if it's not the placeholder
            if 'placehold.co' not in ebook.cover_image_url:
                old_cover_name = ebook.cover_image_url.split('/')[-1]
                old_cover_path = os.path.join(cover_path, old_cover_name)
                if os.path.exists(old_cover_path):
                    os.remove(old_cover_path)

            cover_image.save(os.path.join(cover_path, cover_filename))
            ebook.cover_image_url = url_for('static', filename=f'ebooks/covers/{cover_filename}')

        db.session.commit()
        flash('E-book updated successfully!', 'success')
        return redirect(url_for('main.ebook_list'))

    return render_template('ebooks/edit.html', ebook=ebook)

@bp.route('/ebooks/listen/<int:id>')
@login_required
def ebook_listen(id):
    ebook = EBook.query.get_or_404(id)
    if not ebook.audio_path:
        flash('Audio book not available for this title.', 'warning')
        return redirect(url_for('main.ebook_list'))
    return render_template('ebooks/listen.html', ebook=ebook)

@bp.route('/ebooks/delete/<int:id>', methods=['POST'])
@login_required
def ebook_delete(id):
    if not current_user.is_admin():
        flash('You are not authorized to delete E-books.', 'danger')
        return redirect(url_for('main.ebook_list'))
    
    ebook = EBook.query.get_or_404(id)
    
    # Remove files
    upload_folder = os.path.join(current_app.root_path, 'static', 'ebooks')
    
    # Remove PDF
    if ebook.file_path:
        file_path = os.path.join(upload_folder, ebook.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    # Remove Audio
    if ebook.audio_path:
        audio_path = os.path.join(upload_folder, 'audio', ebook.audio_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)

    # Remove Cover
    if 'placehold.co' not in ebook.cover_image_url:
        cover_name = ebook.cover_image_url.split('/')[-1]
        cover_path = os.path.join(upload_folder, 'covers', cover_name)
        if os.path.exists(cover_path):
            os.remove(cover_path)

    db.session.delete(ebook)
    db.session.commit()
    flash('E-book deleted successfully.', 'success')
    return redirect(url_for('main.ebook_list'))
