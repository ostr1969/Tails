// modals.js
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
    document.getElementById('modalOverlay').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    document.getElementById('modalOverlay').style.display = 'none';
}

function closeAllModals() {
    var modals = document.getElementsByClassName('modal');
    for (var i = 0; i < modals.length; i++) {
        modals[i].style.display = 'none';
    }
    document.getElementById('modalOverlay').style.display = 'none';
}
