import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, json
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

from helpers import (
    apology,
    login_required,
    usd,
    isint,
    isfloat,
    allowed_file,
    update_store_balance,
    log_into_trans_seller,
)

UPLOAD_FOLDER = "./static/img"


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

# Declare global variables
DELIVERY_CHARGE = 0.2
CATEGORY = {"Clothes", "Foods&Beverages", "Accessories", "Decorations"}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    # Redirect to browser page
    return redirect("/browser")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    session["portal"] = "buyer"

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE status='ENABLED' AND username=?",
            request.form.get("username"),
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
        session["username"] = rows[0]["username"]
        session["wallet_bal"] = rows[0]["deposit"]
        session["store_bal"] = rows[0]["store_balance"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)
        else:
            password = request.form.get("password")

        # Ensure confirmation was submitted
        if not request.form.get("confirmation"):
            return apology("must provide confirmation", 400)
        else:
            confirmation = request.form.get("confirmation")

        # Compare password and confirmation
        if not password == confirmation:
            return apology("confirmation does not match password")

        # Query database for existing username
        rows = db.execute(
            "SELECT * FROM users WHERE status='ENABLED' AND username=?",
            request.form.get("username"),
        )

        # Ensure username does not already exist
        if len(rows) > 0:
            return apology("username already exist", 400)
        else:
            # Insert user name
            db.execute(
                "INSERT INTO users (username, hash, status) VALUES (?, ?, 'ENABLED')",
                request.form.get("username"),
                generate_password_hash(
                    request.form.get("password"), method="pbkdf2:sha256", salt_length=8
                ),
            )

            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/browser")
@login_required
def browser():
    """Show available products"""
    # Change portal to buyer
    session["portal"] = "buyer"

    # Call data of all active products and display
    products = db.execute("SELECT * FROM products WHERE status='ENABLED'")
    return render_template("browser.html", products=products, CATEGORY=CATEGORY)


@app.route("/cart")
@login_required
def cart():
    """Show user's shopping cart"""
    # Identify user from session and retrieve user data
    user_id = session["user_id"]
    users = db.execute("SELECT * FROM users WHERE user_id=?", user_id)

    # Retrieve cart data of the user
    cart = db.execute(
        "SELECT cart.quantity, cart.product_id, products.product_name, products.price \
            FROM cart, products \
            WHERE cart.buyer=? \
                AND products.product_id=cart.product_id",
        user_id,
    )
    
    # Calculate the cart total value
    total = 0
    for row in cart:
        total += row["quantity"] * row["price"]

    # Render "Cart" page
    return render_template("cart.html", cart=cart, total=total, users=users)


@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    """To add selected item to user's cart"""
    # Identify user and selected item
    user_id = session["user_id"]
    product_id = int(request.form.get("product_id"))

    # Retrieve corresponding cart data from database
    rows = db.execute("SELECT * FROM cart WHERE buyer=?", user_id)
    
    # Check if the item already exists in cart. If so, update the qty and return to "Browser" page
    for row in rows:
        if product_id == row["product_id"]:
            qty = row["quantity"] + 1
            db.execute(
                "UPDATE cart SET quantity=? WHERE product_id=? AND buyer=?",
                qty,
                product_id,
                user_id,
            )
            return redirect("/browser")

    # If item does not already exist in cart, add new item in cart and return to "Browser" page
    db.execute("INSERT INTO cart VALUES (?, ?, ?)", user_id, product_id, 1)
    return redirect("/browser")


