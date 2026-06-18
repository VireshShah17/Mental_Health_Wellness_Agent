# Import the required libraries
import os.path
import logging
import re
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


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


def download_docx_from_drive(service, file_name):
    """
        Searches for a specific file by name and downloads/exports it locally.
    """
    query = f"name='{file_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        logging.error(f"===== File '{file_name}' not found in Drive. =====")
        return None

    file_id = items[0]['id']
    mime_type = items[0]['mimeType']
    logging.info(f"===== Downloading {file_name} from Google Drive... =====")
    
    if 'application/vnd.google-apps.document' in mime_type:
        logging.info("===== Google Doc detected. Exporting to .docx format... =====")
        request = service.files().export_media(
            fileId = file_id, 
            mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    else:
        logging.info("===== Standard file detected. Downloading directly... =====")
        request = service.files().get_media(fileId=file_id)
        
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    # Ensure the local file ends with .docx so python-docx can parse it
    local_path = f"temp_{file_name}"
    if not local_path.endswith('.docx'):
         local_path += '.docx'
         
    with open(local_path, 'wb') as f:
        f.write(fh.getvalue())
        
    return local_path

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
