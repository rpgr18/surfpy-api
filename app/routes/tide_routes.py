from flask import Blueprint, jsonify, request
from surfpy import Location, TideStations, TideStation
from datetime import datetime, timedelta
import pytz
from functools import lru_cache

bp = Blueprint('tides', __name__, url_prefix='/api/tides')


# Cache for tide data
@lru_cache(maxsize=128)
def fetch_tide_data(station_id, start_time_str, end_time_str, datum):
    try:
        stations = TideStations()
        stations.fetch_stations()
        station = stations.find_station(station_id)

        if not station:
            return None

        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)

        return station.fetch_tide_data(
            start_time,
            end_time,
            datum=datum,
            interval=TideStation.DataInterval.high_low
        )
    except Exception as e:
        print(f"Error fetching tide data: {str(e)}")
        return None


@bp.route('/location')
def get_tides():
    try:
        # Validate required parameters
        if 'lat' not in request.args or 'lon' not in request.args:
            return jsonify({
                'error': 'Missing parameters',
                'required': ['lat', 'lon']
            }), 400

        try:
            lat = float(request.args.get('lat'))
            lon = float(request.args.get('lon'))
        except ValueError:
            return jsonify({
                'error': 'Invalid coordinate format',
                'details': 'Coordinates must be numeric values'
            }), 400

        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({
                'error': 'Invalid coordinates',
                'valid_ranges': {
                    'latitude': '[-90, 90]',
                    'longitude': '[-180, 180]'
                }
            }), 400

        # Create location and get time range
        location = Location(lat, lon)
        days = min(max(1, int(request.args.get('days', '3'))), 10)  # Limit between 1-10 days
        start_time = datetime.now(pytz.UTC)
        end_time = start_time + timedelta(days=days)

        # Find nearest station
        stations = TideStations()
        if not stations.fetch_stations():
            return jsonify({
                'error': 'Failed to fetch tide stations'
            }), 500

        station = stations.find_closest_station(location)
        if not station:
            return jsonify({
                'error': 'No tide station found near location',
                'location': {'latitude': lat, 'longitude': lon}
            }), 404

        # Try different datums in order of preference
        result = None
        used_datum = None
        for datum in [
            TideStation.TideDatum.mean_lower_low_water,
            TideStation.TideDatum.mean_sea_level,
            TideStation.TideDatum.mean_tide_level
        ]:
            result = fetch_tide_data(
                station.station_id,
                start_time.isoformat(),
                end_time.isoformat(),
                datum
            )
            if result:
                used_datum = datum
                break

        if not result:
            return jsonify({
                'error': 'Failed to fetch tide data',
                'station_id': station.station_id,
                'location': {'latitude': lat, 'longitude': lon}
            }), 500

        tide_events, tide_data = result

        # Format response
        response = {
            'station': {
                'id': station.station_id,
                'name': station.name,
                'location': {
                    'latitude': station.location.latitude,
                    'longitude': station.location.longitude
                },
                'distance_km': location.distance(station.location) / 1000
            },
            'request': {
                'latitude': lat,
                'longitude': lon,
                'days': days,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'datum': used_datum
            },
            'tides': [],
            'predictions': []
        }

        if tide_events:
            response['tides'] = [{
                'timestamp': event.date.isoformat(),
                'type': event.tidal_event,
                'height': event.water_level,
                'datum': event.water_level_datum
            } for event in tide_events]

        if tide_data:
            response['predictions'] = [{
                'timestamp': pred.date.isoformat(),
                'height': pred.water_level,
                'datum': pred.water_level_datum
            } for pred in tide_data]

        return jsonify(response)

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500


@bp.route('/station/<station_id>')
def get_station_tides(station_id):
    try:
        # Validate and get parameters
        days = min(max(1, int(request.args.get('days', '3'))), 10)
        start_time = datetime.now(pytz.UTC)
        end_time = start_time + timedelta(days=days)

        # Get station data
        stations = TideStations()
        if not stations.fetch_stations():
            return jsonify({
                'error': 'Failed to fetch tide stations'
            }), 500

        station = stations.find_station(station_id)
        if not station:
            return jsonify({
                'error': 'Station not found',
                'station_id': station_id
            }), 404

        # Fetch tide data with caching
        result = fetch_tide_data(
            station_id,
            start_time.isoformat(),
            end_time.isoformat(),
            TideStation.TideDatum.mean_lower_low_water
        )

        if not result:
            return jsonify({
                'error': 'Failed to fetch tide data',
                'station_id': station_id
            }), 500

        tide_events, tide_data = result

        response = {
            'station': {
                'id': station.station_id,
                'name': station.name,
                'location': {
                    'latitude': station.location.latitude,
                    'longitude': station.location.longitude
                }
            },
            'request': {
                'days': days,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'datum': TideStation.TideDatum.mean_lower_low_water
            },
            'tides': [],
            'predictions': []
        }

        if tide_events:
            response['tides'] = [{
                'timestamp': event.date.isoformat(),
                'type': event.tidal_event,
                'height': event.water_level,
                'datum': event.water_level_datum
            } for event in tide_events]

        if tide_data:
            response['predictions'] = [{
                'timestamp': pred.date.isoformat(),
                'height': pred.water_level,
                'datum': pred.water_level_datum
            } for pred in tide_data]

        return jsonify(response)

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
            'location': {
                'path': '/api/tides/location',
                'method': 'GET',
                'parameters': {
                    'lat': 'latitude (-90 to 90)',
                    'lon': 'longitude (-180 to 180)',
                    'days': 'number of days to forecast (1-10, default: 3)'
                },
                'example': '/api/tides/location?lat=41.4302&lon=-71.455&days=3'
            },
            'station': {
                'path': '/api/tides/station/<station_id>',
                'method': 'GET',
                'parameters': {
                    'days': 'number of days to forecast (1-10, default: 3)'
                },
                'example': '/api/tides/station/8454658?days=3'
            }
        }
    })


@bp.route('/station/<station_id>/debug')
def debug_station(station_id):
    try:
        stations = TideStations()
        stations.fetch_stations()
        station = stations.find_station(station_id)

        if not station:
            return jsonify({
                'error': 'Station not found',
                'station_id': station_id
            }), 404

        # Get the tide URL for debugging
        start_time = datetime.now(pytz.UTC)
        end_time = start_time + timedelta(days=1)
        url = station.create_tide_data_url(
            start_time,
            end_time,
            datum=TideStation.TideDatum.mean_tide_level,
            interval=TideStation.DataInterval.high_low
        )

        return jsonify({
            'station_id': station.station_id,
            'name': station.name,
            'location': {
                'latitude': station.location.latitude,
                'longitude': station.location.longitude
            },
            'tide_url': url
        })

    except Exception as e:
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500