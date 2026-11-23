"""Generate comprehensive 20 sample emails (5 HAM, 15 SPAM) in Markdown (.md) format.

Includes: Subject, To, From, CC, Reply-To, Date & Time, Email Body,
Signatures, External Links, Images, Attachments, Auth Headers.
"""

from pathlib import Path

emails_data = [
    # =========================================================================
    # HAM EMAILS (5 Legitimate Emails)
    # =========================================================================
    {
        "id": "EMAIL_001",
        "label": "HAM (Legitimate)",
        "category": "Banking",
        "sub_category": "Monthly Credit Card e-Statement",
        "claimed_org": "HDFC Bank Limited",
        "subject": "Your HDFC Bank Credit Card e-Statement for Card ending 4892 (Billing Cycle: Sept 2026)",
        "from_addr": "HDFC Bank NetBanking Alerts <alerts@hdfcbank.net>",
        "to_addr": "customer.prakash@gmail.com",
        "cc_addr": "None",
        "reply_to": "customer.service@hdfcbank.com",
        "date_time": "Sat, 05 Oct 2026 04:15:30 +0530 (IST)",
        "spf": "pass (sender IP: 175.100.162.24 is authorized by hdfcbank.net)",
        "dkim": "pass (signature verified for domain hdfcbank.net, selector: hdfc2025)",
        "dmarc": "pass (p=reject, pct=100, strict alignment satisfied)",
        "attachments": [
            {
                "filename": "HDFC_Statement_Sep2026_4892.pdf",
                "mime_type": "application/pdf",
                "size": "248 KB",
                "is_password_protected": True,
                "password_hint": "First 4 letters of name in lowercase + DDMM of birth",
            }
        ],
        "images": [
            {
                "alt": "HDFC Bank Official Blue Logo",
                "url": "https://www.hdfcbank.com/content/api/contentstream-id/723fb80a-2dde-42a3-9793-7ae1be57c87f/2c9c7f68-7c85-4dbb-8b5d-007a0cbe6a8e/logo.png",
            },
            {
                "alt": "VeriSign SSL Secured Email Shield",
                "url": "https://www.hdfcbank.com/assets/images/security-guarantee-shield.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "HDFC Bank NetBanking Portal",
                "url": "https://netbanking.hdfcbank.com",
                "is_phishing": False,
            },
            {
                "anchor_text": "Pay Credit Card Bill Online",
                "url": "https://www.hdfcbank.com/personal/pay/cards/credit-cards",
                "is_phishing": False,
            },
            {
                "anchor_text": "RBI Integrated Banking Ombudsman Scheme",
                "url": "https://cms.rbi.org.in",
                "is_phishing": False,
            },
        ],
        "body_plain": """Dear PRAKASH R,

Thank you for banking with HDFC Bank.

Please find attached your password-protected monthly e-Statement for HDFC Bank Credit Card ending with 4892 for the billing cycle ending 04-Oct-2026.

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
The attached statement is password-protected. Your password is your 4-character Date & Month of Birth (DDMM) followed by the last 4 digits of your Credit Card number.
Example: If your Date of Birth is 15th August and your card number ends with 4892, your password is: 15084892.

PAYMENT OPTIONS:
You can settle your dues seamlessly using:
1. HDFC Bank NetBanking / MobileBanking App: https://netbanking.hdfcbank.com
2. Auto-Debit instructions from your HDFC savings account
3. UPI / BillDesk / BBPS using your card number

SECURITY NOTICE:
HDFC Bank never asks for your NetBanking password, OTP, Credit Card PIN, or CVV over email, phone call, or SMS. If you notice any suspicious activity, immediately call our 24x7 toll-free helpline at 1800 202 6161.""",
        "signature": """Warm Regards,
Credit Card Customer Services Team
HDFC Bank Limited
Registered Office: HDFC Bank House, Senapati Bapat Marg, Lower Parel (West), Mumbai - 400013
CIN: L65920MH1994PLC080618 | Website: https://www.hdfcbank.com
National Cyber Crime Helpline: 1930 | RBI Banking Ombudsman: https://cms.rbi.org.in

DISCLAIMER:
This email and any files transmitted with it are confidential and intended solely for the use of the individual to whom they are addressed. If you have received this transmission in error, please notify the sender immediately and delete this email from your system.""",
    },
    {
        "id": "EMAIL_002",
        "label": "HAM (Legitimate)",
        "category": "Banking",
        "sub_category": "NEFT Outward Debit Notification",
        "claimed_org": "State Bank of India (SBI)",
        "subject": "Debit Alert: Your SBI A/C XXXXXXXX4012 has been debited by Rs 25,000.00 via NEFT",
        "from_addr": "SBI Internet Banking Alerts <donotreply@sbi.co.in>",
        "to_addr": "anita.deshmukh@gmail.com",
        "cc_addr": "None",
        "reply_to": "None",
        "date_time": "Wed, 16 Oct 2026 14:22:15 +0530 (IST)",
        "spf": "pass (sender IP: 115.112.234.18 is authorized by sbi.co.in)",
        "dkim": "pass (signature verified for domain sbi.co.in, selector: sbi2024)",
        "dmarc": "pass (p=reject, strict alignment satisfied)",
        "attachments": [],
        "images": [
            {
                "alt": "SBI Official Blue Keyhole Emblem",
                "url": "https://www.onlinesbi.sbi/sbijava/images/sbi_logo.png",
            }
        ],
        "external_links": [
            {
                "anchor_text": "SBI Official NetBanking (onlinesbi.sbi)",
                "url": "https://www.onlinesbi.sbi",
                "is_phishing": False,
            },
            {
                "anchor_text": "SBI Customer Grievance Redressal",
                "url": "https://sbi.co.in/web/customer-care",
                "is_phishing": False,
            },
        ],
        "body_plain": """Dear Customer,

Your State Bank of India Account XXXXXXXX4012 has been debited by Rs. 25,000.00 on 16-Oct-2026 14:21:42 IST towards an outward NEFT transfer.

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
1. Block your Internet Banking profile by sending SMS 'BLOCK <Account No>' to 567676.
2. Dial our 24x7 toll-free helpline numbers: 1800-11-2211 / 1800-425-3800.
3. Lock your Debit Card instantly via the YONO SBI App.

Always ensure the URL in your browser address bar is strictly: https://www.onlinesbi.sbi""",
        "signature": """Yours faithfully,
Chief General Manager (Digital Banking)
State Bank of India
Corporate Centre: State Bank Bhavan, Madame Cama Road, Nariman Point, Mumbai - 400021
Customer Care Toll-Free: 1800 1234 / 1800 2100 | Email: customercare@sbi.co.in

State Bank of India - The Banker to Every Indian""",
    },
    {
        "id": "EMAIL_003",
        "label": "HAM (Legitimate)",
        "category": "Insurance",
        "sub_category": "Annual Policy Premium Due Notice",
        "claimed_org": "Life Insurance Corporation of India (LIC)",
        "subject": "LIC Policy Premium Due Notice - Policy No. 842109482 (Plan: Jeevan Labh)",
        "from_addr": "LIC Portal Customer Services <customer.service@licindia.in>",
        "to_addr": "vikram.malhotra@yahoo.com",
        "cc_addr": "branch.882@licindia.in",
        "reply_to": "customer.service@licindia.in",
        "date_time": "Mon, 02 Sep 2026 09:00:12 +0530 (IST)",
        "spf": "pass (sender IP: 121.241.242.70 is authorized by licindia.in)",
        "dkim": "pass (signature verified for domain licindia.in, selector: lic2025)",
        "dmarc": "pass (p=quarantine, alignment pass)",
        "attachments": [],
        "images": [
            {
                "alt": "LIC Hands with Flame Emblem (Yogakshemam Vahamyaham)",
                "url": "https://licindia.in/o/lic-theme/images/lic_logo.png",
            }
        ],
        "external_links": [
            {
                "anchor_text": "LIC Official Direct Pay Portal",
                "url": "https://licindia.in/Home/Pay-Premium-Online",
                "is_phishing": False,
            },
            {
                "anchor_text": "LIC Customer Portal Login",
                "url": "https://customer.onlinelic.in",
                "is_phishing": False,
            },
        ],
        "body_plain": """Dear Policyholder VIKRAM MALHOTRA,

Greetings from Life Insurance Corporation of India.

This is to inform you that the renewal premium for your LIC Life Insurance Policy is due for payment.

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
1. Pay directly without registration: https://licindia.in/Home/Pay-Premium-Online
2. Pay via LIC Customer Portal App (Android / iOS): https://customer.onlinelic.in
3. Authorized digital billers: NACH Mandate, UPI, NetBanking, BBPS, or Authorized Bank Counters.

IMPORTANT SAFETY NOTICE:
LIC never asks policyholders to transfer funds into any individual's personal savings account or personal UPI VPA handle. Never surrender your policy based on false promises of high bonus returns or lottery payouts from callers claiming to represent IRDAI or LIC.""",
        "signature": """Yours sincerely,
Divisional Manager (Customer Relationship Management)
Life Insurance Corporation of India
Divisional Office: Yogakshema Building, West Wing, J.B. Marg, Mumbai - 400021
LIC Call Centre 24x7: 022-68276827 | IRDAI Reg No: 512

LIC of India - Har Pal Aapke Saath""",
    },
    {
        "id": "EMAIL_004",
        "label": "HAM (Legitimate)",
        "category": "Income Tax",
        "sub_category": "Official Intimation u/s 143(1)",
        "claimed_org": "Income Tax Department, Ministry of Finance, Govt of India",
        "subject": "Intimation Order u/s 143(1) of the Income-tax Act, 1961 for PAN: AXXXX1234X - AY 2024-25",
        "from_addr": "Income Tax Department CPC Bengaluru <donotreply@incometax.gov.in>",
        "to_addr": "sunita.verma@gmail.com",
        "cc_addr": "None",
        "reply_to": "None",
        "date_time": "Thu, 22 Aug 2026 11:45:00 +0530 (IST)",
        "spf": "pass (sender IP: 164.100.14.92 is authorized by incometax.gov.in)",
        "dkim": "pass (signature verified for domain incometax.gov.in, selector: itdcpc2024)",
        "dmarc": "pass (p=reject, strict alignment satisfied)",
        "attachments": [
            {
                "filename": "PAN_AXXXX1234X_AY2024-25_143_1.pdf",
                "mime_type": "application/pdf",
                "size": "512 KB",
                "is_password_protected": True,
                "password_hint": "PAN in lowercase + Date of Birth in DDMMYYYY format",
            }
        ],
        "images": [
            {
                "alt": "Ashoka Lion Capital National Emblem of India",
                "url": "https://www.incometax.gov.in/iec/foportal/sites/default/files/emblem-dark.png",
            },
            {
                "alt": "Income Tax Department Official Crest",
                "url": "https://www.incometax.gov.in/iec/foportal/sites/default/files/itd-logo.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Official e-Filing Portal (incometax.gov.in)",
                "url": "https://www.incometax.gov.in/iec/foportal/",
                "is_phishing": False,
            }
        ],
        "body_plain": """Dear SUNITA VERMA,

PAN: AXXXX1234X
Assessment Year: 2024-25
Acknowledgement Number: 829104820194821
Communication Ref No: CPC/2425/A2/829104820194821

The Centralized Processing Centre (CPC), Bengaluru has processed your electronically filed Income Tax Return for Assessment Year 2024-25 under section 143(1) of the Income-tax Act, 1961.

SUMMARY OF COMPUTATION:
--------------------------------------------------
Total Tax & Interest Payable as per Return : Rs. 0
Total Tax & Interest Determined by CPC     : Rs. 0
Net Refund Determined (Including 244A Int) : Rs. 14,280.00
Refund Disbursement Channel                : Direct Credit via NECS/RTGS
Designated Pre-Validated Bank Account      : State Bank of India (A/C ending 5821)
--------------------------------------------------

The detailed computation sheet is enclosed in the attached password-protected PDF document.
Password Format: Your 10-digit PAN in lowercase followed by your Date of Birth in DDMMYYYY format.
Example: If PAN is ABCDE1234F and DOB is 01-Jan-1985, password is: abcde1234f01011985.

You can inspect all processed returns and refund statuses by logging in to the e-Filing portal:
https://www.incometax.gov.in/iec/foportal/

STATUTORY CAUTION:
The Income Tax Department NEVER asks taxpayers for their bank account passwords, debit/credit card PINs, or OTPs. All official communications carry a unique Document Identification Number (DIN) verifiable on the e-Filing portal.""",
        "signature": """Deputy Commissioner of Income Tax
Centralized Processing Centre (CPC)
Income Tax Department, Post Bag No. 1, Electronic City Post Office, Bengaluru - 560100, Karnataka
e-Filing Helpdesk Toll-Free: 1800 103 0025 / 1800 419 0025

Government of India - Ministry of Finance - Central Board of Direct Taxes (CBDT)""",
    },
    {
        "id": "EMAIL_005",
        "label": "HAM (Legitimate)",
        "category": "Customs & Postal Services",
        "sub_category": "Official Consignment Tracking Dispatch Alert",
        "claimed_org": "Department of Posts, Ministry of Communications, Govt of India",
        "subject": "Speed Post Consignment Dispatched: Article No. EK829104821IN (From: NSDL e-Governance)",
        "from_addr": "Department of Posts India <tracking@indiapost.gov.in>",
        "to_addr": "dev.kapoor@gmail.com",
        "cc_addr": "None",
        "reply_to": "None",
        "date_time": "Fri, 11 Oct 2026 16:10:45 +0530 (IST)",
        "spf": "pass (sender IP: 164.100.89.44 is authorized by indiapost.gov.in)",
        "dkim": "pass (signature verified for domain indiapost.gov.in, selector: postal2024)",
        "dmarc": "pass (p=reject, strict alignment satisfied)",
        "attachments": [],
        "images": [
            {
                "alt": "India Post Iconic Red Wing Logo",
                "url": "https://www.indiapost.gov.in/_layouts/15/images/DOP.Portal.UILibrary/India_Post_Logo_with_Text.svg",
            }
        ],
        "external_links": [
            {
                "anchor_text": "Official India Post Consignment Tracking Portal",
                "url": "https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx",
                "is_phishing": False,
            }
        ],
        "body_plain": """Dear Customer,

Your Speed Post article with Tracking Number EK829104821IN has been booked at New Delhi GPO on 11-Oct-2026 15:45:10 IST and dispatched to Mumbai National Sorting Hub (NSH).

CONSIGNMENT INFORMATION:
--------------------------------------------------
Article Tracking Number : EK829104821IN
Sender Details          : National Securities Depository Limited (NSDL)
Destination City & Pin  : Mumbai - 400050
Service Classification  : Domestic Speed Post
Booked At               : New Delhi GPO (110001)
Estimated Delivery Date : 14-Oct-2026
--------------------------------------------------

Track live transit events and delivery status on the official Department of Posts portal:
https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx

CUSTOMER ADVISORY:
India Post delivery personnel collect payments ONLY for articles marked as Cash on Delivery (CoD). India Post never sends SMS or email messages requesting payment of nominal redelivery charges (e.g., Rs. 5 or Rs. 25) through shortened third-party web links. Do not click on unverified links.""",
        "signature": """Postal Operations Directorate
Department of Posts, Ministry of Communications
Dak Bhawan, Sansad Marg, New Delhi - 110001, India
Toll-Free Customer Grievance Helpline: 1800 266 6868 | Email: customer.care@indiapost.gov.in

India Post - Delivering Trust Across Every Village and Town""",
    },

    # =========================================================================
    # SPAM EMAILS (15 Fraudulent / Phishing / Extortion Emails)
    # =========================================================================
    {
        "id": "EMAIL_006",
        "label": "SPAM (Phishing)",
        "category": "Banking",
        "sub_category": "YONO NetBanking Suspension Phishing",
        "claimed_org": "State Bank of India (Spoofed)",
        "subject": "CRITICAL NOTICE: Your SBI YONO Account is Suspended - Immediate KYC Update Required",
        "from_addr": "State Bank of India Online Alerts <no-reply@sbi-kyc-verify.xyz>",
        "to_addr": "target.victim@gmail.com",
        "cc_addr": "None",
        "reply_to": "support-ticket-842@fraud-mailbox.xyz",
        "date_time": "Mon, 18 Nov 2026 10:14:22 +0530 (IST)",
        "spf": "softfail (sender IP: 194.38.20.14 is NOT authorized by sbi.co.in)",
        "dkim": "fail (no valid DKIM signature found for sending domain sbi-kyc-verify.xyz)",
        "dmarc": "fail (unaligned domain; fails DMARC policy check)",
        "attachments": [],
        "images": [
            {
                "alt": "Spoofed SBI YONO Logo Banner",
                "url": "http://sbi-kyc-verify.xyz/assets/sbi_yono_banner.png",
            },
            {
                "alt": "Fake RBI Compliance Seal",
                "url": "http://sbi-kyc-verify.xyz/assets/rbi_verified_badge.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Update KYC & Restore YONO Access Now",
                "url": "http://sbi-kyc-verify.xyz/login.php?user=verify",
                "is_phishing": True,
            }
        ],
        "body_plain": """Dear SBI Customer,

Your State Bank of India YONO Internet Banking profile has been TEMPORARILY SUSPENDED due to non-submission of updated Aadhaar card and PAN card biometrics as mandated under RBI Circular RBI/2026-27/89.

IMPACT OF NON-COMPLIANCE:
- All ATM Debit Card cash withdrawals will be blocked tonight at 23:59 IST.
- Inward NEFT/IMPS and UPI transactions on GPay/PhonePe will be declined.
- A penalty surcharge of Rs. 10,000 will be debited from your savings balance.

MANDATORY ACTION:
You must update your KYC details immediately on our secure compliance server:
http://sbi-kyc-verify.xyz/login.php?user=verify

INSTRUCTIONS:
1. Access the link above on your smartphone or PC.
2. Enter your YONO Username, Password, and Profile Password.
3. Submit the 6-digit verification OTP received on your mobile phone to complete synchronization.

Do not ignore this notice. Customer security is our priority.

Sincerely,
SBI Customer Support Unit
State Bank of India, Corporate Centre, Mumbai""",
        "signature": """State Bank of India Online Security Operations
Email: support@sbi-kyc-verify.xyz (Spoofed)
Helpline WhatsApp: +91 9876543210 (Fraudulent)
Address: State Bank Bhavan, Nariman Point, Mumbai - 400021

Note: This automated alert was generated by the SBI Core Banking System. Failure to verify credentials within 24 hours will result in permanent closure of account services.""",
    },
    {
        "id": "EMAIL_007",
        "label": "SPAM (Phishing)",
        "category": "Banking",
        "sub_category": "Reward Points Expiry Phishing & CVV Harvesting",
        "claimed_org": "ICICI Bank (Spoofed)",
        "subject": "Notice: 18,450 ICICI Payback Points Expiring Tonight - Claim Cash Value Rs 9,225 Directly",
        "from_addr": "ICICI Rewards Desk <rewards@icici-point-claim.top>",
        "to_addr": "rohit.sharma@yahoo.co.in",
        "cc_addr": "claims-archive@icici-point-claim.top",
        "reply_to": "claims@icici-point-claim.top",
        "date_time": "Sun, 03 Nov 2026 18:30:10 +0530 (IST)",
        "spf": "fail (sender IP: 45.145.89.112 not authorized by icicibank.com)",
        "dkim": "fail (no cryptographic signature present)",
        "dmarc": "fail (unauthorized sending server)",
        "attachments": [],
        "images": [
            {
                "alt": "Spoofed ICICI Bank Orange Logo",
                "url": "http://icici-point-claim.top/images/icici_logo_orange.png",
            },
            {
                "alt": "Fake 100% Cash Redemption Guarantee Stamp",
                "url": "http://icici-point-claim.top/images/guarantee_seal.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Redeem Rs 9,225 Cash to Account Now",
                "url": "http://icici-point-claim.top/redeem_cash.html",
                "is_phishing": True,
            }
        ],
        "body_plain": """Dear ICICI Bank Cardholder,

Our records indicate that you have 18,450 UNCLAIMED ICICI Bank Payback Reward Points accumulated on your Debit/Credit Card.

These reward points carry a redeemable cash balance of Rs. 9,225.00.

IMPORTANT EXPIRATION WARNING:
As per the revised end-of-year rewards policy, all points earned prior to 2026 are scheduled to EXPIRE TONIGHT AT 11:59 PM. Expired points will be forfeited to the bank pool.

HOW TO CONVERT YOUR REWARD POINTS TO LIQUID CASH:
Click on the direct credit redemption portal below:
http://icici-point-claim.top/redeem_cash.html

3 SIMPLE STEPS TO CREDIT:
1. Open the redemption link above.
2. Enter your 16-digit Card Number, Expiry Date (MM/YY), and 3-digit CVV code.
3. Enter your NetBanking password and submit the verification OTP received on SMS.

The amount of Rs. 9,225.00 will be credited directly to your primary savings account within 10 minutes.

Regards,
ICICI Bank Customer Rewards Division
Bandra Kurla Complex, Mumbai""",
        "signature": """Customer Loyalty & Rewards Wing
ICICI Bank Towers, Bandra-Kurla Complex, Mumbai - 400051
Toll-Free Customer Line: 1800-POINT-ICICI (Fake)
Website: http://icici-point-claim.top (Malicious)

CONFIDENTIALITY NOTICE: This email is confidential and contains proprietary reward entitlement data. If you are not the intended cardholder, immediately delete this communication.""",
    },
    {
        "id": "EMAIL_008",
        "label": "SPAM (Phishing)",
        "category": "Banking",
        "sub_category": "PAN Section 139AA Debit Freeze Scam",
        "claimed_org": "HDFC Bank (Spoofed)",
        "subject": "Final Reminder: Immediate PAN Linking Required for HDFC Bank Account - Debit Freeze Alert",
        "from_addr": "HDFC Bank Compliance Unit <alert@hdfc-pan-update.online>",
        "to_addr": "priya.nair@hotmail.com",
        "cc_addr": "None",
        "reply_to": "support@hdfc-pan-update.online",
        "date_time": "Tue, 29 Oct 2026 12:05:44 +0530 (IST)",
        "spf": "fail (domain hdfc-pan-update.online has no SPF record)",
        "dkim": "fail (unauthorized key)",
        "dmarc": "fail (fails DMARC policy check)",
        "attachments": [],
        "images": [
            {
                "alt": "Spoofed HDFC Bank Header",
                "url": "http://hdfc-pan-update.online/static/hdfc_header.jpg",
            }
        ],
        "external_links": [
            {
                "anchor_text": "Link PAN with HDFC Account Online",
                "url": "http://hdfc-pan-update.online/auth/login",
                "is_phishing": True,
            }
        ],
        "body_plain": """Dear Valued Customer,

This is a mandatory compliance alert from HDFC Bank Risk & Vigilance Department regarding Section 139AA of the Income Tax Act.

Your savings account ending with 1984 has been marked as NON-COMPLIANT due to pending PAN-Aadhaar linking validation on our centralized CBS servers.

CONSEQUENCES OF NON-LINKING STARTING TODAY AT 23:59 IST:
1. Immediate debit freeze on all netbanking, mobile banking, and branch cash withdrawals.
2. Inward NEFT/IMPS and salary credits will be returned to sender.
3. Deduction of a mandatory non-compliance statutory fee of Rs. 2,500 monthly.

Complete your instant biometric linking online without visiting the branch:
http://hdfc-pan-update.online/auth/login

Please keep your Customer ID, NetBanking IPIN, and registered phone number accessible to authorize the instant linkage.

HDFC Bank Risk & Compliance Department
Lower Parel, Mumbai""",
        "signature": """HDFC Bank Vigilance & Compliance Operations
HDFC Bank House, Senapati Bapat Marg, Lower Parel, Mumbai - 400013
Grievance Officer: compliance@hdfc-pan-update.online (Fraudulent)
Customer Safety Line: +91 9123456789 (Fraudulent)

Notice: HDFC Bank will not be responsible for operational losses or penalty charges resulting from failure to update PAN credentials within the deadline.""",
    },
    {
        "id": "EMAIL_009",
        "label": "SPAM (Phishing)",
        "category": "Banking",
        "sub_category": "Credit Limit Enhancement Credential Harvesting",
        "claimed_org": "Axis Bank (Spoofed)",
        "subject": "Congratulations: Your Axis Credit Card limit has been increased to Rs 8,50,000 (Action Required)",
        "from_addr": "Axis Bank Pre-Approved Cards <offers@axis-limit-boost.click>",
        "to_addr": "kunal.sen@gmail.com",
        "cc_addr": "None",
        "reply_to": "None",
        "date_time": "Thu, 17 Oct 2026 15:40:19 +0530 (IST)",
        "spf": "softfail (unauthorized sending IP: 185.220.101.5)",
        "dkim": "fail (no DKIM signature)",
        "dmarc": "fail (fails alignment check)",
        "attachments": [],
        "images": [
            {
                "alt": "Spoofed Axis Bank Burgundy Logo",
                "url": "http://axis-limit-boost.click/assets/axis_logo.png",
            },
            {
                "alt": "Pre-Approved Gold Credit Card Badge",
                "url": "http://axis-limit-boost.click/assets/gold_card_mockup.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Activate New Credit Limit of Rs 8,50,000",
                "url": "http://axis-limit-boost.click/upgrade",
                "is_phishing": True,
            }
        ],
        "body_plain": """Dear Axis Bank Cardholder,

Congratulations! In recognition of your excellent CIBIL credit score and flawless repayment track record, Axis Bank is pleased to offer you an instant pre-approved credit limit enhancement:

OFFER DETAILS:
- Existing Credit Limit   : Rs. 1,50,000.00
- Enhanced Credit Limit   : Rs. 8,50,000.00
- Annual Fee Waiver       : 100% Lifetime Free (LTF)
- Complimentary Benefits  : Unlimited Airport Lounge Access & 5X Reward Points

This promotional limit upgrade is valid for activation only for the next 48 hours.

ACTIVATE YOUR ENHANCED LIMIT NOW:
http://axis-limit-boost.click/upgrade

Please complete validation by entering:
1. 16-digit Axis Bank Credit Card Number
2. Expiry Date & 3-digit CVV
3. NetBanking Login Password
4. Dynamic Authentication OTP

Your enhanced limit will be available immediately upon verification.

Warm Regards,
Cards Division, Axis Bank Limited""",
        "signature": """Axis Bank Credit Card Enhancement Cell
Axis House, C-2, Wadia International Centre, Pandurang Budhkar Marg, Worli, Mumbai - 400025
Helpdesk: support@axis-limit-boost.click (Fake) | Tel: 1800-419-5577 (Spoofed text)

Disclaimer: This email contains pre-approved confidential customer financial offers. Unclaimed upgrades lapse automatically after 48 hours.""",
    },
    {
        "id": "EMAIL_010",
        "label": "SPAM (Phishing)",
        "category": "Banking",
        "sub_category": "Fake Unauthorized Transaction Reversal Lure",
        "claimed_org": "Punjab National Bank (Spoofed)",
        "subject": "ALERT: Unauthorized transfer of Rs. 74,500 debited from your PNB A/C - Cancel Immediately",
        "from_addr": "PNB Anti-Fraud Cell <security@pnb-security-alert.live>",
        "to_addr": "ajay.singh@gmail.com",
        "cc_addr": "disputes@pnb-security-alert.live",
        "reply_to": "fraud-desk@pnb-security-alert.live",
        "date_time": "Mon, 11 Nov 2026 21:18:03 +0530 (IST)",
        "spf": "fail (sender IP 89.248.165.70 not authorized for pnbindia.in)",
        "dkim": "fail (invalid signature)",
        "dmarc": "fail (strict rejection policy triggered)",
        "attachments": [],
        "images": [
            {
                "alt": "Spoofed PNB Maroon Emblem",
                "url": "http://pnb-security-alert.live/pnb_logo.png",
            },
            {
                "alt": "Urgent Red Security Warning Icon",
                "url": "http://pnb-security-alert.live/warning_icon.gif",
            },
        ],
        "external_links": [
            {
                "anchor_text": "CANCEL TRANSACTION & REVERSE DEBIT (Within 10 Mins)",
                "url": "http://pnb-security-alert.live/dispute_transaction.php",
                "is_phishing": True,
            }
        ],
        "body_plain": """CRITICAL SECURITY ALERT - PUNJAB NATIONAL BANK

An online transfer of Rs. 74,500.00 was initiated from your PNB savings account to an unknown cryptocurrency merchant VPA (CRYPTO-EXCHANGE-IN@okaxis) on 11-Nov-2026 21:15:30 IST.

TRANSACTION SUMMARY:
Amount Debited : Rs. 74,500.00
Reference ID   : PNB94821048201
Status         : Pending Clearing

IF YOU DID NOT AUTHORIZE THIS TRANSACTION:
You must cancel this debit immediately before the transaction is finalized by the settlement network.

CLICK HERE TO CANCEL AND RESTORE YOUR BALANCE:
http://pnb-security-alert.live/dispute_transaction.php

Note: Cancellation gateway remains open for only 10 minutes. You will be prompted to enter your NetBanking username, password, and transaction authorization OTP to reverse the charges to your balance.

If you authorized this transfer, no further action is required.

PNB Fraud Risk Management Cell
Dwarka, New Delhi""",
        "signature": """Punjab National Bank - Fraud Risk Management Operations
Head Office: Plot No 4, Sector 10, Dwarka, New Delhi - 110075
Emergency Hotline: 1800-180-2222 (Spoofed text) | Portal: http://pnb-security-alert.live (Malicious)

This is an automated emergency security alert. Punjab National Bank will not be liable for delayed disputes after the 10-minute clearing window.""",
    },
    {
        "id": "EMAIL_011",
        "label": "SPAM (Advance Fee Fraud)",
        "category": "Insurance",
        "sub_category": "Lapsed Policy Unclaimed Bonus Scam",
        "claimed_org": "Life Insurance Corporation of India (Spoofed)",
        "subject": "Approval of Accumulated Lapsed Policy Bonus: Rs. 4,85,000 (Mandatory Action Required)",
        "from_addr": "LIC Claims Settlement Officer <claims@lic-bonus-settlement.xyz>",
        "to_addr": "ramesh.babu@gmail.com",
        "cc_addr": "None",
        "reply_to": "licofficer.sharma98@gmail.com",
        "date_time": "Wed, 06 Nov 2026 11:12:40 +0530 (IST)",
        "spf": "fail (unauthorized sender IP)",
        "dkim": "fail (no DKIM signature)",
        "dmarc": "fail (domain mismatch)",
        "attachments": [
            {
                "filename": "LIC_Bonus_Disbursement_Sanction_Letter.pdf",
                "mime_type": "application/pdf",
                "size": "310 KB",
                "is_password_protected": False,
                "password_hint": "None",
            }
        ],
        "images": [
            {
                "alt": "Forged LIC Header with Government of India Seal",
                "url": "http://lic-bonus-settlement.xyz/assets/lic_gold_emblem.jpg",
            }
        ],
        "external_links": [
            {
                "anchor_text": "Download Bonus Disbursement Application Form",
                "url": "http://lic-bonus-settlement.xyz/claim_form",
                "is_phishing": True,
            }
        ],
        "body_plain": """Dear Policyholder RAMESH BABU,

We are pleased to inform you that your dormant LIC policy records have been successfully audited under the Special IRDAI Unclaimed Fund Settlement Scheme 2026.

An accumulated bonus along with maturity interest amounting to Rs. 4,85,000.00 has been sanctioned for direct disbursement to your bank account.

DISBURSEMENT BREAKDOWN:
- Accumulated Loyalty Additions : Rs. 3,10,000.00
- Compound Guaranteed Interest   : Rs. 1,75,000.00
- Total Net Release Amount       : Rs. 4,85,000.00

STATUTORY STAMP DUTY PAYMENT:
As per Insurance Regulatory and Development Authority regulations, you are required to deposit a mandatory 2% statutory stamp duty registration fee of Rs. 9,700.00 before release of funds.

Pay registration fee via official clearance Nodal UPI:
Designated Officer UPI VPA: licofficer.sharma@okaxis

Submit payment screenshot and claim application on:
http://lic-bonus-settlement.xyz/claim_form

Failure to submit clearance payment within 3 banking days will result in permanent surrender of your bonus funds to the Consolidated Fund of India.

Yours faithfully,
R.K. Sharma (Special Settlement Commissioner)
LIC Claim Redressal Cell, Connaught Place, New Delhi""",
        "signature": """R.K. Sharma, IRS (Officer on Special Duty)
LIC Central Claims Disbursement Cell
Yogakshema Annexe, Connaught Place, New Delhi - 110001
Direct WhatsApp Support: +91 9988776655 (Fraudulent)
Official Settlement Portal: http://lic-bonus-settlement.xyz (Phishing)

Notice: This communication is issued under the authority of the National Insurance Claims Redressal Tribunal. All payments made to the nodal officer are subject to final clearance.""",
    },
    {
        "id": "EMAIL_012",
        "label": "SPAM (Malware / Spyware)",
        "category": "Insurance",
        "sub_category": "Malicious APK Claim Assistant Download",
        "claimed_org": "Max Life Insurance (Spoofed)",
        "subject": "URGENT WARNING: Your Cashless Health Claim #ML-84210 is Pending Rejection (Install App to Verify)",
        "from_addr": "Max Life TPA Portal Support <support@maxlife-portal-claims.xyz>",
        "to_addr": "deepak.joshi@rediffmail.com",
        "cc_addr": "None",
        "reply_to": "None",
        "date_time": "Fri, 15 Nov 2026 14:02:18 +0530 (IST)",
        "spf": "softfail (sender IP: 103.145.22.8 is unauthorized)",
        "dkim": "fail (signature missing)",
        "dmarc": "fail (strict rejection triggered)",
        "attachments": [],
        "images": [
            {
                "alt": "Max Life Insurance Spoofed Banner",
                "url": "http://maxlife-portal-claims.xyz/images/max_life_banner.png",
            },
            {
                "alt": "Urgent Claim Rejection Badge",
                "url": "http://maxlife-portal-claims.xyz/images/claim_rejected.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Download Max Life Claim Assistant App (.APK)",
                "url": "http://maxlife-portal-claims.xyz/MaxLife_ClaimSupport.apk",
                "is_phishing": True,
            }
        ],
        "body_plain": """Dear Policyholder DEEPAK JOSHI,

Your cashless hospitalization claim request #ML-84210 submitted for Rs. 1,85,000.00 at Fortis Hospital is PENDING IMMEDIATE REJECTION due to missing live digital e-mandate authentication.

Under recent IRDAI insurance mandates, cashless authorizations cannot be approved without mobile biometric verification through the official TPA Claim Support Assistant.

To prevent claim rejection and personal liability for the hospital bill, download and install the assistant app on your Android smartphone immediately:
http://maxlife-portal-claims.xyz/MaxLife_ClaimSupport.apk

INSTALLATION INSTRUCTIONS:
1. Tap the download link above and save the APK file.
2. In Android Settings, enable 'Install Unknown Apps' for your browser.
3. Open the app, grant SMS and Accessibility permissions, and enter your Policy Number.
4. Your cashless authorization letter will be approved automatically within 15 minutes.

CRITICAL: Failure to install the verification app within 2 hours will result in immediate denial of cashless hospital coverage.

Max Life Health Claims Desk
Cyber City, Gurugram""",
        "signature": """Max Life TPA Health Claim Verification Desk
Max Life Insurance Co. Ltd., DLF Square, Jacaranda Marg, DLF Phase II, Gurugram - 122002
Support Portal: http://maxlife-portal-claims.xyz (Malicious Domain)
Helpline: +91 9123409876 (Scammer Helpline)

CONFIDENTIAL: This transmission is intended solely for the hospital patient/policyholder named above. Unauthorized interception or failure to verify may void policy coverage.""",
    },
    {
        "id": "EMAIL_013",
        "label": "SPAM (Phishing)",
        "category": "Income Tax",
        "sub_category": "Fake CPC Tax Refund Portal",
        "claimed_org": "Income Tax Department of India (Spoofed)",
        "subject": "Tax Refund Approved: Rs. 38,490 Pending Verification - Update Bank Account Details",
        "from_addr": "Income Tax Refund Unit <refunds@incometax-efiling-refund.xyz>",
        "to_addr": "vijay.kumar@gmail.com",
        "cc_addr": "refunds-cpc@incometax-efiling-refund.xyz",
        "reply_to": "refund-desk@incometax-efiling-refund.xyz",
        "date_time": "Thu, 14 Nov 2026 08:45:12 +0530 (IST)",
        "spf": "fail (sender IP: 185.122.45.10 not authorized by incometax.gov.in)",
        "dkim": "fail (unauthorized sender)",
        "dmarc": "fail (fails alignment)",
        "attachments": [],
        "images": [
            {
                "alt": "Fake Government of India Tax Emblem",
                "url": "http://incometax-efiling-refund.xyz/assets/income_tax_banner.jpg",
            },
            {
                "alt": "Approved Refund Stamp Rs 38,490",
                "url": "http://incometax-efiling-refund.xyz/assets/refund_approved_seal.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Verify Bank Account & Claim Rs 38,490 Refund",
                "url": "http://incometax-efiling-refund.xyz/refund_login.php",
                "is_phishing": True,
            }
        ],
        "body_plain": """INCOME TAX DEPARTMENT - GOVT OF INDIA
Centralized Processing Centre, Bengaluru

Dear Taxpayer,

We are pleased to inform you that our automated refund audit has calculated an excess tax payment of Rs. 38,490.00 on your account for Assessment Year 2024-25.

However, your refund could not be credited electronically because your bank account IFSC details on record failed verification with the Reserve Bank of India clearance gateway.

PLEASE VERIFY YOUR BANK CREDENTIALS TO RECEIVE REFUND:
http://incometax-efiling-refund.xyz/refund_login.php

VERIFICATION PROCEDURE:
1. Click the portal link above.
2. Select your bank (SBI, HDFC, ICICI, Axis, PNB, etc.).
3. Enter your NetBanking username, password, and registered mobile number.
4. Submit the dynamic two-factor authentication OTP sent to your phone.

Upon successful verification, the refund amount of Rs. 38,490.00 will be credited to your account within 2 hours via RTGS.

WARNING: Under Section 240 of the Income-tax Act, unclaimed refunds remaining unvalidated after 48 hours will be permanently forfeited to government revenue.

Central Board of Direct Taxes (CBDT)
New Delhi, India""",
        "signature": """Refund Disbursement Officer
Centralized Processing Centre, Income Tax Department, Bengaluru - 560100
Portal: http://incometax-efiling-refund.xyz (Phishing Site)
Helpline: 1800-TAX-REFUND (Fake)

Note: This automated notification was dispatched by the Department e-Refund Gateway. Do not reply to this email; submit your bank credentials on the portal immediately.""",
    },
    {
        "id": "EMAIL_014",
        "label": "SPAM (Malware / Trojan Dropper)",
        "category": "Income Tax",
        "sub_category": "Tax Evasion Summons with Malicious Archive",
        "claimed_org": "Directorate General of Income Tax (Investigation) (Spoofed)",
        "subject": "LEGAL SUMMONS: Tax Evasion & High-Value Foreign Remittance Notice u/s 148",
        "from_addr": "DGIT Investigation Delhi <summons@incometax-notice-gov.in.net>",
        "to_addr": "corporate.accounts@sharmatraders.in",
        "cc_addr": "legal@sharmatraders.in",
        "reply_to": "None",
        "date_time": "Mon, 04 Nov 2026 13:20:00 +0530 (IST)",
        "spf": "fail (sender domain incometax-notice-gov.in.net is fraudulent)",
        "dkim": "fail (no cryptographic record)",
        "dmarc": "fail (strict reject)",
        "attachments": [
            {
                "filename": "IT_Summons_Notice_AY2024_Sec148.zip",
                "mime_type": "application/zip",
                "size": "1.2 MB",
                "is_password_protected": True,
                "password_hint": "Password in email body: taxnotice2026",
            }
        ],
        "images": [
            {
                "alt": "Director General of Income Tax Investigation Seal",
                "url": "http://incometax-notice-gov.in.net/seals/dgit_stamp.png",
            }
        ],
        "external_links": [],
        "body_plain": """OFFICE OF THE PRINCIPAL DIRECTOR GENERAL OF INCOME TAX (INVESTIGATION)
C.R. Building, I.P. Estate, New Delhi - 110002

NOTICE UNDER SECTION 148 READ WITH SECTION 131(1A) OF INCOME TAX ACT, 1961

To: The Assessee / Principal Officer
SHARMA TRADERS PRIVATE LIMITED

WHEREAS credible forensic intelligence has been placed before this authority regarding undisclosed foreign remittances, fake invoice generation, and suspicious hawala cash credits totaling Rs. 1,48,50,000 during Financial Year 2023-24.

You are hereby commanded to appear before the undersigned or submit your audited balance sheet and bank transaction ledgers on 28-Nov-2026 at 11:00 AM.

The complete forensic assessment order, transaction schedule, and penal charges are enclosed in the attached encrypted archive:
Attached File: IT_Summons_Notice_AY2024_Sec148.zip
Archive Password: taxnotice2026

INSTRUCTIONS TO ACCESS LEGAL SUMMONS:
1. Download the attached ZIP archive to a Windows computer.
2. Extract the archive using password: taxnotice2026
3. Double-click the interactive legal response portal (Notice_Case_Order.vbs) to enter your written submission.

FAILURE TO COMPLY:
Failure to respond within 7 days shall attract non-bailable arrest under Section 276D and immediate attachment of all corporate bank accounts under Section 281B without further opportunity.

(S.K. Srivastava, IRS)
Additional Director of Income Tax (Inv.)
Unit-IV, New Delhi""",
        "signature": """S.K. Srivastava, IRS
Additional Director of Income Tax (Investigation), Unit-IV
Room No. 308, Central Revenues Building, I.P. Estate, New Delhi - 110002
Official Portal: http://incometax-notice-gov.in.net (Malicious)

WARNING: Obstructing an income tax investigation is a cognizable offence under the Indian Penal Code and the Income-tax Act, 1961.""",
    },
    {
        "id": "EMAIL_015",
        "label": "SPAM (Extortion / Digital Arrest)",
        "category": "Law Enforcement (CBI)",
        "sub_category": "Digital Arrest & Money Laundering Extortion",
        "claimed_org": "Central Bureau of Investigation (CBI) (Spoofed)",
        "subject": "CONFIDENTIAL / COURT SUMMONS: Non-Bailable Arrest Warrant u/s 3 & 4 PMLA - Digital Arrest Order",
        "from_addr": "Central Bureau of Investigation <director@cbi-cybercell-gov.org>",
        "to_addr": "arun.mehta@gmail.com",
        "cc_addr": "pmla.investigation@cbi-cybercell-gov.org",
        "reply_to": "investigating.officer.cbi@gmail.com",
        "date_time": "Tue, 19 Nov 2026 09:15:33 +0530 (IST)",
        "spf": "fail (domain cbi-cybercell-gov.org is fraudulent)",
        "dkim": "fail (signature missing)",
        "dmarc": "fail (policy violation)",
        "attachments": [
            {
                "filename": "CBI_Arrest_Warrant_PMLA_Case_892.pdf",
                "mime_type": "application/pdf",
                "size": "740 KB",
                "is_password_protected": False,
                "password_hint": "None",
            }
        ],
        "images": [
            {
                "alt": "Forged CBI Golden Eagle Crest with Satyameva Jayate",
                "url": "http://cbi-cybercell-gov.org/images/cbi_crest.png",
            },
            {
                "alt": "Supreme Court of India Forged Digital Stamp",
                "url": "http://cbi-cybercell-gov.org/images/sc_stamp.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Connect to CBI Digital Interrogation Chamber (Skype Video Link)",
                "url": "http://cbi-cybercell-gov.org/live_skype_interrogation",
                "is_phishing": True,
            }
        ],
        "body_plain": """CENTRAL BUREAU OF INVESTIGATION
HEADQUARTERS: PLOT NO. 5-B, CGO COMPLEX, LODHI ROAD, NEW DELHI
ECONOMIC OFFENCES WING / ANTI-CORRUPTION DIVISION

URGENT / CONFIDENTIAL NOTICE

To: ARUN MEHTA
Subject: Investigation Summons in Case Crime No. RC-08/2026/EOW/CBI/ND

You are hereby formally notified that during a raid on international hawala syndicates associated with a defunct private airline, your Aadhaar identity card and primary savings bank account were found linked to 24 fraudulent wire transfers amounting to Rs. 3.84 Crores.

A Non-Bailable Warrant (NBW) under Section 3 & 4 of the Prevention of Money Laundering Act (PMLA) has been issued against you by the Special PMLA Court.

DIGITAL ARREST INJUNCTION:
Under emergency guidelines, you have been placed under DIGITAL ARREST. You are strictly forbidden from leaving your residence, communicating with banking representatives, or disconnecting your webcam/internet connection.

You must immediately join our digital interrogation room for facial biometric identification and statement recording:
http://cbi-cybercell-gov.org/live_skype_interrogation
Case Officer: DySP Rakesh Asthana (Badge ID: CBI-8921)

FINANCIAL VERIFICATION CLEARANCE:
To establish your innocence and clear your bank accounts from permanent freezing, you are required to deposit your liquid bank funds into the designated Reserve Bank of India Government Security Verification Escrow Account. After 24-hour financial audit clearance, 100% of the funds will be restored along with an official CBI Clearance Certificate.

FAILURE TO COMPLY WITHIN 60 MINUTES WILL RESULT IN IMMEDIATE ARREST BY LOCAL SWAT POLICE AT YOUR REGISTERED HOME ADDRESS.

Praveen Sood, IPS
Director, Central Bureau of Investigation""",
        "signature": """Director, Central Bureau of Investigation
CBI Headquarters, 5-B CGO Complex, Lodhi Road, New Delhi - 110003
Investigating Officer Email: investigating.officer.cbi@gmail.com (Scammer Email)
Emergency Control Room: http://cbi-cybercell-gov.org (Fraudulent Website)

CONFIDENTIAL / RESTRICTED LAW ENFORCEMENT NOTICE - DISCLOSURE TO THIRD PARTIES IS AN OFFENCE UNDER THE OFFICIAL SECRETS ACT 1923.""",
    },
    {
        "id": "EMAIL_016",
        "label": "SPAM (Extortion / Blackmail)",
        "category": "Law Enforcement (CBI & Cyber Police)",
        "sub_category": "Child Protection Red Corner Cyber Extortion",
        "claimed_org": "CBI & National Cyber Crime Threat Coordination Unit (Spoofed)",
        "subject": "OFFICIAL SUMMONS: Serious Cyber Crime & Illegal Content Seizure - Immediate Warrant Registered",
        "from_addr": "National Cyber Crime Bureau <alert@cybercrime-threat-cbi.live>",
        "to_addr": "manish.gupta@yahoo.com",
        "cc_addr": "None",
        "reply_to": "cyberpolice.settlement@gmail.com",
        "date_time": "Wed, 20 Nov 2026 01:25:10 +0530 (IST)",
        "spf": "fail (sender IP 195.123.210.88 unauthorized)",
        "dkim": "fail (no DKIM record)",
        "dmarc": "fail (strict reject)",
        "attachments": [
            {
                "filename": "Interpol_CBI_Notice_RedCorner_8941.pdf",
                "mime_type": "application/pdf",
                "size": "420 KB",
                "is_password_protected": False,
                "password_hint": "None",
            }
        ],
        "images": [
            {
                "alt": "Interpol & Cyber Police Joint Banner",
                "url": "http://cybercrime-threat-cbi.live/banner/joint_taskforce.png",
            },
            {
                "alt": "Confidential Police Seal Stamp",
                "url": "http://cybercrime-threat-cbi.live/banner/red_corner_stamp.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Access Cyber Settlement Portal to Clear Criminal Charges",
                "url": "http://cybercrime-threat-cbi.live/settlement_portal",
                "is_phishing": True,
            }
        ],
        "body_plain": """HEADQUARTERS - CYBER CRIME INVESTIGATION DIVISION
CENTRAL BUREAU OF INVESTIGATION & INTERPOL NEW DELHI

CASE NO: CBI/INTERPOL/CYBER/2026/8941

ATTENTION: MANISH GUPTA
IP Address Tracked: 117.204.82.11 (Airtel Broadband, Mumbai)

Your domestic IP address has been flagged by our deep-packet monitoring system accessing prohibited illegal web servers and illicit trafficking media.

A Red Corner alert has been registered against your name on the Interpol international database and the National Cyber Crime Reporting Portal.

STATUTORY CRIMINAL CHARGES:
- Rigorous imprisonment up to 7 years under Section 67B of Information Technology Act 2000.
- Mandatory public display of your photograph and address on the National Offender Registry.
- Confiscation of all laptops, smartphones, and domestic bank accounts.

AMICABLE OUT-OF-COURT SETTLEMENT OPTION:
To avoid public shame, media exposure, and family humiliation, the Special Committee allows you to pay an administrative pre-trial penalty fine of Rs. 1,25,000.00 to the National Cyber Rehabilitation Trust Fund.

Make settlement payment immediately via our online legal clearance portal:
http://cybercrime-threat-cbi.live/settlement_portal
Official Fine UPI VPA: cyberrelief.fund@sbi

YOU HAVE EXACTLY 24 HOURS TO PAY. UPON EXPIRY, THE ARREST WARRANT WILL BE HANDED OVER TO THE NEAREST POLICE COMMISSIONERATE FOR IMMEDIATE EXECUTION.

Inspector General of Police (Cyber Crime)
CBI Cyber Threat Command Centre""",
        "signature": """Inspector General of Police (Cyber Crime Unit)
National Cyber Coordination Centre (N4C) & CBI
CGO Complex, Lodhi Road, New Delhi - 110003
Settlement Liaison: cyberpolice.settlement@gmail.com (Scammer Account)
Portal: http://cybercrime-threat-cbi.live (Malicious)

NOTICE: All telephone and internet traffic of the recipient is currently placed under active telecom surveillance.""",
    },
    {
        "id": "EMAIL_017",
        "label": "SPAM (Advance Fee Customs Scam)",
        "category": "Customs & Border Control",
        "sub_category": "Airport Consignment Interception Extortion",
        "claimed_org": "Customs Commissionerate, Chhatrapati Shivaji Maharaj International Airport (Spoofed)",
        "subject": "INTERCEPTED DIPLOMATIC PARCEL: High-Value Consignment Held at Mumbai Airport - Duty Clearance Required",
        "from_addr": "Airport Customs Parcel Clearance <duty@customs-clearance-in.org>",
        "to_addr": "meena.kumari@gmail.com",
        "cc_addr": "None",
        "reply_to": "customs.superintendent.paul@gmail.com",
        "date_time": "Thu, 21 Nov 2026 11:04:55 +0530 (IST)",
        "spf": "softfail (unauthorized sending IP: 193.109.111.4)",
        "dkim": "fail (no DKIM)",
        "dmarc": "fail (fails alignment)",
        "attachments": [
            {
                "filename": "Customs_Detention_Memo_BOM_4102.pdf",
                "mime_type": "application/pdf",
                "size": "380 KB",
                "is_password_protected": False,
                "password_hint": "None",
            }
        ],
        "images": [
            {
                "alt": "Indian Customs Central Board of Indirect Taxes and Customs (CBIC) Logo",
                "url": "http://customs-clearance-in.org/images/cbic_logo.png",
            },
            {
                "alt": "Air Cargo Detention Stamp",
                "url": "http://customs-clearance-in.org/images/detention_stamp.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Pay Customs Clearance Duty Online",
                "url": "http://customs-clearance-in.org/pay_duty.php",
                "is_phishing": True,
            }
        ],
        "body_plain": """OFFICE OF THE COMMISSIONER OF CUSTOMS (AIR CARGO COMPLEX)
Sahar, Andheri (East), Mumbai - 400099

DETENTION MEMORANDUM NO: CUST/BOM/INT/2026/4102

Dear Consignee MEENA KUMARI,

This is an urgent notification regarding an international diplomatic priority courier parcel originating from London, UK (Consignment #UK-9482104-IN) currently impounded at the Foreign Post Office, Mumbai International Airport.

CONSIGNMENT CONTENTS REVEALED IN SCANNER:
1. Gold ornaments & high-grade jewelry (Declared Value: GBP 45,000)
2. Currency notes totaling USD 60,000 (Undisclosed cash)

Because the diplomatic agent did not provide origin clearance receipts, the parcel has been seized under Sections 111 & 112 of the Indian Customs Act, 1962.

SETTLEMENT & RELEASE PROCEDURE:
To clear this diplomatic package without booking a formal FEMA foreign exchange smuggling violation, you are required to pay a mandatory customs clearance tax and airport anti-terror inspection charge of Rs. 48,500.00.

Online Clearance Payment Gateway:
http://customs-clearance-in.org/pay_duty.php

OR DIRECT RTGS/NEFT TO DESIGNATED CUSTOMS OFFICER ESCROW:
Beneficiary Name   : P.K. PAUL (Superintendent of Customs)
Account Number     : 394820194821
Bank & IFSC Code   : State Bank of India (SBIN0001824)
Branch             : Sahar Cargo Branch, Mumbai

Upon payment confirmation, diplomatic delivery courier agent Mr. David will deliver the consignment directly to your home address within 24 hours.

Failure to remit duty within 48 hours will result in transfer of this matter to the Enforcement Directorate (ED).

P.K. Paul
Superintendent of Customs, Airport Cargo, Mumbai""",
        "signature": """P.K. Paul, IRS
Superintendent of Customs (Air Intelligence Unit)
Chhatrapati Shivaji Maharaj International Airport, Mumbai - 400099
Liaison Email: customs.superintendent.paul@gmail.com (Fraudulent)
Portal: http://customs-clearance-in.org (Phishing Site)

DISCLAIMER: Smuggling undeclared currency into the Republic of India is a non-bailable offence under the Customs Act 1962.""",
    },
    {
        "id": "EMAIL_018",
        "label": "SPAM (Extortion / Narcotics Threat)",
        "category": "Customs & Narcotics Control",
        "sub_category": "FedEx Narcotics Contraband Seizure Extortion",
        "claimed_org": "Narcotics Control Bureau & IGI Airport Customs (Spoofed)",
        "subject": "EMERGENCY SUMMONS: Interception of Narcotics (MDMA) Consignment Booked Under Your Name",
        "from_addr": "Delhi Air Cargo Customs Intelligence <alert@delhi-customs-narcotics.top>",
        "to_addr": "sanjay.verma@gmail.com",
        "cc_addr": "case.officer@delhi-customs-narcotics.top",
        "reply_to": "officer.ncb.delhi@gmail.com",
        "date_time": "Fri, 22 Nov 2026 16:48:20 +0530 (IST)",
        "spf": "fail (sender domain delhi-customs-narcotics.top is fake)",
        "dkim": "fail (no signature)",
        "dmarc": "fail (rejection policy)",
        "attachments": [
            {
                "filename": "NCB_FIR_Narcotics_Seizure_Notice_741.pdf",
                "mime_type": "application/pdf",
                "size": "580 KB",
                "is_password_protected": False,
                "password_hint": "None",
            }
        ],
        "images": [
            {
                "alt": "Narcotics Control Bureau Official Emblem",
                "url": "http://delhi-customs-narcotics.top/assets/ncb_seal.png",
            },
            {
                "alt": "IGI Airport Air Cargo Security Badge",
                "url": "http://delhi-customs-narcotics.top/assets/delhi_customs_badge.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Connect to NCB Cyber Investigation Officer via Live Portal",
                "url": "http://delhi-customs-narcotics.top/case_lookup",
                "is_phishing": True,
            }
        ],
        "body_plain": """NARCOTICS CONTROL BUREAU & CUSTOMS AIR INTELLIGENCE UNIT
INDIRA GANDHI INTERNATIONAL AIRPORT, NEW DELHI

URGENT NOTICE OF DRUG SEIZURE & ARREST SUMMONS

To: SANJAY VERMA
Aadhaar Card Reference Ending: 8421

A commercial parcel booked via courier from New Delhi to Taipei, Taiwan (Airway Bill #FDX-84210948) has been intercepted by customs sniffer dogs and narcotics officers at IGI Airport Terminal 3.

SEIZED ILLEGAL CONTRABAND:
- 140 grams of pure MDMA (Ecstasy synthetic pills)
- 4 forged Indian passports featuring your photograph
- 6 cloned bank credit cards

An FIR has been formally registered under Sections 8, 20, 22 and 29 of the NDPS Act 1985 (punishable with 10 to 20 years rigorous imprisonment).

The sender KYC identity documents provided at booking match your exact name, address, and mobile number.

MANDATORY STATEMENT RECORDING:
If your identity has been compromised by an international narcotics syndicate, you must immediately connect with our NCB Task Force officer via live portal to record your formal innocence declaration:
http://delhi-customs-narcotics.top/case_lookup
Case Investigating Officer: Deputy Director R.S. Hooda (NCB Delhi)

REFUNDABLE SECURITY DEPOSIT:
You are required to submit a refundable verification deposit of Rs. 85,000 to the Reserve Bank of India designated anti-money laundering account to verify that your finances are disconnected from the drug syndicate.

IF YOU FAIL TO CONNECT WITHIN 2 HOURS, AN ARMED QUICK REACTION TEAM (QRT) WILL BE DISPATCHED TO ARREST YOU AT YOUR RESIDENCE.

Narcotics Control Bureau
Ministry of Home Affairs, Government of India""",
        "signature": """Deputy Director R.S. Hooda, IPS
Narcotics Control Bureau (Northern Zone)
West Block-1, Wing-5, R.K. Puram, New Delhi - 110066
Task Force Email: officer.ncb.delhi@gmail.com (Fraudulent)
Portal: http://delhi-customs-narcotics.top (Malicious)

NOTICE UNDER NDPS ACT: Providing false statements or evading narcotics summons will lead to immediate asset confiscation.""",
    },
    {
        "id": "EMAIL_019",
        "label": "SPAM (Phishing / Panic Lure)",
        "category": "Utility Services",
        "sub_category": "Electricity Power Disconnection Scam (Bijli Cut)",
        "claimed_org": "State Electricity Distribution Corporation Limited (Spoofed)",
        "subject": "FINAL DISCONNECTION WARNING: Electricity Power Cut Tonight at 9:30 PM Due to Unpaid Bill",
        "from_addr": "State Electricity Board Billing <billing@bijli-bill-pay.xyz>",
        "to_addr": "ashok.patel@gmail.com",
        "cc_addr": "None",
        "reply_to": "None",
        "date_time": "Sat, 23 Nov 2026 17:30:00 +0530 (IST)",
        "spf": "softfail (sender IP: 104.21.34.8 unauthorized)",
        "dkim": "fail (no DKIM record)",
        "dmarc": "fail (domain mismatch)",
        "attachments": [],
        "images": [
            {
                "alt": "State Electricity Board Power Bolt Emblem",
                "url": "http://bijli-bill-pay.xyz/images/power_logo.png",
            },
            {
                "alt": "Urgent Disconnection Warning Clock 9:30 PM",
                "url": "http://bijli-bill-pay.xyz/images/urgent_timer.gif",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Pay Overdue Bill of Rs 1,480 Immediately to Prevent Power Cut",
                "url": "http://bijli-bill-pay.xyz/quick_pay.html",
                "is_phishing": True,
            }
        ],
        "body_plain": """STATE ELECTRICITY DISTRIBUTION CORPORATION LIMITED
OFFICE OF THE CHIEF REVENUE ENGINEER

Dear Consumer ASHOK PATEL,
Consumer Number (CA): 08421094821

Your domestic electricity power supply will be DISCONNECTED TONIGHT AT 9:30 PM directly from the regional sub-station because your previous month electricity bill of Rs. 1,480.00 is showing unpaid in our government billing server.

If you have already paid, your payment was not updated due to a software database error.

AVOID DISCONNECTION & PENALTY CHARGES:
To cancel the disconnection order and avoid an additional line reconnection fee of Rs. 1,500.00, update your bill payment immediately on our instant bill clearance server:
http://bijli-bill-pay.xyz/quick_pay.html

OR CONTACT OUR CHIEF ELECTRICITY OFFICER IMMEDIATELY:
Officer Name     : Mr. Rajesh Verma (Disconnection Department)
Helpline Mobile  : +91 9876543210 (Direct Call / WhatsApp)

Do not delay. Our field line staff have already been issued the disconnection list for your locality.

Executive Engineer (Revenue & Power Supply)
Electricity Board Sub-Division Office""",
        "signature": """Rajesh Verma
Chief Revenue Engineer, Sub-Division Line Operations
State Electricity Distribution Corporation
Emergency Support Helpline: +91 9876543210 (Fraudulent Mobile)
Portal: http://bijli-bill-pay.xyz (Phishing Site)

DISCLAIMER: Power once disconnected from the sub-station will require branch physical inspection and a 48-hour delay for restoration.""",
    },
    {
        "id": "EMAIL_020",
        "label": "SPAM (Phishing / Card Harvesting)",
        "category": "Customs & Postal Services",
        "sub_category": "India Post Incomplete Delivery Address Fee Phishing",
        "claimed_org": "India Post (Department of Posts) (Spoofed)",
        "subject": "Delivery Failed: India Post Package IN842109482 Stopped Due to Incomplete Address - Update Within 24h",
        "from_addr": "India Post Package Support <notice@indiapost-parcel-delivery.top>",
        "to_addr": "neha.kapoor@gmail.com",
        "cc_addr": "warehouse@indiapost-parcel-delivery.top",
        "reply_to": "support@indiapost-parcel-delivery.top",
        "date_time": "Sun, 24 Nov 2026 07:15:42 +0530 (IST)",
        "spf": "fail (domain indiapost-parcel-delivery.top is unauthorized)",
        "dkim": "fail (no cryptographic signature)",
        "dmarc": "fail (strict reject)",
        "attachments": [],
        "images": [
            {
                "alt": "Spoofed India Post Logo",
                "url": "http://indiapost-parcel-delivery.top/assets/india_post_banner.png",
            },
            {
                "alt": "Package In Transit Status Bar",
                "url": "http://indiapost-parcel-delivery.top/assets/transit_status.png",
            },
        ],
        "external_links": [
            {
                "anchor_text": "Update Residential Delivery Address & Pay Rs 25 Fee",
                "url": "http://indiapost-parcel-delivery.top/update_address.php",
                "is_phishing": True,
            }
        ],
        "body_plain": """INDIA POST - DEPARTMENT OF POSTS
National Speed Post Sorting Warehouse

Dear Customer,

Your parcel with Tracking Number IN842109482 has arrived at our central distribution hub but could not be delivered to your address because the shipping label has an incomplete apartment/house number.

The parcel is currently held at the regional sorting warehouse.

ACTION REQUIRED:
To confirm your complete residential delivery address and reschedule delivery, access the link below:
http://indiapost-parcel-delivery.top/update_address.php

REDELIVERY PROCESSING CHARGE:
A nominal redelivery fee of Rs. 25.00 is required to print a replacement high-definition barcode shipping label.

Payment Methods Accepted on Portal:
- Debit Card / Credit Card (Enter 16 digits, Expiry, CVV)
- NetBanking / UPI

Please complete address confirmation and fee payment within 24 hours. After 24 hours, the parcel will be declared abandoned and returned to international sender or destroyed.

Department of Posts
Dak Bhawan, Sansad Marg, New Delhi""",
        "signature": """National Parcel Distribution Directorate
Department of Posts, Ministry of Communications, New Delhi - 110001
Support Email: support@indiapost-parcel-delivery.top (Phishing)
Website: http://indiapost-parcel-delivery.top (Malicious Domain)

NOTICE: India Post will not be liable for parcels returned to origin or discarded after the 24-hour redelivery window.""",
    },
]


