# 安装依赖
pip install -r requirements.txt

# 分析单个基金
python main.py 000001

# 对比多个基金
python main.py 000001 000002 --compare

# 快速预测
python main.py 000001 --quick

# 保存图表
python main.py 000001 --save-plots
