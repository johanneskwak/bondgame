import base64
import io
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

st.set_page_config(page_title="Bond History Premium Game", page_icon="💵", layout="wide")

CUSTOM_CSS = """
<style>
html, body, [class*="css"] { font-family: "Pretendard", "Noto Sans KR", sans-serif; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1450px; }
.hero {
    background: radial-gradient(circle at top left, rgba(95,129,255,0.17), transparent 28%),
                radial-gradient(circle at top right, rgba(0,191,165,0.12), transparent 22%),
                linear-gradient(180deg, #f8faff 0%, #f2f6fd 100%);
    border: 1px solid #dfe7fb; border-radius: 28px; padding: 24px 26px; margin-bottom: 18px;
    box-shadow: 0 18px 50px rgba(27,45,94,0.06);
}
.hero-title { font-size: 2.4rem; font-weight: 900; color: #172341; margin-bottom: .2rem; }
.hero-sub { font-size: 1rem; color: #62708c; margin-bottom: .8rem; }
.chip {
    display:inline-block; padding:5px 12px; border-radius:999px; background:#eef3ff; border:1px solid #d7e2ff;
    font-size:.82rem; font-weight:700; color:#2d406d; margin-right:8px; margin-bottom:8px;
}
.panel { background:#fff; border:1px solid #e7ecf7; border-radius:24px; padding:20px; box-shadow:0 10px 30px rgba(20,40,90,.05); margin-bottom:16px; }
.kpi { background:linear-gradient(180deg,#fff 0%,#fbfcff 100%); border:1px solid #e4eaf7; border-radius:22px; padding:16px 18px; box-shadow:0 10px 28px rgba(40,60,120,.05); min-height:116px; }
.kpi-label { color:#6a7390; font-size:.9rem; margin-bottom:4px; }
.kpi-value { color:#17213b; font-size:1.65rem; font-weight:900; line-height:1.15; }
.kpi-sub { color:#7c859d; font-size:.82rem; margin-top:6px; }
.event-card { background:linear-gradient(145deg,#fff 0%,#f8fbff 100%); border:1px solid #dfe7ff; border-radius:28px; padding:22px; box-shadow:0 14px 40px rgba(30,50,100,.07); }
.choice-card { background:#fff; border:1px solid #e5ebf7; border-radius:22px; padding:16px; box-shadow:0 8px 26px rgba(40,60,120,.05); min-height:250px; }
.event-title { font-size:1.7rem; font-weight:900; color:#16213d; margin-top:6px; }
.section-title { font-size:1.04rem; font-weight:800; color:#1c2b52; margin-bottom:8px; }
.muted { color:#66728f; }
.soft-line { border:none; border-top:1px solid #eef2fb; margin:16px 0; }
.explain-box { background:linear-gradient(180deg,#f9fcff 0%,#f1f7ff 100%); border:1px solid #d7e8ff; border-radius:20px; padding:18px; margin-top:16px; }
.learn-box { background:linear-gradient(180deg,#fffdfa 0%,#fff7eb 100%); border:1px solid #ffe0a8; border-radius:20px; padding:18px; margin-bottom:12px; }
.term-box { background:#fff; border:1px solid #eceff7; border-radius:16px; padding:12px 14px; margin-bottom:10px; }
.good-result { background:linear-gradient(180deg,#eefcf4 0%,#e7fbef 100%); border:1px solid #bde7ca; border-radius:20px; padding:18px; margin-top:14px; }
.bad-result { background:linear-gradient(180deg,#fff4f4 0%,#fff0f0 100%); border:1px solid #f1c0c0; border-radius:20px; padding:18px; margin-top:14px; }
.ending-card { background:radial-gradient(circle at top right, rgba(108,137,255,.13), transparent 22%), linear-gradient(145deg,#fff 0%,#f5f8ff 100%); border:1px solid #dce5ff; border-radius:28px; padding:28px; box-shadow:0 16px 42px rgba(20,40,90,.08); }
.log-card { background:#fff; border:1px solid #e7ecf7; border-radius:16px; padding:14px 16px; margin-bottom:10px; }
.grade-pill { display:inline-block; background:#eef3ff; border:1px solid #d7e3ff; color:#28406d; padding:5px 12px; border-radius:999px; font-size:.84rem; font-weight:800; margin-bottom:10px; }
.small-note { font-size:.82rem; color:#7b849b; }
.nav-caption { color:#6f7a93; font-size:.9rem; margin-bottom:4px; }
.portfolio-card { background:#fff; border:1px solid #e7ecf7; border-radius:20px; padding:18px; margin-bottom:14px; box-shadow:0 8px 26px rgba(40,60,120,.04); }
.portfolio-title { font-weight:900; color:#17213b; margin-bottom:8px; }
img.card-art { width:100%; border-radius:18px; border:1px solid #e5ebf8; background:#f7f9ff; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

TERM_DICTIONARY = [
    ("채권", "정부나 회사에 돈을 빌려주고, 나중에 이자와 원금을 돌려받는 약속 증서."),
    ("국채", "정부가 발행하는 채권. 보통 가장 안전한 축에 들어간다."),
    ("회사채", "기업이 발행하는 채권. 국채보다 위험할 수 있지만 이자가 더 높을 수 있다."),
    ("금리", "돈의 가격. 금리가 오르면 기존 채권 가격은 대체로 내려가고, 금리가 내리면 기존 채권 가격은 대체로 오른다."),
    ("듀레이션", "채권 가격이 금리 변화에 얼마나 민감한지 보여주는 개념. 길수록 더 크게 흔들린다."),
    ("신용스프레드", "회사채가 국채보다 더 얹어 주는 금리 차이. 불안할수록 커지기 쉽다."),
    ("양적완화(QE)", "중앙은행이 채권을 직접 사들여 시장에 돈을 푸는 정책."),
    ("테이퍼", "중앙은행이 채권 매입 규모를 줄이는 것. 시장은 긴축 신호로 받아들일 수 있다."),
    ("장단기 금리차 역전", "단기금리가 장기금리보다 높아진 상태. 경기 둔화 신호로 자주 해석된다."),
    ("TIPS", "물가가 오를수록 원금이 조정되는 미국 물가연동국채."),
]

BEGINNER_EXPLAINERS = {
    "디플레이션": "물가가 내려가면 미래에 받을 고정 이자의 가치가 상대적으로 커진다. 그래서 안전한 국채가 강해지기 쉽다.",
    "인플레이션": "물가가 오르면 미래에 받는 고정 이자의 실질 가치가 깎인다. 그래서 일반 채권, 특히 장기채에는 불리하다.",
    "금리 인상": "새로 발행되는 채권 이자가 더 높아지므로, 예전에 낮은 이자를 약속한 채권 가격은 내려가기 쉽다.",
    "금리 인하": "기존 채권의 이자가 상대적으로 좋아 보이므로, 기존 채권 가격은 올라가기 쉽다.",
    "안전자산 선호": "시장이 무서울 때 투자자들은 위험한 자산보다 국채처럼 비교적 안전한 자산으로 몰린다.",
    "듀레이션": "쉽게 말해 금리 충격에 얼마나 크게 흔들리는지다. 장기채일수록 보통 더 민감하다.",
    "QE": "중앙은행이 직접 채권을 사들이면 채권 수요가 늘어 가격이 오르고 금리는 내려가기 쉽다.",
}

COLOR_MAP = {
    "blue": ("#eaf2ff", "#d5e4ff", "#678df2"),
    "teal": ("#e8fbf7", "#d0f5eb", "#32b89c"),
    "gold": ("#fff8e8", "#ffe9b0", "#d8a11e"),
    "rose": ("#fff0f4", "#ffd5df", "#db6791"),
    "slate": ("#f2f5f9", "#dde5f0", "#6b7b93"),
    "mint": ("#eefcf4", "#d7f6e3", "#51b57c"),
}

@dataclass
class MiniQuiz:
    question: str
    options: List[str]
    answer_idx: int
    explanation: str

@dataclass
class Scenario:
    year: str
    title: str
    fed_news: str
    concept: str
    event_icon: str
    choices: List[str]
    results: List[float]
    result_texts: List[str]
    choice_icons: List[str]
    difficulty: int
    easy_bond_explanation: str
    beginner_tip: str
    keyword: str
    teacher_commentary: str
    discussion_prompt: str
    event_palette: str
    choice_palettes: List[str]
    portfolio_shift: List[Dict[str, float]]
    mini_quiz: MiniQuiz


def money_to_str(amount: float) -> str:
    eok = amount / 100
    return f"{eok:,.1f}억 원"


def pct_to_str(r: float) -> str:
    sign = "+" if r >= 0 else ""
    return f"{sign}{r * 100:.1f}%"


def safe_ratio(balance: float, base: float) -> float:
    return 0.0 if base == 0 else balance / base


def svg_data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def make_banner_svg(title: str, subtitle: str, accent: str = "blue", icon: str = "◆") -> str:
    bg, bg2, line = COLOR_MAP[accent]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="330" viewBox="0 0 1200 330">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="{bg}"/>
        <stop offset="100%" stop-color="#ffffff"/>
      </linearGradient>
    </defs>
    <rect x="0" y="0" width="1200" height="330" rx="28" fill="url(#g)"/>
    <circle cx="985" cy="65" r="120" fill="{bg2}" opacity="0.8"/>
    <circle cx="1115" cy="260" r="95" fill="{bg2}" opacity="0.55"/>
    <rect x="42" y="42" width="150" height="150" rx="28" fill="#ffffff" opacity="0.96" stroke="{line}" stroke-width="3"/>
    <text x="117" y="138" text-anchor="middle" font-size="78" font-weight="700" fill="{line}">{icon}</text>
    <text x="230" y="116" font-family="Arial" font-size="20" fill="#64748b">Bond History Event Card</text>
    <text x="230" y="168" font-family="Arial" font-size="38" font-weight="700" fill="#17213b">{title}</text>
    <text x="230" y="212" font-family="Arial" font-size="24" fill="#475569">{subtitle}</text>
    <rect x="230" y="240" width="170" height="14" rx="7" fill="{line}" opacity="0.75"/>
    <rect x="415" y="240" width="95" height="14" rx="7" fill="{bg2}"/>
    <rect x="525" y="240" width="68" height="14" rx="7" fill="{bg2}"/>
    </svg>'''
    return svg_data_uri(svg)


def make_choice_svg(title: str, tag: str, accent: str = "teal", icon: str = "■") -> str:
    bg, bg2, line = COLOR_MAP[accent]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="{bg}"/></linearGradient></defs>
    <rect x="0" y="0" width="900" height="240" rx="24" fill="url(#g)" stroke="{bg2}" stroke-width="2"/>
    <circle cx="118" cy="120" r="72" fill="{bg2}"/>
    <text x="118" y="145" text-anchor="middle" font-size="72" font-weight="700" fill="{line}">{icon}</text>
    <text x="220" y="92" font-family="Arial" font-size="20" fill="#64748b">Decision Card</text>
    <text x="220" y="136" font-family="Arial" font-size="30" font-weight="700" fill="#17213b">{title}</text>
    <rect x="220" y="160" width="155" height="34" rx="17" fill="{bg2}"/>
    <text x="297" y="183" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700" fill="#21436b">{tag}</text>
    <rect x="784" y="42" width="68" height="18" rx="9" fill="{line}" opacity="0.65"/>
    <rect x="736" y="74" width="116" height="18" rx="9" fill="{bg2}" opacity="0.7"/>
    <rect x="694" y="106" width="158" height="18" rx="9" fill="{bg2}" opacity="0.5"/>
    </svg>'''
    return svg_data_uri(svg)


def get_badge(balance: float, initial_balance: float) -> str:
    ratio = safe_ratio(balance, initial_balance)
    if ratio >= 2.0:
        return "👑 글로벌 매크로 황제"
    if ratio >= 1.6:
        return "🏆 연준 해석 마스터"
    if ratio >= 1.3:
        return "📈 채권 전략가"
    if ratio >= 1.0:
        return "🧭 생존형 포트폴리오 매니저"
    return "⚠️ 흔들리는 트레이더"


def get_ending(balance: float, initial_balance: float) -> Dict[str, str]:
    ratio = safe_ratio(balance, initial_balance)
    if ratio >= 2.0:
        return {"grade": "S급", "title": "JP모건 싱가포르 본부장", "icon": "👑", "desc": "연준의 워딩, 물가 경로, 금리 곡선의 변화를 누구보다 먼저 읽어낸 인물. 이제 당신의 한마디가 아시아 채권시장을 흔든다."}
    if ratio >= 1.6:
        return {"grade": "A급+", "title": "골드만삭스 아시아 매크로 헤드", "icon": "💼", "desc": "불확실성과 변동성을 통제하면서도 수익 기회를 놓치지 않았다. 방향성과 리스크 관리가 모두 뛰어나다."}
    if ratio >= 1.3:
        return {"grade": "A급", "title": "NH투자증권 전임운용역", "icon": "📊", "desc": "국내 기관 자금 운용을 맡길 만한 수준의 해석력과 실전 감각을 보여줬다. 급등락 구간에서도 포지션을 망가뜨리지 않았다."}
    if ratio >= 1.1:
        return {"grade": "B급+", "title": "국민연금 채권운용 주니어 매니저", "icon": "🏦", "desc": "큰 실수 없이 기회를 포착했다. 아직 더 날카로워질 필요는 있지만 기본기는 탄탄하다."}
    if ratio >= 0.9:
        return {"grade": "B급", "title": "증권사 채권영업부 애널리스트", "icon": "📝", "desc": "시장 해석의 감은 있다. 다만 결정적 순간에 확신과 사이징이 조금 부족했다."}
    return {"grade": "C급", "title": "리스크관리팀 인턴 재배치", "icon": "⚠️", "desc": "이번 사이클은 쉽지 않았다. 하지만 채권시장은 한 번 무너져본 사람이 더 오래 살아남기도 한다."}


def get_survival_status(balance: float, survival_limit: float, initial_balance: float) -> Tuple[str, str]:
    ratio = safe_ratio(balance, initial_balance)
    if balance <= survival_limit:
        return "위험", "생존선 붕괴"
    if ratio >= 1.6:
        return "최상", "압도적 우위"
    if ratio >= 1.2:
        return "안정", "상당히 우세"
    if ratio >= 1.0:
        return "보통", "버티는 중"
    return "주의", "방어 필요"


def bounded_add(base: float, delta: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, base + delta))


def normalize_portfolio(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(v, 0.0) for v in weights.values())
    if total == 0:
        return {k: 0.0 for k in weights}
    return {k: max(v, 0.0) / total for k, v in weights.items()}


def get_teacher_summary(scenario: dict) -> str:
    best_idx = max(range(len(scenario["results"])), key=lambda i: scenario["results"][i])
    return f"교사 해설: 이번 장면의 최적 선택은 '{scenario['choices'][best_idx]}'이다. 이유는 {scenario['teacher_commentary']}"


def load_scenarios() -> List[Scenario]:
    return [
        Scenario(
            year="1929년", title="대공황의 시작",
            fed_news="주식 시장 붕괴 이후 연준은 초기에 적극적으로 금리를 내리지 않았고, 심각한 디플레이션이 발생했다.",
            concept="디플레이션 시기에는 고정된 이자를 주는 안전자산의 실질 가치가 상승한다.",
            event_icon="⬡", choices=["우량 국채 매수", "회사채 매수"], results=[0.20, -0.50],
            result_texts=["디플레이션과 안전자산 선호가 겹치며 국채 가격이 크게 올랐다.", "기업 부도 위험이 커지며 회사채는 심하게 흔들렸다."],
            choice_icons=["▣", "▲"], difficulty=1,
            easy_bond_explanation="국채는 나라에 돈을 빌려주는 것에 가깝고, 회사채는 기업에 돈을 빌려주는 것에 가깝다. 경제가 무너지면 정부가 기업보다 더 안전하다고 여겨지기 쉽다.",
            beginner_tip="경기가 급격히 나빠질 때는 누가 더 안전한가를 먼저 생각하면 된다.", keyword="디플레이션",
            teacher_commentary="디플레이션에서는 미래의 고정 현금흐름 가치가 커지고, 동시에 기업 부도 위험이 급격히 상승한다.",
            discussion_prompt="왜 디플레이션 국면에서는 높은 이자보다 안전성이 더 중요해질까?",
            event_palette="blue", choice_palettes=["blue", "rose"],
            portfolio_shift=[{"gov_bonds":0.14,"cash":-0.04,"duration":0.08,"credit":-0.10,"inflation":-0.02},{"credit":0.16,"cash":-0.06,"gov_bonds":-0.08,"duration":0.02}],
            mini_quiz=MiniQuiz("디플레이션 시기에 상대적으로 유리해지기 쉬운 자산은?", ["고정 이자를 주는 안전한 국채", "부도 위험이 큰 저신용 회사채", "현금흐름이 불안한 장외채권"], 0, "디플레이션에서는 미래 고정 이자의 실질 가치가 커지고, 안전자산 선호도 강화되기 쉽다."),
        ),
        Scenario(
            year="1973년", title="제1차 오일쇼크",
            fed_news="유가 급등으로 물가는 오르는데 경기는 나빠지는 스태그플레이션이 발생했다.",
            concept="인플레이션은 채권 투자자에게 불리하며, 특히 장기채일수록 충격이 크다.",
            event_icon="◈", choices=["단기채 보유", "장기채 매수"], results=[-0.02, -0.15],
            result_texts=["손실은 있었지만 만기가 짧아 충격을 크게 줄였다.", "장기채는 금리 상승 충격을 크게 받아 가격이 더 많이 내려갔다."],
            choice_icons=["◆", "▭"], difficulty=1,
            easy_bond_explanation="같은 채권이라도 만기가 짧은 채권은 금리 변화에 덜 흔들리고, 만기가 긴 채권은 더 크게 흔들리는 편이다.",
            beginner_tip="금리가 오를 것 같으면 보통 장기채보다 단기채가 덜 아프다.", keyword="인플레이션",
            teacher_commentary="스태그플레이션은 물가 압력이 금리 상승을 자극하므로 듀레이션 관리가 핵심이다.",
            discussion_prompt="장기채가 단기채보다 금리 상승 충격에 더 민감한 이유는 무엇일까?",
            event_palette="gold", choice_palettes=["mint", "gold"],
            portfolio_shift=[{"short_bonds":0.16,"duration":-0.12,"cash":-0.04},{"long_bonds":0.18,"duration":0.18,"cash":-0.06,"inflation":-0.08}],
            mini_quiz=MiniQuiz("금리가 오르는 시기에 보통 더 크게 흔들리는 것은?", ["단기채", "장기채", "현금"], 1, "장기채는 만기가 길어 금리 변화에 더 민감하다. 즉 듀레이션이 더 길다."),
        ),
        Scenario(
            year="1979년", title="폴커 쇼크",
            fed_news="폴 볼커 의장은 초고금리 정책으로 인플레이션을 강하게 잡으려 했다.",
            concept="급격한 금리 인상은 기존 저금리 장기채 가격을 크게 떨어뜨린다.",
            event_icon="✦", choices=["채권 매도 후 현금 보유", "초장기 국채 매수"], results=[0.00, -0.40],
            result_texts=["현금을 보유하며 금리 충격을 피했다.", "장기채가 금리 급등을 정면으로 맞아 큰 손실이 났다."],
            choice_icons=["■", "◉"], difficulty=2,
            easy_bond_explanation="새로운 채권 금리가 아주 높아지면, 예전에 낮은 이자를 약속한 채권은 매력이 떨어진다. 그래서 가격이 내려간다.",
            beginner_tip="금리가 급격히 오르는 장면에서는 좋은 채권인가보다 금리 충격을 얼마나 세게 맞는가가 중요하다.", keyword="금리 인상",
            teacher_commentary="볼커 쇼크는 인플레이션 기대를 꺾기 위한 극단적 긴축이었고, 기존 장기채는 재평가를 피할 수 없었다.",
            discussion_prompt="금리가 급등할 때 현금 보유가 왜 하나의 전략이 될 수 있을까?",
            event_palette="rose", choice_palettes=["slate", "rose"],
            portfolio_shift=[{"cash":0.18,"gov_bonds":-0.10,"long_bonds":-0.12,"duration":-0.18},{"long_bonds":0.22,"gov_bonds":0.08,"duration":0.25,"cash":-0.12}],
            mini_quiz=MiniQuiz("기존 저금리 장기채 가격이 크게 하락하는 가장 직접적인 이유는?", ["새로 발행되는 채권 금리가 더 매력적이어서", "국채는 항상 위험해서", "현금이 사라져서"], 0, "새 채권 금리가 더 높으면 기존 저금리 채권은 가격을 낮춰야 경쟁력이 생긴다."),
        ),
        Scenario(
            year="1987년", title="블랙 먼데이",
            fed_news="주식시장이 하루 만에 폭락했고, 연준은 유동성 공급과 완화적 대응 의지를 보였다.",
            concept="위기 상황에서 연준의 완화 기대는 장기채 가격 상승으로 이어질 수 있다.",
            event_icon="✺", choices=["현금 관망", "장기 국채 매수"], results=[0.00, 0.18],
            result_texts=["자산은 지켰지만 큰 기회는 얻지 못했다.", "완화 기대를 앞서 읽고 장기 국채 상승을 잡았다."],
            choice_icons=["▤", "⬢"], difficulty=2,
            easy_bond_explanation="위기가 오면 중앙은행이 금리를 낮출 것이라는 기대가 생긴다. 그러면 기존 채권 가격이 먼저 오르기 시작할 수 있다.",
            beginner_tip="중앙은행이 시장을 살릴 것 같으면 채권은 먼저 반응할 수 있다.", keyword="금리 인하",
            teacher_commentary="시장 붕괴는 즉시 완화 기대를 키웠고, 장기금리 하락 기대가 장기채 가격을 밀어 올렸다.",
            discussion_prompt="왜 주식시장 폭락이 채권시장 상승 재료가 될 수 있을까?",
            event_palette="slate", choice_palettes=["slate", "blue"],
            portfolio_shift=[{"cash":0.14,"gov_bonds":-0.04,"duration":-0.02},{"long_bonds":0.18,"gov_bonds":0.12,"duration":0.18,"cash":-0.12}],
            mini_quiz=MiniQuiz("위기 때 장기 국채가 강해질 수 있는 이유로 가장 알맞은 것은?", ["중앙은행의 완화 기대가 생기기 때문", "장기 국채는 만기가 짧기 때문", "물가가 항상 오르기 때문"], 0, "위기 상황에서는 금리 인하와 안전자산 선호가 동시에 장기 국채를 밀어 줄 수 있다."),
        ),
        Scenario(
            year="1994년", title="채권 대학살",
            fed_news="시장 예상보다 강한 금리 인상으로 채권시장이 급락했다.",
            concept="기습적 금리 인상기에는 고정금리 장기채보다 변동금리 자산이 유리할 수 있다.",
            event_icon="✹", choices=["변동금리부 채권(FRN) 매수", "고정금리 장기채 매수"], results=[0.05, -0.25],
            result_texts=["금리가 올라갈수록 이자도 조정되는 자산이 방어에 유리했다.", "고정금리 장기채는 금리 상승 충격을 크게 받았다."],
            choice_icons=["◫", "▥"], difficulty=2,
            easy_bond_explanation="변동금리채는 시장 금리가 오르면 받는 이자도 어느 정도 따라 올라간다. 그래서 금리 상승기에 상대적으로 덜 아플 수 있다.",
            beginner_tip="금리가 오를 때 고정금리 장기채는 특히 취약하다.", keyword="금리 인상",
            teacher_commentary="서프라이즈 긴축은 듀레이션이 긴 자산일수록 불리하고, 플로팅 구조가 상대적으로 방어력을 보였다.",
            discussion_prompt="변동금리채는 왜 금리 상승기에 방어력이 높을까?",
            event_palette="teal", choice_palettes=["teal", "gold"],
            portfolio_shift=[{"credit":0.06,"short_bonds":0.08,"duration":-0.10,"cash":-0.04},{"long_bonds":0.18,"duration":0.20,"cash":-0.06}],
            mini_quiz=MiniQuiz("변동금리부 채권이 금리 상승기에 상대적으로 유리한 이유는?", ["이자 지급이 시장 금리에 맞춰 조정되기 때문", "만기가 무조건 짧기 때문", "가격이 절대 떨어지지 않기 때문"], 0, "변동금리 구조는 금리 상승의 일부를 쿠폰 조정으로 흡수할 수 있다."),
        ),
        Scenario(
            year="1998년", title="러시아 위기와 LTCM",
            fed_news="신흥국 금융 불안과 헤지펀드 위기가 겹치며 시장은 극도로 불안정해졌다.",
            concept="위기 국면에서는 안전자산 선호가 강해져 국채가 상대적으로 강할 수 있다.",
            event_icon="✪", choices=["미 국채 매수", "신흥국 고수익 채권 매수"], results=[0.12, -0.60],
            result_texts=["불안한 시기에는 국채로 자금이 몰리며 가격이 상승했다.", "위기 상황에서 위험한 채권을 고른 탓에 손실이 매우 컸다."],
            choice_icons=["⬒", "▲"], difficulty=2,
            easy_bond_explanation="시장이 겁에 질리면 사람들은 이자를 많이 주는 채권보다 원금을 지킬 가능성이 높은 채권을 더 선호한다.",
            beginner_tip="불안할수록 수익률보다 생존이 우선이다.", keyword="안전자산 선호",
            teacher_commentary="유동성 위기에서는 하이일드와 신흥국채가 가장 먼저 압박받고, 미국 국채가 피난처 역할을 한다.",
            discussion_prompt="왜 위기 때 높은 금리를 주는 자산이 오히려 더 위험해질까?",
            event_palette="blue", choice_palettes=["blue", "rose"],
            portfolio_shift=[{"gov_bonds":0.18,"cash":-0.06,"credit":-0.12,"duration":0.05},{"credit":0.22,"cash":-0.10,"gov_bonds":-0.14}],
            mini_quiz=MiniQuiz("안전자산 선호가 강해질 때 가장 먼저 자금이 몰리기 쉬운 곳은?", ["비우량 회사채", "미 국채", "신흥국 고수익채"], 1, "위기 국면에서는 신용 위험이 낮고 유동성이 큰 국채가 선호되기 쉽다."),
        ),
        Scenario(
            year="2000년", title="닷컴 버블 붕괴",
            fed_news="IT 버블이 꺼지며 경기 둔화가 시작됐고, 연준은 금리 인하에 나섰다.",
            concept="경기 둔화와 금리 인하는 대체로 채권 가격 상승에 유리하다.",
            event_icon="✧", choices=["국채선물 매수(Long)", "국채선물 매도(Short)"], results=[0.30, -0.30],
            result_texts=["금리 인하 방향을 맞히며 큰 수익을 냈다.", "금리 하락 방향을 거슬러 큰 손실을 봤다."],
            choice_icons=["◩", "◪"], difficulty=3,
            easy_bond_explanation="금리가 내려가면 기존 채권 가격은 오르기 쉽다. 그 방향에 강하게 베팅한 것이 선물 매수다.",
            beginner_tip="경기 둔화 + 금리 인하는 채권시장에 대체로 우호적이다.", keyword="금리 인하",
            teacher_commentary="리세션 우려와 정책 완화가 겹치며 duration long 포지션의 성과가 크게 확대되는 장면이다.",
            discussion_prompt="왜 채권 선물 매수는 현물 채권보다 수익과 손실이 더 크게 나타날 수 있을까?",
            event_palette="teal", choice_palettes=["teal", "rose"],
            portfolio_shift=[{"long_bonds":0.18,"gov_bonds":0.10,"duration":0.20,"cash":-0.14},{"cash":0.06,"duration":-0.15,"gov_bonds":-0.04}],
            mini_quiz=MiniQuiz("연준이 금리를 인하하기 시작하면 일반적으로 기존 채권 가격은 어떻게 되는가?", ["하락한다", "상승한다", "무조건 변하지 않는다"], 1, "금리 인하는 기존 채권의 상대 매력을 높여 가격 상승 요인이 된다."),
        ),
        Scenario(
            year="2008년", title="글로벌 금융위기",
            fed_news="리먼 브라더스 파산 이후 제로금리와 양적완화가 시작됐다.",
            concept="중앙은행이 채권을 직접 사들이면 채권 가격 상승 압력이 커질 수 있다.",
            event_icon="✵", choices=["초우량 장기 국채 매수", "금리상승 베팅"], results=[0.25, -0.20],
            result_texts=["안전자산 선호와 QE가 동시에 국채를 밀어 올렸다.", "정책 흐름을 거스르는 베팅이 되어 손실을 봤다."],
            choice_icons=["⬣", "▽"], difficulty=2,
            easy_bond_explanation="중앙은행이 직접 채권을 사면 그만큼 채권 수요가 늘어난다. 수요가 늘면 보통 가격이 오른다.",
            beginner_tip="중앙은행이 직접 사준다는 말은 채권시장에 매우 강한 재료다.", keyword="QE",
            teacher_commentary="리세션, 안전자산 선호, 중앙은행 매입이라는 세 가지 호재가 duration long에 동시에 작동했다.",
            discussion_prompt="양적완화는 왜 채권 수익률을 낮추는 방향으로 작동할까?",
            event_palette="blue", choice_palettes=["mint", "rose"],
            portfolio_shift=[{"gov_bonds":0.14,"long_bonds":0.16,"duration":0.18,"cash":-0.12},{"cash":0.03,"duration":-0.10}],
            mini_quiz=MiniQuiz("양적완화(QE)의 직접적 설명으로 가장 알맞은 것은?", ["중앙은행이 채권을 매입하는 것", "중앙은행이 세금을 올리는 것", "기업이 회사채를 상환하는 것"], 0, "QE는 중앙은행이 시장에서 채권을 사들여 유동성을 공급하는 정책이다."),
        ),
        Scenario(
            year="2013년", title="테이퍼 탠트럼",
            fed_news="양적완화 축소 가능성 발언만으로도 시장 금리가 급등했다.",
            concept="연준은 실제 행동뿐 아니라 발언만으로도 장기금리를 움직인다.",
            event_icon="✶", choices=["단기채 중심 방어", "장기채 계속 홀딩"], results=[0.00, -0.10],
            result_texts=["짧은 만기로 버티며 충격을 줄였다.", "장기채는 발언 충격으로 가격이 하락했다."],
            choice_icons=["◧", "◨"], difficulty=2,
            easy_bond_explanation="중앙은행이 앞으로 돈을 덜 풀 것 같다는 신호만 줘도, 시장은 미리 긴축을 반영해 장기채를 팔 수 있다.",
            beginner_tip="채권시장은 실제 결정 전에도 먼저 움직인다.", keyword="듀레이션",
            teacher_commentary="장기채는 미래 정책 경로에 민감해, 코멘트만으로도 실질 가격 조정이 크게 발생한다.",
            discussion_prompt="왜 실제 금리 인상이 없었는데도 장기채가 먼저 흔들렸을까?",
            event_palette="gold", choice_palettes=["slate", "gold"],
            portfolio_shift=[{"short_bonds":0.14,"duration":-0.12,"cash":-0.04},{"long_bonds":0.15,"duration":0.16,"cash":-0.05}],
            mini_quiz=MiniQuiz("테이퍼 탠트럼에서 장기채가 크게 흔들린 핵심 이유는?", ["중앙은행 발언이 미래 긴축 기대를 자극해서", "국채가 회사채보다 위험해서", "현금 금리가 0이어서"], 0, "정책 기대 변화만으로도 장기금리는 크게 반응할 수 있다."),
        ),
        Scenario(
            year="2015년", title="제로금리 시대 종료",
            fed_news="7년 만에 기준금리 인상이 시작됐다.",
            concept="금리 인상 초기에는 듀레이션 관리가 성과 차이를 만든다.",
            event_icon="✷", choices=["바벨 전략", "불렛 전략"], results=[0.05, -0.05],
            result_texts=["유연한 구조가 변동성을 이겨냈다.", "중간 만기 중심 구조가 애매하게 흔들렸다."],
            choice_icons=["⧉", "◎"], difficulty=3,
            easy_bond_explanation="바벨 전략은 아주 짧은 것과 아주 긴 것을 섞는 방식이고, 불렛 전략은 중간 만기에 몰아두는 방식이다.",
            beginner_tip="채권 운용은 단순히 맞히기보다 어떻게 섞느냐도 중요하다.", keyword="듀레이션",
            teacher_commentary="정책 정상화 초반에는 포트폴리오 구성이 중요하며, 유연성을 가진 구조가 변동성에 유리했다.",
            discussion_prompt="왜 만기를 한 구간에 몰아두는 것보다 분산하는 전략이 유리할 수 있을까?",
            event_palette="teal", choice_palettes=["teal", "slate"],
            portfolio_shift=[{"short_bonds":0.10,"long_bonds":0.08,"duration":-0.04,"cash":-0.05},{"gov_bonds":0.10,"duration":0.05,"cash":-0.04}],
            mini_quiz=MiniQuiz("바벨 전략의 가장 가까운 설명은?", ["짧은 만기와 긴 만기를 함께 보유하는 전략", "중간 만기에만 집중하는 전략", "현금만 보유하는 전략"], 0, "바벨 전략은 양 끝단 만기를 함께 가져가며 유연성을 확보한다."),
        ),
        Scenario(
            year="2019년", title="장단기 금리차 역전",
            fed_news="단기금리가 장기금리보다 높아지는 현상이 나타나며 경기 둔화 우려가 커졌다.",
            concept="금리 역전은 이후 경기 둔화와 금리 인하 기대를 반영하는 경우가 많다.",
            event_icon="✴", choices=["장기채 매수", "회사채 매수"], results=[0.15, -0.10],
            result_texts=["침체 가능성을 읽고 장기채 강세를 잡았다.", "회사채는 경기 우려와 신용불안에 더 취약했다."],
            choice_icons=["⬡", "▣"], difficulty=2,
            easy_bond_explanation="경기가 나빠질 것 같으면 나중에 금리가 내려갈 가능성이 커진다. 그러면 장기채 가격이 올라갈 수 있다.",
            beginner_tip="금리 역전은 지금보다 나중이 더 안 좋을 수 있다는 시장의 신호다.", keyword="금리 인하",
            teacher_commentary="커브 역전은 향후 성장 둔화와 정책 완화 기대를 반영하기 때문에 장기채 선호가 강해질 수 있다.",
            discussion_prompt="왜 경기 침체 신호가 나오면 회사채보다 장기 국채가 더 매력적일 수 있을까?",
            event_palette="blue", choice_palettes=["blue", "rose"],
            portfolio_shift=[{"long_bonds":0.16,"gov_bonds":0.10,"duration":0.16,"cash":-0.10},{"credit":0.16,"cash":-0.06,"gov_bonds":-0.08}],
            mini_quiz=MiniQuiz("장단기 금리차 역전이 자주 의미하는 것은?", ["향후 경기 둔화 가능성", "물가가 무조건 0이 됨", "회사채가 항상 상승"], 0, "금리 역전은 경기 둔화와 이후 금리 인하 기대를 반영하는 경우가 많다."),
        ),
        Scenario(
            year="2020년", title="코로나19 팬데믹",
            fed_news="제로금리와 무제한 QE, 그리고 회사채 시장 안정 조치가 동시에 발표됐다.",
            concept="중앙은행이 신용시장까지 지지하면 우량 회사채도 강하게 반등할 수 있다.",
            event_icon="✹", choices=["우량 회사채 매수", "현금 관망"], results=[0.20, 0.00],
            result_texts=["정책 백스톱을 믿고 위험 프리미엄 축소를 잡아냈다.", "안전했지만 큰 회복 구간은 놓쳤다."],
            choice_icons=["◫", "■"], difficulty=2,
            easy_bond_explanation="원래 회사채는 불안할 때 더 크게 흔들리는데, 중앙은행이 받쳐주겠다고 하면 다시 빠르게 회복할 수 있다.",
            beginner_tip="국채만 안전한 것이 아니다. 정책이 받쳐주면 우량 회사채도 급반등할 수 있다.", keyword="QE",
            teacher_commentary="정책 백스톱은 신용스프레드 축소를 유도하며, 우량 회사채에 빠른 리레이팅을 만들어냈다.",
            discussion_prompt="왜 같은 위기 상황에서도 정책 개입 유무에 따라 회사채 성과가 달라질까?",
            event_palette="mint", choice_palettes=["teal", "slate"],
            portfolio_shift=[{"credit":0.18,"cash":-0.06,"gov_bonds":-0.04},{"cash":0.12,"credit":-0.04}],
            mini_quiz=MiniQuiz("중앙은행이 회사채 시장까지 지지하면 기대할 수 있는 변화는?", ["우량 회사채의 위험 프리미엄 축소", "국채 발행 즉시 중단", "회사채 금리의 영구 고정"], 0, "정책 개입은 회사채 시장의 공포를 줄여 스프레드를 축소시킬 수 있다."),
        ),
        Scenario(
            year="2022년", title="인플레이션의 귀환",
            fed_news="파월은 매우 가파른 금리 인상으로 인플레이션을 잡으려 했다.",
            concept="급격한 금리 상승기에는 대부분의 장기채가 매우 불리하다.",
            event_icon="✸", choices=["국채선물 매도(Short)+현금", "장기채 매수"], results=[0.15, -0.30],
            result_texts=["금리 급등 방향을 맞히며 방어와 수익을 동시에 챙겼다.", "장기채가 급락하며 포트폴리오가 크게 훼손됐다."],
            choice_icons=["▽", "▭"], difficulty=3,
            easy_bond_explanation="금리가 너무 빨리 오르면 예전에 발행된 채권은 매력이 급격히 떨어진다. 장기채는 그 충격이 특히 크다.",
            beginner_tip="고금리 충격기에는 좋은 채권도 가격이 크게 떨어질 수 있다.", keyword="인플레이션",
            teacher_commentary="물가 쇼크 국면에서는 실질금리 재평가와 정책금리 급등이 동시에 장기채에 부담을 준다.",
            discussion_prompt="왜 높은 인플레이션은 채권 보유자에게 특히 불리할까?",
            event_palette="rose", choice_palettes=["slate", "rose"],
            portfolio_shift=[{"cash":0.12,"duration":-0.18,"gov_bonds":-0.06},{"long_bonds":0.20,"duration":0.24,"cash":-0.08,"inflation":-0.10}],
            mini_quiz=MiniQuiz("인플레이션 급등기에 일반 장기채가 약세를 보이기 쉬운 이유는?", ["미래 고정 이자의 실질 가치가 깎이고 금리도 오르기 때문", "장기채는 이자가 없기 때문", "국채가 자동 상환되기 때문"], 0, "인플레이션은 고정 이자의 실질 가치를 낮추고, 금리 인상을 자극해 채권 가격에 이중 부담을 준다."),
        ),
        Scenario(
            year="2023년", title="SVB 쇼크",
            fed_news="은행권 불안이 커지며 시장은 긴축 지속보다 금융 안정 문제를 더 크게 보기 시작했다.",
            concept="금융 시스템 불안은 갑작스러운 채권 강세를 만들 수 있다.",
            event_icon="✺", choices=["중장기 국채 매수", "회사채 확대"], results=[0.14, -0.08],
            result_texts=["안전자산 선호와 금리 기대 변화가 국채를 밀어 올렸다.", "신용불안 국면에서 회사채 확대로 손실이 났다."],
            choice_icons=["⬢", "▲"], difficulty=2,
            easy_bond_explanation="은행이 흔들리면 시장은 연준이 더 세게 긴축하기 어려울 수도 있다고 생각해 채권을 사기 시작할 수 있다.",
            beginner_tip="채권시장은 물가만 보는 것이 아니라 금융 시스템 안정도 본다.", keyword="안전자산 선호",
            teacher_commentary="금융 시스템 리스크는 정책 경로를 재해석하게 만들고, 국채에는 피난 수요가 집중된다.",
            discussion_prompt="왜 금융 시스템 불안은 오히려 국채 강세의 재료가 되기도 할까?",
            event_palette="blue", choice_palettes=["blue", "rose"],
            portfolio_shift=[{"gov_bonds":0.16,"long_bonds":0.08,"credit":-0.10,"cash":-0.08},{"credit":0.15,"cash":-0.05,"gov_bonds":-0.07}],
            mini_quiz=MiniQuiz("은행 시스템 불안이 커질 때 상대적으로 선호되기 쉬운 것은?", ["안전자산인 국채", "고수익 저신용 회사채", "레버리지 올인 포지션"], 0, "금융 시스템 불안은 안전자산 선호를 강화하기 쉽다."),
        ),
        Scenario(
            year="2024년", title="피벗 기대와 되돌림",
            fed_news="시장에서는 금리 인하 기대가 컸지만, 물가와 고용 데이터가 엇갈리며 장기채 변동성이 이어졌다.",
            concept="기대만 믿고 장기채에 올인하면 안 되며, 실제 데이터와 포지션 조절이 중요하다.",
            event_icon="✧", choices=["분할 매수 + 듀레이션 관리", "장기채 올인"], results=[0.08, -0.12],
            result_texts=["유연한 분할 대응이 변동성 장세를 버텼다.", "기대만 믿고 올인했다가 되돌림에 크게 흔들렸다."],
            choice_icons=["⧉", "◎"], difficulty=3,
            easy_bond_explanation="시장은 기대만으로 움직이기도 하지만, 결국 실제 숫자와 정책이 확인되면 다시 방향을 바꿀 수 있다.",
            beginner_tip="채권은 맞히기보다 버틸 수 있게 들어가기가 더 중요할 때가 많다.", keyword="듀레이션",
            teacher_commentary="데이터 의존적 국면에서는 확신보다 포지션 사이징과 평균단가 관리가 성과를 좌우한다.",
            discussion_prompt="왜 확실해 보이는 장면에서도 분할 매수가 유효한 전략이 될 수 있을까?",
            event_palette="teal", choice_palettes=["teal", "gold"],
            portfolio_shift=[{"short_bonds":0.08,"long_bonds":0.08,"cash":-0.06,"duration":0.02},{"long_bonds":0.20,"duration":0.24,"cash":-0.10}],
            mini_quiz=MiniQuiz("데이터가 엇갈리는 장세에서 상대적으로 바람직한 접근은?", ["분할 매수와 포지션 관리", "한 번에 전액 올인", "근거 없이 손절 회피"], 0, "불확실한 장세에서는 사이즈 조절과 분할 접근이 생존 확률을 높인다."),
        ),
        Scenario(
            year="최종장", title="연준의 수수께끼 회견",
            fed_news="연준 의장은 물가도 중요하고 금융안정도 중요하다는 모호한 메시지를 남겼다.",
            concept="현실 시장에서는 확실한 정답보다 포지션 크기와 생존 능력이 더 중요할 때가 있다.",
            event_icon="✪", choices=["보수적 분산 포지션", "레버리지 올인"], results=[0.10, -0.20],
            result_texts=["불확실성 구간에서 생존 중심 전략이 통했다.", "방향성 올인이 큰 대가를 치렀다."],
            choice_icons=["◧", "◉"], difficulty=3,
            easy_bond_explanation="시장이 헷갈릴 때는 크게 맞히는 것보다 크게 틀리지 않는 것이 더 중요하다.",
            beginner_tip="최고의 트레이더는 늘 공격적인 사람이 아니라 오래 살아남는 사람이다.", keyword="듀레이션",
            teacher_commentary="모호한 가이던스 구간에서는 방향성 확신보다 리스크 예산과 분산이 우위를 만든다.",
            discussion_prompt="시장이 불확실할 때 분산과 사이징이 정답 그 자체보다 중요한 이유는 무엇일까?",
            event_palette="slate", choice_palettes=["mint", "rose"],
            portfolio_shift=[{"cash":0.08,"gov_bonds":0.06,"credit":-0.04,"duration":-0.02},{"cash":-0.12,"duration":0.20,"credit":0.06}],
            mini_quiz=MiniQuiz("불확실한 시장에서 가장 중요한 원칙에 가까운 것은?", ["한 번에 크게 맞히기", "생존 가능한 크기로 포지션 잡기", "손실 무시하기"], 1, "현실 시장에서는 장기적으로 살아남을 수 있는 포지션 크기가 가장 중요할 때가 많다."),
        ),
    ]


def init_game_state():
    if "bond_game_initialized" in st.session_state:
        return
    scenarios = load_scenarios()
    st.session_state.bond_game_initialized = True
    st.session_state.started = False
    st.session_state.finished = False
    st.session_state.mode = "학생용"
    st.session_state.initial_balance = 10000.0
    st.session_state.balance = 10000.0
    st.session_state.survival_limit = 6000.0
    st.session_state.turn_index = 0
    st.session_state.correct_count = 0
    st.session_state.streak = 0
    st.session_state.best_streak = 0
    st.session_state.hint_tokens = 3
    st.session_state.shield_tokens = 1
    st.session_state.difficulty_mode = "보통"
    st.session_state.random_noise = False
    st.session_state.noise_range = 0.02
    st.session_state.scenarios = [asdict(s) for s in scenarios]
    st.session_state.logs = []
    st.session_state.last_result = None
    st.session_state.last_hint = None
    st.session_state.quiz_state = {"active": False, "answered": False, "selected": None, "correct": None}
    st.session_state.portfolio = normalize_portfolio({
        "cash": 0.28,
        "gov_bonds": 0.24,
        "credit": 0.18,
        "short_bonds": 0.14,
        "long_bonds": 0.16,
    })
    st.session_state.metrics = {
        "duration": 0.50,
        "credit_risk": 0.48,
        "inflation_sensitivity": 0.44,
        "liquidity": 0.64,
    }
    st.session_state.portfolio_history = [{
        "turn": 0,
        "balance": st.session_state.balance,
        "cash": st.session_state.portfolio["cash"],
        "gov_bonds": st.session_state.portfolio["gov_bonds"],
        "credit": st.session_state.portfolio["credit"],
        "short_bonds": st.session_state.portfolio["short_bonds"],
        "long_bonds": st.session_state.portfolio["long_bonds"],
        "duration": st.session_state.metrics["duration"],
        "credit_risk": st.session_state.metrics["credit_risk"],
        "inflation_sensitivity": st.session_state.metrics["inflation_sensitivity"],
        "liquidity": st.session_state.metrics["liquidity"],
    }]


init_game_state()


def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_game_state()


def apply_return(base_return: float) -> Tuple[float, bool]:
    actual_return = base_return
    if st.session_state.random_noise:
        actual_return += random.uniform(-st.session_state.noise_range, st.session_state.noise_range)
    if st.session_state.streak >= 2 and actual_return > 0:
        bonus = min(0.03, 0.01 * (st.session_state.streak - 1))
        actual_return += bonus
    if st.session_state.difficulty_mode == "어려움" and actual_return < 0:
        actual_return *= 1.05
    shield_used = False
    if actual_return < -0.20 and st.session_state.shield_tokens > 0:
        st.session_state.shield_tokens -= 1
        actual_return *= 0.5
        shield_used = True
    st.session_state.balance *= (1 + actual_return)
    st.session_state.balance = max(0.0, st.session_state.balance)
    return actual_return, shield_used


def update_portfolio(choice_shift: Dict[str, float], actual_return: float):
    portfolio = st.session_state.portfolio.copy()
    metrics = st.session_state.metrics.copy()
    metric_map = {"duration": "duration", "credit": "credit_risk", "inflation": "inflation_sensitivity", "liquidity": "liquidity"}
    for key, delta in choice_shift.items():
        if key in portfolio:
            portfolio[key] = max(0.02, portfolio[key] + delta)
        elif key in metric_map:
            metrics[metric_map[key]] = bounded_add(metrics[metric_map[key]], delta)
    if actual_return > 0:
        metrics["liquidity"] = bounded_add(metrics["liquidity"], 0.01)
    else:
        metrics["liquidity"] = bounded_add(metrics["liquidity"], -0.02)
    st.session_state.portfolio = normalize_portfolio(portfolio)
    st.session_state.metrics = metrics
    st.session_state.portfolio_history.append({
        "turn": st.session_state.turn_index + 1,
        "balance": st.session_state.balance,
        **st.session_state.portfolio,
        **metrics,
    })


def use_hint(scenario: dict) -> str:
    if st.session_state.hint_tokens <= 0:
        return "힌트 토큰이 없다."
    st.session_state.hint_tokens -= 1
    best_idx = max(range(len(scenario["results"])), key=lambda i: scenario["results"][i])
    weak_idx = min(range(len(scenario["results"])), key=lambda i: scenario["results"][i])
    hint_pool = [
        f"핵심 개념을 다시 보자: {scenario['concept']}",
        f"초보자 팁: {scenario['beginner_tip']}",
        f"상대적으로 위험한 선택은 '{scenario['choices'][weak_idx]}' 쪽이다.",
        f"이번 장면의 키워드는 '{scenario['keyword']}'이다.",
        f"상대적으로 유리한 방향은 '{scenario['choices'][best_idx]}'에 가깝다.",
    ]
    hint = random.choice(hint_pool)
    st.session_state.last_hint = hint
    return hint


def submit_choice(choice_idx: int):
    scenario = st.session_state.scenarios[st.session_state.turn_index]
    optimal_idx = max(range(len(scenario["results"])), key=lambda i: scenario["results"][i])
    is_correct = choice_idx == optimal_idx
    actual_return, shield_used = apply_return(scenario["results"][choice_idx])
    update_portfolio(scenario["portfolio_shift"][choice_idx], actual_return)
    if is_correct:
        st.session_state.correct_count += 1
        st.session_state.streak += 1
        st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
    else:
        st.session_state.streak = 0
    st.session_state.logs.append({
        "turn": st.session_state.turn_index + 1,
        "year": scenario["year"],
        "title": scenario["title"],
        "choice": scenario["choices"][choice_idx],
        "actual_return": actual_return,
        "balance": st.session_state.balance,
        "is_correct": is_correct,
        "keyword": scenario["keyword"],
        "quiz_bonus": 0,
    })
    st.session_state.last_result = {
        "scenario": scenario,
        "choice_idx": choice_idx,
        "optimal_idx": optimal_idx,
        "is_correct": is_correct,
        "actual_return": actual_return,
        "shield_used": shield_used,
    }
    st.session_state.quiz_state = {"active": is_correct, "answered": False, "selected": None, "correct": None}
    if st.session_state.balance <= st.session_state.survival_limit:
        st.session_state.finished = True
        st.session_state.quiz_state["active"] = False


def submit_quiz_answer(selected_idx: int):
    if not st.session_state.last_result:
        return
    scenario = st.session_state.last_result["scenario"]
    quiz = scenario["mini_quiz"]
    correct = selected_idx == quiz["answer_idx"]
    st.session_state.quiz_state.update({"answered": True, "selected": selected_idx, "correct": correct})
    if correct:
        bonus = 150.0
        st.session_state.balance += bonus
        st.session_state.hint_tokens += 1
        if st.session_state.logs:
            st.session_state.logs[-1]["quiz_bonus"] = bonus
            st.session_state.logs[-1]["balance"] = st.session_state.balance
        if st.session_state.portfolio_history:
            st.session_state.portfolio_history[-1]["balance"] = st.session_state.balance


def advance_turn():
    st.session_state.last_result = None
    st.session_state.quiz_state = {"active": False, "answered": False, "selected": None, "correct": None}
    st.session_state.last_hint = None
    st.session_state.turn_index += 1
    if st.session_state.turn_index >= len(st.session_state.scenarios):
        st.session_state.finished = True


def build_pdf_report() -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#17213b"), alignment=TA_LEFT, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=colors.HexColor("#1c2b52"), spaceBefore=8, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#334155"))

    story = []
    story.append(Paragraph("Bond History Game 학습 리포트", title_style))
    ending = get_ending(st.session_state.balance, st.session_state.initial_balance)
    summary_text = (
        f"최종 자산: {money_to_str(st.session_state.balance)}<br/>"
        f"총 수익률: {pct_to_str(safe_ratio(st.session_state.balance, st.session_state.initial_balance) - 1)}<br/>"
        f"최종 엔딩: {ending['grade']} - {ending['title']}<br/>"
        f"정답 수: {st.session_state.correct_count}/{len(st.session_state.scenarios)}<br/>"
        f"최고 연속 정답: {st.session_state.best_streak}"
    )
    story.append(Paragraph(summary_text, body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. 성과 요약", h2))
    perf_table = Table([
        ["항목", "값"],
        ["현재 커리어 배지", get_badge(st.session_state.balance, st.session_state.initial_balance)],
        ["난이도", st.session_state.difficulty_mode],
        ["남은 힌트 토큰", str(st.session_state.hint_tokens)],
        ["남은 실드 토큰", str(st.session_state.shield_tokens)],
    ], colWidths=[48*mm, 112*mm])
    perf_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eef3ff")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#1f335d")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d7e3ff")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fbfdff")]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. 모의 포트폴리오 최종 상태", h2))
    p = st.session_state.portfolio
    m = st.session_state.metrics
    port_table = Table([
        ["구성", "비중"],
        ["현금", f"{p['cash']*100:.1f}%"],
        ["국채", f"{p['gov_bonds']*100:.1f}%"],
        ["회사채", f"{p['credit']*100:.1f}%"],
        ["단기채", f"{p['short_bonds']*100:.1f}%"],
        ["장기채", f"{p['long_bonds']*100:.1f}%"],
        ["듀레이션 민감도", f"{m['duration']*100:.0f}/100"],
        ["신용위험", f"{m['credit_risk']*100:.0f}/100"],
        ["인플레이션 취약도", f"{m['inflation_sensitivity']*100:.0f}/100"],
        ["유동성", f"{m['liquidity']*100:.0f}/100"],
    ], colWidths=[60*mm, 100*mm])
    port_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eefcf4")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#22543d")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d3e9db")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fbfffd")]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(port_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. 턴별 학습 로그", h2))
    rows = [["턴", "시기", "선택", "수익률", "퀴즈 보너스", "잔고"]]
    for log in st.session_state.logs:
        rows.append([
            str(log["turn"]),
            f"{log['year']} {log['title']}",
            log["choice"],
            pct_to_str(log["actual_return"]),
            f"{log.get('quiz_bonus', 0):,.0f}",
            money_to_str(log["balance"]),
        ])
    log_table = Table(rows, colWidths=[12*mm, 40*mm, 55*mm, 22*mm, 26*mm, 30*mm], repeatRows=1)
    log_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#fff7eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#7a4d00")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#e8d8b2")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fffcf6")]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(log_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("4. 학습 정리", h2))
    lessons = [
        "금리가 오르면 기존 채권 가격은 대체로 내려간다.",
        "금리가 내리면 기존 채권 가격은 대체로 올라간다.",
        "위기 때는 국채 같은 안전자산 선호가 강화되기 쉽다.",
        "인플레이션 급등기는 일반 장기채에 특히 불리할 수 있다.",
        "불확실한 장세에서는 정답보다 포지션 사이즈와 생존이 중요할 때가 많다.",
    ]
    for idx, lesson in enumerate(lessons, start=1):
        story.append(Paragraph(f"{idx}. {lesson}", body))
        story.append(Spacer(1, 3))

    doc.build(story)
    return buffer.getvalue()


def render_svg(src: str):
    st.markdown(f'<img class="card-art" src="{src}" />', unsafe_allow_html=True)

def get_base64_image(image_path: str) -> str:
    import os
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as f:
        data = f.read()
    return "data:image/png;base64," + base64.b64encode(data).decode("utf-8")


def render_header():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">Bond History Premium Game</div>
            <div class="hero-sub">연준의 역사적 결정 속에서 살아남아라. 채권을 어렵게 외우는 대신, 직접 선택하고 틀려보며 이해하는 카드형 웹게임.</div>
            <div>
                <span class="chip">실제 카드 일러스트</span>
                <span class="chip">학생용 / 교사용 모드</span>
                <span class="chip">모의 포트폴리오</span>
                <span class="chip">미니 퀴즈</span>
                <span class="chip">PDF 학습 리포트</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_setup():
    st.markdown("### 게임 설정")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        difficulty = st.selectbox("난이도", ["쉬움", "보통", "어려움"], index=1)
    with c2:
        noise = st.toggle("시장 랜덤 노이즈", value=False)
    with c3:
        shield = st.selectbox("초기 실드 수", [1, 2], index=0)
    with c4:
        mode = st.selectbox("표시 모드", ["학생용", "교사용"], index=0)
    st.markdown(
        """
        <div class="learn-box">
            <div class="section-title">처음 하는 사람을 위한 설명</div>
            <div>
                이 게임의 기본 원리는 단순하다.<br><br>
                <b>금리 오름 → 기존 채권 가격 내림</b><br>
                <b>금리 내림 → 기존 채권 가격 오름</b><br><br>
                시장이 무서울수록 보통 <b>국채 같은 안전한 채권</b>이 강해지고,
                물가가 너무 오르면 <b>일반 장기채</b>는 불리해지기 쉽다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("게임 시작", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.session_state.mode = mode
        st.session_state.difficulty_mode = difficulty
        st.session_state.random_noise = noise
        st.session_state.shield_tokens = shield
        if difficulty == "쉬움":
            st.session_state.hint_tokens = 4
            st.session_state.noise_range = 0.0
        elif difficulty == "보통":
            st.session_state.hint_tokens = 3
            st.session_state.noise_range = 0.02
        else:
            st.session_state.hint_tokens = 2
            st.session_state.noise_range = 0.03
            st.session_state.random_noise = True


def render_sidebar():
    with st.sidebar:
        st.markdown("## 게임 설정")
        mode = st.radio("모드", ["학생용", "교사용"], index=0 if st.session_state.mode == "학생용" else 1)
        st.session_state.mode = mode
        st.markdown("---")
        st.markdown("## 쉬운 채권 설명")
        st.write("1. 금리 오름 → 기존 채권 가격 내림  ")
        st.write("2. 금리 내림 → 기존 채권 가격 오름  ")
        st.write("3. 위기 때는 국채가 강해질 수 있음  ")
        st.write("4. 물가 급등 때는 일반 장기채가 불리함")
        st.markdown("---")
        st.markdown("## 용어사전")
        for term, desc in TERM_DICTIONARY:
            st.markdown(f'<div class="term-box"><b>{term}</b><br><span class="small-note">{desc}</span></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.write(f"현재 난이도: **{st.session_state.difficulty_mode}**")
        st.write(f"시장 노이즈: **{'ON' if st.session_state.random_noise else 'OFF'}**")
        if st.button("전체 리셋", use_container_width=True):
            reset_game()
            st.rerun()


def render_dashboard():
    balance = st.session_state.balance
    initial_balance = st.session_state.initial_balance
    survival_limit = st.session_state.survival_limit
    total_return = safe_ratio(balance, initial_balance) - 1
    progress = st.session_state.turn_index / len(st.session_state.scenarios) if st.session_state.scenarios else 0
    status_label, status_desc = get_survival_status(balance, survival_limit, initial_balance)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi"><div class="kpi-label">현재 자산</div><div class="kpi-value">{money_to_str(balance)}</div><div class="kpi-sub">생존선: {money_to_str(survival_limit)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi"><div class="kpi-label">누적 수익률</div><div class="kpi-value">{pct_to_str(total_return)}</div><div class="kpi-sub">정답 수 {st.session_state.correct_count}회</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi"><div class="kpi-label">현재 커리어 트랙</div><div class="kpi-value" style="font-size:1.22rem;">{get_badge(balance, initial_balance)}</div><div class="kpi-sub">{status_label} · {status_desc}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi"><div class="kpi-label">턴 / 전체</div><div class="kpi-value">{min(st.session_state.turn_index + 1, len(st.session_state.scenarios))}/{len(st.session_state.scenarios)}</div><div class="kpi-sub">연속 정답 {st.session_state.streak} · 최고 {st.session_state.best_streak}</div></div>', unsafe_allow_html=True)
    st.progress(progress, text="게임 진행도")
    c5, c6, c7 = st.columns([1, 1, 2])
    with c5:
        st.metric("힌트 토큰", st.session_state.hint_tokens)
    with c6:
        st.metric("실드 토큰", st.session_state.shield_tokens)
    with c7:
        health = max(0.0, min(1.0, (balance - survival_limit) / (initial_balance * 1.4)))
        st.progress(health, text="포트폴리오 안정성")


def render_portfolio_screen():
    p = st.session_state.portfolio
    m = st.session_state.metrics
    hist = st.session_state.portfolio_history
    st.markdown("### 모의 포트폴리오 화면")
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="portfolio-card"><div class="portfolio-title">현재 자산 배분</div></div>', unsafe_allow_html=True)
        for key, label in [("cash", "현금"), ("gov_bonds", "국채"), ("credit", "회사채"), ("short_bonds", "단기채"), ("long_bonds", "장기채")]:
            st.progress(float(p[key]), text=f"{label} {p[key]*100:.1f}%")
    with right:
        st.markdown('<div class="portfolio-card"><div class="portfolio-title">리스크 프로필</div></div>', unsafe_allow_html=True)
        st.progress(float(m["duration"]), text=f"듀레이션 민감도 {m['duration']*100:.0f}/100")
        st.progress(float(m["credit_risk"]), text=f"신용위험 {m['credit_risk']*100:.0f}/100")
        st.progress(float(m["inflation_sensitivity"]), text=f"인플레이션 취약도 {m['inflation_sensitivity']*100:.0f}/100")
        st.progress(float(m["liquidity"]), text=f"유동성 {m['liquidity']*100:.0f}/100")
    if hist:
        last = hist[-1]
        prev = hist[-2] if len(hist) >= 2 else hist[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("최근 턴 자산 변화", money_to_str(last["balance"]), delta=money_to_str(last["balance"] - prev["balance"]))
        c2.metric("최근 듀레이션 변화", f"{last['duration']*100:.0f}/100", delta=f"{(last['duration']-prev['duration'])*100:+.0f}")
        c3.metric("최근 신용위험 변화", f"{last['credit_risk']*100:.0f}/100", delta=f"{(last['credit_risk']-prev['credit_risk'])*100:+.0f}")


def render_current_scenario():
    scenario = st.session_state.scenarios[st.session_state.turn_index]
    left, right = st.columns([1.25, 1])
    with left:
        chips = ''.join([f'<span class="chip">{scenario["year"]}</span>', f'<span class="chip">난이도 {"★"*scenario["difficulty"]}</span>', f'<span class="chip">키워드 {scenario["keyword"]}</span>'])
        
        image_idx = st.session_state.turn_index + 1
        image_path = f"assets/scene_{image_idx}.png"
        art = get_base64_image(image_path)
        if not art:
            art = make_banner_svg(scenario["title"], scenario["year"], scenario["event_palette"], scenario["event_icon"])
            
        st.markdown('<div class="event-card">', unsafe_allow_html=True)
        render_svg(art)
        st.markdown(f'{chips}<div class="event-title">{scenario["title"]}</div>', unsafe_allow_html=True)
        st.markdown('<hr class="soft-line"/>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">Fed 뉴스</div><div>{scenario["fed_news"]}</div>', unsafe_allow_html=True)
        st.markdown('<hr class="soft-line"/>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">핵심 개념</div><div>{scenario["concept"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="explain-box"><div class="section-title">이 장면을 쉬운 말로 풀면</div><div>{scenario["easy_bond_explanation"]}</div><div class="small-note" style="margin-top:8px;">초보자 팁: {scenario["beginner_tip"]}</div></div>', unsafe_allow_html=True)
        if st.session_state.mode == "교사용":
            st.markdown(f'<div class="learn-box"><div class="section-title">교사용 해설</div><div>{get_teacher_summary(scenario)}</div><div class="small-note" style="margin-top:8px;">토론 질문: {scenario["discussion_prompt"]}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("힌트 보기", use_container_width=True):
                st.info(use_hint(scenario))
        with c2:
            if st.button("키워드 설명", use_container_width=True):
                st.success(f"{scenario['keyword']}: {BEGINNER_EXPLAINERS.get(scenario['keyword'], scenario['concept'])}")
        if st.session_state.last_hint:
            st.caption(f"최근 힌트: {st.session_state.last_hint}")
    with right:
        st.markdown("### 투자 선택")
        for i, choice in enumerate(scenario["choices"]):
            choice_art = make_choice_svg(choice, f"선택지 {i+1}", scenario["choice_palettes"][i], scenario["choice_icons"][i])
            st.markdown('<div class="choice-card">', unsafe_allow_html=True)
            render_svg(choice_art)
            st.markdown(f'<div class="section-title" style="margin-top:10px;">선택지 {i+1}</div><div>{choice}</div></div>', unsafe_allow_html=True)
            if st.button(f"선택지 {i+1} 실행", key=f"choice_{st.session_state.turn_index}_{i}", use_container_width=True, type="primary" if i == 0 else "secondary"):
                submit_choice(i)
                st.rerun()
        st.markdown(
            '<div class="learn-box"><div class="section-title">판단 순서 추천</div><div>① 지금 시장은 <b>물가 걱정</b>이 큰가, <b>경기 침체</b>가 큰가?<br>② 중앙은행은 앞으로 <b>금리를 올릴 것 같은가</b>, <b>내릴 것 같은가</b>?<br>③ 불안할수록 <b>안전자산</b>이 유리한가?<br>④ 만기가 긴 채권이 금리 충격을 더 크게 받지 않는가?</div></div>',
            unsafe_allow_html=True,
        )


def render_last_result():
    r = st.session_state.last_result
    if not r:
        return
    scenario = r["scenario"]
    box_class = "good-result" if r["is_correct"] else "bad-result"
    judge = "정답에 가까운 판단" if r["is_correct"] else "아쉬운 판단"
    keyword_text = BEGINNER_EXPLAINERS.get(scenario["keyword"], scenario["concept"])
    extra = ""
    if not r["is_correct"]:
        extra = f'<div style="margin-top:10px;"><b>더 나은 선택:</b> {scenario["choices"][r["optimal_idx"]]}</div>'
    shield_text = "<div style='margin-top:8px;'><b>실드 발동:</b> 큰 손실이 절반 수준으로 완화됐다.</div>" if r["shield_used"] else ""
    st.markdown(
        f'<div class="{box_class}"><div class="section-title">턴 결과</div><div><b>선택:</b> {scenario["choices"][r["choice_idx"]]}</div><div><b>판정:</b> {judge}</div><div><b>설명:</b> {scenario["result_texts"][r["choice_idx"]]}</div><div><b>이번 턴 수익률:</b> {pct_to_str(r["actual_return"])}</div><div><b>현재 자산:</b> {money_to_str(st.session_state.balance)}</div>{shield_text}{extra}<hr class="soft-line"/><div><b>핵심 복습:</b> {scenario["concept"]}</div><div style="margin-top:8px;"><b>쉬운 해설:</b> {keyword_text}</div><div style="margin-top:8px;"><b>초보자 한 줄:</b> {scenario["beginner_tip"]}</div></div>',
        unsafe_allow_html=True,
    )
    if r["is_correct"] and st.session_state.quiz_state["active"]:
        render_mini_quiz(scenario)
    elif st.button("다음 턴으로", use_container_width=True, type="primary"):
        advance_turn()
        st.rerun()


def render_mini_quiz(scenario: dict):
    quiz = scenario["mini_quiz"]
    st.markdown('<div class="learn-box"><div class="section-title">정답 보너스 미니 퀴즈</div><div>맞히면 자산 +1.5억 원, 힌트 토큰 +1</div></div>', unsafe_allow_html=True)
    qkey = f'quiz_{st.session_state.turn_index}'
    selected = st.radio(quiz["question"], options=list(range(len(quiz["options"]))), format_func=lambda i: quiz["options"][i], key=qkey)
    if not st.session_state.quiz_state["answered"]:
        if st.button("미니 퀴즈 제출", use_container_width=True):
            submit_quiz_answer(selected)
            st.rerun()
    else:
        if st.session_state.quiz_state["correct"]:
            st.success(f"정답. {quiz['explanation']} 보너스로 자산 +1.5억 원, 힌트 토큰 +1이 지급됐다.")
        else:
            st.error(f"오답. {quiz['explanation']}")
        if st.button("다음 턴으로", use_container_width=True, type="primary"):
            advance_turn()
            st.rerun()


def render_finished():
    balance = st.session_state.balance
    initial_balance = st.session_state.initial_balance
    ending = get_ending(balance, initial_balance)
    total_return = safe_ratio(balance, initial_balance) - 1
    if balance <= st.session_state.survival_limit:
        st.error("마진콜 발생. 자산이 생존 기준선 아래로 내려갔다.")
    st.markdown(f'<div class="ending-card"><div style="font-size:3.2rem;">{ending["icon"]}</div><div class="grade-pill">{ending["grade"]} 엔딩</div><div class="event-title" style="margin-top:0;">{ending["title"]}</div><div class="muted" style="margin-top:10px;">{ending["desc"]}</div><hr class="soft-line"/><div><b>최종 자산:</b> {money_to_str(balance)}</div><div><b>총 수익률:</b> {pct_to_str(total_return)}</div><div><b>정답 수:</b> {st.session_state.correct_count}/{len(st.session_state.scenarios)}</div><div><b>최고 연속 정답:</b> {st.session_state.best_streak}</div><div><b>최종 배지:</b> {get_badge(balance, initial_balance)}</div></div>', unsafe_allow_html=True)
    pdf_bytes = build_pdf_report()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("처음부터 다시 시작", use_container_width=True, type="primary"):
            reset_game()
            st.rerun()
    with c2:
        st.download_button("학습 리포트 PDF 다운로드", data=pdf_bytes, file_name="bond_history_learning_report.pdf", mime="application/pdf", use_container_width=True)
    st.markdown("### 플레이 로그")
    for log in st.session_state.logs:
        bonus_txt = f" | 퀴즈 보너스 {money_to_str(log.get('quiz_bonus', 0))}" if log.get("quiz_bonus", 0) else ""
        mark = "✅" if log["is_correct"] else "❌"
        st.markdown(f'<div class="log-card"><b>{mark} TURN {log["turn"]}</b> · {log["year"]} · {log["title"]}<br>선택: {log["choice"]}<br>키워드: {log["keyword"]}<br>턴 수익률: {pct_to_str(log["actual_return"])}{bonus_txt}<br>턴 종료 자산: {money_to_str(log["balance"])} </div>', unsafe_allow_html=True)


render_header()
render_sidebar()

if not st.session_state.started:
    render_setup()
else:
    render_dashboard()
    tab_game, tab_portfolio = st.tabs(["게임 진행", "모의 포트폴리오"])
    with tab_game:
        if st.session_state.finished:
            render_finished()
        else:
            if st.session_state.last_result is not None:
                render_last_result()
            else:
                render_current_scenario()
    with tab_portfolio:
        render_portfolio_screen()
