from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, current_app, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Measurement, MeasurementCategory, Sensor, User, sensor_categories


api = Blueprint("api", __name__)

VALID_ROLES = {"user", "admin"}
VALID_SENSOR_STATUSES = {"active", "inactive", "maintenance"}
VALID_RESOLUTIONS = {"hour", "day", "month"}


def current_user():
    identity = get_jwt_identity()
    if identity is None:
        return None
    try:
        return db.session.get(User, int(identity))
    except (TypeError, ValueError):
        return None


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user.role != "admin" or not user.is_active:
            return {"message": "Administrator privileges are required."}, 403
        return fn(*args, **kwargs)

    return wrapper


def parse_datetime(value):
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def get_categories_from_payload(payload):
    category_ids = payload.get("category_ids") or []
    category_codes = payload.get("category_codes") or []

    query = MeasurementCategory.query
    categories = []
    if category_ids:
        categories.extend(query.filter(MeasurementCategory.id.in_(category_ids)).all())
    if category_codes:
        categories.extend(query.filter(MeasurementCategory.code.in_(category_codes)).all())

    unique_categories = {category.id: category for category in categories}.values()
    return list(unique_categories)


def sensor_from_payload(sensor, payload):
    for field in ["identifier", "name", "description", "location", "status"]:
        if field in payload:
            setattr(sensor, field, payload[field])

    if not sensor.status:
        sensor.status = "active"

    if sensor.status not in VALID_SENSOR_STATUSES:
        raise ValueError("Sensor status must be active, inactive, or maintenance.")

    if "category_ids" in payload or "category_codes" in payload:
        categories = get_categories_from_payload(payload)
        if not categories:
            raise ValueError("At least one valid measurement category is required.")
        sensor.categories = categories
    elif not sensor.categories:
        raise ValueError("At least one measurement category is required.")

    return sensor


@api.errorhandler(IntegrityError)
def handle_integrity_error(error):
    db.session.rollback()
    return {"message": "A record with the same unique field already exists."}, 409


@api.errorhandler(ValueError)
def handle_value_error(error):
    db.session.rollback()
    return {"message": str(error)}, 400


@api.post("/auth/login")
def login():
    payload = request.get_json() or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password) or not user.is_active:
        return {"message": "Invalid username or password."}, 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return {"access_token": token, "user": user.to_dict()}


@api.get("/auth/me")
@jwt_required()
def me():
    user = current_user()
    if not user or not user.is_active:
        return {"message": "User is not active."}, 401
    return {"user": user.to_dict()}


@api.get("/categories")
@jwt_required()
def categories():
    return {"categories": [category.to_dict() for category in MeasurementCategory.query.order_by(MeasurementCategory.name).all()]}


@api.get("/dashboard")
@jwt_required()
def dashboard():
    sensors = Sensor.query.order_by(Sensor.identifier).all()
    active_count = sum(1 for sensor in sensors if sensor.status == "active")

    average_rows = (
        db.session.query(MeasurementCategory.code, func.avg(Measurement.value))
        .join(Measurement, Measurement.category_id == MeasurementCategory.id)
        .group_by(MeasurementCategory.code)
        .all()
    )
    averages = {code: round(float(average), 2) for code, average in average_rows}

    type_rows = (
        db.session.query(MeasurementCategory.name, func.count(sensor_categories.c.sensor_id))
        .join(sensor_categories, sensor_categories.c.category_id == MeasurementCategory.id)
        .group_by(MeasurementCategory.name)
        .order_by(MeasurementCategory.name)
        .all()
    )

    status_rows = db.session.query(Sensor.status, func.count(Sensor.id)).group_by(Sensor.status).all()

    latest_rows = (
        Measurement.query.join(Measurement.category)
        .join(Measurement.sensor)
        .order_by(Measurement.recorded_at.desc())
        .limit(12)
        .all()
    )

    payload = {
        "summary": {
            "total_sensors": len(sensors),
            "active_sensors": active_count,
            "average_temperature": averages.get("temperature"),
            "average_humidity": averages.get("humidity"),
        },
        "sensor_type_distribution": [{"name": name, "value": count} for name, count in type_rows],
        "sensor_status_distribution": [{"name": status, "value": count} for status, count in status_rows],
        "latest_measurements": [
            {
                "sensor": measurement.sensor.identifier,
                "category": measurement.category.name,
                "value": float(measurement.value),
                "unit": measurement.category.unit,
                "recorded_at": measurement.recorded_at.isoformat(),
            }
            for measurement in latest_rows
        ],
        "sensors": [sensor.to_dict() for sensor in sensors],
    }

    user = current_user()
    if user and user.role == "admin":
        payload["users"] = [item.to_dict() for item in User.query.order_by(User.username).all()]

    return payload


@api.get("/sensors")
@jwt_required()
def list_sensors():
    sensors = Sensor.query.order_by(Sensor.identifier).all()
    return {"sensors": [sensor.to_dict() for sensor in sensors]}


