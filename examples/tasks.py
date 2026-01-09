"""Predefined verifiable tasks for the file system environment."""

from examples.file_api_env import Task

# Easy tasks - direct navigation and simple commands
EASY_TASKS = [
    Task(
        goal="Navigate to /home/user/projects and list the files there",
        verify=lambda s: s.cwd == "/home/user/projects"
        and "README.md" in s.last_output,
    ),
    Task(
        goal="Find out what directory you're currently in",
        verify=lambda s: "/" in s.last_output and "pwd" not in s.last_output.lower(),
    ),
    Task(
        goal="List all files in the /etc/app directory",
        verify=lambda s: "config.json" in s.last_output,
    ),
    Task(
        goal="Navigate to /home/user/docs and display the contents of notes.txt",
        verify=lambda s: "Meeting notes" in s.last_output,
    ),
]

# Medium tasks - require exploration and multi-step reasoning
MEDIUM_TASKS = [
    Task(
        goal="Find the database password stored in the config files under /etc",
        verify=lambda s: "secret123" in s.last_output,
    ),
    Task(
        goal="Find the port number configured in /etc/app/config.json",
        verify=lambda s: "8080" in s.last_output,
    ),
    Task(
        goal="Find all Python files in the system and list them",
        verify=lambda s: all(
            f in s.last_output for f in ["main.py", "utils.py", "config.py"]
        ),
    ),
    Task(
        goal="Navigate to /home/user/projects/src and read the main.py file",
        verify=lambda s: "Hello, World!" in s.last_output,
    ),
    Task(
        goal="Find the DEBUG setting in the Python config file under projects",
        verify=lambda s: "DEBUG" in s.last_output and "True" in s.last_output,
    ),
]

# Hard tasks - require complex multi-step reasoning and file operations
HARD_TASKS = [
    Task(
        goal="Copy the notes.txt file from /home/user/docs to the /backup directory",
        verify=lambda s: s.file_exists("/backup/notes.txt"),
    ),
    Task(
        goal="Find the main.py file and copy it to /backup",
        verify=lambda s: s.file_exists("/backup/main.py"),
    ),
    Task(
        goal="Create a new directory called 'archive' in /tmp and copy README.md there",
        verify=lambda s: s.dir_exists("/tmp/archive")
        and s.file_exists("/tmp/archive/README.md"),
    ),
    Task(
        goal="Find the config.json file, read its contents, then copy it to /backup",
        verify=lambda s: s.file_exists("/backup/config.json")
        and "port" in s.last_output,
    ),
]

# All tasks combined for training
ALL_TASKS = EASY_TASKS + MEDIUM_TASKS + HARD_TASKS

# Training tasks (subset for quick testing)
TRAINING_TASKS = [
    EASY_TASKS[0],  # Navigate and list
    EASY_TASKS[3],  # Read notes.txt
    MEDIUM_TASKS[0],  # Find password
    MEDIUM_TASKS[2],  # Find Python files
    HARD_TASKS[0],  # Copy notes.txt
]

# Evaluation tasks (held out for testing generalization)
EVAL_TASKS = [
    EASY_TASKS[2],  # List /etc/app
    MEDIUM_TASKS[1],  # Find port number
    HARD_TASKS[1],  # Find and copy main.py
]


