console.log("[DEBUG] script.js charge !");

function playMusic() {
    var track = document.getElementById('track').value;
    fetch('/play', {
        method: 'POST',
        body: new URLSearchParams({ "track": track })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('musicStatus').innerText = "Lecture : " + data.track;
        console.log("[DEBUG] Musique en lecture :", data.track);
    })
    .catch(error => {
        console.error('[ERREUR] Impossible de jouer la musique:', error);
    });
}

// Arret de la musique
function stopMusic() {
    fetch('/stop', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        document.getElementById('musicStatus').innerText = "Musique arretee";
        console.log("[DEBUG] Musique arretee");
    })
    .catch(error => {
        console.error('[ERREUR] Impossible d arreter la musique:', error);
    });
}
