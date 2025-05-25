from flask import request
from flask_restful import Resource
from app.models.store_model import store_model
from app.models.product_price import product_price_model


class ProductPriceListResource(Resource):
    def get(self, product_id):
        """
        GET /products/<product_id>/prices
        Returns all prices for a product, sorted by price ascending.
        """
        try:
            prices = product_price_model.get_prices_for_product(product_id)
            return prices, 200
        except Exception as e:
            return {"error": str(e)}, 500

    def post(self, product_id):
        """
        POST /products/<product_id>/prices
        Adds a new store + price for the specified product.
        """
        try:
            data = request.get_json()

            store_id = store_model.get_or_create({
                "store": data["store"],
                "address": data.get("address"),
                "link": data.get("link"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude")
            })

            product_price_model.add_price(
                product_id=product_id,
                store_id=store_id,
                price=data["price"],
                currency=data.get("currency", "USD")
            )

            return {"status": "success"}, 201

        except Exception as e:
            return {"error": str(e)}, 500
