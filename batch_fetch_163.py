#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量从网易彩票获取双色球数据
"""

import requests
from bs4 import BeautifulSoup
import time
import re

def fetch_163_data(period):
    """从网易彩票获取指定期号的开奖数据"""
    url = f"https://sports.163.com/caipiao/lottery/ssq/{period}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # 获取全部文本内容
            full_text = response.text

            # 提取期号
            period_match = re.search(r'(\d{7})期', full_text)
            if period_match:
                period_num = period_match.group(1)
            else:
                period_num = period

            # 提取开奖日期
            date_match = re.search(r'开奖日期:\s*(\d{4})-(\d{1,2})-(\d{1,2})', full_text)
            if date_match:
                year, month, day = date_match.groups()
                date = f"{year}/{month}/{day}"
            else:
                date = ""

            # 提取出球顺序 (优先获取，因为这个信息更准确)
            draw_order = ""
            blue_ball = ""
            red_balls = ""
            red_balls_sorted = ""
            order_match = re.search(r'出球顺序:\s*((?:\d{2}\s*){6})\s*\|\s*(\d{2})', full_text)
            if order_match:
                draw_order = ' '.join(order_match.group(1).split())
                blue_ball = order_match.group(2)
                # 从出球顺序提取红球并排序
                red_balls_list = draw_order.split()
                sorted_list = sorted(red_balls_list)
                red_balls = ' '.join(sorted_list)
                red_balls_sorted = ' '.join(sorted_list)

            # 提取销售金额和奖池金额 - 查找所有"X.XX亿"模式
            sales = 0
            prize_pool = 0
            amounts = re.findall(r'([\d.]+)\s*亿', full_text)
            if len(amounts) >= 1:
                sales = int(float(amounts[0]) * 100000000)
            if len(amounts) >= 2:
                prize_pool = int(float(amounts[1]) * 100000000)

            # 计算星期
            if date:
                from datetime import datetime
                try:
                    date_obj = datetime.strptime(date, '%Y/%m/%d')
                    weekday = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][date_obj.weekday()]
                except:
                    weekday = ""
            else:
                weekday = ""

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
            print(f"期号 {period} 请求失败，状态码: {response.status_code}")
            return None

    except Exception as e:
        print(f"获取期号 {period} 时出错: {str(e)}")
        return None


def batch_fetch(start_period, end_period):
    """批量获取期号范围内的数据"""
    results = []

    start_year = int(start_period[:4])
    start_num = int(start_period[4:])
    end_year = int(end_period[:4])
    end_num = int(end_period[4:])

    current_year = start_year
    current_num = start_num

    while (current_year < end_year) or (current_year == end_year and current_num <= end_num):
        period = f"{current_year}{current_num:03d}"
        print(f"正在获取 {period} 期...")

        data = fetch_163_data(period)
        if data:
            results.append(data)
            print(f"[OK] {period} 期获取成功")
        else:
            print(f"[FAIL] {period} 期获取失败")

        time.sleep(0.5)  # 避免请求过快

        current_num += 1
        if current_num > 155:  # 假设每年最多155期
            current_num = 1
            current_year += 1

    return results


def save_to_csv(data_list, filename):
    """保存数据到CSV文件"""
    if not data_list:
        print("没有数据需要保存")
        return

    import csv

    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
        writer.writeheader()
        writer.writerows(data_list)

    print(f"数据已保存到 {filename}，共 {len(data_list)} 条记录")


if __name__ == "__main__":
    print("=" * 60)
    print("双色球数据批量获取工具（网易彩票）")
    print("=" * 60)
    print()

    # 获取2025年剩余数据
    print("开始获取2025年剩余数据...")
    data_2025 = batch_fetch("2025073", "2025155")
    save_to_csv(data_2025, "lottery_data_2025_partial.csv")
    print()

    # 获取2026年数据
    print("开始获取2026年数据...")
    data_2026 = batch_fetch("2026001", "2026030")
    save_to_csv(data_2026, "lottery_data_2026.csv")
    print()

    # 合并所有数据
    all_data = data_2025 + data_2026
    save_to_csv(all_data, "lottery_data_new.csv")

    print()
    print("=" * 60)
    print("数据获取完成！")
    print(f"2025年数据: {len(data_2025)} 条")
    print(f"2026年数据: {len(data_2026)} 条")
    print(f"总计: {len(all_data)} 条")
    print("=" * 60)
