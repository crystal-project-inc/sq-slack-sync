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
from typing import Dict, List
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


async def format_channel_topic(schedules: List[OncallSchedule], slack_client: SlackClient) -> str:
    """
    Format the channel topic with oncall information for all schedules
    
    Args:
        schedules: List of oncall schedules
        slack_client: The Slack API client
        
    Returns:
        Formatted topic string
    """
    topic_lines = []
    
    for schedule_state in schedules:
        schedule_name = schedule_state.schedule.name
        oncall_users = schedule_state.get_oncall_users()
        
        if not oncall_users:
            continue
            
        # Get Slack user mentions for oncall users
        mentions = []
        for user in oncall_users:
            try:
                slack_user = await slack_client.get_user_by_email(user.email)
                mentions.append(f"<@{slack_user.id}>")
            except SlackAPIError as e:
                logger.warning(f"Failed to find Slack user for email {user.email}: {e.message}")
                # Fallback to first name if Slack user not found
                mentions.append(f"{user.firstName}")
        
        if mentions:
            mentions_str = " ".join(mentions)
            topic_lines.append(f"{schedule_name}: {mentions_str}")
    
    return "\n".join(topic_lines)


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
        
        # Filter schedules that have slack-usergroup-id tag (only processed schedules)
        processed_schedules = []
        channel_ids = set()  # Collect unique channel IDs from all schedules
        
        # Update usergroups for each schedule
        for schedule_state in schedule_states:
            # Check if schedule has the required tag
            slack_tags = list(
                filter(
                    lambda tag: tag.key == "slack-usergroup-id",
                    schedule_state.schedule.tags,
                )
            )
            
            if len(slack_tags) == 1:
                processed_schedules.append(schedule_state)
                await process_schedule(schedule_state, slack_client)
                
                # Check for slack-channel-id tags
                channel_tags = list(
                    filter(
                        lambda tag: tag.key == "slack-channel-id",
                        schedule_state.schedule.tags,
                    )
                )
                
                # Add channel IDs from this schedule (support comma-separated values)
                for channel_tag in channel_tags:
                    channel_ids_from_tag = [cid.strip() for cid in channel_tag.value.split(",")]
                    channel_ids.update(channel_ids_from_tag)
            else:
                logger.info(f"Skipping schedule '{schedule_state.schedule.name}' as no slack-usergroup-id tag is found")
        
        # Update channel topics for all collected channel IDs
        for channel_id in channel_ids:
            if channel_id:
                logger.info(f"Checking channel topic for channel {channel_id}")
                try:
                    new_topic = await format_channel_topic(processed_schedules, slack_client)
                    if new_topic:
                        try:
                            current_topic = await slack_client.get_channel_topic(channel_id)
                            if current_topic == new_topic:
                                logger.info(f"Channel topic for {channel_id} is already up to date")
                            else:
                                logger.info(f"Updating channel topic for channel {channel_id}")
                                await slack_client.set_channel_topic(channel_id, new_topic)
                                logger.info(f"Successfully updated channel topic for {channel_id}")
                        except SlackAPIError as e:
                            logger.warning(f"Could not get current topic for channel {channel_id}: {e.message}")
                            logger.info(f"Proceeding with topic update for channel {channel_id}")
                            await slack_client.set_channel_topic(channel_id, new_topic)
                            logger.info(f"Successfully updated channel topic for {channel_id}")
                    else:
                        logger.warning("No oncall information available for channel topic")
                except SlackAPIError as e:
                    logger.error(f"Failed to update channel topic for {channel_id}: {e.message}")
        
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
        
    Returns:
        None
    """
    schedule_name = schedule_state.schedule.name
    
    slack_tags = list(
        filter(
            lambda tag: tag.key == "slack-usergroup-id",
            schedule_state.schedule.tags,
        )
    )
    
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
