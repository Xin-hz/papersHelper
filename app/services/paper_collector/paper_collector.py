"""论文采集服务：支持从多个学术网站搜索、下载论文并自动入库RAG"""
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

import arxiv
from tqdm import tqdm

from app.config import get_settings
from app.services.document_loader import load_and_chunk_file
from app.services.vector_store import add_documents_to_store
from app.services.paper_collector.cnki_collector import CNKICollector, CNKIPaper
from app.services.paper_collector.core_collector import CORECollector, COREPaper
from app.services.paper_collector.eric_collector import ERICCollector, ERICPaper
from app.services.paper_collector.doaj_collector import DOAJCollector, DOAJPaper
from app.services.paper_collector.openalex_collector import OpenAlexCollector, OpenAlexPaper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperMetadata:
    """论文元数据"""
    def __init__(
        self,
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        abstract: str = "",
        doi: str = "",
        download_url: str = "",
        source: str = "",
        pdf_available: bool = False,
    ):
        self.title = title
        self.authors = authors
        self.year = year
        self.abstract = abstract
        self.doi = doi
        self.download_url = download_url
        self.source = source
        self.pdf_available = pdf_available
        self.collected_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "doi": self.doi,
            "download_url": self.download_url,
            "source": self.source,
            "pdf_available": self.pdf_available,
            "collected_at": self.collected_at.isoformat(),
        }


