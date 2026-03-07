const products = [
  // 컴퓨터
  {
    id: 1,
    name: "LG 일체형 PC 24V70R",
    category: "컴퓨터",
    price: 39000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+PC",
    desc: "인텔 코어 i5, 23.8인치 FHD"
  },
  {
    id: 2,
    name: "LG 일체형 PC 27V70R",
    category: "컴퓨터",
    price: 49000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+PC+27",
    desc: "인텔 코어 i7, 27인치 QHD"
  },

  // 노트북
  {
    id: 3,
    name: "LG 그램 14 (2024)",
    category: "노트북",
    price: 45000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+gram+14",
    desc: "인텔 Ultra 5, 14인치, 1kg대 초경량"
  },
  {
    id: 4,
    name: "LG 그램 16 (2024)",
    category: "노트북",
    price: 55000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+gram+16",
    desc: "인텔 Ultra 7, 16인치 WQXGA"
  },
  {
    id: 5,
    name: "LG 그램 Pro 16 (2024)",
    category: "노트북",
    price: 69000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+gram+Pro",
    desc: "인텔 Ultra 7, OLED, AI 성능"
  },

  // 청소기
  {
    id: 6,
    name: "LG 코드제로 A9S",
    category: "청소기",
    price: 19000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+A9S",
    desc: "무선 청소기, 올인원타워 포함"
  },
  {
    id: 7,
    name: "LG 코드제로 R9 로봇청소기",
    category: "청소기",
    price: 29000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+R9",
    desc: "로봇청소기, 자동 먼지 비움"
  },
  {
    id: 8,
    name: "LG 코드제로 M9 물걸레",
    category: "청소기",
    price: 25000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+M9",
    desc: "물걸레 로봇청소기"
  },

  // 세탁기
  {
    id: 9,
    name: "LG 트롬 세탁기 21kg",
    category: "세탁기",
    price: 35000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+트롬+21",
    desc: "드럼세탁기, AI DD모터, 21kg"
  },
  {
    id: 10,
    name: "LG 트롬 워시타워 콤팩트",
    category: "세탁기",
    price: 55000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+워시타워",
    desc: "세탁+건조 일체형, 공간 절약"
  },
  {
    id: 11,
    name: "LG 트롬 건조기 16kg",
    category: "세탁기",
    price: 29000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+건조기",
    desc: "듀얼 인버터 히트펌프 건조기"
  },

  // TV
  {
    id: 12,
    name: "LG OLED 65인치 C4",
    category: "TV",
    price: 79000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+OLED+65",
    desc: "OLED evo, 4K, 120Hz, webOS"
  },
  {
    id: 13,
    name: "LG QNED 75인치 (2024)",
    category: "TV",
    price: 59000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+QNED+75",
    desc: "QNED, 4K, 120Hz"
  },
  {
    id: 14,
    name: "LG UHD TV 55인치",
    category: "TV",
    price: 35000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+UHD+55",
    desc: "4K UHD, ThinQ AI"
  },

  // 냉장고
  {
    id: 15,
    name: "LG 디오스 오브제컬렉션 냉장고 870L",
    category: "냉장고",
    price: 89000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+냉장고+870",
    desc: "양문형, 870L, 오브제 디자인"
  },
  {
    id: 16,
    name: "LG 디오스 냉장고 636L",
    category: "냉장고",
    price: 59000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+냉장고+636",
    desc: "양문형, 636L, 냉장고 매직스페이스"
  },
  {
    id: 17,
    name: "LG 김치냉장고 324L",
    category: "냉장고",
    price: 39000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+김치냉장고",
    desc: "스탠드형 김치냉장고, 324L"
  },

  // 에어컨
  {
    id: 18,
    name: "LG 휘센 타워 에어컨 18평",
    category: "에어컨",
    price: 49000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+휘센+18",
    desc: "스탠드형, 18평, AI 스마트케어"
  },
  {
    id: 19,
    name: "LG 휘센 벽걸이 에어컨 14평",
    category: "에어컨",
    price: 29000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+벽걸이+14",
    desc: "벽걸이형, 14평, 인버터"
  },
  {
    id: 20,
    name: "LG 휘센 시스템 에어컨",
    category: "에어컨",
    price: 69000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+시스템에어컨",
    desc: "4방향 카세트형, 멀티 제어"
  },

  // 기타
  {
    id: 21,
    name: "LG 스타일러 5벌",
    category: "기타",
    price: 35000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+스타일러",
    desc: "의류관리기, 5벌, 살균+탈취"
  },
  {
    id: 22,
    name: "LG 식기세척기 14인용",
    category: "기타",
    price: 29000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+식기세척기",
    desc: "빌트인형, 14인용, 스팀세척"
  },
  {
    id: 23,
    name: "LG 정수기 오브제컬렉션",
    category: "기타",
    price: 19000,
    image: "https://placehold.co/300x220/f5f5f5/999?text=LG+정수기",
    desc: "냉온정수, 직수형, UV살균"
  }
];
