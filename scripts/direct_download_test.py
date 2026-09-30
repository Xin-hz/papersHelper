#!/usr/bin/env python3
"""
直接解决论文采集问题
既然用户能在浏览器中下载PDF，我们就模拟浏览器行为
"""

import requests
from pathlib import Path
import sys
sys.path.append('/Users/Stars/Projects/PapersHelper')

from app.services.document_loader import load_and_chunk_file
from app.services.vector_store import add_documents_to_store
from app.config import get_settings

def download_pdf_like_browser(url, title):
    """模拟浏览器下载PDF"""
    print(f"🔍 尝试下载: {title}")
    print(f"链接: {url}")

    # 使用完整的浏览器头部
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)

        print(f"状态码: {response.status_code}")
        print(f"最终URL: {response.url}")
        print(f"内容类型: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()

            # 检查是否是PDF
            if 'pdf' in content_type or 'application/octet-stream' in content_type:
                # 保存文件
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title[:50]

                settings = get_settings()
                download_dir = Path(settings.upload_dir) / "collected_papers"
                download_dir.mkdir(parents=True, exist_ok=True)

                file_path = download_dir / f"{safe_title}.pdf"

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                print(f"✅ 下载成功: {file_path.name} ({file_path.stat().st_size} bytes)")
                return str(file_path)
            else:
                print(f"❌ 不是PDF内容: {content_type}")
                # 如果是HTML，可能需要进一步处理
                if 'text/html' in content_type:
                    print("⚠️ 收到HTML页面，可能需要登录或特殊权限")
                return None
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None

def ingest_pdf_to_knowledge_base(pdf_path, title):
    """将PDF入库到知识库"""
    print(f"\n📚 开始入库: {title}")

    try:
        # 加载并切片
        docs = load_and_chunk_file(pdf_path)

        # 添加元数据
        for doc in docs:
            doc.metadata.update({
                "source": "manual_download",
                "title": title,
                "collected_at": "2026-07-05T00:00:00"
            })

        # 入库
        add_documents_to_store(docs)

        print(f"✅ 入库成功: {len(docs)} 个片段")
        return True

    except Exception as e:
        print(f"❌ 入库失败: {e}")
        return False

# 测试用的论文链接（用户需要提供实际链接）
print("🚀 论文下载和入库测试")
print("=" * 50)
print("\n请提供你想测试的PDF链接：")
print("1. 从浏览器中复制PDF的实际下载链接")
print("2. 在这里测试下载和入库功能")