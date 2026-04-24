# 函数可视化工具 - 实现计划（分解和优先级任务列表）

## [ ] Task 1: 项目初始化和基础结构
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 使用 uv 初始化 Python 项目结构
  - 创建必要的目录结构（app, static, templates, tests）
  - 配置 pyproject.toml 依赖（fastapi, uvicorn, jinja2, numpy）
  - 创建入口文件 main.py
- **Acceptance Criteria Addressed**: [基础框架]
- **Test Requirements**:
  - `programmatic` TR-1.1: 项目可通过 `uv run uvicorn main:app` 启动
  - `programmatic` TR-1.2: 访问根路径返回 200 状态码
  - `human-judgement` TR-1.3: 目录结构符合预期（app/, static/, templates/, tests/）
- **Notes**: 项目结构参考:
  ```
  project/
    ├── app/
    │   ├── __init__.py
    │   ├── parser.py      # 表达式解析
    │   ├── calculator.py  # 函数计算
    │   ├── operations.py  # 集合运算
    │   └── routes.py      # API路由
    ├── static/
    │   ├── js/
    │   │   ├── app.js
    │   │   └── renderer.js  # Three.js渲染
    │   └── css/
    │       └── style.css
    ├── templates/
    │   └── index.html
    ├── tests/
    ├── main.py
    └── pyproject.toml
  ```

## [ ] Task 2: 数学表达式解析器（安全）
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 实现安全的数学表达式解析器，防止代码注入
  - 支持的运算符: +, -, *, /, ^(幂)
  - 支持的函数: sin, cos, tan, asin, acos, atan, exp, log, log10, sqrt, abs, sign
  - 支持的常量: pi, e
  - 自动检测变量数量（二元: x,y; 三元: x,y,z）
  - 将表达式转换为可调用的 numpy 兼容函数
- **Acceptance Criteria Addressed**: [AC-2, AC-3]
- **Test Requirements**:
  - `programmatic` TR-2.1: 解析 `x^2 + y^2` 并在 x=1, y=2 时返回 5
  - `programmatic` TR-2.2: 解析 `sin(x) * cos(y)` 并正确计算
  - `programmatic` TR-2.3: 解析 `exp(-x^2 - y^2)` 并正确计算
  - `programmatic` TR-2.4: 无效表达式 `__import__('os')` 应抛出安全错误，不执行
  - `programmatic` TR-2.5: 自动检测 `x^2 + y^2 + z^2` 为三元函数
  - `programmatic` TR-2.6: 语法错误表达式 `x + + y` 返回友好错误信息
- **Notes**: 使用 ast 模块解析表达式，白名单允许的函数和运算符，禁止 __builtins__ 访问

## [ ] Task 3: 二元函数计算和曲面网格生成
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现二元函数在指定范围内的数值计算
  - 生成 3D 曲面网格数据（顶点坐标、三角面片索引、法向量）
  - 支持参数配置: x范围, y范围, 采样点数（分辨率）
  - 输出标准化的网格数据格式供前端渲染
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-3.1: 计算 `x^2 + y^2` 在 x=[-5,5], y=[-5,5] 范围内，验证原点处值为 0，边缘处值为 50
  - `programmatic` TR-3.2: 生成的顶点数量 = (nx) * (ny)，三角面片数量 = (nx-1) * (ny-1) * 2
  - `programmatic` TR-3.3: 法向量计算正确，指向曲面外侧
  - `programmatic` TR-3.4: 输出格式包含 vertices, faces, normals, values 四个字段
- **Notes**: 使用 numpy 网格计算，使用 marching squares 或简单的矩形分割算法

## [ ] Task 4: 三元函数等值面生成（Marching Cubes）
- **Priority**: P1
- **Depends On**: Task 2
- **Description**: 
  - 实现 Marching Cubes 算法生成等值面
  - 支持三元函数 f(x,y,z) 在指定范围内的体素计算
  - 用户可指定等值面值（isovalue）
  - 输出标准化的网格数据
- **Acceptance Criteria Addressed**: [AC-9]
- **Test Requirements**:
  - `programmatic` TR-4.1: `x^2 + y^2 + z^2` 在 isovalue=25 时生成球体网格，验证半径≈5
  - `programmatic` TR-4.2: 验证生成的网格是封闭的（没有边界边）
  - `programmatic` TR-4.3: 改变 isovalue 后，网格大小按预期变化
  - `programmatic` TR-4.4: 支持不同采样分辨率，顶点数随分辨率增加而增加
