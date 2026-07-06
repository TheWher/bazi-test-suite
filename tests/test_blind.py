"""盲测 — 名人命例排盘准确性 + Agent验盘命中率

Part A: 排盘正确性 — 对比已知四柱
Part B: 数据完整性 — 验证 Agent 所需字段齐全
Part C: API 盲测 — 调 Agent 验盘，对比 known_facts（需 API Key）

用法：
    pytest tests/test_blind.py -m blind -k "test_blind_paipan"       # Part A+B
    pytest tests/test_blind.py -m blind -k "test_blind_api"          # Part C（调API）
"""

import json
import os
import re
import sys
import pytest
from collections import Counter

# ═══════════════════════════════════════════════════════════════
# 名人命例库
# 时辰来源：多数名人出生时辰未公开，时柱均为命理界推测
# 前三柱来源：多个命理网站交叉验证
# ═══════════════════════════════════════════════════════════════

BLIND_CASES = [
    {
        "name": "邓小平",
        "birth": "1904-08-22 00:30", "gender": "男",
        "longitude": 106.55, "location": "四川广安",
        "expected_sizhu": "甲辰 壬申 戊子 壬子",
        "birth_hour_verified": False,
        "known_facts": [
            "1920年赴法勤工俭学",
            "1978年十一届三中全会",
            "1992年南巡讲话",
        ],
    },
    {
        "name": "马云",
        "birth": "1964-09-10 12:00", "gender": "男",
        "longitude": 120.17, "location": "杭州",
        "expected_3pillar": "甲辰 癸酉 壬戌",
        "birth_hour_verified": False,
        "known_facts": [
            "1988年杭州师范学院毕业",
            "1999年创立阿里巴巴",
            "2014年阿里巴巴纽交所上市",
        ],
    },
    {
        "name": "王菲",
        "birth": "1969-08-08 10:00", "gender": "女",
        "longitude": 116.40, "location": "北京",
        "expected_3pillar": "己酉 壬申 乙卯",
        "birth_hour_verified": False,
        "known_facts": [
            "1989年出道",
            "1996年与窦唯结婚，1999年离婚",
            "2005年与李亚鹏结婚，2013年离婚",
        ],
    },
    {
        "name": "郎朗",
        "birth": "1982-06-14 08:00", "gender": "男",
        "longitude": 123.43, "location": "辽宁沈阳",
        "expected_3pillar": "壬戌 丙午 戊辰",
        "birth_hour_verified": False,
        "known_facts": [
            "1985年（3岁）开始学钢琴",
            "1999年（17岁）替补演出成名",
            "2003年（21岁）发行协奏曲专辑",
        ],
    },
    {
        "name": "姚明",
        "birth": "1980-09-12 18:00", "gender": "男",
        "longitude": 121.47, "location": "上海",
        "expected_3pillar": "庚申 乙酉 戊子",
        "birth_hour_verified": False,
        "known_facts": [
            "2002年NBA选秀状元",
            "2008年北京奥运会旗手",
            "2011年正式退役",
        ],
    },
    {
        "name": "李娜",
        "birth": "1982-02-26 10:00", "gender": "女",
        "longitude": 114.27, "location": "湖北武汉",
        "expected_3pillar": "壬戌 壬寅 庚辰",
        "birth_hour_verified": False,
        "known_facts": [
            "2011年法网女单冠军",
            "2014年澳网女单冠军",
            "2014年9月正式退役",
        ],
    },
]

# ═══════════════════════════════════════════════════════════════
# Part A: 排盘正确性
# ═══════════════════════════════════════════════════════════════

@pytest.mark.blind
@pytest.mark.parametrize("case", BLIND_CASES, ids=lambda c: c["name"])
def test_blind_paipan_accuracy(paipan, case):
    """验证名人命例排盘前三柱与已知四柱一致"""
    parts = case["birth"].split()
    date_parts = parts[0].split("-")
    time_parts = parts[1].split(":")
    y, m, d = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
    h, mi = int(time_parts[0]), int(time_parts[1])

    plate = paipan(y, m, d, h, mi, case["gender"], case["longitude"], case["location"])
    s = plate.sizhu
    actual_full = f"{s['year']['gz']} {s['month']['gz']} {s['day']['gz']} {s['hour']['gz']}"
    actual_3p = f"{s['year']['gz']} {s['month']['gz']} {s['day']['gz']}"

    if case.get("expected_sizhu"):
        assert actual_full == case["expected_sizhu"], \
            f"四柱不匹配: 预期 {case['expected_sizhu']}, 实际 {actual_full}"
    elif case.get("expected_3pillar"):
        assert actual_3p == case["expected_3pillar"], \
            f"前三柱不匹配: 预期 {case['expected_3pillar']}, 实际 {actual_3p}"


# ═══════════════════════════════════════════════════════════════
# Part B: 数据完整性
# ═══════════════════════════════════════════════════════════════

REQUIRED_FIELDS = [
    "pillars.year.gz",
    "pillars.month.gz",
    "pillars.day.gz",
    "pillars.hour.gz",
    "ri_zhu",
    "year_type",
    "qiyun.age",
    "qiyun.direction",
    "dayun[0].gz",
    "taiyuan",
    "minggong",
    "shengong",
    "shensha.tianguiren",
    "shensha.wenchang",
    "shensha.yima",
    "shensha.taohua",
    "kongwang.kong1",
]


