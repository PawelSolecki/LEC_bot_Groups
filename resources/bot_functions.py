import os,sys,discord
from discord.ui import View
import models.models as models
import controllers.db as db
import resources.const as const

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

#createView tworzy buttony na dany mecz
def createView(today):
    view = View(timeout = None)
    todaysMatches = db.getTodaysMatches(today)
    for i in range(2):
        view.add_item(models.TeamButton(f'team_1.{i}',i*2,todaysMatches[i].team_1_short, todaysMatches[i].match_id, today))
        view.add_item(models.VsButton(i*2))
        view.add_item(models.TeamButton(f'team_2.{i}',i*2,todaysMatches[i].team_2_short, todaysMatches[i].match_id, today))
        view.add_item(models.ScoreButton(f'20_{i}',(i+1)*2-1,'2:0',todaysMatches[i].match_id,today))
        view.add_item(models.OrButton((i+1)*2-1))
        view.add_item(models.ScoreButton(f'21_{i}',(i+1)*2-1,'2:1',todaysMatches[i].match_id,today))
    view.add_item(models.ResetButton('reset',3,'Reset',today))
    return view

#createVotingMessage zwraca embed dolaczany do wiadomosci z glosowaniem
def createVotingMessage(server,is_bonus, week, day, role):
    title = f"\t\tWeek {week} Day {day}"
    description = ""
    roleToPing = None
    if is_bonus:
        bonus = db.setServerBonus(server,week,day)
        description +=f"**Today bonus:** \n{bonus}\n"
    footer = "To vote just click the buttons below"
    if role != 'None': #jezeli jest rola do pingowania
        roleToPing = "Hi "
        if role == 'everyone':
            roleToPing += f"@{role}"
        else:
            roleToPing += f"<@&{role}>"
        roleToPing += " new voting has just dropped!"

    return f_embed(title, description, const.color_basic,footer),roleToPing

#createVoteEmbedMessage zwraca wiadomosc z glosami usera
def createVoteEmbedMessage(member:discord.member,today):
    users_votes = db.getUserVote(member,today) #[[team,score],[g2,2:1]]
    message = ""
    matches = db.getTodaysMatches(today)
    for i in range(len(matches)): #todays_matches = [team_1_short, team_2_short, match_id]
        if matches[i].team_1_short == users_votes[i][0]:
            message+=f"**{matches[i].team_1_short}** {users_votes[i][1]} {matches[i].team_2_short}\n" #pogrubiamy mecz (**) na który user głosował
        else:
            message+=f"**{matches[i].team_2_short}** {users_votes[i][1]} {matches[i].team_1_short}\n"
    return f_embed("**Your votes:**",message,const.color_basic)

#f_embed funckja zwraca embed
def f_embed(title, description, color,footer=None):
    embed=discord.Embed(title=title, description=description, color=color)
    embed.set_author(name="LEC_Bot", url="https://twitter.com/LEC_bot", icon_url="https://pbs.twimg.com/profile_images/1611378090298449920/FtZ5m_6N_400x400.jpg")
    embed.set_footer(text=footer)
    return embed

