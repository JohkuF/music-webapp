window.onload = function (data) {
  // Your code here

  if (window.appData) {
    // Turn on votes when needed
    var likes = window.appData.likes;
    likes.forEach((like) => {
      let voteType = like["vote_type"];
      let targetId = like["target_id"];
      if (voteType === "upvote" || voteType === "downvote") {
        // Turn upvote or downvote on
        let voteOFF = document.getElementById(`${voteType}-off-${targetId}`);
        toggle(voteOFF);
      }
    });
  }
};

function updateVoteOnScreen(newVote, id) {
  // Get the count element
  let count = document.getElementById(`count-${id}`);
  if (count) {
    let voteCount = parseInt(count.textContent);

    // Find the previous vote object
    let prevVoteObj = window.appData.likes.find(
      (like) => like.target_id === id
    );
    let prevVote = prevVoteObj ? prevVoteObj.vote_type : null;

    // Determine the change in vote
    if (prevVote === newVote) {
      return;
    }
    // Update the vote count based on the new vote type
    if (prevVote === "upvote") {
      voteCount--;
    } else if (prevVote === "downvote") {
      voteCount++;
    }

    if (newVote === "upvote") {
      voteCount++;
    } else if (newVote === "downvote") {
      voteCount--;
    }

    count.textContent = `${voteCount}`;
  } else {
    console.log(`Element with ID "count-${id}" not found.`);
  }
}

function updateAppData(id, type) {
  let prevVoteObj = window.appData.likes.find((like) => like.target_id === id);
  if (prevVoteObj) {
    prevVoteObj["vote_type"] = type;
  } else {
    window.appData.likes.push({
      target_id: id,
      target_type: "song",
      vote_type: type,
    });
  }
}

function toggleVote(icon) {
  console.log(window.appData.likes);

  var change = toggle(icon);
  var [type, _, id] = icon.id.split("-");
  id = parseInt(id);

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
  if (change === "off") {
    type = "nonevote";
  }

  updateVoteOnScreen(type, id);

  // Update appData
  updateAppData(id, type);

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
