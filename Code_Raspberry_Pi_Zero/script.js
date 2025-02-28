console.log("[DEBUG] script.js charge !");

// Connexion MQTT
const client = mqtt.connect('ws://192.168.1.17:9001');

client.on('connect', function () {
    console.log("[DEBUG] Connecte a MQTT via WebSocket");

    // S'abonner aux capteurs
    client.subscribe('home/temperature');
    client.subscribe('home/humidity');
    client.subscribe('home/light');
    client.subscribe('home/noise');
    client.subscribe('home/movement');
    client.subscribe('home/fan'); 
});

// Mise a jour des valeurs sur la page
client.on('message', function (topic, message) {
    console.log(`[DEBUG] MQTT -> ${topic}: ${message.toString()}`);

    let elementId = null;
    if (topic === 'home/temperature') elementId = 'temp';
    else if (topic === 'home/humidity') elementId = 'humidity';
    else if (topic === 'home/light') elementId = 'light';
    else if (topic === 'home/noise') elementId = 'noise';
    else if (topic === 'home/movement') elementId = 'movement';
    else if (topic === 'home/fan') elementId = 'fan-state';
    if (elementId) {
        let element = document.getElementById(elementId);
        if (element) {
            element.textContent = message.toString();
        } else {
            console.warn(`[ERREUR] Element #${elementId} introuvable !`);
        }
    }
});

// Gestion des boutons du ventilateur
document.getElementById('btn-niv1').addEventListener('click', function () {
    console.log("[DEBUG] Ventilateur Niveau 1");
    client.publish("home/fan", "niv1");
});

document.getElementById('btn-niv2').addEventListener('click', function () {
    console.log("[DEBUG] Ventilateur Niveau 2");
    client.publish("home/fan", "niv2");
});

document.getElementById('btn-niv3').addEventListener('click', function () {
    console.log("[DEBUG] Ventilateur Niveau 3");
    client.publish("home/fan", "niv3");
});

document.getElementById('btn-off').addEventListener('click', function () {
    console.log("[DEBUG] Ventilateur OFF");
    client.publish("home/fan", "off");
});
