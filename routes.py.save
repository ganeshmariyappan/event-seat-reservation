from datetime import date
from flask import Blueprint, request, jsonify

from extension import db
from models import Event, Seat, SeatHold


api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    name = data.get("name")
    venue = data.get("venue")
    event_date = data.get("event_date")
    seat_rows = data.get("seat_rows")
    seats_per_row = data.get("seats_per_row")

    if not name or not venue or not event_date or not seat_rows or not seats_per_row:
        return jsonify({
            "error": "name, venue, event_date, seat_rows and seats_per_row are required"
        }), 400

    if seat_rows <= 0 or seats_per_row <= 0:
        return jsonify({
            "error": "seat_rows and seats_per_row must be greater than 0"
        }), 400

    try:
        event_date = date.fromisoformat(event_date)
    except ValueError:
        return jsonify({
            "error": "event_date must be in YYYY-MM-DD format"
        }), 400

    event = Event(
        name=name,
        venue=venue,
        event_date=event_date
    )

    db.session.add(event)
    db.session.flush()

    created_seats = []

    for row in range(seat_rows):
        row_letter = chr(ord("A") + row)

        for number in range(1, seats_per_row + 1):
            seat_number = f"{row_letter}{number}"

            seat = Seat(
                event_id=event.id,
                seat_number=seat_number,
                status="AVAILABLE"
            )

            db.session.add(seat)
            created_seats.append(seat_number)

    db.session.commit()

    return jsonify({
        "message": "Event created successfully",
        "event": {
            "id": event.id,
            "name": event.name,
            "venue": event.venue,
            "event_date": event.event_date.isoformat(),
            "total_seats": len(created_seats),
            "seats": created_seats
        }

    }), 201

@api.route("/events", methods=["GET"])
def get_events():
    events = Event.query.all()

    return jsonify({
        "events": [
            {
                "id": event.id,
           

     "name": event.name,
                "venue": event.venue,
                "event_date": event.event_date.isoformat(),
                "total_seats": len(event.seats)
            }
            for event in events
        ]
    }), 200

@api.route("/events/<int:event_id>/seats", methods=["GET"])
def get_seats(event_id):
    event = db.session.get(Event, event_id)

    if not event:
        return jsonify({
            "error": "Event not found"
        }), 404

    seats = Seat.query.filter_by(event_id=event_id).all()

    return jsonify({
        "event_id": event_id,
        "event": event.name,
        "event_date": event.event_date.isoformat(),
        "seats": [
            {
                "id": seat.id,
                "seat_number": seat.seat_number,
                "status": seat.status
            }
            for seat in seats
        ]
    }), 200
