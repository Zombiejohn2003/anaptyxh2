from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import Measurement, MeasurementCategory, Sensor, User


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        temperature = MeasurementCategory(code="temperature", name="Temperature", unit="C")
        humidity = MeasurementCategory(code="humidity", name="Humidity", unit="%")
        db.session.add_all([temperature, humidity])

        admin = User(username="admin", full_name="System Administrator", email="admin@example.com", role="admin")
        admin.set_password("admin123")
        user = User(username="user", full_name="Demo User", email="user@example.com", role="user")
        user.set_password("user123")
        db.session.add_all([admin, user])

        sensors = [
            Sensor(
                identifier="LAB-TEMP-01",
                name="Lab Temperature Probe",
                description="Temperature sensor installed in the main laboratory.",
                location="Computer Lab",
                status="active",
                categories=[temperature],
            ),
            Sensor(
                identifier="GREENHOUSE-01",
                name="Greenhouse Climate Sensor",
                description="Combined temperature and humidity sensor for greenhouse monitoring.",
                location="Greenhouse",
                status="active",
                categories=[temperature, humidity],
            ),
            Sensor(
                identifier="SERVER-HUM-01",
                name="Server Room Humidity Sensor",
                description="Humidity probe for the network equipment room.",
                location="Server Room",
                status="maintenance",
                categories=[humidity],
            ),
            Sensor(
                identifier="OFFICE-CLIMATE-02",
                name="Office Climate Sensor",
                description="Combined sensor used for office comfort tracking.",
                location="Administration Office",
                status="active",
                categories=[temperature, humidity],
            ),
        ]
        db.session.add_all(sensors)
        db.session.flush()

        base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(days=3)
        measurements = []
        for index in range(72):
            recorded_at = base_time + timedelta(hours=index)
            measurements.extend(
                [
                    Measurement(
                        sensor=sensors[0],
                        category=temperature,
                        value=Decimal("21.0") + Decimal(index % 8) / Decimal("4"),
                        recorded_at=recorded_at,
                    ),
                    Measurement(
                        sensor=sensors[1],
                        category=temperature,
                        value=Decimal("18.0") + Decimal(index % 12) / Decimal("3"),
                        recorded_at=recorded_at,
                    ),
                    Measurement(
                        sensor=sensors[1],
                        category=humidity,
                        value=Decimal("55.0") + Decimal(index % 10),
                        recorded_at=recorded_at,
                    ),
                    Measurement(
                        sensor=sensors[2],
                        category=humidity,
                        value=Decimal("43.0") + Decimal(index % 6),
                        recorded_at=recorded_at,
                    ),
                    Measurement(
                        sensor=sensors[3],
                        category=temperature,
                        value=Decimal("20.5") + Decimal(index % 6) / Decimal("5"),
                        recorded_at=recorded_at,
                    ),
                    Measurement(
                        sensor=sensors[3],
                        category=humidity,
                        value=Decimal("48.0") + Decimal(index % 7),
                        recorded_at=recorded_at,
                    ),
                ]
            )

        db.session.add_all(measurements)
        db.session.commit()
        print("Seeded PostgreSQL database with demo users, sensors, categories, and measurements.")


if __name__ == "__main__":
    seed()
