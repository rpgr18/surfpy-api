from flask import Blueprint, jsonify
from surfpy import BuoyStations, Location

bp = Blueprint('buoys', __name__, url_prefix='/api/buoys')


@bp.route('/nearby/<float:lat>/<float:lon>')
def get_nearby_buoys(lat, lon):
    try:
        location = Location(lat, lon)
        stations = BuoyStations()
        stations.fetch_stations()

        nearby = []
        closest_stations = stations.find_closest_stations(location, 5)

        for station in closest_stations:
            nearby.append({
                'id': station.station_id,
                'name': station.name,
                'location': {
                    'latitude': station.location.latitude,
                    'longitude': station.location.longitude
                },
                'active': station.active,
                'type': station.buoy_type
            })

        return jsonify(nearby)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<string:station_id>/current')
def get_buoy_data(station_id):
    try:
        stations = BuoyStations()
        stations.fetch_stations()
        station = stations.find_station(station_id)

        if not station:
            return jsonify({'error': 'Station not found'}), 404

        data = station.fetch_latest_reading()
        if data:
            return jsonify({
                'wave_height': data.wave_summary.wave_height if data.wave_summary else None,
                'wave_period': data.wave_summary.period if data.wave_summary else None,
                'wave_direction': data.wave_summary.direction if data.wave_summary else None,
                'wind_speed': data.wind_speed,
                'wind_direction': data.wind_direction
            })
        else:
            return jsonify({'error': 'No data available'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500