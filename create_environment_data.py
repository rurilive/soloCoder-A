#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_platform.settings')
django.setup()

from projects.models import Project, Environment, GlobalConfig

def create_environment_data():
    print("=" * 60)
    print("为现有项目创建环境配置和全局配置...")
    print("=" * 60)
    
    projects = Project.objects.all()
    
    for project in projects:
        print(f"\n📦 项目: {project.name}")
        
        # 更新项目图标配置
        project.icon_emoji = '📁'
        project.icon_color = '#1890ff'
        project.save()
        print(f"   ✅ 更新项目图标配置")
        
        # 创建环境配置
        print(f"\n   🌍 创建环境配置:")
        
        env_dev, created = Environment.objects.get_or_create(
            project=project,
            name='开发环境',
            defaults={
                'type': 'development',
                'host': 'http://localhost:3000',
                'description': '本地开发环境',
                'is_default': True,
                'is_active': True
            }
        )
        if created:
            print(f"      ✅ 开发环境 (默认): {env_dev.host}")
        else:
            print(f"      ℹ️  开发环境已存在: {env_dev.host}")
        
        env_test, created = Environment.objects.get_or_create(
            project=project,
            name='测试环境',
            defaults={
                'type': 'testing',
                'host': 'https://test-api.example.com',
                'description': '测试服务器环境',
                'is_default': False,
                'is_active': True
            }
        )
        if created:
            print(f"      ✅ 测试环境: {env_test.host}")
        else:
            print(f"      ℹ️  测试环境已存在: {env_test.host}")
        
        env_prod, created = Environment.objects.get_or_create(
            project=project,
            name='生产环境',
            defaults={
                'type': 'production',
                'host': 'https://api.example.com',
                'description': '生产服务器环境',
                'is_default': False,
                'is_active': True
            }
        )
        if created:
            print(f"      ✅ 生产环境: {env_prod.host}")
        else:
            print(f"      ℹ️  生产环境已存在: {env_prod.host}")
        
        # 创建全局Headers
        print(f"\n   📋 创建全局Headers:")
        
        header_content, created = GlobalConfig.objects.get_or_create(
            project=project,
            name='Content-Type',
            defaults={
                'type': 'header',
                'auth_type': 'none',
                'config_data': {
                    'key': 'Content-Type',
                    'value': 'application/json',
                    'description': '请求内容类型'
                },
                'is_active': True,
                'is_global': True
            }
        )
        if created:
            print(f"      ✅ Content-Type Header")
        else:
            print(f"      ℹ️  Content-Type Header已存在")
        
        header_accept, created = GlobalConfig.objects.get_or_create(
            project=project,
            name='Accept',
            defaults={
                'type': 'header',
                'auth_type': 'none',
                'config_data': {
                    'key': 'Accept',
                    'value': 'application/json',
                    'description': '接受的响应类型'
                },
                'is_active': True,
                'is_global': True
            }
        )
        if created:
            print(f"      ✅ Accept Header")
        else:
            print(f"      ℹ️  Accept Header已存在")
        
        # 创建认证配置
        print(f"\n   🔐 创建认证配置:")
        
        auth_bearer, created = GlobalConfig.objects.get_or_create(
            project=project,
            name='Bearer Token认证',
            defaults={
                'type': 'auth',
                'auth_type': 'bearer',
                'config_data': {
                    'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzgwMDAwMDAwfQ.example',
                    'prefix': 'Bearer',
                    'header_name': 'Authorization'
                },
                'is_active': True,
                'is_global': False
            }
        )
        if created:
            print(f"      ✅ Bearer Token认证")
        else:
            print(f"      ℹ️  Bearer Token认证已存在")
        
        auth_basic, created = GlobalConfig.objects.get_or_create(
            project=project,
            name='Basic Auth认证',
            defaults={
                'type': 'auth',
                'auth_type': 'basic',
                'config_data': {
                    'username': 'admin',
                    'password': 'password123',
                    'header_name': 'Authorization'
                },
                'is_active': False,
                'is_global': False
            }
        )
        if created:
            print(f"      ✅ Basic Auth认证 (禁用)")
        else:
            print(f"      ℹ️  Basic Auth认证已存在")
        
        # 创建环境变量
        print(f"\n   🔧 创建环境变量:")
        
        var_base_url, created = GlobalConfig.objects.get_or_create(
            project=project,
            name='API_BASE_URL',
            defaults={
                'type': 'variable',
                'auth_type': 'none',
                'config_data': {
                    'key': 'API_BASE_URL',
                    'value': 'http://localhost:3000',
                    'description': 'API基础地址'
                },
                'is_active': True,
                'is_global': True
            }
        )
        if created:
            print(f"      ✅ API_BASE_URL 变量")
        else:
            print(f"      ℹ️  API_BASE_URL 变量已存在")
        
        var_timeout, created = GlobalConfig.objects.get_or_create(
            project=project,
            name='REQUEST_TIMEOUT',
            defaults={
                'type': 'variable',
                'auth_type': 'none',
                'config_data': {
                    'key': 'REQUEST_TIMEOUT',
                    'value': '30000',
                    'description': '请求超时时间(ms)'
                },
                'is_active': True,
                'is_global': True
            }
        )
        if created:
            print(f"      ✅ REQUEST_TIMEOUT 变量")
        else:
            print(f"      ℹ️  REQUEST_TIMEOUT 变量已存在")
    
    print("\n" + "=" * 60)
    print("环境配置和全局配置创建完成！")
    print("=" * 60)
    
    # 统计
    total_projects = Project.objects.count()
    total_envs = Environment.objects.count()
    total_configs = GlobalConfig.objects.count()
    
    print(f"\n📊 统计:")
    print(f"   - 项目数: {total_projects}")
    print(f"   - 环境配置数: {total_envs}")
    print(f"   - 全局配置数: {total_configs}")
    
    # 列出所有环境
    print("\n🌍 环境列表:")
    for env in Environment.objects.all():
        default_mark = " (默认)" if env.is_default else ""
        active_mark = " ✅" if env.is_active else " ❌"
        print(f"   [{env.project.name}] {env.name}{default_mark}: {env.host}{active_mark}")
    
    # 列出所有全局配置
    print("\n📋 全局配置列表:")
    for config in GlobalConfig.objects.all():
        type_display = {'header': 'Header', 'auth': '认证', 'variable': '变量'}
        active_mark = " ✅" if config.is_active else " ❌"
        print(f"   [{config.project.name}] [{type_display.get(config.type, config.type)}] {config.name}{active_mark}")

if __name__ == "__main__":
    create_environment_data()
