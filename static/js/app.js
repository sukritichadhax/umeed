/* =========================================================
   UMEED — ENGLISH / HINDI LANGUAGE SYSTEM
   Works with existing [data-language="en"] and
   [data-language="hi"] buttons.

   No new Python package is required.
   ========================================================= */

(() => {
    "use strict";

    const LANGUAGE_KEY = "umeed-language";

    const translations = {

        // =====================================================
        // NAVIGATION AND SHARED LAYOUT
        // =====================================================

        "Home": "होम",
        "Explore Campaigns": "अभियान देखें",
        "Explore campaigns": "अभियान देखें",
        "Affiliated NGOs": "संबद्ध NGO",
        "My Donations": "मेरे दान",
        "My donations": "मेरे दान",
        "Our Donations": "हमारे दान",
        "Our Campaigns": "हमारे अभियान",
        "Create Campaign": "अभियान बनाएँ",
        "Create campaign": "अभियान बनाएँ",
        "Create a campaign": "अभियान बनाएँ",
        "Offline Donations": "ऑफलाइन दान",
        "Create Offline Donation": "ऑफलाइन दान दर्ज करें",
        "NGO Workspace": "NGO कार्यक्षेत्र",
        "Open NGO workspace": "NGO कार्यक्षेत्र खोलें",
        "Admin Panel": "एडमिन पैनल",
        "Open Admin Panel": "एडमिन पैनल खोलें",
        "Dashboard": "डैशबोर्ड",
        "My dashboard": "मेरा डैशबोर्ड",
        "Manage donations": "दान प्रबंधित करें",
        "View my donations": "मेरे दान देखें",
        "Open donations": "दान खोलें",
        "Find campaigns": "अभियान खोजें",
        "Browse relief campaigns": "राहत अभियान देखें",
        "Donate supplies": "सामग्री दान करें",
        "Sign in": "साइन इन करें",
        "Sign In": "साइन इन करें",
        "Sign in to continue.": "जारी रखने के लिए साइन इन करें।",
        "Sign in to donate": "दान करने के लिए साइन इन करें",
        "Sign in to select products": "उत्पाद चुनने के लिए साइन इन करें",
        "Sign in to donate physical supplies": "भौतिक सामग्री दान करने के लिए साइन इन करें",
        "Login": "लॉग इन",
        "Log in": "लॉग इन",
        "Create Account": "खाता बनाएँ",
        "Create account": "खाता बनाएँ",
        "Register": "पंजीकरण करें",
        "Sign out": "लॉग आउट",
        "Logout": "लॉग आउट",
        "English": "English",
        "हिन्दी": "हिन्दी",
        "Language": "भाषा",

        "Cancel": "रद्द करें",
        "Save": "सहेजें",
        "Save changes": "बदलाव सहेजें",
        "Save profile": "प्रोफ़ाइल सहेजें",
        "Update profile": "प्रोफ़ाइल अपडेट करें",
        "Submit": "जमा करें",
        "Update": "अपडेट करें",
        "Back": "वापस",
        "Back to dashboard": "डैशबोर्ड पर वापस जाएँ",
        "Back to donations": "दान सूची पर वापस जाएँ",
        "View details": "विवरण देखें",
        "View record": "रिकॉर्ड देखें",
        "View more": "और देखें",
        "View more →": "और देखें →",
        "Search": "खोजें",
        "Filter": "फ़िल्टर करें",
        "Actions": "कार्रवाई",
        "Download": "डाउनलोड करें",
        "Print": "प्रिंट करें",
        "Continue": "जारी रखें",
        "Confirm": "पुष्टि करें",
        "Close": "बंद करें",
        "Refresh": "रीफ़्रेश करें",
        "Optional": "वैकल्पिक",
        "Required": "आवश्यक",
        "Choose an option": "एक विकल्प चुनें",
        "Select an option": "एक विकल्प चुनें",
        "Choose campaign": "अभियान चुनें",
        "Choose emergency type": "आपातस्थिति का प्रकार चुनें",

        // =====================================================
        // HOMEPAGE
        // =====================================================

        "Welcome to Umeed": "उम्मीद में आपका स्वागत है",
        "Verified relief campaigns": "सत्यापित राहत अभियान",
        "Verified Relief Campaigns": "सत्यापित राहत अभियान",
        "Verified relief initiatives": "सत्यापित राहत पहल",
        "A little help.": "थोड़ी सी मदद।",
        "A little more hope.": "थोड़ी और उम्मीद।",
        "Every contribution matters.": "हर योगदान महत्वपूर्ण है।",
        "Your generosity.": "आपकी उदारता।",
        "Your kindness.": "आपकी दयालुता।",
        "Their hope.": "उनकी उम्मीद।",
        "For every helping hand": "हर मदद करने वाले के लिए",
        "Make your contribution count.": "अपने योगदान को सार्थक बनाएँ।",
        "Relief begins with readiness.": "राहत की शुरुआत तैयारी से होती है।",
        "Become a donor": "दाता बनें",
        "Already registered?": "पहले से पंजीकृत हैं?",
        "Campaign management": "अभियान प्रबंधन",
        "Register offline donations": "ऑफलाइन दान दर्ज करें",
        "No affiliated NGOs yet": "अभी कोई संबद्ध NGO नहीं है",
        "The organisations behind the relief": "राहत कार्य करने वाले संगठन",

        // =====================================================
        // REGISTRATION AND LOGIN
        // =====================================================

        "Your name": "आपका नाम",
        "Full name": "पूरा नाम",
        "Email": "ईमेल",
        "Email address": "ईमेल पता",
        "Password": "पासवर्ड",
        "Account type": "खाते का प्रकार",
        "Donor": "दाता",
        "NGO representative": "NGO प्रतिनिधि",
        "NGO name": "NGO का नाम",
        "NGO location": "NGO का स्थान",
        "About your organisation": "आपके संगठन के बारे में",
        "Join Umeed to contribute supplies or manage an NGO.": "सामग्री दान करने या NGO प्रबंधित करने के लिए उम्मीद से जुड़ें।",
        "Use at least 8 characters.": "कम से कम 8 अक्षरों का उपयोग करें।",
        "Please complete all required fields.": "कृपया सभी आवश्यक फ़ील्ड भरें।",
        "An account with this email already exists.": "इस ईमेल से खाता पहले से मौजूद है।",
        "Your password must contain at least 8 characters.": "आपके पासवर्ड में कम से कम 8 अक्षर होने चाहिए।",
        "Incorrect email or password.": "ईमेल या पासवर्ड गलत है।",
        "Welcome back.": "वापस स्वागत है।",
        "You have signed out.": "आपने लॉग आउट कर लिया है।",
        "Your account has been created successfully.": "आपका खाता सफलतापूर्वक बनाया गया है।",
        "Your NGO registration is awaiting administrator approval.": "आपका NGO पंजीकरण प्रशासक की स्वीकृति की प्रतीक्षा में है।",
        "Please sign in to continue.": "जारी रखने के लिए कृपया साइन इन करें।",

        // =====================================================
        // NGO PROFILE
        // =====================================================

        "Edit NGO Profile": "NGO प्रोफ़ाइल संपादित करें",
        "Organisation name": "संगठन का नाम",
        "Organisation description": "संगठन का विवरण",
        "Location": "स्थान",
        "The organisations behind the relief": "राहत कार्य करने वाले संगठन",
        "This organisation has not added a profile description yet.": "इस संगठन ने अभी तक अपना परिचय नहीं जोड़ा है।",
        "Save profile": "प्रोफ़ाइल सहेजें",

        // =====================================================
        // CAMPAIGNS
        // =====================================================

        "Active campaigns": "सक्रिय अभियान",
        "No active campaigns yet": "अभी कोई सक्रिय अभियान नहीं है",
        "Campaign title": "अभियान का शीर्षक",
        "Campaign location": "अभियान का स्थान",
        "Campaign": "अभियान",
        "Category": "श्रेणी",
        "Category:": "श्रेणी:",
        "Location:": "स्थान:",
        "Emergency": "आपातस्थिति",
        "Emergency type": "आपातस्थिति का प्रकार",
        "Required items": "आवश्यक सामग्री",
        "Description": "विवरण",
        "Active": "सक्रिय",
        "Closed": "बंद",
        "Pending": "लंबित",
        "Rejected": "अस्वीकृत",
        "Awaiting approval": "स्वीकृति की प्रतीक्षा में",
        "Natural disaster": "प्राकृतिक आपदा",
        "Food insecurity": "खाद्य असुरक्षा",
        "Infrastructure collapse": "बुनियादी ढाँचे का ढहना",
        "Civil unrest": "नागरिक अशांति",
        "Emergency preparedness": "आपातकालीन तैयारी",
        "Close campaign": "अभियान बंद करें",
        "Close this campaign": "यह अभियान बंद करें",

        // =====================================================
        // NEW CAMPAIGN EDITOR
        // =====================================================

        "NGO campaign management": "NGO अभियान प्रबंधन",
        "Edit campaign": "अभियान संपादित करें",
        "Edit Campaign": "अभियान संपादित करें",
        "Manage campaign information, carousel images, vendor products, and physical in-kind supplies.": "अभियान की जानकारी, तस्वीरें, विक्रेता से खरीदे जाने वाले उत्पाद और भौतिक सामग्री प्रबंधित करें।",

        "1. Campaign information": "1. अभियान की जानकारी",
        "2. Campaign story": "2. अभियान की कहानी",
        "3. Campaign carousel images": "3. अभियान की तस्वीरें",
        "4. Donate Products catalogue": "4. उत्पाद दान सूची",
        "5. In-kind donation catalogue": "5. वस्तु दान सूची",

        "Campaign information": "अभियान की जानकारी",
        "Campaign story": "अभियान की कहानी",
        "Main campaign description": "अभियान का मुख्य विवरण",
        "These descriptions appear under their respective headings on the donor-facing campaign page.": "ये विवरण दाता को दिखाई देने वाले अभियान पेज पर संबंधित शीर्षकों के नीचे दिखेंगे।",

        "Who you're helping": "आप किसकी मदद कर रहे हैं",
        "Why support is urgent": "सहायता तुरंत क्यों ज़रूरी है",
        "Who's behind the mission": "इस पहल के पीछे कौन है",
        "What your donation makes possible": "आपका दान क्या संभव बनाता है",

        "Use a public image URL or a local /static/ path. Use HTTPS for deployed websites.": "सार्वजनिक इमेज URL या स्थानीय /static/ पथ का उपयोग करें। लाइव वेबसाइट पर HTTPS उपयोग करें।",
        "Image 1": "तस्वीर 1",
        "Image 2": "तस्वीर 2",
        "Image 3": "तस्वीर 3",
        "Campaign carousel images": "अभियान की तस्वीरें",

        "Donate Products catalogue": "उत्पाद दान सूची",
        "These are products Umeed arranges from vendors. This catalogue is separate from physical in-kind donations. Add, remove, or edit rows here; donors will see the same saved products on the campaign page. Each row includes a target quantity, indicative unit price in ₹, and either an image URL or an uploaded PNG/JPEG/WebP image.": "ये वे उत्पाद हैं जिन्हें उम्मीद विक्रेताओं से मँगवाता है। यह सूची भौतिक वस्तु दान से अलग है। यहाँ उत्पाद जोड़ें, हटाएँ या संपादित करें। दाताओं को अभियान पेज पर सहेजे गए उत्पाद दिखाई देंगे। हर उत्पाद में लक्ष्य मात्रा, ₹ में प्रति इकाई अनुमानित मूल्य और तस्वीर का URL या अपलोड की गई PNG/JPEG/WebP तस्वीर हो सकती है।",

        "Donor-facing introduction": "दाता को दिखाई देने वाला परिचय",
        "Products, target quantities, prices and image URLs": "उत्पाद, लक्ष्य मात्रा, कीमतें और तस्वीरों के URL",
        "Products, target quantities, prices, and image URLs": "उत्पाद, लक्ष्य मात्रा, कीमतें और तस्वीरों के URL",
        "Product name / pack size": "उत्पाद का नाम / पैक का आकार",
        "Target quantity": "लक्षित मात्रा",
        "Unit value (₹)": "प्रति इकाई मूल्य (₹)",
        "Image URL (optional)": "तस्वीर का URL (वैकल्पिक)",
        "An uploaded image overrides this URL.": "अपलोड की गई तस्वीर इस URL की जगह उपयोग होगी।",
        "Upload PNG/JPG/WebP": "PNG/JPG/WebP अपलोड करें",
        "Clear image": "तस्वीर हटाएँ",
        "＋ Add product": "＋ उत्पाद जोड़ें",
        "Add product": "उत्पाद जोड़ें",
        "Removing a row removes it from the donor-facing vendor catalogue when saved.": "किसी पंक्ति को हटाने और सहेजने पर वह दाता को दिखाई देने वाली उत्पाद सूची से हट जाएगी।",

        "In-kind donation catalogue": "वस्तु दान सूची",
        "These are physical items donors can bring or request pickup for. This catalogue is separate from Donate Products. Add or remove items here; the donor-facing cards, target quantities, available counts, and images update from the saved catalogue.": "यह उन भौतिक वस्तुओं की सूची है जिन्हें दाता स्वयं पहुँचा सकते हैं या पिकअप का अनुरोध कर सकते हैं। यह उत्पाद दान से अलग है। यहाँ वस्तुएँ जोड़ें या हटाएँ; दाता को दिखाई देने वाले कार्ड, लक्ष्य मात्रा, उपलब्ध मात्रा और तस्वीरें सहेजी गई सूची से अपडेट होंगी।",
        "Physical item": "भौतिक वस्तु",
        "Donor-provided supply": "दाता द्वारा दी जाने वाली सामग्री",
        "＋ Add physical item": "＋ भौतिक वस्तु जोड़ें",
        "Add physical item": "भौतिक वस्तु जोड़ें",
        "This list controls the separate physical in-kind tab, not vendor purchases.": "यह सूची अलग भौतिक वस्तु दान टैब को नियंत्रित करती है, विक्रेता से खरीद को नहीं।",
        "Packaging instructions — exactly four steps": "पैकिंग निर्देश — ठीक चार चरण",
        "One instruction per line. These rules apply only to physical in-kind donations.": "हर पंक्ति में एक निर्देश लिखें। ये नियम केवल भौतिक वस्तु दान पर लागू होते हैं।",
        "Save campaign changes": "अभियान के बदलाव सहेजें",
        "Closing removes this campaign from the public active-campaign list. Existing donation history remains.": "अभियान बंद करने पर यह सार्वजनिक सक्रिय अभियान सूची से हट जाएगा। पुराने दान का इतिहास बना रहेगा।",

        // =====================================================
        // DONOR CAMPAIGN PAGE
        // =====================================================

        "Receiving organisation": "प्राप्तकर्ता संगठन",
        "Receiving organization": "प्राप्तकर्ता संगठन",
        "NGO approved by Umeed admin": "उम्मीद प्रशासक द्वारा स्वीकृत NGO",
        "Requirements last recorded:": "ज़रूरतें अंतिम बार दर्ज की गईं:",
        "Not recorded": "दर्ज नहीं है",
        "Supplies needed for this campaign": "इस अभियान के लिए आवश्यक सामग्री",
        "Live supply requirements": "सामग्री की मौजूदा ज़रूरतें",
        "Donate Products": "उत्पाद दान करें",
        "Donate products": "उत्पाद दान करें",
        "In-kind donation": "वस्तु के रूप में दान",
        "In-kind Donation": "वस्तु के रूप में दान",
        "Choose your donation": "अपना दान चुनें",
        "Choose products": "उत्पाद चुनें",
        "Current campaign requirements": "अभियान की मौजूदा ज़रूरतें",
        "Choose physical supplies to donate": "दान के लिए भौतिक सामग्री चुनें",
        "Supply": "सामग्री",
        "Supplies": "सामग्री",
        "Accepted": "स्वीकृत",
        "Available": "उपलब्ध",
        "Still available": "अभी उपलब्ध",
        "Still available for new offers": "नए प्रस्तावों के लिए अभी उपलब्ध",
        "Needs supplies": "सामग्री की आवश्यकता",
        "In progress": "प्रगति पर",
        "Almost fulfilled": "लगभग पूरा",
        "Target reached": "लक्ष्य पूरा",
        "Target fulfilled or committed": "लक्ष्य पूरा हुआ या सामग्री प्रतिबद्ध है",
        "No remaining quantity currently listed": "फिलहाल कोई शेष मात्रा सूचीबद्ध नहीं है",
        "No products have been configured for this campaign yet.": "इस अभियान के लिए अभी उत्पाद नहीं जोड़े गए हैं।",
        "The NGO has not configured supply targets yet.": "NGO ने अभी सामग्री के लक्ष्य तय नहीं किए हैं।",
        "Physical in-kind submissions are available to donor accounts.": "भौतिक वस्तु दान केवल दाता खातों के लिए उपलब्ध है।",

        "Choose the quantities you would like Umeed to procure from vendors for this campaign.": "इस अभियान के लिए उम्मीद द्वारा विक्रेताओं से मँगवाई जाने वाली मात्रा चुनें।",
        "Select the quantities you would like Umeed to procure from vendors for this campaign.": "इस अभियान के लिए उम्मीद द्वारा विक्रेताओं से मँगवाई जाने वाली मात्रा चुनें।",
        "Choose physical supplies you will provide yourself. These are separate from products procured by Umeed.": "वे भौतिक सामग्री चुनें जो आप स्वयं देंगे। यह उम्मीद द्वारा खरीदे जाने वाले उत्पादों से अलग है।",
        "How will you provide the supplies?": "आप सामग्री कैसे देंगे?",
        "I will deliver the supplies myself": "मैं सामग्री स्वयं पहुँचाऊँगा/पहुँचाऊँगी",
        "Request a pickup (the NGO will confirm separately)": "पिकअप का अनुरोध करें (NGO अलग से पुष्टि करेगा)",
        "Donate now": "अभी दान करें",
        "Pack in 4 easy steps": "4 आसान चरणों में पैक करें",
        "Pack your donation in 4 easy steps": "अपने दान को 4 आसान चरणों में पैक करें",
        "Packing step": "पैकिंग चरण",

        // =====================================================
        // CHECKOUT
        // =====================================================

        "Review your contribution": "अपने योगदान की समीक्षा करें",
        "Review your in-kind contribution": "अपने वस्तु दान की समीक्षा करें",
        "Complete your contribution": "अपना योगदान पूरा करें",
        "Supply": "सामग्री",
        "Product": "उत्पाद",
        "Quantity": "मात्रा",
        "Quantity selected": "चुनी गई मात्रा",
        "Unit value": "प्रति इकाई मूल्य",
        "Unit value (₹)": "प्रति इकाई मूल्य (₹)",
        "Subtotal": "उप-योग",
        "Estimated basket value": "अनुमानित कुल मूल्य",
        "Continue to checkout": "चेकआउट पर आगे बढ़ें",
        "Confirm contribution": "योगदान की पुष्टि करें",
        "Confirm demo contribution": "योगदान की पुष्टि करें",
        "Back to supplies": "सामग्री पर वापस जाएँ",
        "Donation source": "दान का स्रोत",
        "Vendor procurement": "विक्रेता से खरीद",
        "Physical in-kind donation": "भौतिक वस्तु दान",
        "Donor drop-off": "दाता स्वयं पहुँचाएगा",
        "Pickup requested — awaiting confirmation": "पिकअप का अनुरोध किया गया — पुष्टि लंबित",
        "No real payment": "कोई वास्तविक भुगतान नहीं",
        "Prototype checkout — no real payment": "प्रोटोटाइप चेकआउट — वास्तविक भुगतान नहीं",
        "No money is charged.": "कोई पैसा नहीं लिया जाता है।",

        // =====================================================
        // DONATION PASSPORT
        // =====================================================

        "Donation Passport": "दान पासपोर्ट",
        "Your Donation Passport": "आपका दान पासपोर्ट",
        "Donation Record": "दान रिकॉर्ड",
        "Donation record": "दान रिकॉर्ड",
        "NGO Donation Record": "NGO दान रिकॉर्ड",
        "Read-only record": "केवल पढ़ने योग्य रिकॉर्ड",
        "Donation ID": "दान ID",
        "Donation ID:": "दान ID:",
        "Registered": "पंजीकरण की तारीख",
        "Current status": "वर्तमान स्थिति",
        "Current record status": "वर्तमान रिकॉर्ड स्थिति",
        "Contribution type": "योगदान का प्रकार",
        "Donation source": "दान का स्रोत",
        "Print donation label": "दान लेबल प्रिंट करें",
        "Download QR code": "QR कोड डाउनलोड करें",
        "Scan or enter the donation ID.": "QR स्कैन करें या दान ID दर्ज करें।",
        "For physical supplies, print the QR label and attach it clearly to the outside of the box.": "भौतिक सामग्री के लिए QR लेबल प्रिंट करके डिब्बे के बाहर स्पष्ट रूप से लगाएँ।",
        "Use this reference to follow the progress of the products selected for this campaign.": "इस संदर्भ से अपने चुने हुए उत्पादों की प्रगति देखें।",
        "Products selected": "चुने गए उत्पाद",
        "Product progress history": "उत्पाद प्रगति इतिहास",
        "Physical donation history": "भौतिक दान का इतिहास",
        "Physical donation item record": "भौतिक दान सामग्री रिकॉर्ड",
        "Itemised donation record": "वस्तुवार दान रिकॉर्ड",
        "Declared, received, accepted, and rejected quantities.": "घोषित, प्राप्त, स्वीकृत और अस्वीकृत मात्राएँ।",
        "Declared": "घोषित",
        "Received": "प्राप्त",
        "Rejected": "अस्वीकृत",
        "Offer Submitted": "दान प्रस्ताव जमा किया गया",
        "Offer submitted": "दान प्रस्ताव जमा किया गया",
        "Intake Verified": "प्राप्त सामग्री सत्यापित की गई",
        "Intake verified": "प्राप्त सामग्री सत्यापित की गई",
        "Delivery Confirmed": "डिलीवरी की पुष्टि की गई",
        "Delivery confirmed": "डिलीवरी की पुष्टि की गई",
        "Distribution reported": "वितरण दर्ज किया गया",
        "No history updates have been recorded yet.": "अभी तक कोई इतिहास अपडेट दर्ज नहीं हुआ है।",
        "No progress milestones have been recorded yet.": "अभी तक प्रगति का कोई चरण दर्ज नहीं हुआ है।",
        "Milestones are shown when an authorised team member records them.": "प्रगति के चरण तभी दिखते हैं जब अधिकृत टीम सदस्य उन्हें दर्ज करता है।",

        // =====================================================
        // DONATION AND NGO WORKFLOWS
        // =====================================================

        "Incoming donations": "प्राप्त दान",
        "Identify a donation": "दान की पहचान करें",
        "Scan QR with Camera": "कैमरे से QR स्कैन करें",
        "Stop Camera": "कैमरा बंद करें",
        "Upload QR Image": "QR छवि अपलोड करें",
        "Register offline donation": "ऑफलाइन दान दर्ज करें",
        "Find a donation using its printed ID": "प्रिंट किए गए ID से दान खोजें",
        "Donation ID": "दान ID",
        "Find donation": "दान खोजें",
        "Donation records": "दान रिकॉर्ड",
        "Source": "स्रोत",
        "Online": "ऑनलाइन",
        "Offline": "ऑफलाइन",
        "General donation": "सामान्य दान",
        "Accept offer": "दान प्रस्ताव स्वीकार करें",
        "Verify receipt": "प्राप्ति सत्यापित करें",
        "No donations have been registered yet.": "अभी तक कोई दान पंजीकृत नहीं किया गया है।",
        "Choose camera scanning, upload a QR image, or enter the printed donation ID.": "कैमरे से स्कैन करें, QR छवि अपलोड करें या प्रिंट किया गया दान ID दर्ज करें।",
        "Camera stopped. You can restart scanning or upload a QR image.": "कैमरा बंद है। आप दोबारा स्कैन कर सकते हैं या QR छवि अपलोड कर सकते हैं।",
        "Camera active. Hold the donation QR code inside the four white corners.": "कैमरा चालू है। दान का QR कोड चार सफेद कोनों के भीतर रखें।",
        "The camera could not be opened.": "कैमरा नहीं खुल सका।",

        "Record a processing update": "प्रक्रिया अपडेट दर्ज करें",
        "Processing stage": "प्रक्रिया का चरण",
        "Items sorted": "सामग्री छाँटी गई",
        "Allocated to a programme": "कार्यक्रम के लिए आवंटित",
        "Dispatched": "भेज दिया गया",
        "Delivery confirmed": "डिलीवरी की पुष्टि हुई",
        "Distribution reported": "वितरण दर्ज किया गया",
        "Batch reference": "बैच संदर्भ",
        "Batch code": "बैच कोड",
        "Evidence or explanation": "प्रमाण या विवरण",
        "Record update": "अपडेट दर्ज करें",
        "Frontline quick update": "मैदानी त्वरित अपडेट",
        "Optional note": "वैकल्पिक टिप्पणी",
        "People assisted (optional)": "सहायता प्राप्त लोगों की संख्या (वैकल्पिक)",
        "Mark as received / verify": "प्राप्त के रूप में दर्ज करें / सत्यापित करें",
        "Mark as distributed": "वितरित के रूप में दर्ज करें",
        "Cancel donation offer": "दान प्रस्ताव रद्द करें",
        "Record a processing update": "प्रक्रिया अपडेट दर्ज करें",
        "Update product progress": "उत्पाद प्रगति अपडेट करें",
        "Progress milestone": "प्रगति का चरण",
        "Procurement started": "खरीद प्रक्रिया शुरू हुई",
        "Supplies procured": "सामग्री खरीदी गई",
        "Supplies prepared": "सामग्री तैयार की गई",
        "Allocated to response": "राहत कार्य के लिए आवंटित",
        "Supplies dispatched": "सामग्री भेजी गई",
        "Supplies delivered": "सामग्री पहुँचाई गई",
        "Supplies reached people in need": "सामग्री ज़रूरतमंद लोगों तक पहुँची",
        "Contribution request recorded": "योगदान अनुरोध दर्ज किया गया",
        "Procurement progress": "खरीद की प्रगति",
        "Record progress update": "प्रगति अपडेट दर्ज करें",
        "Optional update note": "वैकल्पिक अपडेट टिप्पणी",
        "Offline walk-in donation.": "ऑफलाइन प्रत्यक्ष दान।",

        // =====================================================
        // COMMON ERROR AND SUCCESS MESSAGES
        // =====================================================

        "Access denied.": "पहुँच अस्वीकृत।",
        "No records found.": "कोई रिकॉर्ड नहीं मिला।",
        "Your NGO profile has been updated.": "आपकी NGO प्रोफ़ाइल अपडेट कर दी गई है।",
        "Campaign submitted for administrator approval.": "अभियान प्रशासक की स्वीकृति के लिए जमा कर दिया गया है।",
        "Campaign approved and published.": "अभियान स्वीकृत कर प्रकाशित कर दिया गया है।",
        "Campaign rejected.": "अभियान अस्वीकृत कर दिया गया है।",
        "Donation processing update recorded.": "दान की प्रक्रिया का अपडेट दर्ज कर दिया गया है।",
        "Your donation offer has been registered.": "आपका दान प्रस्ताव पंजीकृत कर दिया गया है।",
        "Your procurement request has been recorded.": "आपका खरीद अनुरोध दर्ज कर लिया गया है।",
        "Physical in-kind donation has been registered.": "भौतिक वस्तु दान पंजीकृत कर लिया गया है।",
        "Donation offer accepted.": "दान प्रस्ताव स्वीकार कर लिया गया है।",
        "Receipt verified.": "प्राप्ति सत्यापित कर ली गई है।",

        // =====================================================
        // DEFAULT CAMPAIGN STORY TEXT
        // Exact standard paragraphs are translated. NGO-written
        // custom stories need their own Hindi text or a translation
        // service; this dictionary cannot translate arbitrary prose.
        // =====================================================

        "The receiving organisation will update this section with the current urgency and community needs.": "प्राप्तकर्ता संगठन इस अनुभाग में मौजूदा तात्कालिक ज़रूरतों और समुदाय की आवश्यकताओं की जानकारी देगा।",
        "Each accepted item helps the receiving organisation address its listed supply requirements.": "स्वीकृत प्रत्येक वस्तु प्राप्तकर्ता संगठन की सूचीबद्ध सामग्री आवश्यकताओं को पूरा करने में मदद करती है।",
        "The receiving organisation checks incoming supplies and keeps campaign records updated.": "प्राप्तकर्ता संगठन आने वाली सामग्री की जाँच करता है और अभियान के रिकॉर्ड अपडेट रखता है।",
        "Choose the relief products you would like Umeed to arrange from suppliers. The amount shown is an indicative demo value per unit.": "वे राहत उत्पाद चुनें जिन्हें आप उम्मीद से आपूर्तिकर्ताओं के माध्यम से मँगवाना चाहते हैं। दिखाई गई राशि प्रति इकाई अनुमानित मूल्य है।",
        "Choose the relief products you would like Umeed to arrange from suppliers. Prices are estimated unit costs and may change with supplier quotations.": "वे राहत उत्पाद चुनें जिन्हें आप उम्मीद से आपूर्तिकर्ताओं के माध्यम से मँगवाना चाहते हैं। कीमतें अनुमानित प्रति इकाई लागत हैं और आपूर्तिकर्ताओं के कोटेशन के अनुसार बदल सकती हैं।",

        // =====================================================
        // PRODUCT NAMES — COMMON ITEMS
        // =====================================================

        "Iodised salt (1 kg)": "आयोडीन युक्त नमक (1 किलो)",
        "Salt (1 kg)": "नमक (1 किलो)",
        "Sugar (1 kg)": "चीनी (1 किलो)",
        "Atta (5 kg bag)": "आटा (5 किलो का बैग)",
        "Masoor dal (1 kg pack)": "मसूर दाल (1 किलो का पैक)",
        "Rechargeable LED torch (1 unit)": "रीचार्जेबल LED टॉर्च (1 नग)",
        "Baby food (300 g pack)": "बेबी फूड (300 ग्राम का पैक)",
        "Powdered milk (500 g pack)": "पाउडर दूध (500 ग्राम का पैक)",
        "Poha (1 kg)": "पोहा (1 किलो)",
        "Rice (5 kg bag)": "चावल (5 किलो का बैग)",
        "Mineral water (1 L bottle)": "मिनरल वॉटर (1 लीटर की बोतल)",
        "Tarpaulin sheet (12 x 15 ft)": "तिरपाल शीट (12 x 15 फीट)",

        // =====================================================
        // STATUS WORDS
        // =====================================================

        "Offered": "प्रस्तावित",
        "Accepted": "स्वीकृत",
        "Received": "प्राप्त",
        "Verified": "सत्यापित",
        "Cancelled": "रद्द",
        "Rejected": "अस्वीकृत",
        "Sorted": "छँटी हुई",
        "Allocated": "आवंटित",
        "Dispatched": "भेजा गया",
        "Delivered": "पहुँचाया गया",
        "Fulfilled": "पूरा हुआ",
        "In progress": "प्रगति पर",
        "Needs supplies": "सामग्री की आवश्यकता",
        "Target reached": "लक्ष्य पूरा",
        "Almost fulfilled": "लगभग पूरा",
        "Fully committed — awaiting delivery": "पूरी मात्रा प्रतिबद्ध — डिलीवरी की प्रतीक्षा में"
    };

    // Text in placeholders is translated separately from visible text.
    const placeholders = {
        "Example: UM-DA873DFDD705FD21": "उदाहरण: UM-DA873DFDD705FD21",
        "Enter your name": "अपना नाम दर्ज करें",
        "Enter your organisation's name": "अपने संगठन का नाम दर्ज करें",
        "City, state": "शहर, राज्य",
        "Search campaigns": "अभियान खोजें",
        "Packing or delivery note": "पैकिंग या डिलीवरी टिप्पणी",
        "Shortage, damage or context": "कमी, नुकसान या अन्य जानकारी"
    };

    const reverseTranslations = {};
    Object.entries(translations).forEach(([english, hindi]) => {
        if (!(hindi in reverseTranslations)) {
            reverseTranslations[hindi] = english;
        }
    });

    const reversePlaceholders = {};
    Object.entries(placeholders).forEach(([english, hindi]) => {
        reversePlaceholders[hindi] = english;
    });

    const originalText = new WeakMap();
    const lastRenderedText = new WeakMap();
    const originalAttributes = new WeakMap();
    const lastRenderedAttributes = new WeakMap();

    const normalise = value =>
        String(value ?? "")
            .replace(/\u00A0/g, " ")
            .replace(/\s+/g, " ")
            .trim();

    const sortedPhrases = Object.entries(translations)
        .sort((a, b) => b[0].length - a[0].length);

    function translateDynamicText(source, language) {
        if (language !== "hi") {
            return source;
        }

        let result = source;

        // Example: 5 / 30 accepted
        result = result.replace(
            /^(\s*)(\d+)\s*\/\s*(\d+)\s+accepted(\s*)$/i,
            "$1$2 / $3 स्वीकृत$4"
        );

        // Example: 100 still available
        result = result.replace(
            /^(\s*)(\d+)\s+still available(\s*)$/i,
            "$1$2 अभी उपलब्ध$3"
        );

        // Example: 100 still available for new offers
        result = result.replace(
            /^(\s*)(\d+)\s+still available for new offers(\s*)$/i,
            "$1$2 नए प्रस्तावों के लिए अभी उपलब्ध$3"
        );

        // Example: Committed / awaiting verification: 2
        result = result.replace(
            /^(\s*)Committed\s*\/\s*awaiting verification:\s*(\d+)(\s*)$/i,
            "$1प्रतिबद्ध / सत्यापन की प्रतीक्षा में: $2$3"
        );

        // Example: Category: Natural disaster
        result = result.replace(
            /\bCategory:\s*/gi,
            "श्रेणी: "
        );

        // Example: Location: Ahmedabad, Gujarat
        result = result.replace(
            /\bLocation:\s*/gi,
            "स्थान: "
        );

        // Example: Requirements last recorded: ...
        result = result.replace(
            /\bRequirements last recorded:\s*/gi,
            "ज़रूरतें अंतिम बार दर्ज की गईं: "
        );

        return result;
    }

    function translateText(source, language) {
        if (language !== "hi") {
            return source;
        }

        const cleaned = normalise(source);

        if (!cleaned) {
            return source;
        }

        // Exact translations take priority.
        if (Object.prototype.hasOwnProperty.call(translations, cleaned)) {
            return source.replace(cleaned, translations[cleaned]);
        }

        const dynamic = translateDynamicText(source, language);

        if (dynamic !== source) {
            return dynamic;
        }

        // Try longer phrases before shorter phrases.
        // Word boundaries prevent translating part of a larger word.
        let result = source;

        for (const [english, hindi] of sortedPhrases) {
            if (english.length < 4) {
                continue;
            }

            const escaped = english.replace(
                /[.*+?^${}()|[\]\\]/g,
                "\\$&"
            );

            const startsWithWord = /^[a-z0-9]/i.test(english);
            const endsWithWord = /[a-z0-9]$/i.test(english);

            const pattern =
                (startsWithWord ? "\\b" : "")
                + escaped
                + (endsWithWord ? "\\b" : "");

            result = result.replace(
                new RegExp(pattern, "gi"),
                hindi
            );
        }

        return result;
    }

    function ignoredTextNode(node) {
        const parent = node.parentElement;

        if (!parent) {
            return true;
        }

        return Boolean(parent.closest(
            [
                "script",
                "style",
                "textarea",
                "code",
                "pre",
                "[contenteditable='true']",
                "[data-no-translate]",
                ".ngo-description-text",
                ".user-content",
                ".donation-user-notes"
            ].join(",")
        ));
    }

    function getOriginalText(node, currentValue) {
        const previousRendered = lastRenderedText.get(node);

        if (!originalText.has(node)) {
            originalText.set(node, currentValue);
            return currentValue;
        }

        // If another script changes this text after translation,
        // store that new text as the new original.
        if (
            previousRendered !== undefined
            && currentValue !== previousRendered
        ) {
            originalText.set(node, currentValue);
            return currentValue;
        }

        return originalText.get(node);
    }

    function translateTextNodes(language) {
        if (!document.body) {
            return;
        }

        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT
        );

        const nodes = [];

        while (walker.nextNode()) {
            nodes.push(walker.currentNode);
        }

        nodes.forEach(node => {
            if (ignoredTextNode(node)) {
                return;
            }

            const current = node.nodeValue;

            if (!normalise(current)) {
                return;
            }

            const source = getOriginalText(node, current);
            const translated = translateText(source, language);

            if (translated !== current) {
                node.nodeValue = translated;
            }

            lastRenderedText.set(node, node.nodeValue);
        });
    }

    function translateExplicitElements(language) {
        document.querySelectorAll("[data-en][data-hi]").forEach(element => {
            // Don't replace a button's nested icons or other child markup.
            if (element.children.length > 0) {
                return;
            }

            const translated = element.getAttribute(
                language === "hi" ? "data-hi" : "data-en"
            );

            if (translated !== null) {
                element.textContent = translated;
            }
        });
    }

    function translateAttributes(language) {
        const attributes = [
            "placeholder",
            "aria-label",
            "title",
            "alt"
        ];

        document.querySelectorAll(
            "input, textarea, button, select, a, img, [aria-label], [title]"
        ).forEach(element => {
            if (element.closest("[data-no-translate]")) {
                return;
            }

            attributes.forEach(attribute => {
                if (!element.hasAttribute(attribute)) {
                    return;
                }

                let saved = originalAttributes.get(element);

                if (!saved) {
                    saved = {};
                    originalAttributes.set(element, saved);
                }

                let last = lastRenderedAttributes.get(element);

                if (!last) {
                    last = {};
                    lastRenderedAttributes.set(element, last);
                }

                const current = element.getAttribute(attribute);

                if (
                    saved[attribute] === undefined
                    || (
                        last[attribute] !== undefined
                        && current !== last[attribute]
                    )
                ) {
                    saved[attribute] = current;
                }

                const source = saved[attribute];

                const dictionary =
                    attribute === "placeholder"
                        ? placeholders
                        : translations;

                const reverseDictionary =
                    attribute === "placeholder"
                        ? reversePlaceholders
                        : reverseTranslations;

                let translated = source;

                if (language === "hi") {
                    translated =
                        dictionary[normalise(source)]
                        || translateText(source, language);
                } else {
                    translated =
                        reverseDictionary[normalise(source)]
                        || source;
                }

                element.setAttribute(attribute, translated);
                last[attribute] = translated;
            });
        });
    }

    function updateLanguageButtons(language) {
        document.querySelectorAll("[data-language]").forEach(button => {
            const selected = button.dataset.language === language;

            button.setAttribute("aria-pressed", String(selected));
            button.classList.toggle("language-active", selected);
            button.classList.toggle("is-active", selected);
        });
    }

    function applyLanguage(language) {
        language = language === "hi" ? "hi" : "en";

        document.documentElement.lang = language;

        translateExplicitElements(language);
        translateTextNodes(language);
        translateAttributes(language);
        updateLanguageButtons(language);

        try {
            localStorage.setItem(LANGUAGE_KEY, language);
        } catch (error) {
            console.warn("Could not save language preference.", error);
        }

        document.dispatchEvent(
            new CustomEvent("umeed:language-change", {
                detail: { language }
            })
        );
    }

    // Restore the saved language even if a page is missing the buttons.
    function getSavedLanguage() {
        try {
            const saved = localStorage.getItem(LANGUAGE_KEY);
            return saved === "hi" ? "hi" : "en";
        } catch (error) {
            return "en";
        }
    }

    function initialiseLanguage() {
        // Connect the existing English / Hindi buttons.
        document.querySelectorAll("[data-language]").forEach(button => {
            button.addEventListener("click", event => {
                event.preventDefault();
                applyLanguage(button.dataset.language);
            });
        });

        applyLanguage(getSavedLanguage());

        // Translate elements inserted later, such as product rows
        // added dynamically in the NGO campaign editor.
        let mutationTimer = null;

        const observer = new MutationObserver(records => {
            const hasRelevantChanges = records.some(record => {
                if (record.type === "childList") {
                    return record.addedNodes.length > 0;
                }

                return record.type === "characterData";
            });

            if (!hasRelevantChanges) {
                return;
            }

            clearTimeout(mutationTimer);

            mutationTimer = setTimeout(() => {
                applyLanguage(getSavedLanguage());
            }, 80);
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });

        // Apply language to newly added buttons.
        document.addEventListener("click", () => {
            updateLanguageButtons(getSavedLanguage());
        }, true);
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initialiseLanguage,
            { once: true }
        );
    } else {
        initialiseLanguage();
    }

})();