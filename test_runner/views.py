import requests
import json
import time
import threading
from urllib.parse import urljoin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import TestCase, TestSuite, TestRun, TestResult
from .serializers import (
    TestCaseSerializer, TestSuiteSerializer, 
    TestRunSerializer, TestResultSerializer
)
from projects.models import ApiGroup
from apis.models import ApiDefinition


class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        api_id = self.request.query_params.get('api')
        if api_id:
            queryset = queryset.filter(api_id=api_id)
        return queryset

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        test_case = self.get_object()
        api = test_case.api
        project = api.project
        
        base_url = project.base_url if project.base_url else ''
        path = api.path
        if not path.startswith('/'):
            path = '/' + path
        
        if base_url and not base_url.startswith(('http://', 'https://')):
            base_url = 'http://' + base_url
        
        url = urljoin(base_url, path) if base_url else path
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        method = api.method
        request_headers = {}
        request_params = {}
        request_body = None
        
        for param in test_case.request_headers:
            if param.get('enabled', True) and param.get('key'):
                request_headers[param['key']] = param.get('value', '')
        
        for param in test_case.request_params:
            if param.get('enabled', True) and param.get('key'):
                request_params[param['key']] = param.get('value', '')
        
        if test_case.request_body:
            request_body = test_case.request_body
        
        if request.data.get('url'):
            url = request.data.get('url')
        
        start_time = time.time()
        assertion_results = []
        is_passed = True
        error_message = None
        response_status = 0
        response_headers = {}
        response_body = None
        response_time = 0
        
        try:
            kwargs = {
                'headers': request_headers,
                'params': request_params,
                'timeout': 30,
            }
            
            if method in ['POST', 'PUT', 'PATCH'] and request_body:
                kwargs['json'] = request_body
            
            response = requests.request(method, url, **kwargs)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_status = response.status_code
            response_headers = dict(response.headers)
            
            try:
                response_body = response.json()
            except:
                response_body = response.text
            
            if response_status != test_case.expected_status_code:
                is_passed = False
                assertion_results.append({
                    'type': 'status_code',
                    'expected': test_case.expected_status_code,
                    'actual': response_status,
                    'passed': False,
                    'message': f'状态码不匹配: 期望 {test_case.expected_status_code}, 实际 {response_status}'
                })
            else:
                assertion_results.append({
                    'type': 'status_code',
                    'expected': test_case.expected_status_code,
                    'actual': response_status,
                    'passed': True,
                    'message': '状态码匹配'
                })
            
            for assertion in test_case.assertions:
                result = self._evaluate_assertion(assertion, response_body, response_headers)
                assertion_results.append(result)
                if not result.get('passed'):
                    is_passed = False
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            is_passed = False
            error_message = str(e)
            assertion_results.append({
                'type': 'exception',
                'passed': False,
                'message': f'请求异常: {str(e)}'
            })
        
        test_result = TestResult.objects.create(
            test_case=test_case,
            api=api,
            name=test_case.name,
            is_passed=is_passed,
            request_url=url,
            request_method=method,
            request_headers=request_headers,
            request_body=json.dumps(request_body, ensure_ascii=False) if request_body else None,
            response_status=response_status,
            response_headers=response_headers,
            response_body=json.dumps(response_body, ensure_ascii=False) if isinstance(response_body, (dict, list)) else response_body,
            response_time=response_time,
            error_message=error_message,
            assertion_results=assertion_results
        )
        
        return Response({
            'success': True,
            'data': {
                'test_result_id': test_result.id,
                'is_passed': is_passed,
                'response_time_ms': response_time,
                'assertion_results': assertion_results,
                'response': {
                    'status': response_status,
                    'headers': response_headers,
                    'body': response_body
                }
            }
        })
    
    def _evaluate_assertion(self, assertion, response_body, response_headers):
        assertion_type = assertion.get('type')
        passed = True
        message = ''
        
        try:
            if assertion_type == 'json_path':
                json_path = assertion.get('json_path', '')
                expected_value = assertion.get('expected_value')
                actual_value = self._get_json_value(response_body, json_path)
                
                operator = assertion.get('operator', 'equals')
                passed = self._compare_values(actual_value, expected_value, operator)
                
                message = f'JSON路径 "{json_path}": 期望值 "{expected_value}", 实际值 "{actual_value}", 比较结果: {"通过" if passed else "失败"}'
            
            elif assertion_type == 'header':
                header_name = assertion.get('header_name', '')
                expected_value = assertion.get('expected_value')
                actual_value = response_headers.get(header_name, '')
                
                operator = assertion.get('operator', 'contains')
                passed = self._compare_values(str(actual_value), str(expected_value), operator)
                
                message = f'响应头 "{header_name}": 期望值 "{expected_value}", 实际值 "{actual_value}", 比较结果: {"通过" if passed else "失败"}'
            
            elif assertion_type == 'response_time':
                max_time = assertion.get('max_time_ms', 1000)
                actual_time = assertion.get('actual_time_ms', 0)
                passed = actual_time <= max_time
                
                message = f'响应时间: 最大允许 {max_time}ms, 实际 {actual_time}ms, 比较结果: {"通过" if passed else "失败"}'
            
            elif assertion_type == 'contains_text':
                text = assertion.get('text', '')
                response_str = json.dumps(response_body, ensure_ascii=False) if isinstance(response_body, (dict, list)) else str(response_body)
                passed = text in response_str
                
                message = f'响应包含文本 "{text}": {"通过" if passed else "失败"}'
        
        except Exception as e:
            passed = False
            message = f'断言执行异常: {str(e)}'
        
        return {
            'type': assertion_type,
            'passed': passed,
            'message': message,
            'assertion': assertion
        }
    
    def _get_json_value(self, data, json_path):
        if not json_path:
            return data
        
        parts = json_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    return None
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        
        return current
    
    def _compare_values(self, actual, expected, operator):
        if operator == 'equals':
            return str(actual) == str(expected)
        elif operator == 'not_equals':
            return str(actual) != str(expected)
        elif operator == 'contains':
            return str(expected) in str(actual)
        elif operator == 'not_contains':
            return str(expected) not in str(actual)
        elif operator == 'greater_than':
            try:
                return float(actual) > float(expected)
            except:
                return False
        elif operator == 'less_than':
            try:
                return float(actual) < float(expected)
            except:
                return False
        elif operator == 'regex_match':
            import re
            try:
                return bool(re.match(str(expected), str(actual)))
            except:
                return False
        
        return str(actual) == str(expected)


