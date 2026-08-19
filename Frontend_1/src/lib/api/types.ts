export type Qualification = "qualified" | "review" | "disqualified";
export type CompanyStatus =
  | "new"
  | "researching"
  | "ready_for_outreach"
  | "in_campaign"
  | "engaged"
  | "customer"
  | "opted_out";

export interface Company {
  id: string;
  name: string;
  domain: string;
  industry: string;
  city: string;
  state: string;
  country: string;
  employees: number;
  revenue?: string;
  confidence: number;
  qualification: Qualification;
  qualification_reason: string;
  contacts_count: number;
  owner: string;
  status: CompanyStatus;
  business_division: string;
  products: string[];
  tags: string[];
  needs_research: boolean;
  linkedin_url?: string;
  website?: string;
  created_at: string;
  ai_summary?: string;
}

export type ContactStatus = "new" | "verified" | "contacted" | "replied" | "meeting" | "bounced";

export interface Contact {
  id: string;
  name: string;
  designation: string;
  department: string;
  company_id: string;
  company_name: string;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  source: string;
  confidence: number;
  status: ContactStatus;
  seniority: string;
  created_at: string;
  ai_summary?: string;
}

export interface ResearchItem {
  id: string;
  company_id: string;
  company_name: string;
  website: string | null;
  linkedin_url: string | null;
  contact_page: string | null;
  missing_email: boolean;
  missing_phone: boolean;
  missing_decision_maker: boolean;
  notes: string;
  status: "open" | "in_progress" | "resolved";
  assigned_to: string;
  updated_at: string;
}

export interface DiscoveryRun {
  id: string;
  business_division: string;
  industry_pack: string;
  country: string;
  state: string | null;
  employee_range: string;
  max_companies: number;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  current_search: string;
  api_calls: number;
  credits_used: number;
  companies_found: number;
  contacts_found: number;
  started_at: string;
  strategies: { label: string; queries: number; results: number; status: string }[];
}

export interface Campaign {
  id: string;
  name: string;
  business_division: string;
  audience: string;
  template: string;
  mailbox: string;
  status: "draft" | "pending_approval" | "scheduled" | "active" | "paused" | "completed";
  scheduled_at: string | null;
  recipients: number;
  sent: number;
  opened: number;
  replied: number;
  meetings: number;
}

export interface Draft {
  id: string;
  subject: string;
  body: string;
  contact_name: string;
  company_name: string;
  business_division: string;
  status: "draft" | "approved" | "scheduled" | "sent" | "rejected";
  model: string;
  version: number;
  created_at: string;
}

export interface MailItem {
  id: string;
  subject: string;
  to: string;
  company_name: string;
  mailbox: string;
  folder: "sent" | "scheduled" | "replies" | "bounces" | "unsubscribes";
  delivery_status: "delivered" | "queued" | "bounced" | "opened" | "replied" | "unsubscribed";
  timestamp: string;
  preview: string;
}

export interface DashboardMetrics {
  companies_discovered: number;
  contacts_found: number;
  ready_for_outreach: number;
  needs_research: number;
  campaigns_active: number;
  emails_sent_today: number;
  replies: number;
  meetings: number;
  conversion_rate: number;
  products_pitched: number;
}

export interface TrendPoint {
  date: string;
  companies: number;
  contacts: number;
  emails: number;
  replies: number;
}

export interface Distribution {
  label: string;
  value: number;
}

export interface ActivityEvent {
  id: string;
  type: "discovery" | "email" | "reply" | "meeting" | "note" | "qualification";
  title: string;
  description: string;
  actor: string;
  timestamp: string;
}

export interface TaskItem {
  id: string;
  title: string;
  due: string;
  company_name: string;
  priority: "low" | "medium" | "high";
}

export interface BackendCompany {
  id: number;
  name: string;
  industry: string;
  source: string;
  source_provider: string | null;
  source_record_id: string | null;
  notes: string;
  product_fits: string[];
  contact_count: number;
  apollo_organization_id: string | null;
  apollo_last_updated: string | null;
  last_sync: string | null;
  sync_status: string;
  needs_manual_review: boolean;
  discovery_contacts_returned: number;
  contact_status: string;
  fallback_contact_used: boolean;
  owner_id: number | null;
  assignment_status: string;
  assigned_at: string | null;
  assignment_source: string | null;
  lead_score: number;
}

export interface BackendContact {
  id: number;
  name: string;
  title: string;
  company_id: number;
  company_name: string;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  do_not_contact: boolean;
  added_at: string;
  source: string;
  source_provider: string | null;
  source_record_id: string | null;
  latest_message_subject: string | null;
  latest_message_status: string | null;
  apollo_person_id: string | null;
  verification_status: string;
  last_sync: string | null;
  lead_score: number;
  contact_priority: string | null;
  recommended_primary_contact: boolean;
  fallback_contact_used: boolean;
  contact_selection_reason: string | null;
  discovery_profiles: string[];
}

export interface BackendContactDetail extends BackendContact {
  messages: {
    id: number;
    subject: string;
    body?: string;
    status: string;
    sent_at: string | null;
    sequence_step: number;
    follow_up_at: string | null;
    mailbox_name: string | null;
    campaign_name: string | null;
    reply_count: number;
  }[];
  replies: {
    id: number;
    message_id: number;
    body: string;
    received_at: string;
    outcome: string;
  }[];
}

