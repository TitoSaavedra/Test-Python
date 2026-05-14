# Corsair Profiles Downloader

Automated script to scrape and download Corsair iCUE profiles from lewisgerschwitz.com.

## Features

- Scrapes profile information from the website
- Downloads profiles, images, and metadata
- Organizes profiles by category and version
- Creates README files for each profile
- Automatic retry with exponential backoff
- Comprehensive logging

## Installation

1. Ensure dependencies are in `requirements.txt`
2. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

## Usage

```powershell
python projects\corsair_profiles_downloader\main.py
```

The script will:
1. Connect to the Corsair profiles website
2. Scrape profile metadata
3. Download profiles organized by category and version
4. Save to `Corsair_Profiles_Collection/`

## Directory Structure

```
corsair_profiles_downloader/
├── Corsair_Profiles_Collection/
│   ├── Latest CORSAIR iCUE Profiles/
│   │   ├── iCUE 5/
│   │   │   └── Profile_Name/
│   │   │       ├── README.md
│   │   │       ├── profile.zip
│   │   │       └── image.jpg
│   └── ...
└── main.py
```

## Logging

All logs are stored in two locations:
- **Repository root**: `logs/corsair_downloader.log`
- **Project folder**: `projects/corsair_profiles_downloader/logs/corsair_downloader.log`
- Log level: DEBUG (files), INFO (console)
- Rotating logs: 10MB max size, 5 backup files
- Format: `timestamp | logger_name | level | message`

## Requirements

- Python 3.10+
- beautifulsoup4
- requests
- All dependencies in `requirements.txt`
