from flask import Blueprint, jsonify, request
from surfpy import Location, BuoyStations, us_west_coast_gfs_wave_model, atlantic_gfs_wave_model
from datetime import datetime, timedelta
import pytz

bp = Blueprint('forecast', __name__, url_prefix='/api/forecast')


@bp.route('/<float:lat>/<float:lon>')
def get_forecast(lat, lon):
    try:
        location = Location(lat, lon)

        # Determine which model to use based on location
        if 210 <= location.absolute_longitude <= 250 and 25 <= location.latitude <= 50:
            model = us_west_coast_gfs_wave_model()
        else:
            model = atlantic_gfs_wave_model()

        # Get time range for forecast
        days = int(request.args.get('days', '3'))
        current_time = datetime.now(pytz.UTC)
        end_time = current_time + timedelta(days=days)

        # Fetch and process forecast data
        start_index = model.time_index(current_time)
        end_index = model.time_index(end_time)

        raw_data = model.fetch_grib_datas(int(start_index), int(end_index))
        processed_data = model.parse_grib_datas(location, raw_data)
        buoy_data = model.to_buoy_data(processed_data)

        # Format response
        forecasts = []
        for data in buoy_data:
            forecast = {
                'timestamp': data.date.isoformat(),
                'wave_summary': {
                    'height': data.wave_summary.wave_height if data.wave_summary else None,
                    'period': data.wave_summary.period if data.wave_summary else None,
                    'direction': data.wave_summary.direction if data.wave_summary else None,
                    'compass_direction': data.wave_summary.compass_direction if data.wave_summary else None
                },
                'wind': {
                    'speed': data.wind_speed,
                    'direction': data.wind_direction,
                    'compass_direction': data.wind_compass_direction
                },
                'swells': []
            }

            for swell in data.swell_components:
                forecast['swells'].append({
                    'height': swell.wave_height,
                    'period': swell.period,
                    'direction': swell.direction,
                    'compass_direction': swell.compass_direction
                })

            forecasts.append(forecast)

        return jsonify(forecasts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/buoy/<string:station_id>')
def get_buoy_forecast(station_id):
    try:
        stations = BuoyStations()
        stations.fetch_stations()
        station = stations.find_station(station_id)

        if not station:
            return jsonify({'error': 'Station not found'}), 404

        data = station.fetch_detailed_wave_reading(20)  # Get 20 most recent readings

        if not data:
            return jsonify({'error': 'No data available'}), 404

        forecasts = []
        for reading in data:
            forecast = {
                'timestamp': reading.date.isoformat(),
                'wave_summary': {
                    'height': reading.wave_summary.wave_height if reading.wave_summary else None,
                    'period': reading.wave_summary.period if reading.wave_summary else None,
                    'direction': reading.wave_summary.direction if reading.wave_summary else None,
                    'compass_direction': reading.wave_summary.compass_direction if reading.wave_summary else None
                },
                'swells': []
            }

            for swell in reading.swell_components:
                forecast['swells'].append({
                    'height': swell.wave_height,
                    'period': swell.period,
                    'direction': swell.direction,
                    'compass_direction': swell.compass_direction
                })

            forecasts.append(forecast)

        return jsonify(forecasts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500