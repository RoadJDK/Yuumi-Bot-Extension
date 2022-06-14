import json
import requests
from lcu_driver import Connector
import time
from subprocess import Popen

currentVersion = '4.0'

connector = Connector()
file = open("bot/config.json")
config = json.load(file)
file = open("bot/common/gamemodes.json")
gamemodes = json.load(file)
file = open("bot/common/champions.json")
champions = json.load(file)

dodgeState = 0
gamecount = 1

@connector.ready
async def connect(connection):
    print('Connected Successfully To Client')
    print('(Open A Lobby To Start)')
    print('')


@connector.close
async def disconnect(connection):
    print('Ended app')

@connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
async def lobby_changed(connection, event):
    global gamecount
    if (event.data == 'None'):
        print('In Homescreen')
        print()
        # await create_game(connection)
        pass
    if (event.data == 'Lobby'):
        print('Starting Queue')
        print()
        await choose_roles(connection)
        time.sleep(2)
        await start_queue(connection)
    if (event.data == 'ReadyCheck'):
        print('Accepting Match')
        print()
        await accept_queue(connection)
    if (event.data == 'ChampSelect'):
        print("----------------------------")
        print()
        print(f'Welcome To Champion Select! (Game {gamecount})')
        print()
        await champion_select(connection)
    if (event.data == 'AfterGame'):
        await champion_select(connection)
    if (event.data == 'InProgress'):
        print('Game Started...')
        print()
        await honor_player(connection)
    if (event.data == 'PreEndOfGame'):
        gamecount = gamecount + 1
        time.sleep(15)
        print('Honor Player')
        print()
        await honor_player(connection)
        print('Restarting Ux')
        print()
        time.sleep(5)
        await skip_mission_celebrations(connection)
        time.sleep(30)
        print('Create New Game')
        print()
        await create_game(connection)
    if (event.data in ["WaitingForStats", "PreEndOfGame"]):
        pass
    if (event.data == 'EndOfGame'):
        pass
        # print()
        # await restart_queue(connection)

async def create_game(connection):
    game_mode = config['gameMode'].lower()
    queue_id = gamemodes[game_mode]

    await connection.request('POST', '/lol-lobby/v2/lobby', data={"queueId": queue_id})
    time.sleep(3)

async def send_chat(connection, message):
    response = await connection.request('GET', '/lol-chat/v1/conversations')
    conversations = await response.json()
   
    for conversation in conversations:
        if conversation['type'] == 'championSelect':
            lobby_id = conversation['id']

    await connection.request('POST', '/lol-chat/v1/conversations/' + lobby_id + '/messages', data={'type': 'chat', 'body': message})
 

async def choose_roles(connection):
    await connection.request('PUT', '/lol-lobby/v2/lobby/members/localMember/position-preferences', data={"firstPreference": "UTILITY","secondPreference": "MIDDLE",})

