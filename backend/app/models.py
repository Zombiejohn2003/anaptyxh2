from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


# Many-to-many table: one sensor can report multiple measurement categories
# (for example both temperature and humidity).
sensor_categories = db.Table(
    "sensor_categories",
    db.Column("sensor_id", db.Integer, db.ForeignKey("sensors.id", ondelete="CASCADE"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("measurement_categories.id", ondelete="CASCADE"), primary_key=True),
)


# Application accounts. The role field drives what each user can do in the API/UI.
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Categories are database rows so the frontend can load them dynamically in forms.
class MeasurementCategory(db.Model):
    __tablename__ = "measurement_categories"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {"id": self.id, "code": self.code, "name": self.name, "unit": self.unit}


# Sensor metadata. Actual historical readings live in Measurement rows below.
class Sensor(db.Model):
    __tablename__ = "sensors"

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    location = db.Column(db.String(160), nullable=False, default="")
    status = db.Column(db.String(30), nullable=False, default="active")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    categories = db.relationship("MeasurementCategory", secondary=sensor_categories, lazy="joined")
    measurements = db.relationship("Measurement", back_populates="sensor", cascade="all, delete-orphan")

    def to_dict(self, include_metadata=False):
        payload = {
            "id": self.id,
            "identifier": self.identifier,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "status": self.status,
            "categories": [category.to_dict() for category in self.categories],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_metadata:
            latest = sorted(self.measurements, key=lambda item: item.recorded_at, reverse=True)[:5]
            payload["latest_measurements"] = [measurement.to_dict() for measurement in latest]
        return payload


# One recorded reading for one sensor and one category at a specific time.
class Measurement(db.Model):
    __tablename__ = "measurements"

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("measurement_categories.id"), nullable=False, index=True)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    sensor = db.relationship("Sensor", back_populates="measurements")
    category = db.relationship("MeasurementCategory")

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "category": self.category.to_dict() if self.category else None,
            "value": float(self.value),
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
