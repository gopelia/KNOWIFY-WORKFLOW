from flask import Flask, request, jsonify
import requests
import json
import pickle
import os
from pathlib import Path

app = Flask(__name__)

class KnowifyAPI:
    def __init__(self):
        self.base_url = "https://api.knowify.com"
        self.session = requests.Session()
        self.auth_token = None
        self.cookies = {}
        self.session_file = "session_cookies.pkl"
        self.credentials = {}

    def save_session(self):
        """
        Save session cookies to file
        """
        try:
            session_data = {
                'cookies': self.cookies,
                'auth_token': self.auth_token,
                'credentials': self.credentials
            }
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
            return True
        except Exception as e:
            print(f"Error saving session: {str(e)}")
            return False

    def load_session(self):
        """
        Load session cookies from file
        """
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'rb') as f:
                    session_data = pickle.load(f)
                    self.cookies = session_data.get('cookies', {})
                    self.auth_token = session_data.get('auth_token')
                    self.credentials = session_data.get('credentials', {})

                    # Restore cookies to session
                    for key, value in self.cookies.items():
                        self.session.cookies.set(key, value)

                    return True
            return False
        except Exception as e:
            print(f"Error loading session: {str(e)}")
            return False

    def verify_session(self):
        """
        Verify if current session is still valid by making a test request
        """
        try:
            result = self.get_project_status_ids()
            return result['success']
        except:
            return False

    def login(self, username, password):
        """
        Login to Knowify API
        """
        login_url = f"{self.base_url}/account/login"

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Bearer abc',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://secure.knowify.com',
            'referer': 'https://secure.knowify.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }

        payload = {
            "UserName": username,
            "Password": password
        }

        try:
            response = self.session.post(
                login_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                # Extract cookies from response
                self.cookies = self.session.cookies.get_dict()

                # Extract kAuth token from cookies if available
                if 'kAuth' in self.cookies:
                    self.auth_token = self.cookies['kAuth']

                # Save credentials and session
                self.credentials = {'username': username, 'password': password}
                self.save_session()

                return {
                    'success': True,
                    'message': 'Login successful',
                    'data': response.json() if response.text else None
                }
            else:
                return {
                    'success': False,
                    'message': f'Login failed with status code: {response.status_code}',
                    'data': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Login error: {str(e)}',
                'data': None
            }

    def ensure_authenticated(self, username=None, password=None):
        """
        Ensure user is authenticated.
        Priority: 1) Valid saved session, 2) Provided credentials, 3) Saved credentials
        """
        # Priority 1: Try to load and verify existing session first
        if self.load_session():
            # Verify if session is still valid
            if self.verify_session():
                return {
                    'success': True,
                    'message': 'Authenticated using saved session',
                    'method': 'session'
                }
            else:
                print("Saved session expired, attempting login...")

        # Priority 2: If session invalid or doesn't exist, use provided credentials
        if username and password:
            return {**self.login(username, password), 'method': 'fresh_login'}

        # Priority 3: Try to use saved credentials as last resort
        if self.credentials.get('username') and self.credentials.get('password'):
            return {**self.login(self.credentials['username'], self.credentials['password']), 'method': 'saved_credentials'}

        return {
            'success': False,
            'message': 'No valid session found and no credentials provided',
            'method': 'none'
        }

    def get_project_status_ids(self):
        """
        Get project status IDs including rejected projects (IdsLost)
        """
        url = f"{self.base_url}/Projects/projectsStatusIds"

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Bearer abc',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://secure.knowify.com',
            'referer': 'https://secure.knowify.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }

        # Add kAuth token to headers if available
        if self.auth_token:
            headers['kauth'] = self.auth_token

        payload = {
            "Page": 1,
            "PageSize": 20,
            "Sort": "DateUsed",
            "SortAsc": False,
            "ForClient": True,
            "LimitToProjectLeaders": False,
            "Search": "",
            "ProjectStatus": None,
            "StartDate": "2011-04-11T19:57:41.278Z",
            "EndDate": None,
            "IncludeClosed": True
        }

        try:
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                cookies=self.cookies,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'message': 'Data retrieved successfully',
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'message': f'Request failed with status code: {response.status_code}',
                    'data': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Request error: {str(e)}',
                'data': None
            }

    def get_project_details(self, project_id):
        """
        Get project details by ID
        """
        url = f"https://reporting.knowify.com/api/meta/search/projects?page_size=1&query=%7B%22Id%22:%7B%22$eq%22:%22{project_id}%22%7D%7D"

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,ar-TN;q=0.8,ar;q=0.7',
            'authorization': 'Bearer abc',
            'cache-control': 'no-cache',
            'kauth': self.auth_token if self.auth_token else '',
            'origin': 'https://secure.knowify.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://secure.knowify.com/',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }

        try:
            response = self.session.get(
                url,
                headers=headers,
                cookies=self.cookies,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('DidSucceed') and data.get('Data'):
                    project_data = data['Data']
                    return {
                        'success': True,
                        'data': {
                            'ProjectId': project_data.get('ProjectId'),
                            'ProjectName': project_data.get('ProjectName'),
                            'DateUsed': project_data.get('DateUsed')
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Project not found',
                        'data': None
                    }
            else:
                return {
                    'success': False,
                    'message': f'Request failed with status code: {response.status_code}',
                    'data': None
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Request error: {str(e)}',
                'data': None
            }


# Initialize Knowify API instance
knowify = KnowifyAPI()


@app.route('/get_rejected_projects', methods=['GET'])
def get_rejected_projects():
    """
    Endpoint to login and retrieve latest 3 rejected projects with details
    Accepts username and password as query parameters.
    Will try to use saved session first, then credentials if provided.
    """
    try:
        # Get credentials from query parameters
        username = request.args.get('username') or request.args.get('UserName')
        password = request.args.get('password') or request.args.get('Password')

        # Step 1: Ensure authentication (try session first, then credentials)
        auth_result = knowify.ensure_authenticated(username, password)

        if not auth_result['success']:
            return jsonify({
                'success': False,
                'message': f"Authentication failed: {auth_result['message']}",
                'rejected_projects': []
            }), 401

        # Step 2: Get project status IDs
        projects_result = knowify.get_project_status_ids()

        if not projects_result['success']:
            return jsonify({
                'success': False,
                'message': f"Failed to retrieve projects: {projects_result['message']}",
                'rejected_projects': []
            }), 500

        # Step 3: Extract IdsLost from response and get latest 3
        try:
            ids_lost = projects_result['data']['Data']['Status']['IdsLost']

            # Get latest 3 IDs
            latest_3_ids = ids_lost[:3]

            # Step 4: Get details for each of the latest 3 projects
            project_details = []
            for project_id in latest_3_ids:
                details_result = knowify.get_project_details(project_id)
                if details_result['success']:
                    project_details.append(details_result['data'])
                else:
                    # If we can't get details, still include the ID
                    project_details.append({
                        'ProjectId': project_id,
                        'ProjectName': 'Unable to fetch',
                        'DateUsed': None
                    })

            return jsonify({
                'success': True,
                'message': 'Latest 3 rejected projects retrieved successfully',
                'auth_method': auth_result.get('method', 'unknown'),
                'rejected_projects': project_details,
                'count': len(project_details)
            }), 200

        except KeyError as e:
            return jsonify({
                'success': False,
                'message': f'Could not find IdsLost in response: {str(e)}',
                'rejected_projects': [],
                'raw_data': projects_result['data']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Unexpected error: {str(e)}',
            'rejected_projects': []
        }), 500


@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint with API documentation
    """
    return jsonify({
        'name': 'Knowify API',
        'version': '1.0.0',
        'endpoints': {
            '/get_rejected_projects': {
                'method': 'GET',
                'description': 'Login to Knowify and retrieve latest 3 rejected projects with details',
                'query_parameters': {
                    'username': 'your_username (optional if session exists)',
                    'password': 'your_password (optional if session exists)'
                },
                'example': '/get_rejected_projects?username=your_username&password=your_password',
                'response': {
                    'success': 'boolean',
                    'message': 'string',
                    'auth_method': 'session|fresh_login|saved_credentials',
                    'rejected_projects': 'array of objects with ProjectId, ProjectName, DateUsed',
                    'count': 'number of rejected projects (max 3)'
                },
                'notes': 'Returns latest 3 rejected projects. First request requires credentials. Subsequent requests use saved session automatically.'
            }
        }
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
