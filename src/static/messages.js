function sanitize(string) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;",
  };
  const reg = /[&<>"'/]/gi;
  return string.replace(reg, (match) => map[match]);
}

async function initMessages(id) {
  // Init songs messages onfocus

  try {
    let messages = appData.messages;
    if (!messages) return;
    // Filter -> Only take own ids
    messages = messages.filter((item) => item.song_id === id);

    const messagesContainer = document.getElementById(
      `messagesContainer-${id}`
    );
    var id_extra = 0;

    messages.reverse().forEach((message) => {
      username = sanitize(message.username);
      content = sanitize(message.content);

      const messageCard = `
          <div class="card mb-4" id="messages-${id}-${id_extra}">
            <div class="card-body">
              <p>${content}</p>
              <div class="d-flex justify-content-between">
                <div class="d-flex flex-row align-items-center">
                <p class="small mb-0 ms-2">${username}</p>
                </div>
              </div>
            </div>
          </div>`;
      id_extra++;

      messagesContainer.insertAdjacentHTML("beforeend", messageCard);
    });
  } catch (error) {
    console.log(error);
  }
}
