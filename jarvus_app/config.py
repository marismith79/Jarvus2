import os
from pathlib import Path

from dotenv import load_dotenv

# Get the project root directory
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Load .env file FIRST to ensure it has priority
env_path = Path(basedir) / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")

# Determine environment AFTER loading .env file
FLASK_ENV = os.getenv("FLASK_ENV", "development")
print(f"Running in {FLASK_ENV} mode")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = FLASK_ENV == "development"
    
    # Environment-based database configuration
    @staticmethod
    def get_database_uri():
        """Get database URI based on environment"""
        if FLASK_ENV == "production":
            db_uri = os.getenv("AZURE_SQL_CONNECTION_STRING")
            if not db_uri:
                raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is not set for production")
            print("Using production database (Azure SQL)")
        else:
            # Development - use TEST_DATABASE_URL or fallback to SQLite
            db_uri = os.getenv("TEST_DATABASE_URL")
            if not db_uri:
                # Fallback to SQLite in instance folder
                instance_path = Path(basedir) / "instance"
                instance_path.mkdir(exist_ok=True)
                db_uri = f"sqlite:///{instance_path}/jarvus_app.db"
                print(f"Using development SQLite database: {db_uri}")
            else:
                print("Using development database from TEST_DATABASE_URL")
        
        return db_uri
    
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    print(f"SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # System prompt for the chatbot
    CHATBOT_SYSTEM_PROMPT = """
    You are a AI agent with access to multiple tools via MCP servers. 
    Your job is to complete the task that the user requests to the best of your ability using the tools as necessary.
    When the user uses @ mentions (like @web, @gmail, @cal), consider these as helpful hints about which tools might be most appropriate for their request. You can still use other tools if needed.
        
    You should return when there is an error that you cannot fix, if there are ambiguities that you cannot solve, or when the task is done.
    When you see an error message or the returned tool result does not complete the user's request, you must analyze the tool call results and try a different tool or fix the arguments. 
    
    When using tools, You must use only the operation names provided, exactly as written. 
    Always double check to make sure to include all the fields in the tool parameters that are set to required. 
    When using tools to query data, set the parameters so that you extract only the absolutely necessary information (e.g., not full email but specific fields, not full spreadsheet but selective cells, etc)
    
    The current date and time is: {CURRENT_DATETIME} (ISO 8601 format).
    """

    # Planning prompt for agent step-by-step planning
    AGENT_PLANNING_PROMPT = (
        "You are an expert AI workflow planner. Your job is to break down the user's request into a sequence of the most detailed, unambiguous, and actionable steps possible, using the following tools: {allowed_tools}. "
        "For each step:\n"
        "- Make the instruction as specific and atomic as possible (one action per step).\n"
        "- List all required parameters and context explicitly.\n"
        "- If any information is missing, infer it (If absolutely necessary, insert a step to request from the user).\n"
        "- Minimize calls to user_feedback and try to complete the task yourself as much as possible.\n"
        "- Define clear, objective success criteria for the step.\n"
        "- Optionally, include error handling instructions if the step could fail or be ambiguous.\n"
        "- For each step, explicitly define any data dependencies on previous steps using an 'inputs' field (a list of variable names required from previous steps). The first step cannot have a required input. \n"
        "- For each step, specify an 'extract' field (a list of variable names to extract from the tool result and store for later use).\n"
        "- When a step needs to use the output of a previous step, refer to it by the variable name defined in 'extract'.\n"
        "Output a JSON list. Each item must have:\n"
        "  'instruction': a single, detailed, actionable command,\n"
        "  'tool': the tool to use (or null),\n"
        "  'success_criteria': how to know the step is complete,\n"
        "  'inputs': a list of variable names required from previous steps (if any),\n"
        "  'extract': a list of variable names to extract from the tool result (if any),\n"
        "  'error_handling': what to do if the step fails (optional).\n"
        "After generating the plan, review each step for clarity and completeness. If any step is unclear or missing information, add a step to request clarification or additional data.\n"
        "Do not include any text outside the JSON list.\n"
        "##Examples:\n"
        "\n"
        "User Request: 'Send an email to Alice with the subject \'Project Update\' and attach the latest report, along with it's summary.'\n"
        "Allowed Tools: ['gmail', 'google_drive']\n"
        "Memory Context: ['Recent reports: Q1_Report.pdf, Q2_Report.pdf']\n"
        "Plan:\n"
        "[\n"
        "  {{\n"
        "    'instruction': 'Search Google Drive for the file named \"Q2_Report.pdf\".',\n"
        "    'tool': 'google_drive',\n"
        "    'success_criteria': 'The file ID for Q2_Report.pdf is found.',\n"
        "    'inputs': [],\n"
        "    'extract': ['file_id'],\n"
        "    'error_handling': 'If the file is not found, search for the file to the best of your ability with different parameters.'\n"
        "  }},\n"
        " {{\n"
        "    'instruction': 'Read through the file that we retrieved and summarize its content (use the memory context to decide what may be important and tailor the summarization)',\n"
        "    'tool': 'google_drive',\n"
        "    'success_criteria': 'The tailored summary of the file is generated',\n"
        "    'inputs': ['file_id'],\n"
        "    'extract': [],\n"
        "    'error_handling': 'If the file is not readable, report the error and retry.'\n"
        "  }},\n"
        "  {{\n"
        "    'instruction': 'Send an email to Alice with the subject \"Project Update\" and attach the report with file_id {{file_id}}.',\n"
        "    'tool': 'gmail',\n"
        "    'success_criteria': 'Email is sent to Alice with the correct subject and the report attached.',\n"
        "    'inputs': ['file_id'],\n"
        "    'extract': ['email_id'],\n"
        "    'error_handling': 'If sending fails, report the error and retry.'\n"
        "  }}\n"
        "]\n"

        "User Request: 'Create a new Google Sheet for tracking expenses.'\n"
        "Allowed Tools: ['google_sheets']\n"
        "Plan:\n"
        "[\n"
        "  {{\n"
        "    'instruction': 'Create a new Google Sheet titled \'Expense Tracker\'.',\n"
        "    'tool': 'google_sheets',\n"
        "    'success_criteria': 'A new Google Sheet named \'Expense Tracker\' is created.',\n"
        "    'inputs': [],\n"
        "    'extract': ['spreadsheet_id'],\n"
        "    'error_handling': null\n"
        "  }}\n"
        "]\n"
    )

# Centralized list of all Pipedream MCP tool apps
ALL_PIPEDREAM_APPS = [
    {"slug": "google_docs", "name": "Google Docs", "mention": "docs"},
    {"slug": "gmail", "name": "Gmail", "mention": "gmail"},
    {"slug": "google_calendar", "name": "Google Calendar", "mention": "gcal"},
    {"slug": "google_sheets", "name": "Google Sheets", "mention": "sheets"},
    {"slug": "google_slides", "name": "Google Slides", "mention": "slides"},
    {"slug": "google_drive", "name": "Google Drive", "mention": "drive"},
    {"slug": "zoom", "name": "Zoom", "mention": "zoom"},
    {"slug": "slack", "name": "Slack", "mention": "slack"},
    {"slug": "notion", "name": "Notion", "mention": "notion"},
    {"slug": "scrapingant", "name": "ScrapingAnt", "mention": "web"},
    # Add more as needed
]


[{'instruction': 'Retrieve all emails received today from midnight (00:00) to the current time.', 'tool': 'gmail', 'success_criteria': 'A list of emails received today is retrieved.', 'inputs': [], 'extract': ['emails_today'], 'error_handling': 'If no emails are found, proceed with an empty list.'}, 
 {'instruction': "For each email in emails_today, extract the sender's name or email address, subject line, date received, and a brief preview of the message content.", 'tool': None, 'success_criteria': 'A structured list of email details (sender, subject, date, preview) is created for all emails.', 'inputs': ['emails_today'], 'extract': ['email_details_list'], 'error_handling': "If any email lacks a field, use 'Unknown' or an empty string as placeholder."}, 
 {'instruction': "Create a new Google Sheet titled 'Email Digest - [current date in YYYY-MM-DD format]'.", 'tool': 'google_sheets', 'success_criteria': 'A new spreadsheet with the specified title is created.', 'inputs': [], 'extract': ['spreadsheet_id'], 'error_handling': 'If creation fails, retry once or report the error.'}, {'instruction': 'Add a header row to the spreadsheet with the columns: Sender, Subject, Date, Preview.', 'tool': 'google_sheets', 'success_criteria': 'The header row is added to the first row of the spreadsheet.', 'inputs': ['spreadsheet_id'], 'extract': [], 'error_handling': 'If adding headers fails, retry once.'}, {'instruction': 'Sort the email_details_list first by sender name alphabetically (A to Z), then by date received from earliest to latest.', 'tool': None, 'success_criteria': 'The email_details_list is sorted accordingly.', 'inputs': ['email_details_list'], 'extract': ['sorted_email_details_list'], 'error_handling': 'If sorting fails, proceed with the original order.'}, {'instruction': "Enter each email's details from sorted_email_details_list as a new row under the header in the spreadsheet, filling columns Sender, Subject, Date, and Preview.", 'tool': 'google_sheets', 'success_criteria': 'All email details are entered correctly into the spreadsheet.', 'inputs': ['spreadsheet_id', 'sorted_email_details_list'], 'extract': [], 'error_handling': 'If data entry fails, retry once or report the error.'}, {'instruction': 'Adjust the column widths in the spreadsheet so that all text fits neatly within each column.', 'tool': 'google_sheets', 'success_criteria': 'Columns are resized appropriately to fit their content.', 'inputs': ['spreadsheet_id'], 'extract': [], 'error_handling': 'If adjustment fails, retry once.'}, {'instruction': 'Freeze the top row of the spreadsheet to keep the header visible during scrolling.', 'tool': 'google_sheets', 'success_criteria': 'The top row is frozen in the spreadsheet.', 'inputs': ['spreadsheet_id'], 'extract': [], 'error_handling': 'If freezing fails, retry once.'}, {'instruction': 'Save the spreadsheet and retrieve its shareable link.', 'tool': 'google_sheets', 'success_criteria': 'The shareable link to the spreadsheet is obtained.', 'inputs': ['spreadsheet_id'], 'extract': ['spreadsheet_link'], 'error_handling': 'If link retrieval fails, retry once or report the error.'}, {'instruction': "Send an email to tetsu.k62@gmail.com with the subject 'Daily Email Digest - [current date in YYYY-MM-DD format]' and include the spreadsheet link in the email body.", 'tool': 'gmail', 'success_criteria': 'The email is sent successfully to tetsu.k62@gmail.com with the correct subject and link.', 'inputs': ['spreadsheet_link'], 'extract': ['email_id'], 'error_handling': 'If sending fails, retry once or report the error.'}]