import { type Config } from "tailwindcss";

export default {
  // 指定Tailwind扫描的文件路径
  content: [
    "./app/**/*.{ts,tsx}",       // 扫描app目录下所有TS/TSX文件
    "./src/**/*.{ts,tsx}",       // 扫描src目录下所有TS/TSX文件（可选）
  ],
  // 启用暗黑模式（根据类名切换）
  darkMode: ["class"],
  // 主题扩展配置
  theme: {
    container: {
      center: true,             // 容器居中
      padding: "2rem",          // 默认内边距
      screens: {
        "2xl": "1400px",        // 大屏断点
      },
    },
    extend: {
      // 自定义颜色
      colors: {
        primary: "#666666",     // 主色调（深灰色）
        secondary: "#4f46e5",   // 辅助色（紫色）
      },
      // 自定义圆角
      borderRadius: {
        lg: "0.5rem",           // 大圆角
        md: "calc(0.5rem - 2px)", // 中等圆角
        sm: "calc(0.5rem - 4px)", // 小圆角
      },
      // 自定义动画（Shadcn/ui组件依赖）
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  // 插件配置（必须包含tailwindcss-animate）
  plugins: [
    require("tailwindcss-animate"), // Shadcn/ui动画支持
    // 其他插件（如需要）...
  ],
} satisfies Config;
