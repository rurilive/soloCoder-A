#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_platform.settings')
django.setup()

from projects.models import Project, ApiGroup
from apis.models import ApiDefinition
from mock_server.models import MockConfig
from test_runner.models import TestCase

def create_test_data():
    print("=" * 50)
    print("创建测试数据...")
    print("=" * 50)
    
    # 1. 创建项目
    print("\n1. 创建项目...")
    project, created = Project.objects.get_or_create(
        name="用户管理系统",
        defaults={
            "description": "用户管理相关的API接口，包括用户CRUD操作、登录认证等",
            "base_url": "https://jsonplaceholder.typicode.com"
        }
    )
    if created:
        print(f"   ✅ 项目创建成功: {project.name}")
    else:
        print(f"   ℹ️ 项目已存在: {project.name}")
    
    # 2. 创建分组
    print("\n2. 创建接口分组...")
    group1, _ = ApiGroup.objects.get_or_create(
        name="用户管理",
        project=project,
        defaults={"description": "用户相关接口"}
    )
    group2, _ = ApiGroup.objects.get_or_create(
        name="认证管理",
        project=project,
        defaults={"description": "认证相关接口"}
    )
    print(f"   ✅ 创建分组: {group1.name}, {group2.name}")
    
    # 3. 创建接口
    print("\n3. 创建接口...")
    
    # 接口1: 获取用户列表
    api1, _ = ApiDefinition.objects.get_or_create(
        name="获取用户列表",
        project=project,
        group=group1,
        defaults={
            "path": "/users",
            "method": "GET",
            "description": "获取所有用户列表",
            "request_params": [
                {"enabled": True, "key": "_page", "value": "1", "description": "页码"},
                {"enabled": True, "key": "_limit", "value": "10", "description": "每页数量"}
            ],
            "request_headers": [
                {"enabled": True, "key": "Content-Type", "value": "application/json", "description": "请求类型"}
            ],
            "response_examples": [
                {
                    "name": "成功响应",
                    "status_code": 200,
                    "body": [
                        {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
                        {"id": 2, "name": "李四", "email": "lisi@example.com"}
                    ]
                }
            ]
        }
    )
    print(f"   ✅ 创建接口: {api1.method} {api1.path} - {api1.name}")
    
    # 接口2: 获取单个用户
    api2, _ = ApiDefinition.objects.get_or_create(
        name="获取用户详情",
        project=project,
        group=group1,
        defaults={
            "path": "/users/{id}",
            "method": "GET",
            "description": "根据ID获取单个用户详情",
            "response_examples": [
                {
                    "name": "成功响应",
                    "status_code": 200,
                    "body": {
                        "id": 1,
                        "name": "张三",
                        "email": "zhangsan@example.com",
                        "phone": "13800138000"
                    }
                }
            ]
        }
    )
    print(f"   ✅ 创建接口: {api2.method} {api2.path} - {api2.name}")
    
    # 接口3: 创建用户
    api3, _ = ApiDefinition.objects.get_or_create(
        name="创建用户",
        project=project,
        group=group1,
        defaults={
            "path": "/users",
            "method": "POST",
            "description": "创建新用户",
            "request_body_type": "json",
            "request_body": {
                "name": "新用户",
                "email": "newuser@example.com",
                "phone": "13800138000"
            },
            "response_examples": [
                {
                    "name": "创建成功",
                    "status_code": 201,
                    "body": {
                        "id": 101,
                        "name": "新用户",
                        "email": "newuser@example.com"
                    }
                }
            ]
        }
    )
    print(f"   ✅ 创建接口: {api3.method} {api3.path} - {api3.name}")
    
    # 接口4: 用户登录
    api4, _ = ApiDefinition.objects.get_or_create(
        name="用户登录",
        project=project,
        group=group2,
        defaults={
            "path": "/auth/login",
            "method": "POST",
            "description": "用户登录认证",
            "request_body_type": "json",
            "request_body": {
                "username": "admin",
                "password": "123456"
            },
            "response_examples": [
                {
                    "name": "登录成功",
                    "status_code": 200,
                    "body": {
                        "code": 0,
                        "message": "登录成功",
                        "data": {
                            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "expires_in": 3600
                        }
                    }
                }
            ]
        }
    )
    print(f"   ✅ 创建接口: {api4.method} {api4.path} - {api4.name}")
    
    # 4. 创建Mock配置
    print("\n4. 创建Mock配置...")
    
    # Mock1: 获取用户列表成功
    mock1, _ = MockConfig.objects.get_or_create(
        name="获取用户列表成功",
        api=api1,
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
    print(f"   ✅ 创建Mock: {mock1.name} (默认)")
    
    # Mock2: 获取用户列表空数据
    mock2, _ = MockConfig.objects.get_or_create(
        name="获取用户列表空数据",
        api=api1,
        defaults={
            "status_code": 200,
            "response_headers": {"Content-Type": "application/json"},
            "response_body": [],
            "delay_ms": 50,
            "is_active": True,
            "is_default": False
        }
    )
    print(f"   ✅ 创建Mock: {mock2.name}")
    
    # Mock3: 登录成功
    mock3, _ = MockConfig.objects.get_or_create(
        name="登录成功",
        api=api4,
        defaults={
            "status_code": 200,
            "response_headers": {"Content-Type": "application/json"},
            "response_body": {
                "code": 0,
                "message": "success",
                "data": {
                    "token": "mock_token_abc123",
                    "user": {
                        "id": 1,
                        "name": "管理员",
                        "role": "admin"
                    }
                }
            },
            "delay_ms": 200,
            "is_active": True,
            "is_default": True
        }
    )
    print(f"   ✅ 创建Mock: {mock3.name}")
    
    # 5. 创建测试用例
    print("\n5. 创建测试用例...")
    
    # 测试用例1: 获取用户列表成功
    tc1, _ = TestCase.objects.get_or_create(
        name="获取用户列表-成功用例",
        api=api1,
        defaults={
            "description": "测试获取用户列表接口返回200状态码",
            "request_params": [
                {"enabled": True, "key": "_page", "value": "1", "description": "页码"},
                {"enabled": True, "key": "_limit", "value": "5", "description": "每页数量"}
            ],
            "expected_status_code": 200,
            "assertions": [
                {
                    "type": "status_code",
                    "expected": 200,
                    "description": "状态码应为200"
                },
                {
                    "type": "response_time",
                    "max_time_ms": 5000,
                    "description": "响应时间应小于5秒"
                }
            ],
            "is_active": True
        }
    )
    print(f"   ✅ 创建测试用例: {tc1.name}")
    
    # 测试用例2: 登录成功
    tc2, _ = TestCase.objects.get_or_create(
        name="用户登录-成功用例",
        api=api4,
        defaults={
            "description": "测试用户登录接口",
            "request_body": {
                "username": "testuser",
                "password": "testpass"
            },
            "expected_status_code": 200,
            "assertions": [
                {
                    "type": "status_code",
                    "expected": 200
                },
                {
                    "type": "contains_text",
                    "text": "token",
                    "description": "响应应包含token"
                }
            ],
            "is_active": True
        }
    )
    print(f"   ✅ 创建测试用例: {tc2.name}")
    
    print("\n" + "=" * 50)
    print("测试数据创建完成！")
    print("=" * 50)
    print(f"""
项目信息:
  - 项目名称: {project.name}
  - 项目ID: {project.id}
  - 基础URL: {project.base_url}

接口统计:
  - 总分组数: {ApiGroup.objects.filter(project=project).count()}
  - 总接口数: {ApiDefinition.objects.filter(project=project).count()}
  - Mock配置数: {MockConfig.objects.filter(api__project=project).count()}
  - 测试用例数: {TestCase.objects.filter(api__project=project).count()}

访问地址:
  - 主页: http://localhost:8765
  - Mock地址示例: http://localhost:8765/mock/users
""")
    
    return project

if __name__ == "__main__":
    create_test_data()