@app.route("/revise_cart_qty", methods=["POST"])
@login_required
def revise_cart_qty():
    """To change item qty in cart"""
    # Identify user
    user_id = session["user_id"]
    
    # Retrieve data from form
    product_id = int(request.form.get("product_id"))
    qty_dropdown = request.form.get("qty_dropdown")
    qty_btn = request.form.get("qty_btn")
    
    # Retrieve item data from database
    row = db.execute(
        "SELECT * FROM cart WHERE product_id=? AND buyer=?", product_id, user_id
    )

    # If change is made by +- button, validate input.
    if not qty_btn == None:
        if isint(qty_btn):
            # Accept if input is valid.
            new_qty = row[0]["quantity"] + int(qty_btn)
        else:
            # Redirect to error page if input is invalid.
            return apology("invalid input", 401)

    # If change is made by dropdown list, validate input.
    elif not qty_dropdown == None:
        if isint(qty_dropdown):
            # Accept if input is valid.
            new_qty = int(qty_dropdown)
        else:
            # Redirect to error page if input is invalid.
            return apology("invalid input", 402)
    else:
        return apology("invalid input", 403)

    # Update database with new qty
    db.execute(
        "UPDATE cart SET quantity=? WHERE product_id=? AND buyer=?",
        new_qty,
        product_id,
        user_id,
    )

    # Re-render "Cart" page
    return redirect("/cart")


@app.route("/remove_item", methods=["POST"])
@login_required
def remove_item():
    """To remove item in cart"""
    # Identify user
    user_id = session["user_id"]
    
    # Identify item from form and delete in database correspondingly
    product_id = int(request.form.get("product_id"))
    db.execute("DELETE FROM cart WHERE buyer=? AND product_id=?", user_id, product_id)

    # Re-render "Cart" page
    return redirect("/cart")


@app.route("/check_out", methods=["POST"])
@login_required
def check_out():
    """To check out cart into order"""
    # Identify user
    user_id = session["user_id"]
    
    # Retrieve cart item data from database
    cart_details = db.execute(
        "SELECT cart.quantity, cart.product_id, products.product_name, \
            products.price, products.stock, products.seller, products.sold_qty \
                FROM cart, products \
                WHERE cart.buyer=? AND products.product_id=cart.product_id",
        user_id,
    )

    # check stock
    for item in cart_details:
        # If stock is less than qty, return error message
        if item["quantity"] > item["stock"]:
            return apology("Out of stock!")

    # Check user balance
    deposit = db.execute("SELECT deposit FROM users WHERE user_id=?", user_id)
    balance = deposit[0]["deposit"]

    # Calculate total cost of the whole cart
    cart_total = 0

    for item in cart_details:
        cart_total += item["quantity"] * item["price"]

    # Compare total cost vs balance
    if cart_total > balance:
        # If total cost > balance, return error message
        return apology("Not enough balance!")

    # If no error exist, execute check out:
    # Deduct cost from user balance
    balance = balance - cart_total
    
    # Update balance in users table
    db.execute("UPDATE users SET deposit=? WHERE user_id=?", balance, user_id)
    
    # Update balance in session
    session["wallet_bal"] = balance

    # Update stock and sold qty in products table for each item in cart
    for item in cart_details:
        stock = item["stock"] - item["quantity"]
        sold_qty = item["sold_qty"] + item["quantity"]
        db.execute(
            "UPDATE products SET stock=?, sold_qty=? WHERE product_id=?",
            stock,
            sold_qty,
            item["product_id"],
        )

    # Create order in orders table
    discount = 0
    address = db.execute("SELECT address FROM users WHERE user_id=?", user_id)
    db.execute(
        "INSERT INTO orders (buyer, datetime, status, discount, address) \
            VALUES (?, ?, ?, ?, ?)",
        user_id,
        datetime.now(),
        "PENDING",
        discount,
        address[0]["address"],
    )
    order_id = db.execute("SELECT MAX(order_id) FROM orders WHERE buyer=?", user_id)
    current_oid = order_id[0]["MAX(order_id)"]

    # Create transaction in transactions table
    remark = "Order#" + str(current_oid)
    db.execute(
        "INSERT INTO transactions (datetime, type, amount, user_id, remark) \
            VALUES (?, 'PURCHASE', ?, ?, ?)",
        datetime.now(),
        -cart_total,
        user_id,
        remark,
    )

    # Create details in order_details table
    cart = db.execute("SELECT * FROM cart WHERE buyer=?", user_id)
    for item in cart:
        sold_price = db.execute(
            "SELECT price FROM products WHERE product_id=?", item["product_id"]
        )
        db.execute(
            "INSERT INTO order_details (order_id, product_id, quantity, sold_price, status) \
                VALUES (?, ?, ?, ?, ?)",
            current_oid,
            item["product_id"],
            item["quantity"],
            sold_price[0]["price"],
            "PENDING",
        )

    # Check order amount per seller
    # Create a set of sellers involved in cart
    seller_set = set()
    
    # Load sellers into set
    for item in cart_details:
        seller_set.add(item["seller"])
        
    # Create a dictionary of seller amount pair
    amount_per_seller = {}

    # Declare amount for all sellers
    for seller in seller_set:
        amount_per_seller[seller] = 0

    # Sum up ammount for each seller
    for item in cart_details:
        seller = item["seller"]
        amount_per_seller[seller] += item["price"] * item["quantity"]

    # Update transactions_seller table
    for seller in seller_set:
        amount = amount_per_seller[seller]
        db.execute(
            "INSERT INTO transactions_seller (datetime, type, amount, user_id, remark) \
                VALUES (?, 'SALE', ?, ?, ?)",
            datetime.now(),
            amount,
            seller,
            remark,
        )

    # Update store_balance per seller in users table
    for seller in seller_set:
        
        # Retrieve store balance from database
        store_balance = db.execute(
            "SELECT store_balance FROM users WHERE user_id=?", seller
        )
        
        # Add sale revenue to store balance
        new_store_balance = (
            store_balance[0]["store_balance"] + amount_per_seller[seller]
        )
        
        # Update new store balance to database
        db.execute(
            "UPDATE users SET store_balance=? WHERE user_id=?",
            new_store_balance,
            seller,
        )

    # Clear current cart
    db.execute("DELETE FROM cart WHERE buyer=?", user_id)

    # Redirect to "Wallet" page after successful check out
    return redirect("/wallet")


