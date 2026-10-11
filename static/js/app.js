document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // CONFIGURATION
    // ==========================================

    const LANGUAGE_KEY = "umeed-language";

    const languageButtons = document.querySelectorAll(
        "[data-language]"
    );


    if (languageButtons.length === 0) {
        return;
    }


    // Keep original text so switching languages works repeatedly.

    const originalText = new WeakMap();
    const lastTranslatedText = new WeakMap();

    const originalAttributes = new WeakMap();
    const lastTranslatedAttributes = new WeakMap();


    // ==========================================
    // ENGLISH TO HINDI TRANSLATIONS
    // ==========================================

    const translations = {

        // --------------------------------------
        // NAVIGATION
        // --------------------------------------

        "Home": "होम",
        "Explore Campaigns": "अभियान खोजें",
        "Affiliated NGOs": "संबद्ध NGO",
        "My Donations": "मेरे दान",
        "Our Donations": "हमारे दान",
        "Our Campaigns": "हमारे अभियान",
        "Create Campaign": "अभियान बनाएँ",
        "Offline Donations": "ऑफलाइन दान",
        "Create Offline Donation": "ऑफलाइन दान दर्ज करें",
        "NGO Workspace": "NGO कार्यक्षेत्र",
        "Admin Panel": "एडमिन पैनल",
        "Login": "लॉग इन",
        "Create Account": "खाता बनाएँ",
        "Sign out": "लॉग आउट",
        "Sign in": "लॉग इन करें",
        "Sign in to continue.": "जारी रखने के लिए लॉग इन करें।",
        "English": "English",
        "हिन्दी": "हिन्दी",

        "Cancel": "रद्द करें",
        "Save": "सहेजें",
        "Save changes": "बदलाव सहेजें",
        "Save profile": "प्रोफ़ाइल सहेजें",
        "Submit": "जमा करें",
        "Update": "अपडेट करें",
        "Back": "वापस",
        "Back to dashboard": "डैशबोर्ड पर वापस जाएँ",
        "View details": "विवरण देखें",
        "View record": "रिकॉर्ड देखें",
        "View more": "और देखें",
        "Search": "खोजें",
        "Filter": "फ़िल्टर करें",
        "Actions": "कार्रवाई",


        // --------------------------------------
        // HOMEPAGE
        // --------------------------------------

        "Welcome to Umeed": "उम्मीद में आपका स्वागत है",
        "Verified relief campaigns": "सत्यापित राहत अभियान",
        "A little help.": "थोड़ी सी मदद।",
        "A little more hope.": "थोड़ी और उम्मीद।",
        "Every contribution matters.": "हर योगदान महत्वपूर्ण है।",
        "Your generosity.": "आपकी उदारता।",
        "Your kindness.": "आपकी दयालुता।",
        "Their hope.": "उनकी उम्मीद।",
        "For every helping hand": "हर मदद करने वाले के लिए",
        "Make your contribution count.": "अपने योगदान को सार्थक बनाएँ।",
        "Relief begins with readiness.": "राहत की शुरुआत तैयारी से होती है।",
        "Donate supplies": "सामग्री दान करें",
        "My donations": "मेरे दान",
        "Find campaigns": "अभियान खोजें",
        "Become a donor": "दाता बनें",
        "Already registered?": "पहले से पंजीकृत हैं?",
        "Browse relief campaigns": "राहत अभियान खोजें",
        "Campaign management": "अभियान प्रबंधन",
        "Register offline donations": "ऑफलाइन दान दर्ज करें",
        "Manage donations": "दान प्रबंधित करें",
        "View my donations": "मेरे दान देखें",
        "Open donations": "दान खोलें",
        "Open Admin Panel": "एडमिन पैनल खोलें",
        "Create an account": "अपना खाता बनाएँ",


        // --------------------------------------
        // REGISTRATION
        // --------------------------------------

        "Join Umeed to contribute supplies or manage an NGO.":
            "सामग्री दान करने या NGO प्रबंधित करने के लिए उम्मीद से जुड़ें।",

        "Your name": "आपका नाम",
        "Email address": "ईमेल पता",
        "Password": "पासवर्ड",
        "Account type": "खाते का प्रकार",
        "Donor": "दाता",
        "NGO representative": "NGO प्रतिनिधि",
        "NGO name": "NGO का नाम",
        "NGO location": "NGO का स्थान",
        "About your organisation": "आपके संगठन के बारे में",
        "Create account": "खाता बनाएँ",
        "Use at least 8 characters.": "कम से कम 8 अक्षरों का उपयोग करें।",
        "Please complete all required fields.": "कृपया सभी आवश्यक फ़ील्ड भरें।",
        "An account with this email already exists.": "इस ईमेल से खाता पहले से मौजूद है।",
        "Your password must contain at least 8 characters.": "आपके पासवर्ड में कम से कम 8 अक्षर होने चाहिए।",
        "Incorrect email or password.": "ईमेल या पासवर्ड गलत है।",
        "Welcome back.": "वापस स्वागत है।",
        "You have signed out.": "आपने लॉग आउट कर लिया है।",


        // --------------------------------------
        // NGO PROFILE
        // --------------------------------------

        "Edit NGO Profile": "NGO प्रोफ़ाइल संपादित करें",
        "Organisation name": "संगठन का नाम",
        "Location": "स्थान",
        "The organisations behind the relief": "राहत कार्य करने वाले संगठन",
        "This organisation has not added a profile description yet.":
            "इस संगठन ने अभी तक अपना परिचय नहीं जोड़ा है।",

        "No affiliated NGOs yet": "अभी कोई संबद्ध NGO नहीं है",
        "Explore campaigns": "अभियान देखें",
        "Explore campaigns →": "अभियान देखें →",
        "Save profile": "प्रोफ़ाइल सहेजें",
        "Update profile": "प्रोफ़ाइल अपडेट करें",


        // --------------------------------------
        // CAMPAIGNS
        // --------------------------------------

        "Verified Relief Campaigns": "सत्यापित राहत अभियान",
        "Verified relief initiatives": "सत्यापित राहत पहल",
        "Active campaigns": "सक्रिय अभियान",
        "No active campaigns yet": "अभी कोई सक्रिय अभियान नहीं है",
        "Create campaign": "अभियान बनाएँ",
        "Create a campaign": "अभियान बनाएँ",
        "Campaign title": "अभियान का शीर्षक",
        "Campaign location": "अभियान का स्थान",
        "Emergency": "आपातस्थिति",
        "Emergency type": "आपातस्थिति का प्रकार",
        "Required items": "आवश्यक सामग्री",
        "Description": "विवरण",
        "View more →": "और देखें →",
        "Close campaign": "अभियान बंद करें",
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


        // --------------------------------------
        // INCOMING DONATIONS
        // --------------------------------------

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
        "Campaign": "अभियान",
        "Status": "स्थिति",
        "Registered": "पंजीकरण की तारीख",
        "Online": "ऑनलाइन",
        "Offline": "ऑफलाइन",
        "Verified": "सत्यापित",
        "General donation": "सामान्य दान",
        "Accept offer": "दान प्रस्ताव स्वीकार करें",
        "Verify receipt": "प्राप्ति सत्यापित करें",

        "No donations have been registered yet.":
            "अभी तक कोई दान पंजीकृत नहीं किया गया है।",

        "Choose camera scanning, upload a QR image, or enter the printed donation ID.":
            "कैमरे से स्कैन करें, QR छवि अपलोड करें या प्रिंट किया गया दान ID दर्ज करें।",

        "Camera stopped. You can restart scanning or upload a QR image.":
            "कैमरा बंद है। आप दोबारा स्कैन कर सकते हैं या QR छवि अपलोड कर सकते हैं।",

        "Camera active. Hold the donation QR code inside the four white corners.":
            "कैमरा चालू है। दान का QR कोड चार सफेद कोनों के भीतर रखें।",

        "The camera could not be opened.":
            "कैमरा नहीं खुल सका।",


        // --------------------------------------
        // DONATION HISTORY
        // --------------------------------------

        "Donation history": "दान का इतिहास",
        "Recorded events and their timestamps.": "दर्ज घटनाएँ और उनके समय।",
        "Offer Submitted": "दान प्रस्ताव जमा किया गया",
        "Intake Verified": "प्राप्त सामग्री सत्यापित की गई",
        "Delivery Confirmed": "डिलीवरी की पुष्टि की गई",
        "Donation Passport": "दान पासपोर्ट",
        "Your Donation Passport": "आपका दान पासपोर्ट",
        "Donation record": "दान रिकॉर्ड",
        "Declared quantity": "घोषित मात्रा",
        "Received quantity": "प्राप्त मात्रा",
        "Accepted quantity": "स्वीकृत मात्रा",
        "Rejected quantity": "अस्वीकृत मात्रा",
        "Processing update": "प्रक्रिया अपडेट",
        "Record a processing update": "प्रक्रिया अपडेट दर्ज करें",
        "Delivery method": "डिलीवरी का तरीका",
        "Donation items": "दान की गई सामग्री",
        "Item name": "सामग्री का नाम",
        "Quantity": "मात्रा",
        "Condition": "स्थिति",
        "Notes": "टिप्पणियाँ",
        "Batch code": "बैच कोड",
        "Received": "प्राप्त",
        "Accepted": "स्वीकृत",
        "Rejected": "अस्वीकृत",

        "Offer submitted": "दान प्रस्ताव जमा किया गया",
        "Intake verified": "प्राप्त सामग्री सत्यापित की गई",
        "Delivery confirmed": "डिलीवरी की पुष्टि की गई",


        // --------------------------------------
        // COMMON FORM FIELDS
        // --------------------------------------

        "Required": "आवश्यक",
        "Optional": "वैकल्पिक",
        "Choose an option": "एक विकल्प चुनें",
        "Select an option": "एक विकल्प चुनें",
        "Choose campaign": "अभियान चुनें",
        "Choose emergency type": "आपातस्थिति का प्रकार चुनें",
        "Upload": "अपलोड करें",
        "Download": "डाउनलोड करें",
        "Print": "प्रिंट करें",
        "Continue": "जारी रखें",
        "Confirm": "पुष्टि करें",
        "Close": "बंद करें",
        "Refresh": "रीफ़्रेश करें",


        // --------------------------------------
        // COMMON FEEDBACK AND STATUS MESSAGES
        // --------------------------------------

        "Your account has been created successfully.":
            "आपका खाता सफलतापूर्वक बनाया गया है।",

        "Your NGO registration is awaiting administrator approval.":
            "आपका NGO पंजीकरण प्रशासक की स्वीकृति की प्रतीक्षा में है।",

        "Please sign in to continue.":
            "जारी रखने के लिए लॉग इन करें।",

        "Access denied.": "पहुँच अस्वीकृत।",
        "No records found.": "कोई रिकॉर्ड नहीं मिला।",

        "Your NGO profile has been updated.":
            "आपकी NGO प्रोफ़ाइल अपडेट कर दी गई है।",

        "Campaign submitted for administrator approval.":
            "अभियान प्रशासक की स्वीकृति के लिए जमा कर दिया गया है।",

        "Campaign approved and published.":
            "अभियान स्वीकृत कर प्रकाशित कर दिया गया है।",

        "Campaign rejected.": "अभियान अस्वीकृत कर दिया गया है।",

        "Donation processing update recorded.":
            "दान की प्रक्रिया का अपडेट दर्ज कर दिया गया है।",

        "Your donation offer has been registered.":
            "आपका दान प्रस्ताव पंजीकृत कर दिया गया है।"


    };


    // ==========================================
    // INPUT PLACEHOLDER TRANSLATIONS
    // ==========================================

    const placeholders = {

        "Example: UM-DA873DFDD705FD21":
            "उदाहरण: UM-DA873DFDD705FD21",

        "Enter your name":
            "अपना नाम दर्ज करें",

        "Enter your organisation's name":
            "अपने संगठन का नाम दर्ज करें",

        "City, state":
            "शहर, राज्य",

        "Search campaigns":
            "अभियान खोजें",

        "Search":
            "खोजें"

    };


    // ==========================================
    // REVERSE TRANSLATION MAP
    // ==========================================

    const reverseTranslations = {};

    Object.entries(translations).forEach(function ([english, hindi]) {

        if (!reverseTranslations[hindi]) {

            reverseTranslations[hindi] = english;

        }

    });


    const reversePlaceholders = {};

    Object.entries(placeholders).forEach(function ([english, hindi]) {

        reversePlaceholders[hindi] = english;

    });


    // ==========================================
    // NORMALISE TEXT
    // ==========================================

    function normaliseText(value) {

        return value
            .replace(/\u00A0/g, " ")
            .replace(/\s+/g, " ")
            .trim();

    }


    // ==========================================
    // TRANSLATE A TEXT VALUE
    // ==========================================

    function translateValue(value, language, dictionary, reverseDictionary) {

        const cleanValue = normaliseText(value);

        if (language === "hi") {

            return dictionary[cleanValue] || value;

        }

        return reverseDictionary[cleanValue] || value;

    }


    // ==========================================
    // TRANSLATE EXPLICITLY BILINGUAL ELEMENTS
    // ==========================================

    function translateAttributedElements(language) {

        document.querySelectorAll(
            "[data-en][data-hi]"
        ).forEach(function (element) {

            const translatedText = element.getAttribute(
                "data-" + language
            );

            if (translatedText !== null) {

                element.textContent = translatedText;

            }

        });

    }


    // ==========================================
    // TRANSLATE COMMON PAGE TEXT
    // ==========================================

    function translatePageText(language) {

        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT
        );

        const textNodes = [];

        while (walker.nextNode()) {

            textNodes.push(walker.currentNode);

        }


        textNodes.forEach(function (node) {

            const parent = node.parentElement;

            if (!parent) {
                return;
            }


            // Do not translate scripts, styles, inputs,
            // editable fields, or explicit bilingual elements.

            if (
                parent.closest(
                    "script, style, textarea, [contenteditable='true'], [data-en][data-hi], [data-no-translate]"
                )
            ) {

                return;

            }


            // Do not translate user-authored descriptions.

            if (
                parent.closest(
                    ".ngo-description-text, .user-content, .donation-user-notes"
                )
            ) {

                return;

            }


            const currentText = node.nodeValue;


            if (!normaliseText(currentText)) {
                return;
            }


            let sourceText = originalText.get(node);

            const previousTranslation = lastTranslatedText.get(node);


            // Save original content the first time we see a node.

            if (sourceText === undefined) {

                sourceText = currentText;

                originalText.set(
                    node,
                    sourceText
                );

            }


            // Detect text changed by another script, for example,
            // the QR scanner status message.

            else if (
                previousTranslation !== undefined
                && currentText !== previousTranslation
            ) {

                sourceText = currentText;

                originalText.set(
                    node,
                    sourceText
                );

            }


            const translatedText = translateValue(
                sourceText,
                language,
                translations,
                reverseTranslations
            );


            if (translatedText !== currentText) {

                const leadingWhitespace =
                    currentText.match(/^\s*/)[0];

                const trailingWhitespace =
                    currentText.match(/\s*$/)[0];


                node.nodeValue =
                    leadingWhitespace
                    + translatedText
                    + trailingWhitespace;

            }


            lastTranslatedText.set(
                node,
                node.nodeValue
            );

        });

    }


    // ==========================================
    // TRANSLATE PLACEHOLDERS AND ACCESSIBLE LABELS
    // ==========================================

    function translateAttributes(language) {

        const attributeNames = [
            "placeholder",
            "aria-label",
            "title"
        ];


        document.querySelectorAll(
            "input, textarea, button, select, a, [aria-label], [title]"
        ).forEach(function (element) {

            attributeNames.forEach(function (attributeName) {

                if (!element.hasAttribute(attributeName)) {
                    return;
                }


                let savedValues = originalAttributes.get(element);


                if (!savedValues) {

                    savedValues = {};

                    originalAttributes.set(
                        element,
                        savedValues
                    );

                }


                let savedTranslations =
                    lastTranslatedAttributes.get(element);


                if (!savedTranslations) {

                    savedTranslations = {};

                    lastTranslatedAttributes.set(
                        element,
                        savedTranslations
                    );

                }


                const currentValue = element.getAttribute(
                    attributeName
                );


                if (
                    savedValues[attributeName] === undefined
                    || (
                        savedTranslations[attributeName] !== undefined
                        && currentValue !== savedTranslations[attributeName]
                    )
                ) {

                    savedValues[attributeName] = currentValue;

                }


                const sourceValue = savedValues[attributeName];

                let translatedValue = sourceValue;


                if (attributeName === "placeholder") {

                    translatedValue = translateValue(
                        sourceValue,
                        language,
                        placeholders,
                        reversePlaceholders
                    );

                } else {

                    translatedValue = translateValue(
                        sourceValue,
                        language,
                        translations,
                        reverseTranslations
                    );

                }


                element.setAttribute(
                    attributeName,
                    translatedValue
                );


                savedTranslations[attributeName] = translatedValue;

            });

        });

    }


    // ==========================================
    // UPDATE LANGUAGE BUTTON APPEARANCE
    // ==========================================

    function updateLanguageButtons(language) {

        languageButtons.forEach(function (button) {

            const isSelected =
                button.dataset.language === language;


            button.setAttribute(
                "aria-pressed",
                String(isSelected)
            );


            // Support both existing class names.

            button.classList.toggle(
                "language-active",
                isSelected
            );

            button.classList.toggle(
                "is-active",
                isSelected
            );

        });

    }


    // ==========================================
    // APPLY THE SELECTED LANGUAGE
    // ==========================================

    function setLanguage(language) {

        if (language !== "hi" && language !== "en") {

            language = "en";

        }


        // Translate elements with data-en and data-hi.

        translateAttributedElements(language);


        // Translate common text on pages without bilingual attributes.

        translatePageText(language);


        // Translate placeholders, titles, and accessible labels.

        translateAttributes(language);


        // Update the HTML language declaration.

        document.documentElement.lang = language;


        // Highlight the selected language button.

        updateLanguageButtons(language);


        // Remember the selection across page navigation.

        try {

            localStorage.setItem(
                LANGUAGE_KEY,
                language
            );

        } catch (error) {

            console.warn(
                "Could not save the language preference.",
                error
            );

        }


        // Let components react to a language change if required.

        document.dispatchEvent(
            new CustomEvent(
                "umeed:language-change",
                {
                    detail: {
                        language: language
                    }
                }
            )
        );

    }


    // ==========================================
    // CONNECT LANGUAGE BUTTONS
    // ==========================================

    languageButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            setLanguage(
                button.dataset.language
            );

        });

    });


    // ==========================================
    // RESTORE PREVIOUSLY SELECTED LANGUAGE
    // ==========================================

    let savedLanguage = "en";


    try {

        savedLanguage =
            localStorage.getItem(LANGUAGE_KEY) || "en";

    } catch (error) {

        console.warn(
            "Could not restore the saved language.",
            error
        );

    }


    setLanguage(savedLanguage);

});