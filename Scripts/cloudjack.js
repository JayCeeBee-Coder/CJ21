// Disclaimer: There is room for improvements. This code isn't as organized as I would like to but priority had to be given to making it work.
// A lot had to be developed in a short timeline.

// DOM elements ------------------------------------------------
// Note: Future version may use a more structured approach or even a lightweight framework for UI updates.
const API_ENDPOINT = "https://api.cloudjack-21.com"
const about = document.getElementById("about");
const sound = document.getElementById("sound");
const sessionID = document.getElementById("sessionID");
const sessionRound = document.getElementById("sessionRound");
const loader = document.getElementById("loadindic");
const reset = document.getElementById("reset_button");
const deal = document.getElementById("deal_button");
const hit = document.getElementById("hit_button");
const stand = document.getElementById("stand_button");
const battle = document.getElementById("battle_button");
const action = document.getElementById("action_button");
const hudisplay = document.getElementById("hudispContent");
const pipdisp = document.getElementById("pipdisp");
const pipdispTxt = document.getElementById("pipDispContent");
const closepip = document.getElementById("closePip");
const playerServices = document.getElementById("pServicesTab");
const playerChallenges = document.getElementById("pAttacksTab");
const playerDefenses = document.getElementById("pDefensesTab");
const dealerHand = document.getElementById("dealer_hand");
const dProgress = document.getElementById("d_progress");
const dProgressValue = document.getElementById("d_progVal");
const pProgress = document.getElementById("p_progress");
const pProgressValue = document.getElementById("p_progVal");
const dResult = document.getElementById("dealerResult");
const pResult = document.getElementById("playerResult");
const playerRole = document.getElementById("playerRole");
const dealerRole = document.getElementById("dealerRole");
const pSCard = document.getElementById("playerSC");
const dSCard = document.getElementById("dealerSC");
const pActionCard = document.getElementById("playersActionCard");
const dActionCard = document.getElementById("dealersActionCard");

// Game state variables-----------------------------
// Note: Future version may encapsulate these into a game state object or class to better manage the game's state.
var prCode = ""; //To hold the player role's code
var dealFlag = true; //I need to know if we just dealt so I don't reveal a possible dealer bust too soon.
var round = 1;
var firstBattle = false; // I need to know if the first battle has happened.
var phase = "21"; // Knowing if were in a 21 or battle phase helps better tailor the messaging
var pBust = false; // Was player previously busted?
var dBust = false; // Was dealer previously busted?
var dealerTotal = 0;
var playerTotal = 0;
var soundOn = true;

// Game sounds -------------------------------------
const casinoMusic = new Audio('https://cloudjack-21.com/sounds/Casino.mp3');
casinoMusic.loop = true;
const suspenseMusic = new Audio('https://cloudjack-21.com/sounds/Suspense.mp3');
suspenseMusic.loop = true;
const ticking = new Audio('https://cloudjack-21.com/sounds/Clock.mp3');
ticking.loop = true;
ticking.volume = 0.2; // Adjusting for audio file relative level
const cheers = new Audio('https://cloudjack-21.com/sounds/Cheers.mp3');
cheers.volume = 0.3; // Adjusting for audio file relative level
const aww = new Audio('https://cloudjack-21.com/sounds/Aww.mp3');
const bell = new Audio('https://cloudjack-21.com/sounds/Ding.mp3');
bell.volume = 0.2; // Adjusting for audio file relative level
const bustSound = new Audio('https://cloudjack-21.com/sounds/Bust.mp3');
bustSound.volume = 0.4; // Adjusting for audio file relative level
const resetSound = new Audio('https://cloudjack-21.com/sounds/Reset.mp3');