def _dot_get(d, path):
    """按点号路径从嵌套 dict 中取值，支持 list[idx]"""
    for key in path.split("."):
        if "[" in key:
            k, idx = key.split("[")
            idx = int(idx.rstrip("]"))
            val = d.get(k, [])
            d = val[idx] if isinstance(val, list) and len(val) > idx else None
        else:
            d = d.get(key) if isinstance(d, dict) else None
        if d is None:
            return None
    return d


@pytest.mark.blind
@pytest.mark.parametrize("case", BLIND_CASES, ids=lambda c: c["name"])
def test_blind_data_completeness(paipan, plate_to_dict, case):
    """验证 plate_to_dict 输出包含 Agent 所需全部字段"""
    parts = case["birth"].split()
    date_parts = parts[0].split("-")
    time_parts = parts[1].split(":")
    y, m, d = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
    h, mi = int(time_parts[0]), int(time_parts[1])

    plate = paipan(y, m, d, h, mi, case["gender"], case["longitude"], case["location"])
    p = plate_to_dict(plate)

    missing = []
    for field in REQUIRED_FIELDS:
        label = field
        if _dot_get(p, field) in (None, ""):
            missing.append(label)

    assert not missing, f"{case['name']}: 缺少字段 {missing}"


# ═══════════════════════════════════════════════════════════════
# Part C: Agent API 盲测（需 API Key，标记 slow）
# ═══════════════════════════════════════════════════════════════

GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
ZHI_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
          "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
          "戌": "土", "亥": "水"}

BALANCED_CASES = [c for c in BLIND_CASES if c["name"] in ("马云", "王菲", "李娜")]


def _compute_spread(plate):
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for p in ["year", "month", "day", "hour"]:
        counts[GAN_WX[plate.sizhu[p]["gan"]]] += 1
        counts[ZHI_WX[plate.sizhu[p]["zhi"]]] += 1
    vals = list(counts.values())
    return max(vals) - min(vals), counts


def _extract_years(text):
    years = set()
    for m in re.finditer(r'\b(1[89]\d{2}|20[0-2]\d)\b', text):
        y = int(m.group(0))
        if 1900 <= y <= 2026:
            years.add(y)
    return sorted(years)


def _match_by_year(pred_text, facts):
    pred_years = _extract_years(pred_text)
    matches = []
    for fact in facts:
        fact_years = _extract_years(fact)
        for py in pred_years:
            for fy in fact_years:
                if abs(py - fy) <= 1:
                    matches.append((py, fy, fact))
                    break
    return matches


@pytest.mark.blind
@pytest.mark.slow
@pytest.mark.parametrize("case", BALANCED_CASES, ids=lambda c: c["name"])
def test_blind_api_balanced(paipan, plate_to_dict, analysis_service, case):
    """均衡命局 Agent 盲测 — 调 API 验盘，对比 known_facts 年份"""
    if analysis_service is None:
        pytest.skip("analysis_service 不可用（无 API Key）")

    parts = case["birth"].split()
    date_parts = parts[0].split("-")
    time_parts = parts[1].split(":")
    y, m, d = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
    h, mi = int(time_parts[0]), int(time_parts[1])

    plate = paipan(y, m, d, h, mi, case["gender"], case["longitude"], case["location"])
    pdict = plate_to_dict(plate)
    spread, wx_counts = _compute_spread(plate)
    s = plate.sizhu
    gz_str = f"{s['year']['gz']} {s['month']['gz']} {s['day']['gz']} {s['hour']['gz']}"

    label = "均衡" if spread <= 1 else ("略偏" if spread <= 2 else "偏枯")

    # 调 API 验盘
    try:
        result = analysis_service.analyze_bazi(pdict, timeout=180)
    except Exception as e:
        pytest.fail(f"API 调用异常: {e}")

    assert result.get("success"), f"API 失败: {result.get('error')}"

    analysis = result["analysis"]
    usage = result.get("usage", {})
    pred_years = _extract_years(analysis)
    fact_years = set()
    for f in case["known_facts"]:
        fact_years.update(_extract_years(f))

    matches = _match_by_year(analysis, case["known_facts"])
    hit_years = set(py for py, fy, _ in matches)

    # 保存完整分析
    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"blind_{case['name']}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# {case['name']} 盲测\n\n")
        f.write(f"- 四柱: {gz_str}\n- spread: {spread} ({label})\n")
        f.write(f"- tokens: {usage.get('input_tokens', 0)}+{usage.get('output_tokens', 0)}\n\n")
        f.write("## Agent 验盘输出\n\n")
        f.write(analysis)

    print(f"\n{case['name']}: {gz_str}  spread={spread}({label})")
    print(f"  预测年份: {pred_years}")
    print(f"  事实年份: {sorted(fact_years)}")
    print(f"  命中: {sorted(hit_years)}")
    for fact in case["known_facts"]:
        fy = _extract_years(fact)
        hit = any(fy_i in hit_years for fy_i in fy)
        print(f"    {'✅' if hit else '❌'} {fact}")
    print(f"  报告: {report_path}")

    # 均衡命局预期命中率不高 — 不强制断言，记录结果
    hit_rate = len(hit_years) / max(len(fact_years), 1)
    print(f"  命中率: {hit_rate:.0%}")
