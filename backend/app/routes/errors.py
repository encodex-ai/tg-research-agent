from flask import Blueprint, jsonify

errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404


@errors_bp.app_errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500
