from lcu_driver import Connector
import time

connector = Connector()
creating = False

@connector.ready
async def connect(connection):
    print('Yuumi Bot Extension ready!')
    print('')


@connector.close
async def disconnect(connection):
    print('Ended app')

@connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
async def lobby_changed(connection, event):
    print("You are in: " + event.data)
    print()
    if (event.data == 'None'):
        # await create_game(connection)
        pass
    if (event.data == 'Lobby'):
        print('Starting queue')
        print()
        await choose_roles(connection)
        time.sleep(1)
        await start_queue(connection)
    if (event.data == 'ReadyCheck'):
        print('Accepting match')
        print()
        await accept_queue(connection)
    if (event.data == 'ChampSelect'):
        print('Welcome to champion select!')
        print()
        await champion_select(connection)
    if (event.data == 'AfterGame'):
        await champion_select(connection)
    if (event.data == 'InProgress'):
        print('Game started...')
        print()
    if (event.data == 'WaitingForStats'):
        print('Waiting for stats')
        print()
        await dismiss_notifications(connection)
    # honor
    if (event.data == 'PreEndOfGame'):
        print('Game ended')
        print()
        await honor_player(connection)
        time.sleep(1)
        await skip_missions(connection)
        time.sleep(1)
        await dismiss_notifications(connection)
        time.sleep(1)
    # scoreboard
    if (event.data == 'EndOfGame'):
        print('Restarting queue')
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
        cooldown = int(searchstate['errors'][0]['penaltyTimeRemaining'])

        print("Leaver buster detected!")
        print()
        while True:
            response = await connection.request('GET', '/lol-lobby/v2/lobby/matchmaking/search-state')
            searchstate = await response.json()

            if (len(searchstate['errors']) == 0):
                print('over!')
                break
            
            mins, secs = divmod(cooldown, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print('Time remaining: ' + timer, end="\r")
            time.sleep(1)
            cooldown -= 1
        
    print()
    time.sleep(1)
    response = await connection.request('POST', '/lol-lobby/v2/lobby/matchmaking/search')

async def accept_queue(connection):
    await connection.request('POST', '/lol-matchmaking/v1/ready-check/accept')
    
async def honor_player(connection):
    await connection.request('POST', '/lol-honor-v2/v1/honor-player', data={"summonerId": 0})

async def skip_missions(connection):
    time.sleep(1)
    response = await connection.request(method="GET", endpoint="/lol-pre-end-of-game/v1/currentSequenceEvent")
    celebration = await response.data.get('name')
    time.sleep(1)
    await connection.request(method="POST", endpoint=f"/lol-pre-end-of-game/v1/complete/{celebration}")

async def dismiss_notifications(connection):
    time.sleep(1)
    await connection.skip_mission_celebrations()
    
async def restart_queue(connection):
    await connection.request('POST', '/lol-lobby/v2/play-again')
    
async def champion_select(connection):
    session = await connection.request('GET', '/lol-login/v1/session')
    sessionJson = await session.json()
    summonerId = sessionJson['summonerId']

    response = await connection.request('GET', '/lol-champ-select/v1/session')
    cs = await response.json()

    sentPrePickMessage = False
    sentBanMessage = False
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
                    if subaction['type'] == 'ban' and subaction['championId'] == 350 and subaction['completed'] == True:
                        if sentYuumiBanMessage == False:
                            sentYuumiBanMessage = True
                            print('Yuumi ban detected! :(')
                            print('(automatic dodge not implemented yet -> will dodge automatically)')
                            print()
                            # dodge lobby
                            # response = await connection.request('POST', '/lol-lobby/v1/lobby/custom/cancel-champ-select')
                            # time.sleep(2)
                            # response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})
                        
                    if subaction['type'] == 'pick' and subaction['championId'] == 350 and subaction['completed'] == True and subaction['isAllyAction'] == False:
                        if sentYuumiPickedMessage == False:
                            sentYuumiPickedMessage = True
                            print('Yuumi pick detected! :(')
                            print('(automatic dodge not implemented yet -> will dodge automatically)')
                            print()
                            # dodge lobby
                            # response = await connection.request('POST', '/lol-lobby/v1/lobby/custom/cancel-champ-select')
                            # time.sleep(2)
                            # response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})

                    if subaction['actorCellId'] == actorCellId:
                        url = '/lol-champ-select/v1/session/actions/%d' % subaction['id']

                        # prepick champion
                        if subaction['type'] == 'pick' and subaction['completed'] == False and subaction['championId'] == 0:
                            response = await connection.request('PATCH', url, data={'championId': 350})
                            response = await connection.request('POST', url+'/complete', data={'championId': 350})
                            if sentPrePickMessage == False:
                                sentPrePickMessage = True
                                print('Prepicked Yuumi')
                                print()

                        # ban champion
                        if subaction['type'] == 'ban' and subaction['completed'] == False:
                            response = await connection.request('PATCH', url, data={'championId': 111})
                            response = await connection.request('POST', url+'/complete', data={'championId': 111})
                            if sentBanMessage == False:
                                sentBanMessage = True
                                print('Banned Nautilus')
                                print()

                        # pick champion
                        if subaction['type'] == 'pick' and subaction['championId'] == 350:
                            response = await connection.request('POST', url+'/complete', data={'championId': 350})
                            if sentPickMessage == False:
                                sentPickMessage = True
                                print('Picked Yuumi')
                                print()
        except:
            pass

print('Bot started! Enjoy and relax :)')
print()

connector.start()
