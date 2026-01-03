"""
ChromaDB数据库修复脚本
解决版本升级导致的表结构不兼容问题

运行方式：
python fix_chromadb.py
"""
import shutil
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_chromadb():
    """修复ChromaDB数据库"""
    print("\n" + "="*60)
    print("ChromaDB数据库修复工具")
    print("="*60)
    
    # 数据库目录
    data_dir = Path(__file__).parent / "app" / "data" / "rag" / "chroma_db"
    
    if not data_dir.exists():
        print(f"\n✓ 数据库目录不存在，无需修复")
        print(f"  位置: {data_dir}")
        return
    
    print(f"\n📁 数据库位置: {data_dir}")
    
    # 备份旧数据库
    backup_dir = data_dir.parent / "chroma_db_backup"
    
    try:
        print(f"\n🔄 步骤1: 备份现有数据库")
        
        # 如果备份已存在，删除
        if backup_dir.exists():
            print(f"  删除旧备份: {backup_dir}")
            shutil.rmtree(backup_dir)
        
        # 创建备份
        print(f"  创建备份: {backup_dir}")
        shutil.copytree(data_dir, backup_dir)
        print(f"  ✓ 备份完成")
        
        print(f"\n🗑️  步骤2: 删除旧数据库")
        print(f"  删除目录: {data_dir}")
        shutil.rmtree(data_dir)
        print(f"  ✓ 删除完成")
        
        print(f"\n✨ 步骤3: 重新创建数据库")
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ 目录已创建")
        
        # 测试ChromaDB初始化
        try:
            import chromadb
            from chromadb.config import Settings
            
            print(f"\n🧪 步骤4: 测试数据库初始化")
            
            # 尝试新版本API
            try:
                client = chromadb.PersistentClient(
                    path=str(data_dir),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                print(f"  使用新版本API")
            except TypeError:
                client = chromadb.PersistentClient(
                    path=str(data_dir)
                )
                print(f"  使用旧版本API")
            
            # 创建测试集合
            collection = client.create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            print(f"  ✓ 数据库初始化成功")
            
            # 清理测试
            client.delete_collection("rag_documents")
            
            print(f"\n" + "="*60)
            print(f"✅ 修复完成！")
            print(f"="*60)
            print(f"\n说明:")
            print(f"  - 旧数据库已备份到: {backup_dir}")
            print(f"  - 新数据库已创建: {data_dir}")
            print(f"  - 现在可以重新启动服务")
            print(f"\n提示:")
            print(f"  - 如需恢复旧数据，请手动将备份复制回原位置")
            print(f"  - 如不再需要备份，可以删除备份目录")
            
        except ImportError:
            print(f"\n⚠️  警告: ChromaDB未安装")
            print(f"  请运行: pip install chromadb==0.4.15")
            return
        except Exception as e:
            print(f"\n❌ 错误: 数据库初始化失败")
            print(f"  错误信息: {e}")
            
            # 恢复备份
            print(f"\n🔄 尝试恢复备份")
            if data_dir.exists():
                shutil.rmtree(data_dir)
            shutil.copytree(backup_dir, data_dir)
            print(f"  ✓ 备份已恢复")
            
            raise
            
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        print(f"\n建议:")
        print(f"  1. 手动删除数据库目录: {data_dir}")
        print(f"  2. 重新启动服务（会自动创建新数据库）")
        print(f"  3. 或从备份恢复: {backup_dir}")
        import traceback
        traceback.print_exc()


def check_chromadb_version():
    """检查ChromaDB版本"""
    print("\n" + "="*60)
    print("ChromaDB版本检查")
    print("="*60)
    
    try:
        import chromadb
        version = getattr(chromadb, '__version__', 'unknown')
        print(f"\n当前版本: {version}")
        
        if version == 'unknown':
            print(f"  ⚠️  无法获取版本信息")
        elif version.startswith('0.4.'):
            print(f"  ✓ 版本兼容")
        else:
            print(f"  ⚠️  推荐版本: 0.4.15")
            print(f"  当前版本可能不兼容，建议升级或降级")
            print(f"\n升级/降级命令:")
            print(f"  pip install chromadb==0.4.15")
    except ImportError:
        print(f"\n❌ ChromaDB未安装")
        print(f"\n安装命令:")
        print(f"  pip install chromadb==0.4.15")


if __name__ == "__main__":
    print("\n欢迎使用ChromaDB修复工具！")
    print("\n此工具将:")
    print("  1. 备份现有数据库")
    print("  2. 删除旧数据库")
    print("  3. 创建新数据库")
    print("  4. 测试数据库初始化")
    
    # 检查版本
    check_chromadb_version()
    
    # 询问确认
    print("\n" + "="*60)
    response = input("\n是否继续修复? (y/n): ").strip().lower()
    
    if response == 'y':
        fix_chromadb()
    else:
        print("\n操作已取消")
        print("\n如果只是想清理数据库，可以手动删除以下目录:")
        data_dir = Path(__file__).parent / "app" / "data" / "rag" / "chroma_db"
        print(f"  {data_dir}")

