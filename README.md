# Brite Shopping API

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A REST API backend for the **Brite Shopping** ecosystem. This Flask-based API provides product management, store location services, and price comparison functionality for the mobile grocery shopping application.

## 🎯 Project Overview

**Brite Shopping API** is the backend component of the intelligent shopping ecosystem consisting of three core components:

- **[brite-shopping-catalog-engine](https://github.com/kenmarshall/brite-shopping-catalog-engine)** - AI-powered catalog builder
- **[brite-shopping-api](https://github.com/kenmarshall/brite-shopping-api)** (This project) - REST API backend 
- **[brite-shopping-mobile](https://github.com/kenmarshall/brite-shopping-mobile)** - React Native mobile app

### Data Flow
```
🤖 Catalog Engine → 📋 MongoDB Atlas → 🔌 API → 📱 Mobile App → 👥 Users
```

## ✨ Features

- **🛍️ Product Management** - CRUD operations for grocery products
- **🏪 Store Management** - Store location and details management
- **💰 Price Tracking** - Multi-store price comparison functionality
- **🗺️ Google Maps Integration** - Real store location data and search
- **🔍 Product Search** - Name-based product search functionality
- **📊 Price Analytics** - Lowest price detection and comparison

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **MongoDB Atlas** account and connection string
3. **Google Maps API** key for store location services

### Installation

```bash
# Clone the repository
git clone https://github.com/kenmarshall/brite-shopping-api.git
cd brite-shopping-api

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your MongoDB URI and Google Maps API key
```

### Environment Variables

Create a `.env` file with the following:

```bash
# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/brite_shopping

# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Flask
FLASK_ENV=development
```

### Running the Application

```bash
# Development
python run.py

# Production with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

## 📚 API Endpoints

### Products

- `GET /products` - List all products or search by name
- `GET /products/{id}` - Get specific product details
- `POST /products` - Add new product with store and price info

### Stores

- `GET /stores` - Find stores by address or name (Google Maps)
- `GET /stores/search` - Search for store locations

### Product Prices

- `GET /products/{id}/prices` - Get all prices for a product
- `POST /products/{id}/prices` - Add price for a product at a store

## 🏗️ Architecture

### Project Structure
```
brite-shopping-api/
├── app/
│   ├── models/           # Database models
│   │   ├── product_model.py
│   │   ├── product_price_model.py
│   │   └── store_model.py
│   ├── resources/        # API endpoints
│   │   ├── product_resource.py
│   │   ├── product_price_resource.py
│   │   ├── store_resource.py
│   │   └── store_search_resource.py
│   ├── services/         # External service integrations
│   │   ├── google_maps_service.py
│   │   └── logger_service.py
│   ├── tasks/           # Background tasks
│   └── db.py            # Database connection
├── tests/               # Test suite
├── requirements.txt     # Dependencies
├── run.py              # Application entry point
└── README.md           # This file
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/models/        # Model tests
pytest tests/resources/     # API endpoint tests
```

## 🚀 Deployment

The API is configured for deployment on Render.com using the included `render.yaml` configuration.

### Deploy to Render

1. Connect your GitHub repository to Render
2. The `render.yaml` will automatically configure the deployment
3. Set environment variables in the Render dashboard
4. Deploy!

## 📝 Usage Examples

### Adding a Product with Price

```bash
curl -X POST http://localhost:5000/products \
  -H "Content-Type: application/json" \
  -d '{
    "product_data": {
      "name": "Grace Kidney Beans",
      "brand": "Grace",
      "size": "400g"
    },
    "store_info": {
      "place_id": "ChIJ...",
      "store": "Hi-Lo Food Stores",
      "address": "123 Main St, Kingston"
    },
    "price": 250.00,
    "currency": "JMD"
  }'
```

### Searching for Products

```bash
# Search by name
curl "http://localhost:5000/products?name=kidney beans"

# Get specific product
curl "http://localhost:5000/products/607f1f77bcf86cd799439011"
```

### Finding Stores

```bash
# Search stores by name
curl "http://localhost:5000/stores/search?name=Hi-Lo"

# Find store by address
curl "http://localhost:5000/stores/search?address=123 Main St Kingston"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [Brite Shopping Catalog Engine](https://github.com/kenmarshall/brite-shopping-catalog-engine) - AI-powered product catalog builder
- [Brite Shopping Mobile](https://github.com/kenmarshall/brite-shopping-mobile) - React Native mobile application
