import os
import json
import boto3
import random
import string
import cards
import datetime
import time
from boto3.dynamodb.conditions import Key
from random import shuffle

client = boto3.client('dynamodb')
dynamodb = boto3.resource("dynamodb")
sessionsTableName =  os.environ['SESSIONS_TABLE_NAME']
configsTableName =  os.environ['CONFIGS_TABLE_NAME']
sessionsTable = dynamodb.Table(sessionsTableName)
configsTable = dynamodb.Table(configsTableName)

# ------------------------------------------------------------------------------------------------------
# Function that generates a random 6 characters string, prefixed with time stamp
# ------------------------------------------------------------------------------------------------------
def generate_sessionid():
    stamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    return stamp + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

# ------------------------------------------------------------------------------------------------------
# Function that initializes the session data
# ------------------------------------------------------------------------------------------------------
def init_session():
    sessiondata = {
        'id': generate_sessionid(),
        'round': 1,
        'decision': 'none',
        'player': {
            'hand': [],
            'scores': [],
            'result': 'none',
            'challenges': [],
            'defenses': []
        },
        'dealer': {
            'hand': [],
            'scores': [],
            'result': 'none',
            'challenges': [],
            'defenses': []
        },
        'deck': {
            'cards': [],
            'next_index': 0
        },
        'challengesDeck': {
            'cards': [],
            'next_index': 0
        },
        'defensesDeck': {
            'cards': [],
            'next_index': 0
        },
        'battlePlay': {}
    }
    return sessiondata

# ------------------------------------------------------------------------------------------------------
# Function that  returns the list of services / challenges / defenses from the config table
# ------------------------------------------------------------------------------------------------------
def get_cfg_type_ids(cardType):

    # Initialize an empty list to store the IDs
    type_ids = [] 
    
    # Parameters for the query
    query_params = {
        'KeyConditionExpression': Key('config').eq(cardType),
        'ProjectionExpression': 'id'  # We only need the 'id' attribute
    }
    
    # Perform the query
    while True:
        response = configsTable.query(**query_params)
        
        # Add the IDs from this page of results
        for item in response['Items']:
            type_ids.append(item['id'])
        
        # Check if there are more pages of results
        if 'LastEvaluatedKey' not in response:
            break
        
        # If there are more pages, update the ExclusiveStartKey
        query_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
    
    return type_ids

# ------------------------------------------------------------------------------------------------------
# Function that deals one playing card. This is here because I needed to add detailed data to the card
# ------------------------------------------------------------------------------------------------------
def deal_one(deck):
    newcard = deck.dealnext()
    add_details(newcard, newcard['service'],'services')
    return newcard

# ------------------------------------------------------------------------------------------------------
# Function that adds the card's config details
# ------------------------------------------------------------------------------------------------------
def add_details(card, id, cardType):
    # Add an indicator of the card being used or successfully challenged. This will be useful in  battle
    card['used'] = 0
    # Populates the cards details
    card['details'] = configsTable.get_item(Key={'config': cardType, 'id': id}).get('Item')['cfgdata']

# ------------------------------------------------------------------------------------------------------
# Function that calculates individual scores (Blackjack rules)
# ------------------------------------------------------------------------------------------------------
def calc_scores(hand: list[dict], dealer_hand = False) -> list[int]:
    # Find the number of aces in the hand
    num_aces = len([card for card in hand if card['face'] == 'A'])
    scores = []
    score = sum([card['points_val'] for card in hand])
    if (dealer_hand and score < 17):
        score -= num_aces * 10 # Dealer's aces count for 1 if the total is less than 17, and 11 otherwise
    scores.append(score)

    for a in range(num_aces):
        if not(dealer_hand and scores[0] < 17):
            scores.append(scores[0] - ((a+1)*10)) # Aces can be 1 instead of 11 so there are alternate scores

    scores.sort()
    return scores