@app.route("/wallet")
@login_required
def wallet():
    """Display wallet balance and transaction log or order record"""
    # Identify user
    user_id = session["user_id"]
    
    # Retrieve corresponding order data from database
    orders = db.execute("SELECT * FROM orders WHERE buyer=?", user_id)

    # Retrieve order details data from database
    order_details = db.execute(
        "SELECT order_details.*, products.product_name \
            FROM order_details, products \
            WHERE order_details.product_id=products.product_id"
    )
    
    # Retrieve transaction data from database
    transactions = db.execute("SELECT * FROM transactions WHERE user_id=?", user_id)
    
    # # Retrieve balance value from database
    balance = db.execute("SELECT deposit FROM users WHERE user_id=?", user_id)

    # Render "Wallet" page
    return render_template(
        "wallet.html",
        transactions=transactions,
        orders=orders,
        order_details=order_details,
        balance=float(balance[0]["deposit"]),
    )


@app.route("/deposit_wallet", methods=["POST"])
@login_required
def deposit():
    """To deposit to wallet balance"""
    # Validate input. Return to "Wallet" page if input is invalid.
    if not isfloat(request.form.get("amount")):
        return redirect("/wallet")
    else:
        # Store input and identify user if input is valid
        user_id = session["user_id"]
        deposit = float(request.form.get("amount"))

    # Return if input is negative.
    if deposit < 0:
        return redirect("/wallet")
    else:
        # If input is not negative, proceed deposit action:
        # Retrieve current balance value from dataase
        row = db.execute("SELECT deposit FROM users WHERE user_id=?", user_id)
        
        # Calculate new balance value
        balance = row[0]["deposit"] + deposit
        
        # Update new balance to database
        db.execute("UPDATE users SET deposit=? WHERE user_id=?", balance, user_id)
        
        # Update new balance in session
        session["wallet_bal"] = balance

        # Log transaction to database
        db.execute(
            "INSERT INTO transactions (datetime, type, amount, user_id) \
                VALUES (?, 'DEPOSIT', ?, ?)",
            datetime.now(),
            deposit,
            user_id,
        )

        # Return to "Wallet" page after deposit
        return redirect("/wallet")


