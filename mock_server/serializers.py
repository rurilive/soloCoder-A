from rest_framework import serializers
from .models import MockConfig, MockLog


class MockConfigSerializer(serializers.ModelSerializer):
    api_name = serializers.CharField(source='api.name', read_only=True)
    api_path = serializers.CharField(source='api.path', read_only=True)
    api_method = serializers.CharField(source='api.method', read_only=True)

    class Meta:
        model = MockConfig
        fields = [
            'id', 'api', 'api_name', 'api_path', 'api_method', 'name', 
            'status_code', 'response_headers', 'response_body', 'response_body_raw',
            'delay_ms', 'is_active', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class MockLogSerializer(serializers.ModelSerializer):
    api_name = serializers.CharField(source='api.name', read_only=True)
    mock_config_name = serializers.CharField(source='mock_config.name', read_only=True, default=None)

    class Meta:
        model = MockLog
        fields = [
            'id', 'mock_config', 'mock_config_name', 'api', 'api_name',
            'request_method', 'request_path', 'request_headers', 'request_body',
            'request_query_params', 'response_status', 'response_headers',
            'response_body', 'created_at'
        ]
        read_only_fields = ['created_at']
