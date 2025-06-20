#!/usr/bin/env python3
"""
Squadcast Slack Sync

This script synchronizes Squadcast on-call schedules with Slack user groups.
It retrieves the current on-call users from Squadcast and updates the
corresponding Slack user groups based on the "slack-usergroup-id" tag.
"""

import asyncio
import logging
import sys
import env
import config
from typing import Dict
from slack_client import SlackClient, SlackAPIError
from squadcast_client import SquadcastClient, SquadcastAPIError, OncallSchedule
import colorlog

# Configure root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler('squadcast_slack_sync.log', mode='a')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Colored stream handler
color_formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'magenta'
    }
)
color_handler = colorlog.StreamHandler()
color_handler.setFormatter(color_formatter)
logger.addHandler(color_handler)



async def main():
    """Main entry point for the application"""
    # Load configuration
    cfg = config.load_config()
    sync_settings: Dict = cfg.get('sync_settings', {})
    
    logger.info("Squadcast Slack Sync starting")
    
    # Get environment variables
    try:
        sq_ref_token = env.get("SQUADCAST_REFRESH_TOKEN")
        squadcast_team_id = env.get("SQUADCAST_TEAM_ID")
        slack_bot_token = env.get("SLACK_BOT_TOKEN")
    except SystemExit as e:
        logger.error("Missing required environment variables")
        sys.exit(e.code)
    
    try:
        timeout_seconds = sync_settings.get('timeout_seconds', 30)
        logger.info("Initializing API clients")
        squadcast_client = SquadcastClient(sq_ref_token, squadcast_team_id, timeout=timeout_seconds)
        slack_client = SlackClient(slack_bot_token, timeout=timeout_seconds)
        
        # Get schedules from Squadcast
        logger.info(f"Retrieving schedules for team {squadcast_team_id}")
        schedules = await squadcast_client.get_schedules()
        schedule_states = schedules.whoIsOncall
        
        for schedule_state in schedule_states:
            await process_schedule(schedule_state, slack_client)
        
        logger.info("Sync completed successfully")
        
    except SquadcastAPIError as e:
        logger.error(f"Squadcast API error: {e.message}")
        if hasattr(e, 'status_code') and e.status_code:
            logger.debug(f"Status code: {e.status_code}")
        if hasattr(e, 'response') and e.response:
            logger.debug(f"Response: {e.response}")
        sys.exit(2)
        
    except SlackAPIError as e:
        logger.error(f"Slack API error: {e.message}")
        if hasattr(e, 'error_code') and e.error_code:
            logger.debug(f"Error code: {e.error_code}")
        if hasattr(e, 'response') and e.response:
            logger.debug(f"Response: {e.response}")
        sys.exit(2)
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(3)


async def process_schedule(schedule_state: OncallSchedule, slack_client: SlackClient):
    """
    Process a single schedule to sync its members with Slack
    
    Args:
        schedule_state: The schedule to process
        slack_client: The Slack API client
        dry_run: Whether to run in dry-run mode (no actual changes)
        
    Returns:
        None
    """
    schedule_name = schedule_state.schedule.name
    
    # Find the slack usergroup ID tag
    slack_tags = list(
        filter(
            lambda tag: tag.key == "slack-usergroup-id",
            schedule_state.schedule.tags,
        )
    )
    
    # Skip schedules without the required tag
    if len(slack_tags) != 1:
        logger.info(f"Skipping schedule '{schedule_name}' as no slack-usergroup-id tag is found")
        return

    slack_usergroup_id = slack_tags[0].value
    logger.info(f"Processing schedule '{schedule_name}' with Slack usergroup ID: {slack_usergroup_id}")

    # Get emails of users currently on-call
    user_emails = schedule_state.get_user_emails()
    if not user_emails:
        logger.warning(f"No on-call users found for schedule '{schedule_name}'")
        return
    
    # Map emails to Slack user IDs
    slack_user_ids = []
    logger.info(f"Looking up Slack IDs for {len(user_emails)} users")
    
    for email in user_emails:
        try:
            slack_user = await slack_client.get_user_by_email(email)
            slack_user_ids.append(slack_user.id)
            logger.debug(f"Found Slack ID {slack_user.id} for email {email}")
        except SlackAPIError as e:
            logger.error(f"Failed to find Slack user for email {email}: {e.message}")
            if "users_not_found" in e.message:
                logger.warning(f"Email {email} not found in Slack workspace - skipping this user")
                continue
            raise
    
    if not slack_user_ids:
        logger.warning(f"No valid Slack users found for schedule '{schedule_name}' - skipping update")
        return
        
    # Update the usergroup with the new members
    logger.info(f"Updating Slack usergroup ({slack_usergroup_id}) with {len(slack_user_ids)} members")
    await slack_client.update_user_group(
        slack_usergroup_id,
        slack_user_ids,
    )
    logger.info(f"Successfully updated Slack usergroup for schedule '{schedule_name}'")
    return

if __name__ == "__main__":
    asyncio.run(main())
