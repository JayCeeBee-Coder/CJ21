import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from random import shuffle

client = boto3.client('dynamodb')
dynamodb = boto3.resource("dynamodb")
# Table names are stored as environment variables
sessionsTableName =  os.environ['SESSIONS_TABLE_NAME']
configsTableName =  os.environ['CONFIGS_TABLE_NAME']
sessionsTable = dynamodb.Table(sessionsTableName)
configsTable = dynamodb.Table(configsTableName)

# ------------------------------------------------------------------------------------------------------
# Function that  returns the list of services / challenges / defenses from the config table
# ------------------------------------------------------------------------------------------------------
def get_cfg_type_ids(cardType):
    response = configsTable.query(
        KeyConditionExpression=Key('config').eq(cardType),
        ProjectionExpression='id'
    )
    return [item['id'] for item in response['Items']]

# ------------------------------------------------------------------------------------------------------
# Function that adds the card's config details
# ------------------------------------------------------------------------------------------------------
def add_details(card, id, cardType):
    #Populates the cards details
    card['details'] = configsTable.get_item(Key={'config': cardType, 'id': id}).get('Item')['cfgdata']
    card['used'] = 0

# ------------------------------------------------------------------------------------------------------
# Function that adds comments to a list
# ------------------------------------------------------------------------------------------------------
def addComment(commentslistList, status, comment):
    commentslistList.append({
        'status': status,
        'comment': comment
    })

# ------------------------------------------------------------------------------------------------------
# Function that assembles the data needed for battle analysis
# ------------------------------------------------------------------------------------------------------
def get_battle_data(sessiondata, security, jacker):
    # The services in security's hand that can be targetted by the attacks
    targets = [srv['service'] for srv in sessiondata[security]['hand']]

    # The services detailed information:
    services = {card['service']:{'name': card['details']['name'], 'category':card['details']['category']} for card in sessiondata[security]['hand']}

    # Details of the defenses in security's hand:
    defenses = {dfn['service']:{'name': dfn['details']['name'], 'explain':dfn['details']['explain']} for dfn in sessiondata[security]['defenses']}

    # Details of the challenges in jacker's hand:
    challenges = {chlg['service']:{'name': chlg['details']['name'], 'targets': chlg['details']['targets'], 'neutralizers': chlg['details']['neutralizers'], 
                'immune': chlg['details']['immune'], 'reasons': chlg['details']['reasons']} 
                for chlg in sessiondata[jacker]['challenges']}

    # Retrieve the categories details from configsTable:
    response = configsTable.query(
        KeyConditionExpression=Key('config').eq('categories')
    )
    categories = {cat['id']: cat['cfgdata']for cat in response['Items']}

    cats = [cat for cat in categories]
    s_cats = [services[card]['category'] for card in services]
    for cat in cats:
        if cat not in  s_cats:
            categories.pop(cat)

    return{'targets':targets, 'services':services, 'defenses':defenses, 'challenges':challenges, 'categories':categories}

# ------------------------------------------------------------------------------------------------------
# Function that check if any target is immune to the attack
# ------------------------------------------------------------------------------------------------------
def checkImmunities(attack, targets, services, challenges, commentslist):
    addComment(commentslist, 'info', 'Checking ' + challenges[attack]['name'] + ' challenge against ' + ' / '.join([services[s]['name'] for s in targets]) + ' services...')
    challengeStatus = 'ATK-GOOD'
    for target in targets:
        # Challenges are configured to recognize the services that are immune to them
        if (target in challenges[attack]['immune'] or services[target]['category'] not in challenges[attack]['targets']):
            addComment(commentslist, 'good', challenges[attack]['name'] + ' attack cannot be used against ' + services[target]['name'])
            if target in challenges[attack]['immune']:
                addComment(commentslist, 'info', challenges[attack]['reasons'][challenges[attack]['immune'].index(target)])
            targets.remove(target)
    if len(targets) == 0:
        #Attack failed
        challengeStatus = 'ATK-FAIL'

    return challengeStatus