- **Notes**: 可参考 scikit-image 的 marching_cubes 实现，或自行实现简化版本

## [ ] Task 5: 集合运算模块
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 实现多个二元函数图形之间的集合运算
  - **并集 (Union)**: 显示所有函数图形的合并区域
  - **交集 (Intersection)**: 仅显示所有函数共有的区域（基于Z值阈值）
  - **差集 (Difference)**: 从第一个函数中减去其他函数的区域
  - **对称差 (Symmetric Difference)**: 显示所有不重叠的区域
  - 支持阈值参数定义"重叠"的判断标准
- **Acceptance Criteria Addressed**: [AC-5, AC-6, AC-7, AC-8]
- **Test Requirements**:
  - `programmatic` TR-5.1: 两个函数的并集应包含两个函数的所有可见点
  - `programmatic` TR-5.2: 交集运算后，仅保留两个函数Z值在阈值范围内的点
  - `programmatic` TR-5.3: 差集 A-B 保留 A 中不满足 B 阈值条件的点
  - `programmatic` TR-5.4: 对称差 = (A-B) ∪ (B-A)，验证逻辑等价性
- **Notes**: 对于二元函数，集合运算基于网格点的掩膜（mask）操作；对于三元函数，需要基于体素值进行逻辑运算

## [ ] Task 6: FastAPI 后端 API 设计
- **Priority**: P0
- **Depends On**: Task 2, Task 3, Task 5
- **Description**: 
  - 设计 RESTful API 端点
  - POST `/api/render`: 主要渲染端点
    - 输入: functions 数组（每个含 expression, name, color）
    - 输入: operation（集合运算类型: none, union, intersection, difference, symmetric_difference）
    - 输入: params（x_range, y_range, z_range, resolution, isovalue 等）
    - 输出: 标准化网格数据（JSON格式）
  - GET `/api/presets`: 获取预设函数列表
  - POST `/api/validate`: 验证表达式语法（可选）
  - 统一错误响应格式
- **Acceptance Criteria Addressed**: [AC-1, AC-5, AC-6, AC-7, AC-8, AC-9]
- **Test Requirements**:
  - `programmatic` TR-6.1: POST `/api/render` 带有效函数返回 200 和网格数据
  - `programmatic` TR-6.2: 无效表达式返回 400 状态码和错误信息
  - `programmatic` TR-6.3: GET `/api/presets` 返回预设列表
  - `programmatic` TR-6.4: 多函数 + operation 参数正确触发集合运算
- **Notes**: API 响应格式示例:
  ```json
  {
    "success": true,
    "data": {
      "type": "surface",  // 或 "isosurface"
      "vertices": [[x,y,z], ...],
      "faces": [[i,j,k], ...],
      "normals": [[nx,ny,nz], ...],
      "colors": ["#ff0000", ...]  // 或单个颜色
    }
  }
  ```

## [ ] Task 7: 前端页面基础结构（Jinja2模板）
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 创建 index.html 主页面模板
  - 页面布局: 左侧控制面板 + 右侧3D渲染区域
  - 引入必要的 CDN 资源: Three.js, OrbitControls
  - 基础 CSS 样式（响应式布局）
- **Acceptance Criteria Addressed**: [基础UI]
- **Test Requirements**:
  - `human-judgement` TR-7.1: 页面加载后显示两栏布局
  - `human-judgement` TR-7.2: Three.js 初始化成功，显示空白场景
  - `human-judgement` TR-7.3: 基础UI元素（输入框、按钮）正确显示
- **Notes**: Three.js 使用 CDN: `https://unpkg.com/three@0.160.0/build/three.min.js`，OrbitControls 同样从 CDN 引入

## [ ] Task 8: Three.js 3D 渲染器实现
- **Priority**: P0
- **Depends On**: Task 7
- **Description**: 
  - 封装 Three.js 渲染器类
  - 支持加载后端返回的网格数据并渲染
  - 实现 OrbitControls 交互（旋转、缩放、平移）
  - 添加基础光照（环境光 + 方向光）
  - 支持网格颜色和透明度设置
  - 添加坐标轴辅助线和网格平面
- **Acceptance Criteria Addressed**: [AC-1, AC-11]
- **Test Requirements**:
  - `programmatic` TR-8.1: 给定顶点和面数据，渲染器能正确创建 Three.js Mesh
  - `human-judgement` TR-8.2: 鼠标拖动可旋转视角
  - `human-judgement` TR-8.3: 滚轮缩放功能正常
  - `human-judgement` TR-8.4: 右键拖动可平移
  - `human-judgement` TR-8.5: 坐标轴和网格辅助线可见
