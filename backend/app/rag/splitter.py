"""文档切分:
- Markdown 按标题层级切分(MarkdownHeaderTextSplitter),标题链作为片段前缀增强语义
- 超长段落用中文感知分隔符二次递归切分
- 纯文本等其他格式直接走中文感知递归切分
"""
from dataclasses import dataclass

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config import settings
from app.rag.loaders import extract_text

# 中文感知分隔符: 优先在段落/句末标点等自然边界切分
SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

MD_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")]


@dataclass
class Chunk:
    """切分后的文本片段"""

    text: str
    headers: str = ""  # 所属标题链,如 "星耀 X9 Pro > 核心参数"


def _recursive_split(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=SEPARATORS,
        keep_separator=True,  # 句末标点保留在片段内
    )
    return splitter.split_text(text)


def split_markdown(text: str) -> list[Chunk]:
    """Markdown 按标题切分,超长章节继续递归切分;标题链写入片段前缀与元数据"""
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=MD_HEADERS, strip_headers=True
    )
    sections = md_splitter.split_text(text)

    chunks: list[Chunk] = []
    for sec in sections:
        titles = [sec.metadata.get(k) for k in ("h1", "h2", "h3", "h4")]
        titles = [t for t in titles if t]
        header_chain = " > ".join(titles)

        if len(sec.page_content) <= settings.chunk_size:
            pieces = [sec.page_content]
        else:
            pieces = _recursive_split(sec.page_content)

        for piece in pieces:
            chunks.append(
                Chunk(
                    text=f"{header_chain}\n{piece}" if header_chain else piece,
                    headers=header_chain,
                )
            )
    return chunks


def load_and_split(file_path: str, file_type: str) -> list[Chunk]:
    """解析文件并切分为片段(统一入口)"""
    text = extract_text(file_path, file_type)
    if not text.strip():
        return []
    if file_type == "md":
        return split_markdown(text)
    return [Chunk(text=piece) for piece in _recursive_split(text)]