@app.route("/withdrawal_wallet", methods=["POST"])
@login_required
def withdrawal():
    """To withdraw from wallet balance"""
    # Validate input. Return to "Wallet" page if input is invalid.
    if not isfloat(request.form.get("amount")):
        return redirect("/wallet")
    else:
        # Store input and identify user if input is valid
        user_id = session["user_id"]
        withdrawal = float(request.form.get("amount"))

    # Return if input is negative.
    if withdrawal < 0:
        return redirect("/wallet")
    else:
        # If input is not negative, proceed withdrawal action:
        # Retrieve current balance value from dataase
        row = db.execute("SELECT deposit FROM users WHERE user_id=?", user_id)
        
        # Calculate new balance value
        balance = row[0]["deposit"] - withdrawal
        
        # Update new balance to database
        db.execute("UPDATE users SET deposit=? WHERE user_id=?", balance, user_id)
        
        # Update new balance in session
        session["wallet_bal"] = balance

        # Log transaction to database
        db.execute(
            "INSERT INTO transactions (datetime, type, amount, user_id) \
                VALUES (?, 'WITHDRAWAL', ?, ?)",
            datetime.now(),
            -withdrawal,
            user_id,
        )

        # Return to "Wallet" page after withdrawal
        return redirect("/wallet")


@app.route("/product")
@login_required
def product():
    """Display the inventory of products the user put to sell or transaction log"""
    # Identify user
    user_id = session["user_id"]
    
    # Retrieve corresponding product data from database
    products = db.execute(
        "SELECT * FROM products WHERE seller=? AND status='ENABLED'", user_id
    )
    
    # Retrieve corresponding transaction data from database
    transactions_seller = db.execute(
        "SELECT * FROM transactions_seller WHERE user_id=?", user_id
    )
    
    # Retrieve store balance value from database
    balance = db.execute(
        "SELECT deposit, store_balance FROM users WHERE user_id=?", user_id
    )

    # Render "Product" page
    return render_template(
        "product.html",
        products=products,
        transactions_seller=transactions_seller,
        balance=balance,
        CATEGORY=CATEGORY,
    )


def upload_image(pid, file):
    """To store file at dedicated location and update database """
    # Store image in server
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    # Update products table
    db.execute("UPDATE products SET image=? WHERE product_id=?", filename, pid)

    return True


@app.route("/create_product", methods=["POST"])
@login_required
def create_product():
    """To create a new product"""
    # Identify user
    user_id = session["user_id"]
    
    # Retrieve data from form
    product = request.form.get("product_name")
    price = float(request.form.get("price"))
    category = request.form.get("category")

    # Check if product name was submitted. Flash error message if not.
    if product == "":
        flash("Product name required!")
        return redirect("/product")

    # Check if product category is submitted. Flash error message if not.
    if category not in CATEGORY:
        flash("Category name required!")
        return redirect("/product")
    

    # Ensure product does not already exist
    product_list = db.execute(
        "SELECT product_name FROM products WHERE status='ENABLED'"
    )
    for row in product_list:
        if product == row["product_name"]:
            flash("Product already exist!")
            return redirect("/product")

    # Ensure price is submitted and is numeric
    if not isfloat(price):
        flash("Price required!")
        return redirect("/product")

    # Ensure price input is not negative
    if not price >= 0:
        flash("Price must not be negative!")
        return redirect("/product")

    # Retrieve image file from form
    f = request.files["product_image"]

    # Ensure image file is submitted
    if f.filename == "":
        flash("No seleted file")
        return redirect("/product")
    
    # Create product in database
    db.execute(
        "INSERT INTO products \
            (product_name, seller, price, stock, sold_qty, status, category) \
            VALUES (?, ?, ?, ?, ?, 'ENABLED', ?)",
        product,
        user_id,
        price,
        0,
        0,
        category,
    )

    # Retrieve newly created product id (pid)
    new_product = db.execute("SELECT MAX(product_id) FROM products")
    pid = new_product[0]["MAX(product_id)"]
    
    # Upload image file and update database
    upload_image(pid, f)

    # Return to "Product" page after product is created.
    return redirect("/product")


