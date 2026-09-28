'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';

export function PrivatePhoto({id, kind}: {id: string; kind: string}) {
  const [url, setUrl] = useState('');
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let alive = true; let objectUrl = '';
    void api.get<Blob>(`/capture/media/${id}?thumbnail=true`).then(blob => {
      if (alive) { objectUrl = URL.createObjectURL(blob); setUrl(objectUrl); }
    }).catch(() => { if (alive) setFailed(true); });
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [id]);
  if (!url) return <p className="text-sm">{failed ? 'Private photo unavailable.' : 'Loading private photo…'}</p>;
  // Authenticated Blob URL; a public image optimizer must never fetch private media.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt={kind === 'business_card' ? 'Saved business card' : 'Saved moment'} className="max-h-52 max-w-full rounded-lg object-contain" />;
}
