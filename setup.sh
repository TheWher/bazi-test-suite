#!/bin/bash
# 一键初始化测试环境
# 用法: bash setup.sh

set -e

echo "==> 安装 Python 依赖"
pip install -r requirements.txt

echo "==> 克隆主项目"
if [ ! -d "bazi-paipan" ]; then
    git clone https://github.com/TheWher/bazi-paipan.git bazi-paipan
else
    echo "    bazi-paipan 已存在，git pull 更新..."
    cd bazi-paipan && git pull origin master && cd ..
fi

echo "==> 验证排盘引擎"
cd bazi-paipan
python -c "from bazi_calculator import paipan; p=paipan(2005,8,19,1,35,'男',113.75,'东莞'); print(f'日主: {p.ri_zhu}, 四柱: OK')"
cd ..

echo ""
echo "✅ 初始化完成"
echo "   运行冒烟测试:  pytest tests/ -m smoke"
echo "   运行引擎测试:  pytest tests/ -m engine"
echo "   运行全部测试:  pytest tests/ -m 'not slow'"
echo ""
echo "⚠️  Agent 盲测需配置 API Key:"
echo "   在 bazi-paipan/ 目录创建 config.local.py"
