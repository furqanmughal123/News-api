# News Scraper API Endpoints

Base URL: `http://127.0.0.1:8000`

## 1. Get All News
Fetches the latest news articles from all configured sources.

- **URL**: `/news`
- **Method**: `GET`

## 2. Get News by Source
Fetches news from a specific source.

- **URL**: `/news/{source_id}`
- **Method**: `GET`
- **Path Parameters**:
  - `source_id` (string): The ID of the news source (e.g., `geo_tv`, `reuters`).

## 3. List Sources
Returns a list of all available news sources with their IDs.

- **URL**: `/sources`
- **Method**: `GET`
- **Content**:
    ```json
    [
      {"id": "geo_tv", "name": "Geo TV"},
      {"id": "bbc_news", "name": "BBC News"},
      ...
    ]
    ```

## 4. Health Check
Verifies that the API is running and reachable.

- **URL**: `/`
- **Method**: `GET`

## 5. Web Dashboard (UI)
Serves the HTML frontend.

- **URL**: `/ui`
- **Method**: `GET`

## 6. API Documentation
Auto-generated interactive API documentation (Swagger UI).

- **URL**: `/docs`
- **Method**: `GET`

---

## Available Source IDs
Use these IDs with the `/news/{source_id}` endpoint:

- `geo_tv`
- `bbc_news`
- `cnn`
- `pakistan_point`
- `trt_world`
- `middle_east_eye`
