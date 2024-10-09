from PIL import Image
import pytesseract

def extract_price_info_from_receipt_image(image):
    text = pytesseract.image_to_string(image)
    
    return text

def price_mart_parser(text):
  
    
    # This is a dummy function that simulates the parsing of the text extracted from the receipt image
    return {
        'total': 100.00,
        'items': [
            {
                'name': 'Apple',
                'price': 1.00
            },
            {
                'name': 'Banana',
                'price': 2.00
            },
            {
                'name': 'Orange',
                'price': 3.00
            }
        ]
    }