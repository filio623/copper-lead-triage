from backend.app.core.config import get_settings
import os
import httpx
from pprint import pprint
import time

settings = get_settings()

COPPER_API = settings.copper_api_key

EMAIL = settings.copper_email

all_count = 0
page = 1

headers = {
    "X-PW-AccessToken": COPPER_API,
    "X-PW-Application": "developer_api",
    "X-PW-UserEmail": EMAIL,
    "Content-Type": "application/json",
}

start_time = time.time()
end_time = None

first_date = None
last_date = None

while True:

    params = {
    "page_size": 200,
    "page_number": page,
    "sort_by": "date_modified",
    "sort_direction": "desc"
    }

    
    response = httpx.post("https://api.copper.com/developer_api/v1/leads/search", headers=headers, params=params)

    count = len(response.json())

    if page == 1:
        first_date = response.json()[0]['date_created']

    all_count += count

    print(f"Page {page} has {count} leads. Total so far: {all_count}")

    print(f"First id is {response.json()[0]['id']}")

    if count < 200:
        end_time = time.time()
        last_date = response.json()[-1]['date_created']
        break

    page += 1
    break

print(f"Total leads: {all_count}")
print(f"First date: {first_date}")
print(f"Last date: {last_date}")

if end_time is not None:
    print(f"Execution time: {end_time - start_time} seconds")



