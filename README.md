# 机坪加油回执台

机坪油务核算员查对计量票、罐车结存和签收联。工作台保留三联单原始行，以量程版本重建读数和回卷，再按油温与密度折算逐票质量。车辆库存勾稽单独显示未闭合车辆。

运行 `docker compose up --build` 后访问 `http://localhost:18469/`。本机安装 `requirements.txt`，再运行 `flask --app app.main:create_app run --port 18469`。用 `pytest -q` 验证。`FUEL_BOOK` 指定 SQLite 路径，切换为空档案文件可初始化新账簿。

从夜班三联单打开仪表回卷证据，比较真实回卷和人工归零，再查看库存差额及签收差。交班页可归档样例或填写完整三份 CSV。前五项 API 支持 GET 调样例和 POST 提交 `tickets`、`receipts`、`stock` 三份 CSV 文本字段。归档后可签发一份 JSON 证据单。

[换算及字段定义](docs/DATA-DICTIONARY.md) · [业务模块和回归](docs/DEPTH.md)
