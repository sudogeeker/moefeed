import sys
import csv
import ipaddress
import re

SUPERNET = ipaddress.ip_network('2a0f:1cc0::/29')

# 用于检查国家代码 (ISO 3166-1 alpha-2) 的基本正则表达式
COUNTRY_CODE_REGEX = re.compile(r'^[A-Z]{2}$')

# 标记是否有任何错误
validation_failed = False

# 从命令行参数获取文件列表
files_to_check = sys.argv[1:]

if not files_to_check:
    print("No relevant .csv files changed in 'client_feeds/'. Skipping.")
    sys.exit(0)

for filepath in files_to_check:
    print(f"--- Validating file: {filepath} ---")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # 使用 csv.reader 处理，以正确处理带引号的字段
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                linenum = i + 1
                
                # 跳过空行
                if not row:
                    continue

                # 1. 检查列数 (geofeed 至少 2 列，最多 4 列)
                if not (2 <= len(row) <= 4):
                    print(f"  ERROR: {filepath}:{linenum}: Invalid column count ({len(row)}). Must be 2, 3, or 4.")
                    validation_failed = True
                    continue
                
                ip_prefix = row[0].strip()
                country_code = row[1].strip()

                # 2. 验证 IP 前缀
                try:
                    network = ipaddress.ip_network(ip_prefix)
                except ValueError as e:
                    print(f"  ERROR: {filepath}:{linenum}: Invalid IP prefix '{ip_prefix}'. Details: {e}")
                    validation_failed = True
                    continue
                
                # 3. 检查 IP 是否在允许的网内
                if not network.subnet_of(SUPERNET):
                    print(f"  ERROR: {filepath}:{linenum}: IP prefix '{ip_prefix}' is NOT within the allowed range {SUPERNET}.")
                    validation_failed = True
                
                # 4. 验证国家代码格式
                if not COUNTRY_CODE_REGEX.match(country_code):
                    print(f"  ERROR: {filepath}:{linenum}: Invalid country code format '{country_code}'. Must be 2 uppercase letters (e.g., US, JP).")
                    validation_failed = True

    except FileNotFoundError:
        # 如果文件在 PR 中被删除，这里会找不到，忽略即可
        print(f"  INFO: File {filepath} not found (likely deleted in this PR). Skipping.")
    except Exception as e:
        print(f"  FATAL: Could not process file {filepath}. Error: {e}")
        validation_failed = True

# --- 总结 ---
if validation_failed:
    print("\nValidation FAILED. See errors above.")
    sys.exit(1) # 退出代码 1，使 GitHub Action 失败
else:
    print("\nAll changed geofeed files validated SUCCESSFULLY.")
    sys.exit(0) # 退出代码 0，使 GitHub Action 成功
