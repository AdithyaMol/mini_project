from flask import Flask, render_template, request, redirect, url_for, flash, session
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

    # 🔐 CONFIGURATION
    app.config["SECRET_KEY"] = "your-secret-key"
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
    # 🏠 HOME (Search Page + Categories)
    # ==========================================
    @app.route("/")
    @login_required
    def home():

        # Recently viewed products (existing feature)
        recently_viewed = []
        if 'recently_viewed' in session:
            product_ids = session['recently_viewed']
            recently_viewed = Product.query.filter(Product.id.in_(product_ids)).all()
            recently_viewed.sort(key=lambda p: product_ids.index(p.id))

        # ⭐ NEW: Load categories for homepage
        categories = db.session.query(Product.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]

        # Optional category filter
        selected_category = request.args.get("category")

        products = []
        if selected_category:
            products = Product.query.filter_by(category=selected_category).limit(20).all()

        return render_template(
            "index.html",
            recently_viewed=recently_viewed,
            categories=categories,
            products=products,
            selected_category=selected_category
        )

    # ==========================================
    # 🔍 SEARCH
    # ==========================================
    @app.route("/search")
    @login_required
    def search():
        query = request.args.get("q", "").strip()
        sort_by = request.args.get("sort", "price_asc")
        price_filter = request.args.get("price", "all")
        rating_filter = request.args.get("rating", "all")

        if not query:
            return render_template("results.html", products=[], query=query, sort_by=sort_by, price_filter=price_filter, rating_filter=rating_filter)

        products_query = Product.query.filter(Product.name.ilike(f"%{query}%"))

        if price_filter == "under_50000":
            products_query = products_query.filter(Product.price < 50000)
        elif price_filter == "50000_100000":
            products_query = products_query.filter(Product.price.between(50000, 100000))
        elif price_filter == "above_100000":
            products_query = products_query.filter(Product.price >= 100000)

        if rating_filter == "4_plus":
            products_query = products_query.filter(Product.rating >= 4.0)
        elif rating_filter == "3_plus":
            products_query = products_query.filter(Product.rating >= 3.0)

        if sort_by == "price_asc":
            products_query = products_query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            products_query = products_query.order_by(Product.price.desc())
        elif sort_by == "rating_desc":
            products_query = products_query.order_by(Product.rating.desc())

        products = products_query.limit(50).all()

        if not products:
            flash("No products found.", "info")

        return render_template(
            "results.html",
            products=products,
            query=query,
            sort_by=sort_by,
            price_filter=price_filter,
            rating_filter=rating_filter
        )

    # ==========================================
    # ⚖️ COMPARE PRODUCTS
    # ==========================================
    @app.route("/compare", methods=["POST"])
    @login_required
    def compare():
        product_ids = request.form.getlist("compare")

        if len(product_ids) < 1 or len(product_ids) > 3:
            flash("Select 1-3 products to compare.", "error")
            return redirect(request.referrer or url_for("home"))

        products = Product.query.filter(Product.id.in_(product_ids)).all()

        lowest_price_product = min(products, key=lambda p: p.price)
        lowest_price = lowest_price_product.price

        highest_rating_product = max(products, key=lambda p: p.rating or 0)
        highest_rating = highest_rating_product.rating

        recommended_product = lowest_price_product

        price_differences = {}
        for product in products:
            price_differences[product.id] = max(product.price - lowest_price, 0)

        scores = {}
        for product in products:
            score = (product.rating * 2) - (product.price / 10000)
            scores[product.id] = round(score, 2)

        highest_score = max(scores.values()) if scores else 0

        return render_template(
            "compare.html",
            products=products,
            lowest_price=lowest_price,
            highest_rating=highest_rating,
            recommended_product=recommended_product,
            price_differences=price_differences,
            scores=scores,
            highest_score=highest_score
        )

    # ==========================================
    # 📄 PRODUCT DETAILS
    # ==========================================
    @app.route("/product/<int:product_id>")
    @login_required
    def product_details(product_id):
        product = Product.query.get_or_404(product_id)

        if 'recently_viewed' not in session:
            session['recently_viewed'] = []

        if product_id in session['recently_viewed']:
            session['recently_viewed'].remove(product_id)

        session['recently_viewed'].insert(0, product_id)
        session['recently_viewed'] = session['recently_viewed'][:5]

        return render_template("product_details.html", product=product)

    # ==========================================
    # ❤️ WISHLIST
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

    @app.route("/wishlist")
    @login_required
    def wishlist():
        items = Wishlist.query.filter_by(user_id=current_user.id).all()
        return render_template("wishlist.html", items=items)

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
