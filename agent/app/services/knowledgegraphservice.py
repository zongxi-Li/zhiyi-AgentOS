"""
知识图谱增强RAG服务
实现知识图谱构建、图谱与文档联合检索、知识推理
"""
import logging
import json
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """知识图谱类"""
    
    def __init__(self):
        self.entities: Dict[str, Dict] = {}  # 实体字典 {entity_id: entity_data}
        self.relations: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)  # 关系字典 {entity_id: [(target_entity, relation, weight), ...]}
        self.triples: List[Tuple[str, str, str]] = []  # 三元组列表 [(subject, relation, object)]
        
    def add_entity(self, entity_id: str, entity_type: str, properties: Dict = None):
        """添加实体"""
        self.entities[entity_id] = {
            "id": entity_id,
            "type": entity_type,
            "properties": properties or {},
            "relations": []
        }
    
    def add_relation(self, subject: str, relation: str, obj: str, weight: float = 1.0):
        """添加关系"""
        # 确保实体存在
        if subject not in self.entities:
            self.add_entity(subject, "unknown")
        if obj not in self.entities:
            self.add_entity(obj, "unknown")
        
        # 添加关系
        self.relations[subject].append((obj, relation, weight))
        self.relations[obj].append((subject, f"{relation}_reverse", weight))  # 反向关系
        
        # 添加到三元组
        self.triples.append((subject, relation, obj))
        
        # 更新实体的关系列表
        self.entities[subject]["relations"].append({
            "target": obj,
            "relation": relation,
            "weight": weight
        })
    
    def query_entity(self, entity_id: str, relation: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        查询实体相关关系
        
        Args:
            entity_id: 实体ID
            relation: 关系类型（可选）
            limit: 返回结果数量限制
        
        Returns:
            相关实体列表
        """
        if entity_id not in self.relations:
            return []
        
        results = []
        for target, rel, weight in self.relations[entity_id]:
            if relation is None or rel == relation:
                target_entity = self.entities.get(target, {})
                results.append({
                    "entity": target,
                    "relation": rel,
                    "weight": weight,
                    "properties": target_entity.get("properties", {})
                })
        
        # 按权重排序
        results.sort(key=lambda x: x["weight"], reverse=True)
        return results[:limit]
    
    def find_paths(self, start_entity: str, end_entity: str, max_depth: int = 3) -> List[List[Tuple[str, str]]]:
        """查找两个实体之间的路径"""
        if start_entity not in self.entities or end_entity not in self.entities:
            return []
        
        paths = []
        visited = set()
        
        def dfs(current: str, path: List[Tuple[str, str]], depth: int):
            if depth > max_depth:
                return
            
            if current == end_entity:
                paths.append(path.copy())
                return
            
            visited.add(current)
            
            for target, relation, weight in self.relations.get(current, []):
                if target not in visited:
                    path.append((relation, target))
                    dfs(target, path, depth + 1)
                    path.pop()
            
            visited.remove(current)
        
        dfs(start_entity, [], 0)
        return paths


class KnowledgeGraphService:
    """知识图谱服务"""
    
    def __init__(self):
        self.kg = KnowledgeGraph()
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        
    def build_from_documents(self, documents: List[Dict]):
        """
        从文档构建知识图谱
        
        Args:
            documents: 文档列表，每个文档包含text、metadata等
        """
        logger.info(f"开始从 {len(documents)} 个文档构建知识图谱")
        
        for doc in documents:
            text = doc.get("text", "")
            doc_id = doc.get("doc_id", "")
            
            # 1. 实体识别
            entities = self.entity_extractor.extract(text, doc_id)
            
            # 2. 关系抽取
            relations = self.relation_extractor.extract(text, entities, doc_id)
            
            # 3. 添加到知识图谱
            for entity in entities:
                self.kg.add_entity(
                    entity["id"],
                    entity["type"],
                    entity.get("properties", {})
                )
            
            for relation in relations:
                self.kg.add_relation(
                    relation["subject"],
                    relation["relation"],
                    relation["object"],
                    relation.get("weight", 1.0)
                )
        
        logger.info(f"知识图谱构建完成: {len(self.kg.entities)} 个实体, {len(self.kg.triples)} 个三元组")
    
    def hybrid_retrieval(self, question: str, vector_db_results: List[Dict], top_k: int = 5) -> Dict:
        """
        混合检索：知识图谱 + 向量数据库
        
        Args:
            question: 查询问题
            vector_db_results: 向量数据库检索结果
            top_k: 返回结果数量
        
        Returns:
            融合后的检索结果
        """
        # 1. 从问题中提取实体
        question_entities = self.entity_extractor.extract(question, "query")
        
        # 2. 在知识图谱中查找相关实体和关系
        kg_results = []
        for entity in question_entities:
            entity_id = entity["id"]
            related = self.kg.query_entity(entity_id, limit=top_k)
            kg_results.extend(related)
        
        # 3. 融合结果
        fused_results = self._fuse_results(kg_results, vector_db_results, top_k)
        
        return {
            "kg_results": kg_results[:top_k],
            "vector_results": vector_db_results[:top_k],
            "fused_results": fused_results,
            "entities": question_entities
        }
    
    def reason_with_kg(self, question: str) -> Dict:
        """
        基于知识图谱进行推理
        
        Args:
            question: 查询问题
        
        Returns:
            推理结果
        """
        # 提取问题中的实体和关系
        entities = self.entity_extractor.extract(question, "query")
        relations = self.relation_extractor.extract_relations_from_question(question)
        
        reasoning_paths = []
        conclusions = []
        
        # 查找推理路径
        if len(entities) >= 2:
            for i in range(len(entities) - 1):
                start = entities[i]["id"]
                end = entities[i + 1]["id"]
                paths = self.kg.find_paths(start, end, max_depth=3)
                reasoning_paths.extend(paths)
        
        # 生成推理结论
        if reasoning_paths:
            conclusions = self._generate_conclusions(reasoning_paths, entities)
        
        return {
            "reasoning_paths": reasoning_paths[:5],  # 最多5条路径
            "conclusions": conclusions,
            "entities": entities,
            "relations": relations
        }
    
    def _fuse_results(self, kg_results: List[Dict], vector_results: List[Dict], top_k: int) -> List[Dict]:
        """融合知识图谱和向量检索结果"""
        fused = []
        
        # 为知识图谱结果添加权重
        for kg_result in kg_results:
            fused.append({
                "source": "knowledge_graph",
                "content": f"{kg_result['entity']} - {kg_result['relation']}",
                "score": kg_result.get("weight", 0.5),
                "metadata": kg_result.get("properties", {})
            })
        
        # 为向量结果添加权重
        for vec_result in vector_results:
            fused.append({
                "source": "vector_db",
                "content": vec_result.get("content", ""),
                "score": vec_result.get("score", 0.5),
                "metadata": vec_result.get("metadata", {})
            })
        
        # 按分数排序
        fused.sort(key=lambda x: x["score"], reverse=True)
        return fused[:top_k]
    
    def _generate_conclusions(self, paths: List[List[Tuple[str, str]]], entities: List[Dict]) -> List[str]:
        """生成推理结论"""
        conclusions = []
        
        for path in paths[:3]:  # 最多3条路径
            path_str = " -> ".join([f"{rel}({target})" for rel, target in path])
            conclusion = f"通过路径: {path_str}"
            conclusions.append(conclusion)
        
        return conclusions


class EntityExtractor:
    """实体抽取器（增强实现）"""
    
    def __init__(self):
        # 实体类型关键词
        self.entity_keywords = {
            "person": ["先生", "女士", "老师", "医生", "律师", "教授", "经理", "主任", "总监"],
            "organization": ["公司", "机构", "组织", "部门", "学校", "医院", "法院", "政府"],
            "location": ["省", "市", "县", "区", "街道", "路", "广场", "大厦"],
            "time": ["年", "月", "日", "时", "分", "秒", "世纪", "年代"],
            "event": ["会议", "活动", "项目", "计划", "方案", "协议", "合同"]
        }
    
    def extract(self, text: str, source_id: str) -> List[Dict]:
        """从文本中提取实体"""
        entities = []
        seen_entities = set()  # 去重
        
        # 提取人名
        person_pattern = r'([\u4e00-\u9fa5]{2,4})(?:' + '|'.join(self.entity_keywords["person"]) + ')'
        persons = re.findall(person_pattern, text)
        for person in persons:
            entity_id = f"person_{person}"
            if entity_id not in seen_entities:
                seen_entities.add(entity_id)
                entities.append({
                    "id": entity_id,
                    "text": person,
                    "type": "person",
                    "source": source_id,
                    "confidence": 0.8
                })
        
        # 提取机构名
        org_pattern = r'([\u4e00-\u9fa5]{2,15})(?:' + '|'.join(self.entity_keywords["organization"]) + ')'
        orgs = re.findall(org_pattern, text)
        for org in orgs:
            entity_id = f"org_{org}"
            if entity_id not in seen_entities:
                seen_entities.add(entity_id)
                entities.append({
                    "id": entity_id,
                    "text": org,
                    "type": "organization",
                    "source": source_id,
                    "confidence": 0.7
                })
        
        # 提取地点
        location_pattern = r'([\u4e00-\u9fa5]{1,10})(?:' + '|'.join(self.entity_keywords["location"]) + ')'
        locations = re.findall(location_pattern, text)
        for loc in locations:
            entity_id = f"loc_{loc}"
            if entity_id not in seen_entities:
                seen_entities.add(entity_id)
                entities.append({
                    "id": entity_id,
                    "text": loc,
                    "type": "location",
                    "source": source_id,
                    "confidence": 0.6
                })
        
        # 提取事件
        event_pattern = r'([\u4e00-\u9fa5]{2,10})(?:' + '|'.join(self.entity_keywords["event"]) + ')'
        events = re.findall(event_pattern, text)
        for event in events:
            entity_id = f"event_{event}"
            if entity_id not in seen_entities:
                seen_entities.add(entity_id)
                entities.append({
                    "id": entity_id,
                    "text": event,
                    "type": "event",
                    "source": source_id,
                    "confidence": 0.6
                })
        
        return entities


class RelationExtractor:
    """关系抽取器（增强实现）"""
    
    def __init__(self):
        # 关系关键词映射
        self.relation_keywords = {
            "属于": ["属于", "隶属于", "归", "是...的", "在...下"],
            "相关": ["相关", "涉及", "关于", "与...有关", "和...相关"],
            "包含": ["包含", "包括", "含有", "涵盖", "由...组成"],
            "位于": ["位于", "在", "坐落于", "处于"],
            "参与": ["参与", "参加", "加入", "从事"],
            "负责": ["负责", "管理", "主管", "领导"],
            "合作": ["合作", "协作", "联合", "共同"],
            "影响": ["影响", "导致", "引起", "造成"]
        }
    
    def extract(self, text: str, entities: List[Dict], source_id: str) -> List[Dict]:
        """从文本中提取关系"""
        relations = []
        seen_relations = set()  # 去重
        
        # 实体文本到ID的映射
        entity_text_map = {e["text"]: e for e in entities}
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                entity1_text = entity1["text"]
                entity2_text = entity2["text"]
                
                # 查找关系
                for relation, keywords in self.relation_keywords.items():
                    for keyword in keywords:
                        # 双向匹配
                        pattern1 = f"{entity1_text}.*?{keyword}.*?{entity2_text}"
                        pattern2 = f"{entity2_text}.*?{keyword}.*?{entity1_text}"
                        
                        if re.search(pattern1, text, re.DOTALL):
                            rel_key = f"{entity1['id']}_{relation}_{entity2['id']}"
                            if rel_key not in seen_relations:
                                seen_relations.add(rel_key)
                                relations.append({
                                    "subject": entity1["id"],
                                    "relation": relation,
                                    "object": entity2["id"],
                                    "weight": 0.8,
                                    "source": source_id,
                                    "confidence": 0.7
                                })
                            break
                        elif re.search(pattern2, text, re.DOTALL):
                            # 反向关系
                            rel_key = f"{entity2['id']}_{relation}_{entity1['id']}"
                            if rel_key not in seen_relations:
                                seen_relations.add(rel_key)
                                relations.append({
                                    "subject": entity2["id"],
                                    "relation": relation,
                                    "object": entity1["id"],
                                    "weight": 0.8,
                                    "source": source_id,
                                    "confidence": 0.7
                                })
                            break
        
        return relations
    
    def extract_relations_from_question(self, question: str) -> List[str]:
        """从问题中提取关系"""
        relations = []
        
        relation_keywords = ["关系", "属于", "包含", "相关", "影响"]
        for keyword in relation_keywords:
            if keyword in question:
                relations.append(keyword)
        
        return relations


# 全局知识图谱服务实例
knowledge_graph_service = KnowledgeGraphService()

