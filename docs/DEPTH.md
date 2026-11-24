# 深度登记 机坪加油回执台

中型项目。机坪油务班组用计量、回执及库存原件逐票复算并归档异常证据。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 仪表与回执采信 | 校验三联单原件 | `GET/POST /api/intake` | `app/intake/evidence.py` `app/intake/reader.py` | `tests/test_intake.py` `tests/test_csv_shapes.py` |
| M2 罐车量程配置选版 | 决定起止版本 | `GET/POST /api/versions` | `app/meters/select.py` `app/meters/catalog.py` | `tests/test_versions.py` |
| M3 两端读数重建 | 区分回卷和人为归零 | `GET/POST /api/readings` | `app/readings/delta.py` `app/readings/rebuild.py` | `tests/test_readings.py` |
| M4 密度换算与误差带 | 复算油温订正和容差 | `GET/POST /api/mass` | `app/conversion/standard.py` `app/conversion/calculate.py` | `tests/test_mass.py` |
| M5 库存和签单对账 | 核对罐车与逐票签收差额 | `GET/POST /api/balance` | `app/settlement/inventory.py` `app/settlement/receipts.py` `app/settlement/report.py` | `tests/test_settlement.py` |
| M6 批次留档复跑 | 保存清单与各阶段快照 | `POST /api/shifts` | `app/ledger/replay.py` `app/ledger/sqlite_book.py` | `tests/test_replay.py` |
| M7 加注证据签发 | 固定签发证据并复验摘要 | `POST /api/shifts/{batch}/sign` | `app/dispatch/signatures.py` `app/dispatch/document.py` | `tests/test_dispatch.py` |

## 陷阱登记

| TRAP | 现象 | 朴素实现会怎样 | 本项目处理 | 处理位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-02 | 票头 BOM | 首列读错 | 带 BOM 解码 | `app/intake/reader.py` | `tests/test_intake.py::test_unicode_bom_preserves_ticket_column` |
| TRAP-04 | 文件拼接重复表头 | 多算一笔票 | 计分段保留行号 | `app/intake/evidence.py` | `tests/test_intake.py::test_repeated_header_separates_originals` |
| TRAP-05 | 尾部余列 | 票号原件被污染 | 行独立隔离 | `app/intake/evidence.py` | `tests/test_intake.py::test_extra_field_does_not_pollute_original` |
| TRAP-07 | 仪表缺测哨兵 | 按零读数回卷 | 哨兵判缺证 | `app/intake/schemas.py` | `tests/test_intake.py::test_missing_instrument_mark_not_zero` |
| TRAP-10 | 微量票小数相减 | 整克数丢尾差 | Decimal 差分并用整数克累加 | `app/conversion/standard.py` | `tests/test_mass.py::test_decimal_small_tickets_sum_exactly` |
| TRAP-14 | 签收联冲突 | 后写覆盖前件 | 原件留痕且两件隔离 | `app/intake/evidence.py` | `tests/test_intake.py::test_conflicting_receipts_are_both_retained_as_evidence` |
| TRAP-15 | 密度混用 | 吨位严重误算 | 归一单位并做油种范围校验 | `app/conversion/standard.py` | `tests/test_mass.py::test_density_units_normalized` |
| TRAP-23 | 票据正好位于切换点 | 重叠版本被算两次 | 左闭右开，扫描票内切点 | `app/meters/select.py` | `tests/test_versions.py::test_expiry_is_right_open` |
| TRAP-25 | 多版本同时生效 | 配置文件顺序决定 | 高修订胜出，并列挂起 | `app/meters/select.py` | `tests/test_versions.py::test_overlap_higher_version_selected` |

样例包含 40 原件、35 采信、4 隔离和 1 重复。两辆库存可核车辆的 510000 g 等于 247600 g 发放、261000 g 期末与 1400 g 差额。另有 FT-23 的 16000 g 已核计量，库存缺期末锚点。
