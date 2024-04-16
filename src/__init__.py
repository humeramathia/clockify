import json
import os
from urllib.parse import unquote, quote
import requests
import tina4_python
from tina4_python import Debug
from tina4_python.Request import Request
from tina4_python.Router import get, post, put, delete
from tina4_python.Response import Response
from tina4_python.Template import Template
import firebase_admin
from firebase_admin import credentials, firestore

# Clockify API key, workspace ID, and endpoint
CLOCKIFY_API_KEY = 'Nzc4OGM3ZWMtOTU4Zi00ZTZjLTkzZTctNTg2NzEyN2IwODcx'
CLOCKIFY_WORKSPACE_ID = '62bc487c45169565cb1581ec'
CLOCKIFY_ENDPOINT = 'https://api.clockify.me/api/v1'
firebase_private_key = os.getenv('FIREBASE_PRIVATE_KEY')

# firestore project's private key JSON file
cred_path = 'src/secrets/firebase-private-key.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()







# Utility function to find project ID by name
def get_project_id_by_name(project_name, projects):
    for project in projects:
        if project["name"].lower() == project_name.lower():
            return project["id"]
    return None


def fetch_project_id(project_name):
    project_name = unquote(project_name)
    url = f"{CLOCKIFY_ENDPOINT}/workspaces/{CLOCKIFY_WORKSPACE_ID}/projects"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}
    response = requests.get(url, headers=headers)
    if response.ok:
        projects = response.json()
        for project in projects:
            if project["name"].lower() == project_name.lower():
                return project["id"]
    else:
        Debug(f"Error fetching projects: {response.text}")
    return None


# Utility function to find user ID by name
def fetch_user_id(user_name):
    user_name = unquote(user_name)
    url = f"{CLOCKIFY_ENDPOINT}/workspaces/{CLOCKIFY_WORKSPACE_ID}/users"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}
    response = requests.get(url, headers=headers)
    if response.ok:
        users = response.json()
        for user in users:
            if user["name"].lower() == user_name.lower():
                return user["id"]
    else:
        Debug(f"Error fetching users: {response.text}")
    return None


def fetch_task_id(task_name, project_id):
    task_name = unquote(task_name)
    url = f"{CLOCKIFY_ENDPOINT}/workspaces/{CLOCKIFY_WORKSPACE_ID}/projects/{project_id}/tasks"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}
    response = requests.get(url, headers=headers)
    if response.ok:
        tasks = response.json()
        for task in tasks:
            if task["name"].lower() == task_name.lower():
                return task["id"]
    else:
        Debug(f"Error fetching tasks: {response.text}")
    return None


# Get all project names
@get("/clockify/projects/names")
async def get_project_names(**params):
    url = f"{CLOCKIFY_ENDPOINT}/workspaces/{CLOCKIFY_WORKSPACE_ID}/projects"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}
    response = requests.get(url, headers=headers)
    if response.ok:
        projects = response.json()
        project_names = [project["name"] for project in projects]
        return Response(json.dumps(project_names), 200, "application/json")
    else:
        return Response(json.dumps({"error": "Failed to fetch projects"}), response.status_code, "application/json")


# Get tasks for a project by name
@get("/clockify/projects/{project_name}/tasks")
async def get_tasks_for_project(request: Request, **params):
    # Correctly use decoded_project_name after decoding it from request params
    project_name = unquote(request.params['project_name'])

    projects_response = requests.get(f"{CLOCKIFY_ENDPOINT}/workspaces/{CLOCKIFY_WORKSPACE_ID}/projects",
                                     headers={"X-Api-Key": CLOCKIFY_API_KEY})
    if not projects_response.ok:
        return Response(json.dumps({"error": "Failed to fetch projects"}), projects_response.status_code,
                        "application/json")

    projects = projects_response.json()
    # Use decoded_project_name here
    project_id = get_project_id_by_name(project_name, projects)
    if not project_id:
        return Response(json.dumps({"error": "Project not found"}), 404, "application/json")

    tasks_url = f"{CLOCKIFY_ENDPOINT}/workspaces/{CLOCKIFY_WORKSPACE_ID}/projects/{project_id}/tasks"
    tasks_response = requests.get(tasks_url, headers={"X-Api-Key": CLOCKIFY_API_KEY})
    if tasks_response.ok:
        tasks = tasks_response.json()
        task_names = [task["name"] for task in tasks]
        return Response(json.dumps(task_names), 200, "application/json")
    else:
        return Response(json.dumps({"error": "Failed to fetch tasks for project"}), tasks_response.status_code,
                        "application/json")


