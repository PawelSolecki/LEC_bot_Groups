import discord
import mysql.connector,os,sys
from mysql.connector import Error

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import models.models as models
import resources.const as const
import resources.secret_file as secret

def createDatabaseConnection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=secret.db_host,
            user=secret.db_user,
            passwd=secret.db_passwd,
            database=secret.db_database
        )
       
    except Error as err:
        print(f"Error: '{err}'")
    return connection

def insertQuery(query):
    connection = createDatabaseConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
    except Error as err:
        print(f"Error: '{err}'")
        
def selectQuery(query):
    connection = createDatabaseConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Error as err:
        print(f"Error: '{err}'")

def existQuery(query):
    connection = createDatabaseConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchone()[0] == 1
    except Error as err:
        print(f"Error: '{err}'")

#createUser tworzy usera jezeli nie ma w tabeli/tabelach
def createUser(member:discord.Member):
    query = selectQuery(f"SELECT discord_user_id, discord_server_id FROM Users") #pobranie usera z tabeli Users
    
    for tuple_number in range(len(query)): #zmiana typow id z stringow na inty
        query[tuple_number] = list(map(int,list(query[tuple_number])))
    
    if [member.id,member.guild.id] in query: #jezli jest jest user to konczymy funckcje
        return True
     
    query = selectQuery(f"SELECT discord_user_id FROM Discord_users")#jezeli nie ma w tabeli Users to sprawdzamy czy glosowal na innym serwerze czyli
                                                                     #czyli czy jest w tabeli Discord_users
    
     #query = [(/tuple\),(/tuple\)] # tak wyglada struktura query
    for tuple_number in range(len(query)): #zmiana typow id z stringow na inty
        query[tuple_number] = list(map(int,list(query[tuple_number])))

    if [member.id] in query: #jezeli user jest w Discord_users do dodajemy go do tabeli Users i konczymy funckje 
        insertQuery(f"INSERT INTO Users (discord_user_id, discord_server_id) VALUES ('{member.id}', '{member.guild.id}')")
        insertQuery(f"INSERT INTO Users_points(user_id, points, answer_amount) VALUES ({getUserIdFromUsers(member.guild.id, member.id)} , 0, 0)")
        return True
 
    #jezeli nie ma w zadnej z tabel to dodajemy do obu
    insertQuery(f"INSERT INTO Discord_users (discord_user_id, user_name, user_discord_tag) VALUES ('{member.id}', '{member.name}', {member.discriminator})")
    insertQuery(f"INSERT INTO Users (discord_server_id, discord_user_id) VALUES ('{member.guild.id}', '{member.id}')")
    insertQuery(f"INSERT INTO Users_points(user_id, points, answer_amount) VALUES ({getUserIdFromUsers(member.guild.id, member.id)} , 0, 0)")
    return True

#getDates zwraca wszystkie dni jakie graja
def getDates():
    query = "SELECT DISTINCT date FROM Matches ORDER BY date" #pobieranie z db dat bez powtorzen (powtorzen i tak nie ma bo jest godzina (jednak chyba nie ma))
    dates = []
    for i in selectQuery(query): #dodanie dat juz bez godziny do tabeli
        dates.append(i[0])
    dates = list(dict.fromkeys(dates)) # usuniecie powtorzen w tabeli
    return dates

#getTodaysMatches zwraca modele dzisiejszych meczy
def getTodaysMatches(today):
    query = f"SELECT match_id, team_1, team_2, winner, team_1_score, team_2_score, match_day, match_week, date FROM Matches WHERE date = '{today}'" #pobieranie skrotowych nazw teamow danego dnia
    matches = []

    for i in selectQuery(query): #tworznie listy 2d z [team_1_short,team_2_short,match_id]
        matches.append(models.Match(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],None,today)) #nieoptymalne rozwiaznanie ~ Marcel Bączyński 21.12.2022 4:20 #zapytac Senior dev (Maksym B.) o lepsze rozwiazanie
    return matches
    
#getMatchDetails zwraca match_week i match_day zaleznia od podanego today.
def getMatchDetails(today):
    query = f"SELECT match_week, match_day FROM Matches WHERE date = '{today}' LIMIT 1"
    return selectQuery(query)[0][0], selectQuery(query)[0][1]

