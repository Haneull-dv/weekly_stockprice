"""
글로벌 게임 기업 정보 설정 (한국/중국/일본/미국/유럽)
"""
from typing import Dict, List, Optional

# --- 1. 종목코드 → 기업명 (기존 호환) ---
GAME_COMPANIES: Dict[str, str] = {
    # 🇰🇷 한국
    "035420": "네이버", "035720": "카카오", "259960": "크래프톤", "036570": "엔씨소프트", "251270": "넷마블",
    "263750": "펄어비스", "293490": "카카오게임즈", "225570": "넥슨게임즈", "112040": "위메이드", "095660": "네오위즈",
    "181710": "NHN", "078340": "컴투스", "192080": "더블유게임즈", "145720": "더블다운인터액티브", "089500": "그라비티",
    "194480": "데브시스터즈", "069080": "웹젠", "217270": "넵튠", "101730": "위메이드맥스", "063080": "컴투스홀딩스",
    "067000": "조이시티", "950190": "미투젠", "123420": "위메이드플레이", "201490": "미투온", "348030": "모비릭스",
    "052790": "액토즈소프트", "331520": "밸로프", "205500": "넥써쓰", "462870": "시프트업",
    # 🇨🇳 중국 (홍콩/미국/중국본토)
    "00700": "Tencent", "09999": "Netease", "09888": "Baidu", "BIDU": "Baidu", "03888": "Kingsoft",
    "002624": "Perfect World", "00777": "Netdragon", "SOHU": "Sohu", "CMCM": "Cheetah Mobile",
    # 🇯🇵 일본 (도쿄)
    "7974": "Nintendo", "3659": "Nexon", "7832": "Bandai-Namco", "9697": "Capcom", "9766": "KONAMI",
    "9684": "Square-Enix", "6460": "Sega", "3765": "Gungho", "2432": "DeNA", "3632": "Gree",
    "3668": "COLOPL", "3656": "Klab",
    # 🇺🇸 미국 (나스닥/뉴욕)
    "EA": "Electronic-Arts", "RBLX": "Roblox", "TTWO": "Take-Two", "PLTK": "Playtika", "SCPL": "Sciplay",
    # 🇪🇺 유럽 (바르샤바/파리)
    "CDR": "CD Projekt SA", "UBI": "Ubisoft"
}

# --- 2. 기업명 → 종목코드 (역방향) ---
COMPANY_CODES_BY_NAME: Dict[str, str] = {v: k for k, v in GAME_COMPANIES.items()}

# --- 3. 종목코드 → 국가 ---
COMPANY_COUNTRIES: Dict[str, str] = {
    # 한국
    **{code: "KR" for code in [
        "035420","035720","259960","036570","251270","263750","293490","225570","112040","095660",
        "181710","078340","192080","145720","089500","194480","069080","217270","101730","063080",
        "067000","950190","123420","201490","348030","052790","331520","060240","299910"
    ]},
    # 중국
    **{code: "CN" for code in [
        "00700","09999","09888","BIDU","03888","002624","00777","SOHU","CMCM"
    ]},
    # 일본
    **{code: "JP" for code in [
        "7974","3659","7832","9697","9766","9684","6460","3765","2432","3632","3668","3656"
    ]},
    # 미국
    **{code: "US" for code in ["EA","RBLX","TTWO","PLTK","SCPL"]},
    # 유럽
    **{code: "EU" for code in ["CDR","UBI"]}
}

# --- 4. 종목코드 → 네이버 주가 지원여부 ---
NAVER_SUPPORTED: Dict[str, bool] = {
    # 한국, 홍콩, 도쿄, 나스닥/뉴욕, 바르샤바, 파리 등 네이버 지원 종목
    **{code: True for code in [
        # 한국
        "035420","035720","259960","036570","251270","263750","293490","225570","112040","095660",
        "181710","078340","192080","145720","089500","194480","069080","217270","101730","063080",
        "067000","950190","123420","201490","348030","052790","331520","060240","299910",
        # 중국(홍콩/미국)
        "00700","09999","09888","BIDU","03888","00777","SOHU","CMCM",
        # 일본(도쿄)
        "7974","3659","7832","9697","9766","9684","6460","3765","2432","3632","3668","3656",
        # 미국
        "EA","RBLX","TTWO","PLTK","SCPL",
        # 유럽
        "CDR","UBI"
    ]},
    # 중국 본토 등 미지원
    "002624": False
}

# --- 5. 종목코드 → 상세 정보 (확장성) ---
COMPANY_INFO: Dict[str, dict] = {
    code: {
        "name": GAME_COMPANIES[code],
        "country": COMPANY_COUNTRIES.get(code, "Unknown"),
        "naver_supported": NAVER_SUPPORTED.get(code, False)
    }
    for code in GAME_COMPANIES
}

# --- 6. 동적 리스트/필터 함수 예시 ---
def get_company_list(country: Optional[str] = None, naver_supported: Optional[bool] = None) -> List[dict]:
    """
    국가, 네이버 지원여부 등으로 동적 필터링된 기업 리스트 반환
    """
    result = []
    for code, info in COMPANY_INFO.items():
        if country and info["country"] != country:
            continue
        if naver_supported is not None and info["naver_supported"] != naver_supported:
            continue
        result.append({"code": code, **info})
    return result

# --- 7. 기존 리스트/카운트 등도 그대로 유지 ---
TOTAL_COMPANIES = len(GAME_COMPANIES)
COMPANY_NAMES: List[str] = list(GAME_COMPANIES.values())
STOCK_CODES: List[str] = list(GAME_COMPANIES.keys()) 