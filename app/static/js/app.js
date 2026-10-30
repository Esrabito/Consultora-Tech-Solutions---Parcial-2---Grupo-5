// Pedimos confirmación antes de enviar los formularios marcados con data-confirmacion
// (por ejemplo, los de eliminar). El texto viaja en un atributo y no dentro del
// código JavaScript, así un nombre con comillas no rompe nada.
document.addEventListener("submit", (evento) => {
  const mensaje = evento.target.dataset.confirmacion;
  if (mensaje && !window.confirm(mensaje)) {
    evento.preventDefault();
  }
});
