from __future__ import annotations
from typing import List
import httpx
from pydantic import BaseModel
from typing import List


class Profile(BaseModel):
    phone: str
    real_name: str
    display_name: str
    email: str
    huddle_state: str
    huddle_state_expiration_ts: int
    first_name: str
    last_name: str
    team: str

class User(BaseModel):
    id: str
    team_id: str
    name: str
    deleted: bool
    color: str
    real_name: str
    tz: str
    tz_label: str
    tz_offset: int
    profile: Profile
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    is_bot: bool
    is_app_user: bool
    updated: int
    is_email_confirmed: bool
    who_can_share_contact_card: str

class SlackClient(httpx.AsyncClient):
    bot_token: str
    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token

        super().__init__(auth=self.auth, base_url="https://slack.com/api")

    def auth(self, request: httpx.Request) -> httpx.Request:
        request.headers["Authorization"] = f"Bearer {self.bot_token}"
        return request

    async def get_user_by_email(self, email: str) -> (User | Exception):
        resp = (await self.get("/users.lookupByEmail", params={
            "email": email
        })).json()

        if not resp["ok"]:
            return Exception({
                "status": 200,
                "error": resp["error"]
            })
        
        return User(**resp["user"])

    async def update_user_group(self, groupid: str, user_ids: List[str], dry_run=False) -> (None | Exception):
        if dry_run:
            print(f"Updating user group with ID: {groupid} with members: {user_ids}")
            return

        resp = (await self.post("/usergroups.users.update", json={
            "usergroup": groupid,
            "users": user_ids,
        })).json()

        if not resp["ok"]:
            return Exception({
                "status": 200,
                "error": resp["error"]
            })

        return
