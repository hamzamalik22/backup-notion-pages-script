# Notion to Google Drive Backup Script

This Python script automatically backs up your Notion pages to Google Drive, maintaining the hierarchical structure of your pages. Each page is saved in its own folder, with subpages organized as subfolders.

## Features

- Backs up all Notion pages and their content
- Maintains page hierarchy in Google Drive folder structure
- Creates timestamped backups
- Handles pagination for large Notion workspaces
- Uses service account authentication for reliable access
- Includes error handling and progress reporting

## Prerequisites

- Python 3.7 or higher
- A Notion account with admin access
- A Google Cloud project
- A Google Drive folder for backups

## Step-by-Step Setup Guide

### 1. Install Required Python Packages

```bash
pip install notion-client google-api-python-client
# or
pip install -r requirements.txt
```

### 2. Set Up Notion API Access

1. Go to [Notion Developers](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name your integration (e.g., "Notion Backup")
4. Select the workspace where you want to use the integration
5. Click "Submit"
6. Copy the "Internal Integration Token" (starts with `secret_`)
7. In your Notion workspace, share each page you want to backup with your integration:
   - Open a page
   - Click "Share" in the top right
   - Click "Add people, emails, groups, or integrations"
   - Search for your integration name
   - Click "Invite"

### 3. Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create a service account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Click "Create"
   - Skip the optional steps
   - Click "Done"
5. Create and download the service account key:
   - Click on the newly created service account
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format
   - The key file will automatically download
   - Save this file securely - you'll need it for the script

### 4. Set Up Google Drive Folder

1. Create a folder in Google Drive where you want to store the backups
2. Right-click the folder and click "Share"
3. Copy the service account email (looks like: `something@project-id.iam.gserviceaccount.com`)
4. Add this email to your folder with "Editor" access
5. Get the folder ID from the URL:
   - Open the folder in Google Drive
   - The URL will look like: `https://drive.google.com/drive/folders/FOLDER_ID`
   - Copy the `FOLDER_ID` part

### 5. Configure the Script

1. Download the script to your computer
2. Open the script in a text editor
3. Update the configuration in the `main()` function:

```python
def main():
    # Configuration
    NOTION_TOKEN = "your_notion_token"  # Add your Notion API key
    SERVICE_ACCOUNT_PATH = "path/to/your/service-account-key.json"  # Add path to your service account JSON file
    ROOT_FOLDER_ID = "your_folder_id"  # Add your Google Drive folder ID
```

## Usage

Run the script:

```bash
python notion_backup.py
```

The script will:
1. Create a main backup folder with timestamp
2. Create subfolders for each page
3. Save page contents as JSON files
4. Maintain the hierarchy of your Notion pages

The resulting structure will look like:

```
Notion_Backup_20250120_123456/
├── MainPage1_20250120/
│   ├── MainPage1_content_20250120_123456.json
│   └── SubPage1_20250120/
│       └── SubPage1_content_20250120_123456.json
└── MainPage2_20250120/
    └── MainPage2_content_20250120_123456.json
```

## Troubleshooting

### Common Issues

1. **"Access denied" error:**
   - Make sure you've shared your Google Drive folder with the service account email
   - Verify that the service account key file is correct and accessible

2. **"Page not found" error:**
   - Ensure you've shared your Notion pages with your integration
   - Verify that your Notion API key is correct

3. **"Invalid credentials" error:**
   - Check that your service account key file is correctly referenced in the script
   - Verify that the Google Drive API is enabled in your project

### Error Messages

The script provides detailed error messages for:
- Failed page backups
- Connection issues
- Authentication problems
- File creation errors

Check the console output for specific error messages and their causes.

## Scheduling Automatic Backups

You can automate the backup process using:

### On Windows:
Use Task Scheduler:
1. Open Task Scheduler
2. Create a new task
3. Add an action that runs your Python script
4. Set your desired schedule

### On Linux/Mac:
Use cron:
1. Open terminal
2. Type `crontab -e`
3. Add a line like:
```bash
0 0 * * * /usr/bin/python3 /path/to/notion_backup.py
```
This will run the backup daily at midnight.

## Security Notes

- Keep your Notion API key secure
- Store the service account key file in a safe location
- Don't share these credentials with others
- Consider encrypting sensitive configuration files

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.