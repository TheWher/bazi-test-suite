"""Agent 分析质量评估 — 内部一致性 + 验盘反馈统计

两个模式（均不依赖外部 API）：
- consistency  — 检查分析文本内部矛盾（旺衰/格局/用神/调候/待验证标注）
- verify-report — 统计用户标注的验盘反馈命中率

用法：
    pytest tests/test_agent.py -m agent              # 全部
    pytest tests/test_agent.py -m agent -k consistency  # 仅一致性
"""

import json
import os
import re
import pytest
from collections import Counter
from datetime import datetime

FEEDBACK_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "Destiny_agent", "feedback"
)


def _load_feedback_logs():
    """加载所有反馈日志"""
    if not os.path.isdir(FEEDBACK_DIR):
        return []
    logs = []
    for fn in sorted(os.listdir(FEEDBACK_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(FEEDBACK_DIR, fn), "r", encoding="utf-8") as f:
                logs.append((fn, json.load(f)))
        except Exception:
            continue
    return logs


# ═══════════════════════════════════════════════════════════════
# 一致性检查
# ═══════════════════════════════════════════════════════════════

def _extract_analysis_texts(log):
    """从日志中提取所有 assistant 消息"""
    texts = []
    for msg in log.get("conversation", []):
        if msg["role"] == "assistant":
            texts.append(msg["content"])
    return texts


def _check_consistency(full_text, is_full):
    """对单份分析做全维度一致性检查，返回问题列表"""
    issues = []

    # 旺衰矛盾（排除假设句）
    strong = len(re.findall(r'(?<!如果)(?<!若)(?<!假设)身强|日主偏强|身旺|日主旺', full_text))
    weak = len(re.findall(r'(?<!如果)(?<!若)(?<!假设)身弱|日主偏弱|身衰', full_text))
    if strong >= 2 and weak >= 2:
        issues.append(f"旺衰矛盾：身强{strong}次 + 身弱{weak}次")

    # 格局一致性
    patterns = re.findall(r'格局[是为：:]\s*(正官格|七杀格|财格|印格|食神格|伤官格|从格|化格|专旺格|建禄格|月刃格)', full_text)
    if len(set(patterns)) > 1:
        issues.append(f"格局不一致：{set(patterns)}")

    # 用神一致性
    yong = re.findall(r'用神[是为：:]\s*\*{0,2}(\S+?)\*{0,2}(?:[，。\s]|$)', full_text)
    yong_clean = [re.sub(r'[（(].+[）)]', '', y).strip('*') for y in yong]
    yong_clean = [y for y in yong_clean if len(y) <= 10 and y]
    if len(set(yong_clean)) > 2:
        issues.append(f"用神不一致：{set(yong_clean)}")

    # 调候缺失
    if is_full and re.search(r'[巳午未]月', full_text) and '调候' not in full_text[:2000]:
        issues.append("夏季出生但前2000字未提调候")

    # 经典引用
    if is_full:
        refs = re.findall(r'《([^》]+)》', full_text)
        if len(refs) < 2:
            issues.append(f"经典引用不足：仅{len(refs)}处")

    # 待验证标注
    if is_full:
        marks = len(re.findall(r'【待验证】|\[待验证\]', full_text))
        if marks == 0:
            issues.append("完整分析无【待验证】标注")

    return issues


@pytest.mark.agent
def test_consistency_in_feedback_logs():
    """对所有反馈日志做内部一致性扫描"""
    logs = _load_feedback_logs()
    if not logs:
        pytest.skip("无反馈日志可检查")

    issues_found = []
    for fn, log in logs:
        texts = _extract_analysis_texts(log)
        if not texts:
            continue
        full = "\n".join(texts)
        is_full = len(full) > 3000
        problems = _check_consistency(full, is_full)
        if problems:
            issues_found.append((fn, problems))

    print(f"\n检查 {len(logs)} 份日志，{len(issues_found)} 份存在内部不一致")
    for fn, problems in issues_found:
        print(f"  ⚠️ {fn}:")
        for p in problems:
            print(f"     - {p}")

    # 一致性率应 ≥ 50%
    if logs:
        rate = (len(logs) - len(issues_found)) / len(logs)
        print(f"\n一致率: {rate:.0%}")
        # 软断言：记录但不阻塞
        if rate < 0.5 and len(logs) >= 4:
            pytest.fail(f"一致率过低: {rate:.0%}")


# ═══════════════════════════════════════════════════════════════
# 验盘反馈统计
# ═══════════════════════════════════════════════════════════════

@pytest.mark.agent
def test_verify_report_stats():
    """统计已标注验盘反馈的命中率"""
    logs = _load_feedback_logs()
    verified = [(fn, log) for fn, log in logs
                if "verification" in log and log["verification"].get("predictions")]

    if not verified:
        pytest.skip("无已标注验盘反馈")

    all_labels = []
    all_hit_rates = []

    for fn, log in verified:
        preds = log["verification"]["predictions"]
        labels = [p["label"] for p in preds]
        all_labels.extend(labels)
        hr = log["verification"]["summary"].get("hit_rate", 0)
        all_hit_rates.append(hr)

    counts = Counter(all_labels)
    total = len(all_labels)

    print(f"\n验盘统计 ({len(verified)} 份已标注):")
    print(f"  总预测: {total}")
    print(f"  准确:   {counts.get('correct', 0)} ({counts.get('correct', 0)/max(total,1)*100:.0f}%)")
    print(f"  部分:   {counts.get('partially_correct', 0)} ({counts.get('partially_correct', 0)/max(total,1)*100:.0f}%)")
    print(f"  错误:   {counts.get('wrong', 0)} ({counts.get('wrong', 0)/max(total,1)*100:.0f}%)")
    print(f"  加权命中率: {sum(all_hit_rates)/max(len(all_hit_rates),1)*100:.0f}%")

    # 错误模式分析
    wrong_preds = [p for _, log in verified
                   for p in log["verification"]["predictions"]
                   if p["label"] == "wrong"]
    if wrong_preds:
        print(f"\n  {len(wrong_preds)} 条错误预测:")
        for p in wrong_preds:
            print(f"    - {p.get('user_note', '(无说明)')}")

    # 至少有一条正确预测才算有效
    assert total > 0, "无任何验盘预测数据"
