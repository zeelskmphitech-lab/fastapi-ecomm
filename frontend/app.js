const API_BASE = (() => {
  const host = window.location.hostname;
  if (host === '127.0.0.1' || host === 'localhost') {
    return `${window.location.protocol}//${host}:8000`;
  }
  return `${window.location.protocol}//${host}`;
})();

const messageBox = document.getElementById('message');
const loginSection = document.getElementById('login-section');
const registerSection = document.getElementById('register-section');
const productsSection = document.getElementById('products-section');
const cartSection = document.getElementById('cart-section');
const ordersSection = document.getElementById('orders-section');
const sellerSection = document.getElementById('seller-section');
const authSection = document.getElementById('auth-section');
const heroPanel = document.getElementById('hero-panel');

const tokenKey = 'fastapi_ecomm_token';
let currentUser = null;

const showMessage = (text, type = 'success') => {
  messageBox.textContent = text;
  messageBox.className = `message ${type}`;
  messageBox.style.display = 'block';
  setTimeout(() => messageBox.style.display = 'none', 5000);
};

const setToken = (token) => {
  localStorage.setItem(tokenKey, token);
};

const getToken = () => localStorage.getItem(tokenKey);

const clearAuth = () => {
  localStorage.removeItem(tokenKey);
  currentUser = null;
  const tagline = document.querySelector('.tagline');
  if (tagline) tagline.textContent = 'FastAPI powered storefront';
};

const apiFetch = async (path, options = {}) => {
  const token = getToken();
  options.headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || body.message || response.statusText);
  }
  return response.json();
};

const handleFetchError = (error) => {
  if (error.message.includes('Method Not Allowed')) {
    showMessage('The request is being sent to the wrong server or wrong method. Make sure the API is running on http://127.0.0.1:8000', 'error');
  } else {
    showMessage(error.message, 'error');
  }
};

const hideAllSections = () => {
  [authSection, productsSection, cartSection, ordersSection, sellerSection, heroPanel].forEach(s => s.classList.add('hidden'));
};

const showSection = (section) => {
  hideAllSections();
  section.classList.remove('hidden');
};

const renderUserInfo = () => {
  if (!currentUser) return;
  const tagline = document.querySelector('.tagline');
  if (tagline) tagline.textContent = `${currentUser.first_name} ${currentUser.last_name} — ${currentUser.is_seller ? 'Seller' : 'Buyer'}`;
};

const setCurrentUser = (user) => {
  currentUser = user;
  renderUserInfo();
};

const loadProfile = async () => {
  const token = getToken();
  if (!token) return;
  try {
    const profile = await apiFetch('/me/');
    setCurrentUser(profile);
  } catch (error) {
    clearAuth();
  }
};

const refreshProducts = async (query = '') => {
  try {
    const url = query ? `/products/search/?query=${encodeURIComponent(query)}` : '/products/';
    const products = await apiFetch(url);
    const list = document.getElementById('products-list');
    list.innerHTML = '';
    if (!products.length) {
      list.innerHTML = '<div class="item-card"><h3>No products found.</h3></div>';
      return;
    }
    products.forEach(product => {
      const card = document.createElement('div');
      card.className = 'item-card';
      card.innerHTML = `
        <div>
          <h3>${product.product_name}</h3>
          <p>${product.product_description}</p>
        </div>
        <div class="item-meta">
          <span class="price">$${product.product_price.toFixed(2)}</span>
          <span>Stock: ${product.product_stoke}</span>
        </div>
        <div class="item-meta">
          <span>Category: ${product.category || 'General'}</span>
          <span>ID: ${product.product_id}</span>
        </div>
        <div class="item-actions">
          <button class="secondary" onclick="addToCart(${product.product_id}, 1)">Add to Cart</button>
        </div>
      `;
      list.appendChild(card);
    });
  } catch (error) {
    handleFetchError(error);
  }
};

const refreshCart = async () => {
  try {
    const cart = await apiFetch('/cart/');
    const list = document.getElementById('cart-list');
    list.innerHTML = '';
    if (!cart.items.length) {
      list.innerHTML = '<div class="item-card"><h3>Your cart is empty.</h3></div>';
      return;
    }
    cart.items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'item-card';
      card.innerHTML = `
        <div>
          <h3>Product ID ${item.product_id}</h3>
          <p>Quantity: ${item.quantity}</p>
          <p>Total: $${item.total_price.toFixed(2)}</p>
        </div>
        <div class="item-actions">
          <button class="secondary" onclick="removeCartItem(${item.cartitem_id})">Remove</button>
        </div>
      `;
      list.appendChild(card);
    });
  } catch (error) {
    handleFetchError(error);
  }
};

const refreshOrders = async () => {
  try {
    const orders = await apiFetch('/orders/');
    const list = document.getElementById('orders-list');
    list.innerHTML = '';
    if (!orders.length) {
      list.innerHTML = '<div class="item-card"><h3>No orders yet.</h3></div>';
      return;
    }
    orders.forEach(order => {
      const card = document.createElement('div');
      card.className = 'item-card';
      const itemsHtml = order.items.map(item => `<li>Product ${item.product_id} × ${item.quantity} — $${item.total_price.toFixed(2)}</li>`).join('');
      card.innerHTML = `
        <div>
          <h3>Order #${order.order_id}</h3>
          <div class="item-meta"><span>Status: ${order.order_status}</span><span>Payment: ${order.payment_status}</span></div>
          <p>Delivery address: ${order.delivery_address}</p>
          <p>Total: $${order.total_amount.toFixed(2)}</p>
          <ul>${itemsHtml}</ul>
        </div>
      `;
      list.appendChild(card);
    });
  } catch (error) {
    handleFetchError(error);
  }
};

