#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双色球数据更新工具
自动获取最新开奖数据并补全到CSV文件
"""

import csv
import requests
import json
import time
from datetime import datetime, timedelta
import os

class LotteryDataUpdater:
    def __init__(self, csv_file="lottery_data.csv"):
        self.csv_file = csv_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.existing_data = {}
        self.load_existing_data()

    def load_existing_data(self):
        """加载现有CSV数据"""
        if not os.path.exists(self.csv_file):
            print(f"文件 {self.csv_file} 不存在")
            return

        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.existing_data[row['issue']] = row

        print(f"已加载现有数据: {len(self.existing_data)} 期")

        # 找到最新期号
        if self.existing_data:
            latest_issue = max(self.existing_data.keys())
            print(f"最新期号: {latest_issue}")
            return latest_issue
        return None

    def fetch_from_cwl_api(self):
        """从中国福利彩票官网API获取数据"""
        print("\n尝试从中国福利彩票官网获取...")
        url = "https://www.cwl.gov.cn/ygkj/wqkjgg/findDrawNotice"

        all_data = []
        page = 1

        while page <= 20:  # 最多20页
            params = {
                'name': 'ssq',
                'pageCount': 100,
                'pageNo': page
            }

            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    items = result.get('data', {}).get('list', [])

                    if not items:
                        break

                    for item in items:
                        issue = item.get('lotteryDrawNum', '')
                        draw_date = item.get('lotteryDrawTime', '')
                        draw_result = item.get('lotteryDrawResult', '')

                        if draw_result and '+' in draw_result:
                            parts = draw_result.split('+')
                            red_balls = parts[0]
                            blue_ball = parts[1] if len(parts) > 1 else ''

                            # 获取销售金额和奖池
                            sale_money = item.get('saleAmount', '')
                            prize_pool = item.get('poolAmount', '')

                            # 计算星期
                            date_obj = datetime.strptime(draw_date, '%Y-%m-%d %H:%M:%S')
                            week_day = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][date_obj.weekday()]

                            all_data.append({
                                'issue': issue,
                                'openTime': draw_date[:10],
                                'frontWinningNum': red_balls.replace(',', ' '),
                                'backWinningNum': blue_ball,
                                'seqFrontWinningNum': red_balls.replace(',', ' '),
                                'seqBackWinningNum': blue_ball,
                                'saleMoney': sale_money,
                                'r9SaleMoney': '',
                                'prizePoolMoney': prize_pool,
                                'week': week_day
                            })

                    print(f"  第{page}页: 获取{len(items)}条，累计{len(all_data)}条")
                    page += 1
                    time.sleep(0.5)
                else:
                    print(f"  请求失败: {response.status_code}")
                    break

            except Exception as e:
                print(f"  请求出错: {e}")
                break

        return all_data

    def fetch_from_500lottery(self):
        """从500彩票网获取数据"""
        print("\n尝试从500彩票网获取...")
        url = "http://datachart.500.com/ssq/history/newinc/history.php"

        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                # 解析返回的数据
                print("  数据获取成功，正在解析...")
                # 这里需要解析具体的响应格式
        except Exception as e:
            print(f"  请求失败: {e}")

        return []

    def fetch_from_api163(self):
        """从163彩票API获取"""
        print("\n尝试从网易彩票获取...")
        url = "https://caipiao.163.com/award/ssq/"

        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                print("  数据获取成功，正在解析...")
        except Exception as e:
            print(f"  请求失败: {e}")

        return []

    def merge_and_save(self, new_data):
        """合并数据并保存到CSV"""
        if not new_data:
            print("没有新数据需要保存")
            return

        # 统计新增数据
        added_count = 0
        updated_count = 0

        for item in new_data:
            issue = item['issue']
            if issue in self.existing_data:
                # 检查是否需要更新
                existing = self.existing_data[issue]
                if existing['frontWinningNum'] != item['frontWinningNum']:
                    self.existing_data[issue] = item
                    updated_count += 1
            else:
                self.existing_data[issue] = item
                added_count += 1

        print(f"\n数据统计:")
        print(f"  新增: {added_count} 期")
        print(f"  更新: {updated_count} 期")
        print(f"  总计: {len(self.existing_data)} 期")

        # 按期号排序（从新到旧）
        sorted_data = sorted(self.existing_data.values(),
                            key=lambda x: x['issue'],
                            reverse=True)

        # 保存到CSV
        fieldnames = ['issue', 'openTime', 'frontWinningNum', 'backWinningNum',
                     'seqFrontWinningNum', 'seqBackWinningNum', 'saleMoney',
                     'r9SaleMoney', 'prizePoolMoney', 'week']

        backup_file = self.csv_file.replace('.csv', '_backup.csv')

        try:
            # 备份原文件
            if os.path.exists(self.csv_file):
                with open(backup_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.existing_data.values())
                print(f"\n已备份原文件到: {backup_file}")

            # 保存更新后的数据
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(sorted_data)

            print(f"数据已保存到: {self.csv_file}")

            # 显示最新10期
            print(f"\n最新10期开奖结果:")
            print("-" * 80)
            for item in sorted_data[:10]:
                print(f"{item['issue']} | {item['openTime']} | {item['frontWinningNum']} + {item['backWinningNum']} | {item['week']}")
            print("-" * 80)

        except Exception as e:
            print(f"保存失败: {e}")

    def run(self):
        """执行更新"""
        print("=" * 80)
        print("双色球数据更新工具")
        print("=" * 80)

        # 尝试多个数据源
        all_new_data = []

        sources = [
            self.fetch_from_cwl_api,
            self.fetch_from_500lottery,
            self.fetch_from_api163,
        ]

        for source in sources:
            try:
                data = source()
                if data:
                    all_new_data.extend(data)
                    # 如果成功获取数据，不再尝试其他源
                    if len(data) > 10:
                        break
            except Exception as e:
                print(f"数据源失败: {e}")
                continue

        if all_new_data:
            self.merge_and_save(all_new_data)
        else:
            print("\n未能获取到新数据")
            print("\n您可以:")
            print("1. 访问中国福利彩票官网手动下载: http://www.cwl.gov.cn/")
            print("2. 访问500彩票网: http://datachart.500.com/ssq/")
            print("3. 访问网易彩票: https://caipiao.163.com/award/ssq/")


def main():
    updater = LotteryDataUpdater("lottery_data.csv")
    updater.run()


if __name__ == "__main__":
    main()
