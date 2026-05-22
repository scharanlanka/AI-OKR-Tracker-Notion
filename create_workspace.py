import os
import random
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from faker import Faker

load_dotenv()
fake = Faker()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")

BASE_URL = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def request(method, endpoint, payload=None):
    res = requests.request(
        method,
        f"{BASE_URL}{endpoint}",
        headers=HEADERS,
        json=payload
    )

    if not res.ok:
        print("STATUS:", res.status_code)
        print("BODY:", res.text)
        raise Exception("Notion API failed")

    return res.json()


def create_database(name, properties):
    payload = {
        "parent": {
            "type": "page_id",
            "page_id": PARENT_PAGE_ID.replace("-", "")
        },
        "title": [
            {
                "type": "text",
                "text": {"content": name}
            }
        ],
        "properties": properties
    }

    db = request("POST", "/databases", payload)
    print(f"Created database: {name} -> {db['id']}")
    return db["id"]


def create_row(database_id, properties):
    payload = {
        "parent": {
            "database_id": database_id
        },
        "properties": properties
    }

    page = request("POST", "/pages", payload)
    print("Inserted row:", page["id"])


def title(value):
    return {
        "title": [
            {
                "text": {
                    "content": value
                }
            }
        ]
    }


def rich_text(value):
    return {
        "rich_text": [
            {
                "text": {
                    "content": value
                }
            }
        ]
    }


def select(value):
    return {
        "select": {
            "name": value
        }
    }


def number(value):
    return {
        "number": value
    }


def date(value):
    return {
        "date": {
            "start": value.strftime("%Y-%m-%d")
        }
    }


objective_db_schema = {
    "Objective": {"title": {}},
    "Team": {"select": {}},
    "Owner": {"rich_text": {}},
    "Quarter": {"select": {}},
    "Status": {"select": {}},
}

key_result_db_schema = {
    "Key Result": {"title": {}},
    "Team": {"select": {}},
    "Owner": {"rich_text": {}},
    "Progress": {"number": {"format": "percent"}},
    "Due Date": {"date": {}},
    "Status": {"select": {}},
    "Risk": {"select": {}},
    "Blocker": {"rich_text": {}},
    "Last Update": {"date": {}},
}


objectives = [
    "Improve AI assistant reliability",
    "Reduce backend API latency",
    "Launch customer analytics dashboard",
    "Improve onboarding completion rate",
    "Automate weekly leadership reporting",
]

teams = ["AI Team", "Backend Team", "Frontend Team", "Product Team"]
statuses = ["Not Started", "In Progress", "Blocked", "Done"]
risks = ["Low", "Medium", "High", "Delayed"]

blockers = [
    "Waiting on API access",
    "Dependency on design approval",
    "Blocked by missing test data",
    "Delayed due to resource constraints",
    "Waiting for stakeholder review",
    ""
]


def main():
    objectives_db_id = create_database("Objectives", objective_db_schema)
    key_results_db_id = create_database("Key Results", key_result_db_schema)

    for obj in objectives:
        team = random.choice(teams)
        owner = fake.name()
        status = random.choice(statuses)

        create_row(objectives_db_id, {
            "Objective": title(obj),
            "Team": select(team),
            "Owner": rich_text(owner),
            "Quarter": select("Q2"),
            "Status": select(status),
        })

        for i in range(1, 4):
            progress = random.choice([0.10, 0.25, 0.45, 0.60, 0.80, 1.00])
            due_date = datetime.today() + timedelta(days=random.randint(-7, 45))
            last_update = datetime.today() - timedelta(days=random.randint(1, 15))
            blocker = random.choice(blockers)

            create_row(key_results_db_id, {
                "Key Result": title(f"{obj} - KR {i}"),
                "Team": select(team),
                "Owner": rich_text(owner),
                "Progress": number(progress),
                "Due Date": date(due_date),
                "Status": select("Blocked" if blocker else status),
                "Risk": select(random.choice(risks)),
                "Blocker": rich_text(blocker),
                "Last Update": date(last_update),
            })

    print("\nDone.")
    print("Objectives DB:", objectives_db_id)
    print("Key Results DB:", key_results_db_id)


if __name__ == "__main__":
    main()