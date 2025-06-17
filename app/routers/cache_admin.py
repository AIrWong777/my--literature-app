"""
缓存管理API路由

提供缓存状态查询、清理、统计等管理功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from app.utils.cache_manager import cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/cache", tags=["缓存管理"])

@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息
    
    Returns:
        Dict: 包含所有缓存类型的统计信息
    """
    try:
        stats = cache_manager.get_stats()
        logger.info("获取缓存统计信息")
        return {
            "success": True,
            "data": stats,
            "message": "缓存统计信息获取成功"
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

@router.get("/health")
async def get_cache_health() -> Dict[str, Any]:
    """
    获取缓存健康状态
    
    Returns:
        Dict: 缓存健康检查结果
    """
    try:
        health = cache_manager.health_check()
        logger.info(f"缓存健康检查: {health['status']}")
        return {
            "success": True,
            "data": health,
            "message": "缓存健康检查完成"
        }
    except Exception as e:
        logger.error(f"缓存健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"缓存健康检查失败: {str(e)}")

@router.post("/clear")
async def clear_cache(
    cache_type: Optional[str] = Query(
        default="all", 
        description="缓存类型: all, embedding, answer, chunk, 或指定literature_id"
    )
) -> Dict[str, Any]:
    """
    清理缓存
    
    Args:
        cache_type: 要清理的缓存类型
        
    Returns:
        Dict: 清理结果
    """
    try:
        if cache_type == "all":
            success = cache_manager.clear_all()
            message = "所有缓存已清理"
        elif cache_type == "embedding":
            success = cache_manager.embedding_cache.clear()
            message = "Embedding缓存已清理"
        elif cache_type == "answer":
            success = cache_manager.answer_cache.clear()
            message = "答案缓存已清理"
        elif cache_type == "chunk":
            success = cache_manager.chunk_cache.clear()
            message = "文档块缓存已清理"
        elif cache_type.startswith("literature_"):
            # 假设格式为 literature_<id>
            literature_id = cache_type.replace("literature_", "")
            success = cache_manager.clear_by_literature(literature_id)
            message = f"文献 {literature_id} 相关缓存已清理"
        else:
            raise HTTPException(status_code=400, detail="无效的缓存类型")
        
        if success:
            logger.info(f"缓存清理成功: {cache_type}")
            return {
                "success": True,
                "message": message
            }
        else:
            raise HTTPException(status_code=500, detail="缓存清理失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"缓存清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"缓存清理失败: {str(e)}")

@router.get("/info/{cache_type}")
async def get_cache_info(cache_type: str) -> Dict[str, Any]:
    """
    获取指定缓存类型的详细信息
    
    Args:
        cache_type: 缓存类型 (embedding, answer, chunk)
        
    Returns:
        Dict: 缓存详细信息
    """
    try:
        if cache_type == "embedding":
            info = cache_manager.embedding_cache.info()
        elif cache_type == "answer":
            info = cache_manager.answer_cache.info()
        elif cache_type == "chunk":
            info = cache_manager.chunk_cache.info()
        else:
            raise HTTPException(status_code=400, detail="无效的缓存类型")
        
        return {
            "success": True,
            "data": info,
            "message": f"{cache_type} 缓存信息获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存信息失败: {str(e)}")

@router.get("/keys/{cache_type}")
async def get_cache_keys(
    cache_type: str,
    limit: Optional[int] = Query(default=50, description="返回键的数量限制")
) -> Dict[str, Any]:
    """
    获取指定缓存类型的键列表（用于调试）
    
    Args:
        cache_type: 缓存类型 (embedding, answer, chunk)
        limit: 返回键的数量限制
        
    Returns:
        Dict: 缓存键列表
    """
    try:
        if cache_type == "embedding":
            keys = cache_manager.embedding_cache.keys()
        elif cache_type == "answer":
            keys = cache_manager.answer_cache.keys()
        elif cache_type == "chunk":
            keys = cache_manager.chunk_cache.keys()
        else:
            raise HTTPException(status_code=400, detail="无效的缓存类型")
        
        # 限制返回数量
        limited_keys = keys[:limit] if limit and len(keys) > limit else keys
        
        return {
            "success": True,
            "data": {
                "keys": limited_keys,
                "total_count": len(keys),
                "shown_count": len(limited_keys),
                "truncated": len(keys) > limit if limit else False
            },
            "message": f"{cache_type} 缓存键列表获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存键失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存键失败: {str(e)}")

@router.delete("/key/{cache_type}/{key}")
async def delete_cache_key(cache_type: str, key: str) -> Dict[str, Any]:
    """
    删除指定缓存键
    
    Args:
        cache_type: 缓存类型 (embedding, answer, chunk)
        key: 要删除的缓存键
        
    Returns:
        Dict: 删除结果
    """
    try:
        if cache_type == "embedding":
            success = cache_manager.embedding_cache.delete(key)
        elif cache_type == "answer":
            success = cache_manager.answer_cache.delete(key)
        elif cache_type == "chunk":
            success = cache_manager.chunk_cache.delete(key)
        else:
            raise HTTPException(status_code=400, detail="无效的缓存类型")
        
        if success:
            logger.info(f"缓存键删除成功: {cache_type}:{key}")
            return {
                "success": True,
                "message": f"缓存键 {key} 删除成功"
            }
        else:
            return {
                "success": False,
                "message": f"缓存键 {key} 不存在或删除失败"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除缓存键失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除缓存键失败: {str(e)}")

@router.post("/warm")
async def warm_cache() -> Dict[str, Any]:
    """
    预热缓存（生成常用问题的embeddings）
    
    Returns:
        Dict: 预热结果
    """
    try:
        # 常用问题列表
        common_questions = [
            "这篇文献的主要结论是什么？",
            "文献中的实验方法是什么？",
            "这项研究有什么创新点？",
            "研究的局限性是什么？",
            "作者的主要观点是什么？",
            "实验结果如何？",
            "这项研究的意义是什么？",
            "文献中提到了哪些相关工作？"
        ]
        
        warmed_count = 0
        failed_count = 0
        
        # 为常用问题生成并缓存embeddings
        from app.utils.embedding_service import embedding_service
        
        for question in common_questions:
            try:
                # 检查是否已缓存
                cached = cache_manager.get_embedding(question)
                if cached is not None:
                    continue  # 已缓存，跳过
                
                # 生成embedding（会自动缓存）
                embedding = embedding_service.generate_embedding(question)
                if embedding:
                    warmed_count += 1
                    logger.debug(f"预热embedding: {question}")
                else:
                    failed_count += 1
            except Exception as e:
                logger.warning(f"预热问题失败: {question}, 错误: {e}")
                failed_count += 1
        
        logger.info(f"缓存预热完成: 成功 {warmed_count}, 失败 {failed_count}")
        
        return {
            "success": True,
            "data": {
                "warmed_count": warmed_count,
                "failed_count": failed_count,
                "total_questions": len(common_questions)
            },
            "message": f"缓存预热完成，成功预热 {warmed_count} 个问题"
        }
        
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        raise HTTPException(status_code=500, detail=f"缓存预热失败: {str(e)}")

@router.get("/benchmark")
async def cache_benchmark() -> Dict[str, Any]:
    """
    缓存性能基准测试
    
    Returns:
        Dict: 性能测试结果
    """
    try:
        import time
        from app.utils.embedding_service import embedding_service
        
        test_text = "这是一个用于缓存性能测试的示例文本"
        
        # 测试无缓存性能
        start_time = time.time()
        # 清理可能存在的缓存
        cache_manager.embedding_cache.delete(
            cache_manager.embedding_cache._generate_key(test_text)
        )
        
        embedding1 = embedding_service.generate_embedding(test_text)
        no_cache_time = time.time() - start_time
        
        # 测试有缓存性能
        start_time = time.time()
        embedding2 = embedding_service.generate_embedding(test_text)  # 应该命中缓存
        cache_time = time.time() - start_time
        
        # 计算性能提升
        if no_cache_time > 0:
            improvement = ((no_cache_time - cache_time) / no_cache_time) * 100
        else:
            improvement = 0
        
        return {
            "success": True,
            "data": {
                "no_cache_time_ms": round(no_cache_time * 1000, 2),
                "cache_time_ms": round(cache_time * 1000, 2),
                "improvement_percentage": round(improvement, 2),
                "embedding_generated": embedding1 is not None,
                "cache_hit": embedding2 is not None
            },
            "message": "缓存性能基准测试完成"
        }
        
    except Exception as e:
        logger.error(f"缓存基准测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"缓存基准测试失败: {str(e)}") 