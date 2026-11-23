# ScamLens-AI Benchmark Dataset: Indian Bank & Institutional Emails (Raw RFC 5322)

> **Dataset Overview**: 20 complete, realistic emails (5 HAM, 15 SPAM) formatted in standard raw RFC 5322 / MIME format.
> **Purpose**: Offline pipeline execution and Proof-of-Concept testing without connecting to live Gmail APIs.
> **Parser Support**: Python scripts in `src/scamlens/extractors/email.py` (`LocalEmailReader`, `load_emails_from_file`, `parse_raw_email`, `parse_gmail_message`) automatically read and separate out all fields (`From`, `To`, `Cc`, `Subject`, `Date`, `Reply-To`, `Body`, `Attachments`, `Links`, `SPF/DKIM/DMARC`).

---

## Quick Start: Reading and Parsing Local Emails with Python

```python
from scamlens.extractors.email import LocalEmailReader, load_emails_from_file

# Option 1: Drop-in replacement for GmailReader (reads 1.eml ... 20.eml from data/raw_emails/)
reader = LocalEmailReader("data/raw_emails")
emails = reader.fetch_messages()

# Option 2: Read from local JSON dataset (exact Gmail REST API format)
# reader = LocalEmailReader("data/spam-indian-bank-emails.json")

# Option 3: Read directly from Markdown (.md)
# emails = load_emails_from_file("data/spam-indian-bank-emails.md")

# Inspect separated fields
for msg in emails:
    print(f'[{msg.id}] {msg.subject}')
    print(f'  From: {msg.sender} | To: {msg.recipient} | Cc: {msg.cc}')
    print(f'  Auth: SPF={msg.spf_status}, DKIM={msg.dkim_status}, DMARC={msg.dmarc_status}')
    print(f'  Urls found ({len(msg.extracted_urls)}): {msg.extracted_urls[:2]}')
    print(f'  Attachments ({len(msg.attachments)}): {[a.filename for a in msg.attachments]}')
```

---

## Dataset Index Table

| # | EML File | Classification | Category | Claimed Institution | Subject |
|:---|:---|:---|:---|:---|:---|
| 1 | `1.eml` | ✅ **HAM** | Banking | HDFC Bank Limited | Your HDFC Bank Credit Card e-Statement for Card ending 4892 (Billing Cycle: Sept 2026) |
| 2 | `2.eml` | ✅ **HAM** | Banking | State Bank of India (SBI) | Debit Alert: Your SBI A/C XXXXXXXX4012 has been debited by Rs 25,000.00 via NEFT |
| 3 | `3.eml` | ✅ **HAM** | Insurance | Life Insurance Corporation of India (LIC) | LIC Policy Premium Due Notice - Policy No. 842109482 (Plan: Jeevan Labh) |
| 4 | `4.eml` | ✅ **HAM** | Income Tax | Income Tax Department, Ministry of Finance, Govt of India | Intimation Order u/s 143(1) of the Income-tax Act, 1961 for PAN: AXXXX1234X - AY 2024-25 |
| 5 | `5.eml` | ✅ **HAM** | Customs & Postal Services | Department of Posts, Ministry of Communications, Govt of India | Speed Post Consignment Dispatched: Article No. EK829104821IN (From: NSDL e-Governance) |
| 6 | `6.eml` | 🚨 **SPAM** | Banking | State Bank of India (Spoofed) | CRITICAL NOTICE: Your SBI YONO Account is Suspended - Immediate KYC Update Required |
| 7 | `7.eml` | 🚨 **SPAM** | Banking | ICICI Bank (Spoofed) | Notice: 18,450 ICICI Payback Points Expiring Tonight - Claim Cash Value Rs 9,225 Directly |
| 8 | `8.eml` | 🚨 **SPAM** | Banking | HDFC Bank (Spoofed) | Final Reminder: Immediate PAN Linking Required for HDFC Bank Account - Debit Freeze Alert |
| 9 | `9.eml` | 🚨 **SPAM** | Banking | Axis Bank (Spoofed) | Congratulations: Your Axis Credit Card limit has been increased to Rs 8,50,000 (Action Required) |
| 10 | `10.eml` | 🚨 **SPAM** | Banking | Punjab National Bank (Spoofed) | ALERT: Unauthorized transfer of Rs. 74,500 debited from your PNB A/C - Cancel Immediately |
| 11 | `11.eml` | 🚨 **SPAM** | Insurance | Life Insurance Corporation of India (Spoofed) | Approval of Accumulated Lapsed Policy Bonus: Rs. 4,85,000 (Mandatory Action Required) |
| 12 | `12.eml` | 🚨 **SPAM** | Insurance | Max Life Insurance (Spoofed) | URGENT WARNING: Your Cashless Health Claim #ML-84210 is Pending Rejection (Install App to Verify) |
| 13 | `13.eml` | 🚨 **SPAM** | Income Tax | Income Tax Department of India (Spoofed) | Tax Refund Approved: Rs. 38,490 Pending Verification - Update Bank Account Details |
| 14 | `14.eml` | 🚨 **SPAM** | Income Tax | Directorate General of Income Tax (Investigation) (Spoofed) | LEGAL SUMMONS: Tax Evasion & High-Value Foreign Remittance Notice u/s 148 |
| 15 | `15.eml` | 🚨 **SPAM** | Law Enforcement (CBI) | Central Bureau of Investigation (CBI) (Spoofed) | CONFIDENTIAL / COURT SUMMONS: Non-Bailable Arrest Warrant u/s 3 & 4 PMLA - Digital Arrest Order |
| 16 | `16.eml` | 🚨 **SPAM** | Law Enforcement (CBI & Cyber Police) | CBI & National Cyber Crime Threat Coordination Unit (Spoofed) | OFFICIAL SUMMONS: Serious Cyber Crime & Illegal Content Seizure - Immediate Warrant Registered |
| 17 | `17.eml` | 🚨 **SPAM** | Customs & Border Control | Customs Commissionerate, Chhatrapati Shivaji Maharaj International Airport (Spoofed) | INTERCEPTED DIPLOMATIC PARCEL: High-Value Consignment Held at Mumbai Airport - Duty Clearance Required |
| 18 | `18.eml` | 🚨 **SPAM** | Customs & Narcotics Control | Narcotics Control Bureau & IGI Airport Customs (Spoofed) | EMERGENCY SUMMONS: Interception of Narcotics (MDMA) Consignment Booked Under Your Name |
| 19 | `19.eml` | 🚨 **SPAM** | Utility Services | State Electricity Distribution Corporation Limited (Spoofed) | FINAL DISCONNECTION WARNING: Electricity Power Cut Tonight at 9:30 PM Due to Unpaid Bill |
| 20 | `20.eml` | 🚨 **SPAM** | Customs & Postal Services | India Post (Department of Posts) (Spoofed) | Delivery Failed: India Post Package IN842109482 Stopped Due to Incomplete Address - Update Within 24h |

---

## Raw RFC 5322 Email Messages

### 1.eml (EMAIL_001): Your HDFC Bank Credit Card e-Statement for Card ending 4892 (Billing Cycle: Sept 2026)
- **Ground Truth**: `✅ HAM (Legitimate)`
- **Claimed Organization**: `HDFC Bank Limited` (Banking)
- **Raw File**: `data/raw_emails/1.eml`

```email
From: HDFC Bank NetBanking Alerts <alerts@hdfcbank.net>
To: customer.prakash@gmail.com
Subject: Your HDFC Bank Credit Card e-Statement for Card ending 4892 (Billing
 Cycle: Sept 2026)
Date: Mon, 05 Oct 2026 04:15:30 +0530
Reply-To: customer.service@hdfcbank.com
Authentication-Results: mx.google.com; spf=pass (mail.server designates
 permitted sender) smtp.mailfrom=HDFC Bank NetBanking Alerts
 <alerts@hdfcbank.net>; dkim=pass; dmarc=pass
Received-SPF: pass (sender IP: 175.100.162.24 is authorized by hdfcbank.net)
Message-ID: <1.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============1897353019210480090=="

--===============1897353019210480090==
Content-Type: multipart/alternative;
 boundary="===============0484207553250377939=="

--===============0484207553250377939==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear PRAKASH R,

Thank you for banking with HDFC Bank.

Please find attached your password-protected monthly e-Statement for HDFC Ban=
k Credit Card ending with 4892 for the billing cycle ending 04-Oct-2026.

STATEMENT SUMMARY:
--------------------------------------------------
Total Amount Due        : Rs. 14,820.50
Minimum Amount Due      : Rs. 850.00
Payment Due Date        : 24-Oct-2026
Credit Limit            : Rs. 2,50,000.00
Available Credit Limit  : Rs. 2,35,179.50
Reward Points Earned    : 1,480 Points
--------------------------------------------------

HOW TO OPEN YOUR ATTACHED STATEMENT:
The attached statement is password-protected. Your password is your 4-charact=
er Date & Month of Birth (DDMM) followed by the last 4 digits of your Credit =
Card number.
Example: If your Date of Birth is 15th August and your card number ends with =
4892, your password is: 15084892.

PAYMENT OPTIONS:
You can settle your dues seamlessly using:
1. HDFC Bank NetBanking / MobileBanking App: https://netbanking.hdfcbank.com
2. Auto-Debit instructions from your HDFC savings account
3. UPI / BillDesk / BBPS using your card number

SECURITY NOTICE:
HDFC Bank never asks for your NetBanking password, OTP, Credit Card PIN, or C=
VV over email, phone call, or SMS. If you notice any suspicious activity, imm=
ediately call our 24x7 toll-free helpline at 1800 202 6161.

--
Warm Regards,
Credit Card Customer Services Team
HDFC Bank Limited
Registered Office: HDFC Bank House, Senapati Bapat Marg, Lower Parel (West), =
Mumbai - 400013
CIN: L65920MH1994PLC080618 | Website: https://www.hdfcbank.com
National Cyber Crime Helpline: 1930 | RBI Banking Ombudsman: https://cms.rbi.=
org.in

DISCLAIMER:
This email and any files transmitted with it are confidential and intended so=
lely for the use of the individual to whom they are addressed. If you have re=
ceived this transmission in error, please notify the sender immediately and d=
elete this email from your system.

--===============0484207553250377939==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"https://www.hdfcbank.com/content/api/contentstream-id/723fb80a-=
2dde-42a3-9793-7ae1be57c87f/2c9c7f68-7c85-4dbb-8b5d-007a0cbe6a8e/logo.png" al=
t=3D"HDFC Bank Official Blue Logo" style=3D"max-height: 48px; margin-right: 1=
2px; vertical-align: middle;" />
  <img src=3D"https://www.hdfcbank.com/assets/images/security-guarantee-shiel=
d.png" alt=3D"VeriSign SSL Secured Email Shield" style=3D"max-height: 48px; m=
argin-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear PRAKASH R,</p>
<p style=3D"margin: 0 0 12px 0;">Thank you for banking with HDFC Bank.</p>
<p style=3D"margin: 0 0 12px 0;">Please find attached your password-protected=
 monthly e-Statement for HDFC Bank Credit Card ending with 4892 for the billi=
ng cycle ending 04-Oct-2026.</p>
<p style=3D"margin: 0 0 12px 0;">STATEMENT SUMMARY:<br/>---------------------=
-----------------------------<br/>Total Amount Due        : Rs. 14,820.50<br/=
>Minimum Amount Due      : Rs. 850.00<br/>Payment Due Date        : 24-Oct-20=
26<br/>Credit Limit            : Rs. 2,50,000.00<br/>Available Credit Limit  =
: Rs. 2,35,179.50<br/>Reward Points Earned    : 1,480 Points<br/>------------=
--------------------------------------</p>
<p style=3D"margin: 0 0 12px 0;">HOW TO OPEN YOUR ATTACHED STATEMENT:<br/>The=
 attached statement is password-protected. Your password is your 4-character =
Date &amp; Month of Birth (DDMM) followed by the last 4 digits of your Credit=
 Card number.<br/>Example: If your Date of Birth is 15th August and your card=
 number ends with 4892, your password is: 15084892.</p>
<p style=3D"margin: 0 0 12px 0;">PAYMENT OPTIONS:<br/>You can settle your due=
s seamlessly using:<br/>1. HDFC Bank NetBanking / MobileBanking App: <a href=
=3D"https://netbanking.hdfcbank.com" style=3D"color: #0066cc; text-decoration=
: underline;">HDFC Bank NetBanking Portal</a><br/>2. Auto-Debit instructions =
from your HDFC savings account<br/>3. UPI / BillDesk / BBPS using your card n=
umber</p>
<p style=3D"margin: 0 0 12px 0;">SECURITY NOTICE:<br/>HDFC Bank never asks fo=
r your NetBanking password, OTP, Credit Card PIN, or CVV over email, phone ca=
ll, or SMS. If you notice any suspicious activity, immediately call our 24x7 =
toll-free helpline at 1800 202 6161.</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Warm Regards,<br/>Credit Card Cu=
stomer Services Team<br/>HDFC Bank Limited<br/>Registered Office: HDFC Bank H=
ouse, Senapati Bapat Marg, Lower Parel (West), Mumbai - 400013<br/>CIN: L6592=
0MH1994PLC080618 | Website: https://www.hdfcbank.com<br/>National Cyber Crime=
 Helpline: 1930 | RBI Banking Ombudsman: https://cms.rbi.org.in<br/><br/>DISC=
LAIMER:<br/>This email and any files transmitted with it are confidential and=
 intended solely for the use of the individual to whom they are addressed. If=
 you have received this transmission in error, please notify the sender immed=
iately and delete this email from your system.</div>
</body>
</html>

--===============0484207553250377939==--

--===============1897353019210480090==
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="HDFC_Statement_Sep2026_4892.pdf"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIEhERkNfU3RhdGVtZW50X1NlcDIwMjZfNDg5Mi5wZGYKR2Vu
ZXJhdGVkIGZvciBTY2FtTGVucy1BSSBQb0Mu

--===============1897353019210480090==--
```

---

### 2.eml (EMAIL_002): Debit Alert: Your SBI A/C XXXXXXXX4012 has been debited by Rs 25,000.00 via NEFT
- **Ground Truth**: `✅ HAM (Legitimate)`
- **Claimed Organization**: `State Bank of India (SBI)` (Banking)
- **Raw File**: `data/raw_emails/2.eml`

