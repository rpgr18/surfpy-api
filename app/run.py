from flask import Flask, jsonify
from flask_cors import CORS
from app.routes import buoy_routes, forecast_routes, tide_routes


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register blueprints
    app.register_blueprint(buoy_routes)
    app.register_blueprint(forecast_routes)
    app.register_blueprint(tide_routes)

    @app.route('/')
    def index():
        # Add this to see all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule))

        return jsonify({
            "message": "Welcome to SurfPy API",
            "registered_routes": routes,
            "available_endpoints": {
                "buoys": "/api/buoys/nearby/<lat>/<lon>",
                "forecast": "/api/forecast/<lat>/<lon>",
                "tides": "/api/tides/<lat>/<lon>"
            }
        })

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)