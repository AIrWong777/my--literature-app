#!/usr/bin/env python3
"""
快速功能验证脚本
"""

import requests

BASE_URL = "http://localhost:8000"

def main():
    print("🚀 第3天功能验证")
    print("="*30)
    
    # 测试登录
    print('🔐 测试登录...')
    login_r = requests.post(f'{BASE_URL}/login', data={'username': 'testuser', 'password': 'testpass123'})
    if login_r.status_code == 200:
        print('✅ 登录成功')
        token = login_r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试获取研究组
        print('📋 测试获取研究组...')
        groups_r = requests.get(f'{BASE_URL}/user/groups', headers=headers)
        if groups_r.status_code == 200:
            groups = groups_r.json()['groups']
            print(f'✅ 找到 {len(groups)} 个研究组')
            
            if groups:
                group_id = groups[0]['id']
                group_name = groups[0]['name']
                print(f'   - {group_name} ({group_id})')
                
                # 测试文献统计
                print('📊 测试文献统计...')
                stats_r = requests.get(f'{BASE_URL}/literature/stats/{group_id}', headers=headers)
                if stats_r.status_code == 200:
                    stats = stats_r.json()['statistics']
                    print(f'✅ 活跃文献: {stats["active_count"]}, 已删除: {stats["deleted_count"]}')
                    print(f'   总大小: {stats["total_size"]} 字节')
                
                # 测试文献列表
                print('📄 测试文献列表...')
                lit_r = requests.get(f'{BASE_URL}/literature/public/{group_id}', headers=headers)
                if lit_r.status_code == 200:
                    literature = lit_r.json()['literature']
                    print(f'✅ 找到 {len(literature)} 篇文献')
                    for lit in literature[:3]:  # 显示前3篇
                        print(f'   - {lit["title"]} ({lit["filename"]})')
                
                # 测试存储统计
                print('💾 测试存储统计...')
                storage_r = requests.get(f'{BASE_URL}/admin/storage/stats', headers=headers)
                if storage_r.status_code == 200:
                    storage_stats = storage_r.json()['storage_statistics']
                    print(f'✅ 总研究组: {storage_stats["total_groups"]}')
                    print(f'   总文件: {storage_stats["total_files"]}')
                    print(f'   总大小: {storage_stats["total_size"]} 字节')
                
                # 测试已删除文献
                print('🗑️  测试已删除文献...')
                deleted_r = requests.get(f'{BASE_URL}/literature/deleted/{group_id}', headers=headers)
                if deleted_r.status_code == 200:
                    deleted_list = deleted_r.json()['deleted_literature']
                    print(f'✅ 已删除文献: {len(deleted_list)} 篇')
        else:
            print(f'❌ 获取研究组失败: {groups_r.status_code}')
    else:
        print(f'❌ 登录失败: {login_r.status_code}')
    
    print("\n🎉 第3天功能验证完成!")

if __name__ == "__main__":
    main()