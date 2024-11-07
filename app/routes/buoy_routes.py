from flask import Blueprint, jsonify, request
from surfpy import Location, BuoyStations, BuoyStation
from datetime import datetime
import pytz
from functools import lru_cache

bp = Blueprint('buoys', __name__, url_prefix='/api/buoys')


# Cache for buoy data
@lru_cache(maxsize=128)
def fetch_buoy_data(station_id, data_count=20):
    try:
        stations = BuoyStations()
        stations.fetch_stations()
        station = stations.find_station(station_id)

        if not station:
            return None

        # Try to get detailed wave reading first
        data = station.fetch_detailed_wave_reading(data_count)
        if data:
            return data

        # Fall back to latest reading if detailed not available
        return [station.fetch_latest_reading()]
    except Exception as e:
        print(f"Error fetching buoy data: {str(e)}")
        return None


@bp.route('/nearby/<float:lat>/<float:lon>')
def get_nearby_buoys(lat, lon):
    try:
        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({
                'error': 'Invalid coordinates',
                'valid_ranges': {
                    'latitude': '[-90, 90]',
                    'longitude': '[-180, 180]'
                }
            }), 400

        # Get optional parameters with validation
        count = min(max(1, int(request.args.get('count', '5'))), 10)
        active_only = request.args.get('active', 'true').lower() == 'true'
        buoy_type = request.args.get('type', BuoyStation.BuoyType.none)

        location = Location(lat, lon)
        stations = BuoyStations()
        if not stations.fetch_stations():
            return jsonify({
                'error': 'Failed to fetch buoy stations'
            }), 500

        nearby = []
        closest_stations = stations.find_closest_stations(location, count)

        for station in closest_stations:
            if active_only and not station.active:
                continue

            if buoy_type != BuoyStation.BuoyType.none and station.buoy_type != buoy_type:
                continue

            nearby.append({
                'id': station.station_id,
                'name': station.name,
                'location': {
                    'latitude': station.location.latitude,
                    'longitude': station.location.longitude
                },
                'distance_km': location.distance(station.location) / 1000,
                'active': station.active,
                'type': station.buoy_type,
                'owner': station.owner,
                'program': station.program
            })

        return jsonify({
            'request': {
                'latitude': lat,
                'longitude': lon,
                'count': count,
                'active_only': active_only,
                'type': buoy_type
            },
            'stations': nearby
        })

    except Exception as e:
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500


@bp.route('/<string:station_id>/data')
def get_buoy_data(station_id):
    try:
        # Get optional parameters
        data_count = min(max(1, int(request.args.get('count', '20'))), 50)

        # Fetch data with caching
        data = fetch_buoy_data(station_id, data_count)
        if not data:
            return jsonify({
                'error': 'Failed to fetch buoy data',
                'station_id': station_id
            }), 500

        response = []
        for reading in data:
            measurement = {
                'timestamp': reading.date.isoformat() if reading.date else None,
                'wave_summary': None,
                'wind': {
                    'speed': reading.wind_speed,
                    'direction': reading.wind_direction,
                    'compass_direction': reading.wind_compass_direction,
                    'gust': reading.wind_gust
                },
                'weather': {
                    'pressure': reading.pressure,
                    'air_temperature': reading.air_temperature,
                    'water_temperature': reading.water_temperature,
                    'dewpoint': reading.dewpoint_temperature
                },
                'swells': []
            }

            if reading.wave_summary:
                measurement['wave_summary'] = {
                    'height': reading.wave_summary.wave_height,
                    'period': reading.wave_summary.period,
                    'direction': reading.wave_summary.direction,
                    'compass_direction': reading.wave_summary.compass_direction
                }

            for swell in reading.swell_components:
                measurement['swells'].append({
                    'height': swell.wave_height,
                    'period': swell.period,
                    'direction': swell.direction,
                    'compass_direction': swell.compass_direction
                })

            response.append(measurement)

        return jsonify({
            'station_id': station_id,
            'readings': response
        })

    except ValueError as e:
        return jsonify({
            'error': 'Invalid parameters',
            'details': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500


@bp.route('/docs')
def get_docs():
    return jsonify({
        'endpoints': {
            'nearby': {
                'path': '/api/buoys/nearby/<lat>/<lon>',
                'method': 'GET',
                'parameters': {
                    'lat': 'latitude (-90 to 90)',
                    'lon': 'longitude (-180 to 180)',
                    'count': 'number of stations to return (1-10, default: 5)',
                    'active': 'filter for active stations only (true/false, default: true)',
                    'type': f'buoy type ({", ".join(vars(BuoyStation.BuoyType).keys())})'
                },
                'example': '/api/buoys/nearby/41.4302/-71.455?count=5&active=true'
            },
            'data': {
                'path': '/api/buoys/<station_id>/data',
                'method': 'GET',
                'parameters': {
                    'count': 'number of readings to return (1-50, default: 20)'
                },
                'example': '/api/buoys/44097/data?count=20'
            }
        }
    })