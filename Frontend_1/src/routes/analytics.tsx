import { createFileRoute } from "@tanstack/react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader, StateCard, SectionCardTitle } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDashboardStats } from "@/lib/api/hooks";

const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"];

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Analytics — Yash Technology Outreach Hub" },
      {
        name: "description",
        content: "Reporting on discovery, outreach, replies and product target progress from FastAPI.",
      },
      { property: "og:title", content: "Analytics — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Reporting on discovery and outreach metrics across divisions." },
    ],
  }),
  component: AnalyticsPage,
});

function AnalyticsPage() {
  const query = useDashboardStats();
  const stats = query.data;

  if (query.isError) {
    return (
      <StateCard
        title="Analytics unavailable"
        description={query.error.message || "The /dashboard/stats endpoint returned an error."}
      />
    );
  }

  if (query.isLoading || !stats) {
    return <StateCard title="Loading analytics" description="Fetching dashboard stats from FastAPI." />;
  }

  const products = stats.per_product_stats.map((item) => ({
    label: item.product_segment,
    current: item.current,
    target: item.target,
    progress: item.progress,
  }));
  const dailyActivity = stats.daily_leads.map((point) => ({
    date: point.date,
    leads: point.count,
    emails: stats.daily_emails.find((row) => row.date === point.date)?.count ?? 0,
    replies: stats.daily_replies.find((row) => row.date === point.date)?.count ?? 0,
  }));
  const funnel = Object.entries(stats.funnel).map(([label, value]) => ({ label, value }));

  return (
    <div className="space-y-5">
      <PageHeader title="Analytics" description="Discovery and outreach performance breakdowns" />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <SectionCardTitle title="Product progress" hint="Current versus target leads by product" />
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={products}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="current" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionCardTitle title="Daily activity" hint="Leads, emails and replies over time" />
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyActivity}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="leads" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="emails" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="replies" stroke="var(--chart-3)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionCardTitle title="Funnel" hint="Current CRM counts" />
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={funnel} dataKey="value" nameKey="label" innerRadius={55} outerRadius={95}>
                  {funnel.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionCardTitle title="Today by product" hint="Lead counts and remaining targets" />
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(stats.today_leads).map(([segment, target]) => (
              <div key={segment} className="rounded-md border px-3 py-2">
                <div className="flex items-center justify-between gap-3">
                  <p className="truncate text-sm font-medium">{segment}</p>
                  <Badge variant="secondary">
                    {target.current}/{target.target}
                  </Badge>
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
      </div>
    </div>
  );
}
