import type { Metadata } from "next";
// import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from '@/context/AuthContext'

// 1. 移除Google字体配置，使用CSS系统字体
// const inter = Inter({ subsets: ["latin"] });

// 2. 定义页面元数据
export const metadata: Metadata = {
  title: "AI+协同文献管理平台",
  description: "基于Next.js和FastAPI的协作平台",
};

// 3. 定义全局布局结构
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning={true}>
      <body className="font-system" suppressHydrationWarning={true}>
        <AuthProvider>{/* 添加这层包裹 */}
          {/* 主容器：最小高度为屏幕高度，内边距为8单位 */}
          <main className="min-h-screen p-8">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}