about.addEventListener("click", function() { //--------------------------------------------------------------------------------------------------------------------------------------------
    // The "About" info screen...
    pipdispTxt.innerHTML = "CLOUDJACK-21 is an independent game project and is not designed, built, or operated by Amazon Web Services (AWS).\
     This game was created by JC Boissy, an AWS Cloud Institute learner as an entry for a Game Builders Challenge, with the primary goal of furthering their\
      understanding of AWS and its services. While the game utilizes AWS technologies, it is not affiliated with, endorsed by, or supported by AWS\
       in any official capacity. Any references to AWS within the game are solely for educational and demonstrative purposes.";
    openpipdisp();
})

sound.addEventListener("click", function() { //--------------------------------------------------------------------------------------------------------------------------------------------
    // Toggles the game music and sound effects
    if (soundOn) {
        soundOn = false;
        sound.textContent = '🔇'
        casinoMusic.muted = true;
        suspenseMusic.muted = true;
        ticking.muted = true;
        cheers.muted = true;
        aww.muted = true;
        bell.muted = true;
        bustSound.muted = true;
        resetSound.muted = true;
    } else {
        soundOn = true;
        sound.textContent = '🔉';
        casinoMusic.muted = false;
        suspenseMusic.muted = false;
        ticking.muted = false;
        cheers.muted = false;
        aww.muted = false;
        bell.muted = false;
        bustSound.muted = false;
        resetSound.muted = false;
    }
})

reset.addEventListener("click", resetGame);
deal.addEventListener("click", f_deal);
hit.addEventListener("click", f_hit);
stand.addEventListener("click", f_stand);
battle.addEventListener("click", f_battle);
action.addEventListener("click", f_action);
closepip.addEventListener("click", function() {
    closepipdisp();
});

