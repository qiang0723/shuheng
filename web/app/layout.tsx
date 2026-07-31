import type { Metadata } from "next";
import "./styles/base.css";
import "./styles/components.css";
import "./styles/pages.css";
import { AppShell } from "./components/AppShell";

export const metadata: Metadata = {
  title: {
    default: "枢衡研究判断平台",
    template: "%s · 枢衡",
  },
  description: "面向研究判断、证据效力与实验追溯的静态只读平台。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
