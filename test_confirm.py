import requests

BASE_URL = "http://127.0.0.1:8000"
EVENT_ID = 1


def test_confirm_own_hold():
    # Use seat 5 for a fresh test
    seat_id = 5
    user_id = 301

    # Hold the seat first
    hold_response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user_id}
    )

    assert hold_response.status_code == 200

    # Confirm the same user's hold
    response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/confirm",
        json={"user_id": user_id}
    )

    print("\nPositive confirm test:", response.status_code)
    print(response.json())

    assert response.status_code == 200


def test_confirm_without_hold():
    # Use another available seat
    seat_id = 6
    user_id = 302

    response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/confirm",
        json={"user_id": user_id}
    )

    print("\nNegative confirm test:", response.status_code)
    print(response.json())

    assert response.status_code in [400, 403, 404, 409]
