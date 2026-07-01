/*
 * Conflict Zero - Multi-Country Selector Component
 * Fase 3 Enterprise - Country configuration and document validation
 */

export interface CountryInfo {
  code: string;
  name: string;
  currency: string;
  currencySymbol: string;
  documentLabel: string;
  documentExample: string;
  flag: string;
  timezone: string;
  language: string;
  phonePrefix: string;
  vatLabel: string;
  vatRate: number;
}

export const SUPPORTED_COUNTRIES: CountryInfo[] = [
  {
    code: 'PE',
    name: 'Perú',
    currency: 'PEN',
    currencySymbol: 'S/',
    documentLabel: 'RUC',
    documentExample: '20100130204',
    flag: '🇵🇪',
    timezone: 'America/Lima',
    language: 'es',
    phonePrefix: '+51',
    vatLabel: 'IGV',
    vatRate: 0.18,
  },
  {
    code: 'CL',
    name: 'Chile',
    currency: 'CLP',
    currencySymbol: '$',
    documentLabel: 'RUT',
    documentExample: '76.123.456-K',
    flag: '🇨🇱',
    timezone: 'America/Santiago',
    language: 'es',
    phonePrefix: '+56',
    vatLabel: 'IVA',
    vatRate: 0.19,
  },
  {
    code: 'CO',
    name: 'Colombia',
    currency: 'COP',
    currencySymbol: '$',
    documentLabel: 'NIT',
    documentExample: '900.123.456-7',
    flag: '🇨🇴',
    timezone: 'America/Bogota',
    language: 'es',
    phonePrefix: '+57',
    vatLabel: 'IVA',
    vatRate: 0.19,
  },
  {
    code: 'MX',
    name: 'México',
    currency: 'MXN',
    currencySymbol: '$',
    documentLabel: 'RFC',
    documentExample: 'ABCD010101ABC',
    flag: '🇲🇽',
    timezone: 'America/Mexico_City',
    language: 'es',
    phonePrefix: '+52',
    vatLabel: 'IVA',
    vatRate: 0.16,
  },
  {
    code: 'ES',
    name: 'España',
    currency: 'EUR',
    currencySymbol: '€',
    documentLabel: 'NIF/CIF',
    documentExample: 'B12345678',
    flag: '🇪🇸',
    timezone: 'Europe/Madrid',
    language: 'es',
    phonePrefix: '+34',
    vatLabel: 'IVA',
    vatRate: 0.21,
  },
];

export function getCountryByCode(code: string): CountryInfo | undefined {
  return SUPPORTED_COUNTRIES.find(c => c.code === code.toUpperCase());
}

export function getDefaultCountry(): CountryInfo {
  return SUPPORTED_COUNTRIES[0]; // Perú
}

export function formatCurrency(value: number, countryCode: string): string {
  const country = getCountryByCode(countryCode);
  if (!country) {
    return `${value}`;
  }

  const formatter = new Intl.NumberFormat(country.language === 'es' ? 'es-PE' : 'en-US', {
    style: 'currency',
    currency: country.currency,
  });
  return formatter.format(value);
}

export function validateDocumentFormat(
  countryCode: string,
  document: string
): { valid: boolean; message?: string } {
  const country = getCountryByCode(countryCode);
  if (!country) {
    return { valid: false, message: 'País no soportado' };
  }

  const doc = document.trim();

  switch (countryCode.toUpperCase()) {
    case 'PE':
      if (!/^\d{11}$/.test(doc)) {
        return { valid: false, message: `${country.documentLabel} debe tener 11 dígitos` };
      }
      return { valid: true };

    case 'CL':
      if (!/^\d{7,8}-[\dKk]$/.test(doc)) {
        return { valid: false, message: `${country.documentLabel} formato: 12345678-K` };
      }
      return { valid: true };

    case 'CO':
      if (!/^\d{9,10}$/.test(doc.replace(/[.\-]/g, ''))) {
        return { valid: false, message: `${country.documentLabel} debe tener 9-10 dígitos` };
      }
      return { valid: true };

    case 'MX':
      if (!/^[A-Z]{3,4}\d{6}[A-Z0-9]{3}$/.test(doc)) {
        return { valid: false, message: `${country.documentLabel} formato: ABCD010101ABC` };
      }
      return { valid: true };

    case 'ES':
      if (!/^[A-Z0-9]{9}$/.test(doc)) {
        return { valid: false, message: `${country.documentLabel} debe tener 9 caracteres` };
      }
      return { valid: true };

    default:
      return { valid: false, message: 'País no soportado' };
  }
}

export function getDocumentPlaceholder(countryCode: string): string {
  const country = getCountryByCode(countryCode);
  return country?.documentExample || 'Documento';
}

export function getDocumentLabel(countryCode: string): string {
  const country = getCountryByCode(countryCode);
  return country?.documentLabel || 'Documento';
}
