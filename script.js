// ============================================================
// 配置
// ============================================================
const API_BASE = 'https://gvzbz.fun/api';

// 存储 token
let authToken = localStorage.getItem('token');

// ============================================================
// 工具函数
// ============================================================
function showMessage(msg, isError = false) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    toast.style.background = isError ? '#f44336' : '#4caf50';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}

function getHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    return headers;
}

// ============================================================
// API 调用函数
// ============================================================

// 用户注册
async function register(username, password, email) {
    const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, email })
    });
    return response.json();
}

// 用户登录
async function login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const result = await response.json();
    if (result.code === 200 && result.data.token) {
        authToken = result.data.token;
        localStorage.setItem('token', authToken);
        localStorage.setItem('user', JSON.stringify(result.data.user));
    }
    return result;
}

// 获取当前用户
async function getCurrentUser() {
    const response = await fetch(`${API_BASE}/auth/me`, {
        headers: getHeaders()
    });
    return response.json();
}

// 获取分类列表
async function getCategories() {
    const response = await fetch(`${API_BASE}/categories`, {
        headers: getHeaders()
    });
    return response.json();
}

// 创建分类
async function createCategory(name, type, icon = '📌') {
    const response = await fetch(`${API_BASE}/category`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ name, type, icon })
    });
    return response.json();
}

// 获取账单列表
async function getBills(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const url = `${API_BASE}/bills${queryParams ? '?' + queryParams : ''}`;
    const response = await fetch(url, {
        headers: getHeaders()
    });
    return response.json();
}

// 创建账单
async function createBill(categoryId, amount, type, date, note = '', account = '') {
    const response = await fetch(`${API_BASE}/bill`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            category_id: categoryId,
            amount: amount,
            type: type,
            date: date,
            note: note,
            account: account
        })
    });
    return response.json();
}

// 删除账单
async function deleteBill(billId) {
    const response = await fetch(`${API_BASE}/bill/${billId}`, {
        method: 'DELETE',
        headers: getHeaders()
    });
    return response.json();
}

// 获取统计数据概览
async function getOverview(startDate, endDate) {
    let url = `${API_BASE}/statistics/overview`;
    if (startDate && endDate) {
        url += `?start_date=${startDate}&end_date=${endDate}`;
    }
    const response = await fetch(url, {
        headers: getHeaders()
    });
    return response.json();
}

// 获取分类统计（环形图）
async function getCategoryStats(startDate, endDate, type = 'expense') {
    const url = `${API_BASE}/statistics/category?start_date=${startDate}&end_date=${endDate}&type=${type}`;
    const response = await fetch(url, {
        headers: getHeaders()
    });
    return response.json();
}

// 获取趋势数据
async function getTrend(startDate, endDate, interval = 'day', type = 'expense') {
    const url = `${API_BASE}/statistics/trend?start_date=${startDate}&end_date=${endDate}&interval=${interval}&type=${type}`;
    const response = await fetch(url, {
        headers: getHeaders()
    });
    return response.json();
}

// 获取月份对比
async function getCompare(month) {
    const url = `${API_BASE}/statistics/compare?month=${month}`;
    const response = await fetch(url, {
        headers: getHeaders()
    });
    return response.json();
}

// 检查登录状态
function isLoggedIn() {
    return !!authToken;
}

// 退出登录
function logout() {
    authToken = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}
// 获取单条账单详情
async function getBillDetail(billId) {
    const response = await fetch(`${API_BASE}/bill/${billId}`, {
        headers: getHeaders()
    });
    return response.json();
}

// 更新账单
async function updateBill(billId, data) {
    const response = await fetch(`${API_BASE}/bill/${billId}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(data)
    });
    return response.json();
}
