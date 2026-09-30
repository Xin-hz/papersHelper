#!/usr/bin/env python3
"""测试论文采集和入库流程"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_paper_search():
    """测试论文搜索"""
    print("🔍 测试论文搜索...")

    response = requests.post(f"{API_BASE}/api/papers/search", json={
        "query": "early childhood education",
        "sources": ["arxiv"],
        "max_results": 2,
        "year_range": None
    })

    if response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("papers"):
            paper_count = sum(len(papers) for papers in data["papers"].values())
            print(f"✅ 搜索成功: 找到 {paper_count} 篇论文")

            # 显示第一篇论文信息
            for source, papers in data["papers"].items():
                if papers:
                    first_paper = papers[0]
                    print(f"   数据源: {source}")
                    print(f"   标题: {first_paper['title'][:60]}...")
                    print(f"   PDF可用: {first_paper['pdf_available']}")
                    break
            return True
        else:
            print("❌ 搜索失败: 没有找到论文")
            return False
    else:
        print(f"❌ 搜索请求失败: {response.status_code}")
        return False

def test_paper_collection():
    """测试论文采集"""
    print("\n📥 测试论文采集...")

    response = requests.post(f"{API_BASE}/api/papers/collect", json={
        "query": "education research",
        "sources": ["arxiv"],
        "max_papers": 1,
        "year_range": None,
        "auto_ingest": True
    }, timeout=180)  # 设置3分钟超时

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ 采集成功:")
            print(f"   搜索到: {data.get('collected', 0)} 篇")
            print(f"   已入库: {data.get('ingested', 0)} 篇")
            print(f"   失败: {data.get('failed', 0)} 篇")
            print(f"   消息: {data.get('message', 'N/A')}")
            return data.get('ingested', 0) > 0
        else:
            print(f"❌ 采集失败: {data.get('message', '未知错误')}")
            return False
    else:
        print(f"❌ 采集请求失败: {response.status_code}")
        try:
            print(f"   错误详情: {response.text}")
        except:
            pass
        return False

def test_knowledge_stats():
    """测试知识库统计"""
    print("\n📊 测试知识库统计...")

    response = requests.get(f"{API_BASE}/api/knowledge/stats")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            stats = data.get("stats", {})
            print(f"✅ 统计成功:")
            print(f"   文档数: {stats.get('document_count', 0)}")
            print(f"   向量片段: {stats.get('vector_count', 0)}")
            print(f"   数据库大小: {stats.get('db_size_bytes', 0)} bytes")
            return True
        else:
            print("❌ 统计失败")
            return False
    else:
        print(f"❌ 统计请求失败: {response.status_code}")
        return False

def test_knowledge_search():
    """测试知识库检索"""
    print("\n🔎 测试知识库检索...")

    response = requests.post(f"{API_BASE}/api/knowledge/search", json={
        "query": "education",
        "top_k": 2
    })

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            results = data.get("results", [])
            print(f"✅ 检索成功: 找到 {len(results)} 个相关片段")
            if results:
                print(f"   最高相似度: {results[0].get('score', 0)*100:.1f}%")
                print(f"   来源: {results[0].get('metadata', {}).get('source', 'N/A')}")
            return True
        else:
            print(f"❌ 检索失败: {data.get('message', '未知错误')}")
            return False
    else:
        print(f"❌ 检索请求失败: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试论文采集和入库流程\n")
    print("=" * 50)

    results = []

    # 测试搜索
    results.append(("论文搜索", test_paper_search()))

    # 测试采集
    results.append(("论文采集", test_paper_collection()))

    # 测试统计
    results.append(("知识库统计", test_knowledge_stats()))

    # 测试检索
    results.append(("知识库检索", test_knowledge_search()))

    print("\n" + "=" * 50)
    print("📋 测试结果总结:")

    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查相关功能")