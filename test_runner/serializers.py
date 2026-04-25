from rest_framework import serializers
from .models import TestCase, TestSuite, TestRun, TestResult
from apis.serializers import ApiDefinitionSimpleSerializer


class TestCaseSerializer(serializers.ModelSerializer):
    api_name = serializers.CharField(source='api.name', read_only=True)
    api_path = serializers.CharField(source='api.path', read_only=True)
    api_method = serializers.CharField(source='api.method', read_only=True)

    class Meta:
        model = TestCase
        fields = [
            'id', 'api', 'api_name', 'api_path', 'api_method', 'name', 
            'description', 'request_params', 'request_headers', 'request_body',
            'expected_status_code', 'expected_response', 'expected_response_schema',
            'assertions', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TestSuiteSerializer(serializers.ModelSerializer):
    groups_info = serializers.SerializerMethodField()
    apis_info = serializers.SerializerMethodField()

    class Meta:
        model = TestSuite
        fields = [
            'id', 'project', 'groups', 'groups_info', 'apis', 'apis_info',
            'name', 'description', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_groups_info(self, obj):
        return [{'id': g.id, 'name': g.name} for g in obj.groups.all()]

    def get_apis_info(self, obj):
        return [{'id': a.id, 'name': a.name, 'path': a.path, 'method': a.method} for a in obj.apis.all()]


class TestRunSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    test_suite_name = serializers.CharField(source='test_suite.name', read_only=True, default=None)
    pass_rate = serializers.SerializerMethodField()

    class Meta:
        model = TestRun
        fields = [
            'id', 'project', 'project_name', 'test_suite', 'test_suite_name',
            'name', 'status', 'total_tests', 'passed_tests', 'failed_tests',
            'pass_rate', 'started_at', 'completed_at', 'duration_ms', 'created_at'
        ]
        read_only_fields = ['created_at', 'started_at', 'completed_at']

    def get_pass_rate(self, obj):
        if obj.total_tests == 0:
            return 0
        return round((obj.passed_tests / obj.total_tests) * 100, 2)


class TestResultSerializer(serializers.ModelSerializer):
    test_case_name = serializers.CharField(source='test_case.name', read_only=True, default=None)
    api_name = serializers.CharField(source='api.name', read_only=True)
    api_path = serializers.CharField(source='api.path', read_only=True)
    api_method = serializers.CharField(source='api.method', read_only=True)

    class Meta:
        model = TestResult
        fields = [
            'id', 'test_run', 'test_case', 'test_case_name', 'api', 'api_name',
            'api_path', 'api_method', 'name', 'is_passed', 'request_url',
            'request_method', 'request_headers', 'request_body', 'response_status',
            'response_headers', 'response_body', 'response_time', 'error_message',
            'assertion_results', 'executed_at'
        ]
        read_only_fields = ['executed_at']
