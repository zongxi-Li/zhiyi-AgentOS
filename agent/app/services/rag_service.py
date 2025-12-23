"""
RAG服务
实现文档检索和知识库管理
"""
import logging
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class RAGService:
    """RAG服务类"""
    
    def __init__(self, data_dir: str = "data/rag", use_vector_db: bool = False):
        """
        初始化RAG服务
        
        Args:
            data_dir: 数据存储目录
            use_vector_db: 是否使用向量数据库（需要安装相应库）
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 文档存储（内存）
        self.documents: Dict[str, Dict] = {}
        
        # 文档索引（简化版：基于关键词）
        self.index: Dict[str, List[str]] = {}
        
        # 向量数据库支持
        self.use_vector_db = use_vector_db
        self.vector_db = None
        if use_vector_db:
            self._init_vector_db()
        
        # 加载已保存的文档
        self._load_documents()
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        try:
            # 尝试使用ChromaDB（轻量级向量数据库）
            import chromadb
            from chromadb.config import Settings
            
            chroma_dir = self.data_dir / "chroma_db"
            chroma_dir.mkdir(exist_ok=True)
            
            self.vector_client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 创建或获取集合
            self.vector_collection = self.vector_client.get_or_create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.use_vector_db = True
            logger.info("向量数据库初始化成功（ChromaDB）")
        except ImportError:
            logger.warning("ChromaDB未安装，使用关键词索引。安装: pip install chromadb")
            self.use_vector_db = False
        except Exception as e:
            logger.warning(f"向量数据库初始化失败: {e}，使用关键词索引")
            self.use_vector_db = False
    
    def _load_documents(self):
        """从文件加载文档"""
        doc_file = self.data_dir / "documents.json"
        if doc_file.exists():
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                logger.info(f"加载了 {len(self.documents)} 个文档")
            except Exception as e:
                logger.error(f"加载文档失败: {e}")
    
    def _save_documents(self):
        """保存文档到文件"""
        doc_file = self.data_dir / "documents.json"
        try:
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文档失败: {e}")
    
    def _extract_text(self, file_data: bytes, filename: str) -> str:
        """
        从文件数据中提取文本
        
        已集成easydoc、mineru等文档处理工具支持
        """
        try:
            # 使用增强文档处理器
            from app.services.document_processor_enhanced import enhanced_document_processor
            
            result = enhanced_document_processor.extract_text(
                file_data=file_data,
                filename=filename,
                use_enhanced=True
            )
            
            if result.get("success"):
                return result.get("text", "")
            else:
                logger.warning(f"文档提取失败: {result.get('error')}")
                return ""
        except ImportError:
            # 回退到基础实现
            logger.warning("增强文档处理器不可用，使用基础实现")
            try:
                if filename.endswith('.txt') or filename.endswith('.md'):
                    return file_data.decode('utf-8')
                elif filename.endswith('.json'):
                    data = json.loads(file_data.decode('utf-8'))
                    return json.dumps(data, ensure_ascii=False)
                else:
                    logger.warning(f"不支持的文件格式: {filename}")
                    return f"[文档内容: {filename}]"
            except Exception as e:
                logger.error(f"提取文本失败: {e}")
                return ""
    
    def _build_index(self, doc_id: str, text: str):
        """构建文档索引"""
        # 关键词索引
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 2][:100]  # 限制关键词数量
        self.index[doc_id] = keywords
        
        # 向量索引（如果启用）
        if self.use_vector_db and self.vector_collection:
            try:
                # 生成文本向量（简化实现：使用TF-IDF或词频）
                # 实际应该使用embedding模型（如sentence-transformers）
                embedding = self._generate_embedding(text)
                
                # 添加到向量数据库
                self.vector_collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[text[:1000]],  # 限制长度
                    metadatas=[{"doc_id": doc_id}]
                )
            except Exception as e:
                logger.warning(f"向量索引构建失败: {e}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        生成文本向量（简化实现）
        
        实际应该使用embedding模型，如：
        - sentence-transformers
        - OpenAI embeddings
        - 其他embedding服务
        """
        # 简化实现：使用词频向量
        # 实际应该使用专业的embedding模型
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            embedding = model.encode(text).tolist()
            return embedding
        except ImportError:
            # 回退到简单的词频向量
            logger.warning("sentence-transformers未安装，使用简化向量。安装: pip install sentence-transformers")
            words = text.lower().split()
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 创建固定维度的向量（128维）
            embedding = [0.0] * 128
            for i, (word, freq) in enumerate(list(word_freq.items())[:128]):
                embedding[i] = freq / len(words) if words else 0.0
            
            return embedding
    
    def _rebuild_index(self):
        """重建所有文档索引"""
        self.index = {}
        for doc_id, doc_data in self.documents.items():
            text = doc_data.get("text", "")
            self._build_index(doc_id, text)
    
    def upload_document(
        self,
        file_data: bytes,
        filename: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        上传文档到知识库
        
        Args:
            file_data: 文件数据
            filename: 文件名
            metadata: 元数据
        
        Returns:
            文档ID
        """
        try:
            # 生成文档ID
            doc_id = hashlib.md5(file_data).hexdigest()
            
            # 提取文本
            text = self._extract_text(file_data, filename)
            
            # 保存文档
            self.documents[doc_id] = {
                "doc_id": doc_id,
                "filename": filename,
                "text": text,
                "metadata": metadata or {},
                "upload_time": datetime.now().isoformat(),
                "size": len(file_data)
            }
            
            # 构建索引
            self._build_index(doc_id, text)
            
            # 保存到文件
            self._save_documents()
            
            logger.info(f"文档上传成功: {filename} (ID: {doc_id})")
            return doc_id
            
        except Exception as e:
            logger.error(f"文档上传失败: {e}", exc_info=True)
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        context_id: Optional[str] = None,
        use_vector_search: bool = True
    ) -> List[Dict]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            context_id: 上下文ID（可选）
            use_vector_search: 是否使用向量搜索（如果可用）
        
        Returns:
            搜索结果列表
        """
        try:
            # 优先使用向量搜索
            if use_vector_search and self.use_vector_db and self.vector_collection:
                return self._vector_search(query, top_k)
            else:
                return self._keyword_search(query, top_k)
        except Exception as e:
            logger.error(f"搜索失败: {e}", exc_info=True)
            # 回退到关键词搜索
            return self._keyword_search(query, top_k)
    
    def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """向量搜索"""
        try:
            # 生成查询向量
            query_embedding = self._generate_embedding(query)
            
            # 在向量数据库中搜索
            results = self.vector_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # 转换结果格式
            search_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    doc_data = self.documents.get(doc_id, {})
                    search_results.append({
                        "doc_id": doc_id,
                        "filename": doc_data.get("filename", ""),
                        "score": 1.0 - results['distances'][0][i] if 'distances' in results else 0.5,  # 距离转分数
                        "content": doc_data.get("text", "")[:500],
                        "metadata": doc_data.get("metadata", {}),
                        "method": "vector_search"
                    })
            
            return search_results
        except Exception as e:
            logger.warning(f"向量搜索失败: {e}，回退到关键词搜索")
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """关键词搜索"""
        query_words = query.lower().split()
        results = []
        
        # 关键词匹配
        for doc_id, doc_data in self.documents.items():
            text = doc_data.get("text", "").lower()
            score = 0
            
            # 计算匹配分数
            for word in query_words:
                if word in text:
                    score += text.count(word)
            
            if score > 0:
                results.append({
                    "doc_id": doc_id,
                    "filename": doc_data.get("filename", ""),
                    "score": score,
                    "content": doc_data.get("text", "")[:500],
                    "metadata": doc_data.get("metadata", {}),
                    "method": "keyword_search"
                })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def build_context(self, query: str, search_results: List[Dict]) -> str:
        """
        构建增强上下文
        
        Args:
            query: 查询文本
            search_results: 搜索结果
        
        Returns:
            增强后的上下文
        """
        if not search_results:
            return ""
        
        context_parts = [f"查询: {query}\n\n相关文档内容:\n"]
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(
                f"[文档{i}] {result.get('filename', '未知')}\n"
                f"{result.get('content', '')}\n"
            )
        
        return "\n".join(context_parts)
    
    def enhanced_search(
        self,
        query: str,
        top_k: int = 5,
        use_knowledge_graph: bool = False
    ) -> Dict:
        """
        增强检索（可选知识图谱）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_knowledge_graph: 是否使用知识图谱增强
        
        Returns:
            检索结果（包含向量检索和知识图谱结果）
        """
        try:
            # 向量检索
            vector_results = self.search(query, top_k)
            
            # 如果启用知识图谱
            if use_knowledge_graph:
                try:
                    from app.services.knowledge_graph_service import knowledge_graph_service
                    
                    # 混合检索
                    hybrid_result = knowledge_graph_service.hybrid_retrieval(
                        question=query,
                        vector_db_results=vector_results,
                        top_k=top_k
                    )
                    
                    return {
                        "vector_results": vector_results,
                        "kg_results": hybrid_result.get("kg_results", []),
                        "fused_results": hybrid_result.get("fused_results", []),
                        "entities": hybrid_result.get("entities", []),
                        "use_kg": True
                    }
                except ImportError:
                    logger.warning("知识图谱服务未加载，使用标准检索")
                    return {
                        "vector_results": vector_results,
                        "use_kg": False
                    }
            else:
                return {
                    "vector_results": vector_results,
                    "use_kg": False
                }
        except Exception as e:
            logger.error(f"增强检索失败: {e}", exc_info=True)
            return {
                "vector_results": [],
                "use_kg": False,
                "error": str(e)
            }