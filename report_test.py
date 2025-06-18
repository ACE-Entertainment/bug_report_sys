# Copyright (c) 2024 Yuchen (OGisacat)
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import requests

# 设置目标 URL
url = "https://yoururl.com"

# 准备上传的数据
try:
    # 打开文件资源
    with open('player_log.zip', 'rb') as log_file, \
         open('capture.png', 'rb') as image_file, \
         open('save_data.zip', 'rb') as save_file:
        # 准备文件和数据
        files = {
            'log_file': ('player_log.zip', log_file),  # 日志文件
            # 'image': ('capture.png', image_file),  # 图片文件（可选）
            'save_file': ('save_data.zip', save_file)  # 存档文件（必须是 .zip）
        }

        data = {
            'bug_title': 'Game crashes during save',
            'steam_id': '765611979602874930',
            'version': '1.0.0',
            'description': "While attempting to save progress in the game, the application crashes and exits to the desktop without completing the save process.\n\nThis issue occurs consistently when saving after completing a mission or interacting with a large number of in-game assets.\nNo error message is displayed, but the crash creates a dump file in the game directory.\nThis makes it impossible to progress without losing data.\n\nSteps to Reproduce:\n1. Start the game and load any save file.\n2. Play for approximately 10–15 minutes, ensuring interactions with NPCs and looting items.\n3. Attempt to save the game manually or wait for an autosave trigger.\n4. Observe that the game crashes without saving progress.\n\nExpected Behavior:\nThe game should save progress without any interruption or crash.\n\nAdditional Information:\n- Crash occurs in both manual and autosave attempts.\n- System Specs: Windows 10, Intel i7-9700K, RTX 3070, 16GB RAM.\n- No mods or third-party add-ons installed.",
            'hardware': 'CPU: Intel i7-8700, GPU: NVIDIA GTX 1080, RAM: 16GB, Driver: 531.18',
            'type': 'Crash',
            'name': 'John Doe',     # （可选）
            'email': 'johndoe@example.com'  # （可选）
        }

        # 发送 POST 请求
        while True:
            response = requests.post(url, files=files, data=data)

            # 输出响应结果
            print("Status Code:", response.status_code)
            try:
                print("Response JSON:", response.json())
            except ValueError:
                print("Response Text:", response.text)
            break
except FileNotFoundError as e:
    print(f"Error: File not found - {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
