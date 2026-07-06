"""排盘引擎精度测试 — 24 条用例，12 个分类

覆盖：基础四柱、夜子时、节气边界、真太阳时、大运顺逆、
      闰月、十神、藏干、十二长生、空亡、胎元命宫身宫、性别差异

验证基准：sxtwl 官方文档 + 港版《通胜》 + 命理师交叉验证
"""

import pytest
from bazi_calculator import TIAN_GAN, DI_ZHI


# ═══════════════════════════════════════════════════════════════
# 测试用例定义
# ═══════════════════════════════════════════════════════════════

ENGINE_CASES = [
    # ── 基础四柱 ──
    {
        "id": "basic-2005-dongguan-male",
        "category": "基础四柱",
        "params": (2005, 8, 19, 1, 35, "男", 113.75, "东莞"),
        "checks": [
            ("sizhu", "乙酉 甲申 乙亥 丁丑"),
            ("ri_zhu", "乙"),
            ("year_type", "阴年"),
            ("shishen_year", "比肩"),
            ("shishen_month", "劫财"),
            ("shishen_hour", "食神"),
            ("qiyun_direction", "逆行"),
        ],
    },
    {
        "id": "basic-1950-national-day",
        "category": "基础四柱",
        "params": (1950, 10, 1, 12, 0, "男", 116.4, "北京"),
        "checks": [
            ("sizhu", "庚寅 乙酉 己巳 庚午"),
            ("ri_zhu", "己"),
            ("year_type", "阳年"),
        ],
    },
    {
        "id": "basic-1980-reform",
        "category": "基础四柱",
        "params": (1980, 8, 26, 0, 15, "女", 121.47, "上海"),
        "checks": [
            ("sizhu", "庚申 甲申 辛未 戊子"),
            ("ri_zhu", "辛"),
            ("year_type", "阳年"),
            ("qiyun_direction", "逆行"),
        ],
    },
    {
        "id": "basic-2000-millennium",
        "category": "基础四柱",
        "params": (2000, 1, 1, 8, 0, "男", 114.17, "香港"),
        "checks": [
            ("ri_zhu", "戊"),
            ("year_type", "阴年"),  # 己卯年，己=阴
        ],
    },

    # ── 夜子时 ──
    {
        "id": "yezi-23h",
        "category": "夜子时",
        "params": (2005, 8, 19, 23, 15, "男", 120.0, "北京"),
        "kwargs": {"apply_solar_correction": False},
        "checks": [
            ("ri_zhu", "丙"),
            ("sizhu_contains", "戊子"),
        ],
    },
    {
        "id": "yezi-midnight-border",
        "category": "夜子时",
        "params": (2005, 8, 20, 0, 0, "男", 120.0, "北京"),
        "kwargs": {"apply_solar_correction": False},
        "checks": [
            ("ri_zhu", "丙"),
            ("shichen_zhi", "子"),
        ],
    },

    # ── 节气边界 ──
    {
        "id": "jieqi-lichun-border",
        "category": "节气边界",
        "params": (2024, 2, 4, 17, 0, "男", 116.4, "北京"),
        "checks": [("year_type", "阳年")],  # 甲辰年
    },
    {
        "id": "jieqi-before-lichun",
        "category": "节气边界",
        "params": (2024, 2, 4, 10, 0, "男", 116.4, "北京"),
        "checks": [("ri_zhu", "戊")],
    },
    {
        "id": "jieqi-solar-term-month",
        "category": "节气边界",
        "params": (2025, 1, 21, 10, 0, "女", 120.17, "杭州"),
        "checks": [("month_zhi", "丑")],
    },

    # ── 真太阳时 ──
    {
        "id": "solar-time-kashgar",
        "category": "真太阳时",
        "params": (2005, 8, 19, 10, 0, "男", 75.99, "喀什"),
        "checks": [
            ("solar_applied", True),
            ("shichen_zhi", "辰"),
        ],
    },
    {
        "id": "solar-time-japan",
        "category": "真太阳时",
        "params": (2005, 8, 19, 12, 0, "女", 139.69, "东京"),
        "checks": [("solar_applied", True)],
    },

    # ── 大运顺逆 ──
    {
        "id": "dayun-yang-male-forward",
        "category": "大运顺逆",
        "params": (1984, 3, 1, 8, 0, "男", 120.0, "北京"),
        "checks": [("year_type", "阳年"), ("qiyun_direction", "顺行")],
    },
    {
        "id": "dayun-yang-female-backward",
        "category": "大运顺逆",
        "params": (1984, 3, 1, 8, 0, "女", 120.0, "北京"),
        "checks": [("year_type", "阳年"), ("qiyun_direction", "逆行")],
    },
    {
        "id": "dayun-yin-male-backward",
        "category": "大运顺逆",
        "params": (2005, 8, 19, 1, 35, "男", 113.75, "东莞"),
        "checks": [("year_type", "阴年"), ("qiyun_direction", "逆行")],
    },
    {
        "id": "dayun-yin-female-forward",
        "category": "大运顺逆",
        "params": (2005, 8, 19, 1, 35, "女", 113.75, "东莞"),
        "checks": [("year_type", "阴年"), ("qiyun_direction", "顺行")],
    },

    # ── 闰月 ──
    {
        "id": "leap-month-2023",
        "category": "闰月",
        "params": (2023, 4, 20, 10, 0, "男", 116.4, "北京"),
        "checks": [("lunar_month_in", (2, 3))],
    },

    # ── 十神 ──
    {
        "id": "shishen-2005-dongguan",
        "category": "十神",
        "params": (2005, 8, 19, 1, 35, "男", 113.75, "东莞"),
        "checks": [
            ("ri_zhu", "乙"),
            ("shishen_year", "比肩"),
            ("shishen_month", "劫财"),
            ("shishen_hour", "食神"),
        ],
    },
    {
        "id": "shishen-1980-shanghai",
        "category": "十神",
        "params": (1980, 8, 26, 0, 15, "女", 121.47, "上海"),
        "checks": [
            ("ri_zhu", "辛"),
            ("shishen_year", "劫财"),
            ("shishen_month", "正财"),
            ("shishen_hour", "正印"),
        ],
    },

    # ── 藏干 ──
    {
        "id": "canggan-shen-zhi",
        "category": "藏干",
        "params": (2005, 8, 19, 1, 35, "男", 113.75, "东莞"),
        "checks": [("month_canggan_has", ["庚", "壬", "戊"])],
    },
    {
        "id": "canggan-zi-zhi",
        "category": "藏干",
        "params": (1980, 8, 26, 0, 15, "女", 121.47, "上海"),
        "checks": [("hour_canggan_has", ["癸"]), ("hour_canggan_count", 1)],
    },

    # ── 十二长生 ──
    {
        "id": "changsheng-yi-hai",
        "category": "十二长生",
        "params": (2005, 8, 19, 1, 35, "男", 113.75, "东莞"),
        "checks": [("ri_zhu", "乙"), ("day_changsheng", "死")],
    },

    # ── 空亡 ──
    {
        "id": "kongwang-jiaxun",
        "category": "空亡",
        "params": (2005, 8, 19, 1, 35, "男", 113.75, "东莞"),
        "checks": [
            ("kongwang_set", {"申", "酉"}),
            ("kong_pillar_year", True),
            ("kong_pillar_month", True),
        ],
    },

    # ── 胎元/命宫/身宫 ──
    {
        "id": "taiyuan-2005-dongguan",
        "category": "胎元命宫身宫",
        "params": (2005, 8, 19, 1, 35, "男", 113.75, "东莞"),
        "checks": [("taiyuan", "乙亥")],
    },

    # ── 性别 ──
    {
        "id": "female-basic",
        "category": "性别",
        "params": (2005, 8, 19, 1, 35, "女", 113.75, "东莞"),
        "checks": [("ri_zhu", "乙"), ("year_type", "阴年"), ("qiyun_direction", "顺行")],
    },
]


