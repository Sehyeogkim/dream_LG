// ─── 설정 ───
const EMAILJS_PUBLIC_KEY = '4Up8VbSgiQ5b5E4lr';
const EMAILJS_SERVICE_ID = 'service_14qzhtl';
const EMAILJS_TEMPLATE_ID = 'template_rpv4rxq';

const PERIOD_LABELS = { '36': '3년', '48': '4년', '60': '5년', '72': '6년' };
const PERIOD_ORDER = ['36', '48', '60', '72'];

let allProducts = [];
let categoryMap = {};   // category_name -> products[]
let currentCategory = '전체';
let currentSort = 'default';
let searchQuery = '';
let metaData = null;

// ─── 데이터 로딩 (2단계 fetch) ───

async function loadMeta() {
  const res = await fetch('data/meta.json');
  metaData = await res.json();
  return metaData;
}

async function loadCategoryData(file) {
  const res = await fetch(`data/${file}`);
  return await res.json();
}

async function init() {
  try {
    const meta = await loadMeta();
    document.getElementById('footerUpdate').textContent = `데이터 업데이트: ${meta.updated}`;

    // Load all categories in parallel
    const promises = meta.categories.map(cat => loadCategoryData(cat.file));
    const results = await Promise.all(promises);

    results.forEach((catData, i) => {
      const categoryName = meta.categories[i].name;
      const products = catData.products.map(p => ({
        ...p,
        category: categoryName,
      }));
      categoryMap[categoryName] = products;
      allProducts.push(...products);
    });

    initCategories(meta.categories);
    initQuoteProductOptions(meta.categories);
    renderProducts();
  } catch (e) {
    console.error('Data load error:', e);
    document.getElementById('productGrid').innerHTML =
      '<div class="empty-state"><p>상품 데이터를 불러오는 중 오류가 발생했습니다.</p></div>';
  }

  initModalEvents();
  initSearch();
  initSort();
  initMobileCategoryToggle();
}

// ─── 카테고리 ───

function initCategories(categories) {
  const list = document.getElementById('categoryList');
  const allCount = categories.reduce((sum, c) => sum + c.count, 0);

  list.innerHTML = `<li class="category-item active" data-category="전체">전체 <span class="cat-count">${allCount}</span></li>` +
    categories.map(c =>
      `<li class="category-item" data-category="${c.name}">${c.name} <span class="cat-count">${c.count}</span></li>`
    ).join('');

  list.addEventListener('click', (e) => {
    const item = e.target.closest('.category-item');
    if (!item) return;
    list.querySelectorAll('.category-item').forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    currentCategory = item.dataset.category;
    renderProducts();
    document.getElementById('sidebar').classList.remove('open');
    if (window.innerWidth <= 900) {
      document.querySelector('.main-content').scrollIntoView({ behavior: 'smooth' });
    }
  });
}

// ─── 검색 ───

function initSearch() {
  const input = document.getElementById('searchInput');
  let debounceTimer;
  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      searchQuery = input.value.trim().toLowerCase();
      renderProducts();
    }, 200);
  });
}

// ─── 정렬 ───

function initSort() {
  document.getElementById('sortSelect').addEventListener('change', (e) => {
    currentSort = e.target.value;
    renderProducts();
  });
}

// ─── 제품 렌더링 ───

function getFilteredProducts() {
  let products = currentCategory === '전체'
    ? allProducts
    : (categoryMap[currentCategory] || []);

  if (searchQuery) {
    products = products.filter(p => {
      const text = `${p.model_id || ''} ${p.product_name || ''} ${p.category || ''} ${p.service_type || ''}`.toLowerCase();
      return text.includes(searchQuery);
    });
  }

  if (currentSort === 'price-asc') {
    products = [...products].sort((a, b) => getMinPrice(a) - getMinPrice(b));
  } else if (currentSort === 'price-desc') {
    products = [...products].sort((a, b) => getMinPrice(b) - getMinPrice(a));
  } else if (currentSort === 'name-asc') {
    products = [...products].sort((a, b) => (a.product_name || '').localeCompare(b.product_name || ''));
  }

  return products;
}

