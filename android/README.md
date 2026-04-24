# 函数可视化工具 - Android App 使用说明

## 项目结构

```
android/
├── app/
│   ├── src/main/
│   │   ├── AndroidManifest.xml          # 应用清单（权限、配置）
│   │   ├── kotlin/com/example/funcviz/
│   │   │   └── MainActivity.kt          # 主 Activity（WebView 容器）
│   │   └── res/
│   │       ├── layout/
│   │       │   └── activity_main.xml    # 布局文件
│   │       ├── values/
│   │       │   ├── colors.xml           # 颜色定义
│   │       │   ├── strings.xml          # 字符串资源
│   │       │   └── themes.xml           # 主题配置
│   │       └── xml/
│   │           ├── backup_rules.xml
│   │           └── data_extraction_rules.xml
│   ├── build.gradle.kts                 # app 模块构建配置
│   └── proguard-rules.pro               # 混淆规则
├── gradle/wrapper/
│   └── gradle-wrapper.properties        # Gradle 包装器配置
├── build.gradle.kts                     # 根目录构建配置
├── settings.gradle.kts                  # 项目设置
└── gradle.properties                    # Gradle 属性
```

## 使用方法

### 方式一：用 Android Studio 打开（推荐）

1. **安装 Android Studio**
   - 下载地址：https://developer.android.com/studio
   - 需要安装 Android SDK 和 Gradle

2. **打开项目**
   - 启动 Android Studio
   - 选择 `Open an existing project`
   - 选择 `android/` 文件夹

3. **等待 Gradle 同步**
   - 首次打开会自动下载依赖（需要科学上网）
   - 等待右下角进度条完成

4. **连接手机或使用模拟器**
   - 真机：开启开发者选项 → USB 调试
   - 模拟器：在 Android Studio 中创建 AVD

5. **运行 App**
   - 点击工具栏的绿色 ▶ 按钮
   - 选择连接的设备

### 方式二：命令行构建

```bash
# 进入 android 目录
cd android

# 调试版本构建
./gradlew assembleDebug

# 输出位置：app/build/outputs/apk/debug/app-debug.apk

# 安装到连接的设备
./gradlew installDebug
```

## 使用流程

### 1. 启动服务器（电脑端）

确保 FastAPI 服务器正在运行，并且手机和电脑在同一局域网：

```bash
cd /data/projects/work/soloCoder/soloCoder-A
uvicorn main:app --host 0.0.0.0 --port 8000
```

> 注意：必须使用 `--host 0.0.0.0` 才能让局域网内的其他设备访问

### 2. 查找电脑 IP 地址

**Windows:**
```cmd
ipconfig
# 查找 "IPv4 地址"，通常是 192.168.1.xxx 或 192.168.0.xxx
```

**Linux/macOS:**
```bash
ifconfig
# 或
ip addr show
# 查找 inet 地址，通常是 192.168.1.xxx
```

### 3. 在 App 中输入服务器地址

App 启动后会弹出对话框，输入：
```
http://<电脑IP>:8000
```

例如：
```
http://192.168.1.100:8000
```

## App 功能特性

| 功能 | 说明 |
|------|------|
| 🔗 WebView 容器 | 完整的 Web 应用体验 |
| 🎮 触摸控制 | 拖动旋转，双指缩放（Three.js 交互） |
| 🔙 返回导航 | 按系统返回键返回上一页 |
| 📱 屏幕常亮 | 保持屏幕唤醒，防止渲染中断 |
| 🔄 配置地址 | 首次启动可配置服务器地址 |
| ⚡ 进度显示 | 加载时显示进度条 |
| 🛠️ 错误处理 | 连接失败时显示友好提示 |

## 常见问题

### Q1: 无法连接到服务器

**检查项：**
1. 服务器是否使用 `--host 0.0.0.0` 启动？
2. 电脑和手机是否在同一 WiFi 网络？
3. 电脑防火墙是否阻止了 8000 端口？
4. IP 地址是否正确？

**测试方法：**
在手机浏览器中直接输入 `http://<电脑IP>:8000`，看能否访问

### Q2: 3D 渲染卡顿

**可能原因：**
- 手机 GPU 性能有限
- 分辨率设置过高

**解决方案：**
- 在页面中降低分辨率（10-50）
- 减少同时显示的曲面数量

### Q3: 键盘遮挡输入框

**解决方案：**
App 已配置 `android:windowSoftInputMode="adjustResize"`，系统会自动调整布局

## 构建发布版本

### 1. 创建签名密钥

```bash
keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my-key-alias
```

### 2. 配置签名信息

在 `app/build.gradle.kts` 中添加：

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("my-release-key.jks")
            storePassword = "密码"
            keyAlias = "my-key-alias"
            keyPassword = "密码"
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

### 3. 构建发布版本

```bash
cd android
./gradlew assembleRelease
```

输出：`app/build/outputs/apk/release/app-release.apk`

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Kotlin |
| UI 构建 | View Binding |
| 渲染引擎 | WebView + Three.js |
| 构建系统 | Gradle + Kotlin DSL |
| 最低 SDK | Android 7.0 (API 24) |
| 目标 SDK | Android 14 (API 34) |

## 进一步优化建议

1. **PWA 模式**：添加 `addJavascriptInterface` 实现原生-Web 交互
2. **离线缓存**：使用 Service Worker 缓存静态资源
3. **推送通知**：添加 Firebase Cloud Messaging
4. **深度链接**：支持从其他应用打开
5. **深色模式**：跟随系统深色模式自动切换主题

## 许可证

本项目仅供学习和研究使用。
