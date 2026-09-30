"""自动化测试论文采集模块"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.paper_collector import search_papers, collect_papers


def test_search():
    """测试论文搜索功能"""
    print('=' * 50)
    print('🔍 测试论文搜索功能')
    print('=' * 50)

    # 测试搜索 - 使用教育相关的关键词
    query = 'early childhood education technology'
    print(f'\n搜索关键词: {query}')

    try:
        results = search_papers(
            query=query,
            sources=['arxiv'],
            max_results=5,
        )

        # 显示结果
        total = sum(len(papers) for papers in results.items())
        print(f'✅ 搜索完成，共找到 {total} 篇论文\n')

        for source, papers in results.items():
            print(f'📚 数据源: {source}')
            for i, paper in enumerate(papers, 1):
                # 处理字典格式
                if isinstance(paper, dict):
                    title = paper.get('title', 'N/A')
                    authors = paper.get('authors', [])
                    year = paper.get('year')
                    abstract = paper.get('abstract', '')
                    pdf_available = paper.get('pdf_available', False)
                    doi = paper.get('doi', 'N/A')
                else:
                    title = paper.title
                    authors = paper.authors
                    year = paper.year
                    abstract = paper.abstract
                    pdf_available = paper.pdf_available
                    doi = paper.doi

                print(f'\n{i}. {title}')
                authors_list = authors[:2] if isinstance(authors, list) else []
                authors_str = ', '.join(authors_list)
                if len(authors) > 2:
                    authors_str += '...'
                print(f'   作者: {authors_str}')
                print(f'   年份: {year}')
                print(f'   PDF可用: {"✅" if pdf_available else "❌"}')
                if abstract:
                    abstract_text = abstract[:100] + '...' if len(abstract) > 100 else abstract
                    print(f'   摘要: {abstract_text}')
                print(f'   DOI: {doi}')

        print(f'\n🎉 搜索测试成功！')
        return True

    except Exception as e:
        print(f'❌ 搜索失败: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_collect_small():
    """测试小规模论文采集（只下载1篇）"""
    print('\n' + '=' * 50)
    print('📥 测试小规模论文采集')
    print('=' * 50)

    query = 'educational technology'
    print(f'\n采集关键词: {query}')
    print('提示：这将下载 1 篇论文并入库，用于快速测试功能')

    try:
        result = collect_papers(
            query=query,
            sources=['arxiv'],
            max_papers=1,  # 只下载1篇，快速测试
            auto_ingest=True,
        )

        print(f'\n{"✅" if result["success"] else "❌"} {result["message"]}')
        print(f'📊 统计信息:')
        print(f'   搜索到: {result.get("collected", 0)} 篇')
        print(f'   成功入库: {result.get("ingested", 0)} 篇')
        print(f'   失败: {result.get("failed", 0)} 篇')

        if result.get('stats'):
            print(f'   文档片段: {result["stats"].get("total_chunks", 0)} 个')

        if result.get('ingested', 0) > 0:
            print(f'\n🎉 采集测试成功！论文已成功入库！')
        else:
            print(f'\n⚠️ 未能成功入库论文')

        return result.get('ingested', 0) > 0

    except Exception as e:
        print(f'❌ 采集失败: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数 - 自动化运行"""
    print('🎯 论文采集模块自动化测试')
    print('这个测试将验证搜索、下载和入库功能\n')

    # 运行搜索测试
    search_success = test_search()

    if search_success:
        print('\n' + '=' * 50)
        print('✅ 搜索功能正常，准备测试采集功能...')

        # 自动运行采集测试
        print('🚀 开始自动化采集测试...\n')

        collect_success = test_collect_small()

        if collect_success:
            print('\n' + '=' * 50)
            print('🎉🎉🎉 所有测试通过！论文采集模块工作正常！')
            print('=' * 50)
            print('\n✨ 验证结果：')
            print('   ✅ 论文搜索功能正常')
            print('   ✅ PDF 下载功能正常')
            print('   ✅ 文本提取功能正常')
            print('   ✅ 向量化入库功能正常')
            print('\n🎊 你现在可以：')
            print('   1. 访问 http://localhost:8000/docs 查看 API 文档')
            print('   2. 启动前端访问 http://localhost:5173/collector 使用网页界面')
            print('   3. 使用 API 或 Python 代码批量采集论文')
            print('\n📚 示例命令：')
            print('   # API 测试')
            print('   curl -X POST http://localhost:8000/api/papers/collect \\')
            print('     -H "Content-Type: application/json" \\')
            print('     -d \'{"query": "education technology", "max_papers": 5}\'')
        else:
            print('\n⚠️ 采集测试有问题，请检查错误信息')
    else:
        print('\n❌ 搜索测试失败，请先解决搜索功能的问题')


if __name__ == '__main__':
    main()