# Event Seat Reservation System

A REST API-based event seat reservation system built using **Flask, PostgreSQL, Redis, Docker, Kubernetes, and Pytest**.

The system allows users to:

* Create and view events
* View seat availability
* Temporarily hold a seat
* Confirm a booking
* Release a seat hold
* Automatically expire an unconfirmed hold using Redis TTL
* Prevent two users from holding the same seat simultaneously

## Tech Stack

* Python 3.12
* Flask
* Flask-SQLAlchemy
* Flask-Migrate
* PostgreSQL
* Redis
* Pytest
* Docker
* Kubernetes

## Architecture

```text
                Client
                  |
                  | REST API / JSON
                  v
             Flask API
              /      \
             /        \
            v          v
         Redis      PostgreSQL
          |              |
      Seat Holds      Events
      TTL / Locks     Seats
      Cache           Bookings
```

Redis is used for temporary seat locks and TTL-based hold expiry. PostgreSQL is the permanent source of truth for events, seats, and confirmed bookings.

---

# 1. Clone the Repository

```bash
git clone https://github.com/ganeshmariyappan/event-seat-reservation
cd "event seat reservation"
```

---

# 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 3. Configure PostgreSQL

Create the PostgreSQL database and user required by the application.

Example:

```text
Database: seat_reservation
User: seatapp
```

Configure the database connection in your environment configuration.

Example:

```text
DATABASE_URL=postgresql://seatapp:password@localhost:5432/seat_reservation
REDIS_URL=redis://localhost:6379/0
```

Do not commit passwords or `.env` files to GitHub.

Use `.env.example` for configuration documentation.

---

# 4. Run Database Migration

Activate the virtual environment and run:

```bash
flask --app run.py db upgrade
```

This creates the required database tables.

---

# 5. Start Redis

Verify Redis is running:

```bash
redis-cli ping
```

Expected:

```text
PONG
```

You can also check Redis keys:

```bash
redis-cli keys '*'
```

---

# 6. Start the Flask API

Run:

```bash
flask --app run.py run --host=0.0.0.0 --port=8000
```

The API will be available at:

```text
http://localhost:8000
```

For a VM, use the VM IP:

```text
http://<VM-IP>:8000
```

---

# API Documentation

## API Base URL

```text
http://localhost:8000/api
```

---

## 1. Health Check

### Request

```http
GET /healthz
```

### Example

```bash
curl http://localhost:8000/healthz
```

Use this endpoint to verify that the application and its dependencies are working.

---

# 2. Create an Event

### Request

```http
POST /api/events
```

### Example

```bash
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rock Concert",
    "venue": "Chennai Stadium",
    "event_date": "2026-09-20",
    "seat_count": 50
  }'
```

### Example Response

```json
{
  "id": 1,
  "name": "Rock Concert",
  "venue": "Chennai Stadium",
  "event_date": "2026-09-20",
  "seat_count": 50
}
```

Save the returned event ID because it is required by the seat APIs.

---

# 3. Get All Events

### Request

```http
GET /api/events
```

### Example

```bash
curl http://localhost:8000/api/events
```

### Example Response

```json
[
  {
    "id": 1,
    "name": "Rock Concert",
    "venue": "Chennai Stadium",
    "event_date": "2026-09-20"
  }
]
```

---

# 4. Get Event Seat Availability

### Request

```http
GET /api/events/<event_id>/seats
```

### Example

```bash
curl http://localhost:8000/api/events/1/seats
```

### Example Response

```json
[
  {
    "id": 1,
    "seat_number": "A1",
    "status": "available"
  },
  {
    "id": 2,
    "seat_number": "A2",
    "status": "booked"
  },
  {
    "id": 3,
    "seat_number": "A3",
    "status": "held"
  }
]
```

Possible seat statuses:

```text
available
held
booked
```

---

# 5. Hold a Seat

A user can temporarily hold a seat before confirming the booking.

### Request

```http
POST /api/events/<event_id>/seats/<seat_id>/hold
```

### Example

```bash
curl -X POST http://localhost:8000/api/events/1/seats/1/hold \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 101
  }'
```

### Successful Response

```json
{
  "status": "held",
  "user_id": 101,
  "seat_id": 1,
  "expires_in": 120
}
```

The seat is temporarily locked in Redis.

The lock uses Redis `SET NX EX`, meaning the lock is created only if it does not already exist and automatically expires after the configured TTL.

---

# 6. Try to Hold the Same Seat

If another user tries to hold the same seat:

```bash
curl -X POST http://localhost:8000/api/events/1/seats/1/hold \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 102
  }'
```

The API should return:

```text
409 Conflict
```

Example:

```json
{
  "error": "Seat already held"
}
```

This demonstrates that two users cannot successfully hold the same seat at the same time.

---

# 7. Check Redis Hold and TTL

After holding a seat:

```bash
redis-cli
```

Check the lock:

```redis
GET seat_lock:1
```

