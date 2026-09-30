"""DOAJ (Directory of Open Access Journals) 采集器 - 真实API"""
import requests
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class DOAJPaper:
    """DOAJ论文数据结构"""
    title: str
    authors: List[str]
    year: Optional[int] = None
    abstract: str = ""
    source: str = ""  # 期刊名称
    doi: str = ""
    download_url: str = ""
    pdf_available: bool = False
    journal_issn: str = ""
    publisher: str = ""

    def to_dict(self):
        """转换为字典"""
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "source": "doaj",
            "doi": self.doi,
            "download_url": self.download_url,
            "pdf_available": self.pdf_available,
            "journal": self.source,
            "issn": self.journal_issn,
            "publisher": self.publisher
        }


class DOAJCollector:
    """DOAJ开放获取期刊采集器"""

    def __init__(self):
        """初始化DOAJ采集器 - DOAJ API是完全免费的"""
        self.base_url = "https://doaj.org/api/search/articles"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search(self, query: str, max_results: int = 20) -> List[DOAJPaper]:
        """搜索DOAJ开放获取论文"""
        logger.info(f"正在搜索DOAJ真实数据: {query}")

        try:
            # DOAJ API参数
            params = {
                'q': query,
                'pageSize': min(max_results, 100)  # DOAJ限制每页最多100条
            }

            # 发送搜索请求
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=20
            )

            if response.status_code != 200:
                logger.error(f"DOAJ API返回错误: {response.status_code}")
                return []

            data = response.json()

            # 解析DOAJ响应
            papers = []
            if 'results' in data and isinstance(data['results'], list):
                for result in data['results'][:max_results]:
                    try:
                        paper = self._parse_doaj_result(result)
                        if paper and paper.title:
                            papers.append(paper)
                    except Exception as e:
                        logger.warning(f"解析DOAJ结果失败: {e}")
                        continue

            logger.info(f"DOAJ真实搜索完成，找到 {len(papers)} 篇论文")
            return papers

        except requests.exceptions.RequestException as e:
            logger.error(f"DOAJ API请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"DOAJ搜索失败: {e}")
            return []

    def _parse_doaj_result(self, result: Dict) -> Optional[DOAJPaper]:
        """解析DOAJ API返回的单个结果"""
        try:
            # 提取标题
            title = result.get('bibjson', {}).get('title', '')

            # 提取作者
            authors = []
            bibjson = result.get('bibjson', {})
            if 'author' in bibjson:
                for author_info in bibjson['author']:
                    if isinstance(author_info, dict):
                        author_name = author_info.get('name', '')
                        if author_name:
                            authors.append(author_name)
                    elif isinstance(author_info, str):
                        authors.append(author_info)

            # 提取年份
            year = None
            if 'created_date' in result:
                created_date = result['created_date'][:10] if result['created_date'] else None
                if created_date:
                    year_match = re.search(r'(\d{4})', created_date)
                    if year_match:
                        year = int(year_match.group(1))

            # 提取摘要
            abstract = bibjson.get('abstract', '')

            # 提取期刊信息
            journal_name = result.get('bibjson', {}).get('journal', {}).get('name', '')

            # 提取ISSN
            issn = result.get('bibjson', {}).get('journal', {}).get('ISSN', '')

            # 提取发布者
            publisher = result.get('bibjson', {}).get('publisher', {}).get('name', '')

            # 提取DOI
            doi = bibjson.get('doi', '') or bibjson.get('identifier', '')

            # 提取下载链接 (通常是期刊主页或文章页)
            download_url = ''
            pdf_available = False

            # DOAJ通常提供文章链接
            if 'link' in result:
                links = result['link']
                if links and len(links) > 0:
                    # 寻找PDF或全文链接
                    for link_info in links:
                        if isinstance(link_info, dict):
                            url = link_info.get('url', '')
                            content_type = link_info.get('type', '')

                            # 优先选择PDF链接
                            if 'pdf' in content_type.lower() or 'application/pdf' in content_type:
                                download_url = url
                                pdf_available = True
                                break

                            # 如果没有PDF，使用HTML链接
                            if not download_url and 'html' in content_type.lower():
                                download_url = url
                                pdf_available = True

            # 如果没有找到合适的链接，使用期刊主页
            if not download_url and 'journal' in result.get('bibjson', {}):
                journal_home = result['bibjson']['journal'].get('homepage')
                if journal_home:
                    download_url = journal_home
                    pdf_available = True  # 假设可以找到PDF

            paper = DOAJPaper(
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                source=journal_name,
                doi=doi,
                download_url=download_url,
                pdf_available=pdf_available,
                journal_issn=issn,
                publisher=publisher
            )

            return paper

        except Exception as e:
            logger.warning(f"解析DOAJ结果项失败: {e}")
            return None


def create_doaj_collector() -> DOAJCollector:
    """创建DOAJ采集器实例"""
    return DOAJCollector()