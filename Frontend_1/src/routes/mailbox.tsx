import { createFileRoute } from "@tanstack/react-router";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMessages } from "@/lib/api/hooks";

export const Route = createFileRoute("/mailbox")({
  head: () => ({
    meta: [
      { title: "Mailbox — Yash Technology Outreach Hub" },
      { name: "description", content: "Sent, drafted, replied and bounced outreach messages from FastAPI." },
      { property: "og:title", content: "Mailbox — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Track every outreach email and reply across connected mailboxes." },
    ],
  }),
  component: MailboxPage,
});

function MailboxPage() {
  const query = useMessages();
  const messages = query.data ?? [];

  if (query.isError) {
    return (
      <StateCard
        title="Mailbox unavailable"
        description={query.error.message || "The /messages endpoint returned an error."}
      />
    );
  }

  if (query.isLoading) {
    return <StateCard title="Loading mailbox" description="Fetching live message history from FastAPI." />;
  }

  const statuses = Array.from(new Set(messages.map((message) => message.status))).sort();

  return (
    <div className="space-y-5">
      <PageHeader title="Mailbox" description={`${messages.length} message events`} />

      <Tabs defaultValue={statuses[0] ?? "sent"}>
        <TabsList className="flex-wrap">
          {statuses.map((status) => (
            <TabsTrigger key={status} value={status} className="capitalize">
              {status}
            </TabsTrigger>
          ))}
        </TabsList>

        {statuses.map((status) => {
          const items = messages.filter((message) => message.status === status);
          return (
            <TabsContent key={status} value={status} className="space-y-2">
              {items.length === 0 ? (
                <Card>
                  <CardContent className="py-10 text-center text-sm text-muted-foreground">Nothing here yet.</CardContent>
                </Card>
              ) : (
                items.map((message) => (
                  <Card key={message.id}>
                    <CardContent className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-3">
                      <div className="min-w-0">
                        <p className="truncate font-medium">{message.subject}</p>
                        <p className="truncate text-xs text-muted-foreground">
                          {message.contact_name} · {message.company_name} · {message.mailbox_name ?? "No mailbox"}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {message.sent_at ? new Date(message.sent_at).toLocaleString() : "Not sent yet"} · step{" "}
                          {message.sequence_step} · replies {message.reply_count}
                        </p>
                      </div>
                      <StatusBadge status={message.status} />
                    </CardContent>
                  </Card>
                ))
              )}
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
}
