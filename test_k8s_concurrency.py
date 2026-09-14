import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://192.168.49.2:32488"
EVENT_ID = 1
SEAT_ID = 2


def hold_seat(user_id):
    url = f"{BASE_URL}/api/events/{EVENT_ID}/seats/{SEAT_ID}/hold"

    response = requests.post(
        url,
        json={"user_id": user_id}
    )

    return user_id, response.status_code, response.json()


def test_kubernetes_concurrent_hold():
    user_ids = list(range(201, 221))

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(hold_seat, user_ids))

    success_count = sum(
        1 for _, status, _ in results
        if status == 200
    )

    conflict_count = sum(
        1 for _, status, _ in results
        if status == 409
    )

    print("\nResults:")

    for user_id, status, data in results:
        print(user_id, status, data)

    print(f"\nSuccessful requests: {success_count}")
    print(f"Conflict requests: {conflict_count}")

    assert success_count == 1
    assert conflict_count == 19
