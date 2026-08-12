import { BUSINESS_DIVISIONS, DEPARTMENTS, INDIAN_STATES, INDUSTRY_PACKS } from "../constants";
import type {
  ActivityEvent,
  Campaign,
  Company,
  Contact,
  DashboardMetrics,
  Distribution,
  Draft,
  DiscoveryRun,
  MailItem,
  ResearchItem,
  TaskItem,
  TrendPoint,
} from "./types";

/**
 * Deterministic sample data used only when the FastAPI backend is unreachable,
 * so every screen stays reviewable. No business logic lives here.
 */
function rng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1103515245 + 12345) % 2147483648;
    return s / 2147483648;
  };
}

const pick = <T,>(arr: readonly T[], r: number): T => arr[Math.floor(r * arr.length) % arr.length]!;

const COMPANY_NAMES = [
  "Sundaram Auto Components", "Meridian Pharma Labs", "Ultratech Aggregates", "Nova Cold Chain",
  "Aarti Speciality Chemicals", "Bharat Forge Works", "Vertex Logistics Park", "Kirloskar Pumps Division",
  "Shakti Cement Works", "Greenline Food Processing", "Dynamic Textiles Mills", "Sterling Metal Fabricators",
  "Precision Toolroom India", "Orbit Warehousing", "Anand Rathi Steel", "Krishna Dairy Foods",
  "Zenith Infra Projects", "Everest Rebar Solutions", "Kalyani Heavy Engineering", "Sagar Packaging",
  "Trident Rubber Industries", "Vasant Agro Processing", "Concord Motors Plant", "Neelkanth Ceramics",
];

const FIRST = ["Rahul", "Priya", "Anil", "Sneha", "Vikram", "Meera", "Rajesh", "Kavita", "Arun", "Deepa", "Suresh", "Nisha"];
const LAST = ["Sharma", "Iyer", "Patel", "Reddy", "Kulkarni", "Nair", "Gupta", "Desai", "Menon", "Joshi"];
const TITLES = [
  "Plant Head", "VP Operations", "Procurement Manager", "Maintenance Head", "GM Supply Chain",
  "Director Engineering", "Quality Manager", "Managing Director", "Works Manager",
];
const OWNERS = ["A. Kulkarni", "S. Verma", "R. Menon", "Unassigned"];
const PRODUCTS = [
  "Centralised Vacuum System", "Pallet Racking", "Metal Pallets", "GFRP Rebar",
  "CNC Machine Tools", "Cold Room Panels", "Mezzanine Floors",
];

export const mockCompanies: Company[] = Array.from({ length: 48 }, (_, i) => {
  const r = rng(i + 7);
  const name = `${COMPANY_NAMES[i % COMPANY_NAMES.length]!}${i >= COMPANY_NAMES.length ? " Pvt Ltd" : ""}`;
  const confidence = Math.round((0.42 + r() * 0.57) * 100);
  const needsResearch = r() > 0.72;
  const q = confidence > 78 ? "qualified" : confidence > 58 ? "review" : "disqualified";
  const statuses = ["new", "researching", "ready_for_outreach", "in_campaign", "engaged", "customer"] as const;
  return {
    id: `cmp_${1000 + i}`,
    name,
    domain: `${name.toLowerCase().replace(/[^a-z]+/g, "")}.com`,
    industry: pick(INDUSTRY_PACKS, r()),
    city: pick(["Pune", "Ahmedabad", "Chennai", "Bengaluru", "Gurugram", "Hyderabad", "Jaipur"], r()),
    state: pick(INDIAN_STATES, r()),
    country: "India",
    employees: [45, 120, 260, 480, 900, 1800, 3200][Math.floor(r() * 7) % 7]!,
    revenue: pick(["$5M-$10M", "$10M-$50M", "$50M-$100M", "$100M+"], r()),
    confidence,
    qualification: q,
    qualification_reason:
      q === "qualified"
        ? "Manufacturing footprint, employee band and ICP keywords all matched."
        : q === "review"
          ? "Industry match confirmed, but decision-maker signals are incomplete."
          : "Employee band and industry fall outside the ICP for this division.",
    contacts_count: Math.floor(r() * 9),
    owner: pick(OWNERS, r()),
    status: pick(statuses, r()),
    business_division: pick(BUSINESS_DIVISIONS, r()),
    products: [pick(PRODUCTS, r()), pick(PRODUCTS, r())].filter((v, idx, a) => a.indexOf(v) === idx),
    tags: [pick(["High Intent", "Plant Expansion", "Repeat Visitor", "Trade Show Lead"], r())],
    needs_research: needsResearch,
    linkedin_url: `https://linkedin.com/company/${name.toLowerCase().replace(/[^a-z]+/g, "-")}`,
    website: `https://${name.toLowerCase().replace(/[^a-z]+/g, "")}.com`,
    created_at: new Date(Date.now() - i * 36e5 * 7).toISOString(),
    ai_summary:
      `${name} operates multi-shift production lines where dust control and material handling are recurring cost centres. ` +
      `Recent expansion signals suggest budget availability this quarter.`,
  };
});

