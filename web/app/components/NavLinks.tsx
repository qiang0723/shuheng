"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "通俗首页", hint: "结论与边界" },
  { href: "/experiments", label: "实验台账", hint: "26行全量快照" },
];

export function NavLinks() {
  const pathname = usePathname();

  return (
    <nav className="nav-list" aria-label="主导航">
      {links.map((link) => {
        const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
        return (
          <Link key={link.href} href={link.href} className={active ? "nav-link active" : "nav-link"}>
            <span>{link.label}</span><small>{link.hint}</small>
          </Link>
        );
      })}
    </nav>
  );
}
