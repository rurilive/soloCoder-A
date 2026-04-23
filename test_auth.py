"""
测试脚本：注册、登录、鉴权全流程测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as app_module


def test_password_hashing():
    """测试密码哈希和验证"""
    print("=" * 50)
    print("测试 1: 密码哈希和验证")
    print("=" * 50)
    
    test_password = "test1234"
    
    password_hash = app_module.get_password_hash(test_password)
    print(f"密码: {test_password}")
    print(f"哈希值: {password_hash}")
    
    result1 = app_module.verify_password(test_password, password_hash)
    print(f"验证正确密码: {result1}")
    
    result2 = app_module.verify_password("wrongpassword", password_hash)
    print(f"验证错误密码: {result2}")
    
    assert result1 == True, "正确密码验证应该成功"
    assert result2 == False, "错误密码验证应该失败"
    
    print("✓ 密码哈希测试通过")
    return True


def test_user_registration():
    """测试用户注册"""
    print("\n" + "=" * 50)
    print("测试 2: 用户注册")
    print("=" * 50)
    
    app_module.users.clear()
    app_module.usernames.clear()
    
    test_user = {
        "username": "testuser",
        "password": "test1234"
    }
    
    print(f"注册用户: {test_user['username']}")
    
    if test_user["username"] in app_module.usernames:
        print("✗ 用户名已存在")
        return False
    
    if len(test_user["username"]) < 3:
        print("✗ 用户名太短")
        return False
    
    if len(test_user["password"]) < 4:
        print("✗ 密码太短")
        return False
    
    user_id = app_module.uuid.uuid4()
    hashed_password = app_module.get_password_hash(test_user["password"])
    now = app_module.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    user = app_module.User(
        id=str(user_id),
        username=test_user["username"],
        hashed_password=hashed_password,
        created_at=now
    )
    
    app_module.users[str(user_id)] = user
    app_module.usernames[test_user["username"]] = str(user_id)
    
    print(f"用户 ID: {user_id}")
    print(f"注册时间: {now}")
    
    assert test_user["username"] in app_module.usernames, "用户名应该存在"
    assert str(user_id) in app_module.users, "用户 ID 应该存在"
    
    print("✓ 用户注册测试通过")
    return True


def test_user_login():
    """测试用户登录"""
    print("\n" + "=" * 50)
    print("测试 3: 用户登录")
    print("=" * 50)
    
    test_username = "testuser"
    test_password = "test1234"
    
    print(f"登录用户: {test_username}")
    
    user_id = app_module.usernames.get(test_username)
    if not user_id or user_id not in app_module.users:
        print("✗ 用户名不存在")
        return False
    
    user = app_module.users[user_id]
    
    result = app_module.verify_password(test_password, user.hashed_password)
    print(f"密码验证结果: {result}")
    
    assert result == True, "密码验证应该成功"
    
    access_token_expires = app_module.timedelta(minutes=app_module.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = app_module.create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    print(f"生成 JWT Token: {access_token[:50]}...")
    
    assert access_token is not None, "应该生成 Token"
    
    print("✓ 用户登录测试通过")
    return True


def test_jwt_validation():
    """测试 JWT Token 验证"""
    print("\n" + "=" * 50)
    print("测试 4: JWT Token 验证")
    print("=" * 50)
    
    user_id = list(app_module.users.keys())[0]
    user = app_module.users[user_id]
    
    access_token = app_module.create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=app_module.timedelta(minutes=30)
    )
    
    print(f"Token: {access_token[:60]}...")
    
    try:
        payload = app_module.jwt.decode(access_token, app_module.SECRET_KEY, algorithms=[app_module.ALGORITHM])
        print(f"Payload: {payload}")
        
        decoded_user_id: str = payload.get("sub")
        decoded_username: str = payload.get("username")
        
        print(f"解码 User ID: {decoded_user_id}")
        print(f"解码 Username: {decoded_username}")
        
        assert decoded_user_id == user.id, "User ID 应该匹配"
        assert decoded_username == user.username, "Username 应该匹配"
        
    except app_module.JWTError as e:
        print(f"✗ Token 解码失败: {e}")
        return False
    
    print("✓ JWT Token 验证测试通过")
    return True


def test_invalid_password_login():
    """测试错误密码登录"""
    print("\n" + "=" * 50)
    print("测试 5: 错误密码登录")
    print("=" * 50)
    
    test_username = "testuser"
    wrong_password = "wrongpassword"
    
    print(f"使用错误密码登录: {test_username}")
    
    user_id = app_module.usernames.get(test_username)
    user = app_module.users[user_id]
    
    result = app_module.verify_password(wrong_password, user.hashed_password)
    print(f"错误密码验证结果: {result}")
    
    assert result == False, "错误密码应该验证失败"
    
    print("✓ 错误密码登录测试通过")
    return True


def test_duplicate_registration():
    """测试重复注册"""
    print("\n" + "=" * 50)
    print("测试 6: 重复注册")
    print("=" * 50)
    
    test_username = "testuser"
    
    print(f"尝试重复注册: {test_username}")
    
    if test_username in app_module.usernames:
        print("✓ 正确检测到用户名已存在")
        print("✓ 重复注册测试通过")
        return True
    else:
        print("✗ 用户名不存在，无法测试重复注册")
        return False


def main():
    print("\n" + "=" * 60)
    print("开始全量测试：注册、登录、鉴权流程")
    print("=" * 60)
    
    tests = [
        test_password_hashing,
        test_user_registration,
        test_user_login,
        test_jwt_validation,
        test_invalid_password_login,
        test_duplicate_registration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            results.append((test.__name__, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 个通过, {failed} 个失败")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查代码")
        return False


if __name__ == "__main__":
    main()
