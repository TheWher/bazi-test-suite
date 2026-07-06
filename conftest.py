"""共享 fixtures — 为所有测试模块提供排盘引擎访问入口"""

import os
import sys
import pytest

# 将主项目 bazi-paipan 加入 Python path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BAZI_ROOT = os.path.join(_PROJECT_ROOT, "bazi-paipan")
if os.path.isdir(_BAZI_ROOT):
    sys.path.insert(0, _BAZI_ROOT)
else:
    # 回退: 假设与 Destiny_agent 同级
    _FALLBACK = os.path.join(os.path.dirname(_PROJECT_ROOT), "Destiny_agent")
    if os.path.isdir(_FALLBACK):
        sys.path.insert(0, _FALLBACK)


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "engine: 排盘引擎精度")
    config.addinivalue_line("markers", "agent: Agent分析质量")
    config.addinivalue_line("markers", "blind: 盲测(需API Key)")
    config.addinivalue_line("markers", "slow: 耗时测试")


@pytest.fixture(scope="session")
def bazi_calculator():
    """延迟导入排盘引擎"""
    import bazi_calculator
    return bazi_calculator


@pytest.fixture(scope="session")
def paipan(bazi_calculator):
    """排盘函数"""
    return bazi_calculator.paipan


@pytest.fixture(scope="session")
def plate_to_dict():
    """plate → dict 序列化"""
    from app import plate_to_dict
    return plate_to_dict


@pytest.fixture(scope="session")
def analysis_service():
    """分析服务（需 API Key）"""
    try:
        import analysis_service
        return analysis_service
    except Exception:
        return None


# ---- 测试数据 ----

@pytest.fixture(scope="session")
def user_plate(paipan):
    """用户基准命盘 — 乙酉 甲申 乙亥 丁丑"""
    return paipan(2005, 8, 19, 1, 35, "男", 113.75, "东莞")


@pytest.fixture(scope="session")
def beijing_plate(paipan):
    """北京国庆命盘 — 庚寅 乙酉 己巳 庚午"""
    return paipan(1950, 10, 1, 12, 0, "男", 116.4, "北京")


@pytest.fixture(scope="session")
def shanghai_plate(paipan):
    """上海女命 — 庚申 甲申 辛未 戊子"""
    return paipan(1980, 8, 26, 0, 15, "女", 121.47, "上海")
