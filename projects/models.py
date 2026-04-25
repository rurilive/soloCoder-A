from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name='项目名称')
    description = models.TextField(blank=True, null=True, verbose_name='项目描述')
    base_url = models.CharField(max_length=500, blank=True, null=True, verbose_name='基础URL')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ApiGroup(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='groups', verbose_name='所属项目')
    name = models.CharField(max_length=200, verbose_name='分组名称')
    description = models.TextField(blank=True, null=True, verbose_name='分组描述')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='父分组')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '接口分组'
        verbose_name_plural = '接口分组'
        ordering = ['name']

    def __str__(self):
        return self.name
