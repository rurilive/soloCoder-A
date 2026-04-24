# 函数可视化工具 - 验证检查清单

## 后端验证

- [ ] Checkpoint 1: 项目可通过 `uv run uvicorn main:app --reload` 成功启动
- [ ] Checkpoint 2: 访问 `http://localhost:8000/` 返回 200 状态码
- [ ] Checkpoint 3: 数学表达式解析器安全测试 - `__import__('os')` 不执行，返回错误
- [ ] Checkpoint 4: 表达式 `x^2 + y^2` 在 (1,2) 处计算结果正确 (等于 5)
- [ ] Checkpoint 5: 三元函数 `x^2 + y^2 + z^2` 被正确识别为三元
- [ ] Checkpoint 6: 二元函数曲面网格生成 - 顶点数 = nx * ny
- [ ] Checkpoint 7: 二元函数曲面网格生成 - 三角面片数 = (nx-1) * (ny-1) * 2
- [ ] Checkpoint 8: Marching Cubes 等值面 - 球体方程 + isovalue=25 生成半径≈5的网格
- [ ] Checkpoint 9: POST `/api/render` 有效函数返回 200 和包含 vertices, faces 的 JSON
- [ ] Checkpoint 10: POST `/api/render` 无效表达式返回 400 和错误信息
- [ ] Checkpoint 11: GET `/api/presets` 返回至少 5 个预设函数
- [ ] Checkpoint 12: 并集运算 - 两个函数的结果包含两者的所有有效区域
- [ ] Checkpoint 13: 交集运算 - 仅保留两个函数 Z 值接近的区域
- [ ] Checkpoint 14: 差集运算 - A-B 结果 < 交集运算结果
- [ ] Checkpoint 15: 对称差运算 - 结果包含 (A-B) + (B-A)
- [ ] Checkpoint 16: 运行 `uv run pytest` 所有测试通过

## 前端验证

- [ ] Checkpoint 17: 页面加载后显示两栏布局（左侧面板 + 右侧3D区域）
- [ ] Checkpoint 18: Three.js 初始化成功 - 场景中有坐标轴和网格线
- [ ] Checkpoint 19: 点击"添加函数"按钮后出现新的函数输入框
- [ ] Checkpoint 20: 点击函数项的删除按钮后该项消失
- [ ] Checkpoint 21: 集合运算下拉菜单有 5 个选项（无运算、并集、交集、差集、对称差）
- [ ] Checkpoint 22: 颜色选择器更改后，输入框边框颜色同步变化
- [ ] Checkpoint 23: 参数区域有 X/Y/Z 范围输入框、分辨率滑块、透明度滑块
- [ ] Checkpoint 24: 三元函数模式下显示等值面值输入框
- [ ] Checkpoint 25: 预设列表区域显示至少 5 个预设项
- [ ] Checkpoint 26: 点击预设项后函数输入框自动填充

## 交互验证

- [ ] Checkpoint 27: 鼠标左键拖动可旋转 3D 视角
- [ ] Checkpoint 28: 鼠标滚轮可缩放视图
- [ ] Checkpoint 29: 鼠标右键拖动可平移视图
- [ ] Checkpoint 30: 点击"生成"按钮后显示加载状态
- [ ] Checkpoint 31: API 成功后 3D 场景中显示曲面网格
- [ ] Checkpoint 32: 曲面颜色与函数配置的颜色一致
- [ ] Checkpoint 33: 无效表达式生成时显示友好错误提示
- [ ] Checkpoint 34: 调整透明度滑块后曲面透明度变化
- [ ] Checkpoint 35: 调整分辨率后重新生成，网格精细度变化
- [ ] Checkpoint 36: "重置视图"按钮点击后恢复初始视角

## 端到端流程

- [ ] Checkpoint 37: 选择预设"抛物面" -> 点击生成 -> 3D 场景显示抛物面曲面
- [ ] Checkpoint 38: 选择预设"球体"（三元）-> 输入 isovalue=25 -> 点击生成 -> 显示球体等值面
- [ ] Checkpoint 39: 添加两个二元函数 -> 选择"并集"运算 -> 生成 -> 显示两个曲面合并
- [ ] Checkpoint 40: 添加两个重叠函数 -> 选择"交集"运算 -> 生成 -> 仅显示重叠区域
- [ ] Checkpoint 41: 网络断开时点击生成 -> 显示网络错误提示，不崩溃
