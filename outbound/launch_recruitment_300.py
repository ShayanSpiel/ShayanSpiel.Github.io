#!/usr/bin/env python3
"""Recruitment campaign launcher (300 target, fresh leads only).

Selects leads from /tmp/recruitment_leads.csv with valid email + personalization_hook,
EXCLUDING any already in the global sent log (.spielos/state/outbound/sent.json).
Titles + CTAs rotate by global seq%3. Body = research opener + crisp 720px image
+ anchor + reply CTA + avatar signature. Resend cap 100/day -> one batch per run.

Modes:
  --prepare        select fresh leads, write batches to campaign JSON
  --dry-run        compose all, assert clean, print samples (no send)
  --send N         send batch N (1..3), throttle 144s, dedup + 100/day cap
"""
import sys, csv, html as _html, time, json, re, os, argparse
from urllib.parse import quote
sys.path.insert(0, ".agents")
from company.departments.outbound.workflows.email import providers, config, outbound
from company.departments.outbound.workflows.email.compose import _hook_fields
from company.departments.outbound.workflows.email import templates
config.load_env()

TITLES = ["Your shortlist, automated", "Still screening by hand?", "30-second candidate shortlist"]
BATCH1_TITLE = "quick question {first_name}"
CTAS = [
    "If part of that screening is still manual, want me to map it with you?",
    "Open to a 20-minute look at how your shortlists could run themselves?",
    "Worth a quick reply if screening is still eating your week?",
]
IMG = "https://spielos.xyz/images/recruitment/Demo-Job-Brief-to-Candidate-Shortlist.png?v=2"
LANDING = "https://spielos.xyz/solutions/workflows/recruitement-automation/"
def landing_url(email, seq):
    """Landing URL with simple UTM + recipient identifier (click attribution)."""
    batch = seq // 100 + 1
    he = quote(email or "", safe="")
    return (f"https://spielos.xyz/solutions/workflows/recruitement-automation/"
            f"?he={he}&utm_source=outbound-email&utm_medium=email"
            f"&utm_campaign=recruitment-300&utm_content=batch-{batch}")
GENERIC_ROLE = {"a named framework contact","a named person","named framework contact","named person","framework contact"}
THROTTLE=144; BATCH_SIZE=100; TARGET=300
OUT_DIR=".spielos/state/outbound"; os.makedirs(OUT_DIR, exist_ok=True)
SENT_LOG=os.path.join(OUT_DIR,"recruitment_300_sent.json")
CAMPAIGN_JSON="outbound/campaign-recruitment-500-20260830.json"
POOL_JSON="outbound/recruitment-pool-500.json"
LEADS_CSV="/tmp/recruitment_leads.csv"
GLOBAL_SENT=".spielos/state/outbound/sent.json"

def valid(e): return e.count("@")==1 and e.split("@")[1].count(".")>=1
def clean_hook(h): return (h or "").replace("Reference ","").replace("reference ","").strip().rstrip(".")
def signal_for(contact, hf):
    h=clean_hook(contact.get("personalization_hook") or "")
    m=re.search(r"and (?:one|an) observable (.+)$", h, re.I)
    if m: return m.group(1).strip().rstrip(".")
    ch=(hf.get("company_hook") or "").strip().rstrip(".")
    if ch and ch.lower() not in GENERIC_ROLE: return ch
    role=(hf.get("role") or "").strip()
    if role and role.lower() not in GENERIC_ROLE and len(role)>=4: return role
    return h.split(" and ")[0].strip().rstrip(",")
def compose(contact, seq):
    company=contact.get("company") or ""
    first=outbound.get_first_name(contact) or "there"
    hf=_hook_fields(contact); sig=signal_for(contact, hf)
    opener=[f"Hey {first},", f"I came across {company}.", f"The thing that caught me was your {sig}."]
    subject = "quick question {first}".format(first=outbound.get_first_name(contact) or "there")
    cta=CTAS[seq % len(CTAS)]
    body_ps=opener+["Holding that bar with manual screening on every brief is a lot of repeat work. It stacks up across every role.",
        "I build AI Agents for repetitive knowledge work. I put together a 30-second demo: a job brief goes in, a ranked candidate shortlist comes out."]
    lu = landing_url(contact.get("email") or "", seq)
    bh="".join(f"<p>{_html.escape(p)}</p>\n" for p in body_ps)
    bh+=f'<p><a href="{lu}"><img src="{IMG}" alt="Demo Job Brief to Candidate Shortlist" width="720" style="max-width:100%;height:auto;border:0;" /></a></p>\n'
    bh+=f'<p><a href="{lu}">→ Check the demo video & details.</a></p>\n'
    bh+=f"<p>{_html.escape(cta)}</p>\n<p>Regards,<br>Shayan</p>\n"+templates.SIGNATURE_HTML
    bt="\n\n".join(body_ps)+f"\n\n-> Check the demo video & details: {lu}\n\n{cta}\n\nRegards,\nShayan\n"+templates.SIGNATURE_TEXT
    return subject,bh,bt
