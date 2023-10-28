document.querySelectorAll('.contact-button').forEach(button => {
    button.addEventListener('click', function() {
        const serviceId = this.getAttribute('data-service-id');
        openPopup();
        // Дополнительная логика для передачи serviceId в форму всплывающего окна
    });
});

function openPopup() {
    document.getElementById('contact-popup').style.display = 'block';
}

function closePopup() {
    document.getElementById('contact-popup').style.display = 'none';
}

function submitPhoneNumber() {
    const phoneNumber = document.getElementById('phone-input').value;
    // Логика для отправки номера телефона на сервер и обработки
}

document.querySelectorAll('.btn[data-bs-toggle="modal"]').forEach(button => {
    button.addEventListener('click', function() {
        document.getElementById('service_name').value = button.getAttribute('data-service');
    });
});