Example:

```text
"101"
```

Check the remaining TTL:

```redis
TTL seat_lock:1
```

Example:

```text
115
```

The TTL decreases with time.

After the TTL reaches zero, Redis automatically removes the key:

```redis
GET seat_lock:1
```

Result:

```text
(nil)
```

The seat can then be held by another user.

---

# 8. Confirm a Booking

The user who owns the hold can confirm the booking.

### Request

```http
POST /api/events/<event_id>/seats/<seat_id>/confirm
```

### Example

```bash
curl -X POST http://localhost:8000/api/events/1/seats/1/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 101
  }'
```

### Example Response

```json
{
  "status": "confirmed",
  "booking_id": 1,
  "event_id": 1,
  "seat_id": 1,
  "user_id": 101
}
```

After confirmation:

* The booking is stored in PostgreSQL.
* The seat becomes permanently booked.
* The Redis temporary hold is removed.

---

# 9. Release a Seat Hold

A user can cancel their hold before confirmation.

### Request

```http
DELETE /api/events/<event_id>/seats/<seat_id>/hold
```

### Example

```bash
curl -X DELETE http://localhost:8000/api/events/1/seats/1/hold \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 101
  }'
```

After successful release, the Redis lock is deleted and the seat becomes available again.

---

# 10. Complete API Flow

The normal reservation flow is:

```text
1. Create Event
       |
       v
2. Get Event Seats
       |
       v
3. Hold Seat
       |
       +------> Hold expires after TTL
       |             |
       |             v
       |        Seat Available
       |
       v
4. Confirm Booking
       |
       v
5. Booking Stored in PostgreSQL
       |
       v
6. Seat = BOOKED
```

Alternative flow:

```text
Hold Seat
    |
    v
Release Hold
    |
    v
Seat = AVAILABLE
```

---

# 11. Verify PostgreSQL Data

Connect to PostgreSQL:

```bash
psql -U seatapp -d seat_reservation
```

List tables:

```sql
\dt
```

Check events:

```sql
SELECT * FROM events;
```

Check seats:

```sql
SELECT * FROM seats;
```

Check bookings:

```sql
SELECT * FROM bookings;
```

Check seat holds:

```sql
SELECT * FROM seat_holds;
```

A confirmed booking should be stored in the `bookings` table.

---

# 12. Run Tests

Run all tests:

```bash
pytest -v
```

Example:

```text
test_availability.py
test_concurrency.py
test_confirm.py
test_release.py
```

The concurrency test verifies that when multiple users try to hold the same seat simultaneously, exactly one request succeeds and the others receive `409 Conflict`.

The project requirement specifically includes a concurrency test for simultaneous holds on the same seat.

---

# 13. Run the Concurrency Test

Example:

```bash
pytest -v tests/test_concurrency.py
```

Expected behavior:

```text
1 request  -> SUCCESS
Other requests -> 409 Conflict
```

This proves that the seat-locking mechanism prevents double booking.

---

# 14. Docker

Build the application image:

```bash
docker build -t seat-reservation-app .
```

Run the container:

```bash
docker run -d \
  --name seat-test \
  -p 8000:8000 \
  seat-reservation-app
```

Check the container:

```bash
docker ps
```

View logs:

```bash
docker logs seat-test
```

---

# 15. Kubernetes

The project can also be deployed to Kubernetes with separate components for:

```text
Flask Application
       |
       +---- Redis
       |
       +---- PostgreSQL
```

Kubernetes configuration should contain:

* Flask Deployment
* Flask Service
* PostgreSQL Deployment/StatefulSet
* PostgreSQL Service
* Redis Deployment
* Redis Service
* ConfigMap
* Secret
* Health probes

The application is designed to use Redis for distributed seat locking and PostgreSQL as the persistent source of truth.

---

# HTTP Status Codes

| Status Code | Meaning                                      |
| ----------- | -------------------------------------------- |
| 200         | Request successful                           |
| 201         | Resource created                             |
| 400         | Invalid request                              |
| 404         | Event or seat not found                      |
| 409         | Seat already held/booked or booking conflict |
| 500         | Internal server error                        |

---

# Important Notes

* Do not commit `.env` files or passwords to GitHub.
* Redis is responsible for temporary seat holds.
* PostgreSQL stores permanent booking information.
* A seat hold automatically expires when its Redis TTL reaches zero.
* A confirmed booking remains stored in PostgreSQL.
* The Redis lock prevents simultaneous users from successfully holding the same seat.
* PostgreSQL constraints provide an additional safety layer during confirmation.

## Project Goal

The main goal of this project is to demonstrate a real-world reservation system with **REST APIs, PostgreSQL persistence, Redis distributed locking, automatic TTL-based hold expiry, concurrency handling, automated testing, Docker containerization, and Kubernetes deployment**.
expiry, concurrency handling, automated testing, Docker containerization, and Kubernetes deployment.