@app.route("/revise_product", methods=["POST"])
@login_required
def revise_product():
    """To revise details of existing product"""
    # If all inputs are null, redirect to "Apology" page with error message.
    if (
        not request.form.get("category")
        and not isfloat(request.form.get("add_stock"))
        and not isfloat(request.form.get("new_price"))
        and request.files["product_image"].filename == ""
    ):
        return apology("No input")
    else:
        # Otherwise, identify user and product to be revised.
        user_id = session["user_id"]
        pid = int(request.form.get("product_id"))
        
        # Retrieve corresponding product data from database
        rows = db.execute(
            "SELECT * FROM products WHERE product_id=? AND seller=?", pid, user_id
        )

    # If category is submitted, update category
    if request.form.get("category"):
        category = request.form.get("category")
        db.execute(
            "UPDATE products SET category=? WHERE product_id=? AND seller=?",
            category,
            pid,
            user_id,
        )
    # If new stock is submitted, update stock
    if isfloat(request.form.get("add_stock")):
        add_stock = float(request.form.get("add_stock"))

        if int(add_stock) == add_stock:
            db.execute(
                "UPDATE products SET stock=? WHERE product_id=? AND seller=?",
                rows[0]["stock"] + add_stock,
                pid,
                user_id,
            )
        else:
            return apology("Stock must be integer")

    # If new price is submitted, update stock
    if isfloat(request.form.get("new_price")):
        new_price = float(request.form.get("new_price"))

        if new_price >= 0:
            db.execute(
                "UPDATE products SET price=? WHERE product_id=? AND seller=?",
                new_price,
                pid,
                user_id,
            )
        else:
            return apology("Price must not be negative")

    # Retrieve file from form
    f = request.files["product_image"]

    # If image is submitted, update server
    if f.filename != "":
        upload_image(pid, f)

    # Redirect to "Product" page after updating
    return redirect("/product")


@app.route("/delete_product", methods=["POST"])
@login_required
def delete_product():
    """To deactivate existing product"""
    # Change item status in database
    db.execute(
        "UPDATE products SET status='DISABLED' WHERE product_id=?",
        int(request.form.get("product_id")),
    )

    # Redirect to "Product" page after deactivation
    return redirect("/product")


@app.route("/deposit_to_store", methods=["POST"])
@login_required
def deposit_to_store():
    """To deposit from wallet to store"""
    # Validate input type, only proceed if there is a valid input.
    if not isfloat(request.form.get("amount")):
        return redirect("/product")
    
    # Accept input and identify user if input type is valid.
    else:
        user_id = session["user_id"]
        deposit = float(request.form.get("amount"))

    # Validate input, redirect to "Apology" page if input is negative.
    if deposit < 0:
        return apology("Amount must not be negative!", 403)
    
    # Otherwisw, proceed deposit action.
    else:
        # Retrieve wallet balance and store balance value from database
        # and calculate new balance value after the deposit.
        row = db.execute(
            "SELECT deposit, store_balance FROM users WHERE user_id=?", user_id
        )
        store_balance = row[0]["store_balance"] + deposit
        cash_balance = row[0]["deposit"] - deposit

        # Reject transaction if balance is not enough.
        if cash_balance < 0:
            apology("Cash balance not enough!", 403)
            
        # Otherwise, update balance values in database and session
        else:
            db.execute(
                "UPDATE users SET deposit=?, store_balance=? WHERE user_id=?",
                cash_balance,
                store_balance,
                user_id,
            )
            session["wallet_bal"] = cash_balance
            session["store_bal"] = store_balance

            # Log transaction in both wallet and store
            db.execute(
                "INSERT INTO transactions (datetime, type, amount, user_id) \
                    VALUES (?, 'DEPOSIT TO STORE', ?, ?)",
                datetime.now(),
                -deposit,
                user_id,
            )
            db.execute(
                "INSERT INTO transactions_seller (datetime, type, amount, user_id) \
                    VALUES (?, 'DEPOSIT TO STORE', ?, ?)",
                datetime.now(),
                deposit,
                user_id,
            )

        # Redirect to "Product" page after deposit.
        return redirect("/product")


