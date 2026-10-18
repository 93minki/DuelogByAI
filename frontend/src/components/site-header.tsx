import Link from "next/link";
import { cookies } from "next/headers";

import { LogoutButton } from "@/components/logout-button";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { AUTH_COOKIE } from "@/lib/auth-cookie";

export async function SiteHeader() {
  const loggedIn = (await cookies()).has(AUTH_COOKIE);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
          <Logo />
          <span>듀얼로그</span>
        </Link>
        <nav className="flex items-center gap-1">
          {loggedIn ? (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/dashboard">대시보드</Link>
              </Button>
              <LogoutButton />
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">로그인</Link>
              </Button>
              <Button asChild size="sm">
                <Link href="/signup">회원가입</Link>
              </Button>
            </>
          )}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}

function Logo() {
  return (
    <span aria-hidden className="relative inline-flex size-6 items-center justify-center">
      <span className="absolute left-0 top-1 size-4 rounded-full bg-pro/80" />
      <span className="absolute right-0 bottom-1 size-4 rounded-full bg-con/80 mix-blend-multiply dark:mix-blend-screen" />
    </span>
  );
}
