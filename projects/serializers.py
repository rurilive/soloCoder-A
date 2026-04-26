from rest_framework import serializers
from .models import Project, ApiGroup, Environment, GlobalConfig


class ApiGroupSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = ApiGroup
        fields = ['id', 'project', 'name', 'description', 'parent', 'children', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        children = obj.children.all()
        return ApiGroupSerializer(children, many=True).data


class ApiGroupSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiGroup
        fields = ['id', 'name']


class EnvironmentSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Environment
        fields = ['id', 'project', 'name', 'type', 'type_display', 'host', 'description', 
                  'is_default', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class GlobalConfigSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    auth_type_display = serializers.CharField(source='get_auth_type_display', read_only=True)

    class Meta:
        model = GlobalConfig
        fields = ['id', 'project', 'name', 'type', 'type_display', 'auth_type', 
                  'auth_type_display', 'config_data', 'is_active', 'is_global', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'project']


class ProjectSerializer(serializers.ModelSerializer):
    groups = ApiGroupSimpleSerializer(many=True, read_only=True)
    environments = EnvironmentSerializer(many=True, read_only=True)
    global_configs = GlobalConfigSerializer(many=True, read_only=True)
    api_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    icon_type_display = serializers.CharField(source='get_icon_type_display', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'base_url',
            'status', 'status_display', 'visibility', 'visibility_display',
            'icon_type', 'icon_type_display', 'icon_emoji', 'icon_color', 'icon_image',
            'background_color', 'background_image',
            'groups', 'environments', 'global_configs', 'api_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_api_count(self, obj):
        return obj.apis.count()


class ProjectSimpleSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'base_url',
            'status', 'status_display',
            'icon_type', 'icon_emoji', 'icon_color', 'icon_image',
            'created_at'
        ]
