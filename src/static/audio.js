function toggleIcons(icon) {
  const listPlayIcons = document.querySelectorAll(".icon-play");
  const listPauseIcons = document.querySelectorAll(".icon-pause");
  var clickedIconPlay = icon.parentElement.querySelector(".icon-play");
  var clickedIconPause = icon.parentElement.querySelector(".icon-pause");

  // Current song id
  let = currentSongId = parseInt(clickedIconPlay.id.split("-")[1]);
  let audio = document.getElementById("audio");

  if (icon.classList.contains("icon-pause")) {
    audio.pause();
    clickedIconPlay.classList.toggle("d-none");
    clickedIconPause.classList.toggle("d-none");
    return;
  } else if (parseInt(sessionStorage.songId) === currentSongId) {
    audio.play();
    clickedIconPlay.classList.toggle("d-none");
    clickedIconPause.classList.toggle("d-none");
    return;
  }

  // switch previous off
  const playIconsArray = Array.from(listPlayIcons); // Convert NodeList to array

  playIconsArray.forEach((item, index) => {
    if (
      item.classList.contains("d-none") &&
      parseInt(item.id.split("-")[1]) !== parseInt(icon.id.split("-")[1])
    ) {
      item.classList.toggle("d-none");
      listPauseIcons[index].classList.toggle("d-none");
    }
  });

  // Switch clicked on
  clickedIconPlay.classList.toggle("d-none");
  clickedIconPause.classList.toggle("d-none");

  songName = clickedIconPlay.parentElement.parentElement
    .querySelector("div#songNameContainer")
    .querySelector("p").textContent;

  getAudioSong(currentSongId, songName);

  // Toggle offcanvas on if not already
  // (The popup with the music player)
  getOffCanvas();
}

function getOffCanvas() {
  // Get reference to the offcanvas
  const offcanvas = new bootstrap.Offcanvas(
    document.getElementById("offcanvasScrolling")
  );

  // Toggle the offcanvas
  offcanvas.toggle();
}

function getAudioSong(songId, songName) {
  songContainer = document.getElementById("musicContainer");
  songLabel = document.getElementById("offcanvasBottomLabel");

  sessionStorage.setItem("songId", parseInt(songId));

  const songCard = `
      <div id="musicContainer">
        <audio controls autoplay onended="playNextSong()" style="width: 100%" id="audio">
          <source id="audioSource" src="stream/${songId}" type="audio/mp3" />
        </audio>
      </div>
    `;

  songContainer.innerHTML = songCard;
  songLabel.textContent = songName;
}

function playNextSong() {
  const currentSongId = sessionStorage.getItem("songId");

  let nextSongId = currentSongId;
  const songs = appData.songs;
  songs.forEach((song, index) => {
    if (song.id == currentSongId)
      nextSongId = songs[(index + 1) % songs.length].id;
  });

  // Initilialize the song messages
  initMessages(nextSongId);

  // play the next song
  const svgElement = document.getElementById(`play-${nextSongId}`);
  svgElement.dispatchEvent(new Event("click"));
}
