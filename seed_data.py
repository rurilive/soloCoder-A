from datetime import datetime
from app.database import SessionLocal, init_db
from app.models import Post, Category, Tag

def seed_data():
    init_db()
    db = SessionLocal()
    
    try:
        if db.query(Category).count() > 0:
            print("数据库已有数据，跳过初始化...")
            return
        
        categories = [
            Category(name="技术", description="技术相关文章"),
            Category(name="生活", description="生活随笔"),
            Category(name="旅行", description="旅行游记"),
            Category(name="读书", description="读书笔记"),
        ]
        db.add_all(categories)
        db.flush()
        
        tags = [
            Tag(name="Python"),
            Tag(name="FastAPI"),
            Tag(name="JavaScript"),
            Tag(name="Web开发"),
            Tag(name="前端"),
            Tag(name="后端"),
            Tag(name="数据库"),
            Tag(name="编程"),
            Tag(name="生活感悟"),
            Tag(name="摄影"),
        ]
        db.add_all(tags)
        db.flush()
        
        posts_data = [
            {
                "title": "使用 FastAPI 构建现代化 Web 应用",
                "content": """FastAPI 是一个现代、快速（高性能）的 Web 框架，用于基于标准 Python 类型提示使用 Python 3.6+ 构建 API。

## 为什么选择 FastAPI？

1. **快速**：非常高的性能，与 NodeJS 和 Go 相当。
2. **快速编码**：将功能开发速度提高约 200% 到 300%。
3. **更少的 bug**：减少约 40% 的人为（开发人员）导致的错误。
4. **直观**：出色的编辑器支持。到处都是自动完成。更少的调试时间。
5. **简单**：设计为易于使用和学习。更少的时间阅读文档。

## 快速开始

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

这就是一个最简单的 FastAPI 应用！运行它，然后访问 http://localhost:8000/docs 就能看到自动生成的交互式 API 文档。

## 类型提示的力量

FastAPI 利用 Python 的类型提示来提供自动验证、序列化和文档生成。这意味着你可以编写更少的代码，同时获得更好的开发体验。""",
                "excerpt": "FastAPI 是一个现代、快速的 Web 框架，用于基于标准 Python 类型提示构建 API。本文介绍 FastAPI 的核心特性和使用方法。",
                "cover_image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20programming%20code%20on%20dark%20screen%20with%20syntax%20highlighting%20professional%20developer%20workspace&image_size=landscape_4_3",
                "category": "技术",
                "tag_names": ["Python", "FastAPI", "Web开发", "后端"],
                "view_count": 156,
            },
            {
                "title": "CSS 瀑布流布局的三种实现方式",
                "content": """瀑布流布局（Waterfall Layout）是一种常见的网页布局方式，特点是元素高度不一，但宽度一致，像瀑布一样从上到下排列。

## 方式一：CSS Columns（最简单）

```css
.waterfall-container {
    column-count: 3;
    column-gap: 1rem;
}

.waterfall-item {
    break-inside: avoid;
    margin-bottom: 1rem;
}
```

这是最简单的实现方式，纯 CSS，兼容性好。缺点是元素按列排列，不是按行排列。

## 方式二：CSS Grid + 动态高度

使用 CSS Grid 配合 JavaScript 计算每个元素应该放在哪一行：

```css
.waterfall-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: 10px;
    gap: 1rem;
}
```

然后用 JavaScript 计算每个元素需要跨越多少行。

## 方式三：Flexbox + JavaScript

使用 Flexbox 创建多列，然后用 JavaScript 决定每个元素放入哪一列。

## 各方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| CSS Columns | 最简单，纯 CSS | 按列排序，无法控制顺序 |
| CSS Grid | 灵活，可控制排序 | 需要 JavaScript 计算 |
| Flexbox | 兼容性好 | 需要较多 JavaScript |

推荐在大多数场景下使用 CSS Columns，简单高效！""",
                "excerpt": "瀑布流布局是一种常见的网页布局方式。本文介绍三种实现瀑布流布局的方法：CSS Columns、CSS Grid 和 Flexbox。",
                "cover_image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=waterfall%20layout%20design%20colorful%20cards%20different%20heights%20modern%20ui%20interface&image_size=landscape_4_3",
                "category": "技术",
                "tag_names": ["CSS", "JavaScript", "Web开发", "前端"],
                "view_count": 89,
            },
            {
                "title": "我的周末：探索城市角落的咖啡馆",
                "content": """周末，我决定远离熟悉的工作区，去探索城市角落里那些被遗忘的咖啡馆。

## 第一站：老巷子里的「慢时光」

穿过一条狭窄的老巷子，一扇木质门后藏着这家名为「慢时光」的咖啡馆。推开门，一阵咖啡豆的香气扑面而来。

老板是一位五十多岁的大叔，他说这家店已经开了十五年了。"现在的人都太快了，我想让进来的人都慢下来。"

我点了一杯手冲哥伦比亚，坐在窗边的位置。阳光透过老槐树的枝叶洒进来，在木质桌面上形成斑驳的光影。

## 第二站：旧仓库改造的「工业风」

第二家咖啡馆在一个改造过的旧仓库里。高高的天花板、裸露的管道、复古的工业灯，一切都在诉说着这个空间的历史。

这里的咖啡师是个年轻的女孩，她给我推荐了一款埃塞俄比亚的耶加雪菲。"这款豆子有明显的柑橘和花香，适合夏天喝。"

## 感悟

其实城市里从来不缺少美好，缺少的是发现美好的眼睛。我们总是匆匆忙忙，错过了太多值得停下脚步的风景。

下周，我还会继续我的探索之旅。""",
                "excerpt": "周末探索城市角落里的咖啡馆，在老巷子里的「慢时光」和旧仓库改造的工业风咖啡馆中，发现城市的另一面。",
                "cover_image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cozy%20vintage%20coffee%20shop%20interior%20warm%20lighting%20wooden%20furniture%20steam%20rising%20from%20cup&image_size=landscape_4_3",
                "category": "生活",
                "tag_names": ["生活感悟", "摄影"],
                "view_count": 234,
            },
            {
                "title": "SQLite 入门：从零开始学习轻量级数据库",
                "content": """SQLite 是世界上使用最广泛的数据库引擎。它轻量级、零配置、不需要服务器，是嵌入式应用和小型项目的完美选择。

## 为什么选择 SQLite？

1. **零配置**：不需要安装、配置或启动服务器进程
2. **单文件**：整个数据库存储在一个单一的磁盘文件中
3. **跨平台**：数据库文件可以在不同架构的机器之间自由复制
4. **自给自足**：不需要任何外部依赖
5. **小而精**：完全配置时小于 600KiB

## 基本操作

```python
import sqlite3

# 连接数据库（如果不存在则创建）
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     title TEXT NOT NULL,
     content TEXT NOT NULL,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
''')

# 插入数据
cursor.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
               ('第一篇文章', '这是我的第一篇博客文章'))

# 提交更改
conn.commit()

# 查询数据
cursor.execute('SELECT * FROM posts')
for row in cursor.fetchall():
    print(row)

# 关闭连接
conn.close()
```

## SQLAlchemy ORM

在实际项目中，我们通常使用 ORM 来简化数据库操作：

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///./blog.db')
Base = declarative_base()

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
```

SQLite 简单但功能强大，是学习数据库的绝佳起点！""",
                "excerpt": "SQLite 是世界上使用最广泛的数据库引擎。本文从零开始介绍 SQLite 的基本概念、操作方法以及在 Python 中的使用。",
                "cover_image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=database%20visualization%20blue%20digital%20data%20flow%20technology%20background%203d%20rendering&image_size=landscape_4_3",
                "category": "技术",
                "tag_names": ["数据库", "Python", "编程"],
                "view_count": 67,
            },
            {
                "title": "云南之旅：大理的风花雪月",
                "content": """终于踏上了向往已久的云南之旅。第一站，大理。

## 下关风

抵达大理的那天，风很大。当地人说，下关的风是大理四景之首。站在洱海边，风从苍山吹来，带着洱海的湿润气息，令人心旷神怡。

## 上关花

虽然不是花季，但古城里依然有各种各样的花朵绽放。大理的白族人爱花，几乎家家户户的院子里都种着花。走在古城的石板路上，随处可见盛开的三角梅、炮仗花。

## 苍山雪

远看苍山，山顶依然有积雪。当地人说，苍山的雪终年不化，是大理的守护神。我们没有时间爬苍山，但远远望着那连绵的雪峰，内心已经感到宁静。

## 洱海月

夜晚，我们租了一辆电动车，环洱海骑行。月亮从洱海面升起，波光粼粼的水面反射着月光，美得让人窒息。

## 古城慢生活

在大理古城，时间似乎慢了下来。早上睡到自然醒，去古城里的小馆子吃一碗饵丝，然后随便逛逛，或者找一家咖啡馆坐着发呆。

大理，我还会再来的。""",
                "excerpt": "大理的风花雪月，下关的风、上关的花、苍山的雪、洱海的月，每一景都让人沉醉。这是一次难忘的旅行。",
                "cover_image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=erhai%20lake%20dali%20china%20sunset%20reflection%20mountains%20traditional%20architecture%20peaceful%20landscape&image_size=landscape_4_3",
                "category": "旅行",
                "tag_names": ["旅行", "摄影"],
                "view_count": 445,
            },
            {
                "title": "《深入理解计算机系统》读书笔记",
                "content": """最近在读《深入理解计算机系统》（Computer Systems: A Programmer's Perspective），这是一本非常棒的书，让我对计算机系统有了更深的理解。

## 为什么这本书值得一读？

大多数程序员只关注自己编写的代码，很少去思考代码是如何在计算机上运行的。这本书填补了这个空白，从程序员的角度解释了计算机系统的工作原理。

## 第一章：计算机系统漫游

这一章是整本书的概览，通过一个简单的 hello 程序，展示了程序从源代码到运行的整个过程：

1. **预处理**：处理 #include、#define 等指令
2. **编译**：将 C 代码编译成汇编代码
3. **汇编**：将汇编代码转换成机器码
4. **链接**：将目标文件和库文件链接成可执行文件

## 第二章：信息的表示和处理

这一章讲解了计算机如何表示和处理信息：

- **整数表示**：无符号数、有符号数（补码表示）
- **浮点数表示**：IEEE 754 标准
- **字节序**：大端序 vs 小端序

印象最深的是补码的设计。补码让减法可以用加法来实现，大大简化了硬件设计。

## 我的感悟

作为一名应用层程序员，了解系统底层的工作原理非常重要。它能帮助我们写出更高效、更健壮的代码，也能让我们在遇到问题时更快地定位和解决。

强烈推荐所有程序员都读一读这本书！""",
                "excerpt": "《深入理解计算机系统》从程序员的角度解释计算机系统的工作原理。本文分享我的读书笔记和感悟。",
                "cover_image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=old%20book%20stack%20reading%20glasses%20warm%20desk%20lamp%20cozy%20study%20room%20atmosphere&image_size=landscape_4_3",
                "category": "读书",
                "tag_names": ["编程", "生活感悟"],
                "view_count": 178,
            },
            {
                "title": "JavaScript 异步编程全解",
                "content": """JavaScript 的异步编程是前端开发中的核心概念。本文将全面介绍 JavaScript 中的异步编程方式。

## 回调函数（Callbacks）

这是最原始的异步方式：

```javascript
function fetchData(callback) {
    setTimeout(function() {
        callback('数据加载完成');
    }, 1000);
}

fetchData(function(data) {
    console.log(data);
});
```

问题：回调地狱（Callback Hell）

```javascript
getData(function(a) {
    getMoreData(a, function(b) {
        getMoreData(b, function(c) {
            console.log('嵌套太深了！');
        });
    });
});
```

## Promise

ES6 引入了 Promise，解决了回调地狱问题：

```javascript
function fetchData() {
    return new Promise(function(resolve, reject) {
        setTimeout(function() {
            resolve('数据加载完成');
        }, 1000);
    });
}

fetchData()
    .then(function(data) {
        console.log(data);
        return fetchMoreData();
    })
    .then(function(more) {
        console.log(more);
    })
    .catch(function(error) {
        console.error(error);
    });
```

## Async/Await

ES2017 引入的 async/await 让异步代码看起来像同步代码：

```javascript
async function getData() {
    try {
        const data = await fetchData();
        console.log(data);
        
        const more = await fetchMoreData(data);
        console.log(more);
    } catch (error) {
        console.error(error);
    }
}
```

## 总结

| 方式 | 优点 | 缺点 |
|------|------|------|
| 回调函数 | 简单直接 | 回调地狱，难以维护 |
| Promise | 链式调用，错误处理好 | 仍有一定复杂度 |
| async/await | 最直观，代码最清晰 | 需要理解 Promise |

推荐在现代项目中使用 async/await！""",
                "excerpt": "JavaScript 的异步编程是前端开发的核心。本文全面介绍回调函数、Promise 和 async/await 三种异步编程方式。",
                "cover_image": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=javascript%20code%20syntax%20highlight%20blue%20and%20yellow%20theme%20modern%20code%20editor%20interface&image_size=landscape_4_3",
                "category": "技术",
                "tag_names": ["JavaScript", "前端", "Web开发", "编程"],
                "view_count": 312,
            },
        ]
        
        for post_data in posts_data:
            category = db.query(Category).filter(Category.name == post_data["category"]).first()
            
            tags = []
            for tag_name in post_data["tag_names"]:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if tag:
                    tags.append(tag)
            
            post = Post(
                title=post_data["title"],
                slug=post_data["title"].lower().replace(" ", "-"),
                content=post_data["content"],
                excerpt=post_data["excerpt"],
                cover_image=post_data["cover_image"],
                category=category,
                tags=tags,
                view_count=post_data["view_count"],
                is_published=1,
            )
            db.add(post)
        
        db.commit()
        print("示例数据初始化完成！")
        print(f"创建了 {len(categories)} 个分类")
        print(f"创建了 {len(tags)} 个标签")
        print(f"创建了 {len(posts_data)} 篇文章")
        
    except Exception as e:
        print(f"初始化数据时出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
