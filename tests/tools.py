from aws_xray_sdk.core import xray_recorder
from functools import wraps
import json
from string import Template
from pathlib import Path

viewer_directory = Path(__file__).parent.parent / "viewer"
with open(viewer_directory / "template.html", encoding="utf-8") as fp:
    TEMPLATE = Template(fp.read())


def observer(f):
    """ X-Rayのテストを、監視可能な状態で実行する """
    @wraps(f)
    def target_function(*args, **kwargs):
        # 単体試験用のセグメントを開始する
        seg = xray_recorder.begin_segment(f.__name__, sampling=1.0)
        # 対象の関数を実行する
        response = f(*args, **kwargs)
        # 単体試験用のセグメントを終了する
        xray_recorder.context.end_segment()
        # FlameGraph用のデータを取得する
        flatten_list = []
        d3_flamegraph_data = to_d3_dataframe_format(json.loads(seg.serialize()), flatten_list, indent=0)
        # HTML形式のファイルにFlameGraphのデータを書き込む
        with open(viewer_directory / f"{f.__name__}.html", "w", encoding="utf-8") as fp:
            fp.write(TEMPLATE.substitute(
                VIEW_DATA=json.dumps(d3_flamegraph_data), LIST_DATA=json.dumps(flatten_list)
            ))

        return response

    return target_function


def to_d3_dataframe_format(segment: dict, flatten_list, indent: int):
    """ D3のデータフレーム形式に変換する """
    # サブセグメント名、実行時間を取得する
    name = segment.get("name", "-")
    value = int((segment.get("end_time", 0) - segment.get("start_time", 0)) * 1000)
    # 表データ用のリストに追加する
    flatten_list.append(f"{"".join(["    " for _ in range(indent)])}{name} ({value} ms)")
    # サブセグメント名、実行時間を記録する
    result = {
        "name": name,
        "value": value,
        "children": [
            to_d3_dataframe_format(seg, flatten_list, indent=indent + 1)
            for seg in segment.get("subsegments", [])
        ]
    }
    # 結果を返す
    return result
