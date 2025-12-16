from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.main import bp
from app import db
from app.models import Book, SupplyOrder, SupplyOrderItem, User, Supplier

THRESHOLD = 5

def get_or_create_shortlist():
    # Find an active shortlist (draft) order
    order = SupplyOrder.query.filter_by(status='shortlist').first()
    if not order:
        order = SupplyOrder(status='shortlist')
        db.session.add(order)
        db.session.commit()
    return order

@bp.route('/supplier/shortlist', methods=['GET', 'POST'])
@login_required
def supplier_shortlist():
    if not current_user.is_staff():
        flash('Access denied: Staff only.', 'danger')
        return redirect(url_for('main.index'))

    
    order = get_or_create_shortlist()


    # Find all low stock books
    low_stock_books = Book.query.filter(Book.stock_available < THRESHOLD).all()
    
    # Get IDs of books already in the shortlist
    existing_item_book_ids = [item.book_id for item in order.items]
    
    items_added = 0
    for book in low_stock_books:
        # If book defies  (low stock) and isn't already floating (in list)
        if book.id not in existing_item_book_ids:
            # Lift it up!
            new_item = SupplyOrderItem(order_id=order.id, book_id=book.id, mass=5) 
            db.session.add(new_item)
            items_added += 1
    
    if items_added > 0:
        db.session.commit()
        if items_added == 1:
            flash(f'1 item floated up to the shortlist due to low stock.', 'info')
        else:
            flash(f'{items_added} items floated up to the shortlist due to low stock.', 'info')

    items = order.items.all()
    
    # Calculate total mass
    total_mass = sum(item.mass for item in items)

    return render_template('supplier/shortlist.html', order=order, items=items, total_mass=total_mass)

@bp.route('/supplier/lift/<int:book_id>', methods=['POST'])
@login_required
def supplier_lift(book_id):
    if not current_user.is_staff():
        return redirect(url_for('main.index'))
        
    order = get_or_create_shortlist()
    
    # Check if already in list
    existing = SupplyOrderItem.query.filter_by(order_id=order.id, book_id=book_id).first()
    if existing:
        flash('This book is already in the shortlist.', 'warning')
    else:
        new_item = SupplyOrderItem(order_id=order.id, book_id=book_id, mass=5)
        db.session.add(new_item)
        db.session.commit()
        flash('Manual Lift applied! Book added to shortlist.', 'success')
        
    return redirect(url_for('main.supplier_shortlist'))

@bp.route('/supplier/drop/<int:item_id>', methods=['POST'])
@login_required
def supplier_drop(item_id):
    item = SupplyOrderItem.query.get_or_404(item_id)
    # Ensure modifying the shortlist OR pending review
    if item.order.status not in ['shortlist', 'pending_review']:
        flash('Cannot drop items from a locked order.', 'danger')
        return redirect(url_for('main.supplier_shortlist'))
        
    db.session.delete(item)
    db.session.commit()
    flash('Item dropped successfully.', 'success')
    
    # Redirect
    if item.order.status == 'pending_review':
        return redirect(url_for('main.supplier_review'))
    return redirect(url_for('main.supplier_shortlist'))

@bp.route('/supplier/adjust_mass/<int:item_id>', methods=['POST'])
@login_required
def supplier_adjust_mass(item_id):
    item = SupplyOrderItem.query.get_or_404(item_id)
    if item.order.status not in ['shortlist', 'pending_review']:
        flash('Cannot adjust mass of a locked order.', 'danger')
        return redirect(url_for('main.supplier_shortlist'))
        
    action = request.form.get('action') 
    
    if action == 'increase':
        item.mass += 1
    elif action == 'decrease':
        if item.mass > 1:
            item.mass -= 1
    
    db.session.commit()
    
    # Redirect
    if item.order.status == 'pending_review':
        return redirect(url_for('main.supplier_review'))
    return redirect(url_for('main.supplier_shortlist'))

@bp.route('/supplier/submit_review', methods=['POST'])
@login_required
def supplier_submit_review():
    order = get_or_create_shortlist()
    if order.items.count() == 0:
        flash('Shortlist is empty. Nothing to review.', 'warning')
        return redirect(url_for('main.supplier_shortlist'))
        
    order.status = 'pending_review'
    db.session.commit()
    
    flash('Order sent to Owner for Authorization.', 'success')
    return redirect(url_for('main.supplier_shortlist'))

