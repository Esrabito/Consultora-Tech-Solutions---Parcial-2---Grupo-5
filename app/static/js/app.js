// Confirmación para acciones destructivas (eliminar servicios y planes).
document.addEventListener("submit", (evento) => {
  const mensaje = evento.target.dataset.confirmacion;
  if (mensaje && !window.confirm(mensaje)) {
    evento.preventDefault();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  // Cerrar avisos sin depender del componente alert de Bootstrap.
  document.querySelectorAll("[data-flash-close]").forEach((boton) => {
    boton.addEventListener("click", () => {
      const aviso = boton.closest(".flash");
      if (aviso) {
        aviso.remove();
      }
    });
  });

  // Actualizar el nombre accesible del botón del menú al abrirlo o cerrarlo.
  const menu = document.getElementById("menuPrincipal");
  const botonMenu = document.querySelector(".menu-toggle");
  if (menu && botonMenu) {
    menu.addEventListener("show.bs.collapse", () => {
      botonMenu.setAttribute("aria-label", "Cerrar menú");
    });
    menu.addEventListener("hide.bs.collapse", () => {
      botonMenu.setAttribute("aria-label", "Abrir menú");
    });
  }

  // Si el servidor devolvió errores, llevar el foco al primer campo inválido.
  const primerInvalido = document.querySelector(".is-invalid, [aria-invalid=\"true\"]");
  if (primerInvalido) {
    const campo = primerInvalido.matches("fieldset")
      ? primerInvalido.querySelector("input, select, textarea") || primerInvalido
      : primerInvalido;
    campo.focus({ preventScroll: false });
  }

  // Mostrar u ocultar la contraseña del panel.
  const alternarContrasena = document.querySelector("[data-password-toggle]");
  if (alternarContrasena) {
    const campo = document.getElementById(alternarContrasena.dataset.passwordToggle);
    const icono = alternarContrasena.querySelector("i");
    alternarContrasena.addEventListener("click", () => {
      if (!campo) {
        return;
      }
      const visible = campo.type === "text";
      campo.type = visible ? "password" : "text";
      alternarContrasena.setAttribute("aria-pressed", String(!visible));
      alternarContrasena.setAttribute(
        "aria-label",
        visible ? "Mostrar contraseña" : "Ocultar contraseña"
      );
      if (icono) {
        icono.classList.toggle("bi-eye", visible);
        icono.classList.toggle("bi-eye-slash", !visible);
      }
    });
  }

  // Contar los servicios elegidos al armar un plan.
  const casillas = document.querySelectorAll('input[name="servicios"]');
  const contador = document.querySelector("[data-services-count]");
  if (casillas.length && contador) {
    const actualizar = () => {
      const total = Array.from(casillas).filter((casilla) => casilla.checked).length;
      contador.textContent =
        total === 1 ? "1 servicio seleccionado" : `${total} servicios seleccionados`;
    };
    casillas.forEach((casilla) => casilla.addEventListener("change", actualizar));
    actualizar();
  }
});
