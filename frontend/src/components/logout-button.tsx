"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function LogoutButton() {
  const router = useRouter();
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={async () => {
        await api.logout().catch(() => undefined);
        router.push("/");
        router.refresh();
      }}
    >
      로그아웃
    </Button>
  );
}
