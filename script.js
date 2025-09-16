// Capturar el formulario
const form = document.getElementById("contactForm");
const response = document.getElementById("formResponse");

// Evento de envío
form.addEventListener("submit", function(e) {
  e.preventDefault();

  const name = document.getElementById("name").value;
  const subject = document.getElementById("subject").value;

  // Mostrar mensaje de confirmación
  response.textContent = `¡Gracias ${name}! Tu solicitud para reforzar en ${subject} ha sido enviada.`;
  response.style.color = "green";

  // Limpiar formulario
  form.reset();
});