@app.route("/withdrawal_from_store", methods=["POST"])
@login_required
def withdrawal_from_store():
    """To withdraw from store to wallet"""
    # Validate input type, only proceed if there is a valid input.
    if not isfloat(request.form.get("amount")):
        return redirect("/wallet")
    
    # Accept input and identify user if input type is valid.
    else:
        user_id = session["user_id"]
        withdrawal = float(request.form.get("amount"))

    # Validate input, redirect to "Apology" page if input is negative.
    if withdrawal < 0:
        return apology("Amount must not be negative!", 403)
    
    # Otherwisw, proceed withdrawal action.
    else:
        # Retrieve wallet balance and store balance value from database
        # and calculate new balance value after the withdrawal.
        row = db.execute(
            "SELECT deposit, store_balance FROM users WHERE user_id=?", user_id
        )
        store_balance = row[0]["store_balance"] - withdrawal
        cash_balance = row[0]["deposit"] + withdrawal

        # Reject transaction if balance is not enough.
        if store_balance < 0:
            apology("Store balance not enough!", 403)
            
        # Otherwise, update balance values in database and session
        else:
            db.execute(
                "UPDATE users SET deposit=?, store_balance=? WHERE user_id=?",
                cash_balance,
                store_balance,
                user_id,
            )
            session["wallet_bal"] = cash_balance
            session["store_bal"] = store_balance

            # Log transaction in both wallet and store
            db.execute(
                "INSERT INTO transactions (datetime, type, amount, user_id) \
                    VALUES (?, 'WITHDRAWAL FROM STORE', ?, ?)",
                datetime.now(),
                withdrawal,
                user_id,
            )
            db.execute(
                "INSERT INTO transactions_seller (datetime, type, amount, user_id) \
                    VALUES (?, 'WITHDRAWAL FROM STORE', ?, ?)",
                datetime.now(),
                -withdrawal,
                user_id,
            )

        # Redirect to "Product" page after withdrawal.
        return redirect("/product")


@app.route("/order")
@login_required
def order():
    """Display your order records and arrange delivery as well as"""
    # Identify user
    user_id = session["user_id"]

    # Retrieve data of items which are pending for delivery from database
    order_details = db.execute(
        "SELECT order_details.*, products.product_id, products.product_name, orders.address \
            FROM orders, order_details, products \
            WHERE orders.order_id=order_details.order_id \
                AND order_details.product_id = products.product_id \
                AND seller=? \
                AND NOT order_details.status='DELIVERED'",
        user_id,
    )

    # Retrieve records of delivery order from database
    delivery_orders = db.execute(
        "SELECT * FROM delivery_orders WHERE seller=?", user_id
    )
    
    # Retrieve records of delivery details from database
    delivery_details = db.execute(
        "SELECT delivery_details.*, orders.address, order_details.quantity, products.product_name \
            FROM delivery_details, orders, order_details, products \
            WHERE products.product_id=delivery_details.product_id \
                AND orders.order_id=delivery_details.order_id \
                AND order_details.order_id=delivery_details.order_id \
                AND order_details.product_id=delivery_details.product_id"
    )

    # Render "Order" page
    return render_template(
        "order.html",
        order_details=order_details,
        delivery_orders=delivery_orders,
        delivery_details=delivery_details,
    )


