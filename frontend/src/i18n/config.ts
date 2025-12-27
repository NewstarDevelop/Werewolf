import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Initialize i18next with React integration
i18n
  .use(Backend)  // Load translations from public/locales
  .use(LanguageDetector)  // Detect user language preference
  .use(initReactI18next)  // React binding
  .init({
    fallbackLng: 'zh',  // Default to Chinese
    supportedLngs: ['zh', 'en'],  // Supported languages
    defaultNS: 'common',  // Default namespace
    ns: ['common', 'game', 'roles'],  // Available namespaces

    backend: {
      // Path to translation files
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },

    interpolation: {
      escapeValue: false,  // React already handles XSS
    },

    detection: {
      // Language detection order: localStorage > navigator language
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],  // Cache language preference
      lookupLocalStorage: 'i18nextLng',
    },

    react: {
      useSuspense: true,  // Use Suspense for loading translations
      bindI18n: 'languageChanged loaded',
      bindI18nStore: 'added removed',
    },

    // Development mode settings
    debug: import.meta.env.DEV,
  });

export default i18n;
