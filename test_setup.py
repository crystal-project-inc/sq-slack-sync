#!/usr/bin/env python3
"""
Test script for Squadcast Slack Sync setup

This script tests the basic configuration and connectivity
without making any actual changes to Slack user groups.
"""

import asyncio
import logging
import sys
import env
import config
from slack_client import SlackClient, SlackAPIError
from squadcast_client import SquadcastClient, SquadcastAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_setup():
    """Test the basic setup and connectivity"""
    logger.info("Starting setup test...")
    
    # Test 1: Environment variables
    logger.info("Testing environment variables...")
    try:
        sq_ref_token = env.get("SQUADCAST_REFRESH_TOKEN")
        squadcast_team_id = env.get("SQUADCAST_TEAM_ID")
        slack_bot_token = env.get("SLACK_BOT_TOKEN")
        squadcast_tenancy = env.get("SQUADCAST_TENANCY", "squadcast.com")
        
        logger.info("✅ All required environment variables are set")
        logger.info(f"  - Squadcast Team ID: {squadcast_team_id}")
        logger.info(f"  - Squadcast Tenancy: {squadcast_tenancy}")
        logger.info(f"  - Slack Bot Token: {slack_bot_token[:8]}...")
        logger.info(f"  - Squadcast Refresh Token: {sq_ref_token[:8]}...")
        
    except SystemExit as e:
        logger.error("❌ Missing required environment variables")
        return False
    
    # Test 2: Configuration
    logger.info("Testing configuration...")
    try:
        cfg = config.load_config()
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"  - Log level: {cfg.get('sync_settings', {}).get('log_level', 'INFO')}")
        logger.info(f"  - Timeout: {cfg.get('sync_settings', {}).get('timeout_seconds', 30)}s")
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return False
    
    # Test 3: Squadcast API connectivity
    logger.info("Testing Squadcast API connectivity...")
    try:
        squadcast_client = SquadcastClient(sq_ref_token, squadcast_team_id)
        schedules = await squadcast_client.get_schedules()
        logger.info(f"✅ Squadcast API connection successful")
        logger.info(f"  - Found {len(schedules.whoIsOncall)} schedules")
        
        # Check for schedules with slack-usergroup-id tags
        tagged_schedules = []
        for schedule in schedules.whoIsOncall:
            slack_tags = [tag for tag in schedule.schedule.tags if tag.key == "slack-usergroup-id"]
            if slack_tags:
                tagged_schedules.append(schedule.schedule.name)
        
        logger.info(f"  - Schedules with slack-usergroup-id tags: {len(tagged_schedules)}")
        for name in tagged_schedules:
            logger.info(f"    - {name}")
            
    except SquadcastAPIError as e:
        logger.error(f"❌ Squadcast API error: {e.message}")
        return False
    except Exception as e:
        logger.error(f"❌ Squadcast connection error: {e}")
        return False
    
    # Test 4: Slack API connectivity
    logger.info("Testing Slack API connectivity...")
    try:
        slack_client = SlackClient(slack_bot_token)
        
        # Test basic API call
        auth_test = await slack_client.test_auth()
        logger.info(f"✅ Slack API connection successful")
        logger.info(f"  - Bot user: {auth_test.get('user', 'Unknown')}")
        logger.info(f"  - Team: {auth_test.get('team', 'Unknown')}")
        
        # Test user group access
        usergroups = await slack_client.get_user_groups()
        logger.info(f"  - Accessible user groups: {len(usergroups)}")
        
    except SlackAPIError as e:
        logger.error(f"❌ Slack API error: {e.message}")
        return False
    except Exception as e:
        logger.error(f"❌ Slack connection error: {e}")
        return False
    
    logger.info("🎉 All tests passed! Your setup is ready for sync.")
    return True

async def main():
    """Main entry point"""
    try:
        success = await test_setup()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
