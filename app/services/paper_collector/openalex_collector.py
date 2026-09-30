"""OpenAlex 开放学术数据库采集器 - 真实API"""
import requests
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class OpenAlexPaper:
    """OpenAlex论文数据结构"""
    title: str
    authors: List[str]
    year: Optional[int] = None
    abstract: str = ""
    source: str = ""  # 期刊或发布者名称
    doi: str = ""
    download_url: str = ""
    pdf_available: bool = False
    openalex_id: str = ""
    concepts: List[str] = None
    citation_count: int = 0

    def __post_init__(self):
        if self.concepts is None:
            self.concepts = []

    def to_dict(self):
        """转换为字典"""
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "source": "openalex",
            "doi": self.doi,
            "download_url": self.download_url,
            "pdf_available": self.pdf_available,
            "journal": self.source,
            "openalex_id": self.openalex_id,
            "concepts": self.concepts,
            "citation_count": self.citation_count
        }


class OpenAlexCollector:
    """OpenAlex开放学术数据库采集器"""

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        初始化OpenAlex采集器

        Args:
            email: 可选的邮箱地址，用于API礼貌性识别
            api_key: 可选的OpenAlex API密钥，获得更好的服务稳定性
        """
        self.base_url = "https://api.openalex.org"
        self.session = requests.Session()

        # OpenAlex建议在请求中包含email用于识别
        # 这不是为了认证，而是为了API礼貌性
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        if email:
            headers['Email'] = email  # 用于API识别

        if api_key:
            # 使用API密钥获得更好的服务
            headers['Authorization'] = f'Bearer {api_key}'

        self.session.headers.update(headers)

    def search(self, query: str, max_results: int = 20) -> List[OpenAlexPaper]:
        """搜索OpenAlex论文 - 真实API"""
        logger.info(f"正在搜索OpenAlex真实数据: {query}")

        try:
            # OpenAlex Works API
            search_url = f"{self.base_url}/works"

            params = {
                'search': query,
                'per-page': min(max_results, 200),  # OpenAlex每页最多200条
                'filter': 'has_fulltext:true'  # 只搜索有全文的论文
            }

            # 发送搜索请求
            response = self.session.get(
                search_url,
                params=params,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"OpenAlex API返回错误: {response.status_code}")
                return []

            data = response.json()

            # 解析OpenAlex响应
            papers = []
            if 'results' in data and isinstance(data['results'], list):
                for result in data['results'][:max_results]:
                    try:
                        paper = self._parse_openalex_result(result)
                        if paper and paper.title:
                            papers.append(paper)
                    except Exception as e:
                        logger.warning(f"解析OpenAlex结果失败: {e}")
                        continue

            logger.info(f"OpenAlex真实搜索完成，找到 {len(papers)} 篇论文")
            return papers

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAlex API请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"OpenAlex搜索失败: {e}")
            return []

    def _parse_openalex_result(self, result: Dict) -> Optional[OpenAlexPaper]:
        """解析OpenAlex API返回的单个结果"""
        try:
            # 提取标题
            title = result.get('title', '')

            # 提取作者
            authors = []
            if 'authorships' in result and result['authorships']:
                for author_info in result['authorships']:
                    if isinstance(author_info, dict):
                        author = author_info.get('author', {})
                        if isinstance(author, dict):
                            author_name = author.get('display_name', '')
                            if author_name:
                                authors.append(author_name)

            # 提取年份
            year = None
            if 'publication_year' in result:
                year = result['publication_year']
            elif 'publication_date' in result:
                pub_date = result['publication_date']
                if pub_date:
                    year_match = re.search(r'(\d{4})', pub_date)
                    if year_match:
                        year = int(year_match.group(1))

            # 提取摘要
            abstract = result.get('abstract', '') or result.get('abstract_inverted', '')

            # 提取来源信息
            source = ''
            if 'primary_location' in result and result['primary_location']:
                source_info = result['primary_location'].get('source', {})
                if isinstance(source_info, dict):
                    source = source_info.get('display_name', '')

            # 如果没有primary_location，尝试其他位置
            if not source and 'locations' in result:
                for location in result['locations']:
                    if isinstance(location, dict):
                        source_info = location.get('source', {})
                        if isinstance(source_info, dict):
                            source = source_info.get('display_name', '')
                            if source:
                                break

            # 提取DOI
            doi = result.get('doi', '') or result.get('id', '')

            # 提取OpenAlex ID
            openalex_id = result.get('id', '')

            # 提取概念标签
            concepts = []
            if 'concepts' in result and result['concepts']:
                for concept_info in result['concepts'][:5]:  # 只取前5个概念
                    if isinstance(concept_info, dict):
                        concept_name = concept_info.get('display_name', '')
                        if concept_name:
                            concepts.append(concept_name)

            # 提取引用数
            citation_count = result.get('citation_count', 0) or 0

            # 提取下载链接
            download_url = ''
            pdf_available = False

            # OpenAlex通常在locations中包含PDF链接
            if 'locations' in result and result['locations']:
                for location in result['locations']:
                    if isinstance(location, dict):
                        # 查找PDF链接
                        pdf_url = location.get('pdf_url')
                        landing_page = location.get('landing_page')

                        if pdf_url:
                            download_url = pdf_url
                            pdf_available = True
                            logger.info(f"找到PDF链接: {pdf_url[:80]}...")
                            break
                        elif landing_page and not download_url:
                            download_url = landing_page
                            # 不设置pdf_available，因为landing page可能不直接包含PDF
                            logger.info(f"找到landing page: {landing_page[:80]}...")

            # 如果没有找到链接，使用开放获取链接
            if not download_url and 'open_access' in result:
                oa_info = result['open_access']
                if isinstance(oa_info, dict):
                    oa_url = oa_info.get('oa_url')
                    if oa_url:
                        download_url = oa_url
                        pdf_available = True
                        logger.info(f"找到开放获取链接: {oa_url[:80]}...")

            # 如果还是没找到，尝试从最佳位置获取
            if not download_url and 'best_location' in result:
                best_loc = result['best_location']
                if isinstance(best_loc, dict):
                    pdf_url = best_loc.get('pdf_url')
                    landing_page = best_loc.get('landing_page')
                    if pdf_url:
                        download_url = pdf_url
                        pdf_available = True
                    elif landing_page:
                        download_url = landing_page

            paper = OpenAlexPaper(
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                source=source,
                doi=doi,
                download_url=download_url,
                pdf_available=pdf_available,
                openalex_id=openalex_id,
                concepts=concepts,
                citation_count=citation_count
            )

            return paper

        except Exception as e:
            logger.warning(f"解析OpenAlex结果项失败: {e}")
            return None


def create_openalex_collector(email: Optional[str] = None, api_key: Optional[str] = None) -> OpenAlexCollector:
    """创建OpenAlex采集器实例

    Args:
        email: 可选的邮箱地址
        api_key: 可选的OpenAlex API密钥
    """
    return OpenAlexCollector(email=email, api_key=api_key)