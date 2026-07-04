# Electronic Library Bot for Archiving and Documentation

This Telegram bot is designed to facilitate archiving and documentation processes, featuring role-based access control, statistical reporting, and an image templating module.

## Features

- **Database Architecture**: Uses SQLite for storing user information and archived content.
- **Interactive Button Tree**: Intuitive navigation through inline keyboards for month, week, and activity type selection.
- **Role-Based Access Control (RBAC)**: Differentiates between regular users (content creators) and administrators with distinct permissions.
- **Archiving Flow**: Users can submit text reports and attach media (photos, videos, PDFs) for archiving.
- **Admin Panel**: Administrators receive instant notifications, can retrieve archived data, and manage users (add, remove, change roles).
- **Statistics Module**: Generates weekly and monthly statistical reports on archived activities.
- **Template Bot Feature**: Allows authorized users to merge news text with images, applying a watermark or placing the image within a pre-designed frame.

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/archive-bot.git
cd archive-bot
```

### 2. Create a Python Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Create `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### 4. Configuration

Open `config.py` and update the following:

- `TOKEN`: Replace with your Telegram Bot API Token.
- `ADMIN_ID`: Replace with the Telegram User ID of the first administrator. This user will have full admin privileges.
- `TEMPLATE_PASSWORD_SECRET`: Set a strong password for accessing the templating feature.
- `WATERMARK_PATH`: Specify the path to your watermark image file (e.g., `watermark.png`). If you don't have one, you can create a dummy one or remove the feature.

### 5. Run the Bot

```bash
python bot.py
```

The bot will start polling for updates. The database (`archive_bot.db`) will be created automatically upon first run, and the `ADMIN_ID` specified in `config.py` will be registered as an admin.

## Usage

- Send `/start` to the bot to begin interaction.
- Follow the inline keyboard prompts to navigate through the menus.
- **Users**: Can archive content by selecting month, week, and activity type, then sending text and media.
- **Admins**: Can access the admin panel for user management and archive retrieval, and generate statistical reports.

## Project Structure

```
archive-bot/
├── bot.py
├── config.py
├── database.py
├── template_processor.py
├── requirements.txt
└── README.md
```

## Technical Notes

- **File Storage**: The bot stores `file_telegram_id` for media files instead of downloading them, saving server space. Media is re-sent using these IDs when requested.
- **Conversation Handling**: Utilizes `ConversationHandler` from `python-telegram-bot` for managing multi-step user interactions.
- **Database**: Uses SQLite with SQLAlchemy ORM for data persistence.
- **Image Processing**: Employs the Pillow library for image templating, including text overlay and watermarking.