#createVotingResultEmbed tworzy i zwraca wiadomosc z wynikami glosowania
def createVotingResultEmbed(server ,today):
    match_details = db.getMatchDetails(today) # [0] = week number, [1] = day number
    title = f"\t\tWeek {match_details[0]} Day {match_details[1]}"
    description =  f"**Server votes (total votes: {countVotes(server,today)}):\n\n**"
    results = {} # okresla glosy na dany team w danym meczu
    for match in db.getTodaysMatches(today):
        results[match.match_id] = {"team_1_short":"","team_1_votes":0,"team_1_20":0,"team_1_21":0, "team_2_short":"", "team_2_votes":0,"team_2_20":0,"team_2_21":0}

    users_string_for_query = "" # okreslenie wszystkich userow servera jako string dla sql IN query
    for user in db.getUsersFromServer(server):
        users_string_for_query += f"{user}, "
    
    
    for match in db.getTodaysMatches(today):
        team_1_votes = db.getAmountOfVotes(users_string_for_query,match.team_1_short,match.match_id)
        team_2_votes = db.getAmountOfVotes(users_string_for_query,match.team_2_short,match.match_id)

        results[match.match_id]["team_1_short"] = match.team_1_short
        results[match.match_id]["team_1_votes"] = team_1_votes[0]
        results[match.match_id]["team_1_20"] = team_1_votes[1]
        results[match.match_id]["team_1_21"] = team_1_votes[2]

        results[match.match_id]["team_2_short"] = match.team_2_short
        results[match.match_id]["team_2_votes"] = team_2_votes[0]
        results[match.match_id]["team_2_20"] = team_2_votes[1]
        results[match.match_id]["team_2_21"] = team_2_votes[2]
    
    for match in results:
        if results[match]["team_1_votes"] + results[match]["team_2_votes"] == 0:
            description+= f"0% - {results[match]['team_1_short']} {10*const.white_square} {results[match]['team_2_short']} - 0%\n\n"
        else:
            #tworzenie pb (bloczki)
            team_1_percent_votes = results[match]["team_1_votes"]/(results[match]["team_1_votes"]+results[match]["team_2_votes"])
            description += f"{round(team_1_percent_votes*100)}% - {results[match]['team_1_short']} "
            description += f"{int(round(team_1_percent_votes*10)) * const.red_square}"
            description += f"{(10 - int(round(team_1_percent_votes*10))) * const.blue_square}"
            description += f" {results[match]['team_2_short']} - {100 - round(team_1_percent_votes*100)}%\n\n"

            #torzenie procentowego dla kazdego wyniku
            total_score_votes = results[match]["team_1_20"] +results[match]["team_1_21"] +results[match]["team_2_20"] +results[match]["team_2_21"]
            description += f"**2:0** {results[match]['team_1_short']} -> {int(round(results[match]['team_1_20']/total_score_votes*100))} % | {results[match]['team_2_short']} -> {int(round(results[match]['team_2_20']/total_score_votes*100))} %\n"
            description += f"**2:1** {results[match]['team_1_short']} -> {int(round(results[match]['team_1_21']/total_score_votes*100))} % | {results[match]['team_2_short']} -> {int(round(results[match]['team_2_21']/total_score_votes*100))} %\n\n"

    return f_embed(title, description, const.color_basic) # zwrocenie gotowego embeda

#countVotes dodajamy do votingMessageResultEmbed zwraca ilosc glosow danego dnia  
def countVotes(server,today):
    match_ids = "" #do zapytania sql
    for match in db.getTodaysMatches(today):
        match_ids += f"{match.match_id}, "
    
    query = db.selectQuery(f"""
    SELECT Servers.server_name, COUNT(DISTINCT(Users_votes.user_id)) FROM Users_votes
    INNER JOIN Users ON Users_votes.user_id = Users.user_id 
    INNER JOIN Servers ON Users.discord_server_id = Servers.discord_server_id
    WHERE match_id IN ({match_ids[:-2]}) AND Servers.discord_server_id = '{server.discord_server_id}'  GROUP BY Servers.server_name
    """)#query zwraca voty danego servera na dany dzien
    return query[0][1]

#createResultsEmbed zwraca embeda z resultami meczy
def createResultsEmbed(matches):
    description = ""
    for match in matches: #przejscie po kazdym meczu, okreslenie winnera i dodanie odpowiedniego description
        match.isWinner()
        if match.winner == match.team_1_short:
            description+=f"**{match.team_1_short}** {match.team_1_score} : {match.team_2_score} {match.team_2_short}\n"
        if match.winner == match.team_2_short:
            description+=f"**{match.team_2_short}** {match.team_2_score} : {match.team_1_score} {match.team_1_short}\n"
        description+=".......................\n"
    return f_embed("TODAY'S  RESULTS:", description, const.color_admin) #zwrocenie gotowego embeda
 
def availableBonusAnswer(bonus_details):
    champions_lower = [i.lower().replace("'", "").replace("&amp;", "&").replace(" ", "") for i in const.champions]
    players_lower = [i.lower().replace(" ","").replace("'", "") for i in const.players]
    games = [str(i) for i in const.games]
    games_with_zero = [str(i) for i in const.games_with_zero]
    print(bonus_details)
    if bonus_details == champions_lower:
        return ", ".join(const.champions)
    elif sorted(bonus_details) == sorted(players_lower):
            return ", ".join(const.players)
    elif bonus_details == const.teams_lower:
        return ", ".join(const.teams)
    elif bonus_details == ['number']:
        return "Number"
    elif bonus_details == games:
        return ", ".join(games)
    elif bonus_details == games_with_zero:
        return ", ".join(games_with_zero)
