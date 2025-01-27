import os
from notion_client import Client
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json
from datetime import datetime
import io

class NotionBackup:
    def __init__(self, notion_token, service_account_path, root_folder_id):
        self.notion = Client(auth=notion_token)
        self.root_folder_id = root_folder_id
        self.drive_service = self._initialize_drive_service(service_account_path)
        self.folder_cache = {}  # Cache to store folder IDs

    def _initialize_drive_service(self, service_account_path):
        """Initialize Google Drive service with service account"""
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = Credentials.from_service_account_file(
            service_account_path,
            scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)

    def create_folder(self, folder_name, parent_id):
        """Create a folder in Google Drive and return its ID"""
        try:
            # Check if folder already exists
            query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            # Return existing folder ID if found
            if results['files']:
                return results['files'][0]['id']

            # Create new folder if it doesn't exist
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            return folder.get('id')
        except Exception as e:
            raise Exception(f"Failed to create folder '{folder_name}': {str(e)}")

    def get_page_title(self, page):
        """Extract page title from Notion page object"""
        try:
            if 'properties' in page and 'title' in page['properties']:
                title_info = page['properties']['title']
                if isinstance(title_info, list) and title_info:
                    return title_info[0].get('text', {}).get('content', 'Untitled')
                else:
                    return title_info.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
            return 'Untitled'
        except Exception:
            return 'Untitled'

    def get_all_pages(self):
        """Retrieve all pages from Notion and organize them hierarchically"""
        pages = []
        page_dict = {}
        
        try:
            response = self.notion.search(
                **{
                    "filter": {
                        "property": "object",
                        "value": "page"
                    }
                }
            )
            
            # First pass: collect all pages and build dictionary
            while True:
                for page in response['results']:
                    pages.append(page)
                    page_dict[page['id']] = {
                        'page': page,
                        'children': [],
                        'parent_id': page.get('parent', {}).get('page_id')
                    }
                
                if not response.get('has_more'):
                    break
                    
                response = self.notion.search(
                    start_cursor=response['next_cursor'],
                    **{
                        "filter": {
                            "property": "object",
                            "value": "page"
                        }
                    }
                )
            
            # Second pass: build hierarchy
            root_pages = []
            for page_id, info in page_dict.items():
                parent_id = info['parent_id']
                if parent_id:
                    if parent_id in page_dict:
                        page_dict[parent_id]['children'].append(info)
                else:
                    root_pages.append(info)
            
            return root_pages
            
        except Exception as e:
            raise Exception(f"Failed to fetch Notion pages: {str(e)}")

    def backup_page(self, page_info, parent_folder_id):
        """Backup a single Notion page and its subpages to Google Drive"""
        page = page_info['page']
        page_id = page['id']
        page_title = self.get_page_title(page)
        
        try:
            # Create folder for this page
            folder_name = f"{page_title}_{datetime.now().strftime('%Y%m%d')}"
            folder_id = self.create_folder(folder_name, parent_folder_id)
            self.folder_cache[page_id] = folder_id
            
            # Backup page content
            try:
                page_content = self.notion.blocks.children.list(block_id=page_id)
                file_content = json.dumps(page_content, indent=2)
                file_metadata = {
                    'name': f"{page_title}_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    'parents': [folder_id]
                }
                
                media = MediaIoBaseUpload(
                    io.BytesIO(file_content.encode('utf-8')),
                    mimetype='application/json',
                    resumable=True
                )
                
                print(f"Uploading content for page '{page_title}'...")
                self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
            except Exception as e:
                print(f"Error backing up content for page '{page_title}': {str(e)}")
            
            # Backup child pages
            for child_info in page_info['children']:
                try:
                    self.backup_page(child_info, folder_id)
                except Exception as e:
                    print(f"Error backing up child page: {str(e)}")
            
            return folder_name
            
        except Exception as e:
            raise Exception(f"Failed to backup page '{page_title}': {str(e)}")

    def run_backup(self):
        """Run the complete backup process"""
        try:
            print("Starting Notion backup...")
            root_pages = self.get_all_pages()
            print(f"Found {len(root_pages)} root pages")
            
            # Create main backup folder with timestamp
            backup_folder_name = f"Notion_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_folder_id = self.create_folder(backup_folder_name, self.root_folder_id)
            
            successful_backups = 0
            failed_backups = 0
            
            for i, page_info in enumerate(root_pages, 1):
                try:
                    folder_name = self.backup_page(page_info, backup_folder_id)
                    print(f"[{i}/{len(root_pages)}] Backed up: {folder_name}")
                    successful_backups += 1
                except Exception as e:
                    print(f"Error backing up root page {i}: {str(e)}")
                    failed_backups += 1
            
            print(f"\nBackup completed!")
            print(f"Successfully backed up: {successful_backups} root pages and their subpages")
            print(f"Failed to backup: {failed_backups} root pages")
            print(f"Backup folder: {backup_folder_name}")
            
        except Exception as e:
            print(f"Backup failed: {str(e)}")

def main():
    # Configuration
    NOTION_TOKEN = "YOUR_NOTION_API_KEY"  # Your Notion API key
    SERVICE_ACCOUNT_PATH = "service-account-key.json"  # Path to service account JSON file
    ROOT_FOLDER_ID = "GOOGLE_DRIVE_FOLDER_ID"  # Google Drive folder ID
    # Initialize and run backup
    backup = NotionBackup(NOTION_TOKEN, SERVICE_ACCOUNT_PATH, ROOT_FOLDER_ID)
    backup.run_backup()

if __name__ == "__main__":
    main()