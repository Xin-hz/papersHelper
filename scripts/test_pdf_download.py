#!/usr/bin/env python3
"""直接测试PDF下载功能"""

import requests
from pathlib import Path

# 你提到的两篇论文的测试链接
test_papers = [
    {
        "title": "青少年心理健康：现状、影响因素及优化策略",
        # 你需要提供实际的PDF链接
        "url": "",  # 请填入实际的PDF链接
    },
    {
        "title": "科学教育赋能留守儿童校园安全模式研究",
        # 你需要提供实际的PDF链接
        "url": "",  # 请填入实际的PDF链接
    }
]

def test_direct_download(url, title):
    """测试直接下载"""
    print(f"\n🔍 测试下载: {title}")
    print(f"链接: {url}")

    if not url:
        print("❌ 没有提供PDF链接")
        return False

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/pdf,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        response = requests.get(url, headers=headers, timeout=30)

        print(f"状态码: {response.status_code}")
        print(f"内容类型: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type:
                print(f"✅ 可以下载PDF ({len(response.content)} bytes)")
                return True
            else:
                print(f"⚠️ 不是PDF文件，可能是HTML页面")
                return False
        else:
            print(f"❌ 下载失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 下载出错: {e}")
        return False

print("🚀 PDF下载测试工具")
print("=" * 50)
print("\n请提供这两篇论文的实际PDF下载链接：")
print("1. 你可以在浏览器中右键点击'下载PDF'按钮")
print("2. 选择'复制链接地址'来获取真实的PDF链接")
print("3. 把链接填入上面的脚本中测试")