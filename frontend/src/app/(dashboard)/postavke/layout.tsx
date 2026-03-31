"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const settingsTabs = [
  { href: "/postavke/klinika", label: "Klinika" },
  { href: "/postavke/korisnici", label: "Korisnici" },
  { href: "/postavke/sesije", label: "Sesije" },
  { href: "/postavke/tipovi-zapisa", label: "Tip nalaza" },
];

export default function PostavkeLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading) return null;
  if (!user || user.role !== "admin") return null;

  return (
    <div className="space-y-6">
      <nav className="flex gap-1 border-b">
        {settingsTabs.map((tab) => {
          const isActive = pathname === tab.href || pathname.startsWith(tab.href + "/");
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                isActive
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30",
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
