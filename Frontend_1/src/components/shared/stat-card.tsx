import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function StatCard({
  label,
  value,
  delta,
  icon,
  hint,
  loading,
  index = 0,
}: {
  label: string;
  value: string | number;
  delta?: number;
  icon?: ReactNode;
  hint?: string;
  loading?: boolean;
  index?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.03, 0.24) }}
    >
      <Card className="gap-0 p-4 shadow-[var(--shadow-card)] transition-shadow hover:shadow-[var(--shadow-pop)]">
        <div className="flex items-start justify-between gap-3">
          <p className="min-w-0 truncate text-[13px] font-medium text-muted-foreground">{label}</p>
          {icon ? (
            <span className="grid size-8 shrink-0 place-items-center rounded-md bg-primary/8 text-primary">
              {icon}
            </span>
          ) : null}
        </div>
        {loading ? (
          <Skeleton className="mt-3 h-7 w-20" />
        ) : (
          <p className="mt-2 text-2xl font-semibold text-numeric tracking-tight">{value}</p>
        )}
        <div className="mt-1.5 flex items-center gap-1.5 text-xs">
          {typeof delta === "number" ? (
            <span
              className={cn(
                "flex items-center gap-0.5 font-medium",
                delta >= 0 ? "text-success" : "text-destructive",
              )}
            >
              {delta >= 0 ? (
                <ArrowUpRight className="size-3.5" />
              ) : (
                <ArrowDownRight className="size-3.5" />
              )}
              {Math.abs(delta)}%
            </span>
          ) : null}
          {hint ? <span className="truncate text-muted-foreground">{hint}</span> : null}
        </div>
      </Card>
    </motion.div>
  );
}
