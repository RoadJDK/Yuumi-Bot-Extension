from operator import itemgetter
from lcu_driver import Connector
import time

connector = Connector()
creating = False

@connector.ready
async def connect(connection):
    print('LCU API is ready to be used.')
    # await create_game(connection)


@connector.close
async def disconnect(connection):
    print('Finished task')

@connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
async def lobby_changed(connection, event):
    print("You are in: " + event.data)
    if (event.data == 'None'):
        # await create_game(connection)
        pass
    if (event.data == 'Lobby'):
        await choose_roles(connection)
        await start_queue(connection)
    if (event.data == 'ReadyCheck'):
        await accept_queue(connection)
    if (event.data == 'ChampSelect'):
        await champion_select(connection)
    if (event.data == 'AfterGame'):
        await champion_select(connection)
    if (event.data == 'InProgress'):
        print('Game started')
    if (event.data == 'WaitingForStats'):
        print('Waiting for stats')
    # honor
    if (event.data == 'PreEndOfGame'):
        await honor_player(connection)
        print('Game end detected')
    # scoreboard
    if (event.data == 'EndOfGame'):
        await restart_queue(connection)
        print('Game ended')

'''
async def create_game(connection):
    response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})
    time.sleep(3)
'''

async def choose_roles(connection):
    response = await connection.request('put', '/lol-lobby/v2/lobby/members/localMember/position-preferences', data={"firstPreference": "UTILITY","secondPreference": "MIDDLE",})

async def start_queue(connection):
    response = await connection.request('POST', '/lol-lobby/v2/lobby/matchmaking/search')

async def accept_queue(connection):
    response = await connection.request('POST', '/lol-matchmaking/v1/ready-check/accept')
    
async def honor_player(connection):
    response = await connection.request('POST', '/lol-honor-v2/v1/honor-player', data={"summonerId": 0})
    
async def restart_queue(connection):
    response = await connection.request('POST', '/lol-lobby/v2/play-again')
    
async def champion_select(connection):
    session = await connection.request('GET', '/lol-login/v1/session')
    sessionJson = await session.json()
    summonerId = sessionJson['summonerId']

    response = await connection.request('GET', '/lol-champ-select/v1/session')
    cs = await response.json()

    actorCellId = -1

    for member in cs['myTeam']:
            if member['summonerId'] == summonerId:
                actorCellId = member['cellId']

    while True:
        time.sleep(2)
        print('------')
        response = await connection.request('GET', '/lol-champ-select/v1/session')
        cs = await response.json()

        for action in cs['actions']:
            for subaction in action:
                if subaction['actorCellId'] == actorCellId:
                    highest_id = 0
                    if subaction['id'] > highest_id:
                        highest_id = subaction['id']
                        latest_action = subaction

        print(latest_action)

        url = '/lol-champ-select/v1/session/actions/%d' % latest_action['id']

        if latest_action['completed'] == False:
            if latest_action['type'] == 'ban':
                # ban a champion
                response = await connection.request('PATCH', url, data={'championId': 111})
                response = await connection.request('POST', url+'/complete', data={'championId': 111})
            if latest_action['type'] == 'pick':
                # pick a champion
                response = await connection.request('PATCH', url, data={'championId': 350})
                response = await connection.request('POST', url+'/complete', data={'championId': 350})


connector.start()
