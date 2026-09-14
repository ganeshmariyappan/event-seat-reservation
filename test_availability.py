import requests

BASE_URL = "http://127.0.0.1:8000"
EVENT_ID = 1


def get_seats():
    response = requests.get(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats"
    )
    return response


def find_seat(data, seat_id):
    for seat in data["seats"]:
        if seat["id"] == seat_id:
            return seat
    return None


def test_available_seat():
    seat_id = 9

    # Make sure the seat is not held
    requests.delete(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": 501}
    )

    response = get_seats()

    print("\nAvailable seat test:", response.status_code)
    print(find_seat(response.json(), seat_id))

    assert response.status_code == 200
    assert find_seat(response.json(), seat_id)["status"] == "AVAILABLE"


def test_held_seat():
    seat_id = 10
    user_id = 502

    # Hold the seat
    hold_response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user_id}
    )

    assert hold_response.status_code == 200

    # Check availability
    response = get_seats()

    print("\nHeld seat test:", response.status_code)
    print(find_seat(response.json(), seat_id))

    assert response.status_code == 200
    assert find_seat(response.json(), seat_id)["status"] == "HELD"

    # Cleanup
    requests.delete(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user_id}
    )


def test_invalid_event():
    invalid_event_id = 9999

    response = requests.get(
        f"{BASE_URL}/api/events/{invalid_event_id}/seats"
    )

    print("\nNegative invalid event test:", response.status_code)
    print(response.json())

    assert response.status_code == 404
