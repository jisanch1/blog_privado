// my_private_blog/blog/static/blog/js/main.js

const API_BASE_URL = 'http://127.0.0.1:8000/api/'; // URL base de tu API Django

// Elementos del DOM
const loginSection = document.getElementById('login-section');
const blogContentSection = document.getElementById('blog-content');
const loginForm = document.getElementById('login-form');
const errorMessage = document.getElementById('error-message');
const logoutButton = document.getElementById('logout-button');
const postsList = document.getElementById('posts-list');

let authToken = localStorage.getItem('authToken'); // Recupera el token si existe

// --- Funciones de Autenticación ---

async function login(username, password) {
    try {
        const response = await apiFetch(`${API_BASE_URL}token-auth/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.non_field_errors ? errorData.non_field_errors[0] : 'Error de inicio de sesión');
        }

        const data = await response.json();
        authToken = data.token;
        localStorage.setItem('authToken', authToken); // Guarda el token
        await displayBlogContent(); // Muestra el contenido del blog después del login
        hideErrorMessage();

    } catch (error) {
        showErrorMessage(error.message);
        console.error('Error durante el login:', error);
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken'); // Elimina el token
    loginSection.style.display = 'block';
    blogContentSection.style.display = 'none';
    postsList.innerHTML = '<p>Cargando posts...</p>'; // Limpia el contenido
    hideErrorMessage();
}

function isAuthenticated() {
    return authToken !== null;
}

// --- Funciones de Interfaz de Usuario ---

function showErrorMessage(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideErrorMessage() {
    errorMessage.textContent = '';
    errorMessage.style.display = 'none';
}

// Función para obtener el CSRF token de las cookies
function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Actualiza los conteos de likes/dislikes en la UI para un elemento específico.
 * @param {string} type - 'post' o 'comment'
 * @param {string} id - ID del post o comentario
 * @param {object} counts - Objeto con { likes_count, dislikes_count }
 */
function updateReactionCountsInUI(type, id, counts) {
    let container;
    if (type === 'post') {
        container = document.querySelector(`.post-item .like-button[data-id="${id}"]`).closest('.post-item');
    } else if (type === 'comment') {
        // Busca el comentario dentro de todos los comments-list para asegurar que sea el correcto
        container = document.querySelector(`.comment-item .like-button[data-id="${id}"]`).closest('.comment-item');
    }

    if (container) {
        container.querySelector('.like-count').textContent = counts.likes_count;
        container.querySelector('.dislike-count').textContent = counts.dislikes_count;
    }
}


// --- Funciones para interactuar con la API ---

async function apiFetch(url, options = {}) {
    // Helper para añadir el token de autenticación a todas las peticiones
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers // Mantén otros headers que se pasen
    };

    if (isAuthenticated()) {
        headers['Authorization'] = `Token ${authToken}`;
    }

    // Añadir el token CSRF para métodos que no son GET/HEAD/OPTIONS
    // El token CSRF se necesita para POST, PUT, PATCH, DELETE
    if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) {
        const csrfToken = getCsrfToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        } else {
            console.warn('CSRF token not found. This might lead to a 403 Forbidden error for mutating requests.');
        }
    }

    const response = await fetch(url, { ...options, headers });

    // Manejo global de token expirado/inválido
    if (response.status === 401) {
        logout();
        showErrorMessage('Sesión expirada o inválida. Por favor, inicia sesión de nuevo.');
        throw new Error('Unauthorized'); // Lanza error para detener la cadena de promesas
    }

    return response;
}


async function fetchPosts() {
    try {
        const response = await apiFetch(`${API_BASE_URL}posts/`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error al obtener posts:', error);
        if (error.message !== 'Unauthorized') { // No mostrar error si ya manejó el logout
            showErrorMessage('Error al cargar las publicaciones.');
        }
        return [];
    }
}

async function fetchComments(postId) {
    try {
        const response = await apiFetch(`${API_BASE_URL}comments/?post=${postId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error al obtener comentarios para post ${postId}:`, error);
        return [];
    }
}

async function postComment(postId, content) {
    try {
        const response = await apiFetch(`${API_BASE_URL}comments/`, {
            method: 'POST',
            body: JSON.stringify({ post: postId, content: content })
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error al enviar comentario:', error);
        if (error.message !== 'Unauthorized') {
            showErrorMessage('No se pudo enviar el comentario.');
        }
        return null;
    }
}

async function postReaction(contentType, objectId, isLike) {
    try {
        // --- ADVERTENCIA: IDs de ContentType ---
        // Estos IDs (10 y 11) son EJEMPLOS.
        // DEBES OBTENER LOS IDs REALES DE TU INSTANCIA DE DJANGO ADMIN
        // (Ve a /admin/ y en Content Types, busca 'blog | post' y 'blog | comment')
        // Si no son correctos, las reacciones no se guardarán.
        let typeId;
        if (contentType === 'post') {
            typeId = 10; // <<-- VERIFICAR ESTE ID
        } else if (contentType === 'comment') {
            typeId = 11; // <<-- VERIFICAR ESTE ID
        } else {
            throw new Error('Tipo de contenido no soportado para reacción.');
        }

        const response = await apiFetch(`${API_BASE_URL}reactions/`, {
            method: 'POST',
            body: JSON.stringify({
                content_type: typeId,
                object_id: objectId,
                is_like: isLike
            })
        });

        // La API de Django/DRF para ReactionViewSet manejará la lógica de toggle (crear/actualizar/eliminar)
        // La API devolverá 201 (Created), 200 (OK/Updated), o 204 (No Content/Deleted)
        if (response.status === 204) {
            return { action: 'deleted' };
        }
        if (!response.ok) {
            // Si la reacción ya existe y es del mismo tipo, la API la elimina y devuelve 204.
            // Si hay otro tipo de error, lo lanzamos.
            const errorData = await response.json();
            throw new Error(`HTTP error! status: ${response.status}. Details: ${JSON.stringify(errorData)}`);
        }
        return { action: 'created_or_updated', data: await response.json() };

    } catch (error) {
        console.error('Error al enviar reacción:', error);
        if (error.message !== 'Unauthorized') {
            showErrorMessage('No se pudo enviar la reacción.');
        }
        return null;
    }
}


// --- Renderizado del Contenido del Blog ---

async function displayBlogContent() {
    if (isAuthenticated()) {
        loginSection.style.display = 'none';
        blogContentSection.style.display = 'block';
        postsList.innerHTML = '<p>Cargando publicaciones...</p>'; // Mensaje de carga

        const posts = await fetchPosts();
        postsList.innerHTML = ''; // Limpiar mensaje de carga

        if (posts.length === 0) {
            postsList.innerHTML = '<p>No hay publicaciones disponibles.</p>';
            return;
        }

        for (const post of posts) {
            const postElement = document.createElement('div');
            postElement.className = 'post-item';
            postElement.innerHTML = `
                <h3>${post.title}</h3>
                <p>Autor: ${post.author ? post.author.username : 'Desconocido'}</p>
                <p>${post.content}</p>
                <p><small>Publicado: ${new Date(post.created_at).toLocaleDateString()}</small></p>
                <div class="reactions-container">
                    <button class="like-button" data-type="post" data-id="${post.id}" data-is-like="true">
                        👍 <span class="like-count">${post.likes_count}</span>
                    </button>
                    <button class="dislike-button" data-type="post" data-id="${post.id}" data-is-like="false">
                        👎 <span class="dislike-count">${post.dislikes_count}</span>
                    </button>
                </div>
                <div class="comments-section" data-post-id="${post.id}">
                    <h4>Comentarios:</h4>
                    <div class="comments-list"></div>
                    <form class="comment-form">
                        <textarea placeholder="Deja tu comentario..." required></textarea>
                        <button type="submit">Enviar Comentario</button>
                    </form>
                </div>
            `;
            postsList.appendChild(postElement);

            // Cargar comentarios para cada post
            const commentsListElement = postElement.querySelector('.comments-list');
            const comments = await fetchComments(post.id);
            if (comments.length > 0) {
                comments.forEach(comment => {
                    const commentElement = document.createElement('div');
                    commentElement.className = 'comment-item';
                    commentElement.innerHTML = `
                        <p><strong>${comment.author ? comment.author.username : 'Desconocido'}:</strong> ${comment.content}</p>
                        <div class="reactions-container">
                            <button class="like-button" data-type="comment" data-id="${comment.id}" data-is-like="true">
                                👍 <span class="like-count">${comment.likes_count}</span>
                            </button>
                            <button class="dislike-button" data-type="comment" data-id="${comment.id}" data-is-like="false">
                                👎 <span class="dislike-count">${comment.dislikes_count}</span>
                            </button>
                        </div>
                    `;
                    commentsListElement.appendChild(commentElement);
                });
            } else {
                commentsListElement.innerHTML = '<p>No hay comentarios.</p>';
            }
        }
        // Después de renderizar todos los posts, adjuntar event listeners para comentarios y reacciones
        attachEventListeners();

    } else {
        loginSection.style.display = 'block';
        blogContentSection.style.display = 'none';
    }
}

// --- Manejo de Eventos ---

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;
    await login(username, password);
});

logoutButton.addEventListener('click', () => {
    logout();
});

function attachEventListeners() {
    // Limpia listeners anteriores para evitar duplicados si displayBlogContent se llama varias veces
    document.querySelectorAll('.comment-form').forEach(form => {
        form.removeEventListener('submit', handleCommentSubmit);
        form.addEventListener('submit', handleCommentSubmit);
    });

    document.querySelectorAll('.like-button, .dislike-button').forEach(button => {
        button.removeEventListener('click', handleReactionClick);
        button.addEventListener('click', handleReactionClick);
    });
}

async function handleCommentSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const postId = form.closest('.comments-section').dataset.postId;
    const textarea = form.querySelector('textarea');
    const content = textarea.value;

    if (content.trim()) {
        const newComment = await postComment(postId, content);
        if (newComment) {
            textarea.value = ''; // Limpiar textarea
            // Opcional: Podríamos insertar el comentario directamente en el DOM
            // Para simplificar y asegurar consistencia, recargamos la sección de blog.
            await displayBlogContent();
        }
    }
}

async function handleReactionClick(e) {
    const button = e.currentTarget;
    const type = button.dataset.type; // 'post' o 'comment'
    const id = button.dataset.id;
    const isLike = button.dataset.isLike === 'true'; // Convertir string a booleano

    const result = await postReaction(type, id, isLike);
    if (result) {
        // Después de una reacción, en lugar de recargar TODO el blog,
        // podríamos buscar el post/comentario afectado y actualizar SOLO sus conteos.
        // Para esta versión, haremos una recarga más eficiente.

        // Refrescar solo los conteos del elemento afectado
        // Primero, obtener los datos actualizados de ese post/comment específico
        let updatedItem;
        if (type === 'post') {
            const response = await apiFetch(`${API_BASE_URL}posts/${id}/`);
            if (response.ok) {
                updatedItem = await response.json();
            }
        } else if (type === 'comment') {
            const response = await apiFetch(`${API_BASE_URL}comments/${id}/`);
            if (response.ok) {
                updatedItem = await response.json();
            }
        }

        if (updatedItem) {
            updateReactionCountsInUI(type, id, {
                likes_count: updatedItem.likes_count,
                dislikes_count: updatedItem.dislikes_count
            });
        }
    }
}

// --- Inicialización ---
// Verifica el token al cargar la página y muestra el contenido si ya está autenticado
document.addEventListener('DOMContentLoaded', displayBlogContent);
