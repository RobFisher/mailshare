# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import settings
from mailshareapp.models import Contact

class Team(object):
    def __init__(self, name, address):
        self.name = name
        self.address = address
        matching_contacts = Contact.objects.filter(address__iexact=self.address)
        if len(matching_contacts) > 0:
            self.contact_id = matching_contacts[0].id
        else:
            self.contact_id = -1


team_names = settings.MAILSHARE_TEAMS.keys()
team_names.sort()
teams = []
teams_by_contact_id = {}

for team_name in team_names:
    team = Team(team_name, settings.MAILSHARE_TEAMS[team_name])
    teams.append(team)
    teams_by_contact_id[team.contact_id] = team
