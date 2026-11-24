REASONS = {
    'BUNDLE':'请传入三份 CSV 或使用样例', 'SAMPLE':'样例不存在', 'FILE':'文件解码或解析失败',
    'HEADER':'表头字段不匹配', 'EMPTY_FILE':'文件为空', 'BLANK_FILE':'文件只有空白', 'HEADER_ONLY':'文件只有表头',
    'WIDTH':'记录列数不符', 'SENTINEL':'关键值缺失', 'MALFORMED':'值或格式无效', 'BLANK_ROW':'空白行',
    'CONFLICT':'同键原件数值冲突', 'NO_VERSION':'当班没有适用量程', 'VERSION_TIE':'量程出现同级有效版本',
    'VERSION_SPLIT':'起止读数跨量程选版边界', 'METER_BOUNDS':'读数超出量程', 'RESET':'人工归零，读数不能直接相减',
    'BAD_WRAP':'回卷证据与量程边界不符', 'REVERSE':'负差缺少回卷证据', 'DECLARED_LIMIT':'发油量超过单票上限',
    'DENSITY_UNIT':'密度单位未登记', 'DENSITY_RANGE':'换算后密度超出油品允许区间',
    'TEMPERATURE':'油温超出模型范围', 'FUEL':'未配置该油种', 'NO_RECEIPT':'缺少签收回执',
    'SIGN_TRUCK':'计量票与回执车号不一致', 'NO_METER':'签收缺少可计发放票', 'SIGN_DIFF':'签收差超过允许误差',
    'STOCK_ANCHORS':'缺少唯一的期初或期末库存', 'NO_BATCH':'没有此交班归档', 'NOT_SIGNED':'证据单尚未签发',
}


class RampError(ValueError):
    def __init__(self, code, status=422):
        super().__init__(REASONS[code])
        self.code, self.status = code, status


def detail(code):
    return {'code':code,'note':REASONS[code]}