export interface BackendCampaign {
  id: number;
  name: string;
  notes: string;
  company_name: string | null;
  message_count: number;
}

export interface BackendMailbox {
  id: number;
  name: string;
  email: string;
  daily_limit: number;
  active: boolean;
  sent_today: number;
}

export interface BackendDashboardSummary {
  total_contacts: number;
  messages_sent_this_month: number;
  reply_rate: number;
  active_mailboxes: number;
  product_breakdown: { product: string; count: number }[];
  recent_messages: {
    id: number;
    subject: string;
    status: string;
    contact_name: string;
    company_name: string;
    mailbox_name: string | null;
  }[];
}

export interface BackendDashboardStats {
  today_leads: Record<string, { target: number; current: number; remaining: number }>;
  today_emails_sent: number;
  today_replies: number;
  reply_rate: number;
  bounce_rate: number;
  apollo_credits_remaining: number;
  pending_drafts: number;
  pending_reviews: number;
  do_not_contact_count: number;
  per_product_stats: { product_segment: string; target: number; current: number; remaining: number; progress: number }[];
  daily_leads: { date: string; count: number }[];
  daily_emails: { date: string; count: number }[];
  daily_replies: { date: string; count: number }[];
  funnel: Record<string, number>;
  recent_activity: {
    id: number;
    subject: string;
    status: string;
    contact_name: string;
    company_name: string;
    mailbox_name: string | null;
  }[];
  active_mailboxes: number;
  total_contacts: number;
}

export interface BackendDraft {
  id: number;
  contact_id: number;
  contact_name: string;
  company_name: string;
  campaign_id: number | null;
  campaign_name: string | null;
  subject: string;
  body: string;
  status: string;
  sequence_step: number;
  updated_at: string;
}

export interface BackendMessage {
  id: number;
  contact_id: number;
  contact_name: string;
  company_name: string;
  subject: string;
  status: string;
  mailbox_name: string | null;
  sent_at: string | null;
  follow_up_at: string | null;
  sequence_step: number;
  reply_count: number;
}

export interface BackendReply {
  id: number;
  message_id: number;
  body: string;
  received_at: string;
  outcome: string;
}

export interface BackendDiscoveryRun {
  id: number;
  product_name: string;
  search_frequency: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  companies_found: number;
  companies_imported: number;
  companies_updated: number;
  companies_skipped: number;
  contacts_found: number;
  contacts_imported: number;
  contacts_updated: number;
  contacts_skipped: number;
  api_calls_used: number;
  quota_remaining: number | null;
  errors: string[];
  warnings: string[];
  qualification_summary: Record<string, unknown>;
  qualification_top_failure_reasons: { reason: string; count: number }[];
  reason_breakdown: Record<string, unknown>;
  qualification_average_score: number;
  qualification_evaluated_count: number;
  qualification_imported_count: number;
  qualification_manual_review_count: number;
  qualification_rejected_count: number;
}

export interface BackendDiscoveryStagingRecord {
  id: number;
  run_id: number;
  product_name: string;
  provider_name: string;
  record_type: string;
  apollo_organization_id: string | null;
  apollo_person_id: string | null;
  company_name: string | null;
  company_domain: string | null;
  industry: string | null;
  country: string | null;
  region: string | null;
  employee_count: number | null;
  company_size: string | null;
  person_name: string | null;
  person_title: string | null;
  person_email: string | null;
  person_phone: string | null;
  person_linkedin_url: string | null;
  person_seniority: string | null;
  raw_organization: Record<string, unknown>;
  organization_mapping: Record<string, unknown>;
  people_request: unknown;
  raw_people_response: unknown;
  normalized_company: Record<string, unknown>;
  normalized_contacts: Record<string, unknown>[];
  qualification_input: Record<string, unknown>;
  qualification_status: string;
  final_status: string;
  decision_stage: string;
  reason_category: string;
  reason_details: Record<string, unknown>;
  score: number;
  qualification_threshold: number | null;
  manual_review_threshold: number | null;
  qualification_evaluated_at: string | null;
  qualification_result: Record<string, unknown>;
  confidence: string;
  needs_manual_review: boolean;
  sync_status: string;
  error_message: string | null;
  warning_message: string | null;
  crm_company_id: number | null;
  crm_contact_id: number | null;
  apollo_last_updated: string | null;
  last_sync: string | null;
}

export interface BackendDiscoveryStagingPage {
  items: BackendDiscoveryStagingRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface BackendDiscoveryProfile {
  profile_name: string;
  product_name: string;
  business_division: string;
  target_segment: string;
  enabled: boolean;
  countries: string[] | string | null;
  states: string[] | null;
  employee_min: number | null;
  employee_max: number | null;
  decision_makers?: string[];
  company_keywords?: string[];
  apollo_industries?: string[];
  related_industries?: string[];
}

export interface BackendSetting {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_from: string;
  default_campaign_id: number | null;
  default_mailbox_id: number | null;
  max_emails_per_batch: number;
  [key: string]: unknown;
}

export interface BackendWorkspaceProfile {
  company_name: string;
  user_name: string;
  user_role: string;
}

export interface BackendDailyTarget {
  id: number;
  product_segment: string;
  target_leads_per_day: number;
  companies_per_run: number;
  contacts_per_company: number;
  max_emails_per_batch: number;
  active: boolean;
  default_campaign_id: number | null;
  default_mailbox_id: number | null;
  today_leads: number;
}
