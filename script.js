let cardsData = [
    {
        id: 1,
        name: "Semerkin",
        username: "semerkin",
        category: "medijki",
        categoryName: "Медийка",
        description: "Также известен как 'Семеркин'. Появился в комьюнити в 2020 году, создал несколько успешных проектов. Активно участвует в жизни сообщества.",
        avatar: "https://via.placeholder.com/150",
        rating: { likes: 30, dislikes: 16 },
        badges: ["verified"],
        links: ["https://t.me/semerkin"],
        pinned: false
    },
    {
        id: 2,
        name: "Lemon",
        username: "lemon",
        category: "medijki",
        categoryName: "Медийка",
        description: "Владелец сайта, по вопросам писать мне и тд хз сайт говно",
        avatar: "https://via.placeholder.com/150",
        rating: { likes: 24, dislikes: 13 },
        badges: [],
        links: ["https://t.me/lemon"],
        pinned: false
    }
];

let currentCategory = 'medijki';

function renderCards(category) {
    const grid = document.getElementById('cardsGrid');
    if (!grid) return;

    const filteredCards = cardsData.filter(card => card.category === category);
    
    if (filteredCards.length === 0) {
        grid.innerHTML = '<div class="no-cards">В этой категории пока нет анкет</div>';
        return;
    }

    grid.innerHTML = filteredCards.map(card => `
        <div class="card" data-id="${card.id}">
            <div class="card-header">
                <div class="card-avatar">
                    <img src="${card.avatar}" alt="${card.name}">
                </div>
                <div class="card-badges">
                    ${card.badges.map(badge => {
                        let badgeClass = '';
                        let badgeText = '';
                        switch(badge) {
                            case 'verified':
                                badgeClass = 'verified';
                                badgeText = 'Verified';
                                break;
                            case 'scam':
                                badgeClass = 'scam';
                                badgeText = 'SCAM';
                                break;
                            case 'pinned':
                                badgeClass = 'pinned';
                                badgeText = 'Закреплён';
                                break;
                            case 'scamdb':
                                badgeClass = 'scam-db';
                                badgeText = 'В скам базе';
                                break;
                        }
                        return `<span class="badge ${badgeClass}">${badgeText}</span>`;
                    }).join('')}
                </div>
            </div>
            <div class="card-body">
                <div class="card-title">${card.name}</div>
                <div class="card-username">@${card.username}</div>
                <div class="card-category">${card.categoryName}</div>
                <div class="card-description">${card.description.substring(0, 100)}${card.description.length > 100 ? '...' : ''}</div>
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
                    ${card.links.map(link => `<a href="${link}" target="_blank"><i class="fab fa-telegram"></i></a>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

function handleLike(cardId) {
    const card = cardsData.find(c => c.id === cardId);
    if (card) {
        card.rating.likes++;
        renderCards(currentCategory);
    }
}

function handleDislike(cardId) {
    const card = cardsData.find(c => c.id === cardId);
    if (card) {
        card.rating.dislikes++;
        renderCards(currentCategory);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                tabBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentCategory = this.dataset.category;
                renderCards(currentCategory);
                
                const subCategory = document.getElementById('category-sub');
                if (subCategory) {
                    subCategory.textContent = getSubCategoryText(currentCategory);
                }
            });
        });
        
        renderCards(currentCategory);
    }
    
    const uploadArea = document.getElementById('uploadArea');
    const photoInput = document.getElementById('photoInput');
    const photoPreview = document.getElementById('photoPreview');
    const previewImg = document.getElementById('previewImg');
    const removePhoto = document.getElementById('removePhoto');
    
    if (uploadArea && photoInput) {
        uploadArea.addEventListener('click', () => {
            photoInput.click();
        });
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#667eea';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#ddd';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#ddd';
            const file = e.dataTransfer.files[0];
            if (file) {
                handleFileUpload(file);
            }
        });
        
        photoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                handleFileUpload(file);
            }
        });
        
        function handleFileUpload(file) {
            if (file.size > 6 * 1024 * 1024) {
                alert('Файл слишком большой. Максимальный размер 6 МБ');
                return;
            }
            
            if (!file.type.startsWith('image/')) {
                alert('Пожалуйста, выберите изображение');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                uploadArea.style.display = 'none';
                photoPreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }
    
    if (removePhoto) {
        removePhoto.addEventListener('click', () => {
            uploadArea.style.display = 'block';
            photoPreview.style.display = 'none';
            photoInput.value = '';
        });
    }
    
    const categorySelect = document.getElementById('category');
    const subscribersGroup = document.getElementById('subscribersGroup');
    
    if (categorySelect && subscribersGroup) {
        categorySelect.addEventListener('change', function() {
            if (this.value === 'channels' || this.value === 'goods') {
                subscribersGroup.style.display = 'block';
            } else {
                subscribersGroup.style.display = 'none';
            }
        });
    }
    
    const applyForm = document.getElementById('applyForm');
    const applySuccess = document.getElementById('applySuccess');
    
    if (applyForm) {
        applyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            applyForm.style.display = 'none';
            applySuccess.style.display = 'block';
            
            console.log('Форма отправлена');
        });
    }
});

function getSubCategoryText(category) {
    const texts = {
        'medijki': 'Кодеры, Товары, Дизайнеры',
        'fame': '',
        'middle': '',
        'small': '',
        'channels': '',
        'scam': '',
        'goods': '',
        'coders': ''
    };
    return texts[category] || '';
}

const modal = document.getElementById('profileModal');
const closeBtn = document.querySelector('.close');

if (closeBtn) {
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});
