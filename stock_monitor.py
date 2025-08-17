#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极库存监控脚本 (浏览器模式-防Cloudflare)
功能：监控商品库存和价格变化，通过Telegram发送通知，并作为系统服务稳定运行。
"""

import re
import time
import json
import os
from datetime import datetime
import requests # 保留，因为发送Telegram消息时仍在使用
import undetected_chromedriver as uc # 导入新库以模拟浏览器

# ======================================================================
#                            配置区域
# ======================================================================

# --- Telegram Bot 配置 (必须修改) ---
TELEGRAM_BOT_TOKEN = "在这里替换为你的Bot Token"
TELEGRAM_CHAT_ID = "在这里替换为你的电报ID"

# --- 监控商品列表 (请根据需求修改) ---
MONITOR_PRODUCTS = [
{
"name": "商品1", # 可自行更改名称
"url": "https://example.com/product1",
"stock_pattern": r'库存\((\d+)\)', # 修正为正确的库存匹配规则
"price_pattern": r'¥\s*(\d+\.?\d*)' # 修正为正确的价格匹配规则
},
# 下面两个商品，如果网站结构和第一个相同，也需要用新的匹配规则
# 如果不同，则需要为它们单独查找规则
{
"name": "商品2",
"url": "https://example.com/product2",
"stock_pattern": r'库存\((\d+)\)',
"price_pattern": r'¥\s*(\d+\.?\d*)'
},
{
"name": "商品3",
"url": "https://example.com/product1",
"stock_pattern": r'库存\((\d+)\)',
"price_pattern": r'¥\s*(\d+\.?\d*)'
}
]

# --- 全局设置 ---
CHECK_INTERVAL = 3600  # 检查间隔（秒）, 3600 = 1小时
DATA_FILE = "monitor_data.json" # 数据存储文件

# ======================================================================
#                            核心函数区域
# ======================================================================

def load_history():
    """加载历史数据"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(data):
    """保存历史数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_page_content(url):
    """获取网页内容 (使用 Selenium + undetected-chromedriver 版本，防Cloudflare)"""
    driver = None # 先声明driver变量
    try:
        print("   (使用浏览器模式获取网页...)")
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu') # 在某些服务器上需要
        
        driver = uc.Chrome(options=options)
        driver.get(url)
        
        # 等待Cloudflare的JS验证完成，如果网络慢或验证复杂可适当增加
        time.sleep(8) 
        
        html_content = driver.page_source
        return html_content
    except Exception as e:
        print(f"❌ 使用浏览器获取网页失败: {e}")
        return None
    finally:
        # 确保浏览器进程被关闭以释放资源
        if driver:
            driver.quit()

def extract_data(html_content, stock_pattern, price_pattern):
    """从HTML中提取库存和价格"""
    stock, price = None, None
    if stock_pattern and (match := re.search(stock_pattern, html_content, re.IGNORECASE)):
        stock = int(match.group(1))
    if price_pattern and (match := re.search(price_pattern, html_content, re.IGNORECASE)):
        price = float(match.group(1))
    return stock, price

def send_telegram_message(message):
    """发送Telegram消息"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ 消息发送成功")
        else:
            print(f"❌ 消息发送失败: {response.text}")
    except Exception as e:
        print(f"❌ 发送消息异常: {e}")

def format_change_message(product_name, old_stock, new_stock, old_price, new_price, url):
    """格式化变化消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"📦 *{product_name}* 监控提醒\n\n"
    
    if new_stock is not None:
        if old_stock is not None and old_stock != new_stock:
            emoji = "📈" if new_stock > old_stock else "📉"
            message += f"{emoji} 库存变化: {old_stock} → *{new_stock}*\n"
        else:
            message += f"📦 当前库存: *{new_stock}*\n"
            
    if new_price is not None:
        if old_price is not None and old_price != new_price:
            emoji = "💰" if new_price < old_price else "💸"
            message += f"{emoji} 价格变化: ¥{old_price} → *¥{new_price}*\n"
        else:
            message += f"💰 当前价格: *¥{new_price}*\n"
            
    message += f"\n🕐 检查时间: {timestamp}\n🔗 [点击查看商品]({url})"
    return message

def monitor_product(product, history):
    """监控单个商品"""
    name = product['name']
    print(f"🔍 检查商品: {name}")
    
    html_content = get_page_content(product['url'])
    if not html_content:
        return
    
    current_stock, current_price = extract_data(html_content, product['stock_pattern'], product['price_pattern'])
    product_history = history.get(name, {})
    old_stock, old_price = product_history.get('stock'), product_history.get('price')
    
    print(f"    库存: {old_stock} → {current_stock}")
    print(f"    价格: {old_price} → {current_price}")
    
    if not product_history or old_stock != current_stock or old_price != current_price:
        print(f"   ✨ 发现状态变化，准备发送通知...")
        message = format_change_message(name, old_stock, current_stock, old_price, current_price, product['url'])
        send_telegram_message(message)
    
    if current_stock is not None or current_price is not None:
        history[name] = {'stock': current_stock, 'price': current_price}

def main():
    """主函数"""
    print("🚀 库存监控脚本启动 (浏览器模式)")
    print(f"📊 监控商品数量: {len(MONITOR_PRODUCTS)}")
    print(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
    print("-" * 50)
    
    if "在这里替换" in TELEGRAM_BOT_TOKEN or "在这里替换" in TELEGRAM_CHAT_ID:
        print("❌ 致命错误: 请先修改脚本文件，配置好你的 Telegram Bot Token 和 Chat ID!")
        return
    
    history = load_history()
    
    while True:
        print(f"\n🔄 开始检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for product in MONITOR_PRODUCTS:
            try:
                monitor_product(product, history)
            except Exception as e:
                print(f"❌ 监控 {product.get('name', '未知商品')} 失败: {e}")
        save_history(history)
        print(f"✅ 本轮检查完成，等待 {CHECK_INTERVAL} 秒...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 监控脚本已由用户手动停止。")
    except Exception as e:
        print(f"\n💥 程序因无法恢复的严重错误而终止: {e}")