# Squadcast Slack Sync

## Overview

Squadcast Slack Sync is a tool designed to integrate Squadcast schedules with Slack user groups, ensuring seamless communication and collaboration.

## Features

- **Incident Notifications**: Receive Squadcast incident updates directly in Slack.
- **Actionable Commands**: Perform Squadcast actions from Slack.
- **Customizable**: Configure settings to suit your team's workflow.

## Installation

Follow these steps to set up the application:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/squadcast-slack-sync.git
   ```
2. **Navigate to the project directory**:
   ```bash
   cd squadcast-slack-sync
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set up the environment variables:

1. **Set the following environment variables** directly in your system (see [Environment Variables Reference](#environment-variables-reference) for details):
   ```plaintext
   SQUADCAST_REFRESH_TOKEN
   SQUADCAST_TEAM_ID
   SLACK_BOT_TOKEN
   SQUADCAST_TENANCY
   ```

## Usage

Run the application using the following command:

```bash
python main.py
```

## Important Notes

- The `"slack-usergroup-id"` tag is essential for syncing schedules with Slack user groups. If this tag is not set for a schedule, the sync process will skip that schedule.
- Ensure the value of the `"slack-usergroup-id"` tag matches the Slack user group ID in Squadcast schedules for proper integration.

## Project Structure

- **main.py**: Entry point of the application.
- **slack_client.py**: Handles Slack API interactions.
- **squadcast_client.py**: Manages Squadcast API requests.
- **env.py**: Loads environment variables.

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.

## Environment Variables Reference

- **SQUADCAST_REFRESH_TOKEN**: Used to authenticate and refresh Squadcast API access.
- **SQUADCAST_TEAM_ID**: Specifies the Squadcast team for which schedules are managed.
- **SLACK_BOT_TOKEN**: Token for authenticating the Slack bot to perform actions.
- **SQUADCAST_TENANCY**: Defines the Squadcast tenancy domain (default: squadcast.com).