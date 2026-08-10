'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';

export default function PersonDetailPage() {
  const params = useParams();
  const router = useRouter();
  const personId = params?.personId as string;

  const [person, setPerson] = useState<any>(null);
  const [interactions, setInteractions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // States for expanding contact info details
  const [showContactDetails, setShowContactDetails] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('supabase_session_token');
        const headers = { Authorization: `Bearer ${token || ''}` };

        // Fetch Person Details
        const personRes = await fetch(`/api/v1/people/${personId}`, { headers });
        if (!personRes.ok) {
          throw new Error('Failed to retrieve contact card details.');
        }
        const personData = await personRes.json();
        setPerson(personData.data);

        // Fetch chronological interactions
        const interactionRes = await fetch(`/api/v1/interactions?person_id=${personId}`, { headers });
        if (interactionRes.ok) {
          const interactionData = await interactionRes.json();
          setInteractions(interactionData.data);
        }
      } catch (err: any) {
        setError(err.message || 'Error fetching data');
      } finally {
        setLoading(false);
      }
    }

    if (personId) {
      fetchData();
    }
  }, [personId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-mono p-8 flex items-center justify-center">
        <p className="animate-pulse">{"//"} ACCESSING RELATIONSHIP MEMORY MATRIX...</p>
      </div>
    );
  }

  if (error || !person) {
    return (
      <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-mono p-8">
        <div className="border border-red-500 bg-red-950/20 p-6 max-w-lg mx-auto mt-12 text-center">
          <p className="text-red-400 mb-4">{"//"} RECORD UNREACHABLE OR NOT FOUND</p>
          <p className="text-xs text-slate-500 mb-6">{error}</p>
          <button onClick={() => router.push('/people')} className="px-4 py-2 bg-[#301642] border border-[#482264] hover:border-[#00ff9d]">
            [ RETURN TO DIRECTORY ]
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-sans p-6">
      {/* Back link */}
      <Link href="/people" className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-block">
        &lt;= [ BACK TO DIRECTORY ]
      </Link>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-4">
        {/* Left Column: Identity & Metadata */}
        <section className="lg:col-span-1 space-y-6">
          <div className="border border-[#301642] bg-[#0a0510] p-6 relative">
            <div className="w-16 h-16 bg-[#301642] text-[#00ff9d] border border-[#482264] font-mono text-2xl flex items-center justify-center font-extrabold uppercase mb-4">
              {person.name.split(' ').map((n: string) => n[0]).join('')}
            </div>

            <h1 className="text-3xl font-mono tracking-tight font-extrabold mb-1">{person.name}</h1>
            <p className="text-sm font-mono text-slate-300 mb-4">
              {person.role || 'Unspecified Role'} @ <span className="text-[#00ff9d]">{person.company || 'Independent'}</span>
            </p>

            {/* Core details list */}
            <div className="space-y-2 border-t border-[#301642] pt-4 font-mono text-xs text-slate-400">
              <p>
                <span className="text-slate-500 uppercase">CATEGORY:</span>{' '}
                <span className="text-[#f7f4ea]">{person.relationship_type}</span>
              </p>
              <p>
                <span className="text-slate-500 uppercase">LOCATION:</span>{' '}
                <span className="text-[#f7f4ea]">{person.location || 'N/A'}</span>
              </p>
              <p>
                <span className="text-slate-500 uppercase">METRIC:</span>{' '}
                <span className="text-[#f7f4ea]">
                  Last exchange:{' '}
                  {person.last_interaction_at
                    ? new Date(person.last_interaction_at).toLocaleDateString()
                    : 'Never logged'}
                </span>
              </p>
            </div>

            {/* Sensitive details (masked by default) */}
            <div className="border-t border-[#301642] pt-4 mt-4 font-mono text-xs">
              {!showContactDetails ? (
                <button
                  onClick={() => setShowContactDetails(true)}
                  className="w-full text-center py-2 bg-[#12081d] border border-[#301642] text-[#00ff9d] hover:border-[#00ff9d]"
                >
                  [ DECRYPT CONTACT INFO ]
                </button>
              ) : (
                <div className="space-y-2 p-3 bg-[#12081d] border border-[#301642] text-slate-300">
                  <p>Email: {person.email || 'None'}</p>
                  <p>Phone: {person.phone || 'None'}</p>
                  <p>
                    LinkedIn:{' '}
                    {person.linkedin_url ? (
                      <a href={person.linkedin_url} target="_blank" rel="noreferrer" className="text-[#00ff9d] hover:underline">
                        Visit Profile
                      </a>
                    ) : (
                      'None'
                    )}
                  </p>
                  <button
                    onClick={() => setShowContactDetails(false)}
                    className="w-full mt-2 text-center py-1 text-[10px] text-slate-500 border border-[#301642] hover:border-red-500"
                  >
                    [ MASK ]
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Quick Action Toolbar */}
          <div className="border border-[#301642] bg-[#0a0510] p-4 font-mono text-xs space-y-2">
            <h3 className="text-slate-500 uppercase mb-2">{"//"} QUICK OPERATIONS</h3>
            <Link
              href={`/interactions/new?person_id=${person.id}`}
              className="w-full block text-center py-2 border border-[#301642] hover:border-[#00ff9d] text-slate-300 hover:text-[#00ff9d]"
            >
              [ LOG INTERACTION ]
            </Link>
            <Link
              href={`/people/${person.id}/edit`}
              className="w-full block text-center py-2 border border-[#301642] hover:border-[#00ff9d] text-slate-300"
            >
              [ EDIT CONTACT PROFILE ]
            </Link>
          </div>
        </section>

        {/* Right Columns: Insights & Timeline */}
        <section className="lg:col-span-2 space-y-6">
          {/* Notes & Insights summary */}
          <div className="border border-[#301642] bg-[#0a0510] p-6">
            <h2 className="text-lg font-mono text-[#00ff9d] uppercase border-b border-[#301642] pb-2 mb-4">
              {"//"} Relationship Summary & Core Insights
            </h2>
            <div className="space-y-4 text-sm leading-relaxed text-slate-300">
              {person.notes ? (
                <p className="whitespace-pre-wrap">{person.notes}</p>
              ) : (
                <p className="italic text-slate-500 font-mono text-xs">{"//"} No core insights recorded yet. Add notes to describe context.</p>
              )}
            </div>
          </div>

          {/* Interaction Timeline */}
          <div className="border border-[#301642] bg-[#0a0510] p-6">
            <h2 className="text-lg font-mono text-[#00ff9d] uppercase border-b border-[#301642] pb-2 mb-6">
              {"//"} Chronological Interaction Timeline
            </h2>

            {interactions.length === 0 ? (
              <div className="p-8 border border-dashed border-[#301642] text-center font-mono text-xs text-slate-500">
                {"//"} NO CHRONOLOGICAL HISTORY LOGGED YET
              </div>
            ) : (
              <div className="space-y-6 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-[1px] before:bg-[#301642]">
                {interactions.map((interaction) => (
                  <div key={interaction.id} className="relative pl-8 group">
                    {/* Timeline Node dot */}
                    <div className="absolute left-1.5 top-1.5 w-3 h-3 bg-[#12081d] border-2 border-[#301642] group-hover:border-[#00ff9d] transition-colors rounded-full"></div>

                    <div className="border border-[#301642] group-hover:border-[#00ff9d] transition-all p-4 bg-[#12081d]">
                      <div className="flex justify-between items-start mb-2 flex-wrap gap-2">
                        <span className="font-mono text-xs text-[#00ff9d]">{interaction.interaction_type.toUpperCase()}</span>
                        <span className="font-mono text-xs text-slate-500">
                          {new Date(interaction.date).toLocaleDateString()}
                        </span>
                      </div>
                      <h4 className="font-bold text-sm text-[#f7f4ea] mb-1">{interaction.title}</h4>
                      {interaction.summary && <p className="text-xs text-slate-400 mt-2">{interaction.summary}</p>}

                      {/* Key Takeaways */}
                      {interaction.key_takeaways && interaction.key_takeaways.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-[#301642]/50">
                          <h5 className="text-[10px] font-mono text-slate-500 uppercase mb-1">Key Takeaways:</h5>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
                            {interaction.key_takeaways.map((k: string, idx: number) => (
                              <li key={idx}>{k}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
