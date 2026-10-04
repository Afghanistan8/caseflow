export const SOURCE_URL = 'https://www.justice.gov/crt/laws-we-enforce';

export const fixtures = [
  {
    label: 'Title VII',
    law_identifier: 'Title VII of the Civil Rights Act of 1964',
    note: 'An exact heading on the pinned DOJ page.'
  },
  {
    label: 'Negative control',
    law_identifier: 'Fair Housing Act',
    note: 'A law name absent from this specific DOJ page; this does not say anything about that law elsewhere.'
  },
  {
    label: 'Pregnant Workers Fairness Act',
    law_identifier: 'Pregnant Workers Fairness Act',
    note: 'Another exact heading on the pinned DOJ page.'
  }
];

export function parseStored(value) {
  if (typeof value !== 'string' || !value) return null;
  try { return JSON.parse(value); } catch { return null; }
}

export function shortDigest(value) {
  return value ? `${value.slice(0, 12)}…${value.slice(-8)}` : '—';
}
