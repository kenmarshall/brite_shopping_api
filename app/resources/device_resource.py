from datetime import datetime

from flask import request
from flask_restful import Resource

from app.db import db
from app.services.logger_service import logger


class DeviceResource(Resource):
    def post(self):
        """Register or update a device profile."""
        try:
            data = request.get_json(force=True)
            device_id = (data.get("device_id") or "").strip()
            if not device_id:
                return {"message": "device_id is required"}, 400

            platform = (data.get("platform") or "").strip().lower()
            if platform not in ("ios", "android", "web"):
                platform = "unknown"

            push_token = (data.get("push_token") or "").strip() or None

            now = datetime.utcnow()
            result = db.devices.find_one_and_update(
                {"device_id": device_id},
                {
                    "$set": {
                        "platform": platform,
                        "push_token": push_token,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "device_id": device_id,
                        "shopping_list": [],
                        "created_at": now,
                    },
                },
                upsert=True,
                return_document=True,
            )
            return {
                "device_id": result["device_id"],
                "platform": result.get("platform", "unknown"),
                "created_at": str(result.get("created_at", "")),
            }, 200
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return {"message": "An error occurred"}, 500


class DeviceShoppingListResource(Resource):
    def get(self, device_id: str):
        """Get shopping list for a device."""
        try:
            device = db.devices.find_one(
                {"device_id": device_id},
                {"shopping_list": 1, "_id": 0},
            )
            if not device:
                return {"shopping_list": []}, 200
            return {"shopping_list": device.get("shopping_list", [])}, 200
        except Exception as e:
            logger.error(f"Error fetching shopping list: {e}")
            return {"message": "An error occurred"}, 500

    def put(self, device_id: str):
        """Sync (overwrite) shopping list for a device."""
        try:
            data = request.get_json(force=True)
            shopping_list = data.get("shopping_list")
            if not isinstance(shopping_list, list):
                return {"message": "shopping_list must be an array"}, 400

            now = datetime.utcnow()
            db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "shopping_list": shopping_list,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "device_id": device_id,
                        "created_at": now,
                    },
                },
                upsert=True,
            )
            return {"message": "Shopping list synced", "count": len(shopping_list)}, 200
        except Exception as e:
            logger.error(f"Error syncing shopping list: {e}")
            return {"message": "An error occurred"}, 500
