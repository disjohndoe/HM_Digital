const { invoke } = window.__TAURI__.core;

function $(id) { return document.getElementById(id); }

function updateUI(state) {
  // Cloud connection
  const cloudDot = $("cloud-dot");
  const cloudLabel = $("cloud-label");
  const cloudDetail = $("cloud-detail");
  if (state.ws_connected) {
    cloudDot.className = "dot green";
    cloudLabel.textContent = "Spojeno na oblak";
    cloudDetail.textContent = "";
  } else {
    cloudDot.className = "dot red";
    cloudLabel.textContent = "Nije spojeno na oblak";
    cloudDetail.textContent = "";
  }

  // Smart card
  const cardDot = $("card-dot");
  const cardLabel = $("card-label");
  const cardDetail = $("card-detail");
  if (!state.reader_available) {
    cardDot.className = "dot gray";
    cardLabel.textContent = "Čitač nije pronađen";
    cardDetail.textContent = "";
  } else if (state.card_inserted) {
    cardDot.className = "dot green";
    cardLabel.textContent = "Kartica umetnuta";
    cardDetail.textContent = state.card_holder || "";
  } else {
    cardDot.className = "dot red";
    cardLabel.textContent = "Čitač pronađen — umetnite karticu";
    cardDetail.textContent = "";
  }

  // VPN
  const vpnDot = $("vpn-dot");
  const vpnLabel = $("vpn-label");
  const vpnDetail = $("vpn-detail");
  if (state.vpn_connected) {
    vpnDot.className = "dot green";
    vpnLabel.textContent = "VPN spojen";
    vpnDetail.textContent = state.vpn_name || "";
  } else {
    vpnDot.className = "dot red";
    vpnLabel.textContent = "VPN nije spojen";
    vpnDetail.textContent = "";
  }

  // Error
  const errorBox = $("error-box");
  if (state.last_error) {
    errorBox.style.display = "block";
    errorBox.textContent = state.last_error;
  } else {
    errorBox.style.display = "none";
  }
}

async function poll() {
  try {
    const state = await invoke("get_connection_state");
    updateUI(state);
  } catch (e) {
    console.error("Failed to get state:", e);
  }
}

// Initial + poll every 2 seconds
poll();
setInterval(poll, 2000);
