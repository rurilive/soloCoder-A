#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_platform.settings')
django.setup()

from apis.models import ApiDefinition
from mock_server.models import MockConfig

def create_mock_configs():
    print("=" * 60)
    print("为所有接口创建Mock配置...")
    print("=" * 60)
    
    apis = ApiDefinition.objects.all()
    
    for api in apis:
        existing = MockConfig.objects.filter(api=api, is_default=True).first()
        
        if existing:
            print(f"\nℹ️  接口 [{api.method} {api.path}] 已有默认Mock配置: {existing.name}")
            continue
        
        print(f"\n✅ 为接口 [{api.method} {api.path}] 创建Mock配置...")
        
        # 根据接口类型创建不同的响应
        if api.path == '/users' and api.method == 'GET':
            # 获取用户列表
            mock, created = MockConfig.objects.get_or_create(
                name="获取用户列表成功",
                api=api,
                defaults={
                    "status_code": 200,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": [
                        {"id": 1, "name": "张三", "email": "zhangsan@example.com", "status": "active"},
                        {"id": 2, "name": "李四", "email": "lisi@example.com", "status": "active"},
                        {"id": 3, "name": "王五", "email": "wangwu@example.com", "status": "inactive"}
                    ],
                    "delay_ms": 100,
                    "is_active": True,
                    "is_default": True
                }
            )
            if created:
                print(f"   ✅ 创建成功: {mock.name}")
        
        elif '/users/{id}' in api.path and api.method == 'GET':
            # 获取用户详情
            mock, created = MockConfig.objects.get_or_create(
                name="获取用户详情成功",
                api=api,
                defaults={
                    "status_code": 200,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {
                        "id": 1,
                        "name": "张三",
                        "email": "zhangsan@example.com",
                        "phone": "13800138000",
                        "address": "北京市朝阳区",
                        "company": "科技公司",
                        "website": "www.zhangsan.com"
                    },
                    "delay_ms": 80,
                    "is_active": True,
                    "is_default": True
                }
            )
            if created:
                print(f"   ✅ 创建成功: {mock.name}")
            
            # 创建一个404的Mock
            mock_404, _ = MockConfig.objects.get_or_create(
                name="用户不存在",
                api=api,
                defaults={
                    "status_code": 404,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {
                        "code": 404,
                        "message": "用户不存在",
                        "errors": ["该用户ID不存在"]
                    },
                    "delay_ms": 50,
                    "is_active": True,
                    "is_default": False
                }
            )
            print(f"   ✅ 创建成功: {mock_404.name}")
        
        elif api.path == '/users' and api.method == 'POST':
            # 创建用户
            mock, created = MockConfig.objects.get_or_create(
                name="创建用户成功",
                api=api,
                defaults={
                    "status_code": 201,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {
                        "code": 0,
                        "message": "创建成功",
                        "data": {
                            "id": 101,
                            "name": "新用户",
                            "email": "newuser@example.com",
                            "created_at": "2026-04-25T08:00:00Z"
                        }
                    },
                    "delay_ms": 150,
                    "is_active": True,
                    "is_default": True
                }
            )
            if created:
                print(f"   ✅ 创建成功: {mock.name}")
            
            # 创建一个400的Mock
            mock_400, _ = MockConfig.objects.get_or_create(
                name="参数错误",
                api=api,
                defaults={
                    "status_code": 400,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {
                        "code": 400,
                        "message": "参数验证失败",
                        "errors": ["邮箱格式不正确", "用户名不能为空"]
                    },
                    "delay_ms": 50,
                    "is_active": True,
                    "is_default": False
                }
            )
            print(f"   ✅ 创建成功: {mock_400.name}")
        
        elif api.path == '/auth/login' and api.method == 'POST':
            # 登录
            mock, created = MockConfig.objects.get_or_create(
                name="登录成功",
                api=api,
                defaults={
                    "status_code": 200,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {
                        "code": 0,
                        "message": "登录成功",
                        "data": {
                            "token": "mock_token_abc123_xyz789",
                            "refresh_token": "refresh_token_abc123",
                            "expires_in": 3600,
                            "user": {
                                "id": 1,
                                "name": "管理员",
                                "email": "admin@example.com",
                                "role": "admin",
                                "avatar": "https://example.com/avatar.png"
                            }
                        }
                    },
                    "delay_ms": 200,
                    "is_active": True,
                    "is_default": True
                }
            )
            if created:
                print(f"   ✅ 创建成功: {mock.name}")
            else:
                print(f"   ℹ️  已存在: {mock.name}")
            
            # 创建一个401的Mock
            mock_401, _ = MockConfig.objects.get_or_create(
                name="登录失败-密码错误",
                api=api,
                defaults={
                    "status_code": 401,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {
                        "code": 401,
                        "message": "用户名或密码错误",
                        "errors": ["请检查您的用户名和密码"]
                    },
                    "delay_ms": 100,
                    "is_active": True,
                    "is_default": False
                }
            )
            print(f"   ✅ 创建成功: {mock_401.name}")
        
        else:
            # 默认Mock
            mock, created = MockConfig.objects.get_or_create(
                name=f"{api.name}成功",
                api=api,
                defaults={
                    "status_code": 200,
                    "response_headers": {"Content-Type": "application/json"},
                    "response_body": {
                        "code": 0,
                        "message": "success",
                        "data": {}
                    },
                    "delay_ms": 100,
                    "is_active": True,
                    "is_default": True
                }
            )
            if created:
                print(f"   ✅ 创建成功: {mock.name}")
    
    print("\n" + "=" * 60)
    print("Mock配置创建完成！")
    print("=" * 60)
    
    # 统计
    total_apis = ApiDefinition.objects.count()
    total_mocks = MockConfig.objects.count()
    print(f"\n📊 统计:")
    print(f"   - 总接口数: {total_apis}")
    print(f"   - 总Mock配置数: {total_mocks}")
    
    # 列出所有Mock
    print("\n📋 Mock配置列表:")
    apis = ApiDefinition.objects.all()
    for api in apis:
        mocks = MockConfig.objects.filter(api=api)
        print(f"\n   {api.method} {api.path} - {api.name}:")
        for mock in mocks:
            default_mark = " (默认)" if mock.is_default else ""
            print(f"      - {mock.name} [状态码: {mock.status_code}, 延迟: {mock.delay_ms}ms]{default_mark}")

if __name__ == "__main__":
    create_mock_configs()
