import csv
import io

from app.diagnostics import RampError


def rows_from(raw, required):
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            text = raw.decode('gb18030')
        except UnicodeDecodeError as exc:
            raise RampError('FILE') from exc
    if text=='':
        raise RampError('EMPTY_FILE')
    if not text.strip():
        raise RampError('BLANK_FILE')
    reader = csv.reader(io.StringIO(text,newline=''),strict=True)
    try:
        header = next(reader)
        if sorted(header)!=sorted(required):
            raise RampError('HEADER')
        line = reader.line_num+1
        for row in reader:
            yield line,header,row
            line = reader.line_num+1
    except csv.Error as exc:
        raise RampError('FILE') from exc
