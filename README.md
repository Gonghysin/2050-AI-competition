# -_-

AI助手moudel：
./my_code_repository/AI_helper/yunwu_helper.py

后端：python

前段：vue

TTS：方舟豆包TTS。调用方法:
1. 接口说明
接口地址为 https://openspeech.bytedance.com/api/v1/tts

2. 身份认证
认证方式采用 Bearer Token.

1)需要在请求的 Header 中填入"Authorization":"Bearer;${token}"

注意

Bearer和token使用分号 ; 分隔，替换时请勿保留${}
发送参数文档：https://www.volcengine.com/docs/6561/79823
返回参数文档：https://www.volcengine.com/docs/6561/79823

APPID：5171308068
access token：DMwm_fkqA4lHn9-WhsxnRpbERJRRLSkH
voice type：BV119_streaming

ok