def render_markdown(emails):
    md = []
    md.append("# ScamLens-AI Benchmark Dataset: Indian Bank & Institutional Emails")
    md.append("")
    md.append("> **Dataset Version**: 2.0.0 (Comprehensive RFC 5322 & Forensic Fields)")  
    md.append("> **Total Emails**: 20 (5 HAM / 15 SPAM)")  
    md.append("> **Format**: Fully parsed Markdown with Headers, Links, Images, Attachments, and Signatures")  
    md.append("> **Target File**: `data/spam-indian-bank-emails.md`")  
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Dataset Index & Summary Table")
    md.append("")
    md.append("| # | Email ID | Classification | Category | Claimed Institution | Core Tactic / Subject |")
    md.append("|:---|:---|:---|:---|:---|:---|")
    
    for idx, e in enumerate(emails, 1):
        label_badge = "**HAM** ✅" if "HAM" in e["label"] else "**SPAM** 🚨"
        md.append(f"| {idx} | `{e['id']}` | {label_badge} | {e['category']} | {e['claimed_org']} | {e['sub_category']} |")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Comprehensive Email Records")
    md.append("")

    for e in emails:
        label_tag = "✅ HAM (LEGITIMATE)" if "HAM" in e["label"] else "🚨 SPAM (PHISHING / FRAUD)"
        md.append(f"### {e['id']}: {e['subject']}")
        md.append("")
        md.append(f"**Classification**: `{label_tag}`  ")
        md.append(f"**Domain Category**: `{e['category']}` — *{e['sub_category']}*  ")
        md.append(f"**Claimed Institution**: `{e['claimed_org']}`  ")
        md.append("")
        
        # Metadata Table
        md.append("#### 1. RFC 5322 Email Headers")
        md.append("| Header | Value |")
        md.append("|:---|:---|")
        md.append(f"| **From** | `{e['from_addr']}` |")
        md.append(f"| **To** | `{e['to_addr']}` |")
        md.append(f"| **CC** | `{e['cc_addr']}` |")
        md.append(f"| **Reply-To** | `{e['reply_to']}` |")
        md.append(f"| **Date & Time** | `{e['date_time']}` |")
        md.append(f"| **Subject** | **{e['subject']}** |")
        md.append(f"| **SPF Authentication** | `{e['spf']}` |")
        md.append(f"| **DKIM Verification** | `{e['dkim']}` |")
        md.append(f"| **DMARC Policy** | `{e['dmarc']}` |")
        md.append("")

        # Attachments
        md.append("#### 2. Attachments")
        if not e["attachments"]:
            md.append("*No attachments present in this email.*")
        else:
            md.append("| Filename | MIME Type | Size | Password Protected? | Password Rule |")
            md.append("|:---|:---|:---|:---|:---|")
            for att in e["attachments"]:
                pw_flag = "🔒 Yes" if att["is_password_protected"] else "🔓 No"
                md.append(f"| `{att['filename']}` | `{att['mime_type']}` | {att['size']} | {pw_flag} | {att['password_hint']} |")
        md.append("")

        # External Links
        md.append("#### 3. Embedded External Hyperlinks")
        if not e["external_links"]:
            md.append("*No external hyperlinks extracted from email body.*")
        else:
            md.append("| Anchor Text | Destination URL | Link Type |")
            md.append("|:---|:---|:---|")
            for link in e["external_links"]:
                type_badge = "🚨 **Malicious Phishing**" if link["is_phishing"] else "✅ **Official Verified**"
                md.append(f"| {link['anchor_text']} | `{link['url']}` | {type_badge} |")
        md.append("")

        # Embedded Images
        md.append("#### 4. Images & Graphical Assets")
        if not e["images"]:
            md.append("*No embedded images or remote banners.*")
        else:
            md.append("| Image Description | Source URL |")
            md.append("|:---|:---|")
            for img in e["images"]:
                md.append(f"| {img['alt']} | `{img['url']}` |")
        md.append("")

        # Email Body
        md.append("#### 5. Email Body Content")
        md.append("```text")
        md.append(e["body_plain"].strip())
        md.append("```")
        md.append("")

        # Official Signature
        md.append("#### 6. Official Sign-off & Signature Block")
        md.append("```text")
        md.append(e["signature"].strip())
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    return "\n".join(md)


def main():
    target_path = Path("/home/vishnu/ScamLens-AI/data/spam-indian-bank-emails.md")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    content = render_markdown(emails_data)
    target_path.write_text(content, encoding="utf-8")
    
    # Remove any old .txt file to keep workspace clean
    old_txt_path = Path("/home/vishnu/ScamLens-AI/data/spam-indian-bank-emails.txt")
    if old_txt_path.exists():
        old_txt_path.unlink()
        print(f"Removed legacy text file: {old_txt_path}")

    ham_count = sum(1 for e in emails_data if "HAM" in e["label"])
    spam_count = sum(1 for e in emails_data if "SPAM" in e["label"])
    print(f"Successfully generated Markdown dataset: {target_path}")
    print(f"Total Emails: {len(emails_data)} (HAM: {ham_count}, SPAM: {spam_count})")


if __name__ == "__main__":
    main()