function getCookie(name) { //--------------------------------------------------------------------------------------------------------------------------------------------
    // I am actually not using the browser-side cookie in thsi version, but who knows what the future holds?...
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

async function f_deal(){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Starts dealing cards for the first round
    casinoMusic.play(); // Start playing the audio
    phase = "21";
    try{
        dealFlag = true;
        sessionRound.textContent = round;
        hudisplay.textContent = ""; 
        sendToHUD("Dealing...");
        disable(deal);
        loader.style.visibility = "visible";
        const apiUrl = API_ENDPOINT + "/sessions/?action=deal";
        resp = await postToAPI(apiUrl);
        dealerHand.innerHTML = "";
        playerServices.innerHTML = "";
        process21Response(resp);
        sessionID.textContent = resp.id;
        loader.style.visibility = "hidden";
        if (resp.decision == "none") {
            enable(hit);
            enable(stand);
            sendToHUD("Hit / Stand?", "whitefont");
        }
        document.getElementById("sceTab").click();
    } catch (error) {
        sendToHUD(error.name);
        sendToHUD(error.message);
        console.error(error.stack);
        console.error(error.message);
    }
}

async function f_hit(){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Player hits
    phase = "21";
    sendToHUD("Player hits...");
    sessionRound.textContent = round;
    loader.style.visibility = "visible";
    const apiUrl = API_ENDPOINT + "/sessions/" + sessionID.textContent + "?action=hit";
    resp = await postToAPI(apiUrl);
    process21Response(resp);
    document.getElementById("sceTab").click();
    if(pResult.textContent != "BUST!" && dResult.textContent != "BUST!" && pResult.textContent != "21") {
        sendToHUD("Hit / Stand?", "whitefont");
    };
    loader.style.visibility = "hidden";
}

async function f_stand(){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Player stands
    phase = "21";
    dealFlag = false;
    sendToHUD("Player stands...");
    sessionRound.textContent = round;
    loader.style.visibility = "visible";
    try {
        const apiUrl = API_ENDPOINT + "/sessions/" + sessionID.textContent + "?action=stand";
        resp = await postToAPI(apiUrl);
        process21Response(resp);
        loader.style.visibility = "hidden";
    } catch (error) {
        sendToHUD(error.name);
        sendToHUD(error.message);
        console.error(error.stack);
        console.error(error.message);
    }
}

async function f_battle(){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // This starts the battle round when the player assumes a role
    casinoMusic.pause(); 
    ticking.pause();
    suspenseMusic.play();
    firstBattle = true;
   phase = "battleStart";
    sessionRound.textContent = round;
    disable(battle);
    sendToHUD('"AssumedRoleUser": {', "greenfont");
    sendToHUD('...."AssumedRoleId":"' + playerRole.textContent + ':s3-battle-phase"', "greenfont");
    sendToHUD('}', "greenfont");
    try{
        // Post battle call to the dealer API
        var tabToActivate = "atkTab"
        if (playerRole.textContent == "CLOUDJACKER"){
            params = "?action=battle&cj=player&cs=dealer";
            sendToHUD("You have challenge cards available to be used against your opponent. Chose your move wisely!", "whitefont");
        } else {
            params = "?action=battle&cj=dealer&cs=player";
            sendToHUD("You have been delt defense cards to protect your infrastructure.", "whitefont");
            tabToActivate = "defTab";
        }
        const apiUrl = API_ENDPOINT + "/battle/" + sessionID.textContent + params;
        resp = await postToAPI(apiUrl);

        revealBattleCards(resp);

        if (resp.battleResp.attack){
            // Unmask the dealer's defense card. It is no  longer a mistery
            const actCard = findSceCard(resp.battleResp.attack, 'challenge',dealerHand);
            actCard.classList.remove("masked");
            sendToHUD("You have been challenged by the Cloudjacker. Prepare your defense...", "orangefont");
            placeDlrActionCard(actCard);
        }

        document.getElementById(tabToActivate).click();

    } catch (error) {
        sendToHUD("Something went wrong! Please consider replrting it to help us correct.", "orangefont")
        sendToHUD(error.name);
        sendToHUD(error.message);
        console.error(error.stack);
        console.error(error.message);
    }
}

async function f_action(){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Player's action: challenge/defense...
    loader.style.visibility = "visible";
    phase = "battle";
    disable(action);
    try{
        sendToHUD(theCard.dataset.description, 'whitefont');
        sendToHUD('')
        if (playerRole.textContent == "CLOUDJACKER"){
            atck = pActionCard.dataset.id;
            sendToHUD("Throwing challenge...!", "whitefont");
            const apiUrl = API_ENDPOINT + "/battle/" + sessionID.textContent + "?action=defend&cj=player&cs=dealer&atck=" + atck;
            resp = await postToAPI(apiUrl);
            if (resp.defResp.defense){
                const actCard = findSceCard(resp.defResp.defense, 'defense',dealerHand);
                actCard.classList.remove("masked");
                placeDlrActionCard(actCard);
            };
        } else {
            atck = dActionCard.dataset.id;
            dfns = pActionCard.dataset.id;
            sendToHUD("Deploying defense...!", "whitefont");
            const apiUrl = API_ENDPOINT + "/battle/" + sessionID.textContent + "?action=judge&cj=dealer&cs=player&atck=" + atck + "&dfns=" + dfns;
            resp = await postToAPI(apiUrl);
        };

        showPlayByPlay(resp.battlePlay);
        cardsUsed = [];
        // Remove used card, but not defense cards, which remain valid through the game.
        dActionCard.classList.add("used");
        pActionCard.classList.add("used");

        resp.dealer.hand.forEach((card) => { // Dealer service cards...
            if (card.used == 1) {
                usedCard = findSceCard(card.service, 'service', dealerHand);
                usedCard.classList.add("used");
                cardsUsed.push(usedCard);
            }
        });

        resp.dealer.challenges.forEach((card) => { // Dealer challenge cards...
            if (card.used == 1) {
                usedCard = findSceCard(card.service, 'challenge', dealerHand);
                usedCard.classList.add("used");
                cardsUsed.push(usedCard);
            }
        });

        resp.player.hand.forEach((card) => { // Player service cards...
            if (card.used == 1) {
                usedCard = findSceCard(card.service, 'service', playerServices);
                document.getElementById("sceTab").click();
                usedCard.classList.add("used");
                cardsUsed.push(usedCard);
            }
        });

        resp.player.challenges.forEach((card) => { // Player challenge cards...
            if (card.used == 1) {
                usedCard = findSceCard(card.service, 'challenge', playerChallenges);
                document.getElementById("atkTab").click();
                usedCard.classList.add("used");
                cardsUsed.push(usedCard);
            }
        });

        // Give the animation 4 sec to play, then remove the cards. This gives the user a visual of what's happening
        setTimeout(() => {
            clearActionCards();
            cardsUsed.forEach((card) => {
                card.remove();
            });
        }, 2000);

        // Call API to clean the session of non-defense used cards
        const apiUrl = API_ENDPOINT + "/sessions/" + sessionID.textContent + "?action=cleanup";
        resp = await postToAPI(apiUrl);

        showScores(resp);

        // Challenge survival gives cybersecurity 10 points
        if (prCode == "DF" && resp.player.hand.length > 0){
            playerTotal += 10;
            sendToHUD("You received an extra 10 percentage cloudscore points for surviving the challenge.");
        } else if(prCode == "CJ" && resp.dealer.hand.length > 0) {
            dealerTotal += 10;
            sendToHUD("Dealer received 10 extra points for surviving the challenge.");
        }

        // Update CloudScores (Totals)
        if (!pBust && pResult.textContent == "BUST!"){
            playerTotal += res_to_int(pResult.textContent, true);
            pBust = true;
        } else {
            playerTotal += res_to_int(pResult.textContent);
        };
        if (playerTotal < 0) {
            playerTotal = 0;
        } else if (playerTotal > 100) {
            playerTotal = 100; // 100% is where the game ends
        };
        pProgress.style.setProperty("--progress", `${playerTotal}%`);
        pProgressValue.textContent = `${playerTotal}%`;

        if (!dBust && dResult.textContent == "BUST!"){
            dealerTotal += res_to_int(dResult.textContent, true);
            dBust = true;
        } else {
            dealerTotal += res_to_int(dResult.textContent);
        };
        if (dealerTotal < 0) {
            dealerTotal = 0;
        } else if (dealerTotal > 100) {
            dealerTotal = 100;
        };
        dProgress.style.setProperty("--progress", `${dealerTotal}%`);
        dProgressValue.textContent = `${dealerTotal}%`;

        // Set up next round if warranted...
        disable(battle);
        disable(action);
        
        if(pResult.textContent == "BUST!" || dealerTotal == 100){
            // Cases where player loses...
            if(dResult.textContent != '0' && dResult.textContent != "BUST!" ) {
                dProgress.style.setProperty("--progress", `100%`);
                dProgressValue.textContent = `100%`;
            }
            sendToHUD("GAME OVER! YOU DIDN'T WIN THE BATTLE.... But learning is winning.", "orangefont");
            sendToHUD("Please reset the game to play again.", "whitefont");
            casinoMusic.pause(); 
            suspenseMusic.pause();
            aww.play();
            enable(reset);
        } else if ((dResult.textContent == "BUST!" || playerTotal == 100)){
            // Casee where player wins...
            if(pResult.textContent != '0' && pResult.textContent != "BUST!" ) {
                pProgress.style.setProperty("--progress", `100%`);
                pProgressValue.textContent = `100%`;
                sendToHUD("CONGRATULATIONS, YOU WON THE BATTLE!", "greenfont")
                casinoMusic.pause(); 
                suspenseMusic.pause();
                cheers.play();
            }
            sendToHUD("Please reset the game to play again.", "whitefont");
            enable(reset);
        } else { // The game isn't yet over
            enable(hit);
            enable(stand);
            sendToHUD("Starting new round... Hit/Stand?", "whitefont");
            suspenseMusic.pause();
            casinoMusic.play(); 
            enable(reset);
        };

        round += 1;
    } catch (error) {
        sendToHUD(error.name);
        sendToHUD(error.message);
        console.error(error.stack);
        console.error(error.message);
    }
    loader.style.visibility = "hidden";
}

function showPlayByPlay(messages){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // The game battle API returns an array of play by play lines built during challenge or defense assessments. This gives the user insights into the decision process
    for (let i = 0; i <  resp.battlePlay.length; i++ ) {
        let color = "";
        if (messages[i].status == 'good'){
            color = 'greenfont';
        } else if (messages[i].status == 'bad'){
            color = 'orangefont';
        } else if (messages[i].status == 'info'){
            color = 'whitefont';
        } else {
            color = '';
        }

        var comment = messages[i].comment;
        sendToHUD(comment, color);
    };
}

function revealCards(cards, cType, recipient, owner, maskCards = 'no'){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // maskCards can have one of the following values: 'no','first', 'last', or 'all', depending on that cards we want be masked
    c = 0;
    cards.forEach((card) => {
        const exists = findSceCard(card.service, cType, recipient);
        if (exists === undefined){
            c += 1;
            const id = card.service;
            const suit = card.suit;
            const value = card.face;
            const label = card.details.name;
            const image = 'https://cloudjack-21.com/images/' + card.details.image;
            const type = cType;
            const desc = card.details.description;
            var maskedFlag = false;
            // Decide if the card needs to be masked
            if((c == 1 && maskCards == 'first') || (c == cards.length && maskCards == 'last') || (maskCards == 'all')) {
                maskedFlag = true;
            };
            dealCard(id, suit, value, label, image, type, desc, recipient, owner, maskedFlag);
        } else{
            if(exists.dataset.type == 'service' && !dealFlag)
                exists.classList.remove("masked"); // Dealer cards must be revealed since player's turn ended
        }
    });
}

function dealCard(id, suit, value, label, image, type, description, recipient, owner, mask = false){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // This function actually places (paints) cards in the dealer or player's hands as part of the reveal process
    const newCard = document.createElement("div");
    newCard.className = "card-front";
    newCard.dataset.id = id;
    newCard.dataset.suit = suit;
    newCard.dataset.value = value;
    newCard.dataset.label = label;
    newCard.dataset.image = image;
    newCard.dataset.type = type;
    newCard.dataset.description = description;
    newCard.dataset.owner = owner;
    if(mask){
        newCard.classList.add("masked");
    }
    if (recipient == dealerHand) {
        recipient.appendChild(newCard);
    } else {
        recipient.insertBefore(newCard, recipient.firstChild);
    }
    paint(newCard);
    addCardListener(newCard);
}

function revealBattleCards(resp){ //--------------------------------------------------------------------------------------------------------------------------------------------
            // Dealer first. Dealer challenges should be masked.
            var cards = resp.dealer.challenges;
            revealCards(cards, 'challenge', dealerHand, 'dealer', maskCards = 'all');
            cards = resp.dealer.defenses;
            revealCards(cards, 'defense', dealerHand, 'dealer', maskCards = 'all');
            
            // Only the player's cards are revealed. Dealer's attacks and defenses remain secret
            cards = resp.player.challenges;
            revealCards(cards, 'challenge', playerChallenges, 'player');
            cards = resp.player.defenses;
            revealCards(cards, 'defense', playerDefenses, 'player');
}

function addCardListener(newCard){ //--------------------------------------------------------------------------------------------------------------------------------------------
    const owner = newCard.dataset.owner;
    // Listen for doubleClick...
    newCard.addEventListener("dblclick", function(event) {
        // Doubleclick reveals unmasked cards' info 
        theCard = event.currentTarget;
        if(theCard.classList.contains("masked")) {
            pipdispTxt.textContent = "Nice try! ...You know I can't show you this card's information  😀";
        } else {
            pipdispTxt.textContent = event.currentTarget.dataset.description;
        }
        openpipdisp();
    });

    // listen for click on player's challenge or defense cards, which selects them as action cards
    if (owner == "player" && (newCard.dataset.type == "challenge" || newCard.dataset.type == "defense")) {
        newCard.addEventListener("click", function(event) {
            if (phase == "battleStart") { // If the role has been "assumed", which means new actio cards have been dealt...
                theCard = event.currentTarget;
                pActionCard.innerHTML = "";
                pActionCard.style.backgroundColor = `rgb(0, 174, 255, .2)`;
                const pip = createPip(theCard.dataset.image)
                pActionCard.append(pip);
                const label = createLabel(theCard.dataset.label);
                pActionCard.append(label);
                pActionCard.dataset.id = theCard.dataset.id;
                pActionCard.dataset.type = theCard.dataset.type;
                
                if (newCard.dataset.type == "challenge" && playerRole.textContent == "CLOUDJACKER"){
                    enable(action);
                }else{
                    if (newCard.dataset.type == "defense" && playerRole.textContent == "CYBERSECURITY"){
                        enable(action);
                    } else{
                        disable(action);
                    }
                };
            } else {
                sendToHUD("You must assume a battle role to be dealt more cards before you can battle!", "orangefont")
            };
        });
    };
}

function showScores(respBody, both = true){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Formats, and displays the scores...
    var color = "";
    var decision = "";
    if (respBody.decision != "none" && (!dealFlag || respBody.player.result == "JACK")){
        sendToHUD("Dealer Score(s): [" + respBody.dealer.scores + "]");
        sendToHUD("Player Score(s): [" + respBody.player.scores + "]");
        if(respBody.decision == "PLAYR"  && ( Number.isNaN(parseInt(pResult.textContent)) || parseInt(pResult.textContent) > 0)) {
            color = "greenfont";
            decision = "You are leading this stage..."
            playerRole.textContent = "CYBERSECURITY";
            dealerRole.textContent = "CLOUDJACKER";
            action.textContent = "DEFEND";
            prCode = "DF";
            dSCard.style.backgroundImage = "url('https://cloudjack-21.com/images/Cloudjacker.svg')";
            pSCard.style.backgroundImage = "url('https://cloudjack-21.com/images/21Shield.svg')";
            enable(battle);
        }
        else if(respBody.decision == "DEALR"  && ( Number.isNaN(parseInt(dResult.textContent)) || parseInt(dResult.textContent) > 0)) {
            color = "orangefont";
            decision = "Dealer is leading this stage..."
            dealerRole.textContent = "CYBERSECURITY";
            playerRole.textContent = "CLOUDJACKER";
            action.textContent = "CHALLENGE";
            prCode = "CJ";
            pSCard.style.backgroundImage = "url('https://cloudjack-21.com/images/Cloudjacker.svg')";
            dSCard.style.backgroundImage = "url('https://cloudjack-21.com/images/21Shield.svg')";
            enable(battle);
        } else if (round == 1) {
            color = "whitefont";
            decision = "PUSH!"
        } else {
            decision = "This battle is intense..."
            respBody.decision = "none" // To avoid a "PUSH" deadlock situation, since we want the game to cpntinue as long as neither player, nor dealer busted.
            enable(battle);
        };
        both = true;
    }
    if(both){ // We need to also show the dealer's score
        let sc = String(respBody.dealer.scores).replaceAll(",", " / ");
        const resdict = formatRes(respBody.dealer.result, sc);
        var res = resdict.txt;
        dResult.textContent = res;
        dResult.className = resdict.col;
    }

    let sc = String(respBody.player.scores).replaceAll(",", " / ");
    const resdict = formatRes(respBody.player.result, sc);
    var res = resdict.txt;
    pResult.textContent = res;
    pResult.className = resdict.col;
    if(decision != ""){ // Give player feedback...
        disable(hit);
        disable(stand);
        sendToHUD(decision, color);
        sendToHUD("----------------------------------------------------------");
        if(respBody.decision == "PUSH"){
            sendToHUD("'RESET' to start a new game!");
            casinoMusic.pause(); 
            suspenseMusic.pause();
            disable(battle);
        } else if (phase == "21") {
            phase_end_messaging();
        } ;
    };
}

function phase_end_messaging(){
    // Display message at the end pf a game stage/phase
    casinoMusic.pause(); 
    suspenseMusic.pause();
    ticking.play();
    if (prCode == "CJ"){
        if(pResult.textContent != "BUST!" && pResult.textContent != "0"){
        sendToHUD("Do not despair! You may still be able to re-claim the lead by assuming the CLOUDJACKER role, and challenging the deader to a cloud battle. Are you ready for it?", "whitefont");
        } else {
            sendToHUD("You may still be able to deny your opponent the victory by assuming the CLOUDJACKER role, and challenging the deader to a cloud battle...", "whitefont");
            sendToHUD("...But you must beat ALL their service cards with one challenge!", "whitefont");
        };  
    } else if(prCode == "DF"){
    sendToHUD("You must now assume the CYBERSECURITY role and protect your infrastructure against the Cloudjacker's challenges. Ready for the battle?", "whitefont");
    };
}


function res_to_int(res, bustPenalty = false){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Converts the result into a numerical score value
    if(bustPenalty){
        res = res.replace("BUST!", "-11");
        sendToHUD("BUST penalty: " + res);
    } else{
        res = res.replace("BUST!", "0");
    }
    return parseInt(res);
}


function formatRes(res, sc) { //--------------------------------------------------------------------------------------------------------------------------------------------
    // Formats the result for display
    var color = "";
    var jack = "21";
    res = res.replace("none", sc);
    res = res.replace("BUST","BUST!");
    res = res.replace("JACK", jack);
    if(res == jack){
        bell.play();
        color = "greenfont";
    } else if(res == "BUST!"){
        bustSound.play();
        color = "orangefont";
    }
    const dict = {
        txt : res,
        col : color
    }
    return dict;
}

async function postToAPI(apiUrl){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Makes calls to game APIs
    const requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    };
    try {
        const response = await fetch(apiUrl, requestOptions);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const jsonResp = await response.json();
        return jsonResp;
    } catch (error) {
        sendToHUD("Something went wrong! Please consider replrting it to help us correct.", "orangefont")
        sendToHUD(error);
        console.error(error.message);
    }
}

