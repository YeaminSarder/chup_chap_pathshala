from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, StringField, SelectField,FloatField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Length, URL, Optional

from app.models import Category

class RestockForm(FlaskForm):
    quantity = IntegerField(
        "Quantity to Add",
        validators=[DataRequired(), NumberRange(min=1, message="Must be at least 1")]
    )
    submit = SubmitField("Restock")

class EditForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.name, c.name) for c in Category.query.order_by(Category.name).all()]

    title = StringField(
        "Title",
        validators=[DataRequired(), Length(min=1, max=140)]        
    )
    author = StringField(
        "Author",
        validators=[DataRequired(), Length(min=1, max=140)]
    )
    price = FloatField(
        "Price",
        validators=[DataRequired()]
    )
    item_type = SelectField("Availability (Sell/Borrow)",choices=[
        ("circulation", "Circulation (Borrow)"),
        ("sale", "Sale"),
        ("hybrid", "Hybrid (Sell/Borrow)")
    ])
    category = SelectField("Category", choices=[]) 

    location = StringField(
        "Location",
        validators=[DataRequired(), Length(min=1, max=100)]
    )
    image_url = StringField(
        "Image URL",
        validators=[Optional(), URL(), Length(min=0, max=500)]
    )
    stock_available = FloatField(
        "Stock Available",
        validators=[InputRequired()]
    )
    stock_borrowed = IntegerField(
        "Stock Borrowed",
        validators=[InputRequired()]
    )
    stock_sold = IntegerField(
        "Stock Sold",
        validators=[InputRequired()]
    )
    submit = SubmitField("Confirm")
