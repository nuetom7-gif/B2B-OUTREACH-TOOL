import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
        outline: "text-foreground",
        success:
          "border-success/20 bg-success/12 text-success hover:bg-success/18 dark:border-success/30 dark:bg-success/18",
        warning:
          "border-warning/30 bg-warning/15 text-warning-foreground hover:bg-warning/20 dark:text-warning",
        info: "border-info/20 bg-info/12 text-info hover:bg-info/18 dark:border-info/30 dark:bg-info/18",
        pending:
          "border-warning/30 bg-warning/10 text-warning-foreground/90 hover:bg-warning/15 dark:text-warning",
        high:
          "border-destructive/20 bg-destructive/10 text-destructive hover:bg-destructive/15",
        low:
          "border-transparent bg-muted text-muted-foreground hover:bg-muted/80",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
