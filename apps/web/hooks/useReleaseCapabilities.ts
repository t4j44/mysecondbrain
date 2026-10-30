'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';

export function useReleaseCapabilities() {
  const [capabilities, setCapabilities] = useState({ google_integrations: false, portfolio_publishing: false, loaded: false });
  useEffect(() => {
    let active = true;
    api.get<{ google_integrations: boolean; portfolio_publishing: boolean }>('/release-capabilities')
      .then(value => { if (active) setCapabilities({ google_integrations: value.google_integrations === true, portfolio_publishing: value.portfolio_publishing === true, loaded: true }); })
      .catch(() => { if (active) setCapabilities({ google_integrations: false, portfolio_publishing: false, loaded: true }); });
    return () => { active = false; };
  }, []);
  return capabilities;
}
