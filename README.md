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

### Deploying as a Kubernetes CronJob

You can deploy the sync tool as a scheduled Kubernetes CronJob using the files provided in the `deployment/` folder:

1. Build and push your Docker image to a container registry:
   ```bash
   docker build -t your-registry/sq-slack-sync:latest .
   docker push your-registry/sq-slack-sync:latest
   ```

2. Update the image name in `deployment/cronjob.yaml`:
   ```yaml
   image: your-registry/sq-slack-sync:latest
   ```

3. Create base64-encoded secrets for the required environment variables:
   ```bash
   echo -n "your-slack-token" | base64
   echo -n "your-squadcast-refresh-token" | base64
   echo -n "your-squadcast-team-id" | base64
   echo -n "squadcast.com" | base64  # or your custom tenancy
   ```

4. Update `deployment/secrets.yaml` with the base64-encoded values:
   ```yaml
   data:
     SLACK_BOT_TOKEN: <base64-encoded-token>
     SQUADCAST_REFRESH_TOKEN: <base64-encoded-token>
     SQUADCAST_TEAM_ID: <base64-encoded-id>
     SQUADCAST_TENANCY: <base64-encoded-tenancy>
   ```

5. Apply the Kubernetes manifests:
   ```bash
   kubectl apply -f deployment/secrets.yaml
   kubectl apply -f deployment/cronjob.yaml
   ```

6. Verify the CronJob is created:
   ```bash
   kubectl get cronjobs
   ```

By default, the CronJob is configured to run every hour. You can modify the schedule in the `cronjob.yaml` file by updating the `schedule` field using standard cron syntax.

## Setting Up Squadcast and Slack

### Squadcast Setup

1. Get your Squadcast refresh token from the profile
2. Find your team ID from the settings page
3. Add a tag with key `slack-usergroup-id` to each schedule you want to sync:
   - The tag value should be the ID of the corresponding Slack user group (starts with 'S')
   - You can find Slack user group IDs in your Slack workspace settings

### Slack Setup

1. Create a Slack app in your workspace
   - **Option 1**: Create manually with the following OAuth scopes:
     - `usergroups:read`
     - `usergroups:write`
     - `users:read`
     - `users:read.email`
     - `chat:write`
   - **Option 2**: Use the provided manifest files:
     - Go to [api.slack.com/apps](https://api.slack.com/apps)
     - Click "Create New App" → "From an app manifest"
     - Select your workspace and paste the contents of either:
       - `manifests/slack_app.json` (JSON format)
       - `manifests/slack_app.yaml` (YAML format)
2. Install the app to your workspace
3. Copy the Bot User OAuth Token for the `SLACK_BOT_TOKEN` environment variable

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