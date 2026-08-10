'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function NewPersonPage() {
  const router = useRouter();

  // Form Fields
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [company, setCompany] = useState('');
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [relationshipType, setRelationshipType] = useState('contact');
  const [notes, setNotes] = useState('');
  const [tagsInput, setTagsInput] = useState('');

  // Duplicate Check states
  const [duplicates, setDuplicates] = useState<any[]>([]);
  const [checking, setChecking] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Trigger duplicate check on Name / Email changes
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (name.length < 3 && email.length < 4) {
      setDuplicates([]);
      return;
    }

    setChecking(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const token = localStorage.getItem('supabase_session_token');
        const queryParams = new URLSearchParams();
        if (name) queryParams.append('q', name);

        const response = await fetch(`/api/v1/people?${queryParams.toString()}&limit=5`, {
          headers: { Authorization: `Bearer ${token || ''}` },
        });

        if (response.ok) {
          const result = await response.json();
          // Filter exact or close matches
          const matchCandidates = result.data.filter(
            (p: any) =>
              p.name.toLowerCase().includes(name.toLowerCase()) ||
              (email && p.email?.toLowerCase() === email.toLowerCase())
          );
          setDuplicates(matchCandidates);
        }
      } catch (err) {
        console.error('Duplicate detection failed', err);
      } finally {
        setChecking(false);
      }
    }, 500); // 500ms debounce

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [name, email]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Name is a required validation parameter.');
      return;
    }

    setSaving(true);
    setError(null);

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const payload = {
      name,
      role: role || undefined,
      company: company || undefined,
      industry: industry || undefined,
      location: location || undefined,
      email: email || undefined,
      phone: phone || undefined,
      linkedin_url: linkedinUrl || undefined,
      relationship_type: relationshipType,
      notes: notes || undefined,
      tags,
    };

    try {
      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch('/api/v1/people', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errResult = await response.json();
        throw new Error(errResult.error?.message || 'Failed to save contact profile.');
      }

      router.push('/people');
    } catch (err: any) {
      setError(err.message || 'An error occurred during submission.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-sans p-6">
      {/* Breadcrumb back */}
      <Link href="/people" className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-block">
        &lt;= [ BACK TO DIRECTORY ]
      </Link>

      <div className="max-w-3xl border border-[#301642] bg-[#0a0510] p-8 mt-2">
        <h1 className="text-3xl font-mono tracking-tight font-extrabold uppercase mb-8 border-b border-[#301642] pb-4">
          {"//"} Register Connection Profile
        </h1>

        {error && (
          <div className="border border-red-500 bg-red-950/20 p-4 mb-6 font-mono text-xs text-red-300">
            SYSTEM CRITICAL ERROR: {error}
          </div>
        )}

        {/* Duplicate Warning Alert Banner */}
        {duplicates.length > 0 && (
          <div className="border border-yellow-600 bg-yellow-950/20 p-4 mb-6 font-mono text-xs text-yellow-300 space-y-2">
            <p className="font-bold">{"//"} WARNING: POTENTIAL DUPLICATE RECORDS INSTANTIATED</p>
            <div className="space-y-1 mt-2">
              {duplicates.map((dup) => (
                <div key={dup.id} className="flex justify-between items-center bg-[#12081d] p-2 border border-yellow-800">
                  <span>
                    {dup.name} ({dup.company || 'No Company'}) — {dup.relationship_type}
                  </span>
                  <Link href={`/people/${dup.id}`} target="_blank" className="text-[#00ff9d] hover:underline">
                    [ VIEW PROFILE ]
                  </Link>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-slate-500 mt-2">Please verify before completing submission to avoid overlapping records.</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 font-mono text-sm">
          {/* Identity Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Full Name *</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Relationship Category</label>
              <select
                value={relationshipType}
                onChange={(e) => setRelationshipType(e.target.value)}
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              >
                <option value="contact">CONTACT (Default)</option>
                <option value="mentor">MENTOR</option>
                <option value="investor">INVESTOR</option>
                <option value="peer">PEER</option>
                <option value="collaborator">COLLABORATOR</option>
                <option value="lead">LEAD</option>
                <option value="client">CLIENT</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Role Title</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Founder, Principal Designer"
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Firm / Company name</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Industry</label>
              <input
                type="text"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g. AI Workflow, FinTech"
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Dhaka, London"
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>
          </div>

          {/* Contact coordinates */}
          <div className="border-t border-[#301642] pt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Phone Coordinate</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">LinkedIn URL</label>
              <input
                type="text"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>
          </div>

          {/* Descriptive text & tags */}
          <div className="border-t border-[#301642] pt-6 space-y-4">
            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Tags (comma separated)</label>
              <input
                type="text"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="e.g. Mentor, Investor, LegalTech"
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[#00ff9d] uppercase text-xs">Personal Context & Insights</label>
              <textarea
                rows={4}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Where did you meet? What are their core values? What did you discuss?"
                className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d] resize-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-4 border-t border-[#301642] pt-6">
            <Link
              href="/people"
              className="px-6 py-2.5 border border-[#301642] hover:border-[#00ff9d] text-slate-300 font-bold uppercase text-xs leading-loose"
            >
              [ CANCEL ]
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 bg-[#00ff9d] text-[#12081d] hover:bg-[#00e08a] font-bold uppercase text-xs leading-loose disabled:opacity-50"
            >
              {saving ? '[ DEPLOYING... ]' : '[ REGISTER CONNECTION ]'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
