"""快速测试论文采集模块"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.paper_collector import search_papers


def test_search():
    """测试论文搜索功能"""
    print('=' * 50)
    print('🔍 测试论文搜索功能')
    print('=' * 50)

    # 测试搜索
    query = 'machine learning education'
    print(f'\n搜索关键词: {query}')

    try:
        results = search_papers(
            query=query,
            sources=['arxiv'],
            max_results=3,
        )

        # 显示结果
        total = sum(len(papers) for papers in results.values())
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
                    # 处理对象格式
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


if __name__ == '__main__':
    test_search()