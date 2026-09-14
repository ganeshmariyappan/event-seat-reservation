import requests

BASE_URL = "http://127.0.0.1:8000"
EVENT_ID = 1
SEAT_ID = 1


def test_hold_available_seat():
    # Make sure the seat is not currently held
    requests.delete(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{SEAT_ID}/hold"
    )

    response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{SEAT_ID}/hold",
        json={"user_id": 201}
    )

    print("\nPositive test:", response.status_code)
    print(response.json())

    assert response.status_code == 200


def test_hold_already_held_seat():
    # User 202 tries to hold the same seat
    response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{SEAT_ID}/hold",
        json={"user_id": 202}
    )

    print("\nNegative test:", response.status_code)
    print(response.json())

    assert response.status_code == 409