class ArxivCollector:
    """arXiv 论文采集器"""

    def __init__(self):
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3
        )

    def search(self, query: str, max_results: int = 20) -> List[PaperMetadata]:
        """搜索 arXiv 论文"""
        logger.info(f"正在搜索 arXiv: {query}")

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        papers = []
        try:
            for result in self.client.results(search):
                # 提取作者信息
                authors = [author.name for author in result.authors]

                # 构建下载链接
                pdf_url = result.pdf_url

                metadata = PaperMetadata(
                    title=result.title,
                    authors=authors,
                    year=result.published.year if result.published else None,
                    abstract=result.summary.replace("\n", " "),
                    doi=result.entry_id.split("/")[-1],
                    download_url=pdf_url,
                    source="arxiv",
                    pdf_available=True,
                )
                papers.append(metadata)

            logger.info(f"arXiv 搜索完成，找到 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            logger.error(f"arXiv 搜索失败: {e}")
            return []


class PaperDownloader:
    """论文下载器"""

    def __init__(self, download_dir: Optional[Path] = None):
        settings = get_settings()
        self.download_dir = download_dir or Path(settings.upload_dir) / "collected_papers"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_pdf(self, metadata: PaperMetadata) -> Optional[Path]:
        """下载论文PDF - 完全模拟浏览器行为"""
        if not metadata.pdf_available or not metadata.download_url:
            logger.warning(f"论文无PDF可用: {metadata.title}")
            return None

        try:
            import requests
            import time

            # 生成安全的文件名
            safe_title = "".join(c for c in metadata.title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:100]  # 限制长度

            # 清理DOI，只保留安全的字符
            safe_doi = str(metadata.doi or uuid.uuid4().hex[:8])
            safe_doi = "".join(c for c in safe_doi if c.isalnum() or c in ('.', '-', '_')).strip()
            safe_doi = safe_doi[:50]  # 限制DOI长度

            filename = f"{metadata.source}_{safe_doi}_{safe_title}.pdf"
            file_path = self.download_dir / filename

            logger.info(f"正在下载: {metadata.title}")
            logger.info(f"下载链接: {metadata.download_url[:100]}...")

            # 完全模拟真实浏览器的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
            }

            # 添加更多可能的Referer
            if 'tandfonline' in metadata.download_url:
                headers['Referer'] = 'https://scholar.google.com/'
            elif 'springer' in metadata.download_url:
                headers['Referer'] = 'https://link.springer.com/'
            elif 'doi.org' in metadata.download_url:
                headers['Referer'] = 'https://doi.org/'

            # 禁用gzip检查，直接处理
            response = requests.get(
                metadata.download_url,
                timeout=30,
                stream=True,
                headers=headers,
                allow_redirects=True
            )

            logger.info(f"HTTP状态: {response.status_code}")
            logger.info(f"最终URL: {response.url[:80]}...")

            if response.status_code != 200:
                logger.error(f"HTTP错误: {response.status_code}")
                return None

            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            logger.info(f"内容类型: {content_type}")

            # 如果收到HTML，尝试从页面中提取真实PDF链接
            if 'text/html' in content_type:
                logger.warning("收到HTML页面，尝试提取PDF链接...")
                html_content = response.text

                # 尝试多种方式找到PDF链接
                import re
                from html.parser import HTMLParser
                from urllib.parse import urljoin

                # 方法1: 直接查找PDF链接
                pdf_patterns = [
                    r'<a[^>]+href="([^"]*\.pdf[^"]*)"',  # PDF链接
                    r'<iframe[^>]+src="([^"]*\.pdf[^"]*)"',  # PDF iframe
                    r'window\.location\.href="([^"]*pdf[^"]*)"',  # JavaScript重定向
                ]

                for pattern in pdf_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        new_url = matches[0]
                        # 处理相对路径
                        if not new_url.startswith('http'):
                            new_url = urljoin(response.url, new_url)

                        logger.info(f"找到PDF链接: {new_url[:80]}...")

                        # 重新请求PDF
                        response = requests.get(new_url, timeout=30, stream=True, headers=headers, allow_redirects=True)
                        content_type = response.headers.get('content-type', '').lower()

                        if 'pdf' in content_type:
                            logger.info("成功获取PDF内容")
                            break
                        else:
                            logger.warning(f"提取的链接仍不是PDF: {content_type}")
                            continue

            # 检查是否真的是PDF
            if 'pdf' not in content_type:
                logger.error(f"最终内容仍不是PDF: {content_type}")
                return None

            # 写入文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # 过滤掉keep-alive的空chunk
                        f.write(chunk)

            # 验证下载的文件
            if file_path.stat().st_size == 0:
                logger.error("下载的文件为空")
                return None

            # 检查PDF文件头
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    logger.error(f"文件不是有效的PDF，文件头: {header}")
                    return None

            logger.info(f"✅ 下载成功: {file_path.name} ({file_path.stat().st_size} bytes)")
            return file_path

        except Exception as e:
            logger.error(f"下载失败 {metadata.title}: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None


class PaperIngester:
    """论文入库器：将PDF向量化并录入RAG"""

    def __init__(self):
        self.ingested_count = 0
        self.failed_count = 0
        self.total_chunks = 0

    def ingest_paper(self, pdf_path: Path, metadata: PaperMetadata) -> bool:
        """将单篇论文向量化入库"""
        try:
            logger.info(f"正在处理: {metadata.title}")

            # 加载并切片文档
            docs = load_and_chunk_file(str(pdf_path))

            # 添加元数据到文档
            for doc in docs:
                doc.metadata.update({
                    "source": metadata.source,
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "year": metadata.year,
                    "doi": metadata.doi,
                    "collected_at": metadata.collected_at.isoformat(),
                })

            # 入库向量
            add_documents_to_store(docs)

            self.ingested_count += 1
            self.total_chunks += len(docs)
            logger.info(f"入库成功: {metadata.title} ({len(docs)} 个片段)")
            return True

        except Exception as e:
            logger.error(f"入库失败 {metadata.title}: {e}")
            self.failed_count += 1
            return False

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "ingested": self.ingested_count,
            "failed": self.failed_count,
            "total_chunks": self.total_chunks,
        }