#getServers zwraca wszystkie serwery
def getServers(): #tworzenie listy obiekot klasy server
    query = "SELECT discord_server_id, server_name, channel, role_id, is_bonus, voting_message_id FROM Servers" #pobieranie z server_id z bazy danych
    servers = []
    for i in selectQuery(query): #dodanie serverow do listy
        servers.append(models.Server(i[0],i[1],i[2],i[3],i[4],i[5]))
    return servers

#getUserIdFromUsers zwraca id z tabeli user na podstawie discord i user id
def getUserIdFromUsers(discord_guild_id,discord_user_id):
    query =  selectQuery(f"SELECT user_id FROM Users WHERE discord_server_id ='{discord_guild_id}' AND discord_user_id = '{discord_user_id}'")
    if query==[]:
        return False
    return int(query[0][0])

#insertTeamVote dodaje glosc uzytkownika(team) do db
def insertTeamVote(member, match_id,team):
    if existQuery(f"SELECT EXISTS (SELECT team_vote FROM Users_votes WHERE match_id = {match_id} AND user_id = {getUserIdFromUsers(member.guild.id, member.id)})"):
        return True #jezeli user juz glosowal to zwracamy true
    insertQuery(f"INSERT INTO Users_votes(user_id, match_id, team_vote) VALUES ({getUserIdFromUsers(member.guild.id, member.id)}, {match_id}, '{team}')")#jezeli nie to dodajemy

#insertScoreVote dodaje glosc uzytkownika(score) do db
def insertScoreVote(member, match_id, score):
    if existQuery(f"SELECT EXISTS (SELECT team_vote FROM Users_votes WHERE match_id = {match_id} AND user_id = {getUserIdFromUsers(member.guild.id, member.id)})"):
        if existQuery(f"SELECT EXISTS (SELECT score_vote FROM Users_votes WHERE match_id = {match_id} AND user_id = {getUserIdFromUsers(member.guild.id, member.id)} AND score_vote IS NOT NULL)"):
            return True #jezeli user juz glosowal to zwracamy true
        insertQuery(f"UPDATE Users_votes SET score_vote = '{score}' WHERE user_id = {getUserIdFromUsers(member.guild.id, member.id)} AND match_id = {match_id}")
    else:
        return True  

def isVoteForAll(member, today):
    matches = getTodaysMatches(today)
    if len(selectQuery(f"""SELECT team_vote,score_vote FROM Users_votes 
    WHERE user_id = {getUserIdFromUsers(member.guild.id,member.id)} 
    AND match_id IN ({matches[0].match_id},{matches[1].match_id}) 
    AND score_vote IS NOT NULL"""))==2:
        return True

#deleteVote usuwa voty usera na dany mecz
def deleteVote(member:discord.Member,today):
    matches = getTodaysMatches(today)
    insertQuery(f"DELETE FROM Users_votes WHERE user_id = '{getUserIdFromUsers(member.guild.id, member.id)}' AND match_id IN ({matches[0].match_id},{matches[1].match_id})")

#getUserVote zwraca glosy usera jako lista
def getUserVote(member:discord.member,today):
    matches = getTodaysMatches(today)
    users_votes  =[]
    for team in selectQuery(f"SELECT team_vote,score_vote FROM Users_votes WHERE user_id = '{getUserIdFromUsers(member.guild.id, member.id)}' AND match_id IN ({matches[0].match_id},{matches[1].match_id})"):
        users_votes.append([team[0],team[1]])
    return users_votes #[[team,score],[g2,2:1]]

#getAmountOfVotes zwraca ilosc glosow na dany team / mecz uzytkownikow z danego servera
def getAmountOfVotes(users,team_short,match_id):
    if users == "":
        return 0
    team_votes = selectQuery(f"SELECT COUNT(team_vote) FROM Users_votes WHERE team_vote = '{team_short}' AND user_id IN ({users[:-2]}) AND match_id={match_id}")[0][0]
    score_vote_20 = selectQuery(f"SELECT COUNT(score_vote) FROM Users_votes WHERE team_vote = '{team_short}' AND score_vote = '2:0' AND user_id IN ({users[:-2]}) AND match_id={match_id}")[0][0]
    score_vote_21 = selectQuery(f"SELECT COUNT(score_vote) FROM Users_votes WHERE team_vote = '{team_short}' AND score_vote = '2:1' AND user_id IN ({users[:-2]}) AND match_id={match_id}")[0][0]
    return team_votes, score_vote_20, score_vote_21

