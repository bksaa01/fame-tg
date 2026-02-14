// Глобальные переменные
let cardsData = [];
let currentCategory = 'medijki';
let currentUser = null;

// Загрузка данных при запуске
document.addEventListener('DOMContentLoaded', function() {
    loadCards();
    loadUserData();
    initTabs();
    initSearch();
    initTheme();
});

// Загрузка анкет с сервера
async function loadCards() {
    try {
        // В демо-режиме используем локальные данные
        // В реальном проекте здесь будет fetch('/api/cards')
        cardsData = getDemoCards();
        renderCards(currentCategory);
    } catch (error) {
        console.error('Ошибка загрузки анкет:', error);
    }
}

// Загрузка данных пользователя
function loadUserData() {
    // Проверяем, есть ли сохранённый пользователь
    const savedUser = localStorage.getItem('tgUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateUserInterface();
    }
}

// Обновление интерфейса под пользователя
function updateUserInterface() {
    // Здесь будет отображение аватара, имени и т.д.
    console.log('Пользователь загружен:', currentUser);
}

// Инициализация вкладок
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                tabBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentCategory = this.dataset.category;
                renderCards(currentCategory);
            });
        });
    }
}

// Инициализация поиска
function initSearch() {
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            const query = e.target.value.toLowerCase();
            searchCards(query);
        }, 300));
    }

    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterCards(this.textContent.toLowerCase());
        });
    });
}

// Поиск по карточкам
function searchCards(query) {
    if (!query) {
        renderCards(currentCategory);
        return;
    }

    const filtered = cardsData.filter(card => 
        card.name.toLowerCase().includes(query) ||
        card.description.toLowerCase().includes(query) ||
        card.username.toLowerCase().includes(query)
    );

    renderFilteredCards(filtered);
}

// Фильтрация по типу (канал/форум)
function filterCards(type) {
    // В реальном проекте здесь будет фильтрация
    console.log('Фильтр по типу:', type);
}

// Отрисовка карточек
function renderCards(category) {
    const grid = document.getElementById('cardsGrid');
    if (!grid) return;

    const filteredCards = cardsData.filter(card => card.category === category);
    renderFilteredCards(filteredCards);
}

// Отрисовка отфильтрованных карточек
function renderFilteredCards(cards) {
    const grid = document.getElementById('cardsGrid');
    if (!grid) return;

    if (cards.length === 0) {
        grid.innerHTML = '<div class="no-cards">В этой категории пока нет анкет</div>';
        return;
    }

    // Сортируем: закреплённые в начале
    cards.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));

    grid.innerHTML = cards.map(card => `
        <div class="card" data-id="${card.id}">
            <div class="card-header">
                <div class="card-avatar">
                    <img src="${card.avatar}" alt="${card.name}">
                </div>
                <div class="card-badges">
                    ${renderBadges(card.badges)}
                </div>
            </div>
            <div class="card-body">
                <div class="card-title">${card.name}</div>
                <div class="card-username">@${card.username}</div>
                <div class="card-category">${card.categoryName}</div>
                <div class="card-description">${truncateText(card.description, 100)}</div>
            </div>
            <div class="card-footer">
                <div class="card-rating">
                    <div class="rating-item like" onclick="handleLike(${card.id})">
                        <i class="fas fa-thumbs-up"></i>
                        <span class="rating-count">${card.rating.likes}</span>
                    </div>
                    <div class="rating-item dislike" onclick="handleDislike(${card.id})">
                        <i class="fas fa-thumbs-down"></i>
                        <span class="rating-count">${card.rating.dislikes}</span>
                    </div>
                </div>
                <div class="card-links">
                    ${renderLinks(card.links)}
                </div>
            </div>
        </div>
    `).join('');
}

// Отрисовка бейджей
function renderBadges(badges) {
    if (!badges || badges.length === 0) return '';

    return badges.map(badge => {
        const badgeConfig = {
            verified: { class: 'verified', text: 'Verified' },
            scam: { class: 'scam', text: 'SCAM' },
            pinned: { class: 'pinned', text: 'Закреплён' },
            scamdb: { class: 'scam-db', text: 'В скам базе' }
        };
        const config = badgeConfig[badge];
        return config ? `<span class="badge ${config.class}">${config.text}</span>` : '';
    }).join('');
}

// Отрисовка ссылок
function renderLinks(links) {
    if (!links || links.length === 0) return '';

    return links.map(link => {
        if (link.includes('t.me')) {
            return `<a href="${link}" target="_blank"><i class="fab fa-telegram"></i></a>`;
        }
        return `<a href="${link}" target="_blank"><i class="fas fa-link"></i></a>`;
    }).join('');
}

// Обрезание текста
function truncateText(text, length) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

// Обработка лайка
async function handleLike(cardId) {
    const card = cardsData.find(c => c.id === cardId);
    if (card) {
        // В реальном проекте здесь будет fetch POST
        card.rating.likes++;
        renderCards(currentCategory);
    }
}

// Обработка дизлайка
async function handleDislike(cardId) {
    const card = cardsData.find(c => c.id === cardId);
    if (card) {
        card.rating.dislikes++;
        renderCards(currentCategory);
    }
}

// Дебаунс для поиска
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Инициализация темы
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.className = savedTheme;

    const savedSnow = localStorage.getItem('snow') === 'true';
    if (savedSnow) {
        document.body.classList.add('snow');
    }

    const savedBg = localStorage.getItem('bgImage');
    if (savedBg) {
        document.body.style.backgroundImage = `url(${savedBg})`;
    }
}

// Демо-данные (для разработки)
function getDemoCards() {
    return [
        {
            id: 1,
            name: 'Semerk!n',
            username: 'semerkin',
            category: 'medijki',
            categoryName: 'Медийка',
            description: 'Также известен как "Семеркин". Появился в комьюнити в 2020 году, создал несколько успешных проектов.',
            avatar: 'https://via.placeholder.com/150',
            rating: { likes: 30, dislikes: 16 },
            badges: ['verified'],
            links: ['https://t.me/semerkin'],
            pinned: false
        },
        {
            id: 2,
            name: 'Lemon',
            username: 'lemon',
            category: 'medijki',
            categoryName: 'Медийка',
            description: 'Владелец сайта, по вопросам писать мне и тд хз сайт говно',
            avatar: 'https://via.placeholder.com/150',
            rating: { likes: 24, dislikes: 13 },
            badges: [],
            links: ['https://t.me/lemon'],
            pinned: false
        }
    ];
}

// Получение текста подкатегорий
function getSubCategoryText(category) {
    const texts = {
        'medijki': 'Кодеры, Товары, Дизайнеры, Эдиторы',
        'fame': '',
        'middle': '',
        'small': '',
        'coders': '',
        'goods': '',
        'channels': '',
        'scam': '',
        'designers': '',
        'editors': ''
    };
    return texts[category] || '';
                                 }
