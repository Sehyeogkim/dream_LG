let currentCategory = '전체';

function renderProducts(category) {
  const grid = document.getElementById('productGrid');
  const title = document.getElementById('categoryTitle');
  const count = document.getElementById('productCount');

  const filtered = category === '전체'
    ? products
    : products.filter(p => p.category === category);

  title.textContent = category === '전체' ? '전체 제품' : category;
  count.textContent = `총 ${filtered.length}개`;

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-state"><p>해당 카테고리에 제품이 없습니다.</p></div>';
    return;
  }

  grid.innerHTML = filtered.map(p => `
    <div class="product-card">
      <img
        class="product-image"
        src="${p.image}"
        alt="${p.name}"
        loading="lazy"
        onerror="this.src='https://placehold.co/300x220/f0f0f0/bbb?text=이미지+준비중'"
      />
      <div class="product-info">
        <span class="product-category-tag">${p.category}</span>
        <p class="product-name">${p.name}</p>
        <p class="product-desc">${p.desc}</p>
        <div class="product-price-wrap">
          <p class="product-price-label">월 렌탈료</p>
          <p class="product-price">
            ${p.price.toLocaleString()}
            <span class="product-price-unit">원/월</span>
          </p>
        </div>
        <button class="product-inquiry" onclick="handleInquiry('${p.name.replace(/'/g, "\\'")}')">
          렌탈 문의하기
        </button>
      </div>
    </div>
  `).join('');
}

function handleInquiry(productName) {
  alert(`[${productName}] 렌탈 문의\n\n전화: 010-0000-0000\n\n담당자가 친절히 안내해 드립니다.`);
}

function initCategories() {
  const items = document.querySelectorAll('.category-item');
  items.forEach(item => {
    item.addEventListener('click', () => {
      items.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      currentCategory = item.dataset.category;
      renderProducts(currentCategory);
      // 모바일에서 카테고리 선택 후 상품 영역으로 스크롤
      if (window.innerWidth <= 900) {
        document.querySelector('.main-content').scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initCategories();
  renderProducts('전체');
});