#getUsersFromServer zwraca wszystkich userow z danego serwera
def getUsersFromServer(server):
    users = []
    for user in selectQuery(f"SELECT user_id FROM Users WHERE discord_server_id = '{server.discord_server_id}'"):  #selectQuery zwraca: [(user_id,)(user_id,))]
        users.append(user[0])
    return users
    
#updateMatchWinner uzywamy głownie w modelsach, zmienia winnera meczu
def updateMatchWinner(match):
    insertQuery(f"UPDATE Matches SET winner = '{match.winner}', team_1_score = '{match.team_1_score}', team_2_score = '{match.team_2_score}' WHERE match_id = {match.match_id}")

#getUserAnswersAmountToday sprawdz czy user odpowiedzial zwraca 1 jezeli tak w przeciwnym wypadku 0 
def getUserAnswersAmountToday(match, user):
    return selectQuery(f"SELECT COUNT(user_id) FROM Users_votes WHERE user_id = {user} AND match_id ={match.match_id}")[0][0]
   
#updatePoints updatuje pointsy (wywolywane jest po zamknieciu glosowania)
def updatePoints(matches,server): 
    users_array = getUsersFromServer(server) # uzytkownicy z servera
    users_points_dict= getUsersPointsAndAnswersAmount(server)[0] #pointsy uzytkowanikow z servera
    users_answers_amount_dict= getUsersPointsAndAnswersAmount(server)[1] # answer_amount uzytkownikow z servera
    users="" # do sql IN query

    for user in users_array:
        users+=f"{user}, " # do sql IN query

    if users == "":
        return
        
    for match in matches: #przejscie po kazdym dzisiejszym meczu i przejscie po wszystkich dobrych glosach uzytkownikow wraz z dodaniem im punktow
        if int(match.team_1_score) > int(match.team_2_score):
            score = match.team_1_score + ":" + match.team_2_score
        else:
            score = match.team_2_score + ":" + match.team_1_score
        for user in selectQuery(f"SELECT user_id FROM Users_votes WHERE team_vote = '{match.winner}' AND user_id IN ({users[:-2]}) AND match_id = {match.match_id}"):
            if score == selectQuery(f"SELECT score_vote FROM Users_votes WHERE user_id = {user[0]} AND match_id = {match.match_id}")[0][0]:
                users_points_dict[user[0]] += 3
            else:
                users_points_dict[user[0]] += 1
            
        for user in users_array: # to samo co wyzej tylko dla anser_amount
            users_answers_amount_dict[user] += getUserAnswersAmountToday(match, user)
        
    for user in users_points_dict: # update pointsow i answer_amount w db
        insertQuery(f"UPDATE Users_points SET points = {users_points_dict[user]}, answer_amount = {users_answers_amount_dict[user]} WHERE user_id = {user}")

#getUsersPointsAndAnswersAmount zwraca słowniki z aktualnymi punktami i liczba odpowidzi usera
def getUsersPointsAndAnswersAmount(server):
    users_array = getUsersFromServer(server) #sciaganie glosujacych uzytkownikow servera
    users_points_dict={} #dict do pointsow
    users_answers_amount_dict = {} #dict do liczby odpowiedzi
    users=""
    for user in users_array:
        users +=f"{user}, " #zmiana array na stringa do query

    if users == "": #jezli nie ma userow do puste dicty
        return users_points_dict, users_answers_amount_dict

    #selectQuery zwraca [(user_id,points),(user_id,points)] / [(user_id,liczba_odpowiedzi),(user_id,liczba_odpowiedzi)]
    for user in selectQuery(f"SELECT user_id, points FROM Users_points WHERE user_id IN({users[:-2]})"): #tworzenie slownika z kazdym uzytkownikiem i pointsami
        users_points_dict[user[0]] = user[1]
        
    for user in selectQuery(f"SELECT user_id, answer_amount FROM Users_points WHERE user_id IN({users[:-2]})"): #tworzenie slownika z kazdym uzytkownikiem i liczba głosów
        users_answers_amount_dict[user[0]] = user[1]
    
    return users_points_dict, users_answers_amount_dict

#getServerById zwraca model Server na podstawie discord'owego id
def getServerById(discord_server_id): 
    query =  selectQuery(f"SELECT * FROM Servers WHERE discord_server_id = '{discord_server_id}'")
    return models.Server(query[0][0],query[0][2],query[0][4],query[0][1],query[0][3],query[0][5])

