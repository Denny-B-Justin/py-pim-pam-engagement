"""
fallback_data.py — static snapshot of the country list.

Used ONLY when the Databricks tables are unreachable or empty, so the public site
still renders (the original Next.js app did the same with data/countries.ts).
Snapshot taken from the original repository (regenerated from the DB on 2026-06-10).
"""
from __future__ import annotations

FALLBACK_COUNTRIES: list[dict[str, str]] = [
    {"iso3": "ETH", "name": "Ethiopia", "region": "AFR-East", "status": "Awareness", "focus": "pim-pam.ai PIM Policy Profile, possible application of GPB tools (tbc)", "contact": "Vikram Menon / Rajul Awasthi"},
    {"iso3": "KEN", "name": "Kenya", "region": "AFR-East", "status": "Awareness", "focus": "pim-pam.ai PIM Policy Profile, possible application of GPB tools (tbc)", "contact": "Onur Erdem"},
    {"iso3": "RWA", "name": "Rwanda", "region": "AFR-East", "status": "Awareness", "focus": "Possible PIM Policies AI profile testing", "contact": "Djeniffer Zamy Lima Melo"},
    {"iso3": "UGA", "name": "Uganda", "region": "AFR-East", "status": "Application", "focus": "pim-pam.ai PIM Policy Profile, possible application of GPB tools (tbc)", "contact": "Verena Fritz / Barbara Magezi"},
    {"iso3": "ZMB", "name": "Zambia", "region": "AFR-East", "status": "Application", "focus": "pim-pam.ai PIM Policy Profile, GPB PIA, CBA, LDT", "contact": "Lobna Ahmed"},
    {"iso3": "MDG", "name": "Madagascar", "region": "AFR-South", "status": "Awareness", "focus": "pim-pam.ai PIM Policy Profile,", "contact": "Lira Rajenarison"},
    {"iso3": "MOZ", "name": "Mozambique", "region": "AFR-South", "status": "Application", "focus": "pim-pam.ai PIM Policy Profile, GPB CBA Applications", "contact": "Miguel Saldarriaga / Ana Hirata"},
    {"iso3": "ZAF", "name": "South Africa", "region": "AFR-South", "status": "Application", "focus": "pim-pam.ai PIM Policy Profile, GPB CBA Applications", "contact": "Runyararo Senderayi"},
    {"iso3": "AGO", "name": "Angola", "region": "AFR-West", "status": "Awareness", "focus": "pim-pam.ai PIM Policy Profile,", "contact": "Eduardo Estrada"},
    {"iso3": "GHA", "name": "Ghana", "region": "AFR-West", "status": "Application", "focus": "pim-pam.ai PIM Policy Profile, GPB CBA Applications, Portfolio Doctor Application", "contact": "Raymond Muhula"},
    {"iso3": "AUS", "name": "Australia", "region": "EAP", "status": "Awareness", "focus": "", "contact": "—"},
    {"iso3": "IDN", "name": "Indonesia", "region": "EAP", "status": "Awareness", "focus": "Complete PIM Policy Profile", "contact": "Shomikho Raha / Cut Dian Agustina"},
    {"iso3": "KOR", "name": "South Korea", "region": "EAP", "status": "Awareness", "focus": "Complete PIM Policy Profile, possible application of GPB CBA and CCS", "contact": "Hyunseok Kim"},
    {"iso3": "VNM", "name": "Vietnam", "region": "EAP", "status": "Application", "focus": "Complete PIM Policy Profile, possible further application of ePIM-GPB CBA learning at national or sub-national levels", "contact": "Phuong Anh Nguyen"},
    {"iso3": "ARM", "name": "Armenia", "region": "ECA-East", "status": "Application", "focus": "", "contact": "Fabienne Mroczka"},
    {"iso3": "AZE", "name": "Azerbaijan", "region": "ECA-East", "status": "Inception", "focus": "", "contact": "Fabienne Mroczka"},
    {"iso3": "GEO", "name": "Georgia", "region": "ECA-East", "status": "Adoption", "focus": "", "contact": "Fabienne Mroczka / Ruggero"},
    {"iso3": "MDA", "name": "Moldova", "region": "ECA-East", "status": "Inception", "focus": "", "contact": "Iryna Shcherbyna"},
    {"iso3": "UKR", "name": "Ukraine", "region": "ECA-East", "status": "Application", "focus": "", "contact": "Urska Zrinski / Iryna Shcherbyna"},
    {"iso3": "UZB", "name": "Uzbekistan", "region": "ECA-East", "status": "Inception", "focus": "", "contact": "Arman / Kai"},
    {"iso3": "ALB", "name": "Albania", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Pablo Guzman Abastoflor"},
    {"iso3": "AUT", "name": "Austria", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Kai Kaiser / Tessa"},
    {"iso3": "BIH", "name": "Bosnia and Herzegovina", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Zuhra Osmanovic-Pasic"},
    {"iso3": "BGR", "name": "Bulgaria", "region": "ECA-West", "status": "Inception", "focus": "", "contact": "Jonas Arp Fallov"},
    {"iso3": "HRV", "name": "Croatia", "region": "ECA-West", "status": "Awareness", "focus": "", "contact": "Peter Ladegaard"},
    {"iso3": "IRL", "name": "Ireland", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Kai Kaiser"},
    {"iso3": "XKX", "name": "Kosovo", "region": "ECA-West", "status": "Awareness", "focus": "", "contact": "Jonas Arp Fallov"},
    {"iso3": "LTU", "name": "Lithuania", "region": "ECA-West", "status": "Awareness", "focus": "", "contact": "Kai Kaiser"},
    {"iso3": "MNE", "name": "Montenegro", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Elijah Kimani"},
    {"iso3": "MKD", "name": "North Macedonia", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Mediha Agar"},
    {"iso3": "POL", "name": "Poland", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Kai Kaiser"},
    {"iso3": "ROU", "name": "Romania", "region": "ECA-West", "status": "Inception", "focus": "", "contact": "Jonas Arp Fallov"},
    {"iso3": "SRB", "name": "Serbia", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Kai Kaiser"},
    {"iso3": "SVK", "name": "Slovakia", "region": "ECA-West", "status": "Application", "focus": "", "contact": "Kai Kaiser"},
    {"iso3": "TUR", "name": "Türkiye", "region": "ECA-West", "status": "Awareness", "focus": "", "contact": "Mediha Agar"},
    {"iso3": "BRA", "name": "Brazil", "region": "LAC", "status": "Awareness", "focus": "Complete PIM Policy Profile for Federal and 3-states, test CBA application", "contact": "Carolina Vaira / Gustavo Bozzetti"},
    {"iso3": "GTM", "name": "Guatemala", "region": "LAC", "status": "Awareness", "focus": "Apply PAG-FA", "contact": "—"},
    {"iso3": "PER", "name": "Peru", "region": "LAC", "status": "Awareness", "focus": "Complete PIM Policy Profile for Federal and 3-states, test CBA application", "contact": "Juergen Blum"},
    {"iso3": "EGY", "name": "Egypt", "region": "MENA-AP", "status": "Awareness", "focus": "Complete PIM Policy Profile . Possible LDT and CBA applications as part of new Urban-Gov LED operation", "contact": "Michel Maellberg"},
    {"iso3": "MAR", "name": "Morocco", "region": "MENA-AP", "status": "Awareness", "focus": "Complete PIM Policy Profile . Possible LDT and CBA applications as part of new Urban-Gov LED operation", "contact": "Pedro Arizti"},
    {"iso3": "BGD", "name": "Bangladesh", "region": "SAR", "status": "Application", "focus": "", "contact": "Hoon (PM-Gov)"},
    {"iso3": "BTN", "name": "Bhutan", "region": "SAR", "status": "Adoption", "focus": "PIM Country Policy Profile, GPB CBA applied", "contact": "Neha Gupta / Savinay Grover"},
    {"iso3": "NPL", "name": "Nepal", "region": "SAR", "status": "Application", "focus": "Complete PIM Policy Profile, possible application of GPB LDT-PIA for sub-national (JICA mission)", "contact": "Yoshihiro Saito / Timila Shrestha"},
]
