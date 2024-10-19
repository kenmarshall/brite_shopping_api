from flask_restful import Resource
from flask import request

ACCEPTED_IMAGE_FILE_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "heif", "webp"}


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
            return {"message": "image file not found"}, 400

        if not image_file_extension_is_allowed(file.filename):
            return {"message": "file extension is not allowed"}, 400
        
        # Store file in temporary queue for processing
      except Exception as e:
        
        return {"message": "An error occurred"}
      