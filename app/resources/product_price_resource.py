from flask import request
from flask_restful import Resource
from app.models.store_model import StoreModel
from app.models.product_price_model import ProductPriceModel


class ProductPriceListResource(Resource):
    def get(self, product_id):
        """
        GET /products/<product_id>/prices
        Returns all prices for a product, sorted by price ascending.
        """
        try:
            prices = ProductPriceModel.get_prices_for_product(product_id)
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

            store_id = StoreModel.get_or_create({
                "place_id": data.get("place_id"),
                "store": data["store"],
                "address": data.get("address"),
                "link": data.get("link"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude")
            })

            price_id = ProductPriceModel.upsert_price(
                product_id=product_id,
                store_id=str(store_id),
                price=data["price"],
                currency=data.get("currency", "JMD")
            )

            return {"status": "success", "price_id": str(price_id)}, 201

        except Exception as e:
            return {"error": str(e)}, 500
