# 八字排盘 · 测试套件

[![Test Suite](https://github.com/TheWher/bazi-test-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/TheWher/bazi-test-suite/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![pytest](https://img.shields.io/badge/pytest-8.x-orange?logo=pytest)](https://docs.pytest.org/)

[bazi-paipan](https://github.com/TheWher/bazi-paipan) 的自动化测试套件，覆盖排盘引擎精度、Agent 分析质量、盲测命中率三大维度。

## 快速开始

```bash
bash setup.sh                  # 一键：安装依赖 + 克隆主项目
pytest tests/ -m smoke         # 冒烟测试（5 条核心用例，<30s）
pytest tests/ -m engine        # 引擎全量测试（24 条，12 分类）
```

## 测试架构

```
bazi-test-suite/
├── conftest.py                # 共享 fixtures + 路径配置
├── tests/
│   ├── test_engine.py         # 排盘引擎精度（24 条用例）
│   ├── test_agent.py          # Agent 分析质量评估
│   └── test_blind.py          # 名人命例盲测
├── reports/                   # 测试报告输出
└── .github/workflows/ci.yml   # CI 管道
```

## 测试分类

| 标记 | 说明 | 用例数 | 耗时 |
|------|------|--------|------|
| `smoke` | 冒烟测试 — 核心路径快速验证 | 5 | <30s |
| `engine` | 排盘引擎精度 — 四柱/十神/空亡/藏干等 | 24 | ~3s |
| `agent` | Agent 分析质量 — 内部一致性 + 验盘统计 | 动态 | ~1s |
| `blind` | 名人命例盲测 — 排盘 + 数据完整性 | 6 | ~1s |
| `slow` | 耗时测试 — Agent API 盲测（需 API Key） | 3 | ~5min |

## 常用命令

```bash
# 运行指定标记
pytest tests/ -m engine -v
pytest tests/ -m agent -v
pytest tests/ -m blind -v

# 跳过慢速测试
pytest tests/ -m "not slow" -v

# 生成 HTML 报告
pytest tests/ -m engine --html=reports/report.html

# 仅冒烟
pytest tests/ -m smoke -v

# 单条用例
pytest tests/test_engine.py -k "kongwang" -v
```

## 引擎测试覆盖（24 条 × 12 分类）

| 分类 | 用例 | 说明 |
|------|------|------|
| 基础四柱 | 4 | 跨年代/跨性别四柱验证 |
| 夜子时 | 2 | 23:00-0:59 日柱切换 |
| 节气边界 | 3 | 立春/大寒前后的年柱月柱切换 |
| 真太阳时 | 2 | 喀什/东京经度校正 |
| 大运顺逆 | 4 | 阳男/阳女/阴男/阴女四象限 |
| 闰月 | 1 | 闰二月农历转换 |
| 十神 | 2 | 年/月/时干十神比对 |
| 藏干 | 2 | 地支藏干本气/中气 |
| 十二长生 | 1 | 乙日主坐亥→死地 |
| 空亡 | 1 | 甲戌旬→空亡申酉 |
| 胎元命宫 | 1 | 胎元计算公式 |
| 性别差异 | 1 | 同八字不同性别大运方向 |

## Agent 质量评估

### 内部一致性检查

自动扫描反馈日志中的分析文本，检测 6 类矛盾：
- 旺衰矛盾（同时声称身强+身弱）
- 格局不一致（同一分析中切换格局）
- 用神前后矛盾
- 调候缺失（夏月未提调候）
- 经典引用不足
- 缺少【待验证】标注（过度自信）

### 验盘反馈统计

汇总用户标注的正确/部分正确/错误预测，计算命中率及错误模式。

## 盲测命例

| 姓名 | 出生 | 前三柱 | 时辰 |
|------|------|--------|------|
| 邓小平 | 1904-08-22 | 甲辰 壬申 戊子 | 推测 |
| 马云 | 1964-09-10 | 甲辰 癸酉 壬戌 | 推测 |
| 王菲 | 1969-08-08 | 己酉 壬申 乙卯 | 推测 |
| 郎朗 | 1982-06-14 | 壬戌 丙午 戊辰 | 推测 |
| 姚明 | 1980-09-12 | 庚申 乙酉 戊子 | 推测 |
| 李娜 | 1982-02-26 | 壬戌 壬寅 庚辰 | 推测 |

## CI 管道

每周一 8:00 UTC 自动运行 + push/PR 触发：
- **Engine** — 24 条排盘引擎精度测试
- **Agent Quality** — 内部一致性扫描
- **Blind** — 名人命例排盘验证（不含 API 调用）

## 依赖

- **主项目**：[bazi-paipan](https://github.com/TheWher/bazi-paipan)（通过 `setup.sh` 自动克隆）
- **API Key**：仅 `slow` 标记的 Agent 盲测需要（在 `bazi-paipan/config.local.py` 中配置）