```email
From: SBI Internet Banking Alerts <donotreply@sbi.co.in>
To: anita.deshmukh@gmail.com
Subject: Debit Alert: Your SBI A/C XXXXXXXX4012 has been debited by Rs
 25,000.00 via NEFT
Date: Fri, 16 Oct 2026 14:22:15 +0530
Reply-To: None
Authentication-Results: mx.google.com; spf=pass (mail.server designates
 permitted sender) smtp.mailfrom=SBI Internet Banking Alerts
 <donotreply@sbi.co.in>; dkim=pass; dmarc=pass
Received-SPF: pass (sender IP: 115.112.234.18 is authorized by sbi.co.in)
Message-ID: <2.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============5536454062743114745=="

--===============5536454062743114745==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear Customer,

Your State Bank of India Account XXXXXXXX4012 has been debited by Rs. 25,000.=
00 on 16-Oct-2026 14:21:42 IST towards an outward NEFT transfer.

TRANSACTION DETAILS:
--------------------------------------------------
Transaction Reference (UTR) : SBIN326289104821
Beneficiary Name            : SURESH PATIL
Beneficiary Account Number  : XXXXXXXXXX8910
Beneficiary Bank & IFSC     : HDFC Bank (HDFC0000240)
Transfer Mode               : National Electronic Funds Transfer (NEFT)
Available Balance           : Rs. 1,42,850.25
--------------------------------------------------

If you did not authorize this transaction, please immediately:
1. Block your Internet Banking profile by sending SMS 'BLOCK <Account No>' to=
 567676.
2. Dial our 24x7 toll-free helpline numbers: 1800-11-2211 / 1800-425-3800.
3. Lock your Debit Card instantly via the YONO SBI App.

Always ensure the URL in your browser address bar is strictly: https://www.on=
linesbi.sbi

--
Yours faithfully,
Chief General Manager (Digital Banking)
State Bank of India
Corporate Centre: State Bank Bhavan, Madame Cama Road, Nariman Point, Mumbai =
- 400021
Customer Care Toll-Free: 1800 1234 / 1800 2100 | Email: customercare@sbi.co.in

State Bank of India - The Banker to Every Indian

--===============5536454062743114745==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"https://www.onlinesbi.sbi/sbijava/images/sbi_logo.png" alt=3D"S=
BI Official Blue Keyhole Emblem" style=3D"max-height: 48px; margin-right: 12p=
x; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear Customer,</p>
<p style=3D"margin: 0 0 12px 0;">Your State Bank of India Account XXXXXXXX401=
2 has been debited by Rs. 25,000.00 on 16-Oct-2026 14:21:42 IST towards an ou=
tward NEFT transfer.</p>
<p style=3D"margin: 0 0 12px 0;">TRANSACTION DETAILS:<br/>-------------------=
-------------------------------<br/>Transaction Reference (UTR) : SBIN3262891=
04821<br/>Beneficiary Name            : SURESH PATIL<br/>Beneficiary Account =
Number  : XXXXXXXXXX8910<br/>Beneficiary Bank &amp; IFSC     : HDFC Bank (HDF=
C0000240)<br/>Transfer Mode               : National Electronic Funds Transfe=
r (NEFT)<br/>Available Balance           : Rs. 1,42,850.25<br/>--------------=
------------------------------------</p>
<p style=3D"margin: 0 0 12px 0;">If you did not authorize this transaction, p=
lease immediately:<br/>1. Block your Internet Banking profile by sending SMS =
&#x27;BLOCK &lt;Account No&gt;&#x27; to 567676.<br/>2. Dial our 24x7 toll-fre=
e helpline numbers: 1800-11-2211 / 1800-425-3800.<br/>3. Lock your Debit Card=
 instantly via the YONO SBI App.</p>
<p style=3D"margin: 0 0 12px 0;">Always ensure the URL in your browser addres=
s bar is strictly: <a href=3D"https://www.onlinesbi.sbi" style=3D"color: #006=
6cc; text-decoration: underline;">SBI Official NetBanking (onlinesbi.sbi)</a>=
</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Yours faithfully,<br/>Chief Gene=
ral Manager (Digital Banking)<br/>State Bank of India<br/>Corporate Centre: S=
tate Bank Bhavan, Madame Cama Road, Nariman Point, Mumbai - 400021<br/>Custom=
er Care Toll-Free: 1800 1234 / 1800 2100 | Email: customercare@sbi.co.in<br/>=
<br/>State Bank of India - The Banker to Every Indian</div>
</body>
</html>

--===============5536454062743114745==--
```

---

### 3.eml (EMAIL_003): LIC Policy Premium Due Notice - Policy No. 842109482 (Plan: Jeevan Labh)
- **Ground Truth**: `✅ HAM (Legitimate)`
- **Claimed Organization**: `Life Insurance Corporation of India (LIC)` (Insurance)
- **Raw File**: `data/raw_emails/3.eml`

```email
From: LIC Portal Customer Services <customer.service@licindia.in>
To: vikram.malhotra@yahoo.com
Cc: branch.882@licindia.in
Subject:
 LIC Policy Premium Due Notice - Policy No. 842109482 (Plan: Jeevan Labh)
Date: Wed, 02 Sep 2026 09:00:12 +0530
Reply-To: customer.service@licindia.in
Authentication-Results: mx.google.com; spf=pass (mail.server designates
 permitted sender) smtp.mailfrom=LIC Portal Customer Services
 <customer.service@licindia.in>; dkim=pass; dmarc=pass
Received-SPF: pass (sender IP: 121.241.242.70 is authorized by licindia.in)
Message-ID: <3.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============3551686097413338145=="

--===============3551686097413338145==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear Policyholder VIKRAM MALHOTRA,

Greetings from Life Insurance Corporation of India.

This is to inform you that the renewal premium for your LIC Life Insurance Po=
licy is due for payment.

POLICY PARTICULARS:
--------------------------------------------------
Policy Number       : 842109482
Plan & Term         : Jeevan Labh (Table 936, Term 16/10)
Sum Assured         : Rs. 10,00,000.00
Premium Installment : Rs. 28,450.00 (including applicable GST)
Due Date of Premium : 20-Sep-2026
Grace Period Expiry : 20-Oct-2026
Servicing Branch    : Branch 882, Fort, Mumbai
--------------------------------------------------

CONVENIENT ONLINE PAYMENT MODES:
1. Pay directly without registration: https://licindia.in/Home/Pay-Premium-On=
line
2. Pay via LIC Customer Portal App (Android / iOS): https://customer.onlineli=
c.in
3. Authorized digital billers: NACH Mandate, UPI, NetBanking, BBPS, or Author=
ized Bank Counters.

IMPORTANT SAFETY NOTICE:
LIC never asks policyholders to transfer funds into any individual's personal=
 savings account or personal UPI VPA handle. Never surrender your policy base=
d on false promises of high bonus returns or lottery payouts from callers cla=
iming to represent IRDAI or LIC.

--
Yours sincerely,
Divisional Manager (Customer Relationship Management)
Life Insurance Corporation of India
Divisional Office: Yogakshema Building, West Wing, J.B. Marg, Mumbai - 400021
LIC Call Centre 24x7: 022-68276827 | IRDAI Reg No: 512

LIC of India - Har Pal Aapke Saath

--===============3551686097413338145==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"https://licindia.in/o/lic-theme/images/lic_logo.png" alt=3D"LIC=
 Hands with Flame Emblem (Yogakshemam Vahamyaham)" style=3D"max-height: 48px;=
 margin-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear Policyholder VIKRAM MALHOTRA,</p>
<p style=3D"margin: 0 0 12px 0;">Greetings from Life Insurance Corporation of=
 India.</p>
<p style=3D"margin: 0 0 12px 0;">This is to inform you that the renewal premi=
um for your LIC Life Insurance Policy is due for payment.</p>
<p style=3D"margin: 0 0 12px 0;">POLICY PARTICULARS:<br/>--------------------=
------------------------------<br/>Policy Number       : 842109482<br/>Plan &=
amp; Term         : Jeevan Labh (Table 936, Term 16/10)<br/>Sum Assured      =
   : Rs. 10,00,000.00<br/>Premium Installment : Rs. 28,450.00 (including appl=
icable GST)<br/>Due Date of Premium : 20-Sep-2026<br/>Grace Period Expiry : 2=
0-Oct-2026<br/>Servicing Branch    : Branch 882, Fort, Mumbai<br/>-----------=
---------------------------------------</p>
<p style=3D"margin: 0 0 12px 0;">CONVENIENT ONLINE PAYMENT MODES:<br/>1. Pay =
directly without registration: <a href=3D"https://licindia.in/Home/Pay-Premiu=
m-Online" style=3D"color: #0066cc; text-decoration: underline;">LIC Official =
Direct Pay Portal</a><br/>2. Pay via LIC Customer Portal App (Android / iOS):=
 <a href=3D"https://customer.onlinelic.in" style=3D"color: #0066cc; text-deco=
ration: underline;">LIC Customer Portal Login</a><br/>3. Authorized digital b=
illers: NACH Mandate, UPI, NetBanking, BBPS, or Authorized Bank Counters.</p>
<p style=3D"margin: 0 0 12px 0;">IMPORTANT SAFETY NOTICE:<br/>LIC never asks =
policyholders to transfer funds into any individual&#x27;s personal savings a=
ccount or personal UPI VPA handle. Never surrender your policy based on false=
 promises of high bonus returns or lottery payouts from callers claiming to r=
epresent IRDAI or LIC.</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Yours sincerely,<br/>Divisional =
Manager (Customer Relationship Management)<br/>Life Insurance Corporation of =
India<br/>Divisional Office: Yogakshema Building, West Wing, J.B. Marg, Mumba=
i - 400021<br/>LIC Call Centre 24x7: 022-68276827 | IRDAI Reg No: 512<br/><br=
/>LIC of India - Har Pal Aapke Saath</div>
</body>
</html>

--===============3551686097413338145==--
```

---

### 4.eml (EMAIL_004): Intimation Order u/s 143(1) of the Income-tax Act, 1961 for PAN: AXXXX1234X - AY 2024-25
- **Ground Truth**: `✅ HAM (Legitimate)`
- **Claimed Organization**: `Income Tax Department, Ministry of Finance, Govt of India` (Income Tax)
- **Raw File**: `data/raw_emails/4.eml`

```email
From: Income Tax Department CPC Bengaluru <donotreply@incometax.gov.in>
To: sunita.verma@gmail.com
Subject: Intimation Order u/s 143(1) of the Income-tax Act, 1961 for PAN:
 AXXXX1234X - AY 2024-25
Date: Sat, 22 Aug 2026 11:45:00 +0530
Reply-To: None
Authentication-Results: mx.google.com; spf=pass (mail.server designates
 permitted sender) smtp.mailfrom=Income Tax Department CPC Bengaluru
 <donotreply@incometax.gov.in>; dkim=pass; dmarc=pass
Received-SPF:
 pass (sender IP: 164.100.14.92 is authorized by incometax.gov.in)
Message-ID: <4.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============7802998808374479939=="

--===============7802998808374479939==
Content-Type: multipart/alternative;
 boundary="===============4715072640483701190=="

--===============4715072640483701190==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear SUNITA VERMA,

PAN: AXXXX1234X
Assessment Year: 2024-25
Acknowledgement Number: 829104820194821
Communication Ref No: CPC/2425/A2/829104820194821

The Centralized Processing Centre (CPC), Bengaluru has processed your electro=
nically filed Income Tax Return for Assessment Year 2024-25 under section 143=
(1) of the Income-tax Act, 1961.

SUMMARY OF COMPUTATION:
--------------------------------------------------
Total Tax & Interest Payable as per Return : Rs. 0
Total Tax & Interest Determined by CPC     : Rs. 0
Net Refund Determined (Including 244A Int) : Rs. 14,280.00
Refund Disbursement Channel                : Direct Credit via NECS/RTGS
Designated Pre-Validated Bank Account      : State Bank of India (A/C ending =
5821)
--------------------------------------------------

The detailed computation sheet is enclosed in the attached password-protected=
 PDF document.
Password Format: Your 10-digit PAN in lowercase followed by your Date of Birt=
h in DDMMYYYY format.
Example: If PAN is ABCDE1234F and DOB is 01-Jan-1985, password is: abcde1234f=
01011985.

You can inspect all processed returns and refund statuses by logging in to th=
e e-Filing portal:
https://www.incometax.gov.in/iec/foportal/

STATUTORY CAUTION:
The Income Tax Department NEVER asks taxpayers for their bank account passwor=
ds, debit/credit card PINs, or OTPs. All official communications carry a uniq=
ue Document Identification Number (DIN) verifiable on the e-Filing portal.

--
Deputy Commissioner of Income Tax
Centralized Processing Centre (CPC)
Income Tax Department, Post Bag No. 1, Electronic City Post Office, Bengaluru=
 - 560100, Karnataka
e-Filing Helpdesk Toll-Free: 1800 103 0025 / 1800 419 0025

Government of India - Ministry of Finance - Central Board of Direct Taxes (CB=
DT)

--===============4715072640483701190==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"https://www.incometax.gov.in/iec/foportal/sites/default/files/e=
mblem-dark.png" alt=3D"Ashoka Lion Capital National Emblem of India" style=3D=
"max-height: 48px; margin-right: 12px; vertical-align: middle;" />
  <img src=3D"https://www.incometax.gov.in/iec/foportal/sites/default/files/i=
td-logo.png" alt=3D"Income Tax Department Official Crest" style=3D"max-height=
: 48px; margin-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear SUNITA VERMA,</p>
<p style=3D"margin: 0 0 12px 0;">PAN: AXXXX1234X<br/>Assessment Year: 2024-25=
<br/>Acknowledgement Number: 829104820194821<br/>Communication Ref No: CPC/24=
25/A2/829104820194821</p>
<p style=3D"margin: 0 0 12px 0;">The Centralized Processing Centre (CPC), Ben=
galuru has processed your electronically filed Income Tax Return for Assessme=
nt Year 2024-25 under section 143(1) of the Income-tax Act, 1961.</p>
<p style=3D"margin: 0 0 12px 0;">SUMMARY OF COMPUTATION:<br/>----------------=
----------------------------------<br/>Total Tax &amp; Interest Payable as pe=
r Return : Rs. 0<br/>Total Tax &amp; Interest Determined by CPC     : Rs. 0<b=
r/>Net Refund Determined (Including 244A Int) : Rs. 14,280.00<br/>Refund Disb=
ursement Channel                : Direct Credit via NECS/RTGS<br/>Designated =
Pre-Validated Bank Account      : State Bank of India (A/C ending 5821)<br/>-=
-------------------------------------------------</p>
<p style=3D"margin: 0 0 12px 0;">The detailed computation sheet is enclosed i=
n the attached password-protected PDF document.<br/>Password Format: Your 10-=
digit PAN in lowercase followed by your Date of Birth in DDMMYYYY format.<br/=
>Example: If PAN is ABCDE1234F and DOB is 01-Jan-1985, password is: abcde1234=
f01011985.</p>
<p style=3D"margin: 0 0 12px 0;">You can inspect all processed returns and re=
fund statuses by logging in to the e-Filing portal:<br/><a href=3D"https://ww=
w.incometax.gov.in/iec/foportal/" style=3D"color: #0066cc; text-decoration: u=
nderline;">Official e-Filing Portal (incometax.gov.in)</a></p>
<p style=3D"margin: 0 0 12px 0;">STATUTORY CAUTION:<br/>The Income Tax Depart=
ment NEVER asks taxpayers for their bank account passwords, debit/credit card=
 PINs, or OTPs. All official communications carry a unique Document Identific=
ation Number (DIN) verifiable on the e-Filing portal.</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Deputy Commissioner of Income Ta=
x<br/>Centralized Processing Centre (CPC)<br/>Income Tax Department, Post Bag=
 No. 1, Electronic City Post Office, Bengaluru - 560100, Karnataka<br/>e-Fili=
ng Helpdesk Toll-Free: 1800 103 0025 / 1800 419 0025<br/><br/>Government of I=
ndia - Ministry of Finance - Central Board of Direct Taxes (CBDT)</div>
</body>
</html>

--===============4715072640483701190==--

--===============7802998808374479939==
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="PAN_AXXXX1234X_AY2024-25_143_1.pdf"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIFBBTl9BWFhYWDEyMzRYX0FZMjAyNC0yNV8xNDNfMS5wZGYK
R2VuZXJhdGVkIGZvciBTY2FtTGVucy1BSSBQb0Mu

--===============7802998808374479939==--
```

---

### 5.eml (EMAIL_005): Speed Post Consignment Dispatched: Article No. EK829104821IN (From: NSDL e-Governance)
- **Ground Truth**: `✅ HAM (Legitimate)`
- **Claimed Organization**: `Department of Posts, Ministry of Communications, Govt of India` (Customs & Postal Services)
- **Raw File**: `data/raw_emails/5.eml`

