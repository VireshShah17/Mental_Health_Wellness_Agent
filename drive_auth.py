# Import the required libraries
import os.path
import logging
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Configure logging to INFO level by default
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S')

# Set the scope to read-only access to your Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def authenticate_google_drive():
    creds = None

    """ 
        The file token.json stores the user's access and refresh tokens, and is
        created automatically when the authorization flow completes for the first time. 
    """
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        logging.info("===== Loaded existing credentials from token.json. =====")
    
    # If there are no valid credentials availabel, let the user log-in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("===== Credentials expired. Refreshing token... =====")
            creds.refresh(Request())
        else:
            logging.info("===== No valid token found. Initiating local server for authentication flow... =====")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # This will open a browser window on your local machine for you to log in
            creds = flow.run_local_server(port = 0)
        
        # Save the credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            logging.info("===== New credentials saved to token.json. =====")
        
    return build('drive', 'v3', credentials = creds)


def extract_folder_id(url):
    """
        Extracts the folder ID from a standard Google Drive folder URL.
    """
    # Matches the standard /folders/ID format or id=ID format
    match = re.search(r'[-\w]{25,}', url)
    if match:
        return match.group(0)
    else:
        logging.error("===== Could not extract a valid Folder ID from the provided URL. =====")
        return None


def get_files_in_folder(service, folder_id):
    """
        Fetches all files within a specific Drive folder.
    """
    files = []
    page_token = None
    
    # Query: strictly items inside this folder that aren't in the trash
    query = f"'{folder_id}' in parents and trashed = false"
    
    while True:
        try:
            response = service.files().list(
                q = query,
                spaces = 'drive',
                fields = 'nextPageToken, files(id, name)',
                pageToken = page_token
            ).execute()
            
            for file in response.get('files', []):
                files.append(file)
                
            page_token = response.get('nextPageToken', None)

            if page_token is None:
                break
                
        except Exception as e:
            logging.error(f"===== An error occurred while fetching files: {e} =====")
            break
            
    return files


if __name__ == '__main__':
    logging.info("===== Starting Data Ingestion Phase... =====")

    # Ask the user for the specific folder link
    folder_url = input("Please paste the link to your Google Drive diary folder: ")
    folder_id = extract_folder_id(folder_url)

    if folder_id:
        logging.info(f"===== Successfully extracted Folder ID: {folder_id} =====")
        service = authenticate_google_drive()
        logging.info("===== Fetching all files from the specified folder... =====")
        folder_files = get_files_in_folder(service, folder_id)
        
        if not folder_files:
            logging.warning("===== No files found in the folder, or the folder is empty. =====")
        else:
            logging.info(f"===== Success! Found {len(folder_files)} file(s): =====")
            for item in folder_files:
                logging.info(f" - File: {item['name']} | ID: {item['id']}")
