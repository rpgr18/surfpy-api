from flask import Blueprint, jsonify, request
from surfpy import Location, TideStations
from datetime import datetime, timedelta
import pytz

bp = Blueprint('tides', __name__, url_prefix='/api/tides')


@bp.route('/location')
def get_tides():
    try:
        # Parse coordinates
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        location = Location(lat, lon)

        # Debug print
        print(f"Searching for station near: {lat}, {lon}")

        # Get time range for predictions
        days = int(request.args.get('days', '3'))
        start_time = datetime.now(pytz.UTC)
        end_time = start_time + timedelta(days=days)

        # Initialize stations with debug
        print("Initializing TideStations")
        stations = TideStations()

        print("Fetching stations")
        success = stations.fetch_stations()
        if not success:
            return jsonify({
                'error': 'Failed to fetch tide stations',
                'location': {'latitude': lat, 'longitude': lon}
            }), 500

        print(f"Found {len(stations.stations)} total stations")

        # Find nearest station with debug
        print("Finding closest station")
        station = stations.find_closest_station(location)

        if not station:
            return jsonify({
                'error': 'No tide station found near location',
                'location': {'latitude': lat, 'longitude': lon}
            }), 404

        print(f"Found nearest station: {station.station_id} - {station.name}")

        # Fetch tide data with debug
        print("Fetching tide data")
        result = station.fetch_tide_data(start_time, end_time)

        if result is None:
            return jsonify({
                'error': 'Failed to fetch tide data',
                'station_id': station.station_id,
                'location': {'latitude': lat, 'longitude': lon}
            }), 500

        tide_events, tide_data = result

        # Build response
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
                'end_time': end_time.isoformat()
            },
            'tides': [],
            'predictions': []
        }

        # Add tide events if available
        if tide_events:
            for event in tide_events:
                response['tides'].append({
                    'timestamp': event.date.isoformat(),
                    'type': event.tidal_event,
                    'height': event.water_level,
                    'datum': event.water_level_datum
                })

        # Add predictions if available
        if tide_data:
            for pred in tide_data:
                response['predictions'].append({
                    'timestamp': pred.date.isoformat(),
                    'height': pred.water_level,
                    'datum': pred.water_level_datum
                })

        return jsonify(response)

    except (TypeError, ValueError) as e:
        print(f"Validation error: {str(e)}")
        return jsonify({
            'error': 'Invalid coordinates or parameters',
            'details': str(e)
        }), 400
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'details': str(e)
        }), 500


@bp.route('/station/<station_id>')
def get_station_tides(station_id):
    try:
        days = int(request.args.get('days', '3'))
        start_time = datetime.now(pytz.UTC)
        end_time = start_time + timedelta(days=days)

        stations = TideStations()
        stations.fetch_stations()
        station = stations.find_station(station_id)

        if not station:
            return jsonify({
                'error': 'Station not found',
                'station_id': station_id
            }), 404

        tide_events, tide_data = station.fetch_tide_data(start_time, end_time)

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
                'end_time': end_time.isoformat()
            },
            'tides': [],
            'predictions': []
        }

        if tide_events:
            for event in tide_events:
                response['tides'].append({
                    'timestamp': event.date.isoformat(),
                    'type': event.tidal_event,
                    'height': event.water_level,
                    'datum': event.water_level_datum
                })

        if tide_data:
            for pred in tide_data:
                response['predictions'].append({
                    'timestamp': pred.date.isoformat(),
                    'height': pred.water_level,
                    'datum': pred.water_level_datum
                })

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