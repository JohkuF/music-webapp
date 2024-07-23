
function toggleVote(icon) {
  var change = toggle(icon);

  // Turn off the other vote
  // Check if the other vote is on -> turn it off
  if (checkOthervote(icon)) {
    const otherVoteON = getOtherVoteON(icon);
    const otherVoteOFF = getOtherVoteOFF(icon);

    // Check which one has the "d-none"
    if (
      otherVoteOFF.getAttribute("class").includes("d-none") &&
      change === "on"
    ) {
      toggle(otherVoteON);
    }
  }

  // Send info to server
  var change = toggle(icon);
  var [type, _, id] = icon.id.split("-");

  if (change === "off")
  {
    type = "nonevote";
  }

  // Send request to backend
  sendPostRequestFetch("/v", parseInt(id), type);
}

function toggle(icon) {
  var otherId = icon.id;
  var change = otherId.split("-")[1];

  if (change === "on") {
    otherId = otherId.replace("on", "off");
    change = "off";
  } else {
    otherId = otherId.replace("off", "on");
    change = "on";
  }

  var other = icon.parentElement.querySelector("#" + otherId);

  var clickedClass = icon.getAttribute("class");

  clickedClass += " d-none";
  other.classList.remove("d-none");

  // Set change
  icon.setAttribute("class", clickedClass.trim());

  return change;
}

function checkOthervote(icon) {
  /*
  Check if other vote is on or off
  on -> True
  off -> False
  */

  var otherVote = getOtherVoteON(icon);

  // Get other vote

  // Check if the "on" has d-none
  if (otherVote.getAttribute("class").includes("d-none")) {
    return false;
  }
  return true;
}

function getOtherVoteON(icon) {
  /*
  The other vote (upvote, downvote) ON-version
  */
  var otherVoteId = getOtherVoteId(icon);
  otherVoteId = otherVoteId.replace("off", "on");

  var otherVote = icon.parentElement.parentElement.parentElement.querySelector(
    "#" + otherVoteId
  );
  return otherVote;
}

function getOtherVoteOFF(icon) {
  /*
  The other vote (upvote, downvote) ON-version
  */
  var otherVoteId = getOtherVoteId(icon);
  otherVoteId = otherVoteId.replace("on", "off");
  var otherVote = icon.parentElement.parentElement.parentElement.querySelector(
    "#" + otherVoteId
  );
  return otherVote;
}

function getOtherVoteId(icon) {
  var otherVoteId = icon.id;
  if (otherVoteId.startsWith("upvote")) {
    otherVoteId = otherVoteId.replace("upvote", "downvote");
  } else {
    otherVoteId = otherVoteId.replace("downvote", "upvote");
  }

  return otherVoteId;
}

function sendPostRequestFetch(url, id, type) {
  const data = {
    id: id,
    type: type,
  };

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Success:", data);
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}
