
# Wave Forecasting API

A RESTful API service that provides real-time wave, weather, and tide predictions by integrating NOAA's Global Forecast System (GFS) and NDBC buoy data. Built with Python and Flask, this API delivers accurate surf forecasting data with efficient caching and comprehensive error handling.

## Features

- **Wave Forecasts**: Real-time wave height calculations, swell analysis, and breaking wave predictions
- **Weather Integration**: NOAA GFS data processing for detailed weather forecasting
- **Buoy Data**: Live and historical data from NDBC buoys
- **Tide Predictions**: Accurate tide forecasting using NOAA tide stations
- **Performance Optimized**: Redis caching and rate limiting
- **Error Handling**: Comprehensive validation and error management
- **Documentation**: Detailed API documentation and examples

## API Reference

### Forecast Endpoints

```http
GET /api/forecast/location
```

| Parameter | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `lat`     | float  | Latitude (-90 to 90)                |
| `lon`     | float  | Longitude (-180 to 180)             |
| `depth`   | float  | Water depth in meters (default: 30) |
| `angle`   | float  | Beach angle in degrees (default: 145) |
| `slope`   | float  | Beach slope (default: 0.02)         |
| `hours`   | int    | Forecast hours (1-384, default: 24) |

### Buoy Endpoints

```http
GET /api/buoys/location
```

| Parameter | Type    | Description                            |
|-----------|---------|----------------------------------------|
| `lat`     | float   | Latitude (-90 to 90)                  |
| `lon`     | float   | Longitude (-180 to 180)               |
| `count`   | int     | Number of buoys to return (1-10, default: 5) |
| `active`  | bool    | Filter for active buoys (default: true) |
| `type`    | string  | Buoy type (buoy, fixed, etc.)         |

```http
GET /api/buoys/{station_id}/data
```

### Tide Endpoints

```http
GET /api/tides/location
```

| Parameter | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `lat`     | float  | Latitude (-90 to 90)                |
| `lon`     | float  | Longitude (-180 to 180)             |
| `days`    | int    | Days to forecast (default: 3)       |

## Technology Stack

- **Backend**: Python, Flask
- **Data Processing**: NumPy, pygrib, netCDF4
- **Caching**: Redis
- **API Features**: Rate limiting, CORS support
- **Data Sources**: NOAA GFS, NDBC Buoys, NOAA Tides & Currents

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/wave-forecasting-api.git
cd wave-forecasting-api
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Run the development server:

```bash
python run.py
```

## Docker Deployment

Build and run with Docker:

```bash
# Build the image
docker build -t wave-forecasting-api .

# Run the container
docker run -d -p 5000:5000 wave-forecasting-api
```

## Example Usage

### Get Wave Forecast

```bash
curl "http://localhost:5000/api/forecast/location?lat=41.35&lon=-71.4"
```

Example response:

```json
{
    "forecasts": [
        {
            "timestamp": "2024-11-07T12:00:00+00:00",
            "wave_summary": {
                "height": 1.92,
                "period": 6.40,
                "direction": 180.64,
                "compass_direction": "S",
                "steepness": "STEEP"
            },
            "breaking_waves": {
                "maximum_height": 2.16,
                "minimum_height": 1.54
            },
            "swells": [
                {
                    "height": 1.88,
                    "period": 6.40,
                    "direction": 177.79,
                    "compass_direction": "S"
                }
            ],
            "wind": {
                "speed": 4.38,
                "direction": 294.14,
                "compass_direction": "WNW"
            }
        }
    ],
    "location": {
        "latitude": 41.35,
        "longitude": -71.4,
        "depth": 30.0,
        "angle": 145.0,
        "slope": 0.02
    }
}
```

### Find Nearby Buoys

```bash
curl "http://localhost:5000/api/buoys/location?lat=41.35&lon=-71.4&count=3"
```

### Get Buoy Data

```bash
curl "http://localhost:5000/api/buoys/44097/data"
```

## Environment Variables

```env
FLASK_ENV=development
FLASK_APP=run.py
REDIS_URL=redis://localhost:6379
CACHE_TIMEOUT=300
RATE_LIMIT_PER_MINUTE=60
```

## Development

**Requirements:**
- Python 3.9+
- Redis server for caching
- Environment variables configured

## Error Handling

The API provides detailed error responses:

```json
{
    "error": "Invalid parameters",
    "details": "Latitude must be between -90 and 90",
    "timestamp": "2024-11-07T12:00:00Z"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Server Error

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NOAA for providing GFS and buoy data
- NDBC for buoy station information
- Weather data processing libraries contributors