@app.route("/delivered", methods=["POST"])
@login_required
def delivered():
    """To change order status to delivered"""
    # Identify user
    user_id = session["user_id"]

    # Retrieve selected items from form
    selected_items = request.form.getlist("items_to_deliver")

    # Count the total qty of items to be delivered
    delivery_qty = 0
    for item_id in selected_items:
        # Obtain item details from database
        item_details = db.execute(
            "SELECT order_id, product_id, quantity FROM order_details WHERE id=?",
            item_id,
        )

        # Calculate total number of items to be delivered
        delivery_qty += item_details[0]["quantity"]

    # Calculate total cost of the delivery order:
    delivery_cost = DELIVERY_CHARGE * delivery_qty

    # Check if store balance is enough for delivery cost
    if delivery_cost > session["store_bal"]:
        
        # If balance is not enough, redirect to "Apology" page
        return apology("Not enough balance!")
        
    # Otherwise, create new delivery order in delivery_order table
    else:
        db.execute(
            "INSERT INTO delivery_orders (datetime, seller) VALUES (?, ?)",
            datetime.now(),
            user_id,
        )
        
        # Retrieve newly created delivery order id from database
        delivery_order = db.execute(
            "SELECT MAX(delivery_order_id) FROM delivery_orders"
        )
        delivery_order_id = delivery_order[0]["MAX(delivery_order_id)"]

        for item_id in selected_items:
            # For each selected item, identify the item to be delivered in order details table.
            # And retrieve corresponding order_id and product_id
            item_details = db.execute(
                "SELECT order_id, product_id, quantity FROM order_details WHERE id=?",
                item_id,
            )
            order_id = item_details[0]["order_id"]
            product_id = item_details[0]["product_id"]

            # Create a new delivered item in delivery_details table
            db.execute(
                "INSERT INTO delivery_details VALUES (?, ?, ?)",
                delivery_order_id,
                order_id,
                product_id,
            )

            # Update status of the particular item in order_details table
            db.execute(
                "UPDATE order_details SET status='DELIVERED' WHERE order_id=? AND product_id=?",
                order_id,
                product_id,
            )

        # Log the delivery cost transaction in transactions_seller table
        remark = "Delivery Order#" + str(delivery_order_id)
        log_into_trans_seller(
            datetime.now(), "DELIVERY COST", -delivery_cost, user_id, remark
        )

        # Deduct delivery cost from store_balance of the seller in users table
        update_store_balance(-delivery_cost, user_id)

        # Check if all items in the order were delivered
        order_details = db.execute(
            "SELECT order_id, product_id, status FROM order_details WHERE order_id=?",
            order_id,
        )
        for item in order_details:
            if not item["status"] == "DELIVERED":
                # If any item is not delivered, end and redirect to the "Order" page.
                return redirect("/order")

        # If all items were delivered, update status in orders table. 
        # Then redirect to the "Order" page.
        db.execute(
            "UPDATE orders SET status='DELIVERED' WHERE order_id=?", order_id
        )
        
    return redirect("/order")


@app.route("/dashboard")
@login_required
def dashboard():
    """Display charts of sales performance in the past 6 months"""
    # Set portal to "Seller"
    session["portal"] = "seller"
    
    # Identify user
    user_id = session["user_id"]

    # Retrieve user's products' data from database
    product_list_db = db.execute(
        "SELECT product_name FROM products WHERE seller=? AND status='ENABLED'", user_id
    )
    
    # From retrieved data, generate a list of product_name
    product_list = []
    for row in product_list_db:
        product_list.append(row["product_name"])

    # Retrieve products' sale performance data from database
    chart_data = db.execute(
        "SELECT products.product_name AS product, \
            SUM(order_details.quantity) AS qty, \
            SUM(order_details.quantity*order_details.sold_price) as revenue, \
            STRFTIME('%Y-%m',orders.datetime) AS month \
            FROM order_details, orders, products \
            WHERE orders.order_id=order_details.order_id \
                AND products.product_id=order_details.product_id \
                AND products.seller=? \
            GROUP BY product, month",
        user_id,
    )

    # Render "Dashboard" page
    return render_template(
        "dashboard.html", chart_data=chart_data, product_list=product_list
    )


