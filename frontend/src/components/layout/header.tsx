"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LogOut, Menu } from "lucide-react";
import { MobileNav } from "./mobile-nav";
import { useState } from "react";

const roleLabels: Record<string, string> = {
  admin: "Admin",
  doctor: "Liječnik",
  nurse: "Med. sestra",
  receptionist: "Recepcija",
};

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  const initials = user
    ? `${user.ime.charAt(0)}${user.prezime.charAt(0)}`.toUpperCase()
    : "?";

  const handleLogout = async () => {
    await logout();
    router.replace("/prijava");
  };

  return (
    <>
      <header className="flex h-14 items-center gap-4 border-b bg-background px-4 lg:px-6">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={() => setMobileOpen(true)}
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Izbornik</span>
        </Button>

        <div className="flex-1" />

        <div className="flex items-center gap-3">
          {user && (
            <>
              <Badge variant="outline" className="hidden sm:inline-flex">
                {roleLabels[user.role] ?? user.role}
              </Badge>
              <div className="flex items-center gap-2">
                <Avatar size="sm">
                  <AvatarFallback>{initials}</AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium hidden sm:block">
                  {user.ime} {user.prezime}
                </span>
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout} title="Odjava">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </header>

      <MobileNav open={mobileOpen} onOpenChange={setMobileOpen} />
    </>
  );
}