```email
From: Department of Posts India <tracking@indiapost.gov.in>
To: dev.kapoor@gmail.com
Subject: Speed Post Consignment Dispatched: Article No. EK829104821IN (From:
 NSDL e-Governance)
Date: Sun, 11 Oct 2026 16:10:45 +0530
Reply-To: None
Authentication-Results: mx.google.com; spf=pass (mail.server designates
 permitted sender) smtp.mailfrom=Department of Posts India
 <tracking@indiapost.gov.in>; dkim=pass; dmarc=pass
Received-SPF:
 pass (sender IP: 164.100.89.44 is authorized by indiapost.gov.in)
Message-ID: <5.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============0637880857807762677=="

--===============0637880857807762677==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear Customer,

Your Speed Post article with Tracking Number EK829104821IN has been booked at=
 New Delhi GPO on 11-Oct-2026 15:45:10 IST and dispatched to Mumbai National =
Sorting Hub (NSH).

CONSIGNMENT INFORMATION:
--------------------------------------------------
Article Tracking Number : EK829104821IN
Sender Details          : National Securities Depository Limited (NSDL)
Destination City & Pin  : Mumbai - 400050
Service Classification  : Domestic Speed Post
Booked At               : New Delhi GPO (110001)
Estimated Delivery Date : 14-Oct-2026
--------------------------------------------------

Track live transit events and delivery status on the official Department of P=
osts portal:
https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment=
.aspx

CUSTOMER ADVISORY:
India Post delivery personnel collect payments ONLY for articles marked as Ca=
sh on Delivery (CoD). India Post never sends SMS or email messages requesting=
 payment of nominal redelivery charges (e.g., Rs. 5 or Rs. 25) through shorte=
ned third-party web links. Do not click on unverified links.

--
Postal Operations Directorate
Department of Posts, Ministry of Communications
Dak Bhawan, Sansad Marg, New Delhi - 110001, India
Toll-Free Customer Grievance Helpline: 1800 266 6868 | Email: customer.care@i=
ndiapost.gov.in

India Post - Delivering Trust Across Every Village and Town

--===============0637880857807762677==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"https://www.indiapost.gov.in/_layouts/15/images/DOP.Portal.UILi=
brary/India_Post_Logo_with_Text.svg" alt=3D"India Post Iconic Red Wing Logo" =
style=3D"max-height: 48px; margin-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear Customer,</p>
<p style=3D"margin: 0 0 12px 0;">Your Speed Post article with Tracking Number=
 EK829104821IN has been booked at New Delhi GPO on 11-Oct-2026 15:45:10 IST a=
nd dispatched to Mumbai National Sorting Hub (NSH).</p>
<p style=3D"margin: 0 0 12px 0;">CONSIGNMENT INFORMATION:<br/>---------------=
-----------------------------------<br/>Article Tracking Number : EK829104821=
IN<br/>Sender Details          : National Securities Depository Limited (NSDL=
)<br/>Destination City &amp; Pin  : Mumbai - 400050<br/>Service Classificatio=
n  : Domestic Speed Post<br/>Booked At               : New Delhi GPO (110001)=
<br/>Estimated Delivery Date : 14-Oct-2026<br/>------------------------------=
--------------------</p>
<p style=3D"margin: 0 0 12px 0;">Track live transit events and delivery statu=
s on the official Department of Posts portal:<br/><a href=3D"https://www.indi=
apost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx" style=3D"=
color: #0066cc; text-decoration: underline;">Official India Post Consignment =
Tracking Portal</a></p>
<p style=3D"margin: 0 0 12px 0;">CUSTOMER ADVISORY:<br/>India Post delivery p=
ersonnel collect payments ONLY for articles marked as Cash on Delivery (CoD).=
 India Post never sends SMS or email messages requesting payment of nominal r=
edelivery charges (e.g., Rs. 5 or Rs. 25) through shortened third-party web l=
inks. Do not click on unverified links.</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Postal Operations Directorate<br=
/>Department of Posts, Ministry of Communications<br/>Dak Bhawan, Sansad Marg=
, New Delhi - 110001, India<br/>Toll-Free Customer Grievance Helpline: 1800 2=
66 6868 | Email: customer.care@indiapost.gov.in<br/><br/>India Post - Deliver=
ing Trust Across Every Village and Town</div>
</body>
</html>

--===============0637880857807762677==--
```

---

### 6.eml (EMAIL_006): CRITICAL NOTICE: Your SBI YONO Account is Suspended - Immediate KYC Update Required
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `State Bank of India (Spoofed)` (Banking)
- **Raw File**: `data/raw_emails/6.eml`

```email
From: State Bank of India Online Alerts <no-reply@sbi-kyc-verify.xyz>
To: target.victim@gmail.com
Subject: CRITICAL NOTICE: Your SBI YONO Account is Suspended - Immediate KYC
 Update Required
Date: Wed, 18 Nov 2026 10:14:22 +0530
Reply-To: support-ticket-842@fraud-mailbox.xyz
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=State Bank of India Online Alerts
 <no-reply@sbi-kyc-verify.xyz>; dkim=fail; dmarc=fail
Received-SPF:
 softfail (sender IP: 194.38.20.14 is NOT authorized by sbi.co.in)
Message-ID: <6.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============2552825096803577796=="

--===============2552825096803577796==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear SBI Customer,

Your State Bank of India YONO Internet Banking profile has been TEMPORARILY S=
USPENDED due to non-submission of updated Aadhaar card and PAN card biometric=
s as mandated under RBI Circular RBI/2026-27/89.

IMPACT OF NON-COMPLIANCE:
- All ATM Debit Card cash withdrawals will be blocked tonight at 23:59 IST.
- Inward NEFT/IMPS and UPI transactions on GPay/PhonePe will be declined.
- A penalty surcharge of Rs. 10,000 will be debited from your savings balance.

MANDATORY ACTION:
You must update your KYC details immediately on our secure compliance server:
http://sbi-kyc-verify.xyz/login.php?user=3Dverify

INSTRUCTIONS:
1. Access the link above on your smartphone or PC.
2. Enter your YONO Username, Password, and Profile Password.
3. Submit the 6-digit verification OTP received on your mobile phone to compl=
ete synchronization.

Do not ignore this notice. Customer security is our priority.

Sincerely,
SBI Customer Support Unit
State Bank of India, Corporate Centre, Mumbai

--
State Bank of India Online Security Operations
Email: support@sbi-kyc-verify.xyz (Spoofed)
Helpline WhatsApp: +91 9876543210 (Fraudulent)
Address: State Bank Bhavan, Nariman Point, Mumbai - 400021

Note: This automated alert was generated by the SBI Core Banking System. Fail=
ure to verify credentials within 24 hours will result in permanent closure of=
 account services.

--===============2552825096803577796==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://sbi-kyc-verify.xyz/assets/sbi_yono_banner.png" alt=3D"Sp=
oofed SBI YONO Logo Banner" style=3D"max-height: 48px; margin-right: 12px; ve=
rtical-align: middle;" />
  <img src=3D"http://sbi-kyc-verify.xyz/assets/rbi_verified_badge.png" alt=3D=
"Fake RBI Compliance Seal" style=3D"max-height: 48px; margin-right: 12px; ver=
tical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear SBI Customer,</p>
<p style=3D"margin: 0 0 12px 0;">Your State Bank of India YONO Internet Banki=
ng profile has been TEMPORARILY SUSPENDED due to non-submission of updated Aa=
dhaar card and PAN card biometrics as mandated under RBI Circular RBI/2026-27=
/89.</p>
<p style=3D"margin: 0 0 12px 0;">IMPACT OF NON-COMPLIANCE:<br/>- All ATM Debi=
t Card cash withdrawals will be blocked tonight at 23:59 IST.<br/>- Inward NE=
FT/IMPS and UPI transactions on GPay/PhonePe will be declined.<br/>- A penalt=
y surcharge of Rs. 10,000 will be debited from your savings balance.</p>
<p style=3D"margin: 0 0 12px 0;">MANDATORY ACTION:<br/>You must update your K=
YC details immediately on our secure compliance server:<br/><a href=3D"http:/=
/sbi-kyc-verify.xyz/login.php?user=3Dverify" style=3D"color: #0066cc; text-de=
coration: underline;">Update KYC &amp; Restore YONO Access Now</a></p>
<p style=3D"margin: 0 0 12px 0;">INSTRUCTIONS:<br/>1. Access the link above o=
n your smartphone or PC.<br/>2. Enter your YONO Username, Password, and Profi=
le Password.<br/>3. Submit the 6-digit verification OTP received on your mobi=
le phone to complete synchronization.</p>
<p style=3D"margin: 0 0 12px 0;">Do not ignore this notice. Customer security=
 is our priority.</p>
<p style=3D"margin: 0 0 12px 0;">Sincerely,<br/>SBI Customer Support Unit<br/=
>State Bank of India, Corporate Centre, Mumbai</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">State Bank of India Online Secur=
ity Operations<br/>Email: support@sbi-kyc-verify.xyz (Spoofed)<br/>Helpline W=
hatsApp: +91 9876543210 (Fraudulent)<br/>Address: State Bank Bhavan, Nariman =
Point, Mumbai - 400021<br/><br/>Note: This automated alert was generated by t=
he SBI Core Banking System. Failure to verify credentials within 24 hours wil=
l result in permanent closure of account services.</div>
</body>
</html>

--===============2552825096803577796==--
```

---

### 7.eml (EMAIL_007): Notice: 18,450 ICICI Payback Points Expiring Tonight - Claim Cash Value Rs 9,225 Directly
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `ICICI Bank (Spoofed)` (Banking)
- **Raw File**: `data/raw_emails/7.eml`

```email
From: ICICI Rewards Desk <rewards@icici-point-claim.top>
To: rohit.sharma@yahoo.co.in
Cc: claims-archive@icici-point-claim.top
Subject: Notice: 18,450 ICICI Payback Points Expiring Tonight - Claim Cash
 Value Rs 9,225 Directly
Date: Tue, 03 Nov 2026 18:30:10 +0530
Reply-To: claims@icici-point-claim.top
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=ICICI Rewards Desk
 <rewards@icici-point-claim.top>; dkim=fail; dmarc=fail
Received-SPF: fail (sender IP: 45.145.89.112 not authorized by icicibank.com)
Message-ID: <7.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============0734192051946354655=="

--===============0734192051946354655==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear ICICI Bank Cardholder,

Our records indicate that you have 18,450 UNCLAIMED ICICI Bank Payback Reward=
 Points accumulated on your Debit/Credit Card.

These reward points carry a redeemable cash balance of Rs. 9,225.00.

IMPORTANT EXPIRATION WARNING:
As per the revised end-of-year rewards policy, all points earned prior to 202=
6 are scheduled to EXPIRE TONIGHT AT 11:59 PM. Expired points will be forfeit=
ed to the bank pool.

HOW TO CONVERT YOUR REWARD POINTS TO LIQUID CASH:
Click on the direct credit redemption portal below:
http://icici-point-claim.top/redeem_cash.html

3 SIMPLE STEPS TO CREDIT:
1. Open the redemption link above.
2. Enter your 16-digit Card Number, Expiry Date (MM/YY), and 3-digit CVV code.
3. Enter your NetBanking password and submit the verification OTP received on=
 SMS.

The amount of Rs. 9,225.00 will be credited directly to your primary savings =
account within 10 minutes.

Regards,
ICICI Bank Customer Rewards Division
Bandra Kurla Complex, Mumbai

--
Customer Loyalty & Rewards Wing
ICICI Bank Towers, Bandra-Kurla Complex, Mumbai - 400051
Toll-Free Customer Line: 1800-POINT-ICICI (Fake)
Website: http://icici-point-claim.top (Malicious)

CONFIDENTIALITY NOTICE: This email is confidential and contains proprietary r=
eward entitlement data. If you are not the intended cardholder, immediately d=
elete this communication.

--===============0734192051946354655==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://icici-point-claim.top/images/icici_logo_orange.png" alt=
=3D"Spoofed ICICI Bank Orange Logo" style=3D"max-height: 48px; margin-right: =
12px; vertical-align: middle;" />
  <img src=3D"http://icici-point-claim.top/images/guarantee_seal.png" alt=3D"=
Fake 100% Cash Redemption Guarantee Stamp" style=3D"max-height: 48px; margin-=
right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear ICICI Bank Cardholder,</p>
<p style=3D"margin: 0 0 12px 0;">Our records indicate that you have 18,450 UN=
CLAIMED ICICI Bank Payback Reward Points accumulated on your Debit/Credit Car=
d.</p>
<p style=3D"margin: 0 0 12px 0;">These reward points carry a redeemable cash =
balance of Rs. 9,225.00.</p>
<p style=3D"margin: 0 0 12px 0;">IMPORTANT EXPIRATION WARNING:<br/>As per the=
 revised end-of-year rewards policy, all points earned prior to 2026 are sche=
duled to EXPIRE TONIGHT AT 11:59 PM. Expired points will be forfeited to the =
bank pool.</p>
<p style=3D"margin: 0 0 12px 0;">HOW TO CONVERT YOUR REWARD POINTS TO LIQUID =
CASH:<br/>Click on the direct credit redemption portal below:<br/><a href=3D"=
http://icici-point-claim.top/redeem_cash.html" style=3D"color: #0066cc; text-=
decoration: underline;">Redeem Rs 9,225 Cash to Account Now</a></p>
<p style=3D"margin: 0 0 12px 0;">3 SIMPLE STEPS TO CREDIT:<br/>1. Open the re=
demption link above.<br/>2. Enter your 16-digit Card Number, Expiry Date (MM/=
YY), and 3-digit CVV code.<br/>3. Enter your NetBanking password and submit t=
he verification OTP received on SMS.</p>
<p style=3D"margin: 0 0 12px 0;">The amount of Rs. 9,225.00 will be credited =
directly to your primary savings account within 10 minutes.</p>
<p style=3D"margin: 0 0 12px 0;">Regards,<br/>ICICI Bank Customer Rewards Div=
ision<br/>Bandra Kurla Complex, Mumbai</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Customer Loyalty &amp; Rewards W=
ing<br/>ICICI Bank Towers, Bandra-Kurla Complex, Mumbai - 400051<br/>Toll-Fre=
e Customer Line: 1800-POINT-ICICI (Fake)<br/>Website: http://icici-point-clai=
m.top (Malicious)<br/><br/>CONFIDENTIALITY NOTICE: This email is confidential=
 and contains proprietary reward entitlement data. If you are not the intende=
d cardholder, immediately delete this communication.</div>
</body>
</html>

--===============0734192051946354655==--
```

---

### 8.eml (EMAIL_008): Final Reminder: Immediate PAN Linking Required for HDFC Bank Account - Debit Freeze Alert
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `HDFC Bank (Spoofed)` (Banking)
- **Raw File**: `data/raw_emails/8.eml`

