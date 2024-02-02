import asyncio
import env
from slack_client import SlackClient
from squadcast_client import SquadcastClient

sq_ref_token = env.get("SQUADCAST_REFRESH_TOKEN")
squadcast_team_id = env.get("SQUADCAST_TEAM_ID")
slack_bot_token = env.get("SLACK_BOT_TOKEN")

async def main():
    sqc = SquadcastClient(sq_ref_token, squadcast_team_id)
    slc = SlackClient(slack_bot_token)

    print(f"trying to get schedules state of {squadcast_team_id}")
    scres = await sqc.get_schedules()
    if isinstance(scres, Exception):
        print(scres)
        exit(2)

    for schedule_state in scres.whoIsOncall:
        slack_tags = list(
            filter(
                lambda tag: tag.key == "slack-usergroup-id",
                schedule_state.schedule.tags
            )
        )
        # If the slack-tags (slack-usergroup-id) is not set skip the member sync
        if len(slack_tags) != 1:
            print(f"skipping schedule {schedule_state.schedule.name} as no slack usergroup id tag is found")
            continue
        
        slack_usergroup_id = slack_tags[0].value
        
        print(f"syncing for {schedule_state.schedule.name} with team id {slack_usergroup_id}")

        user_emails = schedule_state.get_user_emails()
        slack_user_ids = []
        print(f"gathering slack ids for {user_emails}")
        
        # For all the users, get the user IDs
        for email in user_emails:
            slack_user = await slc.get_user_by_email(email)
            if isinstance(slack_user, Exception):
                print(scres)
                exit(2)
            slack_user_ids.append(slack_user.id)
        print(f"gathered slack ids {slack_user_ids}")
        # Update the usergroup with the new members
        d = await slc.update_user_group(
            slack_usergroup_id,
            slack_user_ids,
        )
        if d is None:
            print(f"slack user group member update succeeded {schedule_state.schedule.name}, {slack_usergroup_id}")
            continue
        else:
            print(f"slack user group member update failed {schedule_state.schedule.name}, {slack_usergroup_id}")
            print(f"\t\t{d}")
            exit(2)

asyncio.run(main())
