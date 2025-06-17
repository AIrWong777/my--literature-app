import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Heading } from "@/components/ui/heading";
import { AiFillBook, AiOutlineUsergroupAdd, AiOutlineRobot} from "react-icons/ai";
export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white">
      {/* 标题部分 */}
      <div className="text-center">
        <Heading as="h1" size="xxxl" className="mb-4">
          AI+协同文献管理平台
        </Heading>
        <p className="text-gray-600 mb-8">
          为研究人员打造的智能文献管理与协作平台
        </p>
      </div>

      {/* 按钮部分 */}
      <div className="flex gap-4 mb-8">
        <Link href="/register">
          <Button className="px-8 py-2">注册账号</Button>
        </Link>
        <Link href="/login">
          <Button variant="outline" className="px-8 py-2">登录账号</Button>
        </Link>
      </div>

      {/* 功能卡片部分 */}
      <div className="flex gap-4">
        <Card className="flex flex-col items-center p-6 gap-4 w-64">
          <AiFillBook size={32} className="text-black-600" />
          <Heading as="h2" size="lg">智能文献管理</Heading>
          <p className="text-gray-500 text-center text-sm">
            轻松组织和管理您的研究文献
          </p>
        </Card>
        <Card className="flex flex-col items-center p-6 gap-4 w-64">
          <AiOutlineUsergroupAdd size={32} className="text-black-600" />
          <Heading as="h2" size="lg">团队协作</Heading>
          <p className="text-gray-500 text-center text-sm">
            与团队成员共享和讨论文献
          </p>
        </Card>
        <Card className="flex flex-col items-center p-6 gap-4 w-64">
          <AiOutlineRobot size={32} className="text-black-600" />
          <Heading as="h2" size="lg">AI辅助分析</Heading>
          <p className="text-gray-500 text-center text-sm">
            智能分析文献，提供研究洞见
          </p>
        </Card>
      </div>
    </div>
  );
}