# ═══════════════════════════════════════════════════════════════
# 校验器：将 check 键映射到 plate 属性
# ═══════════════════════════════════════════════════════════════

def _resolve(plate, key):
    s = plate.sizhu
    ss = plate.shishen
    qy = plate.qiyun
    kg = plate.kongwang

    _map = {
        "sizhu": lambda: f"{s['year']['gz']} {s['month']['gz']} {s['day']['gz']} {s['hour']['gz']}",
        "ri_zhu": lambda: plate.ri_zhu,
        "year_type": lambda: plate.year_type,
        "shishen_year": lambda: ss["year"],
        "shishen_month": lambda: ss["month"],
        "shishen_hour": lambda: ss["hour"],
        "shichen_zhi": lambda: s["hour"]["zhi"],
        "qiyun_direction": lambda: qy["direction"],
        "qiyun_age": lambda: qy["qiyun_age"],
        "month_zhi": lambda: s["month"]["zhi"],
        "solar_applied": lambda: plate.solar_adjusted.get("applied", False),
        "day_changsheng": lambda: plate.changsheng["day"],
        "kongwang_set": lambda: {kg["kong1"], kg["kong2"]},
        "kong_pillar_year": lambda: kg["pillars"]["year"],
        "kong_pillar_month": lambda: kg["pillars"]["month"],
        "taiyuan": lambda: plate.taiyuan,
    }
    if key in _map:
        return _map[key]()
    return None


