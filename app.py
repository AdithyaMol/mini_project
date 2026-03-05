from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Wishlist
import os

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# ---------------- APP FACTORY ----------------
def create_app():

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    # 🔐 CONFIGURATION (HARDCODED)
    app.config["SECRET_KEY"] = "your-secret-key"  # old hardcoded key
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:adithya25@localhost/pricecomp_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    # ==========================================
    # 🔒 LOGIN
    # ==========================================
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"].strip()
            password = request.form["password"]

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for("home"))
            else:
                flash("Invalid email or password", "error")
                return redirect(url_for("login"))

        return render_template("login.html")

    # ==========================================
    # 📝 REGISTER
    # ==========================================
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"].strip()
            email = request.form["email"].strip()
            password = request.form["password"]

            if User.query.filter_by(email=email).first():
                flash("Email already registered", "error")
                return redirect(url_for("register"))

            if User.query.filter_by(username=username).first():
                flash("Username already taken", "error")
                return redirect(url_for("register"))

            user = User(username=username, email=email)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash("Account created successfully!", "success")
            return redirect(url_for("home"))

        return render_template("register.html")

    # ==========================================
    # 🏠 HOME (Search Page)
    # ==========================================
    @app.route("/")
    @login_required
    def home():
        return render_template("index.html")

    # ==========================================
    # 🔍 SEARCH → PRODUCT LISTING PAGE
    # ==========================================
    @app.route("/search")
    @login_required
    def search():
        query = request.args.get("q", "").strip()

        if not query:
            return render_template("results.html", products=[], query=query)

        products = Product.query.filter(
            Product.name.ilike(f"%{query}%")
        ).order_by(Product.price.asc()).limit(50).all()

        if not products:
            flash("No products found.", "info")

        return render_template("results.html", products=products, query=query)

    # ==========================================
    # ⚖️ COMPARE PRODUCTS
    # ==========================================
    @app.route("/compare", methods=["POST"])
    @login_required
    def compare():
        product_ids = request.form.getlist("compare")
        print("DEBUG compare received ids:", product_ids)

        if len(product_ids) < 1 or len(product_ids) > 3:
            flash("Select 1-3 products to compare.", "error")
            return redirect(request.referrer or url_for("home"))

        products = Product.query.filter(Product.id.in_(product_ids)).all()

        if len(products) != len(product_ids):
            flash("Some products not found.", "error")
            return redirect(request.referrer or url_for("home"))

        return render_template("compare.html", products=products)

    # ==========================================
    # ❤️ ADD TO WISHLIST
    # ==========================================
    @app.route("/wishlist/add/<int:product_id>")
    @login_required
    def add_to_wishlist(product_id):
        existing = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()

        if not existing:
            item = Wishlist(user_id=current_user.id, product_id=product_id)
            db.session.add(item)
            db.session.commit()
            flash("Added to wishlist!", "success")
        else:
            flash("Product already in wishlist.", "info")

        return redirect(request.referrer or url_for("home"))

    # ==========================================
    # 📄 VIEW WISHLIST
    # ==========================================
    @app.route("/wishlist")
    @login_required
    def wishlist():
        items = Wishlist.query.filter_by(user_id=current_user.id).all()
        return render_template("wishlist.html", items=items)

    # ==========================================
    # ❌ REMOVE FROM WISHLIST
    # ==========================================
    @app.route("/wishlist/remove/<int:item_id>")
    @login_required
    def remove_from_wishlist(item_id):
        item = Wishlist.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
        db.session.delete(item)
        db.session.commit()
        flash("Removed from wishlist.", "success")
        return redirect(url_for("wishlist"))

    # ==========================================
    # 🚪 LOGOUT
    # ==========================================
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out successfully.", "info")
        return redirect(url_for("login"))

    return app

# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- RUN ----------------
app = create_app()

with app.app_context():
    db.create_all()
    
    # Auto-load data if database is empty
    from models import Product
    if Product.query.count() == 0:
        print("📂 Database is empty. Loading product data...")
        try:
            from load_data import process_file
            process_file("amazon_products.csv", "Amazon")
            process_file("flipkart_products.csv", "Flipkart")
            if os.path.exists("products.csv"):
                process_file("products.csv", "OtherVendor")
            print("✅ Data loaded successfully!")
        except Exception as e:
            print(f"⚠️ Error loading data: {e}")

if __name__ == "__main__":
    app.run(debug=True)
