from __future__ import annotations
from typing import List, Optional, Union
import logging
import httpx
from pydantic import BaseModel, Field
from typing import List

# Configure logger
logger = logging.getLogger(__name__)

class SlackAPIError(Exception):
    """Exception raised when Slack API returns an error"""
    
    def __init__(self, message: str, error_code: str = None, response: dict = None):
        self.message = message
        self.error_code = error_code
        self.response = response
        super().__init__(self.message)


class Profile(BaseModel):
    """
    Represents a Slack user profile with essential information
    """
    phone: str = Field(description="User's phone number")
    real_name: str = Field(description="User's real name")
    display_name: str = Field(description="User's display name")
    email: str = Field(description="User's email address")
    huddle_state: str = Field(description="User's huddle state")
    huddle_state_expiration_ts: int = Field(description="Expiration timestamp for huddle state")
    first_name: str = Field(description="User's first name")
    last_name: str = Field(description="User's last name")
    team: str = Field(description="User's team ID")


class User(BaseModel):
    """
    Represents a Slack user with comprehensive details
    """
    id: str = Field(description="User's unique identifier")
    team_id: str = Field(description="User's team ID")
    name: str = Field(description="User's name in Slack")
    deleted: bool = Field(description="Whether the user has been deleted")
    color: str = Field(description="User's color preference")
    real_name: str = Field(description="User's real name")
    tz: str = Field(description="User's timezone")
    tz_label: str = Field(description="User's timezone label")
    tz_offset: int = Field(description="User's timezone offset")
    profile: Profile = Field(description="User's profile details")
    is_admin: bool = Field(description="Whether the user is an admin")
    is_owner: bool = Field(description="Whether the user is a workspace owner")
    is_primary_owner: bool = Field(description="Whether the user is the primary workspace owner")
    is_restricted: bool = Field(description="Whether the user has restricted access")
    is_ultra_restricted: bool = Field(description="Whether the user has ultra restricted access")
    is_bot: bool = Field(description="Whether the user is a bot")
    is_app_user: bool = Field(description="Whether the user is an application user")
    updated: int = Field(description="Last updated timestamp")
    is_email_confirmed: bool = Field(description="Whether the user's email is confirmed")
    who_can_share_contact_card: str = Field(description="Who can share this user's contact card")


class SlackClient(httpx.AsyncClient):
    """
    Client for interacting with the Slack API using async HTTP requests.
    
    This class handles authentication and provides methods for common Slack API operations
    related to user lookup and user group management.
    """
    bot_token: str
    base_api_url: str = "https://slack.com/api"
    timeout_seconds: int = 30

    def __init__(self, bot_token: str, base_url: str = None, timeout: int = None) -> None:
        """
        Initialize the Slack client with authentication token and optional configuration.
        
        Args:
            bot_token: The Slack bot token used for API authentication
            base_url: Optional custom base URL for the Slack API
            timeout: Optional request timeout in seconds
        """
        self.bot_token = bot_token
        if base_url:
            self.base_api_url = base_url
        if timeout:
            self.timeout_seconds = timeout

        logger.info(f"Initializing Slack client with base URL: {self.base_api_url}")
        super().__init__(
            auth=self.auth, 
            base_url=self.base_api_url, 
            timeout=httpx.Timeout(self.timeout_seconds)
        )

    def auth(self, request: httpx.Request) -> httpx.Request:
        """
        Add authentication header to outgoing requests.
        
        Args:
            request: The HTTP request to modify
            
        Returns:
            The HTTP request with added authorization header
        """
        request.headers["Authorization"] = f"Bearer {self.bot_token}"
        return request

    async def get_user_by_email(self, email: str) -> User:
        """
        Look up a Slack user by their email address.
        
        Args:
            email: The email address of the user to look up
            
        Returns:
            A User object containing the user's details
            
        Raises:
            SlackAPIError: If the API returns an error or the user is not found
        """
        logger.debug(f"Looking up Slack user with email: {email}")
        try:
            response = await self.get("/users.lookupByEmail", params={"email": email})
            resp_data = response.json()

            if not resp_data.get("ok", False):
                error_msg = resp_data.get("error", "Unknown error")
                logger.error(f"Failed to look up user by email: {error_msg}")
                raise SlackAPIError(
                    f"Failed to look up user by email: {error_msg}",
                    error_code=error_msg,
                    response=resp_data
                )

            return User(**resp_data["user"])
        except httpx.HTTPError as e:
            logger.exception(f"HTTP error when looking up user by email: {e}")
            raise SlackAPIError(f"HTTP error when looking up user by email: {str(e)}")

    async def update_user_group(
        self, groupid: str, user_ids: List[str]
    ) -> None:
        """
        Update the members of a Slack user group.
        
        Args:
            groupid: The ID of the user group to update
            user_ids: List of user IDs to add to the group
            
        Returns:
            None on success
            
        Raises:
            SlackAPIError: If the API returns an error
        """
        logger.info(f"Updating user group {groupid} with {len(user_ids)} members")
        
        headers = {"Content-Type": "application/json; charset=utf-8"}

        try:
            response = await self.post(
                "/usergroups.users.update",
                json={
                    "usergroup": groupid,
                    "users": user_ids,
                },
                headers=headers,
            )
            resp_data = response.json()

            if not resp_data.get("ok", False):
                error_msg = resp_data.get("error", "Unknown error")
                logger.error(f"Failed to update user group: {error_msg}")
                raise SlackAPIError(
                    f"Failed to update user group: {error_msg}",
                    error_code=error_msg,
                    response=resp_data
                )

            logger.info(f"Successfully updated user group {groupid}")
            return
        except httpx.HTTPError as e:
            logger.exception(f"HTTP error when updating user group: {e}")
            raise SlackAPIError(f"HTTP error when updating user group: {str(e)}")