function process21Response(jsonResp){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Blackjack stage response processing
    var cards = jsonResp.dealer.hand;
    var maskCards = 'last';
    if (jsonResp.decision != "none") {
        dealFlag = false;
    }
    if((jsonResp.decision != "none") || jsonResp.player.result == "JACK"){
        if (jsonResp.dealer.scores.length > 1){
            jsonResp.dealer.scores = jsonResp.dealer.scores[-1];
        }
        if (jsonResp.player.scores.length > 1){
            jsonResp.player.scores = jsonResp.player.scores[-1];
        }
        maskCards = 'no';
    }
    revealCards(cards, 'service', dealerHand, 'dealer', maskCards);
    cards = jsonResp.player.hand;
    revealCards(cards, 'service',playerServices, 'player');
    revealBattleCards(jsonResp, true)
    showScores(jsonResp, false);
}

function findSceCard(service, type, hand) { //--------------------------------------------------------------------------------------------------------------------------------------------
    // Gets a hold of specific DOM elements representations of a cards
    const retCard = Array.from(hand.children).find(card => card.dataset.id === service && card.dataset.type == type );
    return retCard;
}

function placeDlrActionCard(theCard){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Shows the dealer's action card in the "holographic" spot on the scoreboard
    dActionCard.innerHTML = "";
    dActionCard.style.backgroundColor = `rgb(0, 174, 255, .2)`;
    const pip = createPip(theCard.dataset.image)
    dActionCard.append(pip);
    const label = createLabel(theCard.dataset.label);
    dActionCard.append(label);
    dActionCard.dataset.id = theCard.dataset.id;
    dActionCard.dataset.type = theCard.dataset.type;
    sendToHUD(theCard.dataset.description, 'whitefont');
    sendToHUD('')
}

