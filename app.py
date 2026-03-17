from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Wishlist
import os
from sqlalchemy import or_

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"

def create_app():

    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.config["SECRET_KEY"] = "your-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:adithya25@localhost/pricecomp_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    # ================= LOGIN =================

    @app.route("/login", methods=["GET","POST"])
    def login():

        if request.method == "POST":

            email = request.form["email"].strip()
            password = request.form["password"]

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                flash("Login successful!","success")
                return redirect(url_for("home"))
            else:
                flash("Invalid email or password","error")

        return render_template("login.html")

    # ================= REGISTER =================

    @app.route("/register", methods=["GET","POST"])
    def register():

        if request.method == "POST":

            username = request.form["username"].strip()
            email = request.form["email"].strip()
            password = request.form["password"]

            if User.query.filter_by(email=email).first():
                flash("Email already registered","error")
                return redirect(url_for("register"))

            if User.query.filter_by(username=username).first():
                flash("Username already taken","error")
                return redirect(url_for("register"))

            user = User(username=username,email=email)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash("Account created successfully!","success")

            return redirect(url_for("home"))

        return render_template("register.html")

    # ================= HOME =================

    @app.route("/")
    @login_required
    def home():

        recently_viewed=[]

        if 'recently_viewed' in session:
            product_ids=session['recently_viewed']
            recently_viewed=Product.query.filter(Product.id.in_(product_ids)).all()
            recently_viewed.sort(key=lambda p:product_ids.index(p.id))

        categories=db.session.query(Product.category).distinct().all()
        categories=[c[0] for c in categories if c[0]]

        selected_category=request.args.get("category")

        products=[]
        if selected_category:
            products=Product.query.filter_by(category=selected_category).limit(20).all()

        return render_template(
            "index.html",
            recently_viewed=recently_viewed,
            categories=categories,
            products=products,
            selected_category=selected_category
        )

    # ================= SEARCH =================

    @app.route("/search")
    @login_required
    def search():

        query=request.args.get("q","").strip()
        sort_by=request.args.get("sort","price_asc")
        rating_filter=request.args.get("rating","all")
        selected_brand=request.args.get("brand")
        selected_platform=request.args.get("platform")

        min_price=request.args.get("min_price")
        max_price=request.args.get("max_price")

        if not query:
            return render_template(
                "results.html",
                products=[],
                query=query,
                brands=[],
                platforms=[]
            )

        products_query = Product.query.filter(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.category.ilike(f"%{query}%"),
                Product.brand.ilike(f"%{query}%")
            )
        )

        if selected_brand:
            products_query=products_query.filter(Product.brand==selected_brand)

        if selected_platform:
            products_query=products_query.filter(Product.vendor==selected_platform)

        if min_price:
            products_query=products_query.filter(Product.price>=float(min_price))

        if max_price:
            products_query=products_query.filter(Product.price<=float(max_price))

        if rating_filter=="4_plus":
            products_query=products_query.filter(Product.rating>=4)

        elif rating_filter=="3_plus":
            products_query=products_query.filter(Product.rating>=3)

        if sort_by=="price_asc":
            products_query=products_query.order_by(Product.price.asc())

        elif sort_by=="price_desc":
            products_query=products_query.order_by(Product.price.desc())

        elif sort_by=="rating_desc":
            products_query=products_query.order_by(Product.rating.desc())

        products=products_query.limit(50).all()

        if not products:
            flash("No products found.","info")

        brands=sorted(list(set([p.brand for p in products if p.brand])))
        platforms=sorted(list(set([p.vendor for p in products if p.vendor])))

        return render_template(
            "results.html",
            products=products,
            query=query,
            sort_by=sort_by,
            rating_filter=rating_filter,
            brands=brands,
            platforms=platforms,
            selected_brand=selected_brand,
            selected_platform=selected_platform
        )

    # ================= COMPARE =================

    @app.route("/compare",methods=["POST"])
    @login_required
    def compare():

        product_ids=request.form.getlist("compare")

        if len(product_ids)<1 or len(product_ids)>3:
            flash("Select 1-3 products to compare.","error")
            return redirect(request.referrer or url_for("home"))

        products=Product.query.filter(Product.id.in_(product_ids)).all()

        lowest_price_product=min(products,key=lambda p:p.price)
        highest_rating_product=max(products,key=lambda p:p.rating or 0)

        return render_template(
            "compare.html",
            products=products,
            lowest_price=lowest_price_product.price,
            highest_rating=highest_rating_product.rating,
            recommended_product=lowest_price_product
        )

    # ================= PRODUCT DETAILS =================

    @app.route("/product/<int:product_id>")
    @login_required
    def product_details(product_id):

        product=Product.query.get_or_404(product_id)

        if 'recently_viewed' not in session:
            session['recently_viewed']=[]

        if product_id in session['recently_viewed']:
            session['recently_viewed'].remove(product_id)

        session['recently_viewed'].insert(0,product_id)
        session['recently_viewed']=session['recently_viewed'][:5]

        return render_template("product_details.html",product=product)

    # ================= WISHLIST =================

    @app.route("/wishlist/add/<int:product_id>")
    @login_required
    def add_to_wishlist(product_id):

        existing=Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()

        if not existing:
            item=Wishlist(user_id=current_user.id,product_id=product_id)
            db.session.add(item)
            db.session.commit()
            flash("Added to wishlist!","success")

        return redirect(request.referrer or url_for("home"))

    @app.route("/wishlist")
    @login_required
    def wishlist():

        items=Wishlist.query.filter_by(user_id=current_user.id).all()
        return render_template("wishlist.html",items=items)

    @app.route("/wishlist/remove/<int:item_id>")
    @login_required
    def remove_from_wishlist(item_id):

        item=Wishlist.query.filter_by(id=item_id,user_id=current_user.id).first_or_404()

        db.session.delete(item)
        db.session.commit()

        flash("Removed from wishlist.","success")

        return redirect(url_for("wishlist"))

    # ================= LOGOUT =================

    @app.route("/logout")
    @login_required
    def logout():

        logout_user()
        flash("Logged out successfully.","info")

        return redirect(url_for("login"))

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app=create_app()

with app.app_context():
    db.create_all()

if __name__=="__main__":
    app.run(debug=True)
