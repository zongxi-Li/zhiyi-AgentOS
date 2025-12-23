"""
通信效率优化服务
优化联邦学习和系统间通信效率
"""
import logging
import asyncio
from typing import Dict, List, Optional
import time
from collections import deque

logger = logging.getLogger(__name__)


class CommunicationOptimizer:
    """通信效率优化器"""
    
    def __init__(self):
        self.message_queue = deque(maxlen=1000)  # 消息队列
        self.batch_size = 10  # 批处理大小
        self.compression_enabled = True  # 启用压缩
        self.caching_enabled = True  # 启用缓存
        self.cache = {}  # 通信缓存
        self.stats = {
            "total_messages": 0,
            "batched_messages": 0,
            "compressed_messages": 0,
            "cached_hits": 0,
            "avg_latency": 0.0
        }
    
    async def send_optimized(
        self,
        data: Dict,
        target: str,
        use_batching: bool = True,
        use_compression: bool = True,
        use_cache: bool = True
    ) -> Dict:
        """
        发送优化后的消息
        
        Args:
            data: 消息数据
            target: 目标服务
            use_batching: 是否使用批处理
            use_compression: 是否使用压缩
            use_cache: 是否使用缓存
        
        Returns:
            发送结果
        """
        start_time = time.time()
        
        # 1. 检查缓存
        if use_cache:
            cache_key = self._generate_cache_key(data, target)
            if cache_key in self.cache:
                self.stats["cached_hits"] += 1
                logger.debug(f"使用缓存: {target}")
                return {
                    "success": True,
                    "cached": True,
                    "data": self.cache[cache_key],
                    "latency": 0.001  # 缓存命中延迟极低
                }
        
        # 2. 批处理（如果启用）
        if use_batching:
            self.message_queue.append((data, target))
            
            # 如果队列达到批处理大小，批量发送
            if len(self.message_queue) >= self.batch_size:
                return await self._send_batch()
            else:
                # 如果队列未满，等待一小段时间收集更多消息
                # 注意：在实际应用中，应该使用后台任务或定时器来处理批处理
                # 这里简化处理：如果等待后仍未满，则发送单条消息
                await asyncio.sleep(0.05)  # 等待50ms
                if len(self.message_queue) >= self.batch_size:
                    return await self._send_batch()
                # 如果队列仍未满，从队列中取出当前消息单独发送
                if (data, target) in self.message_queue:
                    self.message_queue.remove((data, target))
        
        # 3. 压缩（如果启用）
        if use_compression:
            compressed_data = self._compress_data(data)
        else:
            compressed_data = data
        
        # 4. 发送消息（模拟）
        result = await self._send_message(compressed_data, target)
        
        # 5. 更新缓存
        if use_cache and result.get("success"):
            cache_key = self._generate_cache_key(data, target)
            self.cache[cache_key] = result
            # 限制缓存大小
            if len(self.cache) > 1000:
                # 删除最旧的缓存
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
        
        # 6. 更新统计
        latency = time.time() - start_time
        self._update_stats(latency, use_batching, use_compression)
        
        return {
            "success": True,
            "data": result,
            "latency": latency,
            "optimizations": {
                "batching": use_batching,
                "compression": use_compression,
                "caching": use_cache
            }
        }
    
    async def _send_batch(self) -> Dict:
        """批量发送消息"""
        if not self.message_queue:
            return {"success": False, "error": "队列为空"}
        
        batch = []
        targets = set()
        
        # 收集一批消息
        while len(batch) < self.batch_size and self.message_queue:
            data, target = self.message_queue.popleft()
            batch.append(data)
            targets.add(target)
        
        # 批量发送
        results = []
        for data, target in zip(batch, list(targets) * len(batch) if len(targets) == 1 else list(targets)):
            result = await self._send_message(data, target)
            results.append(result)
        
        self.stats["batched_messages"] += len(batch)
        
        return {
            "success": True,
            "batch_size": len(batch),
            "results": results,
            "optimization": "batching"
        }
    
    async def _send_message(self, data: Dict, target: str) -> Dict:
        """发送单条消息（模拟）"""
        # 模拟网络延迟
        await asyncio.sleep(0.01)  # 10ms延迟
        
        return {
            "success": True,
            "target": target,
            "timestamp": time.time()
        }
    
    def _compress_data(self, data: Dict) -> Dict:
        """压缩数据（简化实现）"""
        # 实际应该使用gzip、lz4等压缩算法
        # 这里只是标记为已压缩
        self.stats["compressed_messages"] += 1
        return {
            "compressed": True,
            "original_size": len(str(data)),
            "data": data
        }
    
    def _generate_cache_key(self, data: Dict, target: str) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        key_string = f"{target}:{json.dumps(data, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_stats(self, latency: float, batched: bool, compressed: bool):
        """更新统计信息"""
        self.stats["total_messages"] += 1
        
        # 更新平均延迟（移动平均）
        current_avg = self.stats["avg_latency"]
        count = self.stats["total_messages"]
        self.stats["avg_latency"] = (current_avg * (count - 1) + latency) / count
    
    def get_optimization_stats(self) -> Dict:
        """获取优化统计"""
        return {
            "stats": self.stats.copy(),
            "queue_size": len(self.message_queue),
            "cache_size": len(self.cache),
            "optimization_rate": {
                "batching": self.stats["batched_messages"] / max(self.stats["total_messages"], 1),
                "compression": self.stats["compressed_messages"] / max(self.stats["total_messages"], 1),
                "caching": self.stats["cached_hits"] / max(self.stats["total_messages"], 1)
            }
        }
    
    def optimize_federated_communication(
        self,
        client_updates: List[Dict],
        compression: bool = True,
        batching: bool = True
    ) -> Dict:
        """
        优化联邦学习通信
        
        Args:
            client_updates: 客户端更新列表
            compression: 是否压缩
            batching: 是否批处理
        
        Returns:
            优化后的通信数据
        """
        optimized = {
            "updates": client_updates,
            "count": len(client_updates)
        }
        
        if compression:
            # 压缩更新数据
            optimized["compressed"] = True
            optimized["original_size"] = sum(len(str(u)) for u in client_updates)
            # 实际压缩逻辑
            optimized["compressed_size"] = optimized["original_size"] * 0.7  # 假设压缩率30%
        
        if batching:
            # 批处理优化
            optimized["batched"] = True
            optimized["batch_count"] = (len(client_updates) + self.batch_size - 1) // self.batch_size
        
        return optimized


# 全局通信优化器实例
communication_optimizer = CommunicationOptimizer()