# Get all users in the workspace
@get("/clockify/users")
async def get_users(**params):
    url = f"{CLOCKIFY_ENDPOINT}/workspaces/{CLOCKIFY_WORKSPACE_ID}/users"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}
    response = requests.get(url, headers=headers)
    if response.ok:
        users = response.json()
        user_names = [user["name"] for user in users]
        return Response(json.dumps(user_names), 200, "application/json")
    else:
        return Response(json.dumps({"error": "Failed to fetch users"}), response.status_code, "application/json")


# get router which renders the twig form html
@get("/capture")
async def capture_get(request, response):
    # get a token to add to the form
    token = tina4_python.tina4_auth.get_token({"data": {"formName": "capture"}})
    html = Template.render_twig_template("index.twig", {"token": token})
    return response(html)


# returns back to the user the form data that has been posted and sends to firestore
@post("/capture")
async def capture_post(request, response):
    try:
        data = request.body
        # Add data to the 'posts' collection in Firestore
        doc_ref = db.collection('posts').document()
        doc_ref.set(data)

        return response(request.body)
    except Exception as e:
        print(f"Error handling request: {e}")
        return Response("Error handling request", 500)


# Get all data from Firestore
@get("/data")
async def get_data(request, response):
    db = firestore.client()
    # Fetch data from Firestore
    docs = db.collection('posts').get()
    data = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return Response(json.dumps(data), content_type="application/json")


# Update data in Firestore
@put("/update-data")  # Update data in Firestore
async def update_data(request, **params):
    try:
        # Parse the request body to JSON
        payload = request.body
        document_id = payload['id']
        update_fields = payload['data']
        print('Payload:', payload)


        # Check if both the document ID and the update fields are provided
        if not document_id or not update_fields:
            return Response(json.dumps({"error": "Missing document ID or update data"}), 400, "application/json")

        # Reference to the document to be updated
        doc_ref = db.collection('posts').document(document_id)

        # Update the document
        doc_ref.update(update_fields)
        print('Updated document')

        return Response(json.dumps({"success": "Data updated successfully"}), 200, "application/json")
    except Exception as e:
        # Log the exception
        print(f"Error updating document: {e}")
        return Response(json.dumps({"error": "Error updating document"}), 500, "application/json")


@delete("/delete-data")  # Delete data in Firestore
async def delete_data(request, **params):
    try:
        # Parse the request body to JSON
        payload = request.body
        document_id = payload['id']

        # Check if the document ID is provided
        if not document_id:
            return Response(json.dumps({"error": "Missing document ID"}), 400, "application/json")

        # Reference to the document to be deleted
        doc_ref = db.collection('posts').document(document_id)

        # Delete the document
        doc_ref.delete()
        print('Deleted document')

        return Response(json.dumps({"success": "Data deleted successfully"}), 200, "application/json")
    except Exception as e:
        # Log the exception
        print(f"Error deleting document: {e}")
        return Response(json.dumps({"error": "Error deleting document"}), 500, "application/json")

@put("/update-data")  # Update data in Firestore
async def update_data(request, **params):
    try:
        # Parse the request body to JSON
        sorted_ids = request.body

        # Check if the sorted_ids array is provided
        if not sorted_ids:
            return Response(json.dumps({"error": "Missing sorted_ids"}), 400, "application/json")

        # Update the position field of each task in Firestore
        for i, id in enumerate(sorted_ids):
            # Reference to the document to be updated
            doc_ref = db.collection('posts').document(id)

            # Update the document
            doc_ref.update({'position': i})
            print('Updated document')

        return Response(json.dumps({"success": "Data updated successfully"}), 200, "application/json")
    except Exception as e:
        # Log the exception
        print(f"Error updating document: {e}")
        return Response(json.dumps({"error": "Error updating document"}), 500, "application/json")


