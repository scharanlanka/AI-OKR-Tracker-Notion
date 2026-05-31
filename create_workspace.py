import os
import random
import requests
import logging
from time import perf_counter
from contextlib import contextmanager
from datetime import datetime, timedelta
from dotenv import load_dotenv
from faker import Faker

load_dotenv()
fake = Faker()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")

BASE_URL = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


@contextmanager
def timed_step(step_name):
    start = perf_counter()
    logger.info("Starting step: %s", step_name)
    try:
        yield
    finally:
        logger.info("Completed step: %s in %.3fs", step_name, perf_counter() - start)


def request(method, endpoint, payload=None):
    start = perf_counter()
    res = requests.request(
        method,
        f"{BASE_URL}{endpoint}",
        headers=HEADERS,
        json=payload
    )
    logger.info("Notion API %s %s took %.3fs", method, endpoint, perf_counter() - start)

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


def update_database(database_id, properties):
    payload = {"properties": properties}
    db = request("PATCH", f"/databases/{database_id}", payload)
    print(f"Updated database: {database_id}")
    return db


def create_row(database_id, properties):
    payload = {
        "parent": {
            "database_id": database_id
        },
        "properties": properties
    }

    page = request("POST", "/pages", payload)
    print("Inserted row:", page["id"])
    return page["id"]


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
    total_start = perf_counter()
    with timed_step("Create Objectives database"):
        objectives_db_id = create_database("Objectives", objective_db_schema)
    with timed_step("Create Key Results database"):
        key_results_db_id = create_database("Key Results", key_result_db_schema)
    with timed_step("Link Key Results to Objectives relation"):
        update_database(
            key_results_db_id,
            {
                "Objective": {
                    "relation": {
                        "database_id": objectives_db_id,
                        "type": "single_property",
                        "single_property": {}
                    }
                }
            },
        )

    objective_page_ids = {}
    with timed_step("Create objective and key result rows"):
        for obj in objectives:
            obj_start = perf_counter()
            team = random.choice(teams)
            owner = fake.name()
            status = random.choice(statuses)

            page_id = create_row(objectives_db_id, {
                "Objective": title(obj),
                "Team": select(team),
                "Owner": rich_text(owner),
                "Quarter": select("Q2"),
                "Status": select(status),
            })
            objective_page_ids[obj] = page_id

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
                    "Objective": {
                        "relation": [{"id": objective_page_ids[obj]}]
                    },
                })
            logger.info("Finished objective '%s' in %.3fs", obj, perf_counter() - obj_start)

    print("\nDone.")
    print("Objectives DB:", objectives_db_id)
    print("Key Results DB:", key_results_db_id)
    logger.info("Workspace creation total time: %.3fs", perf_counter() - total_start)


if __name__ == "__main__":
    main()
