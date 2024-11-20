import io
import logging
from flask_restful import Resource
from flask import request, jsonify
from app.tasks import receipt_task
from app.services import extract_price_info_from_receipt_image
from PIL import Image


ACCEPTED_IMAGE_FILE_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "heif", "webp"}

logger = logging.getLogger(__name__)


def image_file_extension_is_allowed(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ACCEPTED_IMAGE_FILE_EXTENSIONS
    )


class ReceiptResource(Resource):
    def post(self):

        try:
            file = request.files.get("file")

            if not file or file.filename == "":
                logger.info("image file not found")
                return {"message": "image file not found"}, 400

            if not image_file_extension_is_allowed(file.filename):
                logger.info(f"file extension is not allowed {file.filename}")
                return {"message": "file extension is not allowed"}, 400

            image = Image.open(io.BytesIO(file.read()))

            extracted_text = extract_price_info_from_receipt_image(image)
        
            return jsonify({"extracted_text": extracted_text})
            # receipt_task.process.delay("Processed in the background")
        except Exception as e:

            return {"message": f"An error occurred {e}"}, 500
