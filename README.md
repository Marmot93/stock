# 基金回撤分析与通知系统

一个基于Python的基金回撤分析工具，支持自动获取基金数据、分析回撤情况并通过Bark推送买入建议。

## 功能特点

- 📈 **智能回撤分析**: 基于历史数据分析当前回撤水平和买入时机
- 📱 **Bark推送通知**: 自动发送分析结果到手机
- 🔄 **数据缓存机制**: 按日期缓存数据，避免重复请求
- 📊 **可视化图表**: 支持绘制回撤率时间序列图
- 🏷️ **基金名称映射**: 自动查询并缓存基金名称
- ⚙️ **配置化管理**: 支持批量推送多个基金到多个设备

## 项目结构

```
stock/
├── fund/                    # 基金分析核心模块
│   ├── data_fetcher.py     # 数据获取和缓存
│   ├── drawdown_analyzer.py # 回撤分析算法
│   ├── visualization.py    # 图表可视化
│   └── notification.py     # 通知推送
├── msg/                     # 消息推送模块
│   └── send_bark.py        # Bark推送功能
├── data/                    # 数据存储目录
│   ├── fund_mapping.json   # 基金名称映射
│   └── fund_*.json         # 基金数据缓存
├── config.json             # 配置文件（需要创建）
├── config.example.json     # 配置文件模板
├── main.py                 # 主程序
└── README.md               # 说明文档
```

## 安装和配置

### 1. 克隆项目

```bash
git clone <repository_url>
cd stock
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install akshare pandas matplotlib requests
```

### 3. 创建配置文件

复制配置模板并填入你的信息：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "bark_urls": [
    "https://api.day.app/your_device_key_1",
    "https://api.day.app/your_device_key_2"
  ],
  "fund_codes": [
    "110017",
    "110022",
    "000001",
    "161725"
  ]
}
```

### 4. 获取Bark推送密钥

1. 在App Store下载Bark应用
2. 打开Bark，复制设备密钥
3. 将密钥填入配置文件的URL中

## 使用方法

### 批量推送分析（推荐）

运行主程序，自动为所有配置的设备推送所有基金的分析：

```bash
python main.py
```

### 单个基金分析

```python
from fund import analyze_drawdown_strategy

# 显示详细分析结果
analyze_drawdown_strategy("110017")
```

### 发送单个通知

```python
from fund import send_drawdown_analysis

# 发送特定基金的分析通知
send_drawdown_analysis("https://api.day.app/your_key", "110017")
```

### 绘制回撤图表

```python
from fund import plot_drawdown_hist

# 显示回撤率时间序列图
plot_drawdown_hist("110017")
```

## 分析结果说明

### 回撤率指标

- **当前回撤率**: 当前净值相对历史最高点的回撤幅度
- **当前回撤百分位**: 当前回撤在历史中的排名（越低表示越便宜）
- **最大回撤**: 历史上最大的回撤幅度
- **平均回撤**: 历史平均回撤水平

### 买入建议分级

- **强烈建议买入**: 回撤≤历史5%分位数（极端便宜）
- **建议买入**: 回撤≤历史10%分位数（较好机会）  
- **可以考虑买入**: 回撤≤历史25%分位数（中等机会）
- **谨慎买入**: 接近历史高点（风险较高）
- **观望**: 回撤水平一般

### 通知内容示例

```
标题: 易方达新兴成长(110017)回撤分析

内容:
当前回撤率: -6.39%
当前回撤百分位: 62.4%
最大回撤: -21.12%
平均回撤: -8.03%

买入建议: 观望
风险评估: 中等风险
理由: 当前回撤水平一般，建议继续观察
```

## 数据说明

### 缓存机制

- 基金数据按日期缓存，每天自动更新
- 基金名称自动查询并持久化存储
- 旧缓存文件自动清理

### 支持的基金

支持所有在东方财富可查询的公募基金，包括：
- 股票型基金
- 混合型基金  
- 债券型基金
- 指数型基金

## 定时运行

### 使用crontab（Linux/Mac）

每天上午9点自动运行：

```bash
crontab -e
# 添加以下行
0 9 * * * cd /path/to/stock && python main.py
```

### 使用任务计划程序（Windows）

1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器为每日9:00
4. 操作设置为运行Python脚本

## 注意事项

⚠️ **重要提醒**
- 本工具仅供投资参考，不构成投资建议
- 投资有风险，决策需谨慎
- 建议结合其他分析方法综合判断

🔧 **技术说明**
- 数据来源于akshare，依赖网络连接
- 建议在股市开盘时间使用，数据更及时
- 首次运行可能较慢，后续会使用缓存加速

## 常见问题

**Q: 基金代码在哪里找？**
A: 在基金公司官网、天天基金网等平台可以查到6位基金代码

**Q: 网络连接失败怎么办？**
A: 检查网络连接，或稍后重试。akshare偶尔会有连接问题

**Q: 如何添加新基金？**
A: 直接在config.json的fund_codes中添加基金代码即可

**Q: 可以修改买入建议的阈值吗？**
A: 可以修改fund/drawdown_analyzer.py中的百分位数阈值

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！