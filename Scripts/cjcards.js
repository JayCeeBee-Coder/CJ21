
function paint(card) { //--------------------------------------------------------------------------------------------------------------------------------------------
  // This function visually represents the cads
  const value = card.dataset.value;
  const label = card.dataset.label;
  const image = card.dataset.image;
  const inFrame = document.createElement("div");
  inFrame.classList.add("inFrame");
  card.append(inFrame);
  inFrame.append(createPip(image));
  inFrame.append(createLabel(label));
  card.append(createCornerNumber("left", value));
  card.append(createCornerImage("right"));
}

function createCornerNumber(position, value) { //--------------------------------------------------------------------------------------------------------------------------------------------
  // This function places the card value on the left corner
  const corner = document.createElement("div");
  corner.textContent = value;
  corner.classList.add("corner");
  corner.classList.add(position);
  return corner;
}

function createCornerImage(position) { //--------------------------------------------------------------------------------------------------------------------------------------------
  // This function adds trhe right corner element that will hold an image representing the card's function: Service / Challenge / Defense
  const corner = document.createElement("div");
  corner.classList.add("corner");
  corner.classList.add(position);
  return corner;
}

function createPip(image) { //--------------------------------------------------------------------------------------------------------------------------------------------
  // This function places the main Picture of the card
  const pip = document.createElement("div");
  pip.style.backgroundImage = "url(" + image + ")";
  pip.classList.add("pip");
  pip.classList.add("glossy");
  return pip;
}

function createLabel(cardLabel) { //--------------------------------------------------------------------------------------------------------------------------------------------
  // Places the card's name/label
  const label = document.createElement("div");
  label.classList.add("card-label");
  label.textContent = cardLabel;
  return label;
}


function openTab(evt, tab) { //--------------------------------------------------------------------------------------------------------------------------------------------
  // This function handles the player's hand tabs
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(tab).style.display = "flex";
  evt.currentTarget.className += " active";
}

// Select the player's services tab
document.getElementById("sceTab").click();