from operator import itemgetter
from lcu_driver import Connector
import time

connector = Connector()
creating = False

@connector.ready
async def connect(connection):
    print('Yuumi Bot Extension ready!')
    print('')
    # await create_game(connection)


@connector.close
async def disconnect(connection):
    print('Ended app')

@connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
async def lobby_changed(connection, event):
    print("You are in: " + event.data)
    print()
    if (event.data == 'None'):
        await create_game(connection)
        pass
    if (event.data == 'Lobby'):
        print('Starting queue')
        print()
        await choose_roles(connection)
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
    # honor
    if (event.data == 'PreEndOfGame'):
        await honor_player(connection)
        print('Game ended')
        print()
    # scoreboard
    if (event.data == 'EndOfGame'):
        print('Restarting queue')
        print('')
        await restart_queue(connection)


async def create_game(connection):
    response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})
    time.sleep(3)

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

    while True:
        time.sleep(2)
        response = await connection.request('GET', '/lol-champ-select/v1/session')
        cs = await response.json()

        for action in cs['actions']:
            for subaction in action:
                url = '/lol-champ-select/v1/session/actions/%d' % subaction['id']

                if subaction['type'] == 'ban' and subaction['championId'] == 350 and subaction['completed'] == True:
                    print('Yuumi ban detected! :(')
                    print('(automatic dodge not implemented yet -> will dodge automatically)')
                    print()
                    # dodge lobby
                    # response = await connection.request('POST', '/lol-lobby/v1/lobby/custom/cancel-champ-select')
                    # time.sleep(2)
                    # response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})
                
                if subaction['type'] == 'pick' and subaction['championId'] == 350 and subaction['completed'] == True and subaction['isAllyAction'] == False:
                    print('Yuumi pick detected! :(')
                    print('(automatic dodge not implemented yet -> will dodge automatically)')
                    print()
                    # dodge lobby
                    # response = await connection.request('POST', '/lol-lobby/v1/lobby/custom/cancel-champ-select')
                    # time.sleep(2)
                    # response = await connection.request('post', '/lol-lobby/v2/lobby', data={"queueId": 420})

                if subaction['completed'] == False:
                    if subaction['type'] == 'ban':
                        # ban a champion
                        response = await connection.request('PATCH', url, data={'championId': 111})
                        response = await connection.request('POST', url+'/complete', data={'championId': 111})

                    if subaction['type'] == 'pick':
                        # pick a champion
                        response = await connection.request('PATCH', url, data={'championId': 350})
                        response = await connection.request('POST', url+'/complete', data={'championId': 350})


connector.start()
