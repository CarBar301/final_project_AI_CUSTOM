const askForm = document.querySelector("#ask-form");
const answerOutput = document.querySelector("#answer-output");
const contextOutput = document.querySelector("#context-output");
const userIdInput = document.querySelector("#user-id");
const clearContextBtn = document.querySelector("#clear-context-btn");

const API_BASE_URL = "http://127.0.0.1:8000";

// Cargar contexto inicial al arrancar
if (userIdInput && userIdInput.value) {
  loadContext(userIdInput.value);
}

// Cargar contexto cuando cambie el ID de usuario
if (userIdInput) {
  userIdInput.addEventListener("input", () => {
    loadContext(userIdInput.value);
  });
}

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(askForm);
  const payload = {
    user_id: formData.get("user_id"),
    question: formData.get("question"),
  };

  answerOutput.textContent = "Consultando...";

  try {
    const response = await fetch(`${API_BASE_URL}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    answerOutput.textContent = JSON.stringify(result, null, 2);
    await loadContext(payload.user_id);
  } catch (error) {
    answerOutput.textContent = `No se pudo conectar con el backend: ${error.message}`;
  }
});

// Botón para limpiar contexto
clearContextBtn.addEventListener("click", async () => {
  const userId = userIdInput.value;
  if (!userId) return;

  contextOutput.textContent = "Limpiando...";

  try {
    const response = await fetch(`${API_BASE_URL}/context/${encodeURIComponent(userId)}`, {
      method: "DELETE"
    });
    const result = await response.json();
    contextOutput.textContent = JSON.stringify(result, null, 2);
    // Recargar para mostrar que quedó vacío
    setTimeout(() => loadContext(userId), 800);
  } catch (error) {
    contextOutput.textContent = `Error al limpiar contexto: ${error.message}`;
  }
});

async function loadContext(userId) {
  if (!userId) {
    contextOutput.textContent = "Ingrese un ID de usuario.";
    return;
  }
  try {
    const response = await fetch(`${API_BASE_URL}/context/${encodeURIComponent(userId)}`);
    const result = await response.json();
    contextOutput.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    contextOutput.textContent = "El módulo CAG no respondió correctamente.";
  }
}
