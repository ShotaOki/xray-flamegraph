from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from pydantic import BaseModel
import time
import requests

xray_recorder.configure(service="Application")
patch_all()


class InputClass(BaseModel):
    value: str
    url: str


@xray_recorder.capture("def validation")
def validation(event):
    """入力チェック、値の検証"""
    time.sleep(0.1)
    return InputClass.model_validate_json(event["body"])


@xray_recorder.capture("def network_process")
def network_process(input: InputClass):
    """通信処理"""
    res = requests.get(input.url)
    time.sleep(0.4)
    return res.text


@xray_recorder.capture("def write_process")
def write_process(result):
    """取得したファイルの書き込み処理"""
    time.sleep(0.6)


@xray_recorder.capture("def lambda_handler")
def lambda_handler(event, context):
    """Lambdaのエントリポイント"""
    try:
        # 入力を検証する
        input = validation(event)
    except Exception:
        # 入力チェックエラーなら400を返す
        return {
            "statusCode": 400,
            "body": "Invalid input",
        }

    # ネットワークの処理
    result = network_process(input)
    # ファイルへの書き込み処理
    write_process(result)
    # 結果を返す
    return {
        "statusCode": 200,
        "body": "Hello World",
    }
