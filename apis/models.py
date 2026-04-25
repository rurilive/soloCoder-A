from django.db import models
from django.utils import timezone
from projects.models import Project, ApiGroup
import json


class ApiDefinition(models.Model):
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='apis', verbose_name='所属项目')
    group = models.ForeignKey(ApiGroup, on_delete=models.CASCADE, related_name='apis', null=True, blank=True, verbose_name='所属分组')
    name = models.CharField(max_length=200, verbose_name='接口名称')
    description = models.TextField(blank=True, null=True, verbose_name='接口描述')
    path = models.CharField(max_length=500, verbose_name='接口路径')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='GET', verbose_name='请求方法')
    request_params = models.JSONField(default=list, blank=True, verbose_name='请求参数')
    request_headers = models.JSONField(default=list, blank=True, verbose_name='请求头')
    request_body = models.JSONField(default=dict, blank=True, null=True, verbose_name='请求体')
    request_body_type = models.CharField(max_length=50, default='json', choices=[
        ('json', 'JSON'),
        ('form', 'Form Data'),
        ('x-www-form-urlencoded', 'x-www-form-urlencoded'),
        ('raw', 'Raw'),
        ('binary', 'Binary'),
    ], verbose_name='请求体类型')
    response_examples = models.JSONField(default=list, blank=True, verbose_name='响应示例')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '接口定义'
        verbose_name_plural = '接口定义'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.method} {self.path} - {self.name}'


class ApiTestHistory(models.Model):
    api = models.ForeignKey(ApiDefinition, on_delete=models.CASCADE, related_name='test_history', verbose_name='所属接口')
    request_url = models.CharField(max_length=1000, verbose_name='请求URL')
    request_method = models.CharField(max_length=20, verbose_name='请求方法')
    request_headers = models.JSONField(default=dict, verbose_name='请求头')
    request_body = models.TextField(blank=True, null=True, verbose_name='请求体')
    response_status = models.IntegerField(verbose_name='响应状态码')
    response_headers = models.JSONField(default=dict, verbose_name='响应头')
    response_body = models.TextField(blank=True, null=True, verbose_name='响应体')
    response_time = models.FloatField(verbose_name='响应时间(ms)')
    is_success = models.BooleanField(verbose_name='是否成功')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    environment_id = models.IntegerField(blank=True, null=True, verbose_name='使用的环境ID')
    used_environment_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='使用的环境名称')
    tested_at = models.DateTimeField(default=timezone.now, verbose_name='测试时间')

    class Meta:
        verbose_name = '接口测试历史'
        verbose_name_plural = '接口测试历史'
        ordering = ['-tested_at']

    def __str__(self):
        return f'{self.api.name} - {self.tested_at}'