export const mockContacts: Contact[] = Array.from({ length: 96 }, (_, i) => {
  const r = rng(i + 91);
  const company = mockCompanies[i % mockCompanies.length]!;
  const first = pick(FIRST, r());
  const last = pick(LAST, r());
  const hasEmail = r() > 0.18;
  const hasPhone = r() > 0.45;
  const statuses = ["new", "verified", "contacted", "replied", "meeting", "bounced"] as const;
  return {
    id: `con_${2000 + i}`,
    name: `${first} ${last}`,
    designation: pick(TITLES, r()),
    department: pick(DEPARTMENTS, r()),
    company_id: company.id,
    company_name: company.name,
    email: hasEmail ? `${first.toLowerCase()}.${last.toLowerCase()}@${company.domain}` : null,
    phone: hasPhone ? `+91 ${Math.floor(70000 + r() * 29999)} ${Math.floor(10000 + r() * 89999)}` : null,
    linkedin_url: r() > 0.3 ? `https://linkedin.com/in/${first.toLowerCase()}-${last.toLowerCase()}` : null,
    source: pick(["Apollo", "Manual Research", "Website", "Referral"], r()),
    confidence: Math.round((0.5 + r() * 0.49) * 100),
    status: pick(statuses, r()),
    seniority: pick(["C-Suite", "VP", "Director", "Manager"], r()),
    created_at: new Date(Date.now() - i * 36e5 * 3).toISOString(),
    ai_summary: `Owns plant-level capex decisions and typically responds to ROI-led messaging with payback figures.`,
  };
});

export const mockResearchQueue: ResearchItem[] = mockCompanies
  .filter((c) => c.needs_research)
  .map((c, i) => ({
    id: `res_${3000 + i}`,
    company_id: c.id,
    company_name: c.name,
    website: c.website ?? null,
    linkedin_url: c.linkedin_url ?? null,
    contact_page: `${c.website}/contact-us`,
    missing_email: i % 2 === 0,
    missing_phone: i % 3 !== 0,
    missing_decision_maker: i % 4 === 0,
    notes: i % 3 === 0 ? "Reception number found, awaiting plant head extension." : "",
    status: i % 5 === 0 ? "in_progress" : "open",
    assigned_to: OWNERS[i % OWNERS.length]!,
    updated_at: new Date(Date.now() - i * 36e5 * 11).toISOString(),
  }));

export const mockDiscoveryRuns: DiscoveryRun[] = [
  {
    id: "run_9012",
    business_division: BUSINESS_DIVISIONS[0],
    industry_pack: INDUSTRY_PACKS[0],
    country: "India",
    state: "Maharashtra",
    employee_range: "201-500",
    max_companies: 120,
    status: "running",
    progress: 62,
    current_search: "auto components manufacturers Pune 201-500 employees",
    api_calls: 148,
    credits_used: 612,
    companies_found: 74,
    contacts_found: 191,
    started_at: new Date(Date.now() - 12 * 6e4).toISOString(),
    strategies: [
      { label: "Industry + Geo keywords", queries: 34, results: 41, status: "completed" },
      { label: "Keyword library expansion", queries: 26, results: 22, status: "completed" },
      { label: "People search (decision makers)", queries: 61, results: 191, status: "running" },
      { label: "Domain enrichment", queries: 27, results: 11, status: "queued" },
    ],
  },
  {
    id: "run_9011",
    business_division: BUSINESS_DIVISIONS[3],
    industry_pack: INDUSTRY_PACKS[7],
    country: "India",
    state: null,
    employee_range: "501-1000",
    max_companies: 80,
    status: "completed",
    progress: 100,
    current_search: "—",
    api_calls: 96,
    credits_used: 388,
    companies_found: 63,
    contacts_found: 142,
    started_at: new Date(Date.now() - 26 * 36e5).toISOString(),
    strategies: [
      { label: "Industry + Geo keywords", queries: 30, results: 38, status: "completed" },
      { label: "People search (decision makers)", queries: 44, results: 142, status: "completed" },
    ],
  },
  {
    id: "run_9010",
    business_division: BUSINESS_DIVISIONS[1],
    industry_pack: INDUSTRY_PACKS[5],
    country: "United Arab Emirates",
    state: null,
    employee_range: "51-200",
    max_companies: 60,
    status: "failed",
    progress: 24,
    current_search: "3PL warehouses Dubai",
    api_calls: 21,
    credits_used: 84,
    companies_found: 9,
    contacts_found: 12,
    started_at: new Date(Date.now() - 52 * 36e5).toISOString(),
    strategies: [{ label: "Industry + Geo keywords", queries: 21, results: 9, status: "failed" }],
  },
];

