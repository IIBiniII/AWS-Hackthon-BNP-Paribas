console.log("hello word")

const API_URL = 'http://192.168.43.135:5000/';

/**
 * 1. FONCTION APPART : Gère uniquement l'appel réseau (Fetch)
 * @returns {Promise<Array>} La liste des clients
 */
async function fetchClientData(data) {
    try {
        let url = API_URL+"clients/search?"
        if (data.id){
            url+=`client_id=${data.id}&`
        }
        if (data.firstName){
            url+=`prenom=${data.firstName}&`
        }
        if (data.lastName){
            url+=`nom=${data.lastName}&`
        }
        if (data.dob){
            url+=`date_naissance=${data.dob}`
        }

        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP : ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Erreur lors de la récupération des données :", error);
        throw error; // On propage l'erreur pour que l'UI puisse la gérer
    }
}

/**
 * 2. FONCTION DE LOGIQUE UI : Gère l'affichage des données
 */
async function loadClients(data) {
    console.log("loadClients")
    const container = document.querySelector('.client-list');
    

    try {
        // On appelle la fonction "appart" pour récupérer les données
        const clients = await fetchClientData(data);
        console.log(clients);
        // On vide le conteneur
        container.innerHTML = '';

        // On crée et injecte chaque ligne client
        clients.clients.forEach(client => {
            const clientRow = createClientElement(client);
            container.appendChild(clientRow);
        });

    } catch (error) {
        console.log(error)
        // Gestion de l'affichage en cas d'erreur
        container.innerHTML = `<p style="color: red; text-align: center;">Impossible de charger les clients.</p>`;
    }
}

/**
 * 3. FONCTION DE RENDU : Crée l'élément HTML pour un client
 */
function createClientElement(data) {
    // Formatage de la date : 2004-07-24 -> 24/07/2004
    const [year, month, day] = data.date_naissance.split("T")[0].split("-");
    
    // Tu peux maintenant l'afficher au format français :
    const formattedDate = `${day}/${month}/${year}`;

    const div = document.createElement('div');
    div.className = 'client-row';
    const targetUrl = `clientsummary.html?id=${data.client_id}`;

    div.innerHTML = `
        <p>id : <span>${data.client_id}</span></p>
        <p>first name : <span>${data.prenom}</span></p>
        <p>last name : <span>${data.nom}</span></p>
        <p>date of birth : <span>${formattedDate}</span></p>
        <p>phone : <span>${data.telephone}</span></p>
        <p>email : <span>${data.email}</span></p>
        <a href="${targetUrl}" class="select-link">Select ❯</a>
    `;

    return div;
}


////////////////
function setupFormListener() {
    const form = document.querySelector('form');
    // On récupère les inputs dans l'ordre du HTML
    const inputs = form.querySelectorAll('input');

    form.addEventListener('input', () => {
        // On récupère les valeurs actuelles pour filtrer
        const filters = {
            id: inputs[0].value.toLowerCase(),
            firstName: inputs[1].value.toLowerCase(),
            lastName: inputs[2].value.toLowerCase(),
            dob: inputs[3].value
        };

        // On relance la génération des lignes
        loadClients(filters);
    });
}
//////////////////////////

/**
 * Initialisation des boutons d'action
 */
function setupActionButtons() {
    // On cible le bouton qui contient le texte "Reste" (ou "Reset")
    const resetBtn = document.querySelector('header button');

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            // Recharge la page actuelle
            window.location.href="http://127.0.0.1:5500/frontend/index.html"
        });
    }
}



// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', loadClients);
setupFormListener()
setupActionButtons(); // La nouvelle fonction
