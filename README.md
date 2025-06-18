# Squadcast Slack Sync

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

## Overview

Squadcast Slack Sync is a tool that synchronizes Squadcast on-call schedules with Slack user groups. It ensures that your Slack user groups always reflect who is currently on-call in Squadcast, enabling seamless communication and incident response.

## Features

- **Automatic Synchronization**: Keep Slack user groups up-to-date with Squadcast on-call rotations
- **Schedule Tagging**: Use tags to define which Slack user groups correspond to which schedules
- **Robust Error Handling**: Detailed logging and error recovery
- **Flexible Deployment**: Run as a script, Python package, or Docker container

## Installation

```bash
# Clone the repository
git clone https://github.com/SquadcastHub/sq-slack-sync.git

# Navigate to the project directory
cd sq-slack-sync

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Set the following required environment variables:

| Variable                | Description                                           | Required |
|------------------------|-------------------------------------------------------|----------|
| SQUADCAST_REFRESH_TOKEN | Squadcast API refresh token                           | Yes      |
| SQUADCAST_TEAM_ID       | ID of your Squadcast team                             | Yes      |
| SLACK_BOT_TOKEN         | Slack bot user OAuth token                            | Yes      |
| SQUADCAST_TENANCY       | Squadcast tenancy domain (default: squadcast.com)     | No       |

You can set these variables directly in your environment, in a `.env` file, or pass them as Docker environment variables.

### Configuration File

The application can also be configured using a `config.json` file:

```json
{
  "sync_settings": {
    "log_level": "INFO",
    "log_file": "squadcast_slack_sync.log",
    "timeout_seconds": 30
  },
  "slack_settings": {
    "retry_attempts": 3,
    "retry_delay_seconds": 2
  },
  "squadcast_settings": {
    "sync_interval_minutes": 5
  }
}
```

## Usage

### Running as a Script

```bash
# Basic usage
python main.py
```


### Running from Docker

```bash
docker-compose up
```

## Setting Up Squadcast and Slack

### Squadcast Setup

1. Get your Squadcast refresh token from the profile
2. Find your team ID from the settings page
3. Add a tag with key `slack-usergroup-id` to each schedule you want to sync:
   - The tag value should be the ID of the corresponding Slack user group (starts with 'S')
   - You can find Slack user group IDs in your Slack workspace settings

### Slack Setup

1. Create a Slack app in your workspace
2. Add the following OAuth scopes:
   - `usergroups:read`
   - `usergroups:write`
   - `users:read`
   - `users:read.email`
3. Install the app to your workspace
4. Copy the Bot User OAuth Token for the `SLACK_BOT_TOKEN` environment variable

## Important Notes

- The `"slack-usergroup-id"` tag is essential for syncing schedules with Slack user groups. If this tag is not set for a schedule, the sync process will skip that schedule.
- Ensure the bot has been added to all user groups it needs to manage
- Email addresses must match between Squadcast and Slack for user mapping to work

## Development

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/SquadcastHub/sq-slack-sync.git
cd squadcast-slack-sync

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please:

- Open an issue on [GitHub](https://github.com/SquadcastHub/sq-slack-sync/issues)
- Reach out to [support@squadcast.com](mailto:support@squadcast.com)