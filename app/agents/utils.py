import uuid
from typing import List, Dict, Any, Optional, Union, Literal
from langchain_core.documents import Document


def new_uuid() -> str:
    return str(uuid.uuid4())


def _generate_uuid(seed: str) -> str:
    """
    Generate a deterministic UUID based on the provided seed.

    Falls back to a random UUID when the seed is empty.
    """
    if not seed:
        return new_uuid()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))

def reduce_docs(
    existing: Optional[list[Document]],
    new: Union[
        list[Document],
        list[dict[str, Any]],
        list[str],
        str,
        Literal["delete"],
    ],
) -> list[Document]:
    """Reduce and process documents based on the input type.

    This function handles various input types and converts them into a sequence of Document objects.
    It can delete existing documents, create new ones from strings or dictionaries, or return the existing documents.
    It also combines existing documents with the new one based on the document ID.

    Args:
        existing (Optional[Sequence[Document]]): The existing docs in the state, if any.
        new (Union[Sequence[Document], Sequence[dict[str, Any]], Sequence[str], str, Literal["delete"]]):
            The new input to process. Can be a sequence of Documents, dictionaries, strings, a single string,
            or the literal "delete".
    """
    if new == "delete":
        return []

    existing_list = list(existing) if existing else []
    if isinstance(new, str):
        return existing_list + [
            Document(page_content=new, metadata={"uuid": _generate_uuid(new)})
        ]

    new_list = []
    if isinstance(new, list):
        existing_ids = set(doc.metadata.get("uuid") for doc in existing_list)
        for item in new:
            if isinstance(item, str):
                item_id = _generate_uuid(item)
                new_list.append(Document(page_content=item, metadata={"uuid": item_id}))
                existing_ids.add(item_id)

            elif isinstance(item, dict):
                metadata = item.get("metadata", {})
                item_id = metadata.get("uuid") or _generate_uuid(
                    item.get("page_content", "")
                )

                if item_id not in existing_ids:
                    new_list.append(
                        Document(**{**item, "metadata": {**metadata, "uuid": item_id}})
                    )
                    existing_ids.add(item_id)

            elif isinstance(item, Document):
                item_id = item.metadata.get("uuid", "")
                if not item_id:
                    item_id = _generate_uuid(item.page_content)
                    new_item = item.copy(deep=True)
                    new_item.metadata["uuid"] = item_id
                else:
                    new_item = item

                if item_id not in existing_ids:
                    new_list.append(new_item)
                    existing_ids.add(item_id)

    return existing_list + new_list



def format_docs(docs: List[Document]) -> str:
    """将文档列表格式化为字符串
    
    Args:
        docs: 文档列表
        
    Returns:
        格式化后的字符串
    """
    if not docs:
        return "无相关文档。"
        
    formatted_docs = []
    for i, doc in enumerate(docs):
        content = doc.page_content
        metadata = doc.metadata
        source = metadata.get("source", "未知来源")
        formatted_docs.append(f"[{i+1}] {content}\n来源: {source}\n")
        
    return "\n".join(formatted_docs)

def interrupt(data: Dict[str, Any]) -> str:
    """中断函数，用于人工干预
    
    Args:
        data: 中断数据
        
    Returns:
        人工干预的结果
    """
    return data.get("question", "")
