const messageBox = document.getElementById('message');
const loginSection = document.getElementById('login-section');
const registerSection = document.getElementById('register-section');
const productsSection = document.getElementById('products-section');
const cartSection = document.getElementById('cart-section');

const tokenKey = 'fastapi_ecomm_token';
const refreshKey = 'fastapi_ecomm_refresh';

const showMessage = (text, type = 'success') => {
  messageBox.textContent = text;
  messageBox.className = `message ${type}`;
  messageBox.style.display = 'block';
  setTimeout(() => messageBox.style.display = 'none', 5000);
};

const setToken = (token, refresh) => {
  localStorage.setItem(tokenKey, token);
  localStorage.setItem(refreshKey, refresh);
};

const getToken = () => localStorage.getItem(tokenKey);
const getRefresh = () => localStorage.getItem(refreshKey);

const apiFetch = async (path, options = {}) => {
  const token = getToken();
  options.headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || body.message || response.statusText);
  }
  return response.json();
};

const hideAllSections = () => {
  [loginSection, registerSection, productsSection, cartSection].forEach(s => s.classList.add('hidden'));
};

const showSection = (section) => {
  hideAllSections();
  section.classList.remove('hidden');
};

const refreshProducts = async (query = '') => {
  try {
    const url = query ? `/products/search/?query=${encodeURIComponent(query)}` : '/products/';
    const products = await apiFetch(url);
    const list = document.getElementById('products-list');
    list.innerHTML = '';
    if (!products.length) {
      list.innerHTML = '<div class="item-card">No products found.</div>';
      return;
    }
    products.forEach(product => {
      const card = document.createElement('div');
      card.className = 'item-card';
      card.innerHTML = `
        <strong>${product.product_name}</strong>
        <p>${product.product_description}</p>
        <p>Price: $${product.product_price.toFixed(2)}</p>
        <p>Stock: ${product.product_stoke}</p>
        <p>Category: ${product.category || 'N/A'}</p>
      `;
      list.appendChild(card);
    });
  } catch (error) {
    showMessage(error.message, 'error');
  }
};

const refreshCart = async () => {
  try {
    const cart = await apiFetch('/cart/');
    const list = document.getElementById('cart-list');
    list.innerHTML = '';
    if (!cart.items.length) {
      list.innerHTML = '<div class="item-card">Your cart is empty.</div>';
      return;
    }
    cart.items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'item-card';
      card.innerHTML = `
        <strong>Product ID: ${item.product_id}</strong>
        <p>Quantity: ${item.quantity}</p>
        <p>Total: $${item.total_price.toFixed(2)}</p>
      `;
      list.appendChild(card);
    });
  } catch (error) {
    showMessage(error.message, 'error');
  }
};

const loginUser = async () => {
  try {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const result = await apiFetch('/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(result.access_token, result.refresh_token);
    showMessage('Login successful.');
    showSection(productsSection);
    refreshProducts();
  } catch (error) {
    showMessage(error.message, 'error');
  }
};

const registerUser = async () => {
  try {
    const first_name = document.getElementById('register-firstname').value;
    const last_name = document.getElementById('register-lastname').value;
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const result = await apiFetch('/register/', {
      method: 'POST',
      body: JSON.stringify({ first_name, last_name, username, email, password }),
    });
    setToken(result.access_token, result.refresh_token);
    showMessage('Registration successful.');
    showSection(productsSection);
    refreshProducts();
  } catch (error) {
    showMessage(error.message, 'error');
  }
};

const addToCart = async () => {
  try {
    const product_id = Number(document.getElementById('product-add-id').value);
    const quantity = Number(document.getElementById('product-add-qty').value);
    if (!product_id || quantity < 1) {
      showMessage('Enter valid product ID and quantity.', 'error');
      return;
    }
    await apiFetch('/cart/items/', {
      method: 'POST',
      body: JSON.stringify({ product_id, quantity }),
    });
    showMessage('Added to cart.');
    refreshCart();
  } catch (error) {
    showMessage(error.message, 'error');
  }
};

const clearCart = async () => {
  try {
    await apiFetch('/cart/clear/', { method: 'DELETE' });
    showMessage('Cart cleared.');
    refreshCart();
  } catch (error) {
    showMessage(error.message, 'error');
  }
};

const placeOrder = async () => {
  try {
    const address = prompt('Enter delivery address:', '123 Main St');
    if (!address) return;
    await apiFetch('/orders/', {
      method: 'POST',
      body: JSON.stringify({ delivery_address: address }),
    });
    showMessage('Order placed successfully.');
    refreshCart();
  } catch (error) {
    showMessage(error.message, 'error');
  }
};

const setupListeners = () => {
  document.getElementById('btn-show-login').onclick = () => showSection(loginSection);
  document.getElementById('btn-show-register').onclick = () => showSection(registerSection);
  document.getElementById('btn-show-products').onclick = () => { showSection(productsSection); refreshProducts(); };
  document.getElementById('btn-show-cart').onclick = () => { showSection(cartSection); refreshCart(); };
  document.getElementById('btn-login').onclick = loginUser;
  document.getElementById('btn-register').onclick = registerUser;
  document.getElementById('btn-search').onclick = () => refreshProducts(document.getElementById('search-query').value);
  document.getElementById('btn-refresh-products').onclick = () => refreshProducts();
  document.getElementById('btn-add-to-cart').onclick = addToCart;
  document.getElementById('btn-refresh-cart').onclick = refreshCart;
  document.getElementById('btn-clear-cart').onclick = clearCart;
  document.getElementById('btn-place-order').onclick = placeOrder;
};

window.addEventListener('load', () => {
  setupListeners();
  showSection(loginSection);
});
