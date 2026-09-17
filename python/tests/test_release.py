import requests

BASE_URL = "http://127.0.0.1:8000"
EVENT_ID = 1


def test_release_own_hold():
    seat_id = 7
    user_id = 401

    # First hold the seat
    hold_response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user_id}
    )

    assert hold_response.status_code == 200

    # Release the same user's hold
    response = requests.delete(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user_id}
    )

    print("\nPositive release test:", response.status_code)
    print(response.json())

    assert response.status_code == 200


def test_release_another_users_hold():
    seat_id = 8
    user1 = 402
    user2 = 403

    # User 402 holds the seat
    hold_response = requests.post(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user1}
    )

    assert hold_response.status_code == 200

    # User 403 tries to release User 402's hold
    response = requests.delete(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user2}
    )

    print("\nNegative release test:", response.status_code)
    print(response.json())

    assert response.status_code == 403

    # Cleanup: original owner releases the hold
    requests.delete(
        f"{BASE_URL}/api/events/{EVENT_ID}/seats/{seat_id}/hold",
        json={"user_id": user1}
    )
