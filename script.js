// ─── 설정 ───
const EMAILJS_PUBLIC_KEY = '4Up8VbSgiQ5b5E4lr';
const EMAILJS_SERVICE_ID = 'service_14qzhtl';
const EMAILJS_TEMPLATE_ID = 'template_rpv4rxq';

const PERIOD_LABELS = { '36': '3년', '48': '4년', '60': '5년', '72': '6년' };
const PERIOD_ORDER = ['36', '48', '60', '72'];
const TIER_LABELS = { '1': '1대', '2-3': '2~3대', '4-9': '4~9대', '10-29': '10~29대', '30+': '30대 이상' };
const TIER_ORDER = ['1', '2-3', '4-9', '10-29', '30+'];

let allProducts = [];
let categoryMap = {};
let currentCategory = '전체';
let currentSort = 'default';
let searchQuery = '';
let metaData = null;

// ─── 데이터 로딩 ───

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

// ─── 가격 유틸리티 ───

function getNestedPrice(prices, period, tier) {
  if (!prices || !prices[period]) return null;
  if (typeof prices[period] === 'object') {
    return prices[period][tier] || null;
  }
  return prices[period]; // fallback for flat format
}

function getDefaultDisplayPrice(p) {
  const prices = p.prices || {};
  for (const period of PERIOD_ORDER) {
    if (!prices[period]) continue;
    if (typeof prices[period] === 'object') {
      // prefer "2-3" tier, then "1"
      const val = prices[period]['2-3'] || prices[period]['1'];
      if (val) return { price: val, period, tier: prices[period]['2-3'] ? '2-3' : '1' };
    } else {
      return { price: prices[period], period };
    }
  }
  return null;
}

