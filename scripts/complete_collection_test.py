#!/usr/bin/env python3
"""
完整的论文采集测试：搜索→下载→入库闭环
"""

import sys
sys.path.append('/Users/Stars/Projects/PapersHelper')

from app.services.paper_collector import search_papers, PaperDownloader, PaperIngester
from app.services.vector_store import add_documents_to_store
from pathlib import Path

def complete_paper_collection_test():
    """完整的论文采集测试"""

    print("🚀 开始完整的论文采集测试")
    print("=" * 60)

    # 1. 搜索论文
    print("\n🔍 第1步：搜索论文")
    print("-" * 40)

    query = "child education"  # 使用简单的英文关键词
    sources = ["arxiv"]  # 只用arXiv，因为OpenAlex API不稳定
    max_results = 1

    print(f"关键词: {query}")
    print(f"数据源: {sources}")

    try:
        search_results = search_papers(query, sources, max_results)

        total_papers = sum(len(papers) for papers in search_results.values())
        print(f"✅ 搜索成功: 找到 {total_papers} 篇论文")

        if total_papers == 0:
            print("❌ 没有找到论文，无法继续测试")
            return False

        # 显示搜索结果
        for source, papers in search_results.items():
            if papers:
                for paper in papers[:2]:
                    # 处理可能是字典或对象的情况
                    if isinstance(paper, dict):
                        title = paper.get('title', 'Unknown')
                        pdf_available = paper.get('pdf_available', False)
                        download_url = paper.get('download_url', '')
                    else:
                        title = getattr(paper, 'title', 'Unknown')
                        pdf_available = getattr(paper, 'pdf_available', False)
                        download_url = getattr(paper, 'download_url', '')

                    print(f"  [{source}] {title[:70]}...")
                    print(f"    PDF可用: {pdf_available}")
                    print(f"    下载链接: {download_url[:60]}...")

    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False

    # 2. 下载PDF
    print(f"\n📥 第2步：下载PDF")
    print("-" * 40)

    downloader = PaperDownloader()
    downloaded_files = []

    for source, papers in search_results.items():
        # 转换为统一的格式
        paper_list = []
        for p in papers:
            if isinstance(p, dict):
                # 过滤掉不需要的字段
                filtered_dict = {k: v for k, v in p.items() if k != 'collected_at'}
                from app.services.paper_collector.paper_collector import PaperMetadata
                paper_list.append(PaperMetadata(**filtered_dict))
            else:
                paper_list.append(p)

        for paper in paper_list[:1]:  # 只下载第一篇
            title = getattr(paper, 'title', 'Unknown')[:50]
            print(f"正在下载: {title}...")

            try:
                pdf_path = downloader.download_pdf(paper)

                if pdf_path:
                    downloaded_files.append((pdf_path, paper))
                    print(f"✅ 下载成功: {Path(pdf_path).name}")
                else:
                    print(f"❌ 下载失败: {title}")

            except Exception as e:
                print(f"❌ 下载出错: {e}")

    if not downloaded_files:
        print("❌ 没有成功下载任何PDF")
        return False

    # 3. 入库
    print(f"\n📚 第3步：向量入库")
    print("-" * 40)

    ingester = PaperIngester()
    successful_ingests = 0

    for pdf_path, paper_metadata in downloaded_files:
        print(f"正在入库: {paper_metadata.title[:50]}...")

        try:
            if ingester.ingest_paper(pdf_path, paper_metadata):
                successful_ingests += 1
                print(f"✅ 入库成功: {paper_metadata.title[:50]}...")
            else:
                print(f"❌ 入库失败: {paper_metadata.title[:50]}...")

        except Exception as e:
            print(f"❌ 入库出错: {e}")

    # 4. 验证结果
    print(f"\n📊 第4步：验证结果")
    print("-" * 40)

    stats = ingester.get_stats()
    print(f"入库统计:")
    print(f"  成功: {stats['ingested']} 篇")
    print(f"  失败: {stats['failed']} 篇")
    print(f"  总片段: {stats['total_chunks']} 个")

    # 检查数据库是否真的增加了
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='papers_helper',
            user='postgres',
            password='postgres'
        )
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding")
        total_vectors = cursor.fetchone()[0]

        print(f"\n数据库验证:")
        print(f"  当前向量片段总数: {total_vectors}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"⚠️ 无法验证数据库: {e}")

    # 最终结果
    print("\n" + "=" * 60)
    if successful_ingests > 0:
        print("🎉 完整闭环测试成功!")
        print(f"✅ 搜索 → 下载 → 入库 全流程正常")
        return True
    else:
        print("❌ 闭环测试失败")
        return False

if __name__ == "__main__":
    success = complete_paper_collection_test()
    exit(0 if success else 1)