"""
Squadcast API Client Module

This module provides a client for interacting with the Squadcast API,
specifically for retrieving on-call schedules and related information.
"""

from typing import Any, List, Union, Optional
from typing_extensions import Annotated
import logging
import httpx
import env
from pydantic import BaseModel, Discriminator, Tag as ATag, Field

# Configure logger
logger = logging.getLogger(__name__)

# Use the default as eu.squadcast.com for eu tenancy
squadcast_tenancy = env.get("SQUADCAST_TENANCY", default="squadcast.com")

class SquadcastAPIError(Exception):
    """Exception raised when Squadcast API returns an error"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class Tag(BaseModel):
    """
    Represents a tag associated with a Squadcast entity
    """
    key: str = Field(description="The tag key")
    value: str = Field(description="The tag value")


class Schedule(BaseModel):
    """
    Represents a Squadcast schedule with basic information
    """
    ID: int = Field(description="Unique identifier for the schedule")
    name: str = Field(description="Name of the schedule")
    tags: List[Tag] = Field(description="List of tags associated with the schedule")
    teamID: str = Field(description="ID of the team that owns the schedule")
    paused: bool = Field(description="Whether the schedule is paused")


class User(BaseModel):
    """
    Represents a Squadcast user
    """
    ID: str = Field(description="Unique identifier for the user")
    name: str = Field(description="User's name")
    firstName: str = Field(description="User's first name")
    lastName: str = Field(description="User's last name")
    email: str = Field(description="User's email address")


class Squad(BaseModel):
    """
    Represents a Squadcast squad (team of users)
    """
    ID: str = Field(description="Unique identifier for the squad")
    name: str = Field(description="Name of the squad")
    members: List[User] = Field(description="List of users in the squad")


def user_or_squad(data: Any) -> str:
    """
    Discriminator function to determine if a participant is a user or squad
    
    Args:
        data: The participant data to check
        
    Returns:
        "squad" if the data has a members field, "user" otherwise
    """
    if "members" in data:
        return "squad"
    return "user"


class Participant(BaseModel):
    """
    Represents a participant in an on-call rotation,
    which can be either an individual user or a squad
    """
    ID: str = Field(description="Unique identifier for the participant")
    type: str = Field(description="Type of participant (user or squad)")
    participant: Annotated[
        Union[
            Annotated[User, ATag("user")],
            Annotated[Squad, ATag("squad")],
        ],
        Discriminator(user_or_squad),
    ] = Field(description="The actual participant data (either a User or Squad)")


class OncallSchedule(BaseModel):
    """
    Represents a Squadcast on-call schedule with its participants
    """
    schedule: Schedule = Field(description="Schedule details")
    oncallParticipants: List[Participant] = Field(description="List of participants currently on-call")

    def get_user_emails(self) -> List[str]:
        """
        Extract email addresses of all users currently on-call in this schedule
        
        This handles both individual users and squads (groups of users)
        
        Returns:
            A list of email addresses for all on-call users
        """
        emails = []
        for op in self.oncallParticipants:
            if isinstance(op.participant, User):
                emails.append(op.participant.email)
            else:
                for mem in op.participant.members:
                    emails.append(mem.email)
        
        logger.info(f"Gathered {len(emails)} emails for schedule {self.schedule.name}")
        logger.debug(f"Email list for schedule {self.schedule.name}: {emails}")
        return emails


class WhoIsOncall(BaseModel):
    """
    Represents the response from the Squadcast whoIsOncall API endpoint
    """
    whoIsOncall: List[OncallSchedule] = Field(description="List of on-call schedules with their participants")


class SquadcastClient(httpx.AsyncClient):
    """
    Client for interacting with the Squadcast API using async HTTP requests.
    
    This class handles authentication and provides methods for retrieving
    on-call schedules and other Squadcast-related operations.
    """
    refresh_token: str
    access_token: str
    team_id: str
    timeout_seconds: int = 30

    def __init__(self, refresh_token: str, team_id: str, timeout: int = None) -> None:
        """
        Initialize the Squadcast client with authentication tokens and team ID.
        
        Args:
            refresh_token: The Squadcast refresh token used to obtain access tokens
            team_id: The ID of the Squadcast team to work with
            timeout: Optional request timeout in seconds
            
        Raises:
            SquadcastAPIError: If authentication fails
        """
        self.refresh_token = refresh_token
        self.team_id = team_id
        if timeout:
            self.timeout_seconds = timeout

        logger.info(f"Initializing Squadcast client for team ID: {team_id}")
        
        try:
            # Get the access token using the refresh token
            auth_url = f"https://auth.{squadcast_tenancy}/oauth/access-token"
            logger.debug(f"Requesting access token from {auth_url}")
            
            auth_resp = httpx.get(
                auth_url,
                headers={"X-Refresh-Token": refresh_token},
                timeout=self.timeout_seconds
            )

            if auth_resp.status_code != 200:
                error_msg = f"Failed to fetch access token: expected 200, got {auth_resp.status_code}"
                logger.error(error_msg)
                raise SquadcastAPIError(
                    error_msg,
                    status_code=auth_resp.status_code,
                    response=auth_resp.json() if auth_resp.headers.get("content-type") == "application/json" else None
                )

            self.access_token = auth_resp.json()["data"]["access_token"]
            logger.debug("Successfully obtained access token")
            
            # Initialize the HTTP client
            api_base_url = f"https://api.{squadcast_tenancy}"
            logger.info(f"Using Squadcast API base URL: {api_base_url}")
            super().__init__(
                auth=self.auth, 
                base_url=api_base_url,
                timeout=httpx.Timeout(self.timeout_seconds)
            )
        except httpx.HTTPError as e:
            logger.exception(f"HTTP error during client initialization: {e}")
            raise SquadcastAPIError(f"Failed to initialize Squadcast client: {str(e)}")

    def auth(self, request: httpx.Request) -> httpx.Request:
        """
        Add authentication header to outgoing requests.
        
        Args:
            request: The HTTP request to modify
            
        Returns:
            The HTTP request with added authorization header
        """
        request.headers["Authorization"] = f"Bearer {self.access_token}"
        return request

    async def get_schedules(self) -> WhoIsOncall:
        """
        Retrieve the current on-call schedules and participants for the team.
        
        Returns:
            A WhoIsOncall object containing the schedules and participants
            
        Raises:
            SquadcastAPIError: If the API returns an error
        """
        logger.info(f"Retrieving on-call schedules for team {self.team_id}")
        
        # GraphQL query for the whoIsOncall API endpoint
        graphql_query = """query whoIsOncall($filters: WhoIsOncallFilters) {
	whoIsOncall(filters: $filters) {
		schedule {
			ID
			name
			paused
			tags {
				key
				value
			}
			teamID
		}
		oncallParticipants {
			ID
			type
			participant {
				... on User {
					ID
					name
					firstName
					lastName
					email
				}
				... on Squad {
					ID
					name
					members {
						ID
						name
                        firstName
                        lastName
						email
					}
				}
			}
		}
	}
}
"""
        query = {
            "query": graphql_query,
            "variables": {"filters": {"teamID": self.team_id}},
        }

        try:
            logger.debug("Sending GraphQL query to Squadcast API")
            resp = await self.post("/v3/graphql", json=query)
            body = resp.json()

            if resp.status_code != 200:
                error_msg = body.get("meta", {}).get("error_message", "Unknown error")
                logger.error(f"API error: {error_msg}")
                raise SquadcastAPIError(
                    f"Failed to retrieve schedules: {error_msg}",
                    status_code=resp.status_code,
                    response=body
                )

            logger.info(f"Successfully retrieved on-call schedules")
            schedules = WhoIsOncall(**body["data"])
            logger.debug(f"Retrieved {len(schedules.whoIsOncall)} schedules")
            return schedules
            
        except httpx.HTTPError as e:
            logger.exception(f"HTTP error when retrieving schedules: {e}")
            raise SquadcastAPIError(f"Failed to retrieve schedules: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error when retrieving schedules: {e}")
            raise SquadcastAPIError(f"Failed to retrieve schedules: {str(e)}")
