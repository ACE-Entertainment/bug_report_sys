# Copyright (c) 2024 Yuchen (OGisacat)
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

import json
import os
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.drive.v1 import *
import logging
import pymysql
from time import sleep

LOG_FILE = "error_feishu.log"

feishu_doc_note = ''
feishu_table_id = ''
APP_ID = ''
APP_SECRET = ''

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,  # 记录错误及以上级别日志
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# 存储id的JSON配置文件路径
CONFIG_FILE_PATH = 'config.json'

# 数据库连接函数
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


# 读取配置文件中的last_id
def read_last_id():
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r') as f:
            config = json.load(f)
            return config.get('last_id', 0)  # 如果没有last_id字段，返回0
    return 0  # 如果文件不存在，默认返回0


# 更新配置文件中的last_id
def update_last_id(new_id):
    config = {}
    # 如果文件存在，读取旧配置
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r') as f:
            config = json.load(f)

    # 更新last_id为新的值
    config['last_id'] = new_id

    # 写入更新后的配置到文件
    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump(config, f, indent=4)


def get_reports(client):
    # 从配置文件读取上次处理的最大ID
    last_id = read_last_id()
    connection = None
    try:
        # 连接到数据库
        connection = get_db_connection()

        # 使用 with 语法管理游标
        with connection.cursor() as cursor:
            # 编写查询 SQL 语句，选取id > last_id的数据
            sql = """
                SELECT 
                    id, 
                    bug_title, 
                    log_file_path, 
                    steam_id, 
                    image_file_path, 
                    version, 
                    description, 
                    save_file_path, 
                    hardware, 
                    bug_type, 
                    name, 
                    email, 
                    upload_time
                FROM tos
                WHERE id > %s
                """

            # 执行查询
            cursor.execute(sql, (last_id,))

            # 获取所有结果
            results = cursor.fetchall()

            # 存储所有的 AppTableRecord 对象
            records = []

            # 如果有数据，则构建每一行数据并存储
            if results:
                # 获取当前查询中最大的id
                max_id = max(result['id'] for result in results)

                # 遍历查询结果
                for result in results:
                    bug_title = result.get("bug_title", "") or ""
                    fields = {
                        "log": upload_media(client, result.get("log_file_path", ""), bug_title),
                        "Steam_id": result.get("steam_id", ""),
                        "Version": result.get("version", ""),
                        "Bug Description": result.get("description", ""),
                        "Saving File": upload_media(client, result.get("save_file_path", ""), bug_title),  # 新增存档文件字段
                        "Hardware": result.get("hardware", ""),  # 新增硬件信息字段
                        "Bug Type": result.get("bug_type", ""),  # 新增Bug类型字段
                        "Steam Name": result.get("name", ""),  # 新增提交人字段
                        "Email": result.get("email", ""),  # 新增邮箱字段
                        "Bug Title(Player)": bug_title,  # 新增Bug标题字段
                        "Received Date": result.get("upload_time", "") or "",
                        "Category": "未消化"
                    }

                    image_file_path = result.get("image_file_path", "")
                    if image_file_path and os.path.exists(image_file_path):
                        fields["Screenshot"] = upload_media(client, image_file_path)

                    # 使用现成的 builder 构建每条记录
                    record = AppTableRecord.builder().fields(fields).build()

                    # 将记录添加到列表中
                    records.append(record)

                return records, max_id
            return [], last_id

    except Exception as e:
        # 捕获异常并输出错误信息
        print(f"Error occurred: {e}")
        logger.error("Error occurred while fetching reports: %s", e, exc_info=True)
        return [], last_id

    finally:
        # 确保关闭数据库连接
        if connection:
            connection.close()


def upload_media(client, file_path, bug_title=None):
    # 提取文件扩展名
    file_ext = os.path.splitext(file_path)[1]

    if bug_title:
        file_name = f"{bug_title}{file_ext}"
    else:
        file_name = os.path.basename(file_path)

    # 构造请求对象
    request: UploadAllMediaRequest = UploadAllMediaRequest.builder() \
        .request_body(UploadAllMediaRequestBody.builder()
                      .file_name(file_name)
                      .parent_type("bitable_file")
                      .parent_node(feishu_doc_note)
                      .size(os.path.getsize(file_path))
                      .file(open(file_path, "rb"))
                      .build()) \
        .build()

    # 发起请求
    response: UploadAllMediaResponse = client.drive.v1.media.upload_all(request)
    # if response.data and response.data.file_token:   # 提交成功后立即删除
    #     os.remove(file_path)
    sleep(0.2)
    return [{"file_token": response.data.file_token}]


def to_feishu(client):
    records, max_id = get_reports(client)
    if records:
        # 构造请求对象
        request: BatchCreateAppTableRecordRequest = BatchCreateAppTableRecordRequest.builder() \
            .app_token(feishu_doc_note) \
            .table_id(feishu_table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder()
                .records(records)
                .build()) \
            .build()

        # 发起请求
        response: BatchCreateAppTableRecordResponse = client.bitable.v1.app_table_record.batch_create(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_record.batch_create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))

        # 更新配置文件中的ID为最大值
        update_last_id(max_id)


if __name__ == "__main__":
    # 创建client
    client = lark.Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .log_level(lark.LogLevel.WARNING) \
        .build()
    to_feishu(client)