function clearActionCards(){//--------------------------------------------------------------------------------------------------------------------------------------------
    // Clears used action card "hologram" after the move
    dActionCard.innerHTML = "";
    pActionCard.innerHTML = "";
    dActionCard.style.backgroundColor = `transparent`;
    pActionCard.style.backgroundColor = `transparent`;
}


function disable(elmnt) { //--------------------------------------------------------------------------------------------------------------------------------------------
    // Disables buttons
    elmnt.disabled = true;
    elmnt.classList.add("disabled");
}

function enable(elmnt) { //--------------------------------------------------------------------------------------------------------------------------------------------
    // Enables buttons
    elmnt.disabled = false;
    elmnt.classList.remove("disabled");
}

function openpipdisp() { //--------------------------------------------------------------------------------------------------------------------------------------------
    // The infopip display is always there. It just gets hidden when not needed
    pipdisp.style.visibility = "visible";
    pipdisp.classList.add("fadein");
}

async function closepipdisp() { //--------------------------------------------------------------------------------------------------------------------------------------------
    // The infopip display is always there. It just gets hidden when not needed
    pipdisp.classList.remove("fadein");
    pipdisp.classList.add("fadeout");
    await new Promise(resolve => setTimeout(resolve, 1000));
    pipdisp.style.visibility = "hidden";
    pipdisp.classList.remove("fadeout");
}


