import json
from datetime import date
from flask import Blueprint, request, jsonify, current_app

from extensions import db
from models import Event, Seat, SeatHold, Booking

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
    from flask import current_app
    
    cache_key = f"availability:event:{event_id}"

    # 1. Check Redis cache
    cached_data = current_app.redis.get(cache_key)

    if cached_data:
        return jsonify(json.loads(cached_data)), 200

    # 2. Get event from PostgreSQL
    event = db.session.get(Event, event_id)

    if not event:
        return jsonify({
            "error": "Event not found"
        }), 404

    # 3. Get seats from PostgreSQL
    seats = Seat.query.filter_by(
        event_id=event_id
    ).all()

    result = []

    # 4. Merge PostgreSQL status + Redis holds
    for seat in seats:

        if seat.status == "BOOKED":
            status = "BOOKED"

        else:
            lock_key = f"seat_lock:{seat.id}"
            holder = current_app.redis.get(lock_key)

            if holder:
                status = "HELD"
            else:
                status = "AVAILABLE"

        result.append({
            "id": seat.id,
            "seat_number": seat.seat_number,
            "status": status
        })

    response = {
        "event_id": event_id,
        "event": event.name,
        "event_date": event.event_date.isoformat(),
        "seats": result
    }

    # 5. Store result in Redis for 30 seconds
    current_app.redis.set(
        cache_key,
        json.dumps(response),
        ex=30
    )

    return jsonify(response), 200    
    event = db.session.get(Event, event_id)

    if not event:
        return jsonify({
            "error": "Event not found"
        }), 404

    seats = Seat.query.filter_by(event_id=event_id).all()

    result = []

    for seat in seats:
        status = seat.status

        # Check Redis for temporary hold
        lock_key = f"seat_lock:{seat.id}"
        holder = current_app.redis.get(lock_key)

        if status == "BOOKED":
            status = "BOOKED"

        elif holder is not None:
            status = "HELD"

        else:
            status = "AVAILABLE"

        result.append({
            "id": seat.id,
            "seat_number": seat.seat_number,
            "status": status
        })

  
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

@api.route("/test-redis", methods=["GET"])
def test_redis():
    from flask import current_app

    current_app.redis.set("test_key", "Redis is working", ex=60)

    value = current_app.redis.get("test_key")

    return jsonify({
        "message": value
    }), 200

@api.route("/events/<int:event_id>/seats/<int:seat_id>/hold", methods=["POST"])
def hold_seat(event_id, seat_id):
    from flask import current_app

    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Check that the event exists
    event = db.session.get(Event, event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check that the seat exists and belongs to this event
    seat = Seat.query.filter_by(
        id=seat_id,
        event_id=event_id
    ).first()

    if not seat:
        return jsonify({"error": "Seat not found"}), 404

    # Check if seat is already permanently booked
    if seat.status == "BOOKED":
        return jsonify({"error": "Seat is already booked"}), 409

    # Redis key for this seat
    lock_key = f"seat_lock:{seat_id}"

    # Try to acquire the lock
    acquired = current_app.redis.set(
        lock_key,
        str(user_id),
        nx=True,
        ex=120
)

    print("DEBUG REDIS URL:", current_app.config["REDIS_URL"])
    print("DEBUG LOCK KEY:", lock_key)
    print("DEBUG ACQUIRED:", acquired)
    print("DEBUG REDIS VALUE:", current_app.redis.get(lock_key))
    print("DEBUG REDIS TTL:", current_app.redis.ttl(lock_key))

    if not acquired:
        current_holder = current_app.redis.get(lock_key)

        return jsonify({
            "error": "Seat is already held",
            "seat_id": seat_id,
            "held_by": current_holder
        }), 409 
  
    current_app.redis.delete(
         f"availability:event:{event_id}"
    )

    return jsonify({
        "message": "Seat held successfully",
        "event_id": event_id,
        "seat_id": seat_id,
        "user_id": user_id,
        "expires_in": 120
    }), 200

@api.route(
    "/events/<int:event_id>/seats/<int:seat_id>/confirm",
    methods=["POST"]
)
def confirm_booking(event_id, seat_id):
    from flask import current_app

    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "error": "user_id is required"
        }), 400

    # Check event
    event = db.session.get(Event, event_id)

    if not event:
        return jsonify({
            "error": "Event not found"
        }), 404

    # Check seat
    seat = Seat.query.filter_by(
        id=seat_id,
        event_id=event_id
    ).first()

    if not seat:
        return jsonify({
            "error": "Seat not found"
        }), 404

    # Redis lock
    lock_key = f"seat_lock:{seat_id}"

    holder = current_app.redis.get(lock_key)

    # Hold does not exist
    if holder is None:
        return jsonify({
            "error": "Seat hold expired or does not exist"
        }), 409

    # Another user owns the hold
    if holder != str(user_id):
        return jsonify({
            "error": "Seat is held by another user"
        }), 409

    # Already booked
    if seat.status == "BOOKED":
        return jsonify({
            "error": "Seat is already booked"
        }), 409

    try:
        # Create booking
        booking = Booking(
            event_id=event_id,
            seat_id=seat_id,
            user_id=user_id,
            status="CONFIRMED"
        )

        db.session.add(booking)

        # Mark seat as booked
        seat.status = "BOOKED"

        db.session.commit()

        # Remove Redis hold
        current_app.redis.delete(lock_key)

        return jsonify({
            "message": "Booking confirmed successfully",
            "booking": {
                "id": booking.id,
                "event_id": event_id,
                "seat_id": seat_id,
                "user_id": user_id,
                "status": booking.status
            }
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "error": "Could not confirm booking"
        }), 500

@api.route(
    "/events/<int:event_id>/seats/<int:seat_id>/hold",
    methods=["DELETE"]
)
def release_hold(event_id, seat_id):
    from flask import current_app

    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "error": "user_id is required"
        }), 400

    # Check event
    event = db.session.get(Event, event_id)

    if not event:
        return jsonify({
            "error": "Event not found"
        }), 404

    # Check seat
    seat = Seat.query.filter_by(
        id=seat_id,
        event_id=event_id
    ).first()

    if not seat:
        return jsonify({
            "error": "Seat not found"
        }), 404

    lock_key = f"seat_lock:{seat_id}"

    # Get current holder
    holder = current_app.redis.get(lock_key)

    if holder is None:
        return jsonify({
            "error": "Seat hold does not exist or has expired"
        }), 409

    # Only the current holder can release it
    if holder != str(user_id):
        return jsonify({
            "error": "You do not own this seat hold"
        }), 403

    # Delete Redis hold
    current_app.redis.delete(lock_key)

    return jsonify({
        "message": "Seat hold released successfully",
        "event_id": event_id,
        "seat_id": seat_id,
        "user_id": user_id
    }), 200

@api.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({
        "status": "healthy"
    }), 200
