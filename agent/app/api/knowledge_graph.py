"""
知识图谱API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List, Optional
from app.services.knowledge_graph_service import knowledge_graph_service

router = APIRouter()


class BuildGraphRequest(BaseModel):
    documents: List[Dict]  # [{doc_id, text, metadata}]


class HybridSearchRequest(BaseModel):
    question: str
    vector_db_results: List[Dict]
    top_k: int = 5


class ReasonRequest(BaseModel):
    question: str


@router.post("/knowledge-graph/build")
async def build_knowledge_graph(request: BuildGraphRequest):
    """
    从文档构建知识图谱
    
    示例：
    {
        "documents": [
            {
                "doc_id": "doc1",
                "text": "张三是一名律师，属于ABC律师事务所...",
                "metadata": {}
            }
        ]
    }
    """
    try:
        knowledge_graph_service.build_from_documents(request.documents)
        
        # 获取图谱统计信息
        kg = knowledge_graph_service.kg
        stats = {
            "entities_count": len(kg.entities),
            "triples_count": len(kg.triples),
            "relations_count": len(kg.relations)
        }
        
        return {
            "success": True,
            "message": "知识图谱构建成功",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识图谱构建失败: {str(e)}")


@router.post("/knowledge-graph/search")
async def hybrid_search(request: HybridSearchRequest):
    """
    混合检索：知识图谱 + 向量数据库
    
    示例：
    {
        "question": "ABC律师事务所的律师有哪些？",
        "vector_db_results": [...],
        "top_k": 5
    }
    """
    try:
        result = knowledge_graph_service.hybrid_retrieval(
            question=request.question,
            vector_db_results=request.vector_db_results,
            top_k=request.top_k
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"混合检索失败: {str(e)}")


@router.post("/knowledge-graph/reason")
async def reason_with_kg(request: ReasonRequest):
    """
    基于知识图谱进行推理
    
    示例：
    {
        "question": "张三和李四的关系是什么？"
    }
    """
    try:
        result = knowledge_graph_service.reason_with_kg(request.question)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识推理失败: {str(e)}")


@router.get("/knowledge-graph/stats")
async def get_graph_stats():
    """获取知识图谱统计信息"""
    try:
        kg = knowledge_graph_service.kg
        stats = {
            "entities_count": len(kg.entities),
            "triples_count": len(kg.triples),
            "relations_count": len(kg.relations),
            "entities": list(kg.entities.keys())[:10]  # 前10个实体
        }
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/knowledge-graph/entity/{entity_id}")
async def get_entity_info(entity_id: str, relation: Optional[str] = None, limit: int = 10):
    """查询实体相关信息"""
    try:
        kg = knowledge_graph_service.kg
        related = kg.query_entity(entity_id, relation, limit)
        
        entity_info = kg.entities.get(entity_id, {})
        
        return {
            "success": True,
            "data": {
                "entity": entity_info,
                "related_entities": related
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询实体失败: {str(e)}")