```email
From: HDFC Bank Compliance Unit <alert@hdfc-pan-update.online>
To: priya.nair@hotmail.com
Subject: Final Reminder: Immediate PAN Linking Required for HDFC Bank Account
 - Debit Freeze Alert
Date: Thu, 29 Oct 2026 12:05:44 +0530
Reply-To: support@hdfc-pan-update.online
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=HDFC Bank Compliance Unit
 <alert@hdfc-pan-update.online>; dkim=fail; dmarc=fail
Received-SPF: fail (domain hdfc-pan-update.online has no SPF record)
Message-ID: <8.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============3199586380311985939=="

--===============3199586380311985939==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear Valued Customer,

This is a mandatory compliance alert from HDFC Bank Risk & Vigilance Departme=
nt regarding Section 139AA of the Income Tax Act.

Your savings account ending with 1984 has been marked as NON-COMPLIANT due to=
 pending PAN-Aadhaar linking validation on our centralized CBS servers.

CONSEQUENCES OF NON-LINKING STARTING TODAY AT 23:59 IST:
1. Immediate debit freeze on all netbanking, mobile banking, and branch cash =
withdrawals.
2. Inward NEFT/IMPS and salary credits will be returned to sender.
3. Deduction of a mandatory non-compliance statutory fee of Rs. 2,500 monthly.

Complete your instant biometric linking online without visiting the branch:
http://hdfc-pan-update.online/auth/login

Please keep your Customer ID, NetBanking IPIN, and registered phone number ac=
cessible to authorize the instant linkage.

HDFC Bank Risk & Compliance Department
Lower Parel, Mumbai

--
HDFC Bank Vigilance & Compliance Operations
HDFC Bank House, Senapati Bapat Marg, Lower Parel, Mumbai - 400013
Grievance Officer: compliance@hdfc-pan-update.online (Fraudulent)
Customer Safety Line: +91 9123456789 (Fraudulent)

Notice: HDFC Bank will not be responsible for operational losses or penalty c=
harges resulting from failure to update PAN credentials within the deadline.

--===============3199586380311985939==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://hdfc-pan-update.online/static/hdfc_header.jpg" alt=3D"Sp=
oofed HDFC Bank Header" style=3D"max-height: 48px; margin-right: 12px; vertic=
al-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear Valued Customer,</p>
<p style=3D"margin: 0 0 12px 0;">This is a mandatory compliance alert from HD=
FC Bank Risk &amp; Vigilance Department regarding Section 139AA of the Income=
 Tax Act.</p>
<p style=3D"margin: 0 0 12px 0;">Your savings account ending with 1984 has be=
en marked as NON-COMPLIANT due to pending PAN-Aadhaar linking validation on o=
ur centralized CBS servers.</p>
<p style=3D"margin: 0 0 12px 0;">CONSEQUENCES OF NON-LINKING STARTING TODAY A=
T 23:59 IST:<br/>1. Immediate debit freeze on all netbanking, mobile banking,=
 and branch cash withdrawals.<br/>2. Inward NEFT/IMPS and salary credits will=
 be returned to sender.<br/>3. Deduction of a mandatory non-compliance statut=
ory fee of Rs. 2,500 monthly.</p>
<p style=3D"margin: 0 0 12px 0;">Complete your instant biometric linking onli=
ne without visiting the branch:<br/><a href=3D"http://hdfc-pan-update.online/=
auth/login" style=3D"color: #0066cc; text-decoration: underline;">Link PAN wi=
th HDFC Account Online</a></p>
<p style=3D"margin: 0 0 12px 0;">Please keep your Customer ID, NetBanking IPI=
N, and registered phone number accessible to authorize the instant linkage.</=
p>
<p style=3D"margin: 0 0 12px 0;">HDFC Bank Risk &amp; Compliance Department<b=
r/>Lower Parel, Mumbai</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">HDFC Bank Vigilance &amp; Compli=
ance Operations<br/>HDFC Bank House, Senapati Bapat Marg, Lower Parel, Mumbai=
 - 400013<br/>Grievance Officer: compliance@hdfc-pan-update.online (Fraudulen=
t)<br/>Customer Safety Line: +91 9123456789 (Fraudulent)<br/><br/>Notice: HDF=
C Bank will not be responsible for operational losses or penalty charges resu=
lting from failure to update PAN credentials within the deadline.</div>
</body>
</html>

--===============3199586380311985939==--
```

---

### 9.eml (EMAIL_009): Congratulations: Your Axis Credit Card limit has been increased to Rs 8,50,000 (Action Required)
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Axis Bank (Spoofed)` (Banking)
- **Raw File**: `data/raw_emails/9.eml`

```email
From: Axis Bank Pre-Approved Cards <offers@axis-limit-boost.click>
To: kunal.sen@gmail.com
Subject: Congratulations: Your Axis Credit Card limit has been increased to Rs
 8,50,000 (Action Required)
Date: Sat, 17 Oct 2026 15:40:19 +0530
Reply-To: None
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=Axis Bank Pre-Approved Cards
 <offers@axis-limit-boost.click>; dkim=fail; dmarc=fail
Received-SPF: softfail (unauthorized sending IP: 185.220.101.5)
Message-ID: <9.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============8405710041096336305=="

--===============8405710041096336305==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear Axis Bank Cardholder,

Congratulations! In recognition of your excellent CIBIL credit score and flaw=
less repayment track record, Axis Bank is pleased to offer you an instant pre=
-approved credit limit enhancement:

OFFER DETAILS:
- Existing Credit Limit   : Rs. 1,50,000.00
- Enhanced Credit Limit   : Rs. 8,50,000.00
- Annual Fee Waiver       : 100% Lifetime Free (LTF)
- Complimentary Benefits  : Unlimited Airport Lounge Access & 5X Reward Points

This promotional limit upgrade is valid for activation only for the next 48 h=
ours.

ACTIVATE YOUR ENHANCED LIMIT NOW:
http://axis-limit-boost.click/upgrade

Please complete validation by entering:
1. 16-digit Axis Bank Credit Card Number
2. Expiry Date & 3-digit CVV
3. NetBanking Login Password
4. Dynamic Authentication OTP

Your enhanced limit will be available immediately upon verification.

Warm Regards,
Cards Division, Axis Bank Limited

--
Axis Bank Credit Card Enhancement Cell
Axis House, C-2, Wadia International Centre, Pandurang Budhkar Marg, Worli, M=
umbai - 400025
Helpdesk: support@axis-limit-boost.click (Fake) | Tel: 1800-419-5577 (Spoofed=
 text)

Disclaimer: This email contains pre-approved confidential customer financial =
offers. Unclaimed upgrades lapse automatically after 48 hours.

--===============8405710041096336305==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://axis-limit-boost.click/assets/axis_logo.png" alt=3D"Spoo=
fed Axis Bank Burgundy Logo" style=3D"max-height: 48px; margin-right: 12px; v=
ertical-align: middle;" />
  <img src=3D"http://axis-limit-boost.click/assets/gold_card_mockup.png" alt=
=3D"Pre-Approved Gold Credit Card Badge" style=3D"max-height: 48px; margin-ri=
ght: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear Axis Bank Cardholder,</p>
<p style=3D"margin: 0 0 12px 0;">Congratulations! In recognition of your exce=
llent CIBIL credit score and flawless repayment track record, Axis Bank is pl=
eased to offer you an instant pre-approved credit limit enhancement:</p>
<p style=3D"margin: 0 0 12px 0;">OFFER DETAILS:<br/>- Existing Credit Limit  =
 : Rs. 1,50,000.00<br/>- Enhanced Credit Limit   : Rs. 8,50,000.00<br/>- Annu=
al Fee Waiver       : 100% Lifetime Free (LTF)<br/>- Complimentary Benefits  =
: Unlimited Airport Lounge Access &amp; 5X Reward Points</p>
<p style=3D"margin: 0 0 12px 0;">This promotional limit upgrade is valid for =
activation only for the next 48 hours.</p>
<p style=3D"margin: 0 0 12px 0;">ACTIVATE YOUR ENHANCED LIMIT NOW:<br/><a hre=
f=3D"http://axis-limit-boost.click/upgrade" style=3D"color: #0066cc; text-dec=
oration: underline;">Activate New Credit Limit of Rs 8,50,000</a></p>
<p style=3D"margin: 0 0 12px 0;">Please complete validation by entering:<br/>=
1. 16-digit Axis Bank Credit Card Number<br/>2. Expiry Date &amp; 3-digit CVV=
<br/>3. NetBanking Login Password<br/>4. Dynamic Authentication OTP</p>
<p style=3D"margin: 0 0 12px 0;">Your enhanced limit will be available immedi=
ately upon verification.</p>
<p style=3D"margin: 0 0 12px 0;">Warm Regards,<br/>Cards Division, Axis Bank =
Limited</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Axis Bank Credit Card Enhancemen=
t Cell<br/>Axis House, C-2, Wadia International Centre, Pandurang Budhkar Mar=
g, Worli, Mumbai - 400025<br/>Helpdesk: support@axis-limit-boost.click (Fake)=
 | Tel: 1800-419-5577 (Spoofed text)<br/><br/>Disclaimer: This email contains=
 pre-approved confidential customer financial offers. Unclaimed upgrades laps=
e automatically after 48 hours.</div>
</body>
</html>

--===============8405710041096336305==--
```

---

### 10.eml (EMAIL_010): ALERT: Unauthorized transfer of Rs. 74,500 debited from your PNB A/C - Cancel Immediately
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Punjab National Bank (Spoofed)` (Banking)
- **Raw File**: `data/raw_emails/10.eml`

```email
From: PNB Anti-Fraud Cell <security@pnb-security-alert.live>
To: ajay.singh@gmail.com
Cc: disputes@pnb-security-alert.live
Subject: ALERT: Unauthorized transfer of Rs. 74,500 debited from your PNB A/C
 - Cancel Immediately
Date: Wed, 11 Nov 2026 21:18:03 +0530
Reply-To: fraud-desk@pnb-security-alert.live
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=PNB Anti-Fraud Cell
 <security@pnb-security-alert.live>; dkim=fail; dmarc=fail
Received-SPF: fail (sender IP 89.248.165.70 not authorized for pnbindia.in)
Message-ID: <10.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============4290663482219244046=="

--===============4290663482219244046==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

CRITICAL SECURITY ALERT - PUNJAB NATIONAL BANK

An online transfer of Rs. 74,500.00 was initiated from your PNB savings accou=
nt to an unknown cryptocurrency merchant VPA (CRYPTO-EXCHANGE-IN@okaxis) on 1=
1-Nov-2026 21:15:30 IST.

TRANSACTION SUMMARY:
Amount Debited : Rs. 74,500.00
Reference ID   : PNB94821048201
Status         : Pending Clearing

IF YOU DID NOT AUTHORIZE THIS TRANSACTION:
You must cancel this debit immediately before the transaction is finalized by=
 the settlement network.

CLICK HERE TO CANCEL AND RESTORE YOUR BALANCE:
http://pnb-security-alert.live/dispute_transaction.php

Note: Cancellation gateway remains open for only 10 minutes. You will be prom=
pted to enter your NetBanking username, password, and transaction authorizati=
on OTP to reverse the charges to your balance.

If you authorized this transfer, no further action is required.

PNB Fraud Risk Management Cell
Dwarka, New Delhi

--
Punjab National Bank - Fraud Risk Management Operations
Head Office: Plot No 4, Sector 10, Dwarka, New Delhi - 110075
Emergency Hotline: 1800-180-2222 (Spoofed text) | Portal: http://pnb-security=
-alert.live (Malicious)

This is an automated emergency security alert. Punjab National Bank will not =
be liable for delayed disputes after the 10-minute clearing window.

--===============4290663482219244046==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://pnb-security-alert.live/pnb_logo.png" alt=3D"Spoofed PNB=
 Maroon Emblem" style=3D"max-height: 48px; margin-right: 12px; vertical-align=
: middle;" />
  <img src=3D"http://pnb-security-alert.live/warning_icon.gif" alt=3D"Urgent =
Red Security Warning Icon" style=3D"max-height: 48px; margin-right: 12px; ver=
tical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">CRITICAL SECURITY ALERT - PUNJAB NATIONAL BA=
NK</p>
<p style=3D"margin: 0 0 12px 0;">An online transfer of Rs. 74,500.00 was init=
iated from your PNB savings account to an unknown cryptocurrency merchant VPA=
 (CRYPTO-EXCHANGE-IN@okaxis) on 11-Nov-2026 21:15:30 IST.</p>
<p style=3D"margin: 0 0 12px 0;">TRANSACTION SUMMARY:<br/>Amount Debited : Rs=
. 74,500.00<br/>Reference ID   : PNB94821048201<br/>Status         : Pending =
Clearing</p>
<p style=3D"margin: 0 0 12px 0;">IF YOU DID NOT AUTHORIZE THIS TRANSACTION:<b=
r/>You must cancel this debit immediately before the transaction is finalized=
 by the settlement network.</p>
<p style=3D"margin: 0 0 12px 0;">CLICK HERE TO CANCEL AND RESTORE YOUR BALANC=
E:<br/><a href=3D"http://pnb-security-alert.live/dispute_transaction.php" sty=
le=3D"color: #0066cc; text-decoration: underline;">CANCEL TRANSACTION &amp; R=
EVERSE DEBIT (Within 10 Mins)</a></p>
<p style=3D"margin: 0 0 12px 0;">Note: Cancellation gateway remains open for =
only 10 minutes. You will be prompted to enter your NetBanking username, pass=
word, and transaction authorization OTP to reverse the charges to your balanc=
e.</p>
<p style=3D"margin: 0 0 12px 0;">If you authorized this transfer, no further =
action is required.</p>
<p style=3D"margin: 0 0 12px 0;">PNB Fraud Risk Management Cell<br/>Dwarka, N=
ew Delhi</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Punjab National Bank - Fraud Ris=
k Management Operations<br/>Head Office: Plot No 4, Sector 10, Dwarka, New De=
lhi - 110075<br/>Emergency Hotline: 1800-180-2222 (Spoofed text) | Portal: ht=
tp://pnb-security-alert.live (Malicious)<br/><br/>This is an automated emerge=
ncy security alert. Punjab National Bank will not be liable for delayed dispu=
tes after the 10-minute clearing window.</div>
</body>
</html>

--===============4290663482219244046==--
```

---

### 11.eml (EMAIL_011): Approval of Accumulated Lapsed Policy Bonus: Rs. 4,85,000 (Mandatory Action Required)
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Life Insurance Corporation of India (Spoofed)` (Insurance)
- **Raw File**: `data/raw_emails/11.eml`

```email
From: LIC Claims Settlement Officer <claims@lic-bonus-settlement.xyz>
To: ramesh.babu@gmail.com
Subject: Approval of Accumulated Lapsed Policy Bonus: Rs. 4,85,000 (Mandatory
 Action Required)
Date: Fri, 06 Nov 2026 11:12:40 +0530
Reply-To: licofficer.sharma98@gmail.com
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=LIC Claims Settlement Officer
 <claims@lic-bonus-settlement.xyz>; dkim=fail; dmarc=fail
Received-SPF: fail (unauthorized sender IP)
Message-ID: <11.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============8318931728359201608=="

--===============8318931728359201608==
Content-Type: multipart/alternative;
 boundary="===============8528143545415904897=="

--===============8528143545415904897==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear Policyholder RAMESH BABU,

We are pleased to inform you that your dormant LIC policy records have been s=
uccessfully audited under the Special IRDAI Unclaimed Fund Settlement Scheme =
2026.

An accumulated bonus along with maturity interest amounting to Rs. 4,85,000.0=
0 has been sanctioned for direct disbursement to your bank account.

DISBURSEMENT BREAKDOWN:
- Accumulated Loyalty Additions : Rs. 3,10,000.00
- Compound Guaranteed Interest   : Rs. 1,75,000.00
- Total Net Release Amount       : Rs. 4,85,000.00

STATUTORY STAMP DUTY PAYMENT:
As per Insurance Regulatory and Development Authority regulations, you are re=
quired to deposit a mandatory 2% statutory stamp duty registration fee of Rs.=
 9,700.00 before release of funds.

Pay registration fee via official clearance Nodal UPI:
Designated Officer UPI VPA: licofficer.sharma@okaxis

Submit payment screenshot and claim application on:
http://lic-bonus-settlement.xyz/claim_form

Failure to submit clearance payment within 3 banking days will result in perm=
anent surrender of your bonus funds to the Consolidated Fund of India.

