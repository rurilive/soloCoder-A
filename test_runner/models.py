from django.db import models
from django.utils import timezone
from projects.models import Project, ApiGroup
from apis.models import ApiDefinition


class TestCase(models.Model):
    api = models.ForeignKey(ApiDefinition, on_delete=models.CASCADE, related_name='test_cases', verbose_name='所属接口')
    name = models.CharField(max_length=200, verbose_name='测试用例名称')
    description = models.TextField(blank=True, null=True, verbose_name='用例描述')
    request_params = models.JSONField(default=list, blank=True, verbose_name='请求参数')
    request_headers = models.JSONField(default=list, blank=True, verbose_name='请求头')
    request_body = models.JSONField(default=dict, blank=True, null=True, verbose_name='请求体')
    expected_status_code = models.IntegerField(default=200, verbose_name='期望状态码')
    expected_response = models.JSONField(default=dict, blank=True, null=True, verbose_name='期望响应')
    expected_response_schema = models.JSONField(default=dict, blank=True, null=True, verbose_name='期望响应Schema')
    assertions = models.JSONField(default=list, blank=True, verbose_name='断言规则')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.api.name}'


class TestSuite(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_suites', verbose_name='所属项目')
    groups = models.ManyToManyField(ApiGroup, blank=True, related_name='test_suites', verbose_name='包含分组')
    apis = models.ManyToManyField(ApiDefinition, blank=True, related_name='test_suites', verbose_name='包含接口')
    name = models.CharField(max_length=200, verbose_name='测试套件名称')
    description = models.TextField(blank=True, null=True, verbose_name='套件描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '测试套件'
        verbose_name_plural = '测试套件'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TestRun(models.Model):
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_runs', verbose_name='所属项目')
    test_suite = models.ForeignKey(TestSuite, on_delete=models.SET_NULL, null=True, blank=True, related_name='runs', verbose_name='测试套件')
    name = models.CharField(max_length=200, verbose_name='测试运行名称')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='运行状态')
    total_tests = models.IntegerField(default=0, verbose_name='总测试数')
    passed_tests = models.IntegerField(default=0, verbose_name='通过数')
    failed_tests = models.IntegerField(default=0, verbose_name='失败数')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    duration_ms = models.FloatField(default=0, verbose_name='运行时长(ms)')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        verbose_name = '测试运行'
        verbose_name_plural = '测试运行'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.get_status_display()}'


class TestResult(models.Model):
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='results', verbose_name='测试运行')
    test_case = models.ForeignKey(TestCase, on_delete=models.SET_NULL, null=True, blank=True, related_name='results', verbose_name='测试用例')
    api = models.ForeignKey(ApiDefinition, on_delete=models.CASCADE, related_name='test_results', verbose_name='所属接口')
    name = models.CharField(max_length=200, verbose_name='测试名称')
    is_passed = models.BooleanField(verbose_name='是否通过')
    request_url = models.CharField(max_length=1000, verbose_name='请求URL')
    request_method = models.CharField(max_length=20, verbose_name='请求方法')
    request_headers = models.JSONField(default=dict, verbose_name='请求头')
    request_body = models.TextField(blank=True, null=True, verbose_name='请求体')
    response_status = models.IntegerField(verbose_name='响应状态码')
    response_headers = models.JSONField(default=dict, verbose_name='响应头')
    response_body = models.TextField(blank=True, null=True, verbose_name='响应体')
    response_time = models.FloatField(verbose_name='响应时间(ms)')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    assertion_results = models.JSONField(default=list, blank=True, verbose_name='断言结果')
    executed_at = models.DateTimeField(default=timezone.now, verbose_name='执行时间')

    class Meta:
        verbose_name = '测试结果'
        verbose_name_plural = '测试结果'
        ordering = ['-executed_at']

    def __str__(self):
        return f'{self.name} - {"通过" if self.is_passed else "失败"}'
