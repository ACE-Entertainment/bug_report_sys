
# Bug Report API

这是一个基于 Flask 的 API，用于处理用户提交的 Bug 报告。接受日志、图片及其他元数据，存储到 MySQL 数据库

每隔一段时间，会集中把玩家提交的错误报告发送至：飞书或任何你设置的平台

当前可接受的请求体总大小最大为【 **33MB** 】

当前更新时间为每**分钟**

（客户端设置CD，不要让正常玩家短时间无限发送）

## 使用说明

### API 接口

**URL:** `https://yoururl.com`  
**方法:** `POST`  
**内容类型:** `multipart/form-data`

### 必填参数
1. **bug_title**(字符串): 标题  **最大1000字符**
2. **log_file** (文件): Bug 报告的日志文件 **['.log', '.zip', '.txt']**
3. **steam_id** (字符串): 提交 Bug 的用户 Steam ID **最大255字符**
4. **version** (字符串): 应用程序的版本号 **最大1000字符**
5. **description** (字符串): 对问题的简要描述 **1w6 字以内（65,535个字符）**
6. **save_file** (文件): 玩家存档 **['.zip', '.sav']**
7. **hardware** (字符串): 电脑配置（GPU、CPU、内存、驱动版本等）**1w6 字以内（65,535个字符）**
8. **type** (字符串): Bug 类型 **最大255字符**

### 选填参数
1. **image** (文件): 与 Bug 相关的截图或图片，上传后会自动压缩以优化存储 **['.jpg', '.jpeg', '.png']**
2. **name** (字符串): 称呼 **最大255字符**
3. **email** (字符串): 邮件 **最大255字符**

### 示例请求

以下是一个 Python 示例，用于演示如何与 API 交互：

```python
import requests

# 设置目标 URL
url = "https://yoururl.com"

# 准备上传的数据
try:
    # 打开文件资源
    with open('Player.log', 'rb') as log_file, \
         open('test_image.jpg', 'rb') as image_file, \
         open('save_data.zip', 'rb') as save_file:
        # 准备文件和数据
        files = {
            'log_file': ('Player.log', log_file),  # 日志文件
            # 'image': ('test_image.jpg', image_file),  # 图片文件（可选）
            'save_file': ('save_data.zip', save_file)  # 存档文件（必须是 .zip）
        }

        data = {
            'bug_title': 'Game crashes during save',
            'steam_id': '999999999999',
            'version': '1.0.0',
            'description': 'This is a test bug report with detailed information.',
            'hardware': 'CPU: Intel i7-8700, GPU: NVIDIA GTX 1080, RAM: 16GB, Driver: 531.18',
            'type': 'Crash',
            # 'name': 'John Doe',     # （可选）
            # 'email': 'johndoe@example.com'  # （可选）
        }

        # 发送 POST 请求
        response = requests.post(url, files=files, data=data)

        # 输出响应结果
        print("Status Code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except ValueError:
            print("Response Text:", response.text)
except FileNotFoundError as e:
    print(f"Error: File not found - {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

### 响应结果

API 将返回以下格式的 JSON 响应：

#### 成功， 200

```json
{
  "status": "success"
}
```

#### 失败

- 参数缺失或无效时，400：

```json
{
  "status": "fail",
  "message": "描述信息"
}
```

- 请求过大时，413：

```
<html>
<head><title>413 Request Entity Too Large</title></head>
<body>
<center><h1>413 Request Entity Too Large</h1></center>
<hr><center>nginx/1.26.2</center>
</body>
</html>
```

- 内部服务器错误，500：

```json
{
  "status": "error",
  "message": "发生内部错误"
}
```

### 功能特点

- 使用飞书 Webhook 发送错误通知。
- 自动压缩上传的图片以优化存储。

### 环境变量

以下环境变量用于数据库配置：

- `DB_HOST`: 数据库主机
- `DB_USER`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `DB_NAME`: 数据库名称

### 安装与运行

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 启动 Flask 应用：

   ```bash
   python3 bug_report.py
   ```
   
3. 确保以下目录对应用具有写权限：

   - `./logs`
   - `./images`

4. HTTPS使用Nginx反向代理

### 错误处理

- 错误日志记录到 `error_bugreport.log`。
- 通过飞书 Webhook 发送错误消息。(非必须)