# ------------------------------------------------------------------------------------------------------
# Function that checks Superprotections
# ------------------------------------------------------------------------------------------------------
def checkSuperprotections(shield, attack, targets, categories, services, defenses, commentslist):
    # Superprotectors are defenses that protect entire service categories
    challengeStatus = 'ATK-GOOD'
    vulnerable_cats = []
    superprotectors = []
    for target in targets:
        cat = services[target]['category'] #Categories that can be targetted by the attask
        if cat not in vulnerable_cats: #Vvoid duplicates
            vulnerable_cats.append(cat)
            # build a list of superprotectors without duplicates
            for sup in categories[cat]['superprotectors']:
                if sup not in [s['id'] for s in superprotectors]: #If it's not already in the list...
                    superprotectors.append({'id': sup, 'cats': [cat]})
                elif cat not in [s['cats'] for s in superprotectors if s['id'] == sup][0]:
                    [s['cats'] for s in superprotectors if s['id'] == sup][0].append(cat) #Add the category in the list of protected ones

    if shield in [s['id'] for s in superprotectors]:
        addComment(commentslist, 'good', defenses[shield]['name'] + ' protects all targeted ' + ', '.join([categories[c]['name'] for c in [s['cats'] for s in superprotectors if s['id'] == shield][0]]) + ' services')
        # Remove the protected services from the targets list
        targets_copy = list(targets)
        for target in targets_copy:
            cat = services[target]['category']
            if shield in categories[cat]['superprotectors']:
                # Remove protected categories from the vulnerable list
                if cat in vulnerable_cats:
                    vulnerable_cats.remove(cat)
                    numtargets = len(targets)
                    if numtargets > 0:
                        for s in targets:
                            if services[s]['category'] == cat:
                                targets.remove(s)
                                numtargets -= 1
                                if numtargets == 0:
                                    # Attack failed
                                    challengeStatus = 'ATK-FAIL'
                                    addComment(commentslist, 'good', defenses[shield]['name'] + ' protected all the exposed services')
                                    addComment(commentslist, 'info', defenses[shield]['explain'][attack])
    #addComment(commentslist, '', '-----------------------------------------------------------------')
    return challengeStatus

# ------------------------------------------------------------------------------------------------------
# Function that checks individual shields/defenses' efficacy
# ------------------------------------------------------------------------------------------------------
def checkEfficacy(shield, attack, defenses, challenges, commentslist, defending = False):
    challengeStatus = 'ATK-GOOD'
    if shield in challenges[attack]['neutralizers']: # Attacks/challenges also configured to know what neutralizes them
        challengeStatus ='ATK-FAIL'
        addComment(commentslist, 'good', defenses[shield]['name'] + ' is effective against ' + challenges[attack]['name'] + ' challenge')
        addComment(commentslist, 'info', defenses[shield]['explain'][attack])
    else:
        if ( not defending):
            addComment(commentslist, 'bad', defenses[shield]['name'] + ' cannot neutralize ' + challenges[attack]['name'] + ' challenge')

    return challengeStatus

# ------------------------------------------------------------------------------------------------------
# Function that referees the battle with play by play
# ------------------------------------------------------------------------------------------------------
def judgeBattle(shield, attack, targets, categories, services, defenses, challenges, commentslist, defending = False):
    challengeStatus = 'ATK-GOOD'
    challengeStatus = checkImmunities(attack, targets, services, challenges, commentslist)
    if (len(targets) > 0 and challengeStatus == 'ATK-GOOD'):
        challengeStatus = checkSuperprotections(shield, attack, targets, categories, services, defenses, commentslist)
    if (len(targets) > 0 and challengeStatus == 'ATK-GOOD'):
        challengeStatus = checkEfficacy(shield, attack, defenses, challenges, commentslist, defending)
    if challengeStatus == 'ATK-FAIL':
        addComment(commentslist, 'good', 'CHALLENGE DEFEATED!')
    else:
        if not defending:
            addComment(commentslist, 'bad', challenges[attack]['name'] + ' challenge successful!')
            addComment(commentslist, 'bad', 'Services impacted: ' + ', '.join([services[s]['name'] for s in targets]))

    return challengeStatus

# ------------------------------------------------------------------------------------------------------
# Function that returns the defense to be used by the dealer
# ------------------------------------------------------------------------------------------------------
def defendChallenge(shields, attack, targets, categories, services, defenses, challenges, commentslist):
    addComment(commentslist, 'info', 'Targeted services: ' + ' / '.join([services[s]['name'] for s in targets]))
    useShield = ""
    shieldScore = 0
    targetsCount = len(targets)
    challengeStatus = ""
    for shield in shields:
        challengeStatus = judgeBattle(shield, attack, targets, categories, services, defenses, challenges, commentslist, True)
        if useShield == "":
            useShield = shield
            shieldScore = len(targets)
        if challengeStatus == 'ATK-FAIL':
            #addComment(commentslist, 'good', defenses[shield]['name'] + " used to successfully defend the challenge")
            #addComment(commentslist, '', '-----------------------------------------------------------------')
            return {'defense': shield, 'servicesHit': [], 'servicesRemaining:': targets}
        else:
            if len(targets) > shieldScore:
                useShield = shield
                shieldScore = len(targets)
    if shieldScore < targetsCount:
        addComment(commentslist, 'info', 'Some services are unafected by the challenge')
    else:
        addComment(commentslist, 'bad', "No defense could successfully defend against the challenge!")
    addComment(commentslist, 'info', "ServicesHit: " + ', '.join([services[s]['name'] for s in targets]))
    #addComment(commentslist, '', '-----------------------------------------------------------------')
    return {'defense': "", 'servicesHit': targets}

