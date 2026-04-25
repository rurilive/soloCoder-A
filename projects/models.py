from django.db import models
from django.utils import timezone


class Project(models.Model):
    STATUS_CHOICES = [
        ('active', '进行中'),
        ('archived', '已归档'),
        ('draft', '草稿'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', '公开'),
        ('private', '私有'),
    ]
    
    ICON_TYPE_CHOICES = [
        ('emoji', 'Emoji'),
        ('color', '颜色'),
        ('image', '图片'),
    ]

    name = models.CharField(max_length=200, verbose_name='项目名称')
    description = models.TextField(blank=True, null=True, verbose_name='项目描述')
    base_url = models.CharField(max_length=500, blank=True, null=True, verbose_name='基础URL')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='项目状态')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private', verbose_name='可见性')
    
    icon_type = models.CharField(max_length=20, choices=ICON_TYPE_CHOICES, default='emoji', verbose_name='图标类型')
    icon_emoji = models.CharField(max_length=10, default='📁', verbose_name='Emoji图标')
    icon_color = models.CharField(max_length=20, default='#1890ff', verbose_name='图标颜色')
    icon_image = models.CharField(max_length=500, blank=True, null=True, verbose_name='图标图片URL')
    
    background_color = models.CharField(max_length=20, blank=True, null=True, verbose_name='背景颜色')
    background_image = models.CharField(max_length=500, blank=True, null=True, verbose_name='背景图片URL')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Environment(models.Model):
    TYPE_CHOICES = [
        ('development', '开发环境'),
        ('testing', '测试环境'),
        ('staging', '预发布环境'),
        ('production', '生产环境'),
        ('custom', '自定义'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='environments', verbose_name='所属项目')
    name = models.CharField(max_length=100, verbose_name='环境名称')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='development', verbose_name='环境类型')
    host = models.CharField(max_length=500, verbose_name='Host地址')
    description = models.TextField(blank=True, null=True, verbose_name='环境描述')
    
    is_default = models.BooleanField(default=False, verbose_name='是否默认环境')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '环境配置'
        verbose_name_plural = '环境配置'
        ordering = ['-is_default', 'created_at']
        unique_together = ['project', 'name']

    def __str__(self):
        return f'{self.name} ({self.host})'
    
    def save(self, *args, **kwargs):
        if self.is_default:
            Environment.objects.filter(project=self.project).update(is_default=False)
        super().save(*args, **kwargs)


class GlobalConfig(models.Model):
    TYPE_CHOICES = [
        ('header', '全局Headers'),
        ('auth', '认证配置'),
        ('variable', '环境变量'),
    ]
    
    AUTH_TYPE_CHOICES = [
        ('none', '无认证'),
        ('bearer', 'Bearer Token'),
        ('basic', 'Basic Auth'),
        ('apikey', 'API Key'),
        ('oauth2', 'OAuth 2.0'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='global_configs', verbose_name='所属项目')
    name = models.CharField(max_length=100, verbose_name='配置名称')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='配置类型')
    
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPE_CHOICES, default='none', verbose_name='认证类型')
    config_data = models.JSONField(default=dict, verbose_name='配置数据')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_global = models.BooleanField(default=False, verbose_name='是否全局生效')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '全局配置'
        verbose_name_plural = '全局配置'
        ordering = ['type', '-is_global', 'created_at']

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'


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
