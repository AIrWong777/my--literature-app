#!/usr/bin/env python3
"""
软删除功能测试
"""

import requests

BASE_URL = "http://localhost:8000"

def main():
    """主测试函数"""
    print("🗑️  软删除功能测试")
    print("="*30)
    
    # 登录
    login_r = requests.post(f'{BASE_URL}/login', data={'username': 'testuser', 'password': 'testpass123'})
    token = login_r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 获取文献列表
    groups_r = requests.get(f'{BASE_URL}/user/groups', headers=headers)
    group_id = groups_r.json()['groups'][0]['id']
    lit_r = requests.get(f'{BASE_URL}/literature/public/{group_id}', headers=headers)
    literature = lit_r.json()['literature']
    
    if literature:
        lit_id = literature[0]['id']
        lit_title = literature[0]['title']
        print(f'📄 找到文献: {lit_title} ({lit_id})')
        
        # 软删除
        print("\n🗑️  执行软删除...")
        delete_r = requests.delete(f'{BASE_URL}/literature/{lit_id}?reason=测试软删除功能', headers=headers)
        if delete_r.status_code == 200:
            print(f"✅ 删除成功: {delete_r.json()['message']}")
        else:
            print(f"❌ 删除失败: {delete_r.text}")
            return
        
        # 查看已删除文献
        print("\n📋 查看已删除文献...")
        deleted_r = requests.get(f'{BASE_URL}/literature/deleted/{group_id}', headers=headers)
        deleted_list = deleted_r.json()['deleted_literature']
        print(f"✅ 已删除文献数量: {len(deleted_list)}")
        
        if deleted_list:
            deleted_lit = deleted_list[0]
            print(f"   - 标题: {deleted_lit['title']}")
            print(f"   - 删除时间: {deleted_lit['deleted_at']}")
            print(f"   - 删除原因: {deleted_lit['delete_reason']}")
        
        # 恢复文献
        print("\n🔄 执行恢复...")
        restore_r = requests.post(f'{BASE_URL}/literature/{lit_id}/restore', headers=headers)
        if restore_r.status_code == 200:
            print(f"✅ 恢复成功: {restore_r.json()['message']}")
        else:
            print(f"❌ 恢复失败: {restore_r.text}")
        
        # 验证恢复结果
        print("\n🔍 验证恢复结果...")
        lit_r2 = requests.get(f'{BASE_URL}/literature/public/{group_id}', headers=headers)
        literature2 = lit_r2.json()['literature']
        
        restored_lit = next((lit for lit in literature2 if lit['id'] == lit_id), None)
        if restored_lit:
            print(f"✅ 文献已恢复: {restored_lit['title']}")
        else:
            print("❌ 文献恢复失败")
        
    else:
        print('❌ 没有找到文献进行测试')
    
    print("\n🎉 软删除功能测试完成!")

if __name__ == "__main__":
    main()