# ═══════════════════════════════════════════════════════════════
# pytest 参数化
# ═══════════════════════════════════════════════════════════════

def _case_id(case):
    return f"{case['category']}/{case['id']}"


@pytest.mark.engine
@pytest.mark.parametrize("case", ENGINE_CASES, ids=_case_id)
def test_engine_case(paipan, case):
    """逐条验证排盘引擎输出"""
    args = case["params"]
    kwargs = case.get("kwargs", {})
    plate = paipan(*args, **kwargs)

    for key, expected in case["checks"]:
        if key == "sizhu_contains":
            actual = _resolve(plate, "sizhu")
            assert expected in actual, f"sizhu_contains: '{expected}' not in '{actual}'"
        elif key == "month_canggan_has":
            actual = [g for g, _ in plate.canggan["month"]]
            for g in expected:
                assert g in actual, f"month_canggan missing {g}, got {actual}"
        elif key == "hour_canggan_has":
            actual = [g for g, _ in plate.canggan["hour"]]
            for g in expected:
                assert g in actual, f"hour_canggan missing {g}, got {actual}"
        elif key == "hour_canggan_count":
            actual = len(plate.canggan["hour"])
            assert actual == expected, f"hour_canggan_count: {expected} != {actual}"
        elif key == "shichen_zhi":
            assert plate.sizhu["hour"]["zhi"] == expected, \
                f"shichen_zhi: {expected} != {plate.sizhu['hour']['zhi']}"
        elif key == "lunar_month_in":
            assert plate.lunar["month"] in expected, \
                f"lunar_month: {plate.lunar['month']} not in {expected}"
        else:
            actual = _resolve(plate, key)
            assert actual == expected, \
                f"{key}: expected '{expected}', got '{actual}'"


# ═══════════════════════════════════════════════════════════════
# 冒烟测试 — 5 条核心用例，30 秒内完成
# ═══════════════════════════════════════════════════════════════

SMOKE_IDS = {
    "basic-2005-dongguan-male", "yezi-23h",
    "jieqi-lichun-border", "dayun-yin-male-backward",
    "kongwang-jiaxun",
}

SMOKE_CASES = [c for c in ENGINE_CASES if c["id"] in SMOKE_IDS]


@pytest.mark.smoke
@pytest.mark.parametrize("case", SMOKE_CASES, ids=_case_id)
def test_engine_smoke(paipan, case):
    """冒烟测试 — 核心路径快速验证"""
    args = case["params"]
    kwargs = case.get("kwargs", {})
    plate = paipan(*args, **kwargs)
    assert plate.ri_zhu is not None
    assert plate.sizhu["year"]["gz"] is not None


