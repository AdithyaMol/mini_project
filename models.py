from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ===============================
# 📦 PRODUCT MODEL
# ===============================
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    # External product ID (ASIN etc.)
    product_id = db.Column(db.String(50), index=True)

    name = db.Column(db.String(255), nullable=False, index=True)
    brand = db.Column(db.String(100))
    category = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float)
    review_count = db.Column(db.Integer)
    image_url = db.Column(db.Text)
    product_url = db.Column(db.Text)
    availability = db.Column(db.String(50))
    vendor = db.Column(db.String(50))

    # Relationship
    wishlist_items = db.relationship(
        "Wishlist",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self):
        return f"<Product {self.name}>"



# ===============================
# 👤 USER MODEL
# ===============================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    wishlist_items = db.relationship(
        "Wishlist",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # 🔐 Password Handling
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"



# ===============================
# ❤️ WISHLIST MODEL
# ===============================
class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    # Prevent duplicate wishlist entries
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "product_id",
            name="unique_user_product"
        ),
    )

    user = db.relationship("User", back_populates="wishlist_items")
    product = db.relationship("Product", back_populates="wishlist_items")

    def __repr__(self):
        return f"<Wishlist User:{self.user_id} Product:{self.product_id}>"
