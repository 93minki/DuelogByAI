import { Badge } from "@/components/ui/badge";
import { STATUS_LABEL } from "@/lib/format";
import type { DebateStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const TONE: Record<DebateStatus, string> = {
  running: "border-transparent bg-emerald-600 text-white dark:bg-emerald-500 dark:text-background",
  completed: "border-transparent bg-secondary text-secondary-foreground",
  stopped: "border-border bg-transparent text-muted-foreground",
  failed: "border-transparent bg-destructive/10 text-destructive",
};

export function StatusBadge({ status }: { status: DebateStatus }) {
  return (
    <Badge className={cn("gap-1.5", TONE[status])}>
      {status === "running" && <span className="size-1.5 animate-pulse rounded-full bg-current" />}
      {STATUS_LABEL[status]}
    </Badge>
  );
}
