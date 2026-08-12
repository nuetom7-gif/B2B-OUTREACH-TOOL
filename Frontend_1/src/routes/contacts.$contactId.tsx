import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, Mail, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { PageHeader, StateCard } from "@/components/shared/page-header";
import { ConfidenceBar, StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { useContact } from "@/lib/api/hooks";

export const Route = createFileRoute("/contacts/$contactId")({
  head: () => ({
    meta: [
      { title: "Contact profile — Yash Technology Outreach Hub" },
      { name: "description", content: "Decision-maker profile with messages, replies and contactability data." },
      { property: "og:title", content: "Contact profile — Yash Technology Outreach Hub" },
      { property: "og:description", content: "Contactability, outreach history and decision-maker metadata." },
    ],
  }),
  component: ContactDetailPage,
});

function ContactDetailPage() {
  const { contactId } = Route.useParams();
  const query = useContact(contactId);

  if (query.isError) {
    return (
      <StateCard
        title="Contact unavailable"
        description={query.error.message || "The contact detail endpoint could not be reached."}
        action={
          <Button asChild>
            <Link to="/contacts">Back to contacts</Link>
          </Button>
        }
      />
    );
  }

  const contact = query.data;
  if (query.isLoading || !contact) {
    return <StateCard title="Loading contact" description="Fetching the full CRM record from FastAPI." />;
  }

  return (
    <div className="space-y-5">
      <Button variant="ghost" size="sm" asChild className="-ml-2 w-fit">
        <Link to="/contacts">
          <ArrowLeft className="size-4" /> Contacts
        </Link>
      </Button>

      <PageHeader
        title={contact.name}
        description={`${contact.title} · ${contact.company_name}`}
        actions={
          <Button onClick={() => toast.success("AI draft generation queued")}>
            <Sparkles className="size-4" /> Generate AI draft
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge status={contact.verification_status} />
        <StatusBadge status={contact.do_not_contact ? "opted_out" : "verified"} />
        <ConfidenceBar value={Math.min(100, Math.max(0, contact.lead_score))} />
        {contact.recommended_primary_contact ? <Badge variant="success">primary contact</Badge> : null}
        {contact.fallback_contact_used ? <Badge variant="secondary">fallback</Badge> : null}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <h2 className="text-sm font-semibold">Details</h2>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
            {[
              ["Email", contact.email ?? "missing"],
              ["Phone", contact.phone ?? "missing"],
              ["LinkedIn", contact.linkedin_url ?? "—"],
              ["Source", contact.source],
              ["Priority", contact.contact_priority ?? "unknown"],
              ["Selection reason", contact.contact_selection_reason ?? "—"],
              ["Latest message", contact.latest_message_subject ?? "—"],
              ["Latest status", contact.latest_message_status ?? "—"],
            ].map(([k, v]) => (
              <div key={k} className="min-w-0">
                <p className="text-xs text-muted-foreground">{k}</p>
                <p className="truncate font-medium">{v}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">Notes</h2>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              {contact.recommended_primary_contact
                ? "This contact was selected as the primary decision maker for the company."
                : "This contact was imported as part of the discovery or CRM flow."}
            </p>
            <Textarea rows={4} placeholder="Add a note…" />
            <Button size="sm" onClick={() => toast.success("Note added")}>
              <Mail className="size-3.5" /> Add note
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">Messages</h2>
          </CardHeader>
          <CardContent className="space-y-2">
            {contact.messages.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">No messages recorded.</div>
            ) : (
              contact.messages.map((message) => (
                <div key={message.id} className="rounded-md border p-3">
                  <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{message.subject}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {message.mailbox_name ?? "No mailbox"} · {message.campaign_name ?? "No campaign"}
                      </p>
                    </div>
                    <StatusBadge status={message.status} />
                  </div>
                  <Separator className="my-2" />
                  <p className="text-xs text-muted-foreground">
                    Sent at {message.sent_at ? new Date(message.sent_at).toLocaleString() : "not sent"} · Step{" "}
                    {message.sequence_step} · Replies {message.reply_count}
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">Replies</h2>
          </CardHeader>
          <CardContent className="space-y-2">
            {contact.replies.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">No replies recorded.</div>
            ) : (
              contact.replies.map((reply) => (
                <div key={reply.id} className="rounded-md border p-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium">{reply.outcome}</p>
                    <span className="text-xs text-muted-foreground">
                      {new Date(reply.received_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{reply.body}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