export const mockCampaigns: Campaign[] = [
  { id: "cam_501", name: "Vacuum Systems — Auto Belt Q3", business_division: BUSINESS_DIVISIONS[0], audience: "Qualified · Maharashtra · 201-500", template: "Cost-of-dust ROI", mailbox: "sales@yashtech.in", status: "active", scheduled_at: new Date(Date.now() + 36e5).toISOString(), recipients: 240, sent: 186, opened: 97, replied: 21, meetings: 6 },
  { id: "cam_502", name: "GFRP Rebar — Infra Tenders", business_division: BUSINESS_DIVISIONS[3], audience: "Qualified · Infrastructure", template: "Corrosion-free spec sheet", mailbox: "projects@yashtech.in", status: "scheduled", scheduled_at: new Date(Date.now() + 3 * 864e5).toISOString(), recipients: 128, sent: 0, opened: 0, replied: 0, meetings: 0 },
  { id: "cam_503", name: "Warehouse Racking — 3PL Wave 2", business_division: BUSINESS_DIVISIONS[1], audience: "Logistics · 500+", template: "Storage density calculator", mailbox: "sales@yashtech.in", status: "pending_approval", scheduled_at: null, recipients: 96, sent: 0, opened: 0, replied: 0, meetings: 0 },
  { id: "cam_504", name: "Cool Care — Dairy Cold Rooms", business_division: BUSINESS_DIVISIONS[6], audience: "Food Processing · Gujarat", template: "Energy savings case study", mailbox: "coolcare@yashtech.in", status: "completed", scheduled_at: new Date(Date.now() - 12 * 864e5).toISOString(), recipients: 174, sent: 174, opened: 111, replied: 29, meetings: 11 },
  { id: "cam_505", name: "Machine Tools — Toolroom Upgrade", business_division: BUSINESS_DIVISIONS[4], audience: "Heavy Engineering", template: "Cycle-time benchmark", mailbox: "machines@yashtech.in", status: "paused", scheduled_at: null, recipients: 88, sent: 42, opened: 18, replied: 3, meetings: 1 },
];

export const mockDrafts: Draft[] = Array.from({ length: 14 }, (_, i) => {
  const r = rng(i + 301);
  const contact = mockContacts[i * 3]!;
  const statuses = ["draft", "approved", "scheduled", "sent", "rejected"] as const;
  return {
    id: `drf_${400 + i}`,
    subject: pick(
      [
        "Cutting dust downtime at your plant",
        "Storage density without a new shed",
        "Corrosion-free rebar for your coastal project",
        "Reducing cold room energy spend",
      ],
      r(),
    ),
    body:
      `Hi ${contact.name.split(" ")[0]},\n\nI noticed ${contact.company_name} runs multi-shift production. ` +
      `Teams in your industry typically lose 4-6 hours a week to manual cleaning around the line.\n\n` +
      `We install centralised systems that cut that to under an hour, with payback inside 14 months.\n\n` +
      `Would a 15-minute call next week be useful?\n\nRegards,\nYash Technology`,
    contact_name: contact.name,
    company_name: contact.company_name,
    business_division: pick(BUSINESS_DIVISIONS, r()),
    status: pick(statuses, r()),
    model: pick(["gpt-4o", "claude-3.7-sonnet"], r()),
    version: 1 + Math.floor(r() * 3),
    created_at: new Date(Date.now() - i * 36e5 * 5).toISOString(),
  };
});

