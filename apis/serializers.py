from rest_framework import serializers
from .models import ApiDefinition, ApiTestHistory
from projects.serializers import ApiGroupSimpleSerializer


class ApiDefinitionSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = ApiDefinition
        fields = [
            'id', 'project', 'project_name', 'group', 'group_name', 'name', 
            'description', 'path', 'method', 'request_params', 'request_headers',
            'request_body', 'request_body_type', 'response_examples', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ApiDefinitionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiDefinition
        fields = ['id', 'name', 'path', 'method']


class ApiTestHistorySerializer(serializers.ModelSerializer):
    api_name = serializers.CharField(source='api.name', read_only=True)

    class Meta:
        model = ApiTestHistory
        fields = [
            'id', 'api', 'api_name', 'request_url', 'request_method', 'request_headers',
            'request_body', 'response_status', 'response_headers', 'response_body',
            'response_time', 'is_success', 'error_message', 
            'environment_id', 'used_environment_name',
            'tested_at'
        ]
        read_only_fields = ['tested_at']