@bp.route('/supplier/review', methods=['GET'])
@login_required
def supplier_review():
    if not current_user.is_admin():
        flash('Access denied: Owner/Admin only.', 'danger')
        return redirect(url_for('main.index'))
    
    # Find orders pending review
    orders = SupplyOrder.query.filter_by(status='pending_review').all()
    suppliers = Supplier.query.all()
    return render_template('supplier/review.html', orders=orders, suppliers=suppliers)

@bp.route('/supplier/launch/<int:order_id>', methods=['POST'])
@login_required
def supplier_launch(order_id):
    if not current_user.is_admin():
        return redirect(url_for('main.index'))

    order = SupplyOrder.query.get_or_404(order_id)
    supplier_id = request.form.get('supplier_id')
    if supplier_id:
        order.supplier_id = int(supplier_id)
    order.status = 'placed'

    
    db.session.commit()
    flash('Order Authorized! & transmitted to supplier.', 'success')
    # Redirect to confirmation page instead of review list
    return redirect(url_for('main.supplier_confirmation', order_id=order.id))

@bp.route('/supplier/confirmation/<int:order_id>', methods=['GET'])
@login_required
def supplier_confirmation(order_id):
    order = SupplyOrder.query.get_or_404(order_id)
    
    # WhatsApp Message
    items = order.items.all()
    item_details = "\n".join([f"- {item.book.title} (Qty: {item.mass})" for item in items])
    whatsapp_text = f"Hello {order.supplier.name}, Here is supply order #{order.id}:\n\n{item_details}\n\nPlease check the attached invoice."
    
    return render_template('supplier/confirmation.html', order=order, whatsapp_text=whatsapp_text)

@bp.route('/supplier/preview_invoice/<int:order_id>', methods=['GET'])
@login_required
def preview_invoice(order_id):
    order = SupplyOrder.query.get_or_404(order_id)
    return render_template('supplier/invoice.html', order=order)

from io import BytesIO
from xhtml2pdf import pisa
from flask import make_response

@bp.route('/supplier/download_invoice/<int:order_id>', methods=['GET'])
@login_required
def download_invoice(order_id):
    order = SupplyOrder.query.get_or_404(order_id)
    
    # Render HTML template with data
    html = render_template('supplier/invoice.html', order=order)
    
    # Create PDF buffer
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return 'We had some errors <pre>' + html + '</pre>'
        
    buffer.seek(0)
    
    # Create response
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Invoice_{order.id}.pdf'
    
    return response

@bp.route('/supplier/receive_list', methods=['GET'])
@login_required
def supplier_receive_list():
    if not current_user.is_staff():
         return redirect(url_for('main.index'))
         
    # List orders that are placed and waiting for delivery
    orders = SupplyOrder.query.filter_by(status='placed').all()
    return render_template('supplier/receive_list.html', orders=orders)

@bp.route('/supplier/receive/<int:order_id>', methods=['GET'])
@login_required
def supplier_receive_detail(order_id):
    if not current_user.is_staff():
         return redirect(url_for('main.index'))
         
    order = SupplyOrder.query.get_or_404(order_id)
    return render_template('supplier/receive.html', order=order)

@bp.route('/supplier/update_payload/<int:item_id>', methods=['POST'])
@login_required
def supplier_update_payload(item_id):
    item = SupplyOrderItem.query.get_or_404(item_id)
    if item.order.status != 'placed':
        flash('Cannot update payload for this order.', 'danger')
        return redirect(url_for('main.supplier_receive_detail', order_id=item.order.id))
        
    action = request.form.get('action') 
    
    # Initialize payload if None
    if item.payload is None:
        item.payload = item.mass
        
    if action == 'increase':
        item.payload += 1
    elif action == 'decrease':
        if item.payload > 0:
            item.payload -= 1
            
    db.session.commit()
    return redirect(url_for('main.supplier_receive_detail', order_id=item.order.id))

@bp.route('/supplier/fusion/<int:order_id>', methods=['POST'])
@login_required
def supplier_fusion(order_id):
    order = SupplyOrder.query.get_or_404(order_id)
    if order.status != 'placed':
        flash('Order not ready for fusion.', 'danger')
        return redirect(url_for('main.supplier_receive_list'))
        
    # INVENTORY FUSION
    for item in order.items:

        qty_received = item.payload if item.payload is not None else item.mass
        
        # Update Book Stock
        item.book.stock_total += qty_received
        item.book.stock_available += qty_received
        
        # Update payload field for record keeping if it was None
        if item.payload is None:
            item.payload = qty_received
            
    order.status = 'completed'
    db.session.commit()
    
    flash('Inventory Fusion Complete! Stock updated.', 'success')
    return redirect(url_for('main.supplier_receive_list'))