function getMinPrice(p) {
  const prices = p.prices || {};
  const vals = Object.values(prices).filter(v => v > 0);
  return vals.length > 0 ? Math.min(...vals) : Infinity;
}

function getDisplayPrice(p) {
  const prices = p.prices || {};
  for (const period of PERIOD_ORDER) {
    if (prices[period]) return { price: prices[period], period };
  }
  return null;
}

function renderProducts() {
  const grid = document.getElementById('productGrid');
  const title = document.getElementById('categoryTitle');
  const count = document.getElementById('productCount');

  const filtered = getFilteredProducts();

  title.textContent = currentCategory === '전체' ? '전체 제품' : currentCategory;
  count.textContent = `${filtered.length}개`;

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-state"><p>해당 조건에 맞는 제품이 없습니다.</p></div>';
    return;
  }

  grid.innerHTML = filtered.map((p, idx) => {
    const dp = getDisplayPrice(p);
    const priceHTML = dp
      ? `<p class="product-price-label">월 렌탈료 (${PERIOD_LABELS[dp.period]})</p>
         <p class="product-price">${dp.price.toLocaleString()}<span class="product-price-unit">원/월</span></p>`
      : `<p class="product-price inquiry-price">문의</p>`;

    const modelShort = (p.model_id || '').split('.')[0];
    const serviceTag = p.service_type ? `<span class="service-tag">${p.service_type}</span>` : '';

    return `
      <div class="product-card" data-idx="${idx}" onclick="openDetail(${idx})">
        <div class="product-image-wrap">
          <img
            class="product-image"
            src="https://www.lge.co.kr/lg5-common-gp/images/common/product-default.jpg"
            alt="${p.product_name || ''}"
            loading="lazy"
            onerror="this.src='https://placehold.co/300x220/f0f0f0/bbb?text=LG'"
          />
          ${serviceTag}
        </div>
        <div class="product-info">
          <span class="product-category-tag">${p.category || ''}</span>
          <p class="product-name">${p.product_name || ''}</p>
          <p class="product-model">${modelShort}</p>
          <div class="product-price-wrap">
            ${priceHTML}
          </div>
        </div>
      </div>`;
  }).join('');
}

// ─── 제품 상세 모달 ───

function openDetail(idx) {
  const filtered = getFilteredProducts();
  const p = filtered[idx];
  if (!p) return;

  const modal = document.getElementById('detailModal');
  const content = document.getElementById('detailModalContent');

  const prices = p.prices || {};
  const availablePeriods = PERIOD_ORDER.filter(k => prices[k]);
  const priceRows = availablePeriods.map(k =>
    `<tr><td>${PERIOD_LABELS[k]}</td><td class="price-cell">${prices[k].toLocaleString()}원/월</td></tr>`
  ).join('');

  const infoRows = [];
  if (p.model_id) infoRows.push(`<tr><td>모델번호</td><td>${p.model_id}</td></tr>`);
  if (p.service_type) infoRows.push(`<tr><td>서비스타입</td><td>${p.service_type}</td></tr>`);
  if (p.visit_cycle) infoRows.push(`<tr><td>방문주기</td><td>${p.visit_cycle}</td></tr>`);
  if (p.install_type) infoRows.push(`<tr><td>설치유형</td><td>${p.install_type}</td></tr>`);
  if (p.size) infoRows.push(`<tr><td>용량/사이즈</td><td>${p.size}</td></tr>`);

  const productName = p.product_name || '';
  const escapedName = productName.replace(/'/g, "\\'");
  const escapedCategory = (p.category || '').replace(/'/g, "\\'");

  content.innerHTML = `
    <div class="detail-header">
      <span class="detail-category">${p.category || ''}</span>
      <h2 class="detail-title">${productName}</h2>
      <p class="detail-model">${p.model_id || ''}</p>
    </div>

    <div class="detail-body">
      <div class="detail-section">
        <h3>제품 정보</h3>
        <table class="detail-table">
          ${infoRows.join('')}
        </table>
      </div>

      <div class="detail-section">
        <h3>월 렌탈료 (2~3대 기준)</h3>
        <table class="detail-table price-table">
          <thead><tr><th>약정기간</th><th>월 렌탈료</th></tr></thead>
          <tbody>${priceRows}</tbody>
        </table>
      </div>
    </div>

    <div class="detail-actions">
      <button class="btn-inquiry" onclick="openQuote('${escapedCategory}', '${escapedName} (${p.model_id || ''})'); closeModal('detailModal');">
        견적문의하기
      </button>
    </div>
  `;

  openModal('detailModal');
}

// ─── 견적문의 모달 ───

function initQuoteProductOptions(categories) {
  const select = document.getElementById('quoteProductSelect');
  categories.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = c.name;
    select.appendChild(opt);
  });
  const otherOpt = document.createElement('option');
  otherOpt.value = '기타';
  otherOpt.textContent = '기타 (아래 메모에 작성)';
  select.appendChild(otherOpt);
}