function resetGame() { //--------------------------------------------------------------------------------------------------------------------------------------------
    // The name say it all...
    try{
        casinoMusic.pause(); 
        suspenseMusic.pause();
        ticking.pause();
        resetSound.play();
        enable(deal);
        disable(hit);
        disable(stand);
        disable(battle);
        disable(action);
        sessionID.textContent = "----------";
        round = 1;
        firstBattle = false;
        sessionRound.textContent = round;
        dealerHand.innerHTML = '<span style="opacity: .3 ;font-size:40px; align-self: end;color: lime;">DEALER READY!...</span>';
        playerServices.innerHTML = '<span style="opacity: .3 ;font-size:40px; align-self: end; color: lime;">PLAYER READY!...</span>';
        pResult.className = "";
        dResult.className = "";
        dResult.textContent = "---";
        pResult.textContent = "---";
        playerRole.innerHTML = "---";
        dealerRole.innerHTML = "---";
        action.textContent = "...";
        hudisplay.textContent = ""; 
        dSCard.style.backgroundImage = "url('https://cloudjack-21.com/images/dollar-poker-piece.svg')";
        pSCard.style.backgroundImage = "url('https://cloudjack-21.com/images/poker-chip.svg')";
        playerChallenges.innerHTML = "";
        playerDefenses.innerHTML = "";
        pActionCard.dataset.id = '';
        loader.style.visibility = "hidden";
        clearActionCards();
        document.getElementById("sceTab").click();
        prCode = "";
        pBust = false;
        dBust = false;
        dealerTotal = 0;
        playerTotal = 0;
        dProgress.style.setProperty("--progress", `0%`);
        dProgressValue.textContent = `0%`;
        pProgress.style.setProperty("--progress", `0%`);
        pProgressValue.textContent = `0%`;
        closepipdisp()
    } catch (error) {
        sendToHUD(error);
        console.error(error.message);
    }
}

//Takes a strings and a color classname to output on the HUD
function sendToHUD(content, colorClass=''){ //--------------------------------------------------------------------------------------------------------------------------------------------
    // Directs messages to the main Heads Up display area
    let newElement = document.createElement("span");
    newElement.textContent = content;
    if(colorClass != ''){
        newElement.classList.add(colorClass);
    }
    hudisplay.appendChild(newElement);
    newElement = document.createElement("br");
    hudisplay.appendChild(newElement);
    hudisplay.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

//Initial page load...--------------------------------------------------------------------------------------------------------------------------------------------
enable(deal);
disable(hit);
disable(stand);
disable(battle);
disable(action);
