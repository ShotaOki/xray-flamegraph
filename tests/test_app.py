from project.app import lambda_handler
from .tools import observer
from aws_xray_sdk.core import xray_recorder
import json


@observer
def test_lambda_handler():
    """
    単体試験: 正常系(正しい想定の入力を渡す)
    期待結果: 200が返ること、全ての処理を通ること
    """
    result = lambda_handler(
        {"body": json.dumps({"url": "https://google.co.jp", "value": "abc"})}, {}
    )

    # 実行結果のX-Rayのセグメント情報をJSONで取得する
    current_segment = xray_recorder.current_segment().serialize()
    # 実行済みの処理を検証する
    assert "def lambda_handler" in current_segment
    assert "def validation" in current_segment
    assert "def network_process" in current_segment
    assert "def write_process" in current_segment
    # Network Processの通信先がGoogleであることを検証する
    assert "google.co.jp" in current_segment

    # レスポンスを検証する
    assert result["statusCode"] == 200
    assert result["body"] == "Hello World"


@observer
def test_invalid_parameter():
    """
    単体試験: 準正常系(必須パラメータのない入力を渡す)
    期待結果: 400が返ること、Network以降の処理が通らないこと
    """
    result = lambda_handler({"body": json.dumps({"url": "https://google.co.jp"})}, {})

    # 実行結果のX-Rayのセグメント情報をJSONで取得する
    current_segment = xray_recorder.current_segment().serialize()
    # 実行済みの処理を検証する
    assert "def lambda_handler" in current_segment
    assert "def validation" in current_segment
    # 必須チェックで例外があったことを検証する
    assert "exceptions" in current_segment  # 例外があったことを確認する
    assert "1 validation error for InputClass" in current_segment
    assert "value" in current_segment  # 年齢の項目が誤っている
    assert "Field required" in current_segment  # 必須チェックエラーである
    # ネットワーク通信以降の処理が実行されていないことを検証する
    assert not ("def network_process" in current_segment)
    assert not ("def write_process" in current_segment)

    # レスポンスを検証する
    assert result["statusCode"] == 400