const refreshSellerProducts = async () => {
  try {
    const products = await apiFetch('/seller/products/');
    const list = document.getElementById('seller-products-list');
    list.innerHTML = '';
    if (!products.length) {
      list.innerHTML = '<div class="item-card"><h3>No seller products found.</h3></div>';
      return;
    }
    products.forEach(product => {
      const card = document.createElement('div');
      card.className = 'item-card';
      card.innerHTML = `
        <div>
          <h3>${product.product_name}</h3>
          <p>${product.product_description}</p>
        </div>
        <div class="item-meta">
          <span>$${product.product_price.toFixed(2)}</span>
          <span>Stock: ${product.product_stoke}</span>
        </div>
        <div class="item-meta">
          <span>Category: ${product.category || 'General'}</span>
          <span>ID: ${product.product_id}</span>
        </div>
      `;
      list.appendChild(card);
    });
  } catch (error) {
    handleFetchError(error);
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
    setToken(result.access_token);
    setCurrentUser(result.user);
    showMessage('Login successful.', 'success');
    showSection(productsSection);
    refreshProducts();
  } catch (error) {
    handleFetchError(error);
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
    setToken(result.access_token);
    setCurrentUser(result.user);
    showMessage('Registration successful.', 'success');
    showSection(productsSection);
    refreshProducts();
  } catch (error) {
    handleFetchError(error);
  }
};

const addToCart = async (product_id, quantity = 1) => {
  try {
    await apiFetch('/cart/items/', {
      method: 'POST',
      body: JSON.stringify({ product_id, quantity }),
    });
    showMessage('Added to cart.', 'success');
    refreshCart();
  } catch (error) {
    handleFetchError(error);
  }
};

const removeCartItem = async (item_id) => {
  try {
    await apiFetch(`/cart/items/${item_id}`, { method: 'DELETE' });
    showMessage('Cart item removed.', 'success');
    refreshCart();
  } catch (error) {
    handleFetchError(error);
  }
};

const clearCart = async () => {
  try {
    await apiFetch('/cart/clear/', { method: 'DELETE' });
    showMessage('Cart cleared.', 'success');
    refreshCart();
  } catch (error) {
    handleFetchError(error);
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
    showMessage('Order placed successfully.', 'success');
    refreshCart();
  } catch (error) {
    handleFetchError(error);
  }
};

const becomeSeller = async () => {
  try {
    const user = await apiFetch('/become-seller/', { method: 'POST' });
    setCurrentUser(user);
    showMessage('Now a seller!', 'success');
    refreshSellerProducts();
  } catch (error) {
    handleFetchError(error);
  }
};

const createProduct = async () => {
  try {
    const product_name = document.getElementById('product-name').value;
    const product_description = document.getElementById('product-description').value;
    const product_price = Number(document.getElementById('product-price').value);
    const product_stoke = Number(document.getElementById('product-stock').value);
    const category = document.getElementById('product-category').value;
    const product = { product_name, product_description, product_price, product_stoke, category };
    await apiFetch('/seller/products/', {
      method: 'POST',
      body: JSON.stringify(product),
    });
    showMessage('Product created successfully.', 'success');
    refreshSellerProducts();
    refreshProducts();
  } catch (error) {
    handleFetchError(error);
  }
};

const showHome = () => {
  hideAllSections();
  heroPanel.classList.remove('hidden');
};

const setupListeners = () => {
  document.getElementById('btn-show-home').onclick = showHome;
  document.getElementById('btn-show-products').onclick = () => { showSection(productsSection); refreshProducts(); };
  document.getElementById('btn-show-cart').onclick = () => { showSection(cartSection); refreshCart(); };
  document.getElementById('btn-show-orders').onclick = () => { showSection(ordersSection); refreshOrders(); };
  document.getElementById('btn-show-seller').onclick = () => { showSection(sellerSection); refreshSellerProducts(); };
  document.getElementById('btn-show-auth').onclick = () => { showSection(authSection); loginSection.classList.remove('hidden'); registerSection.classList.add('hidden'); };
  document.getElementById('hero-register').onclick = () => { showSection(authSection); registerSection.classList.remove('hidden'); loginSection.classList.add('hidden'); };
  document.getElementById('hero-login').onclick = () => { showSection(authSection); loginSection.classList.remove('hidden'); registerSection.classList.add('hidden'); };
  document.getElementById('btn-login').onclick = loginUser;
  document.getElementById('btn-register').onclick = registerUser;
  document.getElementById('btn-search').onclick = () => refreshProducts(document.getElementById('search-query').value);
  document.getElementById('btn-refresh-products').onclick = () => refreshProducts();
  document.getElementById('btn-refresh-cart').onclick = () => refreshCart();
  document.getElementById('btn-clear-cart').onclick = () => clearCart();
  document.getElementById('btn-place-order').onclick = () => placeOrder();
  document.getElementById('btn-refresh-orders').onclick = () => refreshOrders();
  document.getElementById('btn-become-seller').onclick = becomeSeller;
  document.getElementById('btn-create-product').onclick = createProduct;
};

window.addEventListener('load', async () => {
  setupListeners();
  await loadProfile();
  showHome();
});

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
    handleFetchError(error);
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
    handleFetchError(error);
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
    handleFetchError(error);
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
    handleFetchError(error);
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
    handleFetchError(error);
  }
};

const clearCart = async () => {
  try {
    await apiFetch('/cart/clear/', { method: 'DELETE' });
    showMessage('Cart cleared.');
    refreshCart();
  } catch (error) {
    handleFetchError(error);
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
    handleFetchError(error);
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
