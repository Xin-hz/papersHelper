#!/usr/bin/env python3
"""直接测试Collector页面的功能"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_search_function():
    """模拟前端的搜索功能"""
    print("🔍 模拟前端搜索功能...")

    # 模拟Collector.vue中的handleSearch函数
    search_data = {
        "query": "education children",
        "sources": ["arxiv"],
        "max_results": 3,
        "year_range": None
    }

    print(f"搜索参数: {json.dumps(search_data, indent=2)}")

    try:
        response = requests.post(f"{API_BASE}/api/papers/search", json=search_data)
        response.raise_for_status()
        data = response.json()

        print(f"✅ 搜索成功!")
        print(f"找到 {data.get('total', 0)} 篇论文")

        if data.get('papers'):
            for source, papers in data['papers'].items():
                if papers:
                    print(f"  {source}: {len(papers)} 篇")
                    for paper in papers[:2]:
                        print(f"    - {paper['title'][:60]}...")
                        print(f"      PDF可用: {paper['pdf_available']}")

        return data.get('success', False)

    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False

def test_collect_function():
    """模拟前端的采集功能"""
    print("\n📥 模拟前端采集功能...")

    collect_data = {
        "query": "education test",
        "sources": ["arxiv"],
        "max_papers": 1,
        "auto_ingest": False  # 只测试采集，不入库
    }

    print(f"采集参数: {json.dumps(collect_data, indent=2)}")

    try:
        response = requests.post(f"{API_BASE}/api/papers/collect", json=collect_data, timeout=60)
        response.raise_for_status()
        data = response.json()

        print(f"✅ 采集成功!")
        print(f"结果: {data.get('message', 'N/A')}")
        print(f"下载: {data.get('collected', 0)} 篇")
        print(f"入库: {data.get('ingested', 0)} 篇")
        print(f"失败: {data.get('failed', 0)} 篇")

        return data.get('success', False)

    except Exception as e:
        print(f"❌ 采集失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试Collector页面功能\n")
    print("=" * 50)

    # 测试搜索
    search_ok = test_search_function()

    # 测试采集
    collect_ok = test_collect_function()

    print("\n" + "=" * 50)
    print("📋 测试结果:")
    print(f"  搜索功能: {'✅ 正常' if search_ok else '❌ 失败'}")
    print(f"  采集功能: {'✅ 正常' if collect_ok else '❌ 失败'}")

    if search_ok and collect_ok:
        print("\n🎉 Collector功能完全正常！")
        print("如果你在前端点击没反应，可能是以下原因:")
        print("1. 浏览器控制台有JavaScript错误")
        print("2. 网络连接问题")
        print("3. 前端页面没有正确加载")
    else:
        print("\n⚠️ 后端功能存在问题，请检查服务器日志")