/**
 * Configuration de l'API
 * Note : J'utilise l'ID du client récupéré dans l'URL pour personnaliser les requêtes
 */
const urlParams = new URLSearchParams(window.location.search);
const clientId = urlParams.get('id') || 'default'; // Repli sur 'default' si pas d'ID
const BASE_API_URL = 'https://bnp.com/api/client';


function getUrlParameters() {
    // 1. On récupère la partie "?id=c001&name=floran..." de l'URL
    const queryString = window.location.search;
    
    // 2. On crée un objet URLSearchParams pour parser cette chaîne
    const urlParams = new URLSearchParams(queryString);
    
    // 3. On transforme le tout en un objet JavaScript classique
    // entries() retourne un itérateur de paires [clé, valeur]
    const params = Object.fromEntries(urlParams.entries());
    
    return params;
}

/**
 * Fonction générique pour récupérer les données d'un bloc spécifique
 */
async function fetchBlockData(blockId) {
    try {
        // Exemple d'URL : https://bnp.com/api/client/Coo01/profile
        const response = await fetch(`${BASE_API_URL}/${clientId}/${blockId}`);
        if (!response.ok) throw new Error(`Erreur pour le bloc ${blockId}`);
        return await response.json();
    } catch (error) {
        console.error(error);
        return null; // Retourne null en cas d'échec pour gérer l'affichage proprement
    }
}

/**
 * Remplit une section avec une liste de données
 */
function renderDataList(sectionElement, data) {
    if (!data) {
        sectionElement.innerHTML += `<p style="color:red; font-size:0.8rem;">Impossible de charger les données.</p>`;
        return;
    }

    // Création de la liste <ul>
    const ul = document.createElement('ul');
    ul.style.listStyle = 'none'; // Style simple sans puces
    ul.style.padding = '0';
    ul.style.marginTop = '10px';

    // On parcourt chaque clé/valeur de l'objet reçu
    for (const [key, value] of Object.entries(data)) {
        const li = document.createElement('li');
        li.style.marginBottom = '5px';
        li.style.fontSize = '0.9rem';
        
        // Formatage : "Clé : Valeur" (avec la clé en gras)
        li.innerHTML = `<strong>${key} :</strong> <span>${value}</span>`;
        
        // On applique la couleur verte de la charte aux valeurs
        li.querySelector('span').style.color = '#008453';
        
        ul.appendChild(li);
    }

    sectionElement.appendChild(ul);
}

/**
 * Initialisation du dashboard
 */
async function initDashboard() {
    // On récupère toutes les sections dans la div "dashboard"
    const sections = document.querySelectorAll('.dashboard section');

    // Pour chaque bloc, on fetch et on affiche
    for (const section of sections) {
        const blockId = section.id; // profile, funding, history, etc.
        const data = await fetchBlockData(blockId);
        renderDataList(section, data);
    }
}

/**
 * Gestion du bouton Reset
 */
document.querySelector('header button').addEventListener('click', () => {
    window.location.reload();
});

// Lancement au chargement du DOM
document.addEventListener('DOMContentLoaded', initDashboard);