@api.post("/sensors")
@admin_required
def create_sensor():
    payload = request.get_json() or {}
    if not payload.get("identifier") or not payload.get("name"):
        return {"message": "Sensor identifier and name are required."}, 400

    sensor = sensor_from_payload(Sensor(), payload)
    db.session.add(sensor)
    db.session.commit()
    return {"sensor": sensor.to_dict()}, 201


@api.get("/sensors/<int:sensor_id>")
@jwt_required()
def sensor_detail(sensor_id):
    sensor = db.session.get(Sensor, sensor_id)
    if not sensor:
        return {"message": "Sensor not found."}, 404
    return {"sensor": sensor.to_dict(include_metadata=True)}


@api.put("/sensors/<int:sensor_id>")
@admin_required
def update_sensor(sensor_id):
    sensor = db.session.get(Sensor, sensor_id)
    if not sensor:
        return {"message": "Sensor not found."}, 404

    sensor_from_payload(sensor, request.get_json() or {})
    db.session.commit()
    return {"sensor": sensor.to_dict()}


@api.delete("/sensors/<int:sensor_id>")
@admin_required
def delete_sensor(sensor_id):
    sensor = db.session.get(Sensor, sensor_id)
    if not sensor:
        return {"message": "Sensor not found."}, 404
    db.session.delete(sensor)
    db.session.commit()
    return {"message": "Sensor deleted."}


@api.get("/sensors/<int:sensor_id>/measurements")
@jwt_required()
def sensor_measurements(sensor_id):
    sensor = db.session.get(Sensor, sensor_id)
    if not sensor:
        return {"message": "Sensor not found."}, 404

    resolution = request.args.get("resolution", "hour")
    if resolution not in VALID_RESOLUTIONS:
        return {"message": "Resolution must be hour, day, or month."}, 400

    bucket = func.date_trunc(resolution, Measurement.recorded_at).label("period")
    rows = (
        db.session.query(bucket, MeasurementCategory.code, MeasurementCategory.unit, func.avg(Measurement.value).label("average"))
        .join(MeasurementCategory, Measurement.category_id == MeasurementCategory.id)
        .filter(Measurement.sensor_id == sensor_id)
        .group_by(bucket, MeasurementCategory.code, MeasurementCategory.unit)
        .order_by(bucket)
        .all()
    )

    return {
        "resolution": resolution,
        "measurements": [
            {
                "period": period.isoformat(),
                "category": code,
                "unit": unit,
                "average": round(float(average), 2),
            }
            for period, code, unit, average in rows
        ],
    }


@api.post("/measurements/ingest")
def ingest_measurement():
    api_key = request.headers.get("X-API-Key")
    if api_key != current_app.config["INGEST_API_KEY"]:
        return {"message": "Invalid ingestion API key."}, 401

    payload = request.get_json() or {}
    sensor = db.session.get(Sensor, payload.get("sensor_id")) if payload.get("sensor_id") else None
    if not sensor and payload.get("sensor_identifier"):
        sensor = Sensor.query.filter_by(identifier=payload["sensor_identifier"]).first()
    if not sensor:
        return {"message": "Sensor not found."}, 404

    category = db.session.get(MeasurementCategory, payload.get("category_id")) if payload.get("category_id") else None
    if not category and payload.get("category_code"):
        category = MeasurementCategory.query.filter_by(code=payload["category_code"]).first()
    if not category or category not in sensor.categories:
        return {"message": "Category is not enabled for this sensor."}, 400
    if "value" not in payload:
        return {"message": "Measurement value is required."}, 400

    measurement = Measurement(
        sensor=sensor,
        category=category,
        value=payload["value"],
        recorded_at=parse_datetime(payload.get("recorded_at")),
    )
    db.session.add(measurement)
    db.session.commit()
    return {"measurement": measurement.to_dict()}, 201


@api.get("/users")
@admin_required
def list_users():
    return {"users": [user.to_dict() for user in User.query.order_by(User.username).all()]}


@api.post("/users")
@admin_required
def create_user():
    payload = request.get_json() or {}
    required_fields = ["username", "password", "full_name", "email", "role"]
    if any(not payload.get(field) for field in required_fields):
        return {"message": "Username, password, full name, email, and role are required."}, 400
    if payload["role"] not in VALID_ROLES:
        return {"message": "Role must be user or admin."}, 400

    user = User(
        username=payload["username"],
        full_name=payload["full_name"],
        email=payload["email"],
        role=payload["role"],
        is_active=payload.get("is_active", True),
    )
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()
    return {"user": user.to_dict()}, 201


@api.put("/users/<int:user_id>")
@admin_required
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"message": "User not found."}, 404

    payload = request.get_json() or {}
    for field in ["username", "full_name", "email", "role", "is_active"]:
        if field in payload:
            setattr(user, field, payload[field])
    if user.role not in VALID_ROLES:
        return {"message": "Role must be user or admin."}, 400
    if payload.get("password"):
        user.set_password(payload["password"])

    db.session.commit()
    return {"user": user.to_dict()}


@api.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"message": "User not found."}, 404

    if user.role == "admin" and User.query.filter_by(role="admin", is_active=True).count() <= 1:
        return {"message": "Cannot delete the last active administrator."}, 400

    db.session.delete(user)
    db.session.commit()
    return {"message": "User deleted."}