# ------------------------------------------------------------------------------------------------------
# Function that removes any score over 21 from the list
# ------------------------------------------------------------------------------------------------------
def cleanup_scores (sessiondata, who):
    if 21 in sessiondata[who]['scores']:
        sessiondata[who]['result'] = 'JACK'
    scores = list(sessiondata[who]['scores']) #I need a copy, because if i delete elements friom the list, indexes get messed up in my iteration
    for s in scores:
        if s > 21:
            # Delete bust scores from the list
            sessiondata[who]['scores'].remove(s)
    if len(sessiondata[who]['scores']) == 0:
        sessiondata[who]['result'] = 'BUST'
        who_wins(sessiondata)

# ------------------------------------------------------------------------------------------------------
# Function that Calculates the 21 round scores for both player and dealer
# ------------------------------------------------------------------------------------------------------
def calc_all_scores(sessiondata):
    sessiondata['player']['scores'] = calc_scores(sessiondata['player']['hand'])
    cleanup_scores(sessiondata, 'player')
    sessiondata['dealer']['scores'] = calc_scores(sessiondata['dealer']['hand'], True)
    cleanup_scores(sessiondata, 'dealer')
    if 21 in sessiondata['dealer']['scores']:
        sessiondata['dealer']['result'] = 'JACK'
    if 21 in sessiondata['player']['scores']:
        sessiondata['player']['result'] = 'JACK'
        dealers_turn(sessiondata)


# ------------------------------------------------------------------------------------------------------
# Function that determines the winner of the 21 (Blackjack) round 
# ------------------------------------------------------------------------------------------------------
def who_wins(sessiondata):
    ld = len(sessiondata['dealer']['scores'])
    lp = len (sessiondata['player']['scores'])
    if ( sessiondata['player']['result'] != 'none' and sessiondata['player']['result'] == sessiondata['dealer']['result']) or (ld > 0 and lp > 0 and sessiondata['dealer']['scores'][-1] == sessiondata['player']['scores'][-1]):
        sessiondata['decision'] = f'PUSH'
    elif sessiondata['dealer']['result'] == 'BUST':
        sessiondata['decision'] = 'PLAYR'
    elif sessiondata['player']['result'] == 'BUST':
        sessiondata['decision'] = f'DEALR'
    elif ld > 0 and lp > 0 and sessiondata['dealer']['scores'][-1] > sessiondata['player']['scores'][-1]:
        sessiondata['decision'] = f'DEALR'
    else:
        sessiondata['decision'] = f'PLAYR'

# ------------------------------------------------------------------------------------------------------
# Function that handles the dealer's draws, after the player stands or gets 21
# ------------------------------------------------------------------------------------------------------
def dealers_turn(sessiondata):
    if sessiondata['dealer']['result'] != 'BUST' and sessiondata['dealer']['result'] != 'JACK':
        while sessiondata['dealer']['scores'][0] < 17:
            ncard = sessiondata['deck']['cards'][int(sessiondata['deck']['next_index'])]
            add_details(ncard,ncard['service'],'services')
            sessiondata['dealer']['hand'].append(ncard)
            sessiondata['deck']['next_index'] += 1
            sessiondata['dealer']['scores'] = calc_scores(sessiondata['dealer']['hand'], True)
            cleanup_scores(sessiondata, 'dealer')
            
            if 21 in sessiondata['dealer']['scores']:
                sessiondata['dealer']['result'] = 'JACK'
                break
            elif len(sessiondata['dealer']['scores']) == 0:
                sessiondata['dealer']['result'] = 'BUST'
                break
    # Determine the winner
    who_wins(sessiondata)

# ------------------------------------------------------------------------------------------------------
# Function that cleans up the session by removing all used cards
# ------------------------------------------------------------------------------------------------------
def cleanup_session(sessiondata):
    who = ['player', 'dealer']
    where = ['hand', 'challenges']
    for actor in who:
        sessiondata[actor]['result'] = 'none'
        for loc in where:
            cards = sessiondata[actor][loc].copy() #i make a copy because I am going to start remiving items
            for card in cards:
                if card['used'] == 1:
                    sessiondata[actor][loc].remove(card)

    sessiondata['decision'] = 'none'

    # Re-calculate the scores
    calc_all_scores(sessiondata)