function openQuote(category, productInfo) {
  const select = document.getElementById('quoteProductSelect');
  for (let i = 0; i < select.options.length; i++) {
    if (select.options[i].value === category) {
      select.selectedIndex = i;
      break;
    }
  }
  if (productInfo) {
    document.getElementById('quoteMessage').value = '문의 제품: ' + productInfo;
  }
  openModal('quoteModal');
}

function resetQuoteForm() {
  const form = document.getElementById('quote-form');
  form.reset();
  document.getElementById('quote-form-section').style.display = '';
  document.getElementById('quote-success-section').style.display = 'none';
  const btn = document.getElementById('quote-submit-btn');
  btn.disabled = false;
  btn.textContent = '견적문의 보내기';
}

// ─── 모달 공통 ───

function openModal(id) {
  document.getElementById(id).classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).classList.remove('active');
  if (!document.querySelector('.modal-overlay.active')) {
    document.body.style.overflow = '';
  }
}

function initModalEvents() {
  document.getElementById('detailModalClose').addEventListener('click', () => closeModal('detailModal'));
  document.getElementById('detailModal').addEventListener('click', function(e) {
    if (e.target === this) closeModal('detailModal');
  });

  document.getElementById('quoteModalClose').addEventListener('click', () => closeModal('quoteModal'));
  document.getElementById('quoteModal').addEventListener('click', function(e) {
    if (e.target === this) closeModal('quoteModal');
  });
  document.getElementById('quoteResetBtn').addEventListener('click', resetQuoteForm);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal('quoteModal');
      closeModal('detailModal');
    }
  });

  // Quote form submit with EmailJS
  const form = document.getElementById('quote-form');
  const submitBtn = document.getElementById('quote-submit-btn');

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = '전송 중...';

    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => { data[key] = value; });

    if (typeof emailjs !== 'undefined' && EMAILJS_PUBLIC_KEY !== 'YOUR_PUBLIC_KEY') {
      emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, data)
        .then(function() {
          document.getElementById('quote-form-section').style.display = 'none';
          document.getElementById('quote-success-section').style.display = 'block';
        })
        .catch(error => {
          alert('전송에 실패했습니다. 전화(010-0000-0000)로 문의해주세요.');
          console.error('EmailJS Error:', error);
          submitBtn.disabled = false;
          submitBtn.textContent = '견적문의 보내기';
        });
    } else {
      console.warn('EmailJS가 설정되지 않았습니다. 폼 데이터:', data);
      document.getElementById('quote-form-section').style.display = 'none';
      document.getElementById('quote-success-section').style.display = 'block';
    }
  });
}

// ─── 모바일 카테고리 토글 ───

function initMobileCategoryToggle() {
  document.getElementById('mobileCategoryToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
}

// ─── 시작 ───
document.addEventListener('DOMContentLoaded', init);