class PaperCollector:
    """论文采集协调器：整合搜索、下载、入库流程"""

    def __init__(self):
        settings = get_settings()

        # 获取OpenAlex API密钥（如果有）
        openalex_api_key = getattr(settings, 'openalex_api_key', None)
        openalex_email = getattr(settings, 'openalex_email', None)

        self.arxiv_collector = ArxivCollector()
        self.cnki_collector = CNKICollector()
        self.core_collector = CORECollector()
        self.eric_collector = ERICCollector()
        self.doaj_collector = DOAJCollector()
        self.openalex_collector = OpenAlexCollector(
            email=openalex_email,
            api_key=openalex_api_key
        )
        self.downloader = PaperDownloader()
        self.ingester = PaperIngester()

    def search_papers(
        self,
        query: str,
        sources: List[str] = ["arxiv"],
        max_results: int = 20,
        year_range: Optional[str] = None,
    ) -> Dict[str, List[PaperMetadata]]:
        """搜索论文（支持多源）"""
        logger.info(f"开始搜索论文: {query}, 数据源: {sources}")

        all_papers = {}

        # arXiv 搜索
        if "arxiv" in sources:
            arxiv_papers = self.arxiv_collector.search(query, max_results)
            all_papers["arxiv"] = arxiv_papers

        # CNKI 搜索
        if "cnki" in sources:
            try:
                cnki_papers = self.cnki_collector.search(query, max_results)
                # 将CNKIPaper转换为PaperMetadata格式
                converted_papers = []
                for cnki_paper in cnki_papers:
                    paper_dict = cnki_paper.to_dict()
                    # 创建PaperMetadata对象
                    metadata = PaperMetadata(
                        title=paper_dict.get("title", ""),
                        authors=paper_dict.get("authors", []),
                        year=paper_dict.get("year"),
                        abstract=paper_dict.get("abstract", ""),
                        doi=paper_dict.get("doi", ""),
                        download_url=paper_dict.get("download_url", ""),
                        source=paper_dict.get("source", "cnki"),
                        pdf_available=paper_dict.get("pdf_available", False),
                    )
                    converted_papers.append(metadata)
                all_papers["cnki"] = converted_papers
            except Exception as e:
                logger.error(f"CNKI搜索失败: {e}")
                all_papers["cnki"] = []

        # CORE 搜索
        if "core" in sources:
            try:
                core_papers = self.core_collector.search(query, max_results)
                # 将COREPaper转换为PaperMetadata格式
                converted_papers = []
                for core_paper in core_papers:
                    paper_dict = core_paper.to_dict()
                    metadata = PaperMetadata(
                        title=paper_dict.get("title", ""),
                        authors=paper_dict.get("authors", []),
                        year=paper_dict.get("year"),
                        abstract=paper_dict.get("abstract", ""),
                        doi=paper_dict.get("doi", ""),
                        download_url=paper_dict.get("download_url", ""),
                        source=paper_dict.get("source", "core"),
                        pdf_available=paper_dict.get("pdf_available", False),
                    )
                    converted_papers.append(metadata)
                all_papers["core"] = converted_papers
            except Exception as e:
                logger.error(f"CORE搜索失败: {e}")
                all_papers["core"] = []

        # ERIC 搜索
        if "eric" in sources:
            try:
                eric_papers = self.eric_collector.search(query, max_results)
                # 将ERICPaper转换为PaperMetadata格式
                converted_papers = []
                for eric_paper in eric_papers:
                    paper_dict = eric_paper.to_dict()
                    metadata = PaperMetadata(
                        title=paper_dict.get("title", ""),
                        authors=paper_dict.get("authors", []),
                        year=paper_dict.get("year"),
                        abstract=paper_dict.get("abstract", ""),
                        doi=paper_dict.get("doi", ""),
                        download_url=paper_dict.get("download_url", ""),
                        source=paper_dict.get("source", "eric"),
                        pdf_available=paper_dict.get("pdf_available", False),
                    )
                    converted_papers.append(metadata)
                all_papers["eric"] = converted_papers
            except Exception as e:
                logger.error(f"ERIC搜索失败: {e}")
                all_papers["eric"] = []

        # DOAJ 搜索 (真实API)
        if "doaj" in sources:
            try:
                logger.info("使用DOAJ真实API搜索...")
                doaj_papers = self.doaj_collector.search(query, max_results)
                # 将DOAJPaper转换为PaperMetadata格式
                converted_papers = []
                for doaj_paper in doaj_papers:
                    paper_dict = doaj_paper.to_dict()
                    metadata = PaperMetadata(
                        title=paper_dict.get("title", ""),
                        authors=paper_dict.get("authors", []),
                        year=paper_dict.get("year"),
                        abstract=paper_dict.get("abstract", ""),
                        doi=paper_dict.get("doi", ""),
                        download_url=paper_dict.get("download_url", ""),
                        source=paper_dict.get("source", "doaj"),
                        pdf_available=paper_dict.get("pdf_available", False),
                    )
                    converted_papers.append(metadata)
                all_papers["doaj"] = converted_papers
            except Exception as e:
                logger.error(f"DOAJ搜索失败: {e}")
                all_papers["doaj"] = []

        # OpenAlex 搜索 (真实API)
        if "openalex" in sources:
            try:
                logger.info("使用OpenAlex真实API搜索...")
                openalex_papers = self.openalex_collector.search(query, max_results)
                # 将OpenAlexPaper转换为PaperMetadata格式
                converted_papers = []
                for openalex_paper in openalex_papers:
                    paper_dict = openalex_paper.to_dict()
                    metadata = PaperMetadata(
                        title=paper_dict.get("title", ""),
                        authors=paper_dict.get("authors", []),
                        year=paper_dict.get("year"),
                        abstract=paper_dict.get("abstract", ""),
                        doi=paper_dict.get("doi", ""),
                        download_url=paper_dict.get("download_url", ""),
                        source=paper_dict.get("source", "openalex"),
                        pdf_available=paper_dict.get("pdf_available", False),
                    )
                    converted_papers.append(metadata)
                all_papers["openalex"] = converted_papers
            except Exception as e:
                logger.error(f"OpenAlex搜索失败: {e}")
                all_papers["openalex"] = []

        # TODO: 添加其他数据源（万方等）

        total = sum(len(papers) for papers in all_papers.values())
        logger.info(f"搜索完成，共找到 {total} 篇论文")

        return all_papers

    def collect_and_ingest(
        self,
        query: str,
        sources: List[str] = ["arxiv"],
        max_papers: int = 10,
        year_range: Optional[str] = None,
        auto_ingest: bool = True,
    ) -> Dict[str, Any]:
        """采集并入库论文"""
        logger.info(f"开始采集任务: {query}")

        # 1. 搜索论文
        search_results = self.search_papers(query, sources, max_papers, year_range)

        all_papers = []
        for source, papers in search_results.items():
            all_papers.extend(papers)

        if not all_papers:
            return {
                "success": False,
                "message": "未找到相关论文",
                "collected": 0,
                "ingested": 0,
                "failed": 0,
                "stats": self.ingester.get_stats(),
            }

        # 2. 下载PDF
        logger.info(f"开始下载 {len(all_papers)} 篇论文...")
        downloaded_files = []

        for metadata in tqdm(all_papers, desc="下载论文"):
            pdf_path = self.downloader.download_pdf(metadata)
            if pdf_path:
                downloaded_files.append((pdf_path, metadata))

        logger.info(f"下载完成: {len(downloaded_files)}/{len(all_papers)}")

        # 3. 入库RAG
        ingested_count = 0
        if auto_ingest:
            logger.info("开始向量化入库...")
            for pdf_path, metadata in tqdm(downloaded_files, desc="入库处理"):
                if self.ingester.ingest_paper(pdf_path, metadata):
                    ingested_count += 1

        stats = self.ingester.get_stats()

        return {
            "success": True,
            "message": f"采集完成: 搜索 {len(all_papers)} 篇，下载 {len(downloaded_files)} 篇，入库 {ingested_count} 篇",
            "collected": len(downloaded_files),
            "ingested": ingested_count,
            "failed": len(all_papers) - len(downloaded_files),
            "stats": stats,
        }


# 全局实例
paper_collector = PaperCollector()


def collect_papers(
    query: str,
    sources: List[str] = ["arxiv"],
    max_papers: int = 10,
    year_range: Optional[str] = None,
    auto_ingest: bool = True,
) -> Dict[str, Any]:
    """便捷函数：采集论文"""
    collector = PaperCollector()
    return collector.collect_and_ingest(
        query=query,
        sources=sources,
        max_papers=max_papers,
        year_range=year_range,
        auto_ingest=auto_ingest,
    )


def search_papers(
    query: str,
    sources: List[str] = ["arxiv"],
    max_results: int = 20,
    year_range: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """便捷函数：搜索论文（只搜索不下载数据库）"""
    collector = PaperCollector()
    results = collector.search_papers(
        query=query,
        sources=sources,
        max_results=max_results,
        year_range=year_range,
    )

    # 转换为可序列化的格式
    serialized = {}
    for source, papers in results.items():
        serialized[source] = [paper.to_dict() for paper in papers]

    return serialized