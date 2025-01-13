#=========Imports=========
from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Table, Column, String, Integer, select, DateTime, Float
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from typing import List, Optional
import datetime
import os

# ======API JSON BODY REFERENCE======
# 1. USERS
#   a) Create a Single User
#      Endpoint: POST /user
#      JSON Body (required keys):
#      {
#        "name": "string",
#        "address": "string",
#        "email": "string"
#      }
#   b) Create Multiple Users
#      Endpoint: POST /users
#      JSON Body (array of user objects):
#      [
#        {
#          "name": "string",
#          "address": "string",
#          "email": "string"
#        },
#        ...
#      ]
#   c) Update a User
#      Endpoint: PUT /users/<int:id>
#      JSON Body (partial or full):
#      {
#        "name": "string (optional)",
#        "address": "string (optional)",
#        "email": "string (optional)"
#      }
# ----------------------------------------------
# 2. PRODUCTS
#   a) Create a Product
#      Endpoint: POST /products
#      JSON Body (required keys):
#      {
#        "product_name": "string",
#        "price": float
#      }
#   b) Update a Product
#      Endpoint: PUT /products/<int:id>
#      JSON Body (partial or full):
#      {
#        "product_name": "string (optional)",
#        "price": float (optional)
#      }
# -------------------------------------------------------------------------------------
# 3. ORDERS
#   a) Create an Order
#      Endpoint: POST /orders
#      JSON Body:
#      {
#        "user_id": int (required),
#        "order_date": "string in ISO format (optional)"
#      }
#   b) Add Multiple Products to an Order
#      Endpoint: POST /order/<int:order_id>/add_products
#      JSON Body:
#      {
#        "product_ids": [int, int, ...]
#      }
#   c) Update an Order’s Shipping Status
#      Endpoint: PUT /orders/<int:order_id>/shipping_status
#      JSON Body:
#      {
#        "shipping_status": "Processing" | "Shipped" | "Delivered" | "Canceled"
#      }
# -------------------------------------------------------------------------------------
# Endpoints That Do NOT Require JSON in the Body:
#   - Retrieve all users (paginated):         GET    /users
#   - Retrieve a single user by ID:           GET    /users/<int:id>
#   - Delete a user by ID:                    DELETE /users/<int:id>
#   - Retrieve all products (paginated):      GET    /products
#   - Retrieve a single product by ID:        GET    /products/<int:id>
#   - Delete a product by ID:                 DELETE /products/<int:id>
#   - Retrieve all orders (paginated):        GET    /all_orders
#   - Add a single product to an order:       POST   /orders/<int:order_id>/add_product/<int:product_id>
#   - Retrieve all orders for a specific user (paginated): GET    /order/user/<int:user_id>
#   - Retrieve all products from a specific order: GET    /order/<int:order_id>/products
#   - Retrieve all products a user has ordered: GET    /order/user/<int:user_id>/products
#   - Remove a product from an order:         DELETE /orders/<int:order_id>/remove_product/<int:product_id>
# =====================================================================================

#=============================
#=============CODE============
#=============================

#=========App Config=========#
#=========SQL Connect========#
#=========DEC. BASE==========#
#=========DB/MA Config=======#

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://<username>:<password>@<host>/<database>'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class = Base)
db.init_app(app)
ma = Marshmallow(app)

#=========Assosciation Table=========
order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key = True),
    Column("product_id", ForeignKey("products.id"), primary_key = True)
)

#=========Models=========
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement= True)
    name: Mapped[str] = mapped_column(String(30),nullable = False)
    address: Mapped[str] = mapped_column(String(100),nullable = False)
    email: Mapped[str] = mapped_column(String(100),nullable = False)
    
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key= True, autoincrement = True)
    order_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    shipping_status: Mapped[str] = mapped_column(String(20), default = "Processing")
    
    SHIPPING_STATUSES = ["Processing", "Shipped", "Delivered", "Canceled"]
    
    products = relationship("Product", secondary = order_product, back_populates="orders")
    user = relationship("User", back_populates = "orders")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key= True, autoincrement = True)
    product_name: Mapped[str] = mapped_column(String(100), nullable = False)
    price: Mapped[float] = mapped_column(Float, nullable = False)
    
    orders = relationship("Order", secondary = order_product, back_populates = "products")