# ═══════════════════════════════════════════════════════════════
# 辅助函数单元测试
# ═══════════════════════════════════════════════════════════════

def test_compute_spread(analysis_service):
    """验证五行极端度计算"""
    if analysis_service is None:
        pytest.skip("analysis_service 不可用")
    from bazi_calculator import paipan

    plate = paipan(2005, 8, 19, 1, 35, "男", 113.75, "东莞")
    spread, label, counts = analysis_service.compute_spread(
        {"pillars": {
            "year": {"gan": "乙", "zhi": "酉"},
            "month": {"gan": "甲", "zhi": "申"},
            "day": {"gan": "乙", "zhi": "亥"},
            "hour": {"gan": "丁", "zhi": "丑"},
        }}
    )
    assert isinstance(spread, int)
    assert spread >= 0
    assert label in ("均衡", "略偏", "偏枯", "极端")


def test_evaluate_liunian_signal(analysis_service):
    """验证六级流年信号判定"""
    if analysis_service is None:
        pytest.skip("analysis_service 不可用")

    fn = analysis_service._evaluate_liunian_signal
    dayun = [{"gz": "戊戌", "gan": "戊", "zhi": "戌",
              "start_year": 2018, "start_age": 14, "end_age": 24, "step": 1}]

    # S级：天克地冲
    level, desc = fn("庚午", "甲子", "申", "辰", dayun, 2026)
    assert level == "S", f"Expected S, got {level}"
    assert "天克地冲" in desc

    # A级：日柱伏吟
    level, desc = fn("甲子", "甲子", "申", "辰", dayun, 2020)
    assert level == "A", f"Expected A, got {level}"

    # B级：冲日支
    level, desc = fn("丙午", "甲子", "申", "辰", dayun, 2026)
    assert level == "B", f"Expected B, got {level}"

    # C级：六合日支
    level, desc = fn("己丑", "甲子", "申", "辰", dayun, 2009)
    assert level == "C", f"Expected C, got {level}"

    # D级：驿马
    level, desc = fn("甲寅", "甲子", "丑", "酉", dayun, 2010)
    assert level == "D", f"Expected D, got {level}"

    # E级：墓库
    level, desc = fn("庚戌", "甲戌", "子", "寅", dayun, 2012)
    assert level == "E", f"Expected E, got {level}"

    # —：无信号
    level, desc = fn("己亥", "甲子", "申", "辰", dayun, 2019)
    assert level is None, f"Expected None, got {level}"


def test_build_year_lookup_table(analysis_service):
    """验证对照表生成格式"""
    if analysis_service is None:
        pytest.skip("analysis_service 不可用")
    from bazi_calculator import paipan

    plate = paipan(2005, 8, 19, 1, 35, "男", 113.75, "东莞")
    table = analysis_service._build_year_lookup_table(plate, 2010)

    assert "流年干支-西历对照表" in table
    assert "出生年：2005年" in table
    assert "日柱：" in table
    assert "2005" in table
    assert "2010" in table
    assert "🔵当前" in table

    data_lines = [l for l in table.split("\n") if l.startswith("| 20")]
    assert len(data_lines) == 6, f"预期6年数据行，实际{len(data_lines)}"


def test_verify_predictions(analysis_service):
    """验证后处理硬校验函数"""
    if analysis_service is None:
        pytest.skip("analysis_service 不可用")
    from bazi_calculator import paipan

    plate = paipan(2005, 8, 19, 1, 35, "男", 113.75, "东莞")
    test_text = """
    ### 第一条：1998年家庭搬迁
    流年戊寅冲月柱甲申...
    ### 第二条：2005年学业转折
    """
    result = analysis_service._verify_predictions(test_text, plate, 2026)
    assert "验盘硬校验" in result
    assert "1998" in result

    # 测试不匹配的预测
    bad_text = "### 第一条：1800年科举中举"
    result = analysis_service._verify_predictions(bad_text, plate, 2026)
    assert "⚠️" in result or "❌" in result