def getDiscordUserIdFromUsers(user_id):
    return selectQuery(f"SELECT discord_user_id FROM Users WHERE user_id = {user_id}")[0][0]

#getUserDiscordName pobieranie nazwy usera i taga z bazy danych
def getUserDiscordName(user_id):
    query = selectQuery(f"""SELECT user_name, user_discord_tag FROM Discord_users
    INNER JOIN Users ON Users.discord_user_id = Discord_users.discord_user_id
    WHERE Users.user_id = '{user_id}'""")

    return f"{query[0][0]}#{'0'*(4-len(str(query[0][1])))}{query[0][1]}" #jezeli tag zaczyna sie od 0 to w bazie jest bez tych zer, wiec trzeba je dodac

#updateServerBonusStatus zmienia czy bonusma byc wlaczony czy wylaczony na serwerze
def updateServerBonusStatus(server_id,state):
    insertQuery(f"UPDATE Servers SET is_bonus = {state} WHERE discord_server_id = {server_id}")

#setServerBonus losuje bonus dla danego serwera na dany dzien
def setServerBonus(server,week,day):
    if selectQuery(f"SELECT discord_server_id FROM Server_bonuses WHERE discord_server_id = '{server.discord_server_id}' AND week = '{week}' AND day = '{day}'") == []:#sprawdzamy czy na ten dzien juz nie ma(np jak byl reset bota zeby nie wywalilo)
        random_bonus = selectQuery(f"SELECT bonus_id, bonus_description FROM Bonuses WHERE bonus_id NOT IN (SELECT bonus_id FROM Server_bonuses WHERE discord_server_id = '{server.discord_server_id}') ORDER BY RAND() LIMIT 1")
        insertQuery(f"INSERT INTO Server_bonuses (discord_server_id, bonus_id, week, day) VALUES ('{server.discord_server_id}',{random_bonus[0][0]},'{week}','{day}')")
        return random_bonus[0][1] #bonus description
    return selectQuery(f"SELECT bonus_description FROM Bonuses WHERE bonus_id IN (SELECT bonus_id FROM Server_bonuses WHERE discord_server_id = '{server.discord_server_id}' AND week = {week} AND day = {day})")[0][0]
    
#insertBonuses uzywany w bot_owenrs, sluzy do jednorazowego dodania bonusow do bazy
def insertBonuses():
    query = "INSERT INTO Bonuses (bonus_description, bonus_answers) VALUES "
    for bonus in const.bonuses:
        temp = str(const.bonuses[bonus]).replace("'", "\"")#zmieniamy pojedyncze ciapki na podwojne
        query += f"('{bonus}', '{temp}'),"#do query dodajemy kolejne VALUES
    insertQuery(query[:-1])#:-1 -> nie bierzemy ostatniego przecinka
    
#getServerTodayBonus zwraca bonus_id, available_answers, bonus_description, na dzis zalenie od serwera
def getServerTodayBonus(server_id,today):
    todays_matches = getTodaysMatches(today)
    bonus_id = selectQuery(f"SELECT bonus_id FROM Server_bonuses WHERE discord_server_id = '{server_id}' AND week = '{todays_matches[0].match_week}' AND day = '{todays_matches[0].match_day}'")[0][0]
    bonus_details = selectQuery(f"SELECT bonus_description, bonus_answers FROM Bonuses WHERE bonus_id = {bonus_id}")
   
    bonus_answers = str(bonus_details[0][1])[1:-1].replace(" ","").replace("\"","").split(",")
    bonus_description = bonus_details[0][0]
    return bonus_id,bonus_answers, bonus_description

#insertBonusVote dodaje glos usera do db
def insertBonusVote(user_id, bonus_id, vote : list):
    if selectQuery(f"SELECT user_id FROM Users_bonus_votes WHERE bonus_id = {bonus_id} AND user_id ={user_id}") == []:#dodajemy jezeli nie glosowal
        vote = str(vote).replace("'", "\"").lower()
        insertQuery(f"INSERT INTO Users_bonus_votes (user_id, bonus_id, vote) VALUES ({user_id}, {bonus_id}, '{vote}')")
        return True
    return False#jezeli glosowal to False