# ------------------------------------------------------------------------------------------------------
# Function that returns the attack to be used by the dealer
# ------------------------------------------------------------------------------------------------------
def launchChallenge(attacks, targets, services, challenges, commentslist):
    addComment(commentslist, 'info', ' / '.join([challenges[a]['name'] for a in attacks]) + ' challenge check against ' + ', '.join([services[s]['name'] for s in targets]) + ' services...')
    #Check how many services can be hit by each attack
    immunities=[0,0]
    a = 0
    for attack in attacks:
        for target in targets:
            if target in challenges[attack]['immune']:
                immunities[a] += 1
        a += 1
    # The attack with the fewer immune targets will be used
    #addComment(commentslist, '', '-----------------------------------------------------------------')
    return attacks[immunities.index(min(immunities))]


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
    
    if event['routeKey'] == "POST /battle/{id}":
        session_id = event['pathParameters']['id'];
        if not session_id:
            return{
                statusCode : 400,
                body : "Missing required path parameter: id"
            }
        else:
            print(session_id)
            # Retrieve the existing session from the database
            sessiondata = sessionsTable.get_item(Key={'id': session_id}).get('Item')['sessiondata']

        #------------------------------------#
        # Process the BATTLE ROUND actions...#
        #------------------------------------#
        if event['queryStringParameters']['action'] == 'battle': #---------------------------------------------------------------------------------------------------------
            # Process the 'battle' action
            #cCount  = int(event['queryStringParameters']['count'])

            if len(sessiondata['challengesDeck']['cards']) == 0:
                # Create the challenges list  and shuffle it
                challengeIds = get_cfg_type_ids('challenges')
                shuffle(challengeIds)
                sessiondata['challengesDeck']['cards'] = challengeIds
                sessiondata['challengesDeck']['next_index'] = 0

            if len(sessiondata['defensesDeck']['cards']) == 0:
                # Create the defenses list and shuffle it
                defenseIds = get_cfg_type_ids('defenses')
                shuffle(defenseIds)
                sessiondata['defensesDeck']['cards'] = defenseIds
                sessiondata['defensesDeck']['next_index'] = 0

            # Deal challenges to the Cloudjacker
            jacker = event['queryStringParameters']['cj']
            if len(sessiondata[jacker]['challenges']) == 0:
                cCount = 2
            else:
                cCount = 1
            #for challenge in challengeIds[0:cCount]:
            idx = int(sessiondata['challengesDeck']['next_index'])
            idx2 = idx + cCount
            for challenge in sessiondata['challengesDeck']['cards'][idx:idx2]:
                cardDict = {'service' : challenge, 'suit':'', 'face':''}
                add_details(cardDict, challenge,'challenges')
                sessiondata[jacker]['challenges'].append(cardDict)
            sessiondata['challengesDeck']['next_index'] += cCount

            # Deal defenses to Cybersecurity
            security = event['queryStringParameters']['cs']
            if len(sessiondata[security]['defenses']) == 0:
                cCount = 2
            else:
                cCount = 1
            #for defense in defenseIds[0:cCount]:
            idx = int(sessiondata['defensesDeck']['next_index'])
            idx2 = idx + cCount
            for defense in sessiondata['defensesDeck']['cards'][idx:idx2]:
                cardDict = {'service': defense, 'suit':'', 'face':''}
                add_details(cardDict, defense, 'defenses')
                sessiondata[security]['defenses'].append(cardDict)
            sessiondata['defensesDeck']['next_index'] += cCount
            sessiondata['battleResp'] = {}
            
            # If dealer is the jacker, we can also figure out what attack card they should use
            if jacker == 'dealer':
                # The attacks in the dealer's hand
                attacks = [at['service']for at in sessiondata[jacker]['challenges']]
                # The services in security's hand that can be targetted by the attacks
                targets = [srv['service'] for srv in sessiondata[security]['hand']]
                # The services detailed information:
                services = {card['service']:{'name': card['details']['name'], 'category':card['details']['category']} for card in sessiondata[security]['hand']}
                # Details of the defenses in security's hand:
                defenses = {dfn['service']:{'name': dfn['details']['name'], 'explain':dfn['details']['explain']} for dfn in sessiondata[security]['defenses']}
                # Details of the challenges in jacker's hand:
                challenges = {chlg['service']:{'name': chlg['details']['name'], 'targets': chlg['details']['targets'], 'neutralizers': chlg['details']['neutralizers'], 
                            'immune': chlg['details']['immune'], 'reasons': chlg['details']['reasons']} 
                            for chlg in sessiondata[jacker]['challenges']}
                # Retrieve the categories details from configsTable:
                response = configsTable.query(
                    KeyConditionExpression=Key('config').eq('categories')
                )
                categories = {cat['id']: cat['cfgdata']for cat in response['Items']}
                comments = [] # This will contain the line-by-line analysis
                useAttack = launchChallenge(attacks, targets, services, challenges, comments)
                # Flag the used challenge card
                for card in sessiondata['dealer']['challenges']:
                    if card['service'] == useAttack:
                        card['used'] = 1
                sessiondata['battleResp'] = {'attack': useAttack}
                sessiondata['battlePlay'] = comments
            
        elif event['queryStringParameters']['action'] == 'defend':#---------------------------------------------------------------------------------------------------------
            # Process the 'defend' action
            jacker  = event['queryStringParameters']['cj']
            security = event['queryStringParameters']['cs']
            attack = event['queryStringParameters']['atck']
            battleData = get_battle_data(sessiondata, security, jacker)
            targets = battleData['targets']
            services = battleData['services']
            defenses = battleData['defenses']
            challenges = battleData['challenges']
            categories = battleData['categories']

            comments = [] # This will contain the line-by-line analysis
            useDefense = defendChallenge(defenses, attack, targets, categories, services, defenses, challenges, comments)

            # Flag the challenge used
            for atck in sessiondata[jacker]['challenges']:
                if atck['service'] == attack:
                    atck['used'] = 1
                    break

            # Flag the used defense card
            for defns in sessiondata[security]['defenses']:
                if (useDefense and defns['service'] == useDefense['defense']):
                    defns['used'] = 1
                    break

            # Flag the services hit
            for hit in useDefense['servicesHit']:
                for sce in sessiondata[security]['hand']:
                    if sce['service'] == hit:
                        sce['used'] = 1
                        break

            if not useDefense['defense']:
                addComment(comments, 'bad', "THE CHALLENGE HAD IMPACT!")
                #mark the first defense card as used because one must be.
                sessiondata[security]['defenses'][0]['used'] = 1
                useDefense['defense'] = sessiondata[security]['defenses'][0]['service']

            #addComment(comments, '', '-----------------------------------------------------------------')
            sessiondata['battlePlay'] = comments
            sessiondata['defResp'] = useDefense


        elif event['queryStringParameters']['action'] == 'judge':#---------------------------------------------------------------------------------------------------------
            # A challenge was launched. The parameters are 'cj' for CloudJacker , 'cs' for CloudSecurity, and 'atck' for the attack card used
            # The values for cj and cs can be 'dealer' or 'player'
            jacker  = event['queryStringParameters']['cj']
            security = event['queryStringParameters']['cs']
            attack = event['queryStringParameters']['atck']
            shield = event['queryStringParameters']['dfns']
            battleData = get_battle_data(sessiondata, security, jacker)
            targets = battleData['targets']
            services = battleData['services']
            defenses = battleData['defenses']
            challenges = battleData['challenges']
            categories = battleData['categories']
            comments = [] # This will contain the line-by-line analysis

            # Call the judgeBattle function
            challengeStatus = judgeBattle(shield, attack, targets, categories, services, defenses, challenges, comments)
            sessiondata['battlePlay'] = comments

            # Flag the attack as used
            for att in sessiondata[jacker]['challenges']:
                if att['service'] == attack:
                    att['used'] = 1
            # Flag the shield as used
            for defns in sessiondata[security]['defenses']:
                if defns['service'] == shield:
                    defns['used'] = 1
            # Flag all successfully targeted services as used
            if challengeStatus =='ATK-GOOD':
                for targ in targets:
                    for card in sessiondata[security]['hand']:
                        if card['service'] == targ:
                            card['used'] = 1
            sessiondata['battleResp'] = challengeStatus

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