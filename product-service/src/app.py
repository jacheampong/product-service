from flask import Flask, jsonify, request
import logging.config
from sqlalchemy import exc
import configparser
from db import db
from Product import Product

# Configure the logging package from the logging ini file
logging.config.fileConfig("/config/logging.ini", disable_existing_loggers=False)

# Get a logger for our module
log = logging.getLogger(__name__)


def get_database_url():
    """
    Loads database configuration from the db.ini file and returns
    a database URL.
     return: A database URL, build from the values ub the db.ini file
    """
    # Load database configuration
    config = configparser.ConfigParser()
    config.read('/config/db.ini')
    database_configuration = config['mysql']
    host = database_configuration['host']
    username = database_configuration['username']
    db_password = open('/run/secrets/db_password')
    password = db_password.read().strip()
    # password = database_configuration['password']
    database = database_configuration['database']
    database_url = f'mysql://{username}:{password}@{host}/{database}'
    log.info(f'Connecting to database: {database_url}')
    return database_url


# configure Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
db.init_app(app)


# curl -v http://localhost:5000/products
@app.route("/products")
def get_products():
    log.debug('GET /products')
    try:
        products = [product.json for product in Product.find_all()]
        return jsonify(products)
    except exc.SQLAlchemyError:
        log.exception('An exception occurred while retrieving all products')
        return 'An exception occurred while retrieving all products ', 500


# curl -v http://localhost:5000/products/1
@app.route("/products/<int:id>")
def get_product(id):
    log.debug(f'GET /product/{id}')

    try:
        product = Product.find_by_id(id)
        if product:
            return jsonify(product.json)
        log.warning(f'GET /product/{id}: Product not found')
        return f"Product with id {id} not found", 404

    except exc.SQLAlchemyError:
        log.exception('An exception occurred while retrieving product id: {id}')
        return f'An exception occurred while retrieving all product id {id} ', 500


# curl --header "Content-Type: application/json" --request POST --data '{"name": "Product 4"}' -v
# http://localhost:5000/product
@app.route("/product", methods=["POST"])
def post_product():
    # print('POST /product')

    # Retrieve the product from the request body
    request_product = request.json
    log.debug(f'POST /product with product: {request_product}')

    # create a new product
    product = Product(None, request_product['name'])

    try:
        # save the product to database
        product.save_to_db()

        # Return the new product back to the client
        return jsonify(product.json), 201

    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while creating product with name: {product.name}')
        return f'An exception occurred while creating product with name: {product.name}', 500


# curl --header "Content-Type: application/json" --request PUT --data '{"name": "Product 2"}' -v
# http://localhost:5000/products
@app.route("/product/<int:id>", methods=["PUT"])
def put_product(id):
    log.debug(f'PUT /product/{id} with product {request.json}')

    try:
        # Find the product with the specified ID
        product = Product.find_by_id(id)

        if product:
            # Get the request payload
            updated_product = request.json

            product.name = updated_product["name"]
            product.save_to_db()

            return jsonify(product.json), 200

        log.warning(f"PUT /product/{id}: Existing Product id {id} not found")
        return f"Product with id {id} not found", 404

    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while updating product with name: {product.name}')
        return f'An exception occurred while updating product with name: {product.name}', 500


# Curl --request DELETE -v http://localhost:5000/product/2
@app.route("/product/<int:id>", methods=["DELETE"])
def delete_product(id):
    log.debug(f'DELETE /product/{id} ')
    # Find the product with the specified ID
    try:
        product = Product.find_by_id(id)

        if product:
            product.delete_from_db()
            return jsonify({
                'message': f"Product with id {id} deleted"
            }), 200

        log.warning(f'DELETE /product/{id}: Existing product not found')
        return f"Product with id {id} not found", 404

    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while deleting id: {id}')
        return f'An exception occurred while deleting id: {id}', 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
