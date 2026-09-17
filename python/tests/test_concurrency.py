import requests
from concurrent.futures import ThreadPoolExecutor


BASE_URL = "http://127.0.0.1:8000"
EVENT_ID = 1
SEAT_ID = 20


def hold_seat(user_id):
    url = f"{BASE_URL}/api/events/{EVENT_ID}/seats/{SEAT_ID}/hold"

    response = requests.post(
        url,
        json={"user_id": user_id}
    )

    return response.status_code, response.json()


def test_concurrent_hold_same_seat():

    user_ids = list(range(101, 121))

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(
            executor.map(hold_seat, user_ids)
        )

    success_count = sum(
        1 for status, data in results
        if status == 200
    )

    conflict_count = sum(
        1 for status, data in results
        if status == 409
    )

    print("\nResults:")

    for user_id, result in zip(user_ids, results):
        print(user_id, result)

    print(f"\nSuccessful requests: {success_count}")
    print(f"Conflict requests: {conflict_count}")

    assert success_count == 1
    assert conflict_count == 19

