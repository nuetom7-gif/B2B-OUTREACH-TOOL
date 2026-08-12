import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { Bell, Check, Moon, Search, Sun, ChevronsUpDown, LogOut, User, Building } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { useTheme } from "@/lib/theme";
import { useCompanies, useContacts, useWorkspaceProfile } from "@/lib/api/hooks";

const LABELS: Record<string, string> = {
  discovery: "Discovery",
  companies: "Companies",
  contacts: "Contacts",
  "research-queue": "Research Queue",
  campaigns: "Campaigns",
  drafts: "Drafts",
  mailbox: "Mailbox",
  analytics: "Analytics",
  reports: "Reports",
  settings: "Settings",
};

const NOTIFICATIONS = [
  { id: "n1", title: "Reply received", body: "Priya Iyer · Meridian Pharma Labs", time: "6m" },
  { id: "n2", title: "Campaign needs approval", body: "Warehouse Racking — 3PL Wave 2", time: "1h" },
  { id: "n3", title: "Discovery run finished", body: "63 companies · GFRP Rebar", time: "3h" },
];

export function Topbar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { theme, toggle } = useTheme();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const companies = useCompanies();
  const contacts = useContacts();
  const workspaceProfile = useWorkspaceProfile();
  const companyResults = companies.data ?? [];
  const contactResults = contacts.data ?? [];
  const profile = workspaceProfile.data;
  const userName = profile?.user_name ?? "Company user";
  const userInitials =
    userName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("") || "CU";

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const crumbs = useMemo(() => {
    const parts = pathname.split("/").filter(Boolean);
    return parts.map((part, i) => ({
      label: LABELS[part] ?? part.replace(/_/g, " "),
      href: "/" + parts.slice(0, i + 1).join("/"),
      last: i === parts.length - 1,
    }));
  }, [pathname]);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/85 px-3 backdrop-blur md:px-5">
      <SidebarTrigger className="shrink-0" />
      <Separator orientation="vertical" className="hidden h-5 md:block" />

      <Breadcrumb className="hidden min-w-0 md:block">
        <BreadcrumbList>
          <BreadcrumbItem>
            {crumbs.length === 0 ? (
              <BreadcrumbPage>Dashboard</BreadcrumbPage>
            ) : (
              <BreadcrumbLink asChild>
                <Link to="/">Dashboard</Link>
              </BreadcrumbLink>
            )}
          </BreadcrumbItem>
          {crumbs.map((c) => (
            <span key={c.href} className="flex items-center gap-1.5">
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                {c.last ? (
                  <BreadcrumbPage className="max-w-[220px] truncate capitalize">
                    {c.label}
                  </BreadcrumbPage>
                ) : (
                  <BreadcrumbLink className="capitalize" href={c.href}>
                    {c.label}
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </span>
          ))}
        </BreadcrumbList>
      </Breadcrumb>

      <button
        onClick={() => setOpen(true)}
        className="ml-auto flex h-9 min-w-0 flex-1 items-center gap-2 rounded-md border bg-muted/40 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted md:max-w-sm md:flex-none"
      >
        <Search className="size-4 shrink-0" />
        <span className="truncate">Search companies, contacts…</span>
        <kbd className="ml-auto hidden shrink-0 rounded border bg-background px-1.5 py-0.5 text-[10px] font-medium md:inline">
          ⌘K
        </kbd>
      </button>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="icon" className="relative shrink-0">
            <Bell className="size-4" />
            <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-primary ring-2 ring-background" />
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-80 p-0">
          <div className="flex items-center justify-between border-b px-3 py-2">
            <span className="text-sm font-semibold">Notifications</span>
            <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs">
              <Check className="size-3" /> Mark all read
            </Button>
          </div>
          <div className="divide-y">
            {NOTIFICATIONS.map((n) => (
              <div key={n.id} className="px-3 py-2.5 hover:bg-muted/50">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-medium">{n.title}</p>
                  <span className="shrink-0 text-[11px] text-muted-foreground">{n.time}</span>
                </div>
                <p className="truncate text-xs text-muted-foreground">{n.body}</p>
              </div>
            ))}
          </div>
        </PopoverContent>
      </Popover>

      <Button variant="ghost" size="icon" onClick={toggle} className="shrink-0" aria-label="Toggle theme">
        {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-9 shrink-0 gap-2 px-1.5">
            <Avatar className="size-7">
              <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-sm font-medium lg:inline">{userName}</span>
            <ChevronsUpDown className="hidden size-3.5 text-muted-foreground lg:inline" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="grid">
            <span className="text-sm">{userName}</span>
            <span className="hidden text-xs font-normal text-muted-foreground">
              Sales Lead · Yash Technology
            </span>
          <span className="text-xs font-normal text-muted-foreground">
            {profile?.user_role ?? "Sales"} · {profile?.company_name ?? "Yash Technology"}
          </span>
        </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem disabled className="gap-2">
            <Building className="size-4" /> Workspace: Yash HQ
            <Badge variant="outline" className="ml-auto text-[10px]">
              Soon
            </Badge>
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2">
            <User className="size-4" /> Profile
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2" onSelect={() => navigate({ to: "/settings" })}>
            <Building className="size-4" /> Settings
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem className="gap-2 text-destructive">
            <LogOut className="size-4" /> Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Search companies, contacts, campaigns…" />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading="Companies">
            {companyResults.slice(0, 6).map((c) => (
              <CommandItem
                key={c.id}
                value={c.name}
                onSelect={() => {
                  setOpen(false);
                  navigate({ to: "/companies/$companyId", params: { companyId: String(c.id) } });
                }}
              >
                <Building className="size-4" />
                <span className="truncate">{c.name}</span>
                <span className="ml-auto text-xs text-muted-foreground">{c.industry}</span>
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandGroup heading="Contacts">
            {contactResults.slice(0, 6).map((c) => (
              <CommandItem
                key={c.id}
                value={`${c.name} ${c.company_name}`}
                onSelect={() => {
                  setOpen(false);
                  navigate({ to: "/contacts/$contactId", params: { contactId: String(c.id) } });
                }}
              >
                <User className="size-4" />
                <span className="truncate">{c.name}</span>
                <span className="ml-auto text-xs text-muted-foreground">{c.company_name}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </header>
  );
}
