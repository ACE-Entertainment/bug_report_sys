# Copyright (c) 2024 Yuchen (OGisacat)
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import os
import pymysql
import logging
from flask import Flask, request, jsonify
import requests
import json
import uuid
from PIL import Image
import time

# 设置日志记录
LOG_FILE = "error_bugreport.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,  # 记录错误及以上级别日志
    format="%(asctime)s - %(levelname)s - %(message)s"
)

home = ''

webhook_url = ''
app = Flask(__name__)
UPLOAD_FOLDER = '.'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
MIGRATION_URL = 'https://github.com/ACE-Entertainment/feishu-bug-gateway'


# 数据库配置
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# 数据库连接函数
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# 压缩图片并保存为 JPG
def compress_image(image_path):
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 生成压缩后的图片路径
            compressed_path = os.path.splitext(image_path)[0] + ".jpg"

            # 删除原始图片
            os.remove(image_path)

            # 保存为 JPG 格式
            img.save(compressed_path, "JPEG", optimize=True, quality=69)

        return compressed_path
    except Exception as e:
        send_feishu_message(e)
        return None


@app.route('/', methods=['POST'])
def upload_data():
    return jsonify({
        "status": "deprecated",
        "message": "This API has been sunset. Please migrate to the new repository.",
        "migration": MIGRATION_URL
    }), 410

    try:
        # 接收 Bug 标题
        bug_title = request.form.get('bug_title')
        if not bug_title:
            return jsonify({"status": "fail", "message": "Title is required"}), 400

        # 接收 SteamID
        steam_id = request.form.get('steam_id')
        if steam_id == '1g2g34hdd56g789':
            return jsonify({"status": "success", "message": "test success"}), 200
        if not steam_id:
            return jsonify({"status": "fail", "message": "SteamID is required"}), 400

        # 接收硬件信息
        hardware = request.form.get('hardware')
        if not hardware:
            return jsonify({"status": "fail", "message": "Hardware information is required"}), 400

        # 接收 Bug 类型
        bug_type = request.form.get('type')
        if not bug_type:
            return jsonify({"status": "fail", "message": "Bug type is required"}), 400

        # 接收版本号
        version = request.form.get('version')
        if not version:
            return jsonify({"status": "fail", "message": "Version is required"}), 400

        # 接收文字描述
        description = request.form.get('description')
        if not description:
            return jsonify({"status": "fail", "message": "Description is required"}), 400

        # 接收称呼
        name = request.form.get('name')

        # 接收邮件
        email = request.form.get('email')

        # 接收 log 文件
        log_file = request.files.get('log_file')
        if log_file and log_file.content_length < 6 * 1024 * 1024:
            log_ext = os.path.splitext(log_file.filename)[1]
            allowed_log_extensions = ['.log', '.zip', '.txt']
            if log_ext not in allowed_log_extensions:
                return jsonify({"status": "fail", "message": "Log file type is not allowed"}), 400
            log_path = os.path.join(UPLOAD_FOLDER, 'logs', f"{uuid.uuid4().hex}{log_ext}")
        else:
            if not log_file:
                return jsonify({"status": "fail", "message": "Log file is required"}), 400
            return jsonify({"status": "fail", "message": "Log file is required and must be < 6MB"}), 400

        # 接收存档文件
        save_file = request.files.get('save_file')
        if save_file and save_file.content_length < 6 * 1024 * 1024:
            save_ext = os.path.splitext(save_file.filename)[1]
            allowed_save_extensions = ['.zip', '.sav']
            if save_ext not in allowed_save_extensions:
                return jsonify({"status": "fail", "message": "Save file type is not allowed"}), 400
            save_file_path = os.path.join(UPLOAD_FOLDER, 'saves', f"{uuid.uuid4().hex}{save_ext}")
        else:
            if not save_file:
                return jsonify({"status": "fail", "message": "Save file is required"}), 400
            return jsonify({"status": "fail", "message": "Save file is required and must be < 6MB"}), 400

        # 接收图片
        image = request.files.get('image')
        if image and image.content_length < 6 * 1024 * 1024:
            image_ext = os.path.splitext(image.filename)[1]
            allowed_image_extensions = ['.jpg', '.jpeg', '.png']
            if image_ext not in allowed_image_extensions:
                return jsonify({"status": "fail", "message": "Image file type is not allowed"}), 400
            image_path = os.path.join(UPLOAD_FOLDER, 'images',
                                      f"{uuid.uuid4().hex}{image_ext}")
        else:
            image_path = None  # 图片是选填的

        # 文件都没问题后，储存文件
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_file.save(log_path)

        os.makedirs(os.path.dirname(save_file_path), exist_ok=True)
        save_file.save(save_file_path)

        if image_path:
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)
        # 插入数据到 MySQL
        try:
            if image_path:
                jpg_path = compress_image(image_path)
                if jpg_path:
                    image_path = jpg_path
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = f"""INSERT INTO tos (
                bug_title, log_file_path, steam_id, image_file_path, version, description, save_file_path,
                hardware, bug_type, name, email, upload_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
                cursor.execute(sql, (
                    bug_title, log_path, steam_id, image_path or None, version, description, save_file_path,
                    hardware, bug_type, name or None, email or None, int(time.time() * 1000)
                ))
                connection.commit()
        except Exception as e:
            send_feishu_message(e, sql)
            return jsonify({"status": "fail", "message": "Database error"}), 500
        finally:
            connection.close()

        # 返回成功响应
        return jsonify({
            "status": "success"
        }), 200

    except Exception as e:
        send_feishu_message(e)
        return jsonify({"status": "error", "message": "Unexpected error occurred"}), 500


def send_feishu_message(e, sql=None):
    """
    发送飞书消息的函数。

    参数:
    - webhook_url (str): 飞书机器人的 webhook URL。
    - message (str): 要发送的文本消息。

    返回:
    - response (dict): 响应的 JSON 数据，如果请求失败则返回错误信息。
    """
    content = [{"tag": "text", "text": f"bug report 出现错误：{e}"}, {"tag": "at", "user_id": 'all'}]
    if sql:
        content.append({"tag": "text", "text": f"sql：{sql}"})


    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "bug report error",
                    "content": [content]
                }
            }
        }
    }

    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print("Message sent successfully.")
        return response.json()
    else:
        print("Failed to send message:", response.status_code, response.text)
        return {"error": response.status_code, "message": response.text}
