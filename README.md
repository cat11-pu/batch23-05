# GSB Bugfix Task
## 题面
短信验证码校验会话状态存在绕过缺陷：验证码不绑定会话id、验证码永不失效、可无限重试、验证码明文存储、同一个验证码可复用多次；verify/code_check.py 是核心，tests/test_sms_code.py 15个红。要修的是：验证码绑定会话标识、设置过期时间、限制最大重试次数、哈希存储验证码、单次校验后立即作废。

## 运行方式
```bash
python -m pytest tests -q
```

## 校验结果

`verify_code(session_id, input_code)` 保持原有布尔返回。需要区分失败原因时使用
`verify_code_result(session_id, input_code)`，其状态包括 `ok`、`invalid`、
`not_found`、`expired`、`already_used`、`too_many_attempts` 和
`invalid_session`。

## 平台字段

所属领域：安全
子方向：漏洞检测与攻防
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：无外部依赖
