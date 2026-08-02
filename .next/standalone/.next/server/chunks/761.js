exports.id=761,exports.ids=[761],exports.modules={1692:(a,b,c)=>{Promise.resolve().then(c.t.bind(c,1170,23)),Promise.resolve().then(c.t.bind(c,3597,23)),Promise.resolve().then(c.t.bind(c,6893,23)),Promise.resolve().then(c.t.bind(c,9748,23)),Promise.resolve().then(c.t.bind(c,6060,23)),Promise.resolve().then(c.t.bind(c,7184,23)),Promise.resolve().then(c.t.bind(c,9576,23)),Promise.resolve().then(c.t.bind(c,3041,23)),Promise.resolve().then(c.t.bind(c,1384,23))},2704:()=>{},2862:()=>{},4614:()=>{},5244:(a,b,c)=>{Promise.resolve().then(c.t.bind(c,4160,23)),Promise.resolve().then(c.t.bind(c,1603,23)),Promise.resolve().then(c.t.bind(c,8495,23)),Promise.resolve().then(c.t.bind(c,5170,23)),Promise.resolve().then(c.t.bind(c,7526,23)),Promise.resolve().then(c.t.bind(c,8922,23)),Promise.resolve().then(c.t.bind(c,9234,23)),Promise.resolve().then(c.t.bind(c,2263,23)),Promise.resolve().then(c.bind(c,2146))},6953:(a,b,c)=>{"use strict";c.r(b),c.d(b,{default:()=>f});var d=c(5338);c(2704);let e=[{href:"/",label:"Dashboard"},{href:"/companies",label:"Companies"},{href:"/contacts",label:"Contacts"},{href:"/messages",label:"Messages"},{href:"/campaigns",label:"Campaigns"},{href:"/mailboxes",label:"Mailboxes"}];function f({children:a}){return(0,d.jsx)("html",{lang:"en",children:(0,d.jsx)("body",{children:(0,d.jsxs)("div",{className:"shell",children:[(0,d.jsxs)("div",{className:"topbar",children:[(0,d.jsxs)("div",{className:"brand",children:[(0,d.jsx)("h1",{children:"Yash Technology Outreach Hub"}),(0,d.jsx)("p",{children:"Manual-first CRM for target-account outreach, tracking, and reply handling."})]}),(0,d.jsx)("nav",{className:"nav","aria-label":"Primary",children:e.map(a=>(0,d.jsx)("a",{href:a.href,children:a.label},a.href))})]}),a]})})})}},7143:(a,b,c)=>{"use strict";c.d(b,{A7:()=>M,Ab:()=>G,E1:()=>L,Gy:()=>h,HI:()=>x,LU:()=>E,MO:()=>C,QV:()=>A,U5:()=>I,_z:()=>y,b4:()=>z,bi:()=>v,cF:()=>B,dh:()=>J,dz:()=>w,eK:()=>t,fL:()=>H,ik:()=>F,mm:()=>D,tO:()=>K,vY:()=>u});var d=c(5511),e=c(99),f=c(9902),g=c.n(f);let h=["INDUSTRIAL_VACUUM","WAREHOUSE_STORAGE","GFRP_REBAR"],i=process.env.DATABASE_URL?.startsWith("file:")?process.env.DATABASE_URL.slice(5):"./dev.db",j=g().resolve(process.cwd(),i),k=`
  PRAGMA foreign_keys = ON;

  CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    source TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS company_product_fits (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    product TEXT NOT NULL,
    UNIQUE(company_id, product)
  );

  CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    do_not_contact INTEGER NOT NULL DEFAULT 0,
    added_at TEXT NOT NULL,
    source TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    company_id TEXT REFERENCES companies(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS mailboxes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    daily_limit INTEGER NOT NULL DEFAULT 30,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    campaign_id TEXT REFERENCES campaigns(id) ON DELETE SET NULL,
    mailbox_id TEXT REFERENCES mailboxes(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    sent_at TEXT,
    sequence_step INTEGER NOT NULL DEFAULT 0,
    follow_up_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS replies (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    contact_id TEXT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    received_at TEXT NOT NULL,
    outcome TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    company_id TEXT REFERENCES companies(id) ON DELETE CASCADE,
    contact_id TEXT REFERENCES contacts(id) ON DELETE CASCADE,
    campaign_id TEXT REFERENCES campaigns(id) ON DELETE CASCADE,
    message_id TEXT REFERENCES messages(id) ON DELETE CASCADE,
    mailbox_id TEXT REFERENCES mailboxes(id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
  CREATE INDEX IF NOT EXISTS idx_messages_contact_id ON messages(contact_id);
  CREATE INDEX IF NOT EXISTS idx_messages_mailbox_sent ON messages(mailbox_id, status, sent_at);
  CREATE INDEX IF NOT EXISTS idx_replies_message_id ON replies(message_id);
  CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
`,l=null;function m(){return l||(l=new e.DatabaseSync(j)).exec(k),l}function n(){return new Date().toISOString()}function o(){return(0,d.randomUUID)()}function p(a,b=[]){return m().prepare(a).run(...b)}function q(a,b=[]){return m().prepare(a).get(...b)}function r(a,b=[]){return m().prepare(a).all(...b)}function s(a){p(`
    INSERT INTO audit_events (
      id, entity_type, entity_id, action, reason, metadata, created_at,
      company_id, contact_id, campaign_id, message_id, mailbox_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `,[o(),a.entityType,a.entityId,a.action,a.reason,JSON.stringify(a.metadata??{}),n(),a.companyId??null,a.contactId??null,a.campaignId??null,a.messageId??null,a.mailboxId??null])}function t(a){let b=o();return!function(a){let b=m();b.exec("BEGIN");try{a(),b.exec("COMMIT")}catch(a){throw b.exec("ROLLBACK"),a}}(()=>{for(let c of(p(`INSERT INTO companies (id, name, industry, source, notes, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,[b,a.name,a.industry,a.source,a.notes,n(),n()]),a.productFits))p(`INSERT INTO company_product_fits (id, company_id, product)
         VALUES (?, ?, ?)`,[o(),b,c])}),s({entityType:"company",entityId:b,action:"created",reason:`Company added manually from ${a.source}.`,metadata:{name:a.name,industry:a.industry,fits:a.productFits},companyId:b}),b}function u(a){let b=o();return p(`
    INSERT INTO contacts (
      id, name, title, company_id, email, phone, linkedin_url, do_not_contact, added_at, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
  `,[b,a.name,a.title,a.companyId,a.email??null,a.phone??null,a.linkedinUrl??null,n(),a.source]),s({entityType:"contact",entityId:b,action:"created",reason:`Contact added manually from ${a.source}.`,metadata:{name:a.name,title:a.title,email:a.email??null,companyId:a.companyId},contactId:b}),b}function v(a){let b=o();return p("INSERT INTO campaigns (id, name, notes, company_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",[b,a.name,a.notes,a.companyId??null,n(),n()]),s({entityType:"campaign",entityId:b,action:"created",reason:"Campaign created manually.",metadata:{name:a.name,companyId:a.companyId??null},campaignId:b}),b}function w(a){let b=o();return p(`INSERT INTO mailboxes (id, name, email, daily_limit, active, created_at, updated_at)
     VALUES (?, ?, ?, ?, 1, ?, ?)`,[b,a.name,a.email,a.dailyLimit,n(),n()]),s({entityType:"mailbox",entityId:b,action:"created",reason:"Mailbox created for throttled sending.",metadata:{email:a.email,dailyLimit:a.dailyLimit},mailboxId:b}),b}function x(a){let b=o();return p(`
    INSERT INTO messages (
      id, contact_id, campaign_id, mailbox_id, subject, body, status, sent_at, sequence_step, follow_up_at, created_at, updated_at
    ) VALUES (?, ?, ?, NULL, ?, ?, 'draft', NULL, ?, NULL, ?, ?)
  `,[b,a.contactId,a.campaignId??null,a.subject,a.body,a.sequenceStep,n(),n()]),s({entityType:"message",entityId:b,action:"created",reason:"Draft message created manually.",metadata:{contactId:a.contactId,subject:a.subject,sequenceStep:a.sequenceStep,campaignId:a.campaignId??null},messageId:b}),b}function y(a){var b;let c=q(`
    SELECT m.id, m.contact_id AS contactId, m.status, m.body, c.do_not_contact AS doNotContact
    FROM messages m
    JOIN contacts c ON c.id = m.contact_id
    WHERE m.id = ?
    LIMIT 1
  `,[a.messageId]);if(!c)throw Error("Message not found.");if("draft"!==c.status)throw Error("Only draft messages can be marked sent.");if(c.doNotContact)throw Error("This contact is marked do not contact.");let d=q("SELECT id, name, daily_limit AS dailyLimit, active FROM mailboxes WHERE id = ? LIMIT 1",[a.mailboxId]);if(!d||!d.active)throw Error("Select an active mailbox.");let e=q(`
    SELECT COUNT(*) AS count
    FROM messages
    WHERE mailbox_id = ?
      AND status = 'sent'
      AND sent_at >= date('now')
  `,[a.mailboxId]);if((e?.count??0)>=d.dailyLimit)throw Error(`Daily limit reached for ${d.name}. Limit is ${d.dailyLimit} per day.`);let f=(b=c.body).toLowerCase().includes("reply stop")?b.trim():`${b.trim()}

Reply STOP to stop hearing from us.`;p(`
    UPDATE messages
    SET status = 'sent', sent_at = ?, mailbox_id = ?, body = ?, updated_at = ?
    WHERE id = ?
  `,[n(),a.mailboxId,f,n(),a.messageId]),s({entityType:"message",entityId:a.messageId,action:"sent",reason:`Marked sent manually via ${d.name}.`,metadata:{mailboxId:a.mailboxId,sentToday:e?.count??0,dailyLimit:d.dailyLimit},messageId:a.messageId,mailboxId:a.mailboxId})}function z(a){let b=o();return p("INSERT INTO replies (id, message_id, contact_id, body, received_at, outcome) VALUES (?, ?, ?, ?, ?, ?)",[b,a.messageId,a.contactId,a.body,n(),a.outcome]),p("UPDATE messages SET status = 'replied', updated_at = ? WHERE id = ?",[n(),a.messageId]),s({entityType:"reply",entityId:b,action:"replied",reason:"Reply recorded manually.",metadata:{outcome:a.outcome},contactId:a.contactId,messageId:a.messageId}),b}function A(a){p("UPDATE messages SET follow_up_at = ?, updated_at = ? WHERE id = ?",[a.followUpAt,n(),a.messageId]),s({entityType:"message",entityId:a.messageId,action:"scheduled_follow_up",reason:"Follow-up date added manually.",metadata:{followUpAt:a.followUpAt},contactId:a.contactId,messageId:a.messageId})}function B(a){p("UPDATE messages SET status = 'bounced', updated_at = ? WHERE id = ?",[n(),a.messageId]),p("UPDATE contacts SET do_not_contact = 1 WHERE id = ?",[a.contactId]),s({entityType:"message",entityId:a.messageId,action:"bounced",reason:"Marked as bounced; contact set to do not contact.",metadata:{},contactId:a.contactId,messageId:a.messageId})}function C(a){p("DELETE FROM contacts WHERE id = ?",[a])}function D(){let a=r("SELECT * FROM companies ORDER BY datetime(created_at) DESC"),b=r("SELECT company_id, product FROM company_product_fits"),c=r("SELECT id, name, title, company_id FROM contacts ORDER BY datetime(added_at) DESC"),d=new Map;for(let a of b){let b=d.get(a.company_id)??[];b.push(a.product),d.set(a.company_id,b)}let e=new Map;for(let a of c){let b=e.get(a.company_id)??[];b.push({id:a.id,name:a.name,title:a.title}),e.set(a.company_id,b)}return a.map(a=>({id:a.id,name:a.name,industry:a.industry,source:a.source,notes:a.notes,createdAt:a.created_at,updatedAt:a.updated_at,productFits:d.get(a.id)??[],contacts:e.get(a.id)??[]}))}function E(){return r("SELECT id, name FROM companies ORDER BY name ASC")}function F(){return r(`
    SELECT
      c.id,
      c.name,
      c.title,
      c.company_id,
      co.name AS company_name,
      c.email,
      c.phone,
      c.linkedin_url,
      c.do_not_contact,
      c.added_at,
      c.source,
      (
        SELECT subject
        FROM messages m
        WHERE m.contact_id = c.id
        ORDER BY datetime(m.created_at) DESC
        LIMIT 1
      ) AS latest_message_subject,
      (
        SELECT status
        FROM messages m
        WHERE m.contact_id = c.id
        ORDER BY datetime(m.created_at) DESC
        LIMIT 1
      ) AS latest_message_status
    FROM contacts c
    JOIN companies co ON co.id = c.company_id
    ORDER BY datetime(c.added_at) DESC
  `).map(a=>({id:a.id,name:a.name,title:a.title,companyId:a.company_id,companyName:a.company_name,email:a.email,phone:a.phone,linkedinUrl:a.linkedin_url,doNotContact:!!a.do_not_contact,addedAt:a.added_at,source:a.source,latestMessageSubject:a.latest_message_subject,latestMessageStatus:a.latest_message_status}))}function G(a){let b=q(`
    SELECT
      c.id,
      c.name,
      c.title,
      c.company_id,
      co.name AS company_name,
      c.email,
      c.phone,
      c.linkedin_url,
      c.do_not_contact,
      c.added_at,
      c.source
    FROM contacts c
    JOIN companies co ON co.id = c.company_id
    WHERE c.id = ?
    LIMIT 1
  `,[a]);if(!b)return null;let c=r(`
    SELECT
      m.id,
      m.subject,
      m.body,
      m.status,
      m.sent_at,
      m.sequence_step,
      m.follow_up_at,
      m.created_at,
      m.updated_at,
      m.mailbox_id,
      mb.name AS mailbox_name,
      mb.email AS mailbox_email,
      m.campaign_id,
      ca.name AS campaign_name
    FROM messages m
    LEFT JOIN mailboxes mb ON mb.id = m.mailbox_id
    LEFT JOIN campaigns ca ON ca.id = m.campaign_id
    WHERE m.contact_id = ?
    ORDER BY datetime(m.created_at) DESC
  `,[a]),d=r("SELECT id, message_id, body, received_at, outcome FROM replies WHERE contact_id = ? ORDER BY datetime(received_at) DESC",[a]),e=new Map;for(let a of d){let b=e.get(a.message_id)??[];b.push(a),e.set(a.message_id,b)}return{id:b.id,name:b.name,title:b.title,companyId:b.company_id,companyName:b.company_name,email:b.email,phone:b.phone,linkedinUrl:b.linkedin_url,doNotContact:!!b.do_not_contact,addedAt:b.added_at,source:b.source,messages:c.map(a=>({id:a.id,subject:a.subject,body:a.body,status:a.status,sentAt:a.sent_at,sequenceStep:a.sequence_step,followUpAt:a.follow_up_at,createdAt:a.created_at,updatedAt:a.updated_at,mailbox:a.mailbox_id?{id:a.mailbox_id,name:a.mailbox_name,email:a.mailbox_email}:null,campaign:a.campaign_id?{id:a.campaign_id,name:a.campaign_name}:null,replies:e.get(a.id)??[]})),replies:d}}function H(){return r(`
    SELECT
      m.id,
      m.contact_id,
      c.name AS contact_name,
      co.name AS company_name,
      m.subject,
      m.status,
      mb.name AS mailbox_name,
      m.sent_at,
      m.follow_up_at,
      m.sequence_step,
      m.updated_at,
      (
        SELECT COUNT(*)
        FROM replies r
        WHERE r.message_id = m.id
      ) AS reply_count
    FROM messages m
    JOIN contacts c ON c.id = m.contact_id
    JOIN companies co ON co.id = c.company_id
    LEFT JOIN mailboxes mb ON mb.id = m.mailbox_id
    ORDER BY datetime(m.updated_at) DESC
  `).map(a=>({id:a.id,contactId:a.contact_id,contactName:a.contact_name,companyName:a.company_name,subject:a.subject,status:a.status,mailboxName:a.mailbox_name,sentAt:a.sent_at,followUpAt:a.follow_up_at,sequenceStep:a.sequence_step,updatedAt:a.updated_at,replyCount:a.reply_count}))}function I(){return r(`
    SELECT
      ca.id,
      ca.name,
      ca.notes,
      co.name AS company_name,
      COUNT(m.id) AS message_count,
      ca.created_at
    FROM campaigns ca
    LEFT JOIN companies co ON co.id = ca.company_id
    LEFT JOIN messages m ON m.campaign_id = ca.id
    GROUP BY ca.id
    ORDER BY datetime(ca.created_at) DESC
  `).map(a=>({id:a.id,name:a.name,notes:a.notes,companyName:a.company_name,messageCount:a.message_count,createdAt:a.created_at}))}function J(){return r(`
    SELECT
      mb.id,
      mb.name,
      mb.email,
      mb.daily_limit,
      mb.active,
      mb.created_at,
      (
        SELECT COUNT(*)
        FROM messages m
        WHERE m.mailbox_id = mb.id
          AND m.status = 'sent'
          AND m.sent_at >= date('now')
      ) AS sent_today
    FROM mailboxes mb
    ORDER BY datetime(mb.created_at) DESC
  `).map(a=>({id:a.id,name:a.name,email:a.email,dailyLimit:a.daily_limit,active:!!a.active,createdAt:a.created_at,sentToday:a.sent_today}))}function K(){let a=q("SELECT COUNT(*) AS count FROM contacts")?.count??0,b=q("SELECT COUNT(*) AS count FROM messages WHERE status = 'sent' AND sent_at >= date('now', 'start of month')")?.count??0,c=q("SELECT COUNT(*) AS count FROM replies")?.count??0,d=q("SELECT COUNT(*) AS count FROM mailboxes WHERE active = 1")?.count??0;return{totalContacts:a,sentMessages:b,replies:c,activeMailboxes:d,productBreakdown:r(`
    SELECT product, COUNT(*) AS count
    FROM company_product_fits
    GROUP BY product
  `),recentMessages:r(`
    SELECT
      m.id,
      m.subject,
      m.status,
      c.name AS contact_name,
      co.name AS company_name,
      mb.name AS mailbox_name
    FROM messages m
    JOIN contacts c ON c.id = m.contact_id
    JOIN companies co ON co.id = c.company_id
    LEFT JOIN mailboxes mb ON mb.id = m.mailbox_id
    ORDER BY datetime(m.updated_at) DESC
    LIMIT 6
  `).map(a=>({id:a.id,subject:a.subject,status:a.status,contactName:a.contact_name,companyName:a.company_name,mailboxName:a.mailbox_name}))}}function L(a){return a?a.split(",").map(a=>a.trim()).filter(Boolean):[]}function M(a){let b=q("SELECT id, name FROM companies WHERE name = ? LIMIT 1",[a.companyName]);return b?b.id:t({name:a.companyName,industry:a.industry,source:a.source,notes:"Created through contact import",productFits:[]})}}};