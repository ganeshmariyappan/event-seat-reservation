from datetime import datetime, timezone
from extension import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False)

    seats = db.relationship(
        "Seat",
        backref="event",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Seat(db.Model):
    __tablename__ = "seats"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False
    )
    seat_number = db.Column(db.String(20), nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="AVAILABLE"
   )
class SeatHold(db.Model):
    __tablename__ = "seat_holds"

    id = db.Column(db.Integer, primary_key=True)

    seat_id = db.Column(
        db.Integer,
        db.ForeignKey("seats.id"),
        nullable=False
    )

    user_id = db.Column(db.Integer, nullable=False)

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    seat = db.relationship("Seat", backref="holds")


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False
    )

    seat_id = db.Column(
        db.Integer,
        db.ForeignKey("seats.id"),
        nullable=False,
        unique=True
    )

    user_id = db.Column(db.Integer, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="CONFIRMED"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    seat = db.relationship("Seat", backref="bookings")
