import { Link, useRouterState } from "@tanstack/react-router";
import {
  BarChart3,
  Building2,
  ClipboardList,
  FileText,
  Inbox,
  LayoutDashboard,
  Mail,
  Radar,
  Settings,
  ShieldCheck,
  Users,
  FileBarChart,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";

const groups = [
  {
    label: "Overview",
    items: [{ title: "Dashboard", url: "/", icon: LayoutDashboard }],
  },
  {
    label: "Pipeline",
    items: [
      { title: "Discovery", url: "/discovery", icon: Radar },
      { title: "Companies", url: "/companies", icon: Building2 },
      { title: "Contacts", url: "/contacts", icon: Users },
      { title: "Research Queue", url: "/research-queue", icon: ClipboardList },
    ],
  },
  {
    label: "Outreach",
    items: [
      { title: "Campaigns", url: "/campaigns", icon: Mail },
      { title: "Drafts", url: "/drafts", icon: FileText },
      { title: "Mailbox", url: "/mailbox", icon: Inbox },
    ],
  },
  {
    label: "Insights",
    items: [
      { title: "Analytics", url: "/analytics", icon: BarChart3 },
      { title: "Reports", url: "/analytics", icon: FileBarChart, soon: true },
    ],
  },
  {
    label: "System",
    items: [
      { title: "Settings", url: "/settings", icon: Settings },
      { title: "Administration", url: "/settings", icon: ShieldCheck, soon: true },
    ],
  },
] as const;

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const isActive = (url: string) => (url === "/" ? pathname === "/" : pathname.startsWith(url));

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border">
        <Link to="/" className="flex items-center gap-2.5 px-1.5 py-1.5">
          <img
            src="/yash-technology-logo.png"
            alt="Yash Technology"
            className="size-8 shrink-0 rounded-md object-contain"
          />
          <span className="grid min-w-0 leading-tight group-data-[collapsible=icon]:hidden">
            <span className="truncate text-sm font-semibold text-sidebar-foreground">
              Yash Technology
            </span>
            <span className="truncate text-[11px] text-sidebar-foreground/60">Outreach Hub</span>
          </span>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        {groups.map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive(item.url) && !("soon" in item)}
                      tooltip={item.title}
                    >
                      <Link to={item.url} className="flex items-center gap-2">
                        <item.icon className="size-4 shrink-0" />
                        <span className="truncate">{item.title}</span>
                        {"soon" in item ? (
                          <Badge
                            variant="outline"
                            className="ml-auto border-sidebar-border text-[10px] text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden"
                          >
                            Soon
                          </Badge>
                        ) : null}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <div className="flex items-center gap-2 px-1.5 py-1 text-[11px] text-sidebar-foreground/60 group-data-[collapsible=icon]:hidden">
          <span className="size-1.5 rounded-full bg-success" />
          Discovery engine online
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
