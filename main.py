from lcu_driver import Connector
import time

connector = Connector()
creating = False

@connector.ready
async def connect(connection):
    print('Yuumi Bot Extension ready!')
    print('')
    await champion_select(connection)


@connector.close
async def disconnect(connection):
    print('Ended app')

@connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
async def lobby_changed(connection, event):
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
        print('Welcome To Champion Select!')
        print()
        await champion_select(connection)
    if (event.data == 'AfterGame'):
        await champion_select(connection)
    if (event.data == 'InProgress'):
        print('Game Started...')
        print()
    if (event.data == 'WaitingForStats' or event.data == 'PreEndOfGame'):
        print('Waiting For Stats')
        print()
        await skip_mission_celebrations(connection)
    if (event.data == 'EndOfGame'):
        print('Restarting Queue')
        print('')
        await restart_queue(connection)

# async def create_game(connection):
#    response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})
#    time.sleep(3)
 

async def choose_roles(connection):
    await connection.request('PUT', '/lol-lobby/v2/lobby/members/localMember/position-preferences', data={"firstPreference": "UTILITY","secondPreference": "MIDDLE",})

async def start_queue(connection):
    response = await connection.request('POST', '/lol-lobby/v2/lobby/matchmaking/search')
    time.sleep(1)
    response = await connection.request('GET', '/lol-lobby/v2/lobby/matchmaking/search-state')
    searchstate = await response.json()

    if (len(searchstate['errors']) != 0):
        cooldown = int(searchstate['errors'][0]['penaltyTimeRemaining']) -1

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

async def accept_queue(connection):
    await connection.request('POST', '/lol-matchmaking/v1/ready-check/accept')
    
async def honor_player(connection):
    await connection.request('POST', '/lol-honor-v2/v1/honor-player', data={"summonerId": 0})

async def skip_mission_celebrations(connection):
    time.sleep(2)
    response = await connection.request('GET', '/lol-pre-end-of-game/v1/currentSequenceEvent')
    sequence = await response.json()
    celebration = sequence['name']

    time.sleep(1)
    await connection.request('POST', f'/lol-pre-end-of-game/v1/complete/{celebration}')

    
async def restart_queue(connection):
    await connection.request('POST', '/lol-lobby/v2/play-again')

is_picking = False
is_banning = False
    
async def champion_select(connection):
    global is_picking
    global is_banning
    messagePrePick = False
    messageBanPick = False
    messagePick = False

    while True:
        response = await connection.request('GET', '/lol-champ-select/v1/session')
        session = await response.json()

        phase = session['timer']['phase']
        playerId = session['localPlayerCellId']

        # use role for later
        for block in session['myTeam']:
            if block['cellId'] == playerId:
                try:
                    role = block['assignedPosition'].upper()
                except:
                    role = 'FILL'
        
        if phase == 'PLANNING':
            if not is_picking:
                await pre_pick_champion(connection, session)
                if messagePrePick == False:
                    messagePrePick = True
                    print('Yuumi Prepicked')
                    print()
        if phase == "BAN_PICK":
            if await block_condition(session, "pick", playerId) and not is_picking:
                await pick_champion(connection, session)
                if messageBanPick == False:
                    messageBanPick = True
                    print('Yuumi Picked')
                    print()
            if await block_condition(session, "ban", playerId) and not is_banning:
                await ban_champion(connection, session)
                if messagePick == False:
                    messagePick = True
                    print('Nautilus Banned')
                    print()

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
            await connection.request('PATCH', url, data={'championId': 350})
    is_picking = False

async def pick_champion(connection, session):
    global is_picking
    is_picking = True
    for action in session['actions']:
        for sub_action in action:
            url = '/lol-champ-select/v1/session/actions/%d' % sub_action['id']
            await connection.request('PATCH', url, data={'championId': 350})
            await connection.request('POST', url + '/complete', data={'championId': 350})
    is_picking = False

async def ban_champion(connection, session):
    global is_banning
    is_banning = True
    for action in session['actions']:
        for sub_action in action:
            url = '/lol-champ-select/v1/session/actions/%d' % sub_action['id']
            await connection.request('PATCH', url, data={'championId': 111})
            await connection.request('POST', url + '/complete', data={'championId': 350})
    is_banning = False


print('Bot Started! Enjoy And Relax :)')
print()

connector.start()
