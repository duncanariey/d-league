import requests
import datetime

teams_api = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
summary_api = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
scoreboard_api = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"


# retrieves the id of each active team and returns them as a list
def get_team_ids():
    team_list = []
    teams_api_response = (requests.get(url=teams_api)).json()
    for t in teams_api_response['sports'][0]['leagues'][0]['teams']:
        team_list.append(int(t["team"]["id"]))
    print("Finished gathering team ids")
    return team_list


# accepts a list of team ids and retrieves the conference and division of each team,
# then returns a data structure to represent the league
def build_league(teams):
    league_structure = {}
    for team in teams:
        team_info = (requests.get(url=f'{teams_api}/{team}')).json()
        conference = team_info["team"]["groups"]["parent"]["id"]
        division = team_info["team"]["groups"]["id"]
        team_id = team_info["team"]["id"]
        league_structure.setdefault(conference, {})
        league_structure[conference].setdefault(division, [])
        league_structure[conference][division].append(int(team_id))
    print("Finished building league structure")
    return league_structure


# accepts a week of the 2022 NFL season and returns the days that comprise that week,
# formatted as ESPN expects in YYYYMMDD
def get_specific_week(week_number):
    days = []
    for days_forward in range(7):
        day = (datetime.date(2022, 9, 8) + datetime.timedelta(days=(days_forward + (week_number-1)*7))).strftime('%Y%m%d')
        days.append(day)
    return days


# accepts a list of dates in the YYYYMMDD format, retrieves the calendar of games played on each of those dates,
# and returns the ids of those games as a list
def get_list_of_games(dates):
    games = []
    for x in dates:
        calendar_response = (requests.get(url=scoreboard_api, params={'dates': str(x)})).json()
        if calendar_response["events"]:
            for game in calendar_response["events"]:
                games.append(game["id"])
    print("Finished gathering games")
    return games


# accepts a game id, retrieves the details about that game, calculates the win probability range,
# and returns a dictionary of that data
def get_game_details(game):
    games_details = {}
    try:
        summary = (requests.get(url=summary_api, params={"event": game})).json()
        team_1_id = summary['boxscore']['teams'][0]['team']['id']
        team1_display_name = summary['boxscore']['teams'][0]['team']['displayName']
        team_2_id = summary['boxscore']['teams'][1]['team']['id']
        team2_display_name = summary['boxscore']['teams'][1]['team']['displayName']
        probabilities = []
        for prob in summary["winprobability"]:
            probabilities.append(prob["homeWinPercentage"])
        win_prob_range = max(probabilities) - min(probabilities)
        win_prob_sum_delta = 0
        for x in range(len(probabilities)-1):
            win_prob_sum_delta += abs(probabilities[x]-probabilities[x+1])
        games_details.update({
            'Team 1 id': int(team_1_id),
            'Team 1 display name': team1_display_name,
            'Team 2 id': int(team_2_id),
            'Team 2 display name': team2_display_name,
            'Win probability range': win_prob_range,
            'Win probability sum deltas': win_prob_sum_delta,
        })
        print(f"finished organizing game {game}")
        return games_details
    except KeyError:
        print(f"something went wrong, game {game} did not have an expected param. It may not have been played yet.")


# accepts a list of game ids, retrieves each game's details, and returns a list of dictionaries of those details
def organize_game_details(games):
    games_details = []
    for game in games:
        games_details.append(get_game_details(game))
    return games_details


# accepts a data structure representing the league, and a list of dictionaries of game details,
# iterates over both to calculate the average win likelihood range for each division,
# and prints the results
def assign_probabilities_to_divisions(league, games_details):
    for conference in league.values():
        for division in conference.values():
            team_names = []
            win_percentage = 0
            number_of_teams = 0
            sum_delta = 0
            for team in division:
                for game in games_details:
                    if team == game['Team 1 id']:
                        team_names.append(game['Team 1 display name'])
                        win_percentage += game['Win probability range']
                        number_of_teams += 1
                        sum_delta += game['Win probability sum deltas']
                    if team == game['Team 2 id']:
                        team_names.append(game['Team 2 display name'])
                        win_percentage += game['Win probability range']
                        number_of_teams += 1
                        sum_delta += game['Win probability sum deltas']
            team_names_string = ""
            if team_names:
                for team in range(len(team_names)-1):
                    team_names_string += f"the {team_names[team]}, "
                team_names_string += f"and the {team_names[-1]}"
                print(f"The division that contains {team_names_string} had an average win probability range of {win_percentage / number_of_teams} and an average win probability sum delta of {sum_delta}")


new_week = input("Which week would you like to calculate win probability ranges for? "
                 "Week 1 is the week that started on 9/8\n")
assign_probabilities_to_divisions(build_league(get_team_ids()), organize_game_details(get_list_of_games(get_specific_week(int(new_week)))))
