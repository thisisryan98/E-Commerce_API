# E-Commerce_API
API program project for E-Commerce

A RESTful API for managing users, products, and orders in an e-commerce system. Built with Python, Flask, SQLAlchemy, and Marshmallow.
Features
User Management: Create, update, retrieve, and delete users.
Product Management: Add, update, retrieve, and delete products.
Order Management: Place orders, manage products in orders, and update shipping status.
Pagination: Retrieve lists of users, products, and orders with paginated responses.
Validation: Ensures correct data input using Marshmallow schemas.
Invoices: Generate detailed invoices for orders.

Requirements
Python 3.8+
MySQL 8.0+
Flask
Flask-SQLAlchemy
Flask-Marshmallow
Marshmallow
MySQL Connector

Installation
Clone the Repository
Copy code
git clone https://github.com/your-repo-name/ecommerce-api.git
cd ecommerce-api
Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install Dependencies
pip install -r requirements.txt
Configure the Database
Update the SQLALCHEMY_DATABASE_URI in the app.config section of the code to match your MySQL setup:
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://<username>:<password>@<host>/<database>'
Set Up the Database
Run program:
python app.py
The database tables will be created on the first run.

Usage
Run the Application
python app.py
The application will start on http://localhost:5000.

API Endpoints
Users
Create a User: POST /user
Retrieve All Users: GET /users?page=<int>&per_page=<int>
Retrieve a User by ID: GET /users/<id>
Update a User: PUT /users/<id>
Delete a User: DELETE /users/<id>

Products
Create a Product: POST /products
Retrieve All Products: GET /products?page=<int>&per_page=<int>
Retrieve a Product by ID: GET /products/<id>
Update a Product: PUT /products/<id>
Delete a Product: DELETE /products/<id>

Orders
Place an Order: POST /orders
Retrieve All Orders: GET /all_orders?page=<int>&per_page=<int>
Add a Product to an Order: POST /orders/<order_id>/add_product/<product_id>
Add Multiple Products to an Order: POST /order/<order_id>/add_products
Update Shipping Status: PUT /orders/<order_id>/shipping_status
Generate an Invoice: GET /orders/<order_id>/invoice

Example Requests:
Create a User
Json
POST /user
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "address": "123 Elm Street"
}
Create a Product
Json
POST /products
{
  "product_name": "Laptop",
  "price": 1299.99
}
Place an Order
Json
POST /orders
{
  "user_id": 1,
  "order_date": "2025-01-01T12:00:00Z"
}

Pagination
Most list endpoints (e.g., /users, /products, /all_orders) support pagination with the following query parameters:
page: The page number (default: 1).
per_page: The number of items per page (default: 50).

Ways to Expand
Add JWT authentication
Add functionalities to ensure users have logins and can only access their own data, and that certain endpoints are restricted to an admin class
Additional Endpoints 
Create more complex functions or add more customizability (i.e. an endpoint that would delete users and all orders related to the user). 

Credits / Disclaimer
Author: Ryan Sullivan
Date: January 2025
This project was developed as a learning exercise in building RESTful APIs with Python, Flask, SQLAlchemy, and rudimentary database management. The focus is on improving skills in object-oriented programming (OOP), API development, and data validation.


