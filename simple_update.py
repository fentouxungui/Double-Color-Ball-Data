#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双色球数据简单更新脚本
自动从网易彩票获取最新的开奖数据
更新后自动按期号从新到旧排序
"""

import requests
import re
import csv
from datetime import datetime
import os

def get_latest_period_from_csv(csv_file='lottery_data.csv'):
    """从CSV文件中获取最新的期号"""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 1:
                last_line = lines[-1].strip()
                latest_period = last_line.split(',')[0]
                return latest_period
        return None
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return None

def fetch_lottery_data(period):
    """从网易彩票获取指定期号的开奖数据"""
    url = f"https://sports.163.com/caipiao/lottery/ssq/{period}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            full_text = response.text

            # 提取期号
            period_match = re.search(r'(\d{7})期', full_text)
            period_num = period_match.group(1) if period_match else period

            # 提取开奖日期
            date_match = re.search(r'开奖日期:\s*(\d{4})-(\d{1,2})-(\d{1,2})', full_text)
            date = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}" if date_match else ""

            # 提取出球顺序和蓝球
            draw_order = ""
            blue_ball = ""
            red_balls = ""
            red_balls_sorted = ""

            order_match = re.search(r'出球顺序:\s*((?:\d{2}\s*){6})\s*\|\s*(\d{2})', full_text)
            if order_match:
                draw_order = ' '.join(order_match.group(1).split())
                blue_ball = order_match.group(2)
                red_balls_list = draw_order.split()
                sorted_list = sorted(red_balls_list)
                red_balls = ' '.join(sorted_list)
                red_balls_sorted = ' '.join(sorted_list)

            # 提取销售金额和奖池金额
            sales = 0
            prize_pool = 0
            amounts = re.findall(r'([\d.]+)\s*亿', full_text)
            if len(amounts) >= 1:
                sales = int(float(amounts[0]) * 100000000)
            if len(amounts) >= 2:
                prize_pool = int(float(amounts[1]) * 100000000)

            # 计算星期
            weekday = ""
            if date:
                try:
                    date_obj = datetime.strptime(date, '%Y/%m/%d')
                    weekday = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][date_obj.weekday()]
                except:
                    pass

            return {
                '期号': period_num,
                '开奖日期': date,
                '红球': red_balls,
                '蓝球': blue_ball,
                '排序红球': red_balls_sorted,
                '排序蓝球': blue_ball,
                '出球顺序': draw_order,
                '销售额': sales,
                '奖池金额': prize_pool,
                '星期': weekday
            }
        else:
            return None

    except Exception as e:
        print(f"获取期号 {period} 时出错: {e}")
        return None

def append_to_csv(data_list, csv_file='lottery_data.csv'):
    """将数据追加到CSV文件（使用UTF-8 with BOM编码）"""
    try:
        # 读取现有数据
        existing_data = []
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                existing_data.append(row)

        # 添加新数据
        if isinstance(data_list, dict):
            data_list = [data_list]
        existing_data.extend(data_list)

        # 写回文件（使用UTF-8 with BOM）
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_data)

        return True
    except Exception as e:
        print(f"追加数据到CSV时出错: {e}")
        return False

def get_next_period(current_period):
    """计算下一期的期号"""
    year = int(current_period[:4])
    num = int(current_period[4:])

    num += 1
    if num > 155:  # 假设每年最多155期
        num = 1
        year += 1

    return f"{year}{num:03d}"

def sort_csv_by_period_desc(csv_file='lottery_data.csv'):
    """读取CSV文件，按期号降序排序（从最新到最早），然后写回"""
    try:
        print()
        print("正在按期号排序（从新到旧）...", end=' ')

        # 备份原文件
        backup_file = csv_file.replace('.csv', '_before_sort.csv')
        import shutil
        shutil.copy2(csv_file, backup_file)

        # 读取所有数据（使用utf-8-sig处理BOM）
        data_list = []
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            # 清理列名中的BOM字符
            fieldnames = [name.replace('\ufeff', '') for name in fieldnames]
            for row in reader:
                # 清理行中的列名
                clean_row = {}
                for key, value in row.items():
                    clean_key = key.replace('\ufeff', '') if key else ''
                    clean_row[clean_key] = value
                data_list.append(clean_row)

        # 按期号降序排序（使用清理后的列名）
        data_list.sort(key=lambda x: int(x.get('期号', '0')), reverse=True)

        # 写回文件（使用UTF-8 with BOM，方便Excel识别）
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_list)

        print(f"[完成]")
        print(f"已备份原文件到: {backup_file}")
        print(f"最新期号: {data_list[0]['期号'] if data_list else 'N/A'}")

        return True
    except Exception as e:
        print(f"[失败] {e}")
        import traceback
        traceback.print_exc()
        return False

def update_lottery_data(max_new_periods=20):
    """更新彩票数据"""
    print("=" * 60)
    print("双色球数据更新工具")
    print("=" * 60)
    print()

    # 获取当前最新期号
    latest_period = get_latest_period_from_csv()
    if not latest_period:
        print("错误：无法读取当前数据文件")
        return

    print(f"当前最新期号: {latest_period}")
    print(f"准备获取新数据...")
    print()

    # 从下一期开始获取
    current_period = get_next_period(latest_period)
    new_records = []
    failed_periods = []

    for i in range(max_new_periods):
        print(f"正在获取 {current_period} 期...", end=' ')

        data = fetch_lottery_data(current_period)
        if data:
            new_records.append(data)
            print(f"[OK] {data['开奖日期']} - {data['红球']} + {data['蓝球']}")
            current_period = get_next_period(current_period)
        else:
            print(f"[FAIL] 期号不存在或未开奖")
            failed_periods.append(current_period)
            current_period = get_next_period(current_period)

    # 追加新数据到CSV
    if new_records:
        print()
        print(f"成功获取 {len(new_records)} 期新数据")
        print("正在写入CSV文件...", end=' ')

        # 一次性写入所有新数据
        append_to_csv(new_records)

        print("[完成]")
        print()
        print("更新详情：")
        for data in new_records:
            print(f"  {data['期号']} | {data['开奖日期']} | {data['红球']} + {data['蓝球']}")

    # 无论是否有新数据，都执行排序
    if new_records:
        print()
    sort_csv_by_period_desc()

    if not new_records:
        print()
        print("没有找到新数据")

    if failed_periods:
        print()
        print(f"未找到的期号（可能未开奖）: {', '.join(failed_periods[:5])}{'...' if len(failed_periods) > 5 else ''}")

    print()
    print("=" * 60)
    print("更新完成！")
    print("=" * 60)

if __name__ == "__main__":
    # 尝试获取最多20期新数据
    update_lottery_data(max_new_periods=20)