export const mockMail: MailItem[] = Array.from({ length: 40 }, (_, i) => {
  const r = rng(i + 555);
  const contact = mockContacts[i * 2]!;
  const folders = ["sent", "scheduled", "replies", "bounces", "unsubscribes"] as const;
  const folder = i < 18 ? "sent" : pick(folders, r());
  const status =
    folder === "replies" ? "replied" : folder === "bounces" ? "bounced" : folder === "unsubscribes" ? "unsubscribed" : folder === "scheduled" ? "queued" : r() > 0.5 ? "opened" : "delivered";
  return {
    id: `mail_${600 + i}`,
    subject: pick(["Cutting dust downtime at your plant", "Re: Storage density proposal", "Cold room energy audit", "Quotation follow-up"], r()),
    to: contact.email ?? `info@${contact.company_name.toLowerCase().replace(/[^a-z]+/g, "")}.com`,
    company_name: contact.company_name,
    mailbox: pick(["sales@yashtech.in", "projects@yashtech.in", "coolcare@yashtech.in"], r()),
    folder,
    delivery_status: status,
    timestamp: new Date(Date.now() - i * 36e5 * 2).toISOString(),
    preview: "Thanks for reaching out — could you share the specification sheet and a ballpark budget range?",
  };
});

export const mockMetrics: DashboardMetrics = {
  companies_discovered: 1284,
  contacts_found: 3612,
  ready_for_outreach: 418,
  needs_research: mockResearchQueue.length * 7,
  campaigns_active: 3,
  emails_sent_today: 186,
  replies: 74,
  meetings: 19,
  conversion_rate: 4.8,
  products_pitched: 7,
};

export const mockTrend: TrendPoint[] = Array.from({ length: 30 }, (_, i) => {
  const r = rng(i + 21);
  return {
    date: new Date(Date.now() - (29 - i) * 864e5).toISOString().slice(5, 10),
    companies: Math.round(20 + r() * 45 + i),
    contacts: Math.round(50 + r() * 90 + i * 2),
    emails: Math.round(60 + r() * 120),
    replies: Math.round(4 + r() * 22),
  };
});

export const mockIndustryDistribution: Distribution[] = INDUSTRY_PACKS.map((label, i) => ({
  label,
  value: [312, 248, 196, 164, 132, 108, 76, 48][i]!,
}));

export const mockDepartmentDistribution: Distribution[] = DEPARTMENTS.map((label, i) => ({
  label,
  value: [742, 664, 520, 438, 362, 254, 168][i]!,
}));

export const mockFunnel: Distribution[] = [
  { label: "Discovered", value: 1284 },
  { label: "Qualified", value: 742 },
  { label: "Contacted", value: 496 },
  { label: "Replied", value: 148 },
  { label: "Meetings", value: 42 },
  { label: "Customers", value: 11 },
];

export const mockProductDistribution: Distribution[] = PRODUCTS.map((label, i) => ({
  label,
  value: [214, 186, 158, 132, 96, 74, 52][i]!,
}));

export const mockActivity: ActivityEvent[] = [
  { id: "a1", type: "discovery", title: "Discovery run completed", description: "63 companies · 142 contacts for GFRP Rebar", actor: "Scheduler", timestamp: new Date(Date.now() - 12 * 6e4).toISOString() },
  { id: "a2", type: "reply", title: "Reply from Meridian Pharma Labs", description: "Priya Iyer asked for the specification sheet", actor: "Mailbox", timestamp: new Date(Date.now() - 46 * 6e4).toISOString() },
  { id: "a3", type: "email", title: "42 emails sent", description: "Vacuum Systems — Auto Belt Q3", actor: "Campaign engine", timestamp: new Date(Date.now() - 96 * 6e4).toISOString() },
  { id: "a4", type: "meeting", title: "Meeting booked", description: "Sterling Metal Fabricators · Thu 3:00 PM", actor: "A. Kulkarni", timestamp: new Date(Date.now() - 4 * 36e5).toISOString() },
  { id: "a5", type: "qualification", title: "18 companies re-qualified", description: "Confidence threshold raised to 0.72", actor: "Qualification engine", timestamp: new Date(Date.now() - 9 * 36e5).toISOString() },
  { id: "a6", type: "note", title: "Research note added", description: "Nova Cold Chain · plant head extension pending", actor: "S. Verma", timestamp: new Date(Date.now() - 14 * 36e5).toISOString() },
];

export const mockTasks: TaskItem[] = [
  { id: "t1", title: "Approve GFRP Rebar campaign", due: "Today, 5:00 PM", company_name: "128 recipients", priority: "high" },
  { id: "t2", title: "Call Vikram Patel (Plant Head)", due: "Tomorrow, 11:30 AM", company_name: "Bharat Forge Works", priority: "high" },
  { id: "t3", title: "Send quotation draft", due: "Wed", company_name: "Nova Cold Chain", priority: "medium" },
  { id: "t4", title: "Clear 12 research queue items", due: "Fri", company_name: "Warehouse & Storage", priority: "medium" },
  { id: "t5", title: "Review keyword library additions", due: "Next week", company_name: "Settings", priority: "low" },
];
