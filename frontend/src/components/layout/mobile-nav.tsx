"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import {
  Home,
  Users,
  CalendarDays,
  FileText,
  Shield,
  Settings,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Početna", icon: Home },
  { href: "/pacijenti", label: "Pacijenti", icon: Users },
  { href: "/termini", label: "Termini", icon: CalendarDays },
  { href: "/postupci", label: "Postupci", icon: FileText },
  { href: "/cezih", label: "CEZIH", icon: Shield },
  { href: "/postavke", label: "Postavke", icon: Settings, adminOnly: true },
];

export function MobileNav({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const pathname = usePathname();
  const { tenant, user } = useAuth();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-72 p-0">
        <SheetHeader className="px-4 py-4">
          <SheetTitle className="text-sm font-semibold truncate">
            {tenant?.naziv ?? "HM Digital"}
          </SheetTitle>
        </SheetHeader>

        <nav className="flex flex-col gap-1 px-2 pb-4">
          {navItems.filter((item) => !item.adminOnly || user?.role === "admin").map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => onOpenChange(false)}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground font-medium"
                    : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
