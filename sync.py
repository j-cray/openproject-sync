import csv
import os
import requests
import json
import base64
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
OPENPROJECT_URL = os.environ.get("OPENPROJECT_URL", "https://openproject.cloud.bitnorth.ca")
API_KEY = os.environ.get("OPENPROJECT_API_KEY")
PROJECT_IDENTIFIER = os.environ.get("OPENPROJECT_PROJECT", "asocial") # Default project identifier
DRY_RUN = "--dry-run" in sys.argv

if not API_KEY:
    print("Error: OPENPROJECT_API_KEY environment variable is not set.")
    exit(1)

# API Headers
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic " + base64.b64encode(f"apikey:{API_KEY}".encode("utf-8")).decode("utf-8")
}

def get_project_href(identifier):
    url = f"{OPENPROJECT_URL}/api/v3/projects/{identifier}"
    if DRY_RUN:
        return f"/api/v3/projects/{identifier}"
    
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["_links"]["self"]["href"]
    else:
        print(f"Error fetching project: {response.status_code} {response.text}")
        exit(1)

def find_work_package(project_href, subject, parent_href=None):
    if DRY_RUN:
        return None 

    filters = [
        {"subject": {"operator": "=", "values": [subject]}},
        {"project": {"operator": "=", "values": [project_href.split("/")[-1]]}} # Filter by project
    ]
    
    params = {"filters": json.dumps(filters)}
    url = f"{OPENPROJECT_URL}/api/v3/work_packages"
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        results = response.json()["_embedded"]["elements"]
        for wp in results:
             # Basic check to see if it's the same task (assumes unique subjects per project roughly)
             if wp["subject"] == subject:
                 return wp["_links"]["self"]["href"]
    return None

def create_work_package(project_href, subject, description, type_name, parent_href=None, estimated_hours=None, priority=None):
    payload = {
        "subject": subject,
        "description": { "format": "markdown", "raw": description or "" },
        "_links": {
            "project": {"href": project_href},
            "type": {"href": f"/api/v3/types/1" if type_name == "Task" else f"/api/v3/types/2"}, # 1=Task, 2=Milestone/Phase (Simplified assumption usually Phase is a milestone or custom type)
            # Find ID logic would be better but hardcoding common defaults for MVP. 
            # Often ID 1 is Task, ID 2,3 etc are others. Let's try to query types dynamically if needed or just use default Task for all and update later.
            # actually better: let's treat "Phase" as a WorkPackage but specific type.
        }
    }

    # Helper for priority/estimate if needed
    if estimated_hours:
         try:
            payload["estimatedTime"] = f"PT{estimated_hours}H"
         except:
            pass

    if parent_href:
        payload["_links"]["parent"] = {"href": parent_href}

    if DRY_RUN:
        print(f"[DRY-RUN] Create '{subject}' (Type: {type_name}) in {project_href} under {parent_href}")
        return "mock-href"

    # NOTE: fetching types first to get correct ID is robust but for this script I'll assume:
    # We need to list types first to map names to IDs.
    # For now, let's just default to 'Task' (usually ID 1) for minimal failure.
    # If Type is 'Phase', we might want to make it a Milestone (ID 2 usually) or Phase.
    
    type_id = 1 # Default Task
    if type_name.lower().startswith("phase"):
        type_id = 2 # Default Milestone often, or just reuse task.

    payload["_links"]["type"]["href"] = f"/api/v3/types/{type_id}"

    url = f"{OPENPROJECT_URL}/api/v3/work_packages"
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code in [200, 201]:
        print(f"Created: {subject}")
        return response.json()["_links"]["self"]["href"]
    else:
        print(f"Failed to create {subject}: {response.status_code} {response.text}")
        return None

def main():
    print(f"Starting Sync (Dry Run: {DRY_RUN})...")
    project_href = get_project_href(PROJECT_IDENTIFIER)
    print(f"Target Project: {project_href}")

    # Read CSV
    tasks = []
    with open("roadmap.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)

    # Processing
    # We need to maintain context of the current 'Phase' parent
    current_phase_href = None

    for task in tasks:
        type_name = task["Type"].strip()
        subject = task["Subject"].strip()
        description = task["Description"].strip()
        est_hours = task["EstHours"].strip()
        # priority = task["Priority"] # Map if needed
        
        if type_name == "Phase":
            # This is a parent container
            existing = find_work_package(project_href, subject)
            if existing:
                print(f"Found existing Phase: {subject}")
                current_phase_href = existing
            else:
                current_phase_href = create_work_package(project_href, subject, description, "Phase")
        else:
            # This is a task, child of current_phase
            existing = find_work_package(project_href, subject, current_phase_href)
            if existing:
                print(f"Found existing Task: {subject}")
            else:
                create_work_package(project_href, subject, description, "Task", parent_href=current_phase_href, estimated_hours=est_hours)

if __name__ == "__main__":
    main()
