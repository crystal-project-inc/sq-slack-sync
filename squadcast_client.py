from typing import Any, List, Union
from typing_extensions import Annotated
import httpx
import env
from pydantic import BaseModel, Discriminator, Tag as ATag

# use the default as eu.squadcast.com for eu tenancy
squadcast_tenancy = env.get("SQUADCAST_TENANCY", default="squadcast.com")

class Tag(BaseModel):
    key: str
    value: str

class Schedule(BaseModel):
    ID: int
    name: str
    tags: List[Tag]
    teamID: str
    paused: bool

class User(BaseModel):
    ID: str
    name: str
    firstName: str
    lastName: str
    email: str

class Squad(BaseModel):
    ID: str
    name: str
    members: List[User]

def user_or_squad(data: Any) -> str:
    if "members" in data:
        return "squad"
    return "user"

class Participant(BaseModel):
    ID: str
    type: str
    participant: Annotated[
        Union[
            Annotated[User, ATag("user")],
            Annotated[Squad, ATag("squad")],
        ],
        Discriminator(user_or_squad),
    ]

class OncallSchedule(BaseModel):
    schedule: Schedule
    oncallParticipants: List[Participant]

    def get_user_emails(self) -> List[str]:
        emails = []
        for op in self.oncallParticipants:
            if isinstance(op.participant, User):
                emails.append(op.participant.email)
            else:
                for mem in op.participant.members:
                    emails.append(mem.email)
        return emails

class WhoIsOncall(BaseModel):
    whoIsOncall: List[OncallSchedule]

class SquadcastClient(httpx.AsyncClient):
    refresh_token: str
    access_token: str
    team_id: str
    
    def __init__(self, refresh_token: str, team_id: str) -> None:
        self.refresh_token = refresh_token
        self.team_id = team_id

        auth_resp = httpx.get(
            f"https://auth.{squadcast_tenancy}/oauth/access-token",
            headers={"X-Refresh-Token": refresh_token}
        )

        if auth_resp.status_code != 200:
            raise Exception(f"fetch access token: expected 200, got {auth_resp.status_code}")
        
        self.access_token = auth_resp.json()["data"]["access_token"]

        super().__init__(auth=self.auth, base_url=f"https://api.{squadcast_tenancy}")

    def auth(self, request: httpx.Request) -> httpx.Request:
        request.headers["Authorization"] = f"Bearer {self.access_token}"
        return request
    
    async def get_schedules(self) -> (WhoIsOncall | Exception):
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
            "query" : graphql_query,
            "variables" : {
                "filters" : {
                    "teamID": self.team_id
                }
            }
        }

        resp = (await self.post("/v3/graphql", json=query))
        body = resp.json()

        if resp.status_code != 200:
            return Exception({
                "status" : resp.status_code,
                "error": body["meta"]["error_message"]
            })

            
        schresp = WhoIsOncall(**body["data"])
        return schresp
