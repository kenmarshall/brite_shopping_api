<!-- SYNC: When updating this file, also update AGENTS.md with the same changes (and vice versa). -->
# Brite Shopping API

Flask REST backend for product/store/price management and Google Maps integration. Part of the Brite Shopping price comparison platform for Jamaican shoppers.

## Product Vision
- Price comparison platform for Jamaican shoppers
- Products have an estimated/average price + per-location prices from each store
- User flow: search → see product + estimated price → see all store locations + their prices → decide
- A "store location" can be online as long as Jamaicans can access it

## Architecture
- **This API is a lightweight REST mediator** — deployed on Render free tier. NO AI or scraping logic.
- Just reads from MongoDB and serves data to the mobile app.
- **Catalog engine** (separate repo, runs on developer's laptop) handles all heavy AI, scraping, enrichment.
- **Mobile app** only talks to this API, never to the catalog engine.
- All repos at `/Users/kennethmarshall/dev/brite_shopping/`
- Shared MongoDB Atlas database (`brite_shopping`)

## Tech Stack
- **Framework**: Flask + Flask-RESTful
- **Database**: PyMongo (MongoDB Atlas M0)
- **External APIs**: Google Maps (Places, Geocoding)
- **Production**: Gunicorn on Render.com

## Development
- Local: `python run.py` (Flask :5000)
- Tests: `pytest`
- Env vars: MONGO_URI, MONGO_DATABASE_NAME, GOOGLE_MAPS_API_KEY

## API Endpoints
- `GET/POST /products`, `GET/PUT/DELETE /products/<id>`
- `GET/POST /products/<id>/prices`
- `GET /stores` (by address or name)
- `GET /stores/search` (Google Maps)
- `GET /health`

## Key Patterns
- Models use static methods (e.g., `ProductModel.get_one()`, `StoreModel.get_or_create()`)
- Store dedup by `place_id`, product dedup by `name`
- Price upsert by (product_id, store_id) pair

## Data Context
- Catalog engine writes ~7,500+ products from multiple Jamaican grocery sources (ShopSampars, Store To Door, CoolMarket, Hi-Lo, Grace Foods)
- All prices are in JMD
- Products have `estimated_price` (average across locations), `location_prices` (per-store), `match_key` for cross-store deduplication
- Stores can be online-only or physical with multiple branches

## Future Work
- **Store locations with Google Maps**: Extend `StoreLocation` model with `place_id`, `lat`, `lng` for map display and `is_online` boolean. Google Maps search endpoint (`GET /stores/search`) already exists. Future: per-branch product availability and pricing.
- **Brand inference**: Brand field exists but is inconsistent across sources — currently hidden in mobile UI. Future: expose once data quality improves.
- **Unit price comparison**: API should support querying/sorting by normalized unit price ($/kg, $/L).
