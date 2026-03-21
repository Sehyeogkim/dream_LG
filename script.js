// ─── Google Apps Script 설정 ───
// Google Apps Script 웹앱 배포 후 아래 URL을 교체하세요
const GAS_WEBAPP_URL = 'YOUR_GAS_WEBAPP_URL';

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
        <button class="product-inquiry" onclick="handleInquiry('${p.category.replace(/'/g, "\\'")}', '${p.name.replace(/'/g, "\\'")}')">
          렌탈 문의하기
        </button>
      </div>
    </div>
  `).join('');
}

// ─── 모달 열기/닫기 ───

function openModal() {
  document.getElementById('modalOverlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('active');
  document.body.style.overflow = '';
}

function handleInquiry(category, productName) {
  // 제품 카테고리 자동 선택
  const productSelect = document.getElementById('modalProductSelect');
  const options = productSelect.options;
  let matched = false;
  for (let i = 0; i < options.length; i++) {
    if (options[i].value === category) {
      productSelect.selectedIndex = i;
      matched = true;
      break;
    }
  }
  if (!matched) {
    // 카테고리가 목록에 없으면 '기타' 선택
    for (let i = 0; i < options.length; i++) {
      if (options[i].value === '기타') {
        productSelect.selectedIndex = i;
        break;
      }
    }
  }

  // 제품명을 추가 요청사항에 미리 입력
  document.getElementById('modalMessage').value = '문의 제품: ' + productName;

  openModal();
}

function resetModalForm() {
  const form = document.getElementById('quote-form');
  form.reset();
  document.getElementById('modal-form-section').style.display = '';
  document.getElementById('modal-success-section').style.display = 'none';
  const btn = document.getElementById('modal-submit-btn');
  btn.disabled = false;
  btn.textContent = '견적문의 보내기';
}

// ─── 카테고리 초기화 ───

function initCategories(categories) {
  const list = document.getElementById('categoryList');

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

// ─── 초기화 ───

async function init() {
  try {
    const res = await fetch('data/products.json');
    const data = await res.json();

    allProducts = data.categories.flatMap(cat =>
      cat.products.map(p => ({ ...p, category: cat.name }))
    );

    initCategories(data.categories);
    renderProducts('전체');
  } catch (e) {
    document.getElementById('productGrid').innerHTML =
      '<div class="empty-state"><p>상품 데이터를 불러오는 중 오류가 발생했습니다.</p></div>';
  }

  // 모달 이벤트
  document.getElementById('modalClose').addEventListener('click', closeModal);
  document.getElementById('modalOverlay').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
  });
  document.getElementById('modalResetBtn').addEventListener('click', resetModalForm);

  // ESC 키로 닫기
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
  });

  // 폼 전송
  const form = document.getElementById('quote-form');
  const submitBtn = document.getElementById('modal-submit-btn');

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    submitBtn.disabled = true;
    submitBtn.textContent = '전송 중...';

    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => { data[key] = value; });

    if (GAS_WEBAPP_URL !== 'YOUR_GAS_WEBAPP_URL') {
      fetch(GAS_WEBAPP_URL, {
        method: 'POST',
        body: JSON.stringify(data),
      })
        .then(function(res) { return res.json(); })
        .then(function(result) {
          if (result.status === 'success') {
            document.getElementById('modal-form-section').style.display = 'none';
            document.getElementById('modal-success-section').style.display = 'block';
          } else {
            throw new Error(result.message || '전송 실패');
          }
        })
        .catch(function(error) {
          alert('전송에 실패했습니다. 전화(010-0000-0000)로 문의해주세요.');
          console.error('GAS Error:', error);
          submitBtn.disabled = false;
          submitBtn.textContent = '견적문의 보내기';
        });
    } else {
      // GAS 미설정 시 성공 화면만 표시 (개발/테스트용)
      console.warn('Google Apps Script URL이 설정되지 않았습니다. 폼 데이터:', data);
      document.getElementById('modal-form-section').style.display = 'none';
      document.getElementById('modal-success-section').style.display = 'block';
    }
  });
}

document.addEventListener('DOMContentLoaded', init);