# ------------------------------------------------------------------------------------------------------
# ************************************** LAMBDA HANDLER FUNCTION ***************************************
# ------------------------------------------------------------------------------------------------------
def lambda_handler(event, context):
    #Added to handle CORS pre-flight , which i need for testing--
    print("Event:", json.dumps(event))
    #if event['httpMethod'] == 'OPTIONS':
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
            }
        }
    #End CORS pre-flight OPTIONS check

    print(event)
    body = {}
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    
    if event['routeKey'] == "POST /sessions/{id}":
        session_id = event['pathParameters']['id'];
        if not session_id:
            # Create a new session
            sessiondata = init_session()
        else:
            print(session_id)
            # Retrieve the existing session from the database
            sessiondata = sessionsTable.get_item(Key={'id': session_id}).get('Item')['sessiondata']

        if event['queryStringParameters']['action'] == 'deal': #-----------------------------------------------------------------------------------------------------------------------
            # Create a new deck and shuffle it
            sceIds = get_cfg_type_ids('services')
            shuffle(sceIds)
            deck = cards.FullDeck([2,3,4,5,6,7,8,9,10,10,10,10,11], sceIds)  # Creates the full deck with point values associated with the cards
            sessiondata['deck']['cards'] = deck.get_deck_as_list()
            # Deal two cards to the player and the dealer
            sessiondata['player']['hand'] = [deal_one(deck), deal_one(deck)]
            sessiondata['dealer']['hand'] = [deal_one(deck), deal_one(deck)]
            sessiondata['deck']['next_index'] = 4
            # Calculate the scores
            calc_all_scores(sessiondata)
            if 21 in sessiondata['player']['scores']:
                who_wins(sessiondata)                                    
            # expiration_time = current time plus 2 days (172800 seconds)
            expiration_time = int(time.time()) + 172800
            # Save the session to the database
            sessionsTable.put_item(Item={'id' : sessiondata['id'], 'sessiondata' : sessiondata, 'expirationTime': expiration_time})

        elif event['queryStringParameters']['action'] == 'hit': #-----------------------------------------------------------------------------------------------------------------------
            # Deal a new card to the player
            ncard = sessiondata['deck']['cards'][int(sessiondata['deck']['next_index'])]
            add_details(ncard, ncard['service'],'services')
            sessiondata['player']['hand'].append(ncard)
            sessiondata['deck']['next_index'] += 1
            sessiondata['player']['scores'] = calc_scores(sessiondata['player']['hand'])
            cleanup_scores(sessiondata, 'player')
            if 21 in sessiondata['player']['scores']:
                sessiondata['player']['result'] = 'JACK'
                dealers_turn(sessiondata)
            if  sessiondata['player']['result'] == 'BUST':
                dealers_turn(sessiondata)

        elif event['queryStringParameters']['action'] == 'stand': #-----------------------------------------------------------------------------------------------------------------------
            if len(sessiondata['player']['scores']) > 0:
                sessiondata['player']['scores'] = [sessiondata['player']['scores'][-1]]
            # Dealer's turn
            dealers_turn(sessiondata)

        elif event['queryStringParameters']['action'] == 'cleanup': #-----------------------------------------------------------------------------------------------------------------------
            cleanup_session(sessiondata)

        else: # Then we have an invalid path
            statusCode = 400

        # Update the database
        sessionsTable.update_item(
            Key={'id': sessiondata['id']},
            UpdateExpression='SET sessiondata = :sessiondata',
            ExpressionAttributeValues={
                ':sessiondata': sessiondata
            }
        )

        #add the session data to the response body, after removing all the decks data. The client ahould not need it
        del(sessiondata['deck']['cards'])
        del(sessiondata['challengesDeck']['cards'])
        del(sessiondata['defensesDeck']['cards'])

        sessiondata = json.loads(json.dumps(sessiondata, default = str))
        body = sessiondata
    else:
        statusCode = 400
        body = 'Unsupported route: ' + event['routeKey']

    body = json.dumps(body)
    res = {
        "statusCode": statusCode,
        "headers": {
            "Set-Cookie": f"SessionID={sessiondata['id']}; Secure; SameSite=Lax",
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": body
    }
    return res