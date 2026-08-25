'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { api } from '@/lib/api/browser-client';
import { ErrorState } from '@/components/shared/error-state';
import { ConfirmActionDialog } from '@/components/shared/confirm-action-dialog';
import { useToast } from '@/components/ui/use-toast';
import { formatApiError } from '@/lib/api/format-error';
import type { Person } from '@/lib/api/domains';

export default function PersonDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const personId = params?.personId as string;

  const [person, setPerson] = useState<Person | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showContactDetails, setShowContactDetails] = useState(false);
  const [confirmArchive, setConfirmArchive] = useState(false);

  const fetchPerson = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<Person>(`/people/${personId}`);
      setPerson(data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [personId]);

  useEffect(() => {
    if (personId) {
      fetchPerson();
    }
  }, [personId, fetchPerson]);

  const handleArchive = async () => {
    try {
      await api.delete(`/people/${personId}`);
      toast({ title: 'Contact archived', description: person?.name });
      router.push('/people');
    } catch (err) {
      toast({ variant: 'destructive', title: 'Archive failed', description: formatApiError(err) });
      throw err;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-mono p-8 flex items-center justify-center">
        <p className="animate-pulse">Loading contact...</p>
      </div>
    );
  }

  if (error || !person) {
    return (
      <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] p-8">
        <Link href="/people" className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-flex items-center gap-1">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to directory
        </Link>
        <ErrorState title="Contact not found" message={error ?? 'Record unavailable'} onRetry={fetchPerson} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-sans p-4 sm:p-6">
      <Link href="/people" className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-flex items-center gap-1">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to directory
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4 max-w-5xl mx-auto">
        <section className="lg:col-span-1 space-y-4">
          <div className="border border-[#301642] bg-[#0a0510] p-6 rounded-xl">
            <div className="w-16 h-16 bg-[#301642] text-[#00ff9d] border border-[#482264] font-mono text-2xl flex items-center justify-center font-extrabold uppercase mb-4 rounded-lg">
              {person.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
            </div>

            <h1 className="text-2xl font-mono font-extrabold mb-1">{person.name}</h1>
            <p className="text-sm text-slate-300 mb-4">
              {person.role || 'Contact'}
              {person.company ? (
                <>
                  {' '}
                  @ <span className="text-[#00ff9d]">{person.company}</span>
                </>
              ) : null}
            </p>

            <div className="space-y-2 border-t border-[#301642] pt-4 font-mono text-xs text-slate-400">
              <p>
                <span className="text-slate-500 uppercase">Category:</span>{' '}
                <span className="text-[#f7f4ea]">{person.relationship_type}</span>
              </p>
              {person.location && (
                <p>
                  <span className="text-slate-500 uppercase">Location:</span>{' '}
                  <span className="text-[#f7f4ea]">{person.location}</span>
                </p>
              )}
              {person.last_interaction_at && (
                <p>
                  <span className="text-slate-500 uppercase">Last contact:</span>{' '}
                  {new Date(person.last_interaction_at).toLocaleDateString()}
                </p>
              )}
            </div>

            <div className="border-t border-[#301642] pt-4 mt-4">
              {!showContactDetails ? (
                <button
                  type="button"
                  onClick={() => setShowContactDetails(true)}
                  className="w-full text-center py-2.5 bg-[#12081d] border border-[#301642] text-[#00ff9d] hover:border-[#00ff9d] rounded-lg text-xs font-mono min-h-[44px]"
                >
                  Show contact info
                </button>
              ) : (
                <div className="space-y-2 p-3 bg-[#12081d] border border-[#301642] text-slate-300 text-sm rounded-lg">
                  <p>Email: {person.email || '—'}</p>
                  <p>Phone: {person.phone || '—'}</p>
                  <p>
                    LinkedIn:{' '}
                    {person.linkedin_url ? (
                      <a href={person.linkedin_url} target="_blank" rel="noreferrer" className="text-[#00ff9d] hover:underline">
                        Profile
                      </a>
                    ) : (
                      '—'
                    )}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="border border-[#301642] bg-[#0a0510] p-4 rounded-xl space-y-2">
            <Link
              href={`/people/${person.id}/edit`}
              data-testid="person-edit"
              className="w-full block text-center py-2.5 border border-[#301642] hover:border-[#00ff9d] text-slate-300 hover:text-[#00ff9d] rounded-lg text-xs font-mono min-h-[44px]"
            >
              Edit contact
            </Link>
            <button
              type="button"
              onClick={() => setConfirmArchive(true)}
              className="w-full flex items-center justify-center gap-1 py-2.5 border border-red-900/50 hover:border-red-500 text-red-400 rounded-lg text-xs font-mono min-h-[44px]"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Archive contact
            </button>
          </div>
        </section>

        <section className="lg:col-span-2">
          <div className="border border-[#301642] bg-[#0a0510] p-6 rounded-xl">
            <h2 className="text-lg font-mono text-[#00ff9d] uppercase border-b border-[#301642] pb-2 mb-4">
              Notes
            </h2>
            {person.notes ? (
              <p className="text-sm leading-relaxed text-slate-300 whitespace-pre-wrap">{person.notes}</p>
            ) : (
              <p className="text-sm text-slate-500 italic">No notes recorded yet.</p>
            )}
          </div>
        </section>
      </div>

      <ConfirmActionDialog
        open={confirmArchive}
        onOpenChange={setConfirmArchive}
        title={`Archive ${person.name}?`}
        description="This contact will be removed from your active directory."
        confirmLabel="Archive Contact"
        onConfirm={handleArchive}
      />
    </div>
  );
}
