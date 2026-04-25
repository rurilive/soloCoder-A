import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import ApiDefinition


class DocumentGenerator:
    """
    API文档生成器，支持多种格式
    """
    
    @staticmethod
    def generate_postman_collection(apis: List[ApiDefinition], 
                                     collection_name: str = "API Collection",
                                     base_url: str = "") -> Dict[str, Any]:
        """
        生成Postman Collection格式的文档
        """
        collection = {
            "info": {
                "name": collection_name,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "description": f"Generated API Documentation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            },
            "item": []
        }
        
        for api in apis:
            item = {
                "name": api.name,
                "request": {
                    "method": api.method,
                    "header": [],
                    "url": {
                        "raw": f"{base_url.rstrip('/')}{api.path if api.path.startswith('/') else '/' + api.path}",
                        "protocol": "https" if "https" in base_url.lower() else "http",
                        "host": [base_url.replace("http://", "").replace("https://", "").split("/")[0]] if base_url else [],
                        "path": api.path.strip("/").split("/") if api.path else []
                    }
                },
                "response": []
            }
            
            if api.description:
                item["request"]["description"] = api.description
            
            for header in api.request_headers:
                if header.get('key'):
                    header_item = {
                        "key": header.get('key', ''),
                        "value": header.get('value', ''),
                        "disabled": not header.get('enabled', True)
                    }
                    if header.get('description'):
                        header_item["description"] = header.get('description')
                    item["request"]["header"].append(header_item)
            
            query_params = []
            for param in api.request_params:
                if param.get('key'):
                    query_item = {
                        "key": param.get('key', ''),
                        "value": param.get('value', ''),
                        "disabled": not param.get('enabled', True)
                    }
                    if param.get('description'):
                        query_item["description"] = param.get('description')
                    query_params.append(query_item)
            
            if query_params:
                item["request"]["url"]["query"] = query_params
            
            if api.request_body and api.request_body_type == 'json':
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(api.request_body, ensure_ascii=False, indent=2),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            
            for example in api.response_examples:
                response_item = {
                    "name": example.get('name', 'Example'),
                    "originalRequest": item["request"].copy(),
                    "status": example.get('status_text', 'OK'),
                    "code": example.get('status_code', 200),
                    "header": [{"key": k, "value": v} for k, v in example.get('headers', {}).items()],
                    "body": json.dumps(example.get('body', {}), ensure_ascii=False, indent=2) if isinstance(example.get('body'), (dict, list)) else str(example.get('body', ''))
                }
                item["response"].append(response_item)
            
            collection["item"].append(item)
        
        return collection
    
    @staticmethod
    def generate_json_document(apis: List[ApiDefinition], 
                                project_name: str = "API Project",
                                base_url: str = "") -> Dict[str, Any]:
        """
        生成结构化JSON格式的文档
        """
        document = {
            "info": {
                "title": project_name,
                "version": "1.0.0",
                "baseUrl": base_url,
                "generatedAt": datetime.now().isoformat(),
                "description": "API Documentation"
            },
            "apis": []
        }
        
        for api in apis:
            api_doc = {
                "id": api.id,
                "name": api.name,
                "description": api.description or "",
                "method": api.method,
                "path": api.path,
                "fullUrl": f"{base_url.rstrip('/')}{api.path if api.path.startswith('/') else '/' + api.path}" if base_url else api.path,
                "requestParams": [],
                "requestHeaders": [],
                "requestBody": None,
                "requestBodyType": api.request_body_type,
                "responseExamples": [],
                "isActive": api.is_active,
                "createdAt": api.created_at.isoformat() if api.created_at else None,
                "updatedAt": api.updated_at.isoformat() if api.updated_at else None
            }
            
            for param in api.request_params:
                api_doc["requestParams"].append({
                    "key": param.get('key', ''),
                    "value": param.get('value', ''),
                    "type": param.get('type', 'string'),
                    "required": param.get('required', False),
                    "description": param.get('description', ''),
                    "enabled": param.get('enabled', True)
                })
            
            for header in api.request_headers:
                api_doc["requestHeaders"].append({
                    "key": header.get('key', ''),
                    "value": header.get('value', ''),
                    "description": header.get('description', ''),
                    "enabled": header.get('enabled', True)
                })
            
            if api.request_body:
                api_doc["requestBody"] = api.request_body
            
            for example in api.response_examples:
                api_doc["responseExamples"].append({
                    "name": example.get('name', 'Example'),
                    "statusCode": example.get('status_code', 200),
                    "statusText": example.get('status_text', 'OK'),
                    "headers": example.get('headers', {}),
                    "body": example.get('body', {})
                })
            
            document["apis"].append(api_doc)
        
        return document
    
    @staticmethod
    def generate_markdown_document(apis: List[ApiDefinition], 
                                     project_name: str = "API Project",
                                     base_url: str = "",
                                     include_toc: bool = True) -> str:
        """
        生成Markdown格式的文档
        """
        lines = []
        
        lines.append(f"# {project_name} API 文档")
        lines.append("")
        lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if base_url:
            lines.append(f"> 基础URL: `{base_url}`")
        lines.append("")
        
        if include_toc and len(apis) > 1:
            lines.append("## 目录")
            lines.append("")
            for i, api in enumerate(apis):
                anchor = f"{api.name.lower().replace(' ', '-')}-{api.id}"
                lines.append(f"{i+1}. [{api.name}](#{anchor})")
            lines.append("")
        
        for api in apis:
            lines.append("---")
            lines.append("")
            lines.append(f"## {api.name}")
            lines.append("")
            
            if api.description:
                lines.append(api.description)
                lines.append("")
            
            method_colors = {
                'GET': 'GET',
                'POST': 'POST',
                'PUT': 'PUT',
                'DELETE': 'DELETE',
                'PATCH': 'PATCH',
                'HEAD': 'HEAD',
                'OPTIONS': 'OPTIONS'
            }
            
            lines.append(f"**请求方法**: `{method_colors.get(api.method, api.method)}`")
            lines.append(f"**请求路径**: `{api.path}`")
            if base_url:
                full_url = f"{base_url.rstrip('/')}{api.path if api.path.startswith('/') else '/' + api.path}"
                lines.append(f"**完整URL**: `{full_url}`")
            lines.append("")
            
            if api.request_headers:
                enabled_headers = [h for h in api.request_headers if h.get('enabled', True) and h.get('key')]
                if enabled_headers:
                    lines.append("### 请求头")
                    lines.append("")
                    lines.append("| 名称 | 值 | 描述 |")
                    lines.append("|------|-----|------|")
                    for header in enabled_headers:
                        name = header.get('key', '')
                        value = header.get('value', '')
                        desc = header.get('description', '-')
                        lines.append(f"| `{name}` | `{value}` | {desc} |")
                    lines.append("")
            
            if api.request_params:
                enabled_params = [p for p in api.request_params if p.get('enabled', True) and p.get('key')]
                if enabled_params:
                    lines.append("### 请求参数")
                    lines.append("")
                    lines.append("| 名称 | 类型 | 必填 | 默认值 | 描述 |")
                    lines.append("|------|------|------|--------|------|")
                    for param in enabled_params:
                        name = param.get('key', '')
                        param_type = param.get('type', 'string')
                        required = "是" if param.get('required', False) else "否"
                        default = param.get('value', '-')
                        desc = param.get('description', '-')
                        lines.append(f"| `{name}` | `{param_type}` | {required} | `{default}` | {desc} |")
                    lines.append("")
            
            if api.request_body and api.request_body_type == 'json':
                lines.append("### 请求体")
                lines.append("")
                lines.append(f"**类型**: `{api.request_body_type}`")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(api.request_body, ensure_ascii=False, indent=2))
                lines.append("```")
                lines.append("")
            
            if api.response_examples:
                lines.append("### 响应示例")
                lines.append("")
                for example in api.response_examples:
                    name = example.get('name', '示例')
                    status_code = example.get('status_code', 200)
                    status_text = example.get('status_text', 'OK')
                    
                    lines.append(f"#### {name}")
                    lines.append("")
                    lines.append(f"**状态码**: `{status_code} {status_text}`")
                    lines.append("")
                    
                    headers = example.get('headers', {})
                    if headers:
                        lines.append("**响应头**:")
                        lines.append("")
                        lines.append("```")
                        for key, value in headers.items():
                            lines.append(f"{key}: {value}")
                        lines.append("```")
                        lines.append("")
                    
                    body = example.get('body', {})
                    if body:
                        lines.append("**响应体**:")
                        lines.append("")
                        lines.append("```json")
                        if isinstance(body, (dict, list)):
                            lines.append(json.dumps(body, ensure_ascii=False, indent=2))
                        else:
                            lines.append(str(body))
                        lines.append("```")
                        lines.append("")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_document(apis: List[ApiDefinition], 
                          format: str = "json",
                          project_name: str = "API Project",
                          base_url: str = "") -> Any:
        """
        根据指定格式生成文档
        
        参数:
            apis: API定义列表
            format: 文档格式 (postman, json, markdown)
            project_name: 项目名称
            base_url: 基础URL
        
        返回:
            根据格式返回不同类型:
            - postman: Dict (Postman Collection)
            - json: Dict (结构化JSON)
            - markdown: str (Markdown文本)
        """
        format = format.lower()
        
        if format == "postman":
            return DocumentGenerator.generate_postman_collection(
                apis, 
                collection_name=project_name,
                base_url=base_url
            )
        elif format == "json":
            return DocumentGenerator.generate_json_document(
                apis,
                project_name=project_name,
                base_url=base_url
            )
        elif format == "markdown":
            return DocumentGenerator.generate_markdown_document(
                apis,
                project_name=project_name,
                base_url=base_url
            )
        else:
            raise ValueError(f"不支持的文档格式: {format}")
