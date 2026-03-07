let allProducts = [];
let currentCategory = '전체';

function renderProducts(category) {
  const grid = document.getElementById('productGrid');
  const title = document.getElementById('categoryTitle');
  const count = document.getElementById('productCount');

  const filtered = category === '전체'
    ? allProducts
    : allProducts.filter(p => p.category === category);

  title.textContent = category === '전체' ? '전체 제품' : category;
  count.textContent = `총 ${filtered.length}개`;

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-state"><p>해당 카테고리에 제품이 없습니다.</p></div>';
    return;
  }

  const priceHTML = (p) => {
    if (p.monthly_price) {
      return `
        <p class="product-price-label">월 렌탈료</p>
        <p class="product-price">
          ${p.monthly_price.toLocaleString()}
          <span class="product-price-unit">원/월</span>
        </p>`;
    }
    return `
      <p class="product-price-label">렌탈료</p>
      <p class="product-price inquiry-price">${p.monthly_price_note || '문의'}</p>`;
  };

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
        ${p.model ? `<p class="product-desc">${p.model}</p>` : ''}
        <div class="product-price-wrap">
          ${priceHTML(p)}
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

function initCategories(categories) {
  const list = document.getElementById('categoryList');

  // 동적으로 카테고리 목록 생성
  list.innerHTML = `<li class="category-item active" data-category="전체">전체</li>` +
    categories.map(c => `<li class="category-item" data-category="${c.name}">${c.name}</li>`).join('');

  list.querySelectorAll('.category-item').forEach(item => {
    item.addEventListener('click', () => {
      list.querySelectorAll('.category-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      currentCategory = item.dataset.category;
      renderProducts(currentCategory);
      if (window.innerWidth <= 900) {
        document.querySelector('.main-content').scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}

async function init() {
  try {
    const res = await fetch('data/products.json');
    const data = await res.json();

    // 카테고리별 products를 flat array로 변환
    allProducts = data.categories.flatMap(cat =>
      cat.products.map(p => ({ ...p, category: cat.name }))
    );

    initCategories(data.categories);
    renderProducts('전체');
  } catch (e) {
    document.getElementById('productGrid').innerHTML =
      '<div class="empty-state"><p>상품 데이터를 불러오는 중 오류가 발생했습니다.</p></div>';
  }
}

document.addEventListener('DOMContentLoaded', init);
