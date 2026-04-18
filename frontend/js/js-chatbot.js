async function listenButton() {
    // Correction des sélecteurs : on ajoute le "." pour les classes
    const sendButton = document.querySelector(".bottom button");
    const textArea = document.querySelector(".bottom textarea");
    const answerBox = document.querySelector(".answer");

    // Utilisation de addEventListener au lieu de setAttribute
    sendButton.addEventListener('click', async () => {
        const userMessage = textArea.value.trim();

        if (!userMessage) return;

        // 1. Afficher le message de l'utilisateur
        answerBox.innerHTML += `<div class="user-msg"><b>Vous :</b> ${userMessage}</div>`;
        textArea.value = ''; // Vider le champ
        
        // Auto-scroll pendant que l'IA réfléchit
        answerBox.scrollTop = answerBox.scrollHeight;

        try {
            // 2. Appel à l'API FastAPI
            const response = await fetch('http://localhost:5000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage })
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP : ${response.status}`);
            }

            const data = await response.json();

            // 3. Afficher la réponse de l'agent
            console.log(data.response.message.content[0]);
            answerBox.innerHTML += `<div class="agent-msg"><b>Assistant :</b> ${data?.response?.message?.content[0].text}</div>`;
            
            // 4. Auto-scroll final
            answerBox.scrollTop = answerBox.scrollHeight;

        } catch (error) {
            console.error("Erreur lors du fetch :", error);
            answerBox.innerHTML += `<div class="error-msg">⚠️ Erreur : Impossible de contacter l'assistant.</div>`;
            answerBox.scrollTop = answerBox.scrollHeight;
        }
    });

    // Optionnel : Permettre l'envoi avec la touche Entrée (sans Shift)
    textArea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });
}

document.addEventListener('DOMContentLoaded', listenButton);