function getMinPrice(p) {
  const prices = p.prices || {};
  let min = Infinity;
  for (const period of PERIOD_ORDER) {
    if (!prices[period]) continue;
    if (typeof prices[period] === 'object') {
      for (const v of Object.values(prices[period])) {
        if (v > 0 && v < min) min = v;
      }
    } else if (prices[period] > 0 && prices[period] < min) {
      min = prices[period];
    }
  }
  return min;
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
    const dp = getDefaultDisplayPrice(p);
    const priceHTML = dp
      ? `<p class="product-price-label">월 렌탈료 (${PERIOD_LABELS[dp.period]})</p>
         <p class="product-price">${dp.price.toLocaleString()}<span class="product-price-unit">원/월</span></p>`
      : `<p class="product-price inquiry-price">문의</p>`;

    const modelShort = (p.model_id || '').split('.')[0];
    const serviceTag = p.service_type ? `<span class="service-tag">${p.service_type}</span>` : '';

    const imgSrc = (p.images && p.images.length > 0)
      ? p.images[0]
      : 'https://www.lge.co.kr/lg5-common-gp/images/common/product-default.jpg';

    return `
      <div class="product-card" data-idx="${idx}" onclick="openDetail(${idx})">
        <div class="product-image-wrap">
          <img
            class="product-image"
            src="${imgSrc}"
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

// ─── 제품 상세 모달 (LG 스타일) ───

// Find all variants of a product (same model_id, different service_type/visit_cycle)
function findProductVariants(product) {
  return allProducts.filter(p => p.model_id === product.model_id && p.category === product.category);
}

// Get unique values for a field across variants
function getUniqueOptions(variants, field) {
  const vals = [...new Set(variants.map(v => v[field]).filter(Boolean))];
  return vals;
}

// Find best matching variant given current selections
function findMatchingVariant(variants, serviceType, visitCycle) {
  let match = variants.find(v =>
    (!serviceType || v.service_type === serviceType) &&
    (!visitCycle || v.visit_cycle === visitCycle)
  );
  if (!match) match = variants.find(v => !serviceType || v.service_type === serviceType);
  if (!match) match = variants[0];
  return match;
}

let detailState = {
  variants: [],
  currentVariant: null,
  selectedPeriod: null,
  selectedTier: '2-3',
  selectedServiceType: null,
  selectedVisitCycle: null,
};

function openDetail(idx) {
  const filtered = getFilteredProducts();
  const p = filtered[idx];
  if (!p) return;

  const variants = findProductVariants(p);
  const serviceTypes = getUniqueOptions(variants, 'service_type');
  const visitCycles = getUniqueOptions(variants, 'visit_cycle');

  detailState.variants = variants;
  detailState.currentVariant = p;
  detailState.selectedServiceType = p.service_type || serviceTypes[0] || null;
  detailState.selectedVisitCycle = p.visit_cycle || visitCycles[0] || null;

  // Pick default period (first available)
  const prices = p.prices || {};
  const availablePeriods = PERIOD_ORDER.filter(k => prices[k]);
  detailState.selectedPeriod = availablePeriods[0] || null;

  // Pick default tier
  detailState.selectedTier = '2-3';

  renderDetailModal();
  openModal('detailModal');
}

function renderDetailModal() {
  const content = document.getElementById('detailModalContent');
  const v = detailState.currentVariant;
  const variants = detailState.variants;

  const serviceTypes = getUniqueOptions(variants, 'service_type');
  const visitCycles = getUniqueOptions(variants, 'visit_cycle');
  const prices = v.prices || {};
  const availablePeriods = PERIOD_ORDER.filter(k => prices[k]);

  // Get available tiers from current period
  const currentPeriodPrices = prices[detailState.selectedPeriod] || {};
  const availableTiers = TIER_ORDER.filter(t => currentPeriodPrices[t] !== undefined);

  // Current price
  const currentPrice = getNestedPrice(prices, detailState.selectedPeriod, detailState.selectedTier);
  const basePrice = getNestedPrice(prices, detailState.selectedPeriod, '1');
  const hasDiscount = currentPrice && basePrice && currentPrice < basePrice;
  const discountPercent = hasDiscount ? Math.round((1 - currentPrice / basePrice) * 100) : 0;

  const imgSrc = (v.images && v.images.length > 0)
    ? v.images[0]
    : 'https://www.lge.co.kr/lg5-common-gp/images/common/product-default.jpg';

  // Build image gallery (if multiple images)
  const images = (v.images && v.images.length > 0) ? v.images : [imgSrc];
  const galleryThumbs = images.length > 1
    ? `<div class="detail-gallery-thumbs">${images.map((img, i) =>
        `<img src="${img}" class="detail-thumb ${i === 0 ? 'active' : ''}" onclick="switchDetailImage(this, '${img}')" onerror="this.style.display='none'" />`
      ).join('')}</div>`
    : '';

  // Service type selector
  const serviceTypeHTML = serviceTypes.length > 0
    ? `<div class="detail-option-group">
        <label class="detail-option-label">서비스타입</label>
        <div class="detail-option-chips" data-option="serviceType">
          ${serviceTypes.map(st =>
            `<button class="option-chip ${st === detailState.selectedServiceType ? 'active' : ''}" data-value="${st}">${st}</button>`
          ).join('')}
        </div>
      </div>`
    : '';

  // Visit cycle selector
  const visitCycleHTML = visitCycles.length > 0
    ? `<div class="detail-option-group">
        <label class="detail-option-label">방문주기</label>
        <div class="detail-option-chips" data-option="visitCycle">
          ${visitCycles.map(vc =>
            `<button class="option-chip ${vc === detailState.selectedVisitCycle ? 'active' : ''}" data-value="${vc}">${vc}</button>`
          ).join('')}
        </div>
      </div>`
    : '';

  // Period selector
  const periodHTML = availablePeriods.length > 0
    ? `<div class="detail-option-group">
        <label class="detail-option-label">약정기간</label>
        <div class="detail-option-chips" data-option="period">
          ${availablePeriods.map(per =>
            `<button class="option-chip ${per === detailState.selectedPeriod ? 'active' : ''}" data-value="${per}">${PERIOD_LABELS[per]}</button>`
          ).join('')}
        </div>
      </div>`
    : '';

  // Tier (quantity) selector
  const tierHTML = availableTiers.length > 0
    ? `<div class="detail-option-group">
        <label class="detail-option-label">수량</label>
        <div class="detail-option-chips" data-option="tier">
          ${availableTiers.map(t =>
            `<button class="option-chip ${t === detailState.selectedTier ? 'active' : ''}" data-value="${t}">${TIER_LABELS[t] || t}</button>`
          ).join('')}
        </div>
      </div>`
    : '';

  // Price display
  const priceDisplayHTML = currentPrice
    ? `<div class="detail-price-box">
        ${hasDiscount ? `<div class="detail-discount-badge">-${discountPercent}%</div>` : ''}
        ${hasDiscount ? `<div class="detail-original-price">${basePrice.toLocaleString()}원/월</div>` : ''}
        <div class="detail-current-price">${currentPrice.toLocaleString()}<span class="detail-price-unit">원/월</span></div>
        <div class="detail-price-desc">${PERIOD_LABELS[detailState.selectedPeriod] || ''} 약정 · ${TIER_LABELS[detailState.selectedTier] || detailState.selectedTier} 기준</div>
      </div>`
    : `<div class="detail-price-box"><div class="detail-current-price">가격 문의</div></div>`;

  // Full price table
  const priceTableRows = availablePeriods.map(per => {
    const perPrices = prices[per] || {};
    return `<tr>
      <td class="period-label">${PERIOD_LABELS[per]}</td>
      ${availableTiers.map(t => {
        const val = perPrices[t];
        const isSelected = per === detailState.selectedPeriod && t === detailState.selectedTier;
        return `<td class="${isSelected ? 'selected-cell' : ''}">${val ? val.toLocaleString() : '-'}</td>`;
      }).join('')}
    </tr>`;
  }).join('');

  const priceTableHTML = availableTiers.length > 0 && availablePeriods.length > 0
    ? `<div class="detail-price-table-wrap">
        <table class="detail-price-table">
          <thead><tr><th></th>${availableTiers.map(t => `<th>${TIER_LABELS[t] || t}</th>`).join('')}</tr></thead>
          <tbody>${priceTableRows}</tbody>
        </table>
      </div>`
    : '';

  const escapedName = (v.product_name || '').replace(/'/g, "\\'");
  const escapedCategory = (v.category || '').replace(/'/g, "\\'");

  content.innerHTML = `
    <div class="detail-layout">
      <div class="detail-left">
        <div class="detail-gallery">
          <img class="detail-main-image" id="detailMainImage" src="${images[0]}"
            alt="${v.product_name || ''}"
            onerror="this.src='https://placehold.co/500x400/f0f0f0/bbb?text=LG'" />
          ${galleryThumbs}
        </div>
      </div>
      <div class="detail-right">
        <div class="detail-right-header">
          <span class="detail-category">${v.category || ''}</span>
          <h2 class="detail-title">${v.product_name || ''}</h2>
          <p class="detail-model">${v.model_id || ''}</p>
        </div>

        <div class="detail-options">
          ${serviceTypeHTML}
          ${visitCycleHTML}
          ${periodHTML}
          ${tierHTML}
        </div>

        ${priceDisplayHTML}

        <div class="detail-actions">
          <button class="btn-inquiry" onclick="openQuote('${escapedCategory}', '${escapedName} (${v.model_id || ''})'); closeModal('detailModal');">
            견적문의하기
          </button>
        </div>
      </div>
    </div>

    <div class="detail-bottom">
      <h3 class="detail-section-title">전체 가격표</h3>
      ${priceTableHTML}
    </div>
  `;

  // Attach option click handlers
  content.querySelectorAll('.detail-option-chips').forEach(group => {
    group.addEventListener('click', (e) => {
      const chip = e.target.closest('.option-chip');
      if (!chip) return;
      const optionType = group.dataset.option;
      const value = chip.dataset.value;

      if (optionType === 'serviceType') {
        detailState.selectedServiceType = value;
        const newVariant = findMatchingVariant(variants, value, detailState.selectedVisitCycle);
        detailState.currentVariant = newVariant;
        // Reset period if not available
        const newPrices = newVariant.prices || {};
        if (!newPrices[detailState.selectedPeriod]) {
          detailState.selectedPeriod = PERIOD_ORDER.find(k => newPrices[k]) || null;
        }
      } else if (optionType === 'visitCycle') {
        detailState.selectedVisitCycle = value;
        const newVariant = findMatchingVariant(variants, detailState.selectedServiceType, value);
        detailState.currentVariant = newVariant;
        const newPrices = newVariant.prices || {};
        if (!newPrices[detailState.selectedPeriod]) {
          detailState.selectedPeriod = PERIOD_ORDER.find(k => newPrices[k]) || null;
        }
      } else if (optionType === 'period') {
        detailState.selectedPeriod = value;
      } else if (optionType === 'tier') {
        detailState.selectedTier = value;
      }

      renderDetailModal();
    });
  });
}

function switchDetailImage(thumbEl, src) {
  document.getElementById('detailMainImage').src = src;
  document.querySelectorAll('.detail-thumb').forEach(t => t.classList.remove('active'));
  thumbEl.classList.add('active');
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