async def start_queue(connection):
    global dodgeState

    response = await connection.request('POST', '/lol-lobby/v2/lobby/matchmaking/search')
    time.sleep(1)
    response = await connection.request('GET', '/lol-lobby/v2/lobby/matchmaking/search-state')
    searchstate = await response.json()

    if (len(searchstate['errors']) != 0):
        cooldown = int(searchstate['errors'][0]['penaltyTimeRemaining']) -1
        if cooldown < 360:
            dodgeState = 1
        elif cooldown < 1800:
            dodgeState = 2
        else:
            dodgeState = 3

        print("Leaverbuster Detected!")
        print()
        while True:
            response = await connection.request('GET', '/lol-lobby/v2/lobby/matchmaking/search-state')
            searchstate = await response.json()

            if (len(searchstate['errors']) == 0):
                print('Leaverbuster Ended!')
                break
            
            mins, secs = divmod(cooldown, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print('Time Remaining: ' + timer, end="\r")
            time.sleep(1)
            cooldown -= 1
        print()
        time.sleep(1)
        response = await connection.request('POST', '/lol-lobby/v2/lobby/matchmaking/search')
    else:
        dodgeState = 0

async def accept_queue(connection):
    await connection.request('POST', '/lol-matchmaking/v1/ready-check/accept')
    
async def honor_player(connection):
    await connection.request('POST', '/lol-honor-v2/v1/honor-player', data={"summonerId": 0})

async def skip_mission_celebrations(connection):
    response = await connection.request('GET', '/lol-pre-end-of-game/v1/currentSequenceEvent')
    sequence = await response.json()
    celebration = sequence['name']

    await connection.request('POST', f'/lol-pre-end-of-game/v1/complete/{celebration}')
    time.sleep(1)
    await connection.request('POST', '/riotclient/kill-and-restart-ux')

    
async def restart_queue(connection):
    await connection.request('POST', '/lol-lobby/v2/play-again')

is_picking = False
is_banning = False
yuumiBanned = False
    
async def champion_select(connection):
    global is_picking
    global is_banning
    global yuumiBanned

    sentPrePick = False
    sentBanPick = False
    sentPick = False
    sentMessage = False
    yuumiBanned = False

    while True:
        response = await connection.request('GET', '/lol-champ-select/v1/session')
        session = await response.json()

        try:
            phase = session['timer']['phase']
            playerId = session['localPlayerCellId']
            pickchamp = config['mainChamp'].lower()
            
            if phase == 'PLANNING':
                if sentMessage == False:
                    sentMessage = True
                    message = config['instantMessage']
                    print('Sent Message: ' + message)
                    print()
                    time.sleep(4)
                    await send_chat(connection, message)
                await pre_pick_champion(connection, session)
                if sentPrePick == False:
                    sentPrePick = True
                    print(f'{pickchamp.capitalize()} Prepicked')
                    print()
            if phase == "BAN_PICK":
                if sentMessage == False:
                    sentMessage = True
                    message = config['instantMessage']
                    time.sleep(3)
                    await send_chat(connection, message)
                    print('Sent Message: ' + message)
                    print()
                    time.sleep(1)
                if await block_condition(session, "ban", playerId) and not is_picking:
                    banChamp = config['banChamp'].lower()

                    await ban_champion(connection, session)
                    if sentBanPick == False:
                        sentBanPick = True
                        print(f'{banChamp.capitalize()} Banned')
                        print()
                elif await block_condition(session, "pick", playerId) and not is_picking:
                    await pick_champion(connection, session)
                    if sentPick == False:
                        sentPick = True
                        print(f'{pickchamp.capitalize()} Picked')
                        print()
            if phase == "FINALIZATION":
                return
        except:
            pass

async def block_condition(session, block_type, player_id):
    for array in session['actions']:
            for block in array:
                if (
                    block["actorCellId"] == player_id
                    and block["type"] == block_type
                    and block["completed"] != True
                    and block["isInProgress"] == True
                ):
                    player_id = block['id']
                    return True

async def pre_pick_champion(connection, session):
    global is_picking
    is_picking = True

    for action in session['actions']:
        for sub_action in action:
            url = '/lol-champ-select/v1/session/actions/%d' % sub_action['id']
            champ_pick = config['mainChamp'].lower()
            pick_id = champions[champ_pick]
            await connection.request('PATCH', url, data={'championId': pick_id})
    is_picking = False

async def pick_champion(connection, session):
    global is_picking
    global yuumiBanned
    global dodgeState
    is_picking = True

    champ_pick = config['mainChamp'].lower()
    pick_id = champions[champ_pick]

    response = await connection.request('GET', '/lol-login/v1/session')
    session = await response.json()
    summonerId = session['summonerId']

    response = await connection.request('GET', '/lol-champ-select/v1/session')
    session = await response.json()

    sentPickMessage = False
    sentYuumiBanMessage = False
    sentYuumiPickedMessage = False

    while True:
        time.sleep(2)
        response = await connection.request('GET', '/lol-champ-select/v1/session')
        cs = await response.json()

        actorCellId = -1

        try:
            for member in cs['myTeam']:
                if member['summonerId'] == summonerId:
                    actorCellId = member['cellId']

            for action in cs['actions']:
                for subaction in action:
                    if subaction['type'] == 'ban' and subaction['championId'] == pick_id and subaction['completed'] == True:
                        if sentYuumiBanMessage == False:
                            sentYuumiBanMessage = True
                            yuumiBanned = True
                            print(f'{champ_pick} ban detected! :(')
                            print('(Automatic Dodge Not Implemented Yet -> Will Pick A Random Champ And Afk In Base (To Remake))')
                            print()
                            # dodge lobby
                            # response = await connection.request('POST', '/lol-lobby/v1/lobby/custom/cancel-champ-select')
                            # time.sleep(2)
                            # response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})
                        
                    if subaction['type'] == 'pick' and subaction['championId'] == pick_id and subaction['completed'] == True and subaction['isAllyAction'] == False:
                        if sentYuumiPickedMessage == False:
                            sentYuumiPickedMessage = True
                            yuumiBanned = True
                            print(f'{champ_pick} Pick Detected! :(')
                            print('(Automatic Dodge Not Implemented Yet -> Will Pick A Random Champ And Afk In Base (To Remake))')
                            print()
                            # dodge lobby
                            # response = await connection.request('POST', '/lol-lobby/v1/lobby/custom/cancel-champ-select')
                            # time.sleep(2)
                            # response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})

                    if subaction['actorCellId'] == actorCellId and subaction['type'] == 'pick':
                        url = '/lol-champ-select/v1/session/actions/%d' % subaction['id']
                        champ_pick = config['mainChamp'].lower()
                        pick_id = champions[champ_pick]

                        # pick champion
                        if yuumiBanned == True:
                            if config['remakeOnBan'] == True:
                                champ_pick = config['remakeChamp'].lower()
                                pick_id = champions[champ_pick]
                                if sentPickMessage == False:
                                    sentPickMessage = True
                                    print(f"Picked {champ_pick.capitalize()}")
                                    print()
                                await connection.request('PATCH', url, data={'championId': pick_id})
                                await connection.request('POST', url + '/complete', data={'championId': pick_id})
                                is_picking = False
                                time.sleep(1)
                            return
                        if yuumiBanned == False:
                            champ_pick = config['mainChamp'].lower()
                            pick_id = champions[champ_pick]
                            if sentPickMessage == False:
                                sentPickMessage = True
                                print(f"Picked {champ_pick.capitalize()}")
                                print()
                            await connection.request('PATCH', url, data={'championId': pick_id})
                            await connection.request('POST', url + '/complete', data={'championId': pick_id})
                            is_picking = False
                            time.sleep(1)
                            return
        except:
            pass

async def ban_champion(connection, session):
    global is_banning
    is_banning = True
    for action in session['actions']:
        for sub_action in action:
            url = '/lol-champ-select/v1/session/actions/%d' % sub_action['id']
            champ_ban = config['banChamp'].lower()
            ban_id = champions[champ_ban]

            await connection.request('PATCH', url, data={'championId': ban_id})
            await connection.request('POST', url + '/complete', data={'championId': ban_id})
    is_banning = False

def update():
    response = requests.get('https://raw.githubusercontent.com/RoadJDK/Yuumi-Bot-Extension/main/version')
    remote_version = response.text.strip()

    if currentVersion != remote_version:
        Popen('update.py', shell=True)
        print()
        exit("exit for updating all files")


update()

print(f'Loaded Yuumi Bot Extension V{currentVersion}')
print('Enjoy And Relax :)')
print()

connector.start()