#=========Schemas=========

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        
#=========Schema Instances=========
user_schema = UserSchema()
users_schema = UserSchema(many = True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many = True)

product_schema = ProductSchema()
products_schema = ProductSchema(many = True)

#=========Endpoint Routes=========

#---------R: Users---------
#Create New User (POST)
@app.route("/user", methods = ["POST"])
def create_user():
    if not request.json:  # Check for missing JSON body
        return jsonify({"error": "Missing JSON body"}), 400
    
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    existing_user = db.session.query(User).filter_by(email=user_data['email']).first()
    if existing_user:
        return jsonify({"error": "A user with this email already exists"}), 409
    
    new_user = User(name = user_data['name'], email = user_data['email'], address = user_data['address'])
    db.session.add(new_user)
    db.session.commit()
    
    return user_schema.jsonify(new_user), 201

@app.route("/users", methods=["POST"])
def create_users():
    # Check if request body contains JSON data
    if not request.json:
        return jsonify({"error": "Request body must be a JSON array of users"}), 400

    users_data = request.json
    created_users = []
    errors = []

    for index, user in enumerate(users_data):  # Add index for tracking errors
        try:
            # Validate and deserialize each user's input JSON data
            user_data = user_schema.load(user)
            
            # Check if user already exists
            existing_user = db.session.query(User).filter_by(email=user_data["email"]).first()
            if existing_user:
                errors.append({
                    "index": index,
                    "email": user_data["email"],
                    "error": "A user with this email already exists"
                })
                continue

            # Create a new User object
            new_user = User(
                name=user_data["name"],
                email=user_data["email"],
                address=user_data["address"]
            )
            
            # Add to session for bulk commit later
            db.session.add(new_user)
            created_users.append(new_user)

        except ValidationError as e:
            errors.append({"index": index, "errors": e.messages})
    
    # Commit all new users to the database
    if created_users:
        db.session.commit()

    response = {
        "created_users": [user_schema.dump(user) for user in created_users],
        "errors": errors
    }
    # Return response with created users and any errors
    status_code = 207 if errors else 201  # 207: Multi-Status
    return jsonify(response), status_code