class TestSuiteViewSet(viewsets.ModelViewSet):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        test_suite = self.get_object()
        project = test_suite.project
        
        test_run = TestRun.objects.create(
            project=project,
            test_suite=test_suite,
            name=f'{test_suite.name} - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}',
            status='running',
            started_at=timezone.now()
        )
        
        thread = threading.Thread(
            target=self._run_suite_async,
            args=(test_run.id, test_suite.id)
        )
        thread.daemon = True
        thread.start()
        
        return Response({
            'success': True,
            'data': {
                'test_run_id': test_run.id,
                'status': 'running',
                'message': '测试套件已开始运行'
            }
        })
    
    def _run_suite_async(self, test_run_id, test_suite_id):
        test_run = TestRun.objects.get(id=test_run_id)
        test_suite = TestSuite.objects.get(id=test_suite_id)
        
        apis_to_test = set()
        
        for group in test_suite.groups.all():
            for api in group.apis.all():
                apis_to_test.add(api)
        
        for api in test_suite.apis.all():
            apis_to_test.add(api)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        start_time = time.time()
        
        for api in apis_to_test:
            test_cases = api.test_cases.filter(is_active=True)
            
            if not test_cases.exists():
                total_tests += 1
                try:
                    result = self._test_api_directly(api, test_run)
                    if result.is_passed:
                        passed_tests += 1
                    else:
                        failed_tests += 1
                except:
                    failed_tests += 1
            else:
                for test_case in test_cases:
                    total_tests += 1
                    try:
                        result = self._run_test_case(test_case, test_run)
                        if result.is_passed:
                            passed_tests += 1
                        else:
                            failed_tests += 1
                    except:
                        failed_tests += 1
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        test_run.status = 'completed'
        test_run.total_tests = total_tests
        test_run.passed_tests = passed_tests
        test_run.failed_tests = failed_tests
        test_run.completed_at = timezone.now()
        test_run.duration_ms = duration_ms
        test_run.save()
    
    def _test_api_directly(self, api, test_run):
        project = api.project
        
        base_url = project.base_url if project.base_url else ''
        path = api.path
        if not path.startswith('/'):
            path = '/' + path
        
        if base_url and not base_url.startswith(('http://', 'https://')):
            base_url = 'http://' + base_url
        
        url = urljoin(base_url, path) if base_url else path
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        method = api.method
        request_headers = {}
        request_params = {}
        request_body = None
        
        for param in api.request_headers:
            if param.get('enabled', True) and param.get('key'):
                request_headers[param['key']] = param.get('value', '')
        
        for param in api.request_params:
            if param.get('enabled', True) and param.get('key'):
                request_params[param['key']] = param.get('value', '')
        
        if api.request_body:
            request_body = api.request_body
        
        start_time = time.time()
        is_passed = False
        error_message = None
        response_status = 0
        response_headers = {}
        response_body = None
        response_time = 0
        
        try:
            kwargs = {
                'headers': request_headers,
                'params': request_params,
                'timeout': 30,
            }
            
            if method in ['POST', 'PUT', 'PATCH'] and request_body:
                kwargs['json'] = request_body
            
            response = requests.request(method, url, **kwargs)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_status = response.status_code
            response_headers = dict(response.headers)
            
            try:
                response_body = response.json()
            except:
                response_body = response.text
            
            is_passed = 200 <= response_status < 300
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            error_message = str(e)
        
        test_result = TestResult.objects.create(
            test_run=test_run,
            api=api,
            name=f'{api.name} - 快速测试',
            is_passed=is_passed,
            request_url=url,
            request_method=method,
            request_headers=request_headers,
            request_body=json.dumps(request_body, ensure_ascii=False) if request_body else None,
            response_status=response_status,
            response_headers=response_headers,
            response_body=json.dumps(response_body, ensure_ascii=False) if isinstance(response_body, (dict, list)) else response_body,
            response_time=response_time,
            error_message=error_message,
            assertion_results=[]
        )
        
        return test_result
    
    def _run_test_case(self, test_case, test_run):
        api = test_case.api
        project = api.project
        
        base_url = project.base_url if project.base_url else ''
        path = api.path
        if not path.startswith('/'):
            path = '/' + path
        
        if base_url and not base_url.startswith(('http://', 'https://')):
            base_url = 'http://' + base_url
        
        url = urljoin(base_url, path) if base_url else path
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        method = api.method
        request_headers = {}
        request_params = {}
        request_body = None
        
        for param in test_case.request_headers:
            if param.get('enabled', True) and param.get('key'):
                request_headers[param['key']] = param.get('value', '')
        
        for param in test_case.request_params:
            if param.get('enabled', True) and param.get('key'):
                request_params[param['key']] = param.get('value', '')
        
        if test_case.request_body:
            request_body = test_case.request_body
        
        start_time = time.time()
        assertion_results = []
        is_passed = True
        error_message = None
        response_status = 0
        response_headers = {}
        response_body = None
        response_time = 0
        
        try:
            kwargs = {
                'headers': request_headers,
                'params': request_params,
                'timeout': 30,
            }
            
            if method in ['POST', 'PUT', 'PATCH'] and request_body:
                kwargs['json'] = request_body
            
            response = requests.request(method, url, **kwargs)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_status = response.status_code
            response_headers = dict(response.headers)
            
            try:
                response_body = response.json()
            except:
                response_body = response.text
            
            if response_status != test_case.expected_status_code:
                is_passed = False
                assertion_results.append({
                    'type': 'status_code',
                    'expected': test_case.expected_status_code,
                    'actual': response_status,
                    'passed': False,
                    'message': f'状态码不匹配: 期望 {test_case.expected_status_code}, 实际 {response_status}'
                })
            else:
                assertion_results.append({
                    'type': 'status_code',
                    'expected': test_case.expected_status_code,
                    'actual': response_status,
                    'passed': True,
                    'message': '状态码匹配'
                })
            
            tc_view = TestCaseViewSet()
            for assertion in test_case.assertions:
                result = tc_view._evaluate_assertion(assertion, response_body, response_headers)
                assertion_results.append(result)
                if not result.get('passed'):
                    is_passed = False
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            is_passed = False
            error_message = str(e)
            assertion_results.append({
                'type': 'exception',
                'passed': False,
                'message': f'请求异常: {str(e)}'
            })
        
        test_result = TestResult.objects.create(
            test_run=test_run,
            test_case=test_case,
            api=api,
            name=test_case.name,
            is_passed=is_passed,
            request_url=url,
            request_method=method,
            request_headers=request_headers,
            request_body=json.dumps(request_body, ensure_ascii=False) if request_body else None,
            response_status=response_status,
            response_headers=response_headers,
            response_body=json.dumps(response_body, ensure_ascii=False) if isinstance(response_body, (dict, list)) else response_body,
            response_time=response_time,
            error_message=error_message,
            assertion_results=assertion_results
        )
        
        return test_result


class TestRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TestRun.objects.all()
    serializer_class = TestRunSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        test_suite_id = self.request.query_params.get('test_suite')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if test_suite_id:
            queryset = queryset.filter(test_suite_id=test_suite_id)
        return queryset

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        test_run = self.get_object()
        results = test_run.results.all()
        serializer = TestResultSerializer(results, many=True)
        return Response(serializer.data)


class TestResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        test_run_id = self.request.query_params.get('test_run')
        api_id = self.request.query_params.get('api')
        if test_run_id:
            queryset = queryset.filter(test_run_id=test_run_id)
        if api_id:
            queryset = queryset.filter(api_id=api_id)
        return queryset


class BatchTestViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'])
    def by_groups(self, request):
        project_id = request.data.get('project_id')
        group_ids = request.data.get('group_ids', [])
        run_name = request.data.get('name', f'批量测试 - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        if not project_id:
            return Response({'success': False, 'error': '缺少项目ID'}, status=400)
        
        try:
            project = ApiGroup.objects.get(id=group_ids[0]).project if group_ids else None
            if not project and project_id:
                from projects.models import Project
                project = Project.objects.get(id=project_id)
        except:
            return Response({'success': False, 'error': '项目不存在'}, status=404)
        
        test_run = TestRun.objects.create(
            project=project,
            name=run_name,
            status='running',
            started_at=timezone.now()
        )
        
        thread = threading.Thread(
            target=self._run_groups_async,
            args=(test_run.id, group_ids)
        )
        thread.daemon = True
        thread.start()
        
        return Response({
            'success': True,
            'data': {
                'test_run_id': test_run.id,
                'status': 'running',
                'message': '按组批量测试已开始'
            }
        })
    
    @action(detail=False, methods=['post'])
    def by_apis(self, request):
        project_id = request.data.get('project_id')
        api_ids = request.data.get('api_ids', [])
        run_name = request.data.get('name', f'勾选测试 - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        if not api_ids:
            return Response({'success': False, 'error': '未选择任何接口'}, status=400)
        
        try:
            api = ApiDefinition.objects.get(id=api_ids[0])
            project = api.project
        except:
            return Response({'success': False, 'error': '接口不存在'}, status=404)
        
        test_run = TestRun.objects.create(
            project=project,
            name=run_name,
            status='running',
            started_at=timezone.now()
        )
        
        thread = threading.Thread(
            target=self._run_apis_async,
            args=(test_run.id, api_ids)
        )
        thread.daemon = True
        thread.start()
        
        return Response({
            'success': True,
            'data': {
                'test_run_id': test_run.id,
                'status': 'running',
                'message': '勾选测试已开始'
            }
        })
    
    def _run_groups_async(self, test_run_id, group_ids):
        test_run = TestRun.objects.get(id=test_run_id)
        
        apis_to_test = set()
        for group_id in group_ids:
            try:
                group = ApiGroup.objects.get(id=group_id)
                for api in group.apis.all():
                    apis_to_test.add(api)
            except:
                continue
        
        self._run_apis(test_run, apis_to_test)
    
    def _run_apis_async(self, test_run_id, api_ids):
        test_run = TestRun.objects.get(id=test_run_id)
        
        apis_to_test = set()
        for api_id in api_ids:
            try:
                api = ApiDefinition.objects.get(id=api_id)
                apis_to_test.add(api)
            except:
                continue
        
        self._run_apis(test_run, apis_to_test)
    
    def _run_apis(self, test_run, apis_to_test):
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        start_time = time.time()
        
        ts_view = TestSuiteViewSet()
        
        for api in apis_to_test:
            test_cases = api.test_cases.filter(is_active=True)
            
            if not test_cases.exists():
                total_tests += 1
                try:
                    result = ts_view._test_api_directly(api, test_run)
                    if result.is_passed:
                        passed_tests += 1
                    else:
                        failed_tests += 1
                except:
                    failed_tests += 1
            else:
                for test_case in test_cases:
                    total_tests += 1
                    try:
                        result = ts_view._run_test_case(test_case, test_run)
                        if result.is_passed:
                            passed_tests += 1
                        else:
                            failed_tests += 1
                    except:
                        failed_tests += 1
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        test_run.status = 'completed'
        test_run.total_tests = total_tests
        test_run.passed_tests = passed_tests
        test_run.failed_tests = failed_tests
        test_run.completed_at = timezone.now()
        test_run.duration_ms = duration_ms
        test_run.save()
