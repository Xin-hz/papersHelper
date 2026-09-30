"""论文采集模块测试脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.paper_collector import search_papers, collect_papers


def test_search():
    """测试论文搜索功能"""
    print("=" * 50)
    print("🔍 测试论文搜索功能")
    print("=" * 50)

    # 测试搜索
    query = "machine learning education"
    print(f"\n搜索关键词: {query}")

    try:
        results = search_papers(
            query=query,
            sources=["arxiv"],
            max_results=5,
        )

        # 显示结果
        total = sum(len(papers) for papers in results.values())
        print(f"✅ 搜索完成，共找到 {total} 篇论文\n")

        for source, papers in results.items():
            print(f"📚 数据源: {source}")
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {paper.title}")
                print(f"   作者: {', '.join(paper.authors[:3])}" + ("..." if len(paper.authors) > 3 else ""))
                print(f"   年份: {paper.year}")
                print(f"   PDF可用: {'✅' if paper.pdf_available else '❌'}")
                if paper.abstract:
                    abstract = paper.abstract[:150] + "..." if len(paper.abstract) > 150 else paper.abstract
                    print(f"   摘要: {abstract}")

        return results

    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_collect(query: str = "early childhood education"):
    """测试论文采集功能"""
    print("\n" + "=" * 50)
    print("📥 测试论文采集功能")
    print("=" * 50)

    print(f"\n采集关键词: {query}")
    print("提示：这将下载 PDF 并向量化入库，可能需要几分钟时间")

    # 询问用户确认
    confirm = input("\n是否继续？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 用户取消操作")
        return

    try:
        result = collect_papers(
            query=query,
            sources=["arxiv"],
            max_papers=3,  # 限制采集数量，避免时间过长
            auto_ingest=True,
        )

        print(f"\n{'✅' if result['success'] else '❌'} {result['message']}")
        print(f"📊 统计信息:")
        print(f"   搜索到: {result.get('collected', 0)} 篇")
        print(f"   成功入库: {result.get('ingested', 0)} 篇")
        print(f"   失败: {result.get('failed', 0)} 篇")

        if result.get('stats'):
            print(f"   文档片段: {result['stats'].get('total_chunks', 0)} 个")

        return result

    except Exception as e:
        print(f"❌ 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_env():
    """测试环境配置"""
    print("=" * 50)
    print("🔧 检查环境配置")
    print("=" * 50)

    # 检查依赖包
    required_packages = [
        ("arxiv", "arxiv"),
        ("requests", "requests"),
        ("tqdm", "tqdm"),
    ]

    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name}")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install", " ".join(missing_packages))
        return False

    print("\n✅ 所有必要依赖包已安装")

    # 检查环境变量
    from app.config import get_settings
    settings = get_settings()

    print(f"\n📝 配置信息:")
    print(f"   数据库: {settings.database_url[:20]}...")
    print(f"   上传目录: {settings.upload_dir}")
    print(f"   LLM提供商: {getattr(settings, 'llm_provider', 'unknown')}")

    return True


def interactive_mode():
    """交互模式"""
    print("\n" + "=" * 50)
    print("🎯 论文采集模块 - 交互式测试")
    print("=" * 50)

    while True:
        print("\n请选择操作:")
        print("1. 检查环境配置")
        print("2. 搜索论文（不下载数据库）")
        print("3. 采集论文（下载并入库）")
        print("4. 退出")

        choice = input("\n请输入选项 (1-4): ").strip()

        if choice == "1":
            test_env()
        elif choice == "2":
            query = input("请输入搜索关键词: ").strip()
            if query:
                test_search()
        elif choice == "3":
            query = input("请输入采集关键词: ").strip()
            if query:
                test_collect(query)
        elif choice == "4":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选项，请重新选择")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "search":
            query = sys.argv[2] if len(sys.argv) > 2 else "machine learning"
            test_search()
        elif command == "collect":
            query = sys.argv[2] if len(sys.argv) > 2 else "education"
            test_collect(query)
        elif command == "env":
            test_env()
        elif command == "interactive":
            interactive_mode()
        else:
            print("用法:")
            print("  python test_paper_collector.py search [关键词]")
            print("  python test_paper_collector.py collect [关键词]")
            print("  python test_paper_collector.py env")
            print("  python test_paper_collector.py interactive")
    else:
        # 默认运行交互模式
        interactive_mode()


if __name__ == "__main__":
    main()