#Retrieve all users (GET)
@app.route("/users", methods = ["GET"])
def get_users():
    #/users?page=<int:page>&per_page=<int:items_per>
    page = request.args.get("page", 1, type=int)  # Default to page 1
    per_page = request.args.get("per_page", 50, type=int)  # Default to 50 items per page
    pagination = db.paginate(
        db.select(User).order_by(User.name),
        page=page,
        per_page=per_page,
    )

    return jsonify({
        "items": [{"id": user.id, "name": user.name} for user in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200
# def get_users():
#     query = select(User)
#     users = db.session.execute(query).scalars().all()
    
#     return users_schema.jsonify(users), 200

#Retrieve specific users (GET)
@app.route("/users/<int:id>", methods = ["GET"])
def get_user(id):
    user = db.session.get(User,id)
    
    if not user:  # Handle missing user
        return jsonify({"error": f"User with ID {id} not found"}), 404
    
    return user_schema.jsonify(user), 200

#Update a user (PUT)
@app.route("/users/<int:id>", methods = ["PUT"])
def update_user(id):
    user = db.session.get(User, id)
    
    if not user:
        return jsonify({"message": "User not found."}), 404
    
    if not request.json:  # Check for missing JSON body
        return jsonify({"error": "Missing JSON body"}), 400
    
    try:
        user_data = user_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    if 'email' in user_data:
        existing_user = db.session.query(User).filter_by(email=user_data['email']).first()
        if existing_user and existing_user.id != id:
            return jsonify({"error": "A user with this email already exists"}), 409
    
    if 'name' in user_data:
        user.name = user_data['name']
    if 'email' in user_data:
        user.email = user_data['email']
    if 'address' in user_data:
        user.address = user_data['address']
    
    db.session.commit()
    return user_schema.jsonify(user), 200

#Delete a user (DELETE)
@app.route("/users/<int:id>", methods = ['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)
    
    if not user:
        return jsonify({"message": "User not found."}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f"successfully deleted user {id}"}), 200

#---------R: Products---------
#Create a new product (POST)
@app.route("/products", methods = ['POST'])
def create_product():
    if not request.json:  # Check for missing JSON body
        return jsonify({"error": "Missing JSON body"}), 400
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(product_name = product_data['product_name'], price = product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    
    return product_schema.jsonify(new_product), 200

#Retrieve all products (GET)
@app.route("/products", methods = ['GET'])
def get_products():
    # /products?page=<int:page>&per_page=<int:items_per>
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = db.paginate(
        db.select(Product).order_by(Product.product_name),
        page=page,
        per_page=per_page,
    )

    return jsonify({
        "items": [{"id": product.id, "name": product.product_name, "price": product.price} for product in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200
#def get_products()
    # query = select(Product)
    # products = db.session.execute(query).scalars().all()
    # return products_schema.jsonify(products), 200

#Retrieve specific product
@app.route("/products/<int:id>", methods = ['GET'])
def get_product(id):
    product = db.session.get(Product, id)
    
    if not product:
        return jsonify({"error": f"Product with ID {id} not found"}), 404

    return product_schema.jsonify(product), 200

#Update a product
@app.route("/products/<int:id>", methods = ['PUT'])
def update_product(id):
    product = db.session.get(Product, id)
    
    if not product:
        return jsonify({"message": "Invalid product ID."}), 404
    
    if not request.json:  # Check for missing JSON body
        return jsonify({"error": "Missing JSON body"}), 400
    
    try: 
        product_data = product_schema.load(request.json, partial = True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    if 'product_name' in product_data:
        product.product_name = product_data['product_name']
    if 'price' in product_data:
        product.price = product_data['price']
    db.session.commit()
    return product_schema.jsonify(product), 200

#Delete a Product (DELETE)
@app.route("/products/<int:id>", methods = ['DELETE'])
def delete_product(id):
    product = db.session.get(Product, id)
    
    if not product:
        return jsonify({"message": "Product not found."}), 400
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': f"successfully deleted product {id}"}), 200

#---------R: Orders---------

#Create order (POST)
@app.route("/orders", methods = ['POST'])
def new_order():
    try:
        order_data = order_schema.load(request.json)
    
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user = db.session.get(User, order_data["user_id"])
    if not user:
        return jsonify({"error": f"User with ID {order_data['user_id']} not found"}), 404
    
    new_order = Order(user_id = order_data["user_id"], order_date = order_data["order_date"])
    db.session.add(new_order)
    db.session.commit()
    
    return order_schema.jsonify(new_order), 201

@app.route("/all_orders", methods=["GET"])
def get_all_orders():
    # /all_orders?page=<int:page>&per_page=<int:items_per>
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = db.paginate(
        db.select(Order).order_by(Order.order_date),
        page=page,
        per_page=per_page,
    )

    return jsonify({
        "items": [{"id": order.id, "date": order.order_date, "user_id": order.user_id} for order in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200
# def get_orders():
#     query = select(Order)
#     orders = db.session.execute(query).scalars().all()
    
#     return orders_schema.jsonify(orders), 200


#Add a product to an order (POST)
@app.route("/orders/<int:order_id>/add_product/<int:product_id>", methods = ['POST'])
def add_to_order(order_id, product_id):

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": f"Order with ID {order_id} not found"}), 404
    
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": f"Product with ID {product_id} not found"}), 404
        
    order.products.append(product)
    db.session.commit()
    return jsonify({"message":f"added {product.product_name} to {order.id}"})

#Add multiple products to an order (POST)
#Sample JSON format
# {
#   "product_ids": [1, 2, 3]
# }
@app.route("/order/<int:order_id>/add_products", methods = ['POST'])
def add_multiple_to_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    product_data = request.json
    if not product_data or 'product_ids' not in product_data:
        return jsonify({"error": "Missing or invalid 'product_ids' in request body"}), 400
    
    if not product_data['product_ids']:  # Validate empty product_ids
        return jsonify({"error": "Product IDs list cannot be empty"}), 400
    
    added_products = []
    skipped_products = []

    for id in product_data['product_ids']:
        product = db.session.get(Product, id)
        
        if not product:
            skipped_products.append(id)
            continue
        
        if product in order.products:
            skipped_products.append(id)
        else:
            order.products.append(product)
            added_products.append(product.product_name)
    
    db.session.commit()

    response = {
        "message": "Products sorted successfully",
        "added_products": added_products,
        "skipped_products": skipped_products
    }
    
    return jsonify(response), 200
 
#Get all orders for a user 
@app.route("/order/user/<user_id>", methods = ['GET'])
def get_user_orders(user_id):
    # /order/user/<user_id>?page=<int:page>&per_page=<int:items_per>
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = db.paginate(
        db.select(Order).where(Order.user_id == user_id).order_by(Order.order_date),
        page=page,
        per_page=per_page,
    )

    return jsonify({
        "items": [{"id": order.id, "date": order.order_date} for order in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200
# def get_user_orders(user_id):
#     user = db.session.get(User, user_id)
    
#     if not user:
#         return jsonify({"error": f"User with ID {user_id} not found"}), 404
    
#     query = select(Order).where(Order.user_id == user_id)
#     orders = db.session.execute(query).scalars().all()
    
#     if not orders:
#         return jsonify({"message": f"User with ID {user_id} has no orders"}), 200
    
#     return orders_schema.jsonify(orders), 200

#Get all products from an order
@app.route("/order/<order_id>/products", methods = ['GET'])
def view_order_products(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": f"Order with ID {order_id} not found"}), 404
    
    products = order.products
    if not products:
        return jsonify({"message": f"Order with ID {order_id} has no products"}), 200
    
    return products_schema.jsonify(products), 200

#Get all products a person has ordered
@app.route("/order/user/<int:user_id>/products", methods = ['GET'])
def get_users_products(user_id):
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({"error": f"User with ID {user_id} not found"}), 404
    
    query = select(Order).where(Order.user_id == user_id)
    orders = db.session.execute(query).scalars().all()

    user_products = []
    for order in orders:
        user_products.extend(order.products)
    
    if not user_products:
        return jsonify({"error": f"No products for user ID {user_id} were found"}), 404
    
    return products_schema.jsonify(user_products), 200

#Create an invoice for an order
@app.route("/orders/<int:order_id>/invoice", methods=["GET"])
def generate_invoice(order_id):
    # Fetch the order from the database
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    # Fetch user associated with the order
    user = order.user
    # Fetch products in the order
    products = [
        {
            "product_name": product.product_name,
            "price": product.price
        }
        for product in order.products
    ]
    # Calculate total cost
    total_cost = sum(product["price"] for product in products)
    # Create the invoice dictionary
    invoice = {
        "invoice_id": order.id,
        "user": {
            "name": user.name,
            "email": user.email,
            "address": user.address
        },
        "order": {
            "order_id": order.id,
            "order_date": order.order_date
        },
        "products": products,
        "total_cost": total_cost
    }
    
    return jsonify(invoice), 200


#Delete a product from an order
@app.route("/orders/<int:order_id>/remove_product/<int:product_id>", methods = ['DELETE'])
def del_prd_from_ord(order_id, product_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": f"Order with ID {order_id} not found"}), 404
    
    products = order.products

    if not products:
        return jsonify({"message": f"Order with ID {order_id} has no products to remove"}), 200
    
    removed_products = []
    for product in products:
        if product.id == product_id:
            removed_products.append({"id": product.id, "name": product.product_name})
            order.products.remove(product)
            break
    if removed_products:
        db.session.commit()
        response = {
            "message": "Product removed successfully",
            "removed_products": removed_products,
        }
        return jsonify(response), 200
    else:
        return jsonify({"error": f"Product with ID {product_id} is not in Order with ID {order_id}"}), 404    

@app.route("/orders/<int:order_id>/shipping_status", methods = ['PUT'])
def update_shipping_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error":f"Order {order_id} not found"}), 404
    if not request.json or "shipping_status" not in request.json:
        return jsonify({"error":"request is missing 'shipping_status'"}), 400
    
    new_shipping_status = request.json["shipping_status"]
    
    if new_shipping_status not in order.SHIPPING_STATUSES:
        return jsonify({"error":"invalid shipping status provided"}), 400
    
    if new_shipping_status == "Canceled" and order.shipping_status == "Delivered":
        return jsonify({
            "error": f"Order {order_id} cannot be canceled because it is already delivered."
        }), 400
    
    order.shipping_status = new_shipping_status
    db.session.commit()
    
    return jsonify({
        "message": f"Order {order_id} shipping status updated to '{new_shipping_status}'",
        "order_id": order.id,
        "new_status": order.shipping_status
    }), 200


#=========DB Start/Drop=========
if __name__ == "__main__":
    with app.app_context():
        # db.drop_all()
        db.create_all()
    
    app.run(debug = True)