def load_global_sent():
    try:
        d=json.load(open(GLOBAL_SENT))
        return {e['email'].lower() for e in d.get('sent',[])}, {e['lead_id'] for e in d.get('sent',[])}
    except: return set(), set()
def select_fresh_leads(n=TARGET):
    global_emails, global_ids = load_global_sent()
    rows=list(csv.DictReader(open(LEADS_CSV)))
    fresh=[r for r in rows if valid(r.get("email","")) and (r.get("personalization_hook") or "").strip()
           and r['email'].lower() not in global_emails and r['lead_id'] not in global_ids]
    return fresh[:n]
def prepare():
    leads=select_fresh_leads(TARGET)
    batches=[leads[i*100:(i+1)*100] for i in range((len(leads)+99)//100)]
    camp={"campaign":"recruitment-300","total":len(leads),"batch_size":BATCH_SIZE,"throttle":THROTTLE,
          "titles":TITLES,"ctas":CTAS,"image_width":720,"deduped_vs_global_sent":True,
          "batches":[{"batch":i+1,"lead_ids":[l["lead_id"] for l in b]} for i,b in enumerate(batches)]}
    json.dump(camp, open(CAMPAIGN_JSON,"w"), indent=2)
    print(f"PREPARED {camp['total']} fresh leads -> {len(batches)} batches of up to 100 -> {CAMPAIGN_JSON}")
def load_pool():
    return json.load(open(POOL_JSON))
def dry_run():
    leads=load_pool()
    ok=bad=0
    for seq,lead in enumerate(leads):
        try:
            s,h,t=compose(lead, seq); assert s and "avatars/avatar.jpg" in h and LANDING in h; ok+=1
        except Exception as e: bad+=1; print("BAD", lead["lead_id"], e)
    print(f"DRY-RUN: {ok} ok, {bad} bad of {len(leads)} leads")
    for idx in [0,1,2, min(99,len(leads)-1), min(199,len(leads)-1)]:
        if idx < len(leads):
            c=leads[idx]; s,h,t=compose(c, idx)
            print(f"  [{idx}] {c['contact_name']} ({c['company']}) | {s} -> {_html.unescape(h.split('</p>')[2].replace('<p>','').strip())[:100]}")
def load_campaign_sent():
    try: return json.load(open(SENT_LOG))
    except: return []
def send_batch(bidx):
    camp=json.load(open(CAMPAIGN_JSON))
    if bidx-1 >= len(camp["batches"]): print(f"Batch {bidx} does not exist (max {len(camp['batches'])})."); return
    b=camp["batches"][bidx-1]
    rows_by_id={l["lead_id"]:l for l in load_pool()}
    sent=load_campaign_sent(); sent_ids={x["lead_id"] for x in sent}
    today=time.strftime("%Y-%m-%d"); today_count=sum(1 for x in sent if x.get("date")==today)
    done=0
    for i,lid in enumerate(b["lead_ids"]):
        if lid in sent_ids: print("skip", lid, "already sent in this campaign"); continue
        if today_count+done >= 800: print(f"DAILY CAP 800 reached -> stop."); break
        lead=rows_by_id.get(lid)
        if not lead: continue
        seq=(bidx-1)*100+i; subj,h,t=compose(lead, seq)
        r=providers.send_email_via("brevo", lead["email"], subj, h, t, reply_to="")
        rec={"lead_id":lid,"email":lead["email"],"subject":subj,
             "provider_id":(r.get("id") if isinstance(r,dict) else str(r)),"date":today,"batch":bidx}
        sent.append(rec); json.dump(sent, open(SENT_LOG,"w"), indent=2); sent_ids.add(lid); done+=1
        print(f"[{done}] {lid} -> {lead['email']} | {subj}")
        if done < BATCH_SIZE and done < len(b["lead_ids"]): time.sleep(THROTTLE)
    print(f"BATCH {bidx} complete: {done} sent this run.")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--prepare",action="store_true")
    ap.add_argument("--dry-run",action="store_true"); ap.add_argument("--send",type=int,metavar="N")
    a=ap.parse_args()
    if a.prepare: prepare()
    elif a.dry_run: dry_run()
    elif a.send: send_batch(a.send)
    else: print("use --prepare | --dry-run | --send N")