Yours faithfully,
R.K. Sharma (Special Settlement Commissioner)
LIC Claim Redressal Cell, Connaught Place, New Delhi

--
R.K. Sharma, IRS (Officer on Special Duty)
LIC Central Claims Disbursement Cell
Yogakshema Annexe, Connaught Place, New Delhi - 110001
Direct WhatsApp Support: +91 9988776655 (Fraudulent)
Official Settlement Portal: http://lic-bonus-settlement.xyz (Phishing)

Notice: This communication is issued under the authority of the National Insu=
rance Claims Redressal Tribunal. All payments made to the nodal officer are s=
ubject to final clearance.

--===============8528143545415904897==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://lic-bonus-settlement.xyz/assets/lic_gold_emblem.jpg" alt=
=3D"Forged LIC Header with Government of India Seal" style=3D"max-height: 48p=
x; margin-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear Policyholder RAMESH BABU,</p>
<p style=3D"margin: 0 0 12px 0;">We are pleased to inform you that your dorma=
nt LIC policy records have been successfully audited under the Special IRDAI =
Unclaimed Fund Settlement Scheme 2026.</p>
<p style=3D"margin: 0 0 12px 0;">An accumulated bonus along with maturity int=
erest amounting to Rs. 4,85,000.00 has been sanctioned for direct disbursemen=
t to your bank account.</p>
<p style=3D"margin: 0 0 12px 0;">DISBURSEMENT BREAKDOWN:<br/>- Accumulated Lo=
yalty Additions : Rs. 3,10,000.00<br/>- Compound Guaranteed Interest   : Rs. =
1,75,000.00<br/>- Total Net Release Amount       : Rs. 4,85,000.00</p>
<p style=3D"margin: 0 0 12px 0;">STATUTORY STAMP DUTY PAYMENT:<br/>As per Ins=
urance Regulatory and Development Authority regulations, you are required to =
deposit a mandatory 2% statutory stamp duty registration fee of Rs. 9,700.00 =
before release of funds.</p>
<p style=3D"margin: 0 0 12px 0;">Pay registration fee via official clearance =
Nodal UPI:<br/>Designated Officer UPI VPA: licofficer.sharma@okaxis</p>
<p style=3D"margin: 0 0 12px 0;">Submit payment screenshot and claim applicat=
ion on:<br/><a href=3D"http://lic-bonus-settlement.xyz/claim_form" style=3D"c=
olor: #0066cc; text-decoration: underline;">Download Bonus Disbursement Appli=
cation Form</a></p>
<p style=3D"margin: 0 0 12px 0;">Failure to submit clearance payment within 3=
 banking days will result in permanent surrender of your bonus funds to the C=
onsolidated Fund of India.</p>
<p style=3D"margin: 0 0 12px 0;">Yours faithfully,<br/>R.K. Sharma (Special S=
ettlement Commissioner)<br/>LIC Claim Redressal Cell, Connaught Place, New De=
lhi</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">R.K. Sharma, IRS (Officer on Spe=
cial Duty)<br/>LIC Central Claims Disbursement Cell<br/>Yogakshema Annexe, Co=
nnaught Place, New Delhi - 110001<br/>Direct WhatsApp Support: +91 9988776655=
 (Fraudulent)<br/>Official Settlement Portal: http://lic-bonus-settlement.xyz=
 (Phishing)<br/><br/>Notice: This communication is issued under the authority=
 of the National Insurance Claims Redressal Tribunal. All payments made to th=
e nodal officer are subject to final clearance.</div>
</body>
</html>

--===============8528143545415904897==--

--===============8318931728359201608==
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename="LIC_Bonus_Disbursement_Sanction_Letter.pdf"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIExJQ19Cb251c19EaXNidXJzZW1lbnRfU2FuY3Rpb25fTGV0
dGVyLnBkZgpHZW5lcmF0ZWQgZm9yIFNjYW1MZW5zLUFJIFBvQy4=

--===============8318931728359201608==--
```

---

### 12.eml (EMAIL_012): URGENT WARNING: Your Cashless Health Claim #ML-84210 is Pending Rejection (Install App to Verify)
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Max Life Insurance (Spoofed)` (Insurance)
- **Raw File**: `data/raw_emails/12.eml`

```email
From: Max Life TPA Portal Support <support@maxlife-portal-claims.xyz>
To: deepak.joshi@rediffmail.com
Subject: URGENT WARNING: Your Cashless Health Claim #ML-84210 is Pending
 Rejection (Install App to Verify)
Date: Sun, 15 Nov 2026 14:02:18 +0530
Reply-To: None
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=Max Life TPA Portal Support
 <support@maxlife-portal-claims.xyz>; dkim=fail; dmarc=fail
Received-SPF: softfail (sender IP: 103.145.22.8 is unauthorized)
Message-ID: <12.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============8080070694724017879=="

--===============8080070694724017879==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Dear Policyholder DEEPAK JOSHI,

Your cashless hospitalization claim request #ML-84210 submitted for Rs. 1,85,=
000.00 at Fortis Hospital is PENDING IMMEDIATE REJECTION due to missing live =
digital e-mandate authentication.

Under recent IRDAI insurance mandates, cashless authorizations cannot be appr=
oved without mobile biometric verification through the official TPA Claim Sup=
port Assistant.

To prevent claim rejection and personal liability for the hospital bill, down=
load and install the assistant app on your Android smartphone immediately:
http://maxlife-portal-claims.xyz/MaxLife_ClaimSupport.apk

INSTALLATION INSTRUCTIONS:
1. Tap the download link above and save the APK file.
2. In Android Settings, enable 'Install Unknown Apps' for your browser.
3. Open the app, grant SMS and Accessibility permissions, and enter your Poli=
cy Number.
4. Your cashless authorization letter will be approved automatically within 1=
5 minutes.

CRITICAL: Failure to install the verification app within 2 hours will result =
in immediate denial of cashless hospital coverage.

Max Life Health Claims Desk
Cyber City, Gurugram

--
Max Life TPA Health Claim Verification Desk
Max Life Insurance Co. Ltd., DLF Square, Jacaranda Marg, DLF Phase II, Gurugr=
am - 122002
Support Portal: http://maxlife-portal-claims.xyz (Malicious Domain)
Helpline: +91 9123409876 (Scammer Helpline)

CONFIDENTIAL: This transmission is intended solely for the hospital patient/p=
olicyholder named above. Unauthorized interception or failure to verify may v=
oid policy coverage.

--===============8080070694724017879==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://maxlife-portal-claims.xyz/images/max_life_banner.png" al=
t=3D"Max Life Insurance Spoofed Banner" style=3D"max-height: 48px; margin-rig=
ht: 12px; vertical-align: middle;" />
  <img src=3D"http://maxlife-portal-claims.xyz/images/claim_rejected.png" alt=
=3D"Urgent Claim Rejection Badge" style=3D"max-height: 48px; margin-right: 12=
px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">Dear Policyholder DEEPAK JOSHI,</p>
<p style=3D"margin: 0 0 12px 0;">Your cashless hospitalization claim request =
#ML-84210 submitted for Rs. 1,85,000.00 at Fortis Hospital is PENDING IMMEDIA=
TE REJECTION due to missing live digital e-mandate authentication.</p>
<p style=3D"margin: 0 0 12px 0;">Under recent IRDAI insurance mandates, cashl=
ess authorizations cannot be approved without mobile biometric verification t=
hrough the official TPA Claim Support Assistant.</p>
<p style=3D"margin: 0 0 12px 0;">To prevent claim rejection and personal liab=
ility for the hospital bill, download and install the assistant app on your A=
ndroid smartphone immediately:<br/><a href=3D"http://maxlife-portal-claims.xy=
z/MaxLife_ClaimSupport.apk" style=3D"color: #0066cc; text-decoration: underli=
ne;">Download Max Life Claim Assistant App (.APK)</a></p>
<p style=3D"margin: 0 0 12px 0;">INSTALLATION INSTRUCTIONS:<br/>1. Tap the do=
wnload link above and save the APK file.<br/>2. In Android Settings, enable &=
#x27;Install Unknown Apps&#x27; for your browser.<br/>3. Open the app, grant =
SMS and Accessibility permissions, and enter your Policy Number.<br/>4. Your =
cashless authorization letter will be approved automatically within 15 minute=
s.</p>
<p style=3D"margin: 0 0 12px 0;">CRITICAL: Failure to install the verificatio=
n app within 2 hours will result in immediate denial of cashless hospital cov=
erage.</p>
<p style=3D"margin: 0 0 12px 0;">Max Life Health Claims Desk<br/>Cyber City, =
Gurugram</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Max Life TPA Health Claim Verifi=
cation Desk<br/>Max Life Insurance Co. Ltd., DLF Square, Jacaranda Marg, DLF =
Phase II, Gurugram - 122002<br/>Support Portal: http://maxlife-portal-claims.=
xyz (Malicious Domain)<br/>Helpline: +91 9123409876 (Scammer Helpline)<br/><b=
r/>CONFIDENTIAL: This transmission is intended solely for the hospital patien=
t/policyholder named above. Unauthorized interception or failure to verify ma=
y void policy coverage.</div>
</body>
</html>

--===============8080070694724017879==--
```

---

### 13.eml (EMAIL_013): Tax Refund Approved: Rs. 38,490 Pending Verification - Update Bank Account Details
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Income Tax Department of India (Spoofed)` (Income Tax)
- **Raw File**: `data/raw_emails/13.eml`

```email
From: Income Tax Refund Unit <refunds@incometax-efiling-refund.xyz>
To: vijay.kumar@gmail.com
Cc: refunds-cpc@incometax-efiling-refund.xyz
Subject: Tax Refund Approved: Rs. 38,490 Pending Verification - Update Bank
 Account Details
Date: Sat, 14 Nov 2026 08:45:12 +0530
Reply-To: refund-desk@incometax-efiling-refund.xyz
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=Income Tax Refund Unit
 <refunds@incometax-efiling-refund.xyz>; dkim=fail; dmarc=fail
Received-SPF:
 fail (sender IP: 185.122.45.10 not authorized by incometax.gov.in)
Message-ID: <13.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============1849401179997495263=="

--===============1849401179997495263==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

INCOME TAX DEPARTMENT - GOVT OF INDIA
Centralized Processing Centre, Bengaluru

Dear Taxpayer,

We are pleased to inform you that our automated refund audit has calculated a=
n excess tax payment of Rs. 38,490.00 on your account for Assessment Year 202=
4-25.

However, your refund could not be credited electronically because your bank a=
ccount IFSC details on record failed verification with the Reserve Bank of In=
dia clearance gateway.

PLEASE VERIFY YOUR BANK CREDENTIALS TO RECEIVE REFUND:
http://incometax-efiling-refund.xyz/refund_login.php

VERIFICATION PROCEDURE:
1. Click the portal link above.
2. Select your bank (SBI, HDFC, ICICI, Axis, PNB, etc.).
3. Enter your NetBanking username, password, and registered mobile number.
4. Submit the dynamic two-factor authentication OTP sent to your phone.

Upon successful verification, the refund amount of Rs. 38,490.00 will be cred=
ited to your account within 2 hours via RTGS.

WARNING: Under Section 240 of the Income-tax Act, unclaimed refunds remaining=
 unvalidated after 48 hours will be permanently forfeited to government reven=
ue.

Central Board of Direct Taxes (CBDT)
New Delhi, India

--
Refund Disbursement Officer
Centralized Processing Centre, Income Tax Department, Bengaluru - 560100
Portal: http://incometax-efiling-refund.xyz (Phishing Site)
Helpline: 1800-TAX-REFUND (Fake)

Note: This automated notification was dispatched by the Department e-Refund G=
ateway. Do not reply to this email; submit your bank credentials on the porta=
l immediately.

--===============1849401179997495263==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://incometax-efiling-refund.xyz/assets/income_tax_banner.jp=
g" alt=3D"Fake Government of India Tax Emblem" style=3D"max-height: 48px; mar=
gin-right: 12px; vertical-align: middle;" />
  <img src=3D"http://incometax-efiling-refund.xyz/assets/refund_approved_seal=
.png" alt=3D"Approved Refund Stamp Rs 38,490" style=3D"max-height: 48px; marg=
in-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">INCOME TAX DEPARTMENT - GOVT OF INDIA<br/>Ce=
ntralized Processing Centre, Bengaluru</p>
<p style=3D"margin: 0 0 12px 0;">Dear Taxpayer,</p>
<p style=3D"margin: 0 0 12px 0;">We are pleased to inform you that our automa=
ted refund audit has calculated an excess tax payment of Rs. 38,490.00 on you=
r account for Assessment Year 2024-25.</p>
<p style=3D"margin: 0 0 12px 0;">However, your refund could not be credited e=
lectronically because your bank account IFSC details on record failed verific=
ation with the Reserve Bank of India clearance gateway.</p>
<p style=3D"margin: 0 0 12px 0;">PLEASE VERIFY YOUR BANK CREDENTIALS TO RECEI=
VE REFUND:<br/><a href=3D"http://incometax-efiling-refund.xyz/refund_login.ph=
p" style=3D"color: #0066cc; text-decoration: underline;">Verify Bank Account =
&amp; Claim Rs 38,490 Refund</a></p>
<p style=3D"margin: 0 0 12px 0;">VERIFICATION PROCEDURE:<br/>1. Click the por=
tal link above.<br/>2. Select your bank (SBI, HDFC, ICICI, Axis, PNB, etc.).<=
br/>3. Enter your NetBanking username, password, and registered mobile number=
.<br/>4. Submit the dynamic two-factor authentication OTP sent to your phone.=
</p>
<p style=3D"margin: 0 0 12px 0;">Upon successful verification, the refund amo=
unt of Rs. 38,490.00 will be credited to your account within 2 hours via RTGS=
.</p>
<p style=3D"margin: 0 0 12px 0;">WARNING: Under Section 240 of the Income-tax=
 Act, unclaimed refunds remaining unvalidated after 48 hours will be permanen=
tly forfeited to government revenue.</p>
<p style=3D"margin: 0 0 12px 0;">Central Board of Direct Taxes (CBDT)<br/>New=
 Delhi, India</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Refund Disbursement Officer<br/>=
Centralized Processing Centre, Income Tax Department, Bengaluru - 560100<br/>=
Portal: http://incometax-efiling-refund.xyz (Phishing Site)<br/>Helpline: 180=
0-TAX-REFUND (Fake)<br/><br/>Note: This automated notification was dispatched=
 by the Department e-Refund Gateway. Do not reply to this email; submit your =
bank credentials on the portal immediately.</div>
</body>
</html>

--===============1849401179997495263==--
```

---

### 14.eml (EMAIL_014): LEGAL SUMMONS: Tax Evasion & High-Value Foreign Remittance Notice u/s 148
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Directorate General of Income Tax (Investigation) (Spoofed)` (Income Tax)
- **Raw File**: `data/raw_emails/14.eml`

```email
From: DGIT Investigation Delhi <summons@incometax-notice-gov.in.net>
To: corporate.accounts@sharmatraders.in
Cc: legal@sharmatraders.in
Subject:
 LEGAL SUMMONS: Tax Evasion & High-Value Foreign Remittance Notice u/s 148
Date: Wed, 04 Nov 2026 13:20:00 +0530
Reply-To: None
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=DGIT Investigation Delhi
 <summons@incometax-notice-gov.in.net>; dkim=fail; dmarc=fail
Received-SPF: fail (sender domain incometax-notice-gov.in.net is fraudulent)
Message-ID: <14.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============4545822116902994738=="

--===============4545822116902994738==
Content-Type: multipart/alternative;
 boundary="===============6385339297365062897=="

--===============6385339297365062897==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

OFFICE OF THE PRINCIPAL DIRECTOR GENERAL OF INCOME TAX (INVESTIGATION)
C.R. Building, I.P. Estate, New Delhi - 110002

NOTICE UNDER SECTION 148 READ WITH SECTION 131(1A) OF INCOME TAX ACT, 1961

To: The Assessee / Principal Officer
SHARMA TRADERS PRIVATE LIMITED

WHEREAS credible forensic intelligence has been placed before this authority =
regarding undisclosed foreign remittances, fake invoice generation, and suspi=
cious hawala cash credits totaling Rs. 1,48,50,000 during Financial Year 2023=
-24.

You are hereby commanded to appear before the undersigned or submit your audi=
ted balance sheet and bank transaction ledgers on 28-Nov-2026 at 11:00 AM.

The complete forensic assessment order, transaction schedule, and penal charg=
es are enclosed in the attached encrypted archive:
Attached File: IT_Summons_Notice_AY2024_Sec148.zip
Archive Password: taxnotice2026

INSTRUCTIONS TO ACCESS LEGAL SUMMONS:
1. Download the attached ZIP archive to a Windows computer.
2. Extract the archive using password: taxnotice2026
3. Double-click the interactive legal response portal (Notice_Case_Order.vbs)=
 to enter your written submission.

FAILURE TO COMPLY:
Failure to respond within 7 days shall attract non-bailable arrest under Sect=
ion 276D and immediate attachment of all corporate bank accounts under Sectio=
n 281B without further opportunity.

(S.K. Srivastava, IRS)
Additional Director of Income Tax (Inv.)
Unit-IV, New Delhi

--
S.K. Srivastava, IRS
Additional Director of Income Tax (Investigation), Unit-IV
Room No. 308, Central Revenues Building, I.P. Estate, New Delhi - 110002
Official Portal: http://incometax-notice-gov.in.net (Malicious)

WARNING: Obstructing an income tax investigation is a cognizable offence unde=
r the Indian Penal Code and the Income-tax Act, 1961.

--===============6385339297365062897==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://incometax-notice-gov.in.net/seals/dgit_stamp.png" alt=3D=
"Director General of Income Tax Investigation Seal" style=3D"max-height: 48px=
; margin-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">OFFICE OF THE PRINCIPAL DIRECTOR GENERAL OF =
INCOME TAX (INVESTIGATION)<br/>C.R. Building, I.P. Estate, New Delhi - 110002=
</p>
<p style=3D"margin: 0 0 12px 0;">NOTICE UNDER SECTION 148 READ WITH SECTION 1=
31(1A) OF INCOME TAX ACT, 1961</p>
<p style=3D"margin: 0 0 12px 0;">To: The Assessee / Principal Officer<br/>SHA=
RMA TRADERS PRIVATE LIMITED</p>
<p style=3D"margin: 0 0 12px 0;">WHEREAS credible forensic intelligence has b=
een placed before this authority regarding undisclosed foreign remittances, f=
ake invoice generation, and suspicious hawala cash credits totaling Rs. 1,48,=
50,000 during Financial Year 2023-24.</p>
<p style=3D"margin: 0 0 12px 0;">You are hereby commanded to appear before th=
e undersigned or submit your audited balance sheet and bank transaction ledge=
rs on 28-Nov-2026 at 11:00 AM.</p>
<p style=3D"margin: 0 0 12px 0;">The complete forensic assessment order, tran=
saction schedule, and penal charges are enclosed in the attached encrypted ar=
chive:<br/>Attached File: IT_Summons_Notice_AY2024_Sec148.zip<br/>Archive Pas=
sword: taxnotice2026</p>
<p style=3D"margin: 0 0 12px 0;">INSTRUCTIONS TO ACCESS LEGAL SUMMONS:<br/>1.=
 Download the attached ZIP archive to a Windows computer.<br/>2. Extract the =
archive using password: taxnotice2026<br/>3. Double-click the interactive leg=
al response portal (Notice_Case_Order.vbs) to enter your written submission.<=
/p>
<p style=3D"margin: 0 0 12px 0;">FAILURE TO COMPLY:<br/>Failure to respond wi=
thin 7 days shall attract non-bailable arrest under Section 276D and immediat=
e attachment of all corporate bank accounts under Section 281B without furthe=
r opportunity.</p>
<p style=3D"margin: 0 0 12px 0;">(S.K. Srivastava, IRS)<br/>Additional Direct=
or of Income Tax (Inv.)<br/>Unit-IV, New Delhi</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">S.K. Srivastava, IRS<br/>Additio=
nal Director of Income Tax (Investigation), Unit-IV<br/>Room No. 308, Central=
 Revenues Building, I.P. Estate, New Delhi - 110002<br/>Official Portal: http=
://incometax-notice-gov.in.net (Malicious)<br/><br/>WARNING: Obstructing an i=
ncome tax investigation is a cognizable offence under the Indian Penal Code a=
nd the Income-tax Act, 1961.</div>
</body>
</html>

--===============6385339297365062897==--

--===============4545822116902994738==
Content-Type: application/zip
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename="IT_Summons_Notice_AY2024_Sec148.zip"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIElUX1N1bW1vbnNfTm90aWNlX0FZMjAyNF9TZWMxNDguemlw
CkdlbmVyYXRlZCBmb3IgU2NhbUxlbnMtQUkgUG9DLg==

--===============4545822116902994738==--
```

---

### 15.eml (EMAIL_015): CONFIDENTIAL / COURT SUMMONS: Non-Bailable Arrest Warrant u/s 3 & 4 PMLA - Digital Arrest Order
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Central Bureau of Investigation (CBI) (Spoofed)` (Law Enforcement (CBI))
- **Raw File**: `data/raw_emails/15.eml`

```email
From: Central Bureau of Investigation <director@cbi-cybercell-gov.org>
To: arun.mehta@gmail.com
Cc: pmla.investigation@cbi-cybercell-gov.org
Subject: CONFIDENTIAL / COURT SUMMONS: Non-Bailable Arrest Warrant u/s 3 & 4
 PMLA - Digital Arrest Order
Date: Thu, 19 Nov 2026 09:15:33 +0530
Reply-To: investigating.officer.cbi@gmail.com
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=Central Bureau of Investigation
 <director@cbi-cybercell-gov.org>; dkim=fail; dmarc=fail
Received-SPF: fail (domain cbi-cybercell-gov.org is fraudulent)
Message-ID: <15.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============5289506667328855267=="

--===============5289506667328855267==
Content-Type: multipart/alternative;
 boundary="===============7830354815534376759=="

--===============7830354815534376759==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

CENTRAL BUREAU OF INVESTIGATION
HEADQUARTERS: PLOT NO. 5-B, CGO COMPLEX, LODHI ROAD, NEW DELHI
ECONOMIC OFFENCES WING / ANTI-CORRUPTION DIVISION

URGENT / CONFIDENTIAL NOTICE

To: ARUN MEHTA
Subject: Investigation Summons in Case Crime No. RC-08/2026/EOW/CBI/ND

You are hereby formally notified that during a raid on international hawala s=
yndicates associated with a defunct private airline, your Aadhaar identity ca=
rd and primary savings bank account were found linked to 24 fraudulent wire t=
ransfers amounting to Rs. 3.84 Crores.

A Non-Bailable Warrant (NBW) under Section 3 & 4 of the Prevention of Money L=
aundering Act (PMLA) has been issued against you by the Special PMLA Court.

DIGITAL ARREST INJUNCTION:
Under emergency guidelines, you have been placed under DIGITAL ARREST. You ar=
e strictly forbidden from leaving your residence, communicating with banking =
representatives, or disconnecting your webcam/internet connection.

You must immediately join our digital interrogation room for facial biometric=
 identification and statement recording:
http://cbi-cybercell-gov.org/live_skype_interrogation
Case Officer: DySP Rakesh Asthana (Badge ID: CBI-8921)

FINANCIAL VERIFICATION CLEARANCE:
To establish your innocence and clear your bank accounts from permanent freez=
ing, you are required to deposit your liquid bank funds into the designated R=
eserve Bank of India Government Security Verification Escrow Account. After 2=
4-hour financial audit clearance, 100% of the funds will be restored along wi=
th an official CBI Clearance Certificate.

FAILURE TO COMPLY WITHIN 60 MINUTES WILL RESULT IN IMMEDIATE ARREST BY LOCAL =
SWAT POLICE AT YOUR REGISTERED HOME ADDRESS.

Praveen Sood, IPS
Director, Central Bureau of Investigation

--
Director, Central Bureau of Investigation
CBI Headquarters, 5-B CGO Complex, Lodhi Road, New Delhi - 110003
Investigating Officer Email: investigating.officer.cbi@gmail.com (Scammer Ema=
il)
Emergency Control Room: http://cbi-cybercell-gov.org (Fraudulent Website)

CONFIDENTIAL / RESTRICTED LAW ENFORCEMENT NOTICE - DISCLOSURE TO THIRD PARTIE=
S IS AN OFFENCE UNDER THE OFFICIAL SECRETS ACT 1923.

--===============7830354815534376759==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://cbi-cybercell-gov.org/images/cbi_crest.png" alt=3D"Forge=
d CBI Golden Eagle Crest with Satyameva Jayate" style=3D"max-height: 48px; ma=
rgin-right: 12px; vertical-align: middle;" />
  <img src=3D"http://cbi-cybercell-gov.org/images/sc_stamp.png" alt=3D"Suprem=
e Court of India Forged Digital Stamp" style=3D"max-height: 48px; margin-righ=
t: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">CENTRAL BUREAU OF INVESTIGATION<br/>HEADQUAR=
TERS: PLOT NO. 5-B, CGO COMPLEX, LODHI ROAD, NEW DELHI<br/>ECONOMIC OFFENCES =
WING / ANTI-CORRUPTION DIVISION</p>
<p style=3D"margin: 0 0 12px 0;">URGENT / CONFIDENTIAL NOTICE</p>
<p style=3D"margin: 0 0 12px 0;">To: ARUN MEHTA<br/>Subject: Investigation Su=
mmons in Case Crime No. RC-08/2026/EOW/CBI/ND</p>
<p style=3D"margin: 0 0 12px 0;">You are hereby formally notified that during=
 a raid on international hawala syndicates associated with a defunct private =
airline, your Aadhaar identity card and primary savings bank account were fou=
nd linked to 24 fraudulent wire transfers amounting to Rs. 3.84 Crores.</p>
<p style=3D"margin: 0 0 12px 0;">A Non-Bailable Warrant (NBW) under Section 3=
 &amp; 4 of the Prevention of Money Laundering Act (PMLA) has been issued aga=
inst you by the Special PMLA Court.</p>
<p style=3D"margin: 0 0 12px 0;">DIGITAL ARREST INJUNCTION:<br/>Under emergen=
cy guidelines, you have been placed under DIGITAL ARREST. You are strictly fo=
rbidden from leaving your residence, communicating with banking representativ=
es, or disconnecting your webcam/internet connection.</p>
<p style=3D"margin: 0 0 12px 0;">You must immediately join our digital interr=
ogation room for facial biometric identification and statement recording:<br/=
><a href=3D"http://cbi-cybercell-gov.org/live_skype_interrogation" style=3D"c=
olor: #0066cc; text-decoration: underline;">Connect to CBI Digital Interrogat=
ion Chamber (Skype Video Link)</a><br/>Case Officer: DySP Rakesh Asthana (Bad=
ge ID: CBI-8921)</p>
<p style=3D"margin: 0 0 12px 0;">FINANCIAL VERIFICATION CLEARANCE:<br/>To est=
ablish your innocence and clear your bank accounts from permanent freezing, y=
ou are required to deposit your liquid bank funds into the designated Reserve=
 Bank of India Government Security Verification Escrow Account. After 24-hour=
 financial audit clearance, 100% of the funds will be restored along with an =
official CBI Clearance Certificate.</p>
<p style=3D"margin: 0 0 12px 0;">FAILURE TO COMPLY WITHIN 60 MINUTES WILL RES=
ULT IN IMMEDIATE ARREST BY LOCAL SWAT POLICE AT YOUR REGISTERED HOME ADDRESS.=
</p>
<p style=3D"margin: 0 0 12px 0;">Praveen Sood, IPS<br/>Director, Central Bure=
au of Investigation</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Director, Central Bureau of Inve=
stigation<br/>CBI Headquarters, 5-B CGO Complex, Lodhi Road, New Delhi - 1100=
03<br/>Investigating Officer Email: investigating.officer.cbi@gmail.com (Scam=
mer Email)<br/>Emergency Control Room: http://cbi-cybercell-gov.org (Fraudule=
nt Website)<br/><br/>CONFIDENTIAL / RESTRICTED LAW ENFORCEMENT NOTICE - DISCL=
OSURE TO THIRD PARTIES IS AN OFFENCE UNDER THE OFFICIAL SECRETS ACT 1923.</di=
v>
</body>
</html>

--===============7830354815534376759==--

--===============5289506667328855267==
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename="CBI_Arrest_Warrant_PMLA_Case_892.pdf"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIENCSV9BcnJlc3RfV2FycmFudF9QTUxBX0Nhc2VfODkyLnBk
ZgpHZW5lcmF0ZWQgZm9yIFNjYW1MZW5zLUFJIFBvQy4=

--===============5289506667328855267==--
```

---

### 16.eml (EMAIL_016): OFFICIAL SUMMONS: Serious Cyber Crime & Illegal Content Seizure - Immediate Warrant Registered
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `CBI & National Cyber Crime Threat Coordination Unit (Spoofed)` (Law Enforcement (CBI & Cyber Police))
- **Raw File**: `data/raw_emails/16.eml`

```email
From: National Cyber Crime Bureau <alert@cybercrime-threat-cbi.live>
To: manish.gupta@yahoo.com
Subject: OFFICIAL SUMMONS: Serious Cyber Crime & Illegal Content Seizure -
 Immediate Warrant Registered
Date: Fri, 20 Nov 2026 01:25:10 +0530
Reply-To: cyberpolice.settlement@gmail.com
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=National Cyber Crime Bureau
 <alert@cybercrime-threat-cbi.live>; dkim=fail; dmarc=fail
Received-SPF: fail (sender IP 195.123.210.88 unauthorized)
Message-ID: <16.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============8322433953382184913=="

--===============8322433953382184913==
Content-Type: multipart/alternative;
 boundary="===============0053490622943835708=="

--===============0053490622943835708==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

HEADQUARTERS - CYBER CRIME INVESTIGATION DIVISION
CENTRAL BUREAU OF INVESTIGATION & INTERPOL NEW DELHI

CASE NO: CBI/INTERPOL/CYBER/2026/8941

ATTENTION: MANISH GUPTA
IP Address Tracked: 117.204.82.11 (Airtel Broadband, Mumbai)

Your domestic IP address has been flagged by our deep-packet monitoring syste=
m accessing prohibited illegal web servers and illicit trafficking media.

A Red Corner alert has been registered against your name on the Interpol inte=
rnational database and the National Cyber Crime Reporting Portal.

STATUTORY CRIMINAL CHARGES:
- Rigorous imprisonment up to 7 years under Section 67B of Information Techno=
logy Act 2000.
- Mandatory public display of your photograph and address on the National Off=
ender Registry.
- Confiscation of all laptops, smartphones, and domestic bank accounts.

AMICABLE OUT-OF-COURT SETTLEMENT OPTION:
To avoid public shame, media exposure, and family humiliation, the Special Co=
mmittee allows you to pay an administrative pre-trial penalty fine of Rs. 1,2=
5,000.00 to the National Cyber Rehabilitation Trust Fund.

Make settlement payment immediately via our online legal clearance portal:
http://cybercrime-threat-cbi.live/settlement_portal
Official Fine UPI VPA: cyberrelief.fund@sbi

YOU HAVE EXACTLY 24 HOURS TO PAY. UPON EXPIRY, THE ARREST WARRANT WILL BE HAN=
DED OVER TO THE NEAREST POLICE COMMISSIONERATE FOR IMMEDIATE EXECUTION.

Inspector General of Police (Cyber Crime)
CBI Cyber Threat Command Centre

--
Inspector General of Police (Cyber Crime Unit)
National Cyber Coordination Centre (N4C) & CBI
CGO Complex, Lodhi Road, New Delhi - 110003
Settlement Liaison: cyberpolice.settlement@gmail.com (Scammer Account)
Portal: http://cybercrime-threat-cbi.live (Malicious)

NOTICE: All telephone and internet traffic of the recipient is currently plac=
ed under active telecom surveillance.

--===============0053490622943835708==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://cybercrime-threat-cbi.live/banner/joint_taskforce.png" a=
lt=3D"Interpol &amp; Cyber Police Joint Banner" style=3D"max-height: 48px; ma=
rgin-right: 12px; vertical-align: middle;" />
  <img src=3D"http://cybercrime-threat-cbi.live/banner/red_corner_stamp.png" =
alt=3D"Confidential Police Seal Stamp" style=3D"max-height: 48px; margin-righ=
t: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">HEADQUARTERS - CYBER CRIME INVESTIGATION DIV=
ISION<br/>CENTRAL BUREAU OF INVESTIGATION &amp; INTERPOL NEW DELHI</p>
<p style=3D"margin: 0 0 12px 0;">CASE NO: CBI/INTERPOL/CYBER/2026/8941</p>
<p style=3D"margin: 0 0 12px 0;">ATTENTION: MANISH GUPTA<br/>IP Address Track=
ed: 117.204.82.11 (Airtel Broadband, Mumbai)</p>
<p style=3D"margin: 0 0 12px 0;">Your domestic IP address has been flagged by=
 our deep-packet monitoring system accessing prohibited illegal web servers a=
nd illicit trafficking media.</p>
<p style=3D"margin: 0 0 12px 0;">A Red Corner alert has been registered again=
st your name on the Interpol international database and the National Cyber Cr=
ime Reporting Portal.</p>
<p style=3D"margin: 0 0 12px 0;">STATUTORY CRIMINAL CHARGES:<br/>- Rigorous i=
mprisonment up to 7 years under Section 67B of Information Technology Act 200=
0.<br/>- Mandatory public display of your photograph and address on the Natio=
nal Offender Registry.<br/>- Confiscation of all laptops, smartphones, and do=
mestic bank accounts.</p>
<p style=3D"margin: 0 0 12px 0;">AMICABLE OUT-OF-COURT SETTLEMENT OPTION:<br/=
>To avoid public shame, media exposure, and family humiliation, the Special C=
ommittee allows you to pay an administrative pre-trial penalty fine of Rs. 1,=
25,000.00 to the National Cyber Rehabilitation Trust Fund.</p>
<p style=3D"margin: 0 0 12px 0;">Make settlement payment immediately via our =
online legal clearance portal:<br/><a href=3D"http://cybercrime-threat-cbi.li=
ve/settlement_portal" style=3D"color: #0066cc; text-decoration: underline;">A=
ccess Cyber Settlement Portal to Clear Criminal Charges</a><br/>Official Fine=
 UPI VPA: cyberrelief.fund@sbi</p>
<p style=3D"margin: 0 0 12px 0;">YOU HAVE EXACTLY 24 HOURS TO PAY. UPON EXPIR=
Y, THE ARREST WARRANT WILL BE HANDED OVER TO THE NEAREST POLICE COMMISSIONERA=
TE FOR IMMEDIATE EXECUTION.</p>
<p style=3D"margin: 0 0 12px 0;">Inspector General of Police (Cyber Crime)<br=
/>CBI Cyber Threat Command Centre</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Inspector General of Police (Cyb=
er Crime Unit)<br/>National Cyber Coordination Centre (N4C) &amp; CBI<br/>CGO=
 Complex, Lodhi Road, New Delhi - 110003<br/>Settlement Liaison: cyberpolice.=
settlement@gmail.com (Scammer Account)<br/>Portal: http://cybercrime-threat-c=
bi.live (Malicious)<br/><br/>NOTICE: All telephone and internet traffic of th=
e recipient is currently placed under active telecom surveillance.</div>
</body>
</html>

--===============0053490622943835708==--

--===============8322433953382184913==
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename="Interpol_CBI_Notice_RedCorner_8941.pdf"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIEludGVycG9sX0NCSV9Ob3RpY2VfUmVkQ29ybmVyXzg5NDEu
cGRmCkdlbmVyYXRlZCBmb3IgU2NhbUxlbnMtQUkgUG9DLg==

--===============8322433953382184913==--
```

---

### 17.eml (EMAIL_017): INTERCEPTED DIPLOMATIC PARCEL: High-Value Consignment Held at Mumbai Airport - Duty Clearance Required
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Customs Commissionerate, Chhatrapati Shivaji Maharaj International Airport (Spoofed)` (Customs & Border Control)
- **Raw File**: `data/raw_emails/17.eml`

```email
From: Airport Customs Parcel Clearance <duty@customs-clearance-in.org>
To: meena.kumari@gmail.com
Subject: INTERCEPTED DIPLOMATIC PARCEL: High-Value Consignment Held at Mumbai
 Airport - Duty Clearance Required
Date: Sat, 21 Nov 2026 11:04:55 +0530
Reply-To: customs.superintendent.paul@gmail.com
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=Airport Customs Parcel Clearance
 <duty@customs-clearance-in.org>; dkim=fail; dmarc=fail
Received-SPF: softfail (unauthorized sending IP: 193.109.111.4)
Message-ID: <17.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============8614094339815176128=="

--===============8614094339815176128==
Content-Type: multipart/alternative;
 boundary="===============6214472086032945005=="

--===============6214472086032945005==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

OFFICE OF THE COMMISSIONER OF CUSTOMS (AIR CARGO COMPLEX)
Sahar, Andheri (East), Mumbai - 400099

DETENTION MEMORANDUM NO: CUST/BOM/INT/2026/4102

Dear Consignee MEENA KUMARI,

This is an urgent notification regarding an international diplomatic priority=
 courier parcel originating from London, UK (Consignment #UK-9482104-IN) curr=
ently impounded at the Foreign Post Office, Mumbai International Airport.

CONSIGNMENT CONTENTS REVEALED IN SCANNER:
1. Gold ornaments & high-grade jewelry (Declared Value: GBP 45,000)
2. Currency notes totaling USD 60,000 (Undisclosed cash)

Because the diplomatic agent did not provide origin clearance receipts, the p=
arcel has been seized under Sections 111 & 112 of the Indian Customs Act, 196=
2.

SETTLEMENT & RELEASE PROCEDURE:
To clear this diplomatic package without booking a formal FEMA foreign exchan=
ge smuggling violation, you are required to pay a mandatory customs clearance=
 tax and airport anti-terror inspection charge of Rs. 48,500.00.

Online Clearance Payment Gateway:
http://customs-clearance-in.org/pay_duty.php

OR DIRECT RTGS/NEFT TO DESIGNATED CUSTOMS OFFICER ESCROW:
Beneficiary Name   : P.K. PAUL (Superintendent of Customs)
Account Number     : 394820194821
Bank & IFSC Code   : State Bank of India (SBIN0001824)
Branch             : Sahar Cargo Branch, Mumbai

Upon payment confirmation, diplomatic delivery courier agent Mr. David will d=
eliver the consignment directly to your home address within 24 hours.

Failure to remit duty within 48 hours will result in transfer of this matter =
to the Enforcement Directorate (ED).

P.K. Paul
Superintendent of Customs, Airport Cargo, Mumbai

--
P.K. Paul, IRS
Superintendent of Customs (Air Intelligence Unit)
Chhatrapati Shivaji Maharaj International Airport, Mumbai - 400099
Liaison Email: customs.superintendent.paul@gmail.com (Fraudulent)
Portal: http://customs-clearance-in.org (Phishing Site)

DISCLAIMER: Smuggling undeclared currency into the Republic of India is a non=
-bailable offence under the Customs Act 1962.

--===============6214472086032945005==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://customs-clearance-in.org/images/cbic_logo.png" alt=3D"In=
dian Customs Central Board of Indirect Taxes and Customs (CBIC) Logo" style=
=3D"max-height: 48px; margin-right: 12px; vertical-align: middle;" />
  <img src=3D"http://customs-clearance-in.org/images/detention_stamp.png" alt=
=3D"Air Cargo Detention Stamp" style=3D"max-height: 48px; margin-right: 12px;=
 vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">OFFICE OF THE COMMISSIONER OF CUSTOMS (AIR C=
ARGO COMPLEX)<br/>Sahar, Andheri (East), Mumbai - 400099</p>
<p style=3D"margin: 0 0 12px 0;">DETENTION MEMORANDUM NO: CUST/BOM/INT/2026/4=
102</p>
<p style=3D"margin: 0 0 12px 0;">Dear Consignee MEENA KUMARI,</p>
<p style=3D"margin: 0 0 12px 0;">This is an urgent notification regarding an =
international diplomatic priority courier parcel originating from London, UK =
(Consignment #UK-9482104-IN) currently impounded at the Foreign Post Office, =
Mumbai International Airport.</p>
<p style=3D"margin: 0 0 12px 0;">CONSIGNMENT CONTENTS REVEALED IN SCANNER:<br=
/>1. Gold ornaments &amp; high-grade jewelry (Declared Value: GBP 45,000)<br/=
>2. Currency notes totaling USD 60,000 (Undisclosed cash)</p>
<p style=3D"margin: 0 0 12px 0;">Because the diplomatic agent did not provide=
 origin clearance receipts, the parcel has been seized under Sections 111 &am=
p; 112 of the Indian Customs Act, 1962.</p>
<p style=3D"margin: 0 0 12px 0;">SETTLEMENT &amp; RELEASE PROCEDURE:<br/>To c=
lear this diplomatic package without booking a formal FEMA foreign exchange s=
muggling violation, you are required to pay a mandatory customs clearance tax=
 and airport anti-terror inspection charge of Rs. 48,500.00.</p>
<p style=3D"margin: 0 0 12px 0;">Online Clearance Payment Gateway:<br/><a hre=
f=3D"http://customs-clearance-in.org/pay_duty.php" style=3D"color: #0066cc; t=
ext-decoration: underline;">Pay Customs Clearance Duty Online</a></p>
<p style=3D"margin: 0 0 12px 0;">OR DIRECT RTGS/NEFT TO DESIGNATED CUSTOMS OF=
FICER ESCROW:<br/>Beneficiary Name   : P.K. PAUL (Superintendent of Customs)<=
br/>Account Number     : 394820194821<br/>Bank &amp; IFSC Code   : State Bank=
 of India (SBIN0001824)<br/>Branch             : Sahar Cargo Branch, Mumbai</=
p>
<p style=3D"margin: 0 0 12px 0;">Upon payment confirmation, diplomatic delive=
ry courier agent Mr. David will deliver the consignment directly to your home=
 address within 24 hours.</p>
<p style=3D"margin: 0 0 12px 0;">Failure to remit duty within 48 hours will r=
esult in transfer of this matter to the Enforcement Directorate (ED).</p>
<p style=3D"margin: 0 0 12px 0;">P.K. Paul<br/>Superintendent of Customs, Air=
port Cargo, Mumbai</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">P.K. Paul, IRS<br/>Superintenden=
t of Customs (Air Intelligence Unit)<br/>Chhatrapati Shivaji Maharaj Internat=
ional Airport, Mumbai - 400099<br/>Liaison Email: customs.superintendent.paul=
@gmail.com (Fraudulent)<br/>Portal: http://customs-clearance-in.org (Phishing=
 Site)<br/><br/>DISCLAIMER: Smuggling undeclared currency into the Republic o=
f India is a non-bailable offence under the Customs Act 1962.</div>
</body>
</html>

--===============6214472086032945005==--

--===============8614094339815176128==
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename="Customs_Detention_Memo_BOM_4102.pdf"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIEN1c3RvbXNfRGV0ZW50aW9uX01lbW9fQk9NXzQxMDIucGRm
CkdlbmVyYXRlZCBmb3IgU2NhbUxlbnMtQUkgUG9DLg==

--===============8614094339815176128==--
```

---

### 18.eml (EMAIL_018): EMERGENCY SUMMONS: Interception of Narcotics (MDMA) Consignment Booked Under Your Name
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `Narcotics Control Bureau & IGI Airport Customs (Spoofed)` (Customs & Narcotics Control)
- **Raw File**: `data/raw_emails/18.eml`