- **Notes**: 关键类: THREE.BufferGeometry, THREE.Mesh, THREE.MeshPhongMaterial, THREE.OrbitControls

## [ ] Task 9: 前端交互逻辑和状态管理
- **Priority**: P0
- **Depends On**: Task 7, Task 8
- **Description**: 
  - 实现函数输入区域（支持添加/删除多个函数）
  - 每个函数有: 名称输入、表达式输入、颜色选择器、启用/禁用开关
  - 实现集合运算选择器（下拉菜单: 无运算、并集、交集、差集、对称差）
  - 实现参数配置区域:
    - 坐标轴范围（X min/max, Y min/max, Z min/max）
    - 采样分辨率（滑块）
    - 等值面值（三元函数专用输入）
    - 透明度滑块
  - 实现"生成"按钮点击事件
  - 调用后端 API 并处理响应
  - 错误显示和加载状态
- **Acceptance Criteria Addressed**: [AC-4, AC-10, AC-12]
- **Test Requirements**:
  - `human-judgement` TR-9.1: 点击"添加函数"按钮增加输入框
  - `human-judgement` TR-9.2: 点击删除按钮移除对应函数输入
  - `human-judgement` TR-9.3: 颜色选择器改变后，输入框边框颜色同步变化
  - `human-judgement` TR-9.4: 集合运算下拉菜单有5个选项
  - `human-judgement` TR-9.5: 点击生成按钮后显示加载状态
  - `programmatic` TR-9.6: API 调用成功后数据传递给渲染器
- **Notes**: 使用原生 JavaScript，无需引入额外状态管理库

## [ ] Task 10: 预设函数功能
- **Priority**: P1
- **Depends On**: Task 6, Task 9
- **Description**: 
  - 后端定义预设函数列表（二元和三元示例）
  - 预设示例:
    - 抛物面: `x^2 + y^2`
    - 正弦波: `sin(x) * cos(y)`
    - 高斯函数: `exp(-x^2 - y^2)`
    - 马鞍面: `x^2 - y^2`
    - 球体: `x^2 + y^2 + z^2`
    - 圆环面: `(sqrt(x^2 + y^2) - 3)^2 + z^2`
  - 前端显示预设选择区域
  - 选择预设后自动填充函数输入框
- **Acceptance Criteria Addressed**: [AC-12]
- **Test Requirements**:
  - `programmatic` TR-10.1: GET `/api/presets` 返回至少5个预设函数
  - `human-judgement` TR-10.2: 预设列表在UI中可见
  - `human-judgement` TR-10.3: 点击预设项后函数输入框自动填充
- **Notes**: 预设数据包含: name, expression, type (2d/3d), color, default_params

## [ ] Task 11: 单元测试
- **Priority**: P1
- **Depends On**: Task 2, Task 3, Task 4, Task 5
- **Description**: 
  - 使用 pytest 编写单元测试
  - 测试表达式解析器的各种情况
  - 测试计算器的数值计算
  - 测试集合运算的正确性
  - 测试 API 端点响应
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-5, AC-6, AC-7, AC-8, AC-9]
- **Test Requirements**:
  - `programmatic` TR-11.1: 运行 `uv run pytest` 所有测试通过
  - `programmatic` TR-11.2: 测试覆盖率 > 80%（核心模块）
- **Notes**: 测试文件放在 tests/ 目录下，命名为 test_*.py

## [ ] Task 12: 集成和优化
- **Priority**: P2
- **Depends On**: Task 6, Task 8, Task 9
- **Description**: 
  - 前后端完整集成测试
  - 性能优化:
    - 网格数据压缩（可选: 简化顶点格式）
    - 大网格的渐进式加载
    - 后端计算缓存（相同参数相同函数直接返回）
  - 错误处理增强:
    - 网络错误提示
    - 计算超时处理
    - 除零、无穷大等数值异常处理
  - 添加重置视图按钮
- **Acceptance Criteria Addressed**: [AC-1, AC-11]
- **Test Requirements**:
  - `human-judgement` TR-12.1: 端到端流程: 选择预设 -> 点击生成 -> 3D图形显示
  - `human-judgement` TR-12.2: 生成过程中网络错误显示友好提示
  - `human-judgement` TR-12.3: 点击重置视图按钮恢复初始视角
- **Notes**: 可考虑使用 lru_cache 缓存相同参数的计算结果
