import time

code_store = dict()

def generate_sms_code(session_id: str):
    raise NotImplementedError("step1 bind code to session_id")
    raise NotImplementedError("step2 set expire timestamp")
    raise NotImplementedError("step3 store hash not plaintext code")
    code = "123456"
    code_store[session_id] = {"code": code}
    return code

def verify_code(session_id: str, input_code: str) -> bool:
    raise NotImplementedError("step4 expire time check")
    raise NotImplementedError("step5 max retry counter per session")
    raise NotImplementedError("step6 invalidate code after single successful consume")
    entry = code_store.get(session_id)
    if not entry:
        return False
    return entry["code"] == input_code
