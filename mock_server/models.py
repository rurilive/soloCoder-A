from django.db import models
from django.utils import timezone
from apis.models import ApiDefinition


class MockConfig(models.Model):
    api = models.ForeignKey(ApiDefinition, on_delete=models.CASCADE, related_name='mock_configs', verbose_name='所属接口')
    name = models.CharField(max_length=200, verbose_name='Mock配置名称')
    status_code = models.IntegerField(default=200, verbose_name='响应状态码')
    response_headers = models.JSONField(default=dict, blank=True, verbose_name='响应头')
    response_body = models.JSONField(default=dict, blank=True, null=True, verbose_name='响应体')
    response_body_raw = models.TextField(blank=True, null=True, verbose_name='原始响应体')
    delay_ms = models.IntegerField(default=0, verbose_name='延迟时间(ms)')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'Mock配置'
        verbose_name_plural = 'Mock配置'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.name} - {self.api.name}'


class MockLog(models.Model):
    mock_config = models.ForeignKey(MockConfig, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs', verbose_name='Mock配置')
    api = models.ForeignKey(ApiDefinition, on_delete=models.CASCADE, related_name='mock_logs', verbose_name='所属接口')
    request_method = models.CharField(max_length=20, verbose_name='请求方法')
    request_path = models.CharField(max_length=1000, verbose_name='请求路径')
    request_headers = models.JSONField(default=dict, verbose_name='请求头')
    request_body = models.TextField(blank=True, null=True, verbose_name='请求体')
    request_query_params = models.JSONField(default=dict, verbose_name='查询参数')
    response_status = models.IntegerField(verbose_name='响应状态码')
    response_headers = models.JSONField(default=dict, verbose_name='响应头')
    response_body = models.TextField(blank=True, null=True, verbose_name='响应体')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='调用时间')

    class Meta:
        verbose_name = 'Mock调用日志'
        verbose_name_plural = 'Mock调用日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.request_method} {self.request_path} - {self.created_at}'
