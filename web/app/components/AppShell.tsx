import Link from "next/link";
import type { ReactNode } from "react";
import { NavLinks } from "./NavLinks";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="枢衡通俗首页">
          <span className="brand-mark">枢</span>
          <span><strong>枢衡</strong><small>研究判断平台</small></span>
        </Link>
        <NavLinks />
        <div className="sidebar-note">
          <span>数据快照</span>
          <strong>2026-07-31</strong>
          <small>北京时间·只读静态版</small>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <div><span className="live-dot" />当前证据基线已锁定</div>
          <div className="topbar-meta">26行台账·十条校准·全部时间按UTC+8</div>
        </header>
        <div className="page-frame">{children}</div>
      </div>
    </div>
  );
}