#deleteBonus usuwa glos usera na bonus (reset_bonus)
def deleteBonus(user_id, bonus_id):
    insertQuery(f"DELETE FROM Users_bonus_votes WHERE user_id = {user_id} AND bonus_id = {bonus_id}")


#updatePointsBonus zlicza pointsy dla bonusu, answers to odpowiedzi danego przez admina jako poprawne
def updatePointsBonus(server, answers,bonus_details):
    try:
        bonus_id = bonus_details[0]
        available_answers = bonus_details[1]
        answers = [i.lower() for i in answers]#zamieniamy wszytko na male litery
        for answer in answers:
            if available_answers==['number']:#jezeli number to sprawdzamy czy podana odpowiedz jest liczba (problem z umber (pi cos inaczej sciaga))
                if not answer.isdigit():
                    return False
            elif (answer not in available_answers):
                return False

        users_array = getUsersFromServer(server)#sciaganie wszystkich userow z servera
        users=""
        for user in users_array:
            users+=f"{user}, "
        if users =="":
            return #jezeli nie ma userow to przerywamy
            
        users_vote_dict ={}
        users_points_dict = getUsersPointsAndAnswersAmount(server)[0]#sciagamy aktualne punkty kazdego usera

        for user in selectQuery(f"SELECT user_id, points FROM Users_points WHERE user_id IN({users[:-2]})"): #tworzenie slownika z kazdym uzytkownikiem i pointsami
            users_points_dict[user[0]] = user[1]#??? to robimy wyzej

        for user_vote in selectQuery(f"SELECT user_id, vote FROM Users_bonus_votes WHERE user_id IN ({users[:-2]}) AND bonus_id = {bonus_id}"):
            users_vote_dict[user_vote[0]] = str(user_vote[1])[2:-2].replace(" ","").replace("\"","").split(",") # user_vote[1] inaczej wyglada na pi(od 2) winda(od 4)
            

        for user_id in users_vote_dict:#przechodzimy po kazdym userze
            for vote in users_vote_dict[user_id]:#przechodzimy po jego votach
                if vote in answers: # jezeli jego vote jest w poprawnych odpowiedziach to +2 point
                    users_points_dict[user_id]+=2
        for user_id in users_points_dict:#update pointsow w bazie
            insertQuery(f"UPDATE Users_points SET points = {users_points_dict[user_id]} WHERE user_id = {user_id}")
    except Exception as e:
        print("bonus update points error: ",e)
        
#updateServerRole updatuje role do pingowania na serwerze
def updateServerRole(discord_server_id,role_id):    
	return f"UPDATE Servers SET role_id = '{role_id}' WHERE discord_server_id = '{discord_server_id}'"

def getAllMatches():
    query = f"SELECT match_id, team_1, team_2, winner, team_1_score, team_2_score , match_day, match_week, date FROM Matches ORDER BY match_id"
    matches = []

    for i in selectQuery(query): #tworznie listy 2d z [team_1_short,team_2_short,match_id]
        matches.append(models.Match(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],None,i[8])) 
    return matches

def getMostVotedBonusAnswer(server, today):
    users_array = getUsersFromServer(server)#sciaganie wszystkich userow z servera
    users=""
    for user in users_array:
        users+=f"{user}, "
    if users =="":
        return #jezeli nie ma userow to przerywamy
    
    sql = f"SELECT vote, COUNT(vote) FROM Users_bonus_votes WHERE user_id IN ({users[:-2]}) AND bonus_id = {getServerTodayBonus(server.discord_server_id,today)[0]} GROUP BY vote ORDER BY COUNT(vote) DESC LIMIT 3"
    sql2 = f"SELECT COUNT(vote) FROM Users_bonus_votes WHERE user_id IN ({users[:-2]}) AND bonus_id = {getServerTodayBonus(server.discord_server_id, today)[0]}"
    query = selectQuery(sql)
    query2 = selectQuery(sql2)
    
    mostVotedBonusAnswer = "\n**Most voted bonus answer:**\n"
    print(query)
    print("---------")
    print(query2)
    if len(query)<3:
        rangeDlaFora = len(query)
    else:
        rangeDlaFora = 3
    for i in range(rangeDlaFora):
        mostVotedBonusAnswer += f"{str(query[i][0])[2:-2] - round((query[i][1]/query2[0][0])*100)}%\n"
    return mostVotedBonusAnswer