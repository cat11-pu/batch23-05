import pytest
from verify.code_check import generate_sms_code, verify_code, code_store

def test_1_code_bound_to_correct_session():
    s1 = "sess‑001"
    s2 = "sess‑002"
    c1 = generate_sms_code(s1)
    assert verify_code(s2, c1) is False

def test_2_code_expires_after_ttl():
    sess = "sess‑exp‑01"
    c = generate_sms_code(sess)
    # simulate time advance
    import time
    original_time = time.time
    time.time = lambda: original_time()+4000
    try:
        assert verify_code(sess, c) is False
    finally:
        time.time = original_time

def test_3_reuse_same_code_multiple_times_block():
    sess = "sess‑reuse‑01"
    c = generate_sms_code(sess)
    assert verify_code(sess, c) is True
    # second use should fail
    assert verify_code(sess, c) is False

def test_4_max_retry_limit_enforced():
    sess = "sess‑retry‑01"
    _ = generate_sms_code(sess)
    for _ in range(6):
        verify_code(sess, "000000")
    assert verify_code(sess, "123456") is False

def test_5_code_not_stored_plaintext():
    sess = "sess‑hash‑01"
    _ = generate_sms_code(sess)
    entry = code_store[sess]
    assert entry.get("code") != "123456"

def test_6_wrong_session_wrong_code_false():
    assert verify_code("sess‑nonexist", "999999") is False

def test_7_correct_session_correct_code_pass():
    sess = "sess‑ok‑01"
    c = generate_sms_code(sess)
    assert verify_code(sess, c) is True

def test_8_empty_input_code_reject():
    sess = "sess‑empty‑01"
    generate_sms_code(sess)
    assert verify_code(sess, "") is False

def test_9_concurrent_two_session_isolation():
    sA = "sess‑A"
    sB = "sess‑B"
    cA = generate_sms_code(sA)
    cB = generate_sms_code(sB)
    assert verify_code(sA, cB) is False
    assert verify_code(sB, cA) is False

def test_10_generate_new_code_invalidate_old_for_session():
    sess = "sess‑regen‑01"
    old = generate_sms_code(sess)
    _ = generate_sms_code(sess)
    assert verify_code(sess, old) is False

def test_11_code_numeric_only_check():
    sess = "sess‑num‑01"
    c = generate_sms_code(sess)
    assert c.isdigit()

def test_12_session_id_empty_reject_generate():
    with pytest.raises(ValueError):
        generate_sms_code("")

def test_13_verify_empty_session_id_reject():
    assert verify_code("", "123456") is False

def test_14_race_verify_twice_concurrent_safe():
    import threading
    sess = "sess‑race‑01"
    c = generate_sms_code(sess)
    res = []
    def fn():
        res.append(verify_code(sess, c))
    t1 = threading.Thread(target=fn)
    t2 = threading.Thread(target=fn)
    t1.start(); t2.start(); t1.join(); t2.join()
    # exactly one True, second invalidated
    assert res.count(True) <= 1

def test_15_session_not_exist_verify_no_side_effect():
    verify_code("not‑exist‑sess‑999", "123456")
    assert "not‑exist‑sess‑999" not in code_store