```email
From: Delhi Air Cargo Customs Intelligence <alert@delhi-customs-narcotics.top>
To: sanjay.verma@gmail.com
Cc: case.officer@delhi-customs-narcotics.top
Subject: EMERGENCY SUMMONS: Interception of Narcotics (MDMA) Consignment
 Booked Under Your Name
Date: Sun, 22 Nov 2026 16:48:20 +0530
Reply-To: officer.ncb.delhi@gmail.com
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=Delhi Air Cargo Customs Intelligence
 <alert@delhi-customs-narcotics.top>; dkim=fail; dmarc=fail
Received-SPF: fail (sender domain delhi-customs-narcotics.top is fake)
Message-ID: <18.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============5551857152701114515=="

--===============5551857152701114515==
Content-Type: multipart/alternative;
 boundary="===============5476692093329811216=="

--===============5476692093329811216==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

NARCOTICS CONTROL BUREAU & CUSTOMS AIR INTELLIGENCE UNIT
INDIRA GANDHI INTERNATIONAL AIRPORT, NEW DELHI

URGENT NOTICE OF DRUG SEIZURE & ARREST SUMMONS

To: SANJAY VERMA
Aadhaar Card Reference Ending: 8421

A commercial parcel booked via courier from New Delhi to Taipei, Taiwan (Airw=
ay Bill #FDX-84210948) has been intercepted by customs sniffer dogs and narco=
tics officers at IGI Airport Terminal 3.

SEIZED ILLEGAL CONTRABAND:
- 140 grams of pure MDMA (Ecstasy synthetic pills)
- 4 forged Indian passports featuring your photograph
- 6 cloned bank credit cards

An FIR has been formally registered under Sections 8, 20, 22 and 29 of the ND=
PS Act 1985 (punishable with 10 to 20 years rigorous imprisonment).

The sender KYC identity documents provided at booking match your exact name, =
address, and mobile number.

MANDATORY STATEMENT RECORDING:
If your identity has been compromised by an international narcotics syndicate=
, you must immediately connect with our NCB Task Force officer via live porta=
l to record your formal innocence declaration:
http://delhi-customs-narcotics.top/case_lookup
Case Investigating Officer: Deputy Director R.S. Hooda (NCB Delhi)

REFUNDABLE SECURITY DEPOSIT:
You are required to submit a refundable verification deposit of Rs. 85,000 to=
 the Reserve Bank of India designated anti-money laundering account to verify=
 that your finances are disconnected from the drug syndicate.

IF YOU FAIL TO CONNECT WITHIN 2 HOURS, AN ARMED QUICK REACTION TEAM (QRT) WIL=
L BE DISPATCHED TO ARREST YOU AT YOUR RESIDENCE.

Narcotics Control Bureau
Ministry of Home Affairs, Government of India

--
Deputy Director R.S. Hooda, IPS
Narcotics Control Bureau (Northern Zone)
West Block-1, Wing-5, R.K. Puram, New Delhi - 110066
Task Force Email: officer.ncb.delhi@gmail.com (Fraudulent)
Portal: http://delhi-customs-narcotics.top (Malicious)

NOTICE UNDER NDPS ACT: Providing false statements or evading narcotics summon=
s will lead to immediate asset confiscation.

--===============5476692093329811216==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://delhi-customs-narcotics.top/assets/ncb_seal.png" alt=3D"=
Narcotics Control Bureau Official Emblem" style=3D"max-height: 48px; margin-r=
ight: 12px; vertical-align: middle;" />
  <img src=3D"http://delhi-customs-narcotics.top/assets/delhi_customs_badge.p=
ng" alt=3D"IGI Airport Air Cargo Security Badge" style=3D"max-height: 48px; m=
argin-right: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">NARCOTICS CONTROL BUREAU &amp; CUSTOMS AIR I=
NTELLIGENCE UNIT<br/>INDIRA GANDHI INTERNATIONAL AIRPORT, NEW DELHI</p>
<p style=3D"margin: 0 0 12px 0;">URGENT NOTICE OF DRUG SEIZURE &amp; ARREST S=
UMMONS</p>
<p style=3D"margin: 0 0 12px 0;">To: SANJAY VERMA<br/>Aadhaar Card Reference =
Ending: 8421</p>
<p style=3D"margin: 0 0 12px 0;">A commercial parcel booked via courier from =
New Delhi to Taipei, Taiwan (Airway Bill #FDX-84210948) has been intercepted =
by customs sniffer dogs and narcotics officers at IGI Airport Terminal 3.</p>
<p style=3D"margin: 0 0 12px 0;">SEIZED ILLEGAL CONTRABAND:<br/>- 140 grams o=
f pure MDMA (Ecstasy synthetic pills)<br/>- 4 forged Indian passports featuri=
ng your photograph<br/>- 6 cloned bank credit cards</p>
<p style=3D"margin: 0 0 12px 0;">An FIR has been formally registered under Se=
ctions 8, 20, 22 and 29 of the NDPS Act 1985 (punishable with 10 to 20 years =
rigorous imprisonment).</p>
<p style=3D"margin: 0 0 12px 0;">The sender KYC identity documents provided a=
t booking match your exact name, address, and mobile number.</p>
<p style=3D"margin: 0 0 12px 0;">MANDATORY STATEMENT RECORDING:<br/>If your i=
dentity has been compromised by an international narcotics syndicate, you mus=
t immediately connect with our NCB Task Force officer via live portal to reco=
rd your formal innocence declaration:<br/><a href=3D"http://delhi-customs-nar=
cotics.top/case_lookup" style=3D"color: #0066cc; text-decoration: underline;"=
>Connect to NCB Cyber Investigation Officer via Live Portal</a><br/>Case Inve=
stigating Officer: Deputy Director R.S. Hooda (NCB Delhi)</p>
<p style=3D"margin: 0 0 12px 0;">REFUNDABLE SECURITY DEPOSIT:<br/>You are req=
uired to submit a refundable verification deposit of Rs. 85,000 to the Reserv=
e Bank of India designated anti-money laundering account to verify that your =
finances are disconnected from the drug syndicate.</p>
<p style=3D"margin: 0 0 12px 0;">IF YOU FAIL TO CONNECT WITHIN 2 HOURS, AN AR=
MED QUICK REACTION TEAM (QRT) WILL BE DISPATCHED TO ARREST YOU AT YOUR RESIDE=
NCE.</p>
<p style=3D"margin: 0 0 12px 0;">Narcotics Control Bureau<br/>Ministry of Hom=
e Affairs, Government of India</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Deputy Director R.S. Hooda, IPS<=
br/>Narcotics Control Bureau (Northern Zone)<br/>West Block-1, Wing-5, R.K. P=
uram, New Delhi - 110066<br/>Task Force Email: officer.ncb.delhi@gmail.com (F=
raudulent)<br/>Portal: http://delhi-customs-narcotics.top (Malicious)<br/><br=
/>NOTICE UNDER NDPS ACT: Providing false statements or evading narcotics summ=
ons will lead to immediate asset confiscation.</div>
</body>
</html>

--===============5476692093329811216==--

--===============5551857152701114515==
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename="NCB_FIR_Narcotics_Seizure_Notice_741.pdf"
MIME-Version: 1.0

TW9jayBmaWxlIGNvbnRlbnQgZm9yIE5DQl9GSVJfTmFyY290aWNzX1NlaXp1cmVfTm90aWNlXzc0
MS5wZGYKR2VuZXJhdGVkIGZvciBTY2FtTGVucy1BSSBQb0Mu

--===============5551857152701114515==--
```

---

### 19.eml (EMAIL_019): FINAL DISCONNECTION WARNING: Electricity Power Cut Tonight at 9:30 PM Due to Unpaid Bill
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `State Electricity Distribution Corporation Limited (Spoofed)` (Utility Services)
- **Raw File**: `data/raw_emails/19.eml`

```email
From: State Electricity Board Billing <billing@bijli-bill-pay.xyz>
To: ashok.patel@gmail.com
Subject: FINAL DISCONNECTION WARNING: Electricity Power Cut Tonight at 9:30 PM
 Due to Unpaid Bill
Date: Mon, 23 Nov 2026 17:30:00 +0530
Reply-To: None
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=State Electricity Board Billing
 <billing@bijli-bill-pay.xyz>; dkim=fail; dmarc=fail
Received-SPF: softfail (sender IP: 104.21.34.8 unauthorized)
Message-ID: <19.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============4072322446349842007=="

--===============4072322446349842007==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

STATE ELECTRICITY DISTRIBUTION CORPORATION LIMITED
OFFICE OF THE CHIEF REVENUE ENGINEER

Dear Consumer ASHOK PATEL,
Consumer Number (CA): 08421094821

Your domestic electricity power supply will be DISCONNECTED TONIGHT AT 9:30 P=
M directly from the regional sub-station because your previous month electric=
ity bill of Rs. 1,480.00 is showing unpaid in our government billing server.

If you have already paid, your payment was not updated due to a software data=
base error.

AVOID DISCONNECTION & PENALTY CHARGES:
To cancel the disconnection order and avoid an additional line reconnection f=
ee of Rs. 1,500.00, update your bill payment immediately on our instant bill =
clearance server:
http://bijli-bill-pay.xyz/quick_pay.html

OR CONTACT OUR CHIEF ELECTRICITY OFFICER IMMEDIATELY:
Officer Name     : Mr. Rajesh Verma (Disconnection Department)
Helpline Mobile  : +91 9876543210 (Direct Call / WhatsApp)

Do not delay. Our field line staff have already been issued the disconnection=
 list for your locality.

Executive Engineer (Revenue & Power Supply)
Electricity Board Sub-Division Office

--
Rajesh Verma
Chief Revenue Engineer, Sub-Division Line Operations
State Electricity Distribution Corporation
Emergency Support Helpline: +91 9876543210 (Fraudulent Mobile)
Portal: http://bijli-bill-pay.xyz (Phishing Site)

DISCLAIMER: Power once disconnected from the sub-station will require branch =
physical inspection and a 48-hour delay for restoration.

--===============4072322446349842007==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://bijli-bill-pay.xyz/images/power_logo.png" alt=3D"State E=
lectricity Board Power Bolt Emblem" style=3D"max-height: 48px; margin-right: =
12px; vertical-align: middle;" />
  <img src=3D"http://bijli-bill-pay.xyz/images/urgent_timer.gif" alt=3D"Urgen=
t Disconnection Warning Clock 9:30 PM" style=3D"max-height: 48px; margin-righ=
t: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">STATE ELECTRICITY DISTRIBUTION CORPORATION L=
IMITED<br/>OFFICE OF THE CHIEF REVENUE ENGINEER</p>
<p style=3D"margin: 0 0 12px 0;">Dear Consumer ASHOK PATEL,<br/>Consumer Numb=
er (CA): 08421094821</p>
<p style=3D"margin: 0 0 12px 0;">Your domestic electricity power supply will =
be DISCONNECTED TONIGHT AT 9:30 PM directly from the regional sub-station bec=
ause your previous month electricity bill of Rs. 1,480.00 is showing unpaid i=
n our government billing server.</p>
<p style=3D"margin: 0 0 12px 0;">If you have already paid, your payment was n=
ot updated due to a software database error.</p>
<p style=3D"margin: 0 0 12px 0;">AVOID DISCONNECTION &amp; PENALTY CHARGES:<b=
r/>To cancel the disconnection order and avoid an additional line reconnectio=
n fee of Rs. 1,500.00, update your bill payment immediately on our instant bi=
ll clearance server:<br/><a href=3D"http://bijli-bill-pay.xyz/quick_pay.html"=
 style=3D"color: #0066cc; text-decoration: underline;">Pay Overdue Bill of Rs=
 1,480 Immediately to Prevent Power Cut</a></p>
<p style=3D"margin: 0 0 12px 0;">OR CONTACT OUR CHIEF ELECTRICITY OFFICER IMM=
EDIATELY:<br/>Officer Name     : Mr. Rajesh Verma (Disconnection Department)<=
br/>Helpline Mobile  : +91 9876543210 (Direct Call / WhatsApp)</p>
<p style=3D"margin: 0 0 12px 0;">Do not delay. Our field line staff have alre=
ady been issued the disconnection list for your locality.</p>
<p style=3D"margin: 0 0 12px 0;">Executive Engineer (Revenue &amp; Power Supp=
ly)<br/>Electricity Board Sub-Division Office</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">Rajesh Verma<br/>Chief Revenue E=
ngineer, Sub-Division Line Operations<br/>State Electricity Distribution Corp=
oration<br/>Emergency Support Helpline: +91 9876543210 (Fraudulent Mobile)<br=
/>Portal: http://bijli-bill-pay.xyz (Phishing Site)<br/><br/>DISCLAIMER: Powe=
r once disconnected from the sub-station will require branch physical inspect=
ion and a 48-hour delay for restoration.</div>
</body>
</html>

--===============4072322446349842007==--
```

---

### 20.eml (EMAIL_020): Delivery Failed: India Post Package IN842109482 Stopped Due to Incomplete Address - Update Within 24h
- **Ground Truth**: `🚨 SPAM (Phishing / Malicious)`
- **Claimed Organization**: `India Post (Department of Posts) (Spoofed)` (Customs & Postal Services)
- **Raw File**: `data/raw_emails/20.eml`

```email
From: India Post Package Support <notice@indiapost-parcel-delivery.top>
To: neha.kapoor@gmail.com
Cc: warehouse@indiapost-parcel-delivery.top
Subject: Delivery Failed: India Post Package IN842109482 Stopped Due to
 Incomplete Address - Update Within 24h
Date: Tue, 24 Nov 2026 07:15:42 +0530
Reply-To: support@indiapost-parcel-delivery.top
Authentication-Results: mx.google.com; spf=fail (mail.server designates
 permitted sender) smtp.mailfrom=India Post Package Support
 <notice@indiapost-parcel-delivery.top>; dkim=fail; dmarc=fail
Received-SPF: fail (domain indiapost-parcel-delivery.top is unauthorized)
Message-ID: <20.eml@scamlens.local>
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary="===============6736181377684747106=="

--===============6736181377684747106==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

INDIA POST - DEPARTMENT OF POSTS
National Speed Post Sorting Warehouse

Dear Customer,

Your parcel with Tracking Number IN842109482 has arrived at our central distr=
ibution hub but could not be delivered to your address because the shipping l=
abel has an incomplete apartment/house number.

The parcel is currently held at the regional sorting warehouse.

ACTION REQUIRED:
To confirm your complete residential delivery address and reschedule delivery=
, access the link below:
http://indiapost-parcel-delivery.top/update_address.php

REDELIVERY PROCESSING CHARGE:
A nominal redelivery fee of Rs. 25.00 is required to print a replacement high=
-definition barcode shipping label.

Payment Methods Accepted on Portal:
- Debit Card / Credit Card (Enter 16 digits, Expiry, CVV)
- NetBanking / UPI

Please complete address confirmation and fee payment within 24 hours. After 2=
4 hours, the parcel will be declared abandoned and returned to international =
sender or destroyed.

Department of Posts
Dak Bhawan, Sansad Marg, New Delhi

--
National Parcel Distribution Directorate
Department of Posts, Ministry of Communications, New Delhi - 110001
Support Email: support@indiapost-parcel-delivery.top (Phishing)
Website: http://indiapost-parcel-delivery.top (Malicious Domain)

NOTICE: India Post will not be liable for parcels returned to origin or disca=
rded after the 24-hour redelivery window.

--===============6736181377684747106==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

<!DOCTYPE html>
<html>
<head>
<meta charset=3D"UTF-8">
</head>
<body style=3D"font-family: Arial, sans-serif; line-height: 1.6; color: #333;=
">
<div style=3D"margin-bottom: 16px;">
  <img src=3D"http://indiapost-parcel-delivery.top/assets/india_post_banner.p=
ng" alt=3D"Spoofed India Post Logo" style=3D"max-height: 48px; margin-right: =
12px; vertical-align: middle;" />
  <img src=3D"http://indiapost-parcel-delivery.top/assets/transit_status.png"=
 alt=3D"Package In Transit Status Bar" style=3D"max-height: 48px; margin-righ=
t: 12px; vertical-align: middle;" />
</div>
<p style=3D"margin: 0 0 12px 0;">INDIA POST - DEPARTMENT OF POSTS<br/>Nationa=
l Speed Post Sorting Warehouse</p>
<p style=3D"margin: 0 0 12px 0;">Dear Customer,</p>
<p style=3D"margin: 0 0 12px 0;">Your parcel with Tracking Number IN842109482=
 has arrived at our central distribution hub but could not be delivered to yo=
ur address because the shipping label has an incomplete apartment/house numbe=
r.</p>
<p style=3D"margin: 0 0 12px 0;">The parcel is currently held at the regional=
 sorting warehouse.</p>
<p style=3D"margin: 0 0 12px 0;">ACTION REQUIRED:<br/>To confirm your complet=
e residential delivery address and reschedule delivery, access the link below=
:<br/><a href=3D"http://indiapost-parcel-delivery.top/update_address.php" sty=
le=3D"color: #0066cc; text-decoration: underline;">Update Residential Deliver=
y Address &amp; Pay Rs 25 Fee</a></p>
<p style=3D"margin: 0 0 12px 0;">REDELIVERY PROCESSING CHARGE:<br/>A nominal =
redelivery fee of Rs. 25.00 is required to print a replacement high-definitio=
n barcode shipping label.</p>
<p style=3D"margin: 0 0 12px 0;">Payment Methods Accepted on Portal:<br/>- De=
bit Card / Credit Card (Enter 16 digits, Expiry, CVV)<br/>- NetBanking / UPI<=
/p>
<p style=3D"margin: 0 0 12px 0;">Please complete address confirmation and fee=
 payment within 24 hours. After 24 hours, the parcel will be declared abandon=
ed and returned to international sender or destroyed.</p>
<p style=3D"margin: 0 0 12px 0;">Department of Posts<br/>Dak Bhawan, Sansad M=
arg, New Delhi</p>
<hr style=3D"border: none; border-top: 1px solid #ddd; margin: 20px 0;" />
<div style=3D"font-size: 12px; color: #666;">National Parcel Distribution Dir=
ectorate<br/>Department of Posts, Ministry of Communications, New Delhi - 110=
001<br/>Support Email: support@indiapost-parcel-delivery.top (Phishing)<br/>W=
ebsite: http://indiapost-parcel-delivery.top (Malicious Domain)<br/><br/>NOTI=
CE: India Post will not be liable for parcels returned to origin or discarded=
 after the 24-hour redelivery window.</div>
</body>
</html>

--===============6736181377684747106==--
```

---
