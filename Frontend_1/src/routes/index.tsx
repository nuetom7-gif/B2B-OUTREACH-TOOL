import { Link, createFileRoute } from "@tanstack/react-router";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  Bell,
  Building2,
  CheckCircle2,
  ClipboardList,
  Coins,
  Mail,
  MessageSquareReply,
  Radar,
  Send,
  ShieldAlert,
  Users,
} from "lucide-react";

import { PageHeader, SectionCardTitle, StateCard } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useDashboardStats, useDashboardSummary } from "@/lib/api/hooks";

const CHART = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"];

const tooltipStyle = {
  contentStyle: {
    background: "var(--popover)",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    fontSize: "12px",
    color: "var(--popover-foreground)",
  },
} as const;

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — Yash Technology Outreach Hub" },
      {
        name: "description",
        content:
          "Executive view of lead discovery, qualified pipeline, campaign performance and replies for Yash Technology sales teams.",
      },
      { property: "og:title", content: "Dashboard — Yash Technology Outreach Hub" },
      {
        property: "og:description",
        content: "Discovery, CRM, outreach and pipeline metrics in one executive dashboard.",
      },
    ],
  }),
  component: DashboardPage,
});

function DashboardPage() {
  const summary = useDashboardSummary();
  const stats = useDashboardStats();

  if (summary.isError || stats.isError) {
    const message = summary.error?.message ?? stats.error?.message ?? "The dashboard endpoint could not be reached.";
    return (
      <StateCard
        title="Dashboard unavailable"
        description={message}
        action={
          <Button asChild>
            <Link to="/settings">Check backend settings</Link>
          </Button>
        }
      />
    );
  }

  if (summary.isLoading || stats.isLoading || !summary.data || !stats.data) {
    return (
      <div className="space-y-5">
        <PageHeader title="Dashboard" description="Pipeline health across discovery, qualification and outreach." />
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          {Array.from({ length: 10 }).map((_, index) => (
            <StatCard
              key={index}
              index={index}
              label="Loading"
              value="—"
              loading
              icon={<Bell className="size-4" />}
            />
          ))}
        </div>
      </div>
    );
  }

  const dashboard = summary.data;
  const metrics = stats.data;
  const funnelData = Object.entries(metrics.funnel).map(([label, value]) => ({ label, value }));
  const dailySeries = metrics.daily_leads.map((point) => ({
    date: point.date,
    leads: point.count,
    emails: metrics.daily_emails.find((row) => row.date === point.date)?.count ?? 0,
    replies: metrics.daily_replies.find((row) => row.date === point.date)?.count ?? 0,
  }));
  const topProducts = metrics.per_product_stats.slice(0, 6);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Dashboard"
        description="Pipeline health across discovery, qualification and outreach."
        actions={
          <>
            <Button variant="outline" asChild>
              <Link to="/analytics">Open analytics</Link>
            </Button>
            <Button asChild>
              <Link to="/discovery">
                <Radar className="size-4" /> Run discovery
              </Link>
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatCard index={0} label="Total contacts" value={metrics.total_contacts.toLocaleString()} icon={<Users className="size-4" />} />
        <StatCard index={1} label="Messages sent this month" value={dashboard.messages_sent_this_month.toLocaleString()} icon={<Send className="size-4" />} />
        <StatCard index={2} label="Reply rate" value={`${(dashboard.reply_rate * 100).toFixed(1)}%`} icon={<MessageSquareReply className="size-4" />} />
        <StatCard index={3} label="Active mailboxes" value={dashboard.active_mailboxes} icon={<Mail className="size-4" />} />
        <StatCard index={4} label="Emails sent today" value={metrics.today_emails_sent} icon={<Send className="size-4" />} />
        <StatCard index={5} label="Replies today" value={metrics.today_replies} icon={<MessageSquareReply className="size-4" />} />
        <StatCard index={6} label="Bounce rate" value={`${(metrics.bounce_rate * 100).toFixed(1)}%`} icon={<ShieldAlert className="size-4" />} />
        <StatCard index={7} label="Apollo credits remaining" value={metrics.apollo_credits_remaining.toLocaleString()} icon={<Coins className="size-4" />} />
        <StatCard index={8} label="Pending drafts" value={metrics.pending_drafts} icon={<ClipboardList className="size-4" />} />
        <StatCard index={9} label="Manual reviews" value={metrics.pending_reviews} icon={<CheckCircle2 className="size-4" />} />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex-row items-center justify-between gap-3">
            <SectionCardTitle title="Lead activity trend" hint="Daily leads, emails and replies" />
            <Badge variant="secondary">14d</Badge>
          </CardHeader>
          <CardContent className="h-[260px] px-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailySeries}>
                <defs>
                  <linearGradient id="gLeads" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gEmails" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--chart-2)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="var(--chart-2)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" width={32} />
                <Tooltip {...tooltipStyle} />
                <Area type="monotone" dataKey="emails" stroke="var(--chart-2)" fill="url(#gEmails)" strokeWidth={2} />
                <Area type="monotone" dataKey="leads" stroke="var(--chart-1)" fill="url(#gLeads)" strokeWidth={2} />
                <Line type="monotone" dataKey="replies" stroke="var(--chart-3)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionCardTitle title="Pipeline funnel" hint="Current CRM staging" />
          </CardHeader>
          <CardContent className="h-[260px] px-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelData} layout="vertical" margin={{ left: 12 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                <YAxis type="category" dataKey="label" width={96} tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {funnelData.map((_, index) => (
                    <Cell key={index} fill={CHART[index % CHART.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <SectionCardTitle title="Product targets" hint="Progress against daily targets" />
          </CardHeader>
          <CardContent className="h-[240px] px-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topProducts}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="product_segment" tick={{ fontSize: 10 }} interval={0} angle={-18} textAnchor="end" height={56} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="current" fill="var(--chart-4)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionCardTitle title="Today by product" hint="Leads discovered against target" />
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(metrics.today_leads).map(([segment, target]) => (
              <div key={segment} className="rounded-md border px-3 py-2">
                <div className="flex items-center justify-between gap-3">
                  <p className="truncate text-sm font-medium">{segment}</p>
                  <p className="text-xs text-muted-foreground">
                    {target.current}/{target.target}
                  </p>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${Math.min(100, target.target === 0 ? 0 : (target.current / target.target) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionCardTitle title="Recent activity" hint="Latest backend activity" />
          </CardHeader>
          <CardContent className="space-y-0 p-0">
            {dashboard.recent_messages.map((message, index) => (
              <div key={message.id}>
                {index > 0 ? <Separator /> : null}
                <div className="flex items-start gap-3 px-6 py-3">
                  <span className="mt-1.5 size-2 shrink-0 rounded-full bg-primary" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{message.subject}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {message.contact_name} · {message.company_name}
                    </p>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground">{message.status}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