@app.route("/update")
@login_required
def update():
    """Show Form for updating user information"""
    return render_template("update.html")


@app.route("/update_password", methods=["POST"])
@login_required
def update_password():
    """To validate and update new password"""
    user_id = session["user_id"]

    # Ensure password was submitted
    if not request.form.get("inputPassword"):
        return apology("must provide password", 400)
    else:
        password = request.form.get("inputPassword")

    # Ensure confirmation was submitted
    if not request.form.get("inputPassword2"):
        return apology("must provide confirmation", 400)
    else:
        confirmation = request.form.get("inputPassword2")

    # Compare password and confirmation
    if not password == confirmation:
        return apology("confirmation does not match password")

    # Generate hash
    hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)

    # Update users table
    db.execute("UPDATE users SET hash=? WHERE user_id=?", hash, user_id)

    return redirect("/")


@app.route("/update_info", methods=["POST"])
@login_required
def update_info():
    """To validate new user info entry and update"""
    # Identify user
    user_id = session["user_id"]
    
    # Retrieve data from form
    address = request.form.get("inputAddress")
    code = request.form.get("inputCode")
    number = request.form.get("inputContact")

    # Update address if input is not empty
    if address != "":
        db.execute("UPDATE users SET address=? WHERE user_id=?", address, user_id)
        
    # Remain in "Update" page if all input are empty
    elif code == "" and number == "":
        return redirect("update")
        
    # Update contact if both code and number are valid
    if isint(code) and isint(number):
        contact = code + "-" + number
        db.execute("UPDATE users SET contact=? WHERE user_id=?", contact, user_id)
        
        # Return to "Cart" page after update
        return redirect("cart")
        
    # If both code and number are empty, pass and return to "Cart" page
    elif code == "" and number == "":
        return redirect("cart")
    
    # If either code or number input is invalid, redirect to "Apology" page
    else:
        return apology("Contact input incomplete!")


@app.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    """To remove existing user account"""
    # Identify user
    user_id = session["user_id"]

    # Disable user  in user database
    db.execute("UPDATE users SET status='DISABLED' WHERE user_id=?", user_id)
    
    # Disable corresponding products in products database
    db.execute("UPDATE products SET status='DISABLED' WHERE seller=?", user_id)

    # Logout user
    logout()

    # Redirect to login page after logout
    return redirect("/")


@app.route("/check")
def check():
    """Show all database table (for admin use)"""

    # Retrieve data from all table in database
    users = db.execute("SELECT * FROM users")
    products = db.execute("SELECT * FROM products")
    cart = db.execute("SELECT * FROM cart")
    orders = db.execute("SELECT * FROM orders")
    order_details = db.execute("SELECT * FROM order_details")
    transactions = db.execute("SELECT * FROM transactions")
    transactions_seller = db.execute("SELECT * FROM transactions_seller")
    delivery_orders = db.execute("SELECT * FROM delivery_orders")
    delivery_details = db.execute("SELECT * FROM delivery_details")

    return render_template(
        "check.html",
        users=users,
        products=products,
        cart=cart,
        orders=orders,
        order_details=order_details,
        transactions=transactions,
        transactions_seller=transactions_seller,
        delivery_orders=delivery_orders,
        delivery_details=delivery_details,
    )


@app.route("/empty_data", methods=["POST"])
def empty_data():
    """To empty database data (for admin use)"""

    # Logout to clear any session data
    logout()

    # Empty database
    db.execute("DELETE FROM cart")
    db.execute("DELETE FROM order_details")
    db.execute("DELETE FROM transactions")
    db.execute("DELETE FROM transactions_seller")
    db.execute("DELETE FROM delivery_details")
    db.execute("DELETE FROM delivery_orders")
    db.execute("DELETE FROM orders")
    db.execute("DELETE FROM products")
    db.execute("DELETE FROM users")

    # Redirect to "Check" page after emptying database
    return redirect("/check")
