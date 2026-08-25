'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api/browser-client';
import { ErrorState } from '@/components/shared/error-state';
import { useToast } from '@/components/ui/use-toast';
import { formatApiError } from '@/lib/api/format-error';
import type { Person } from '@/lib/api/domains';

export default function EditPersonPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const personId = params?.personId as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [company, setCompany] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [relationshipType, setRelationshipType] = useState('contact');
  const [notes, setNotes] = useState('');
  const [location, setLocation] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const person = await api.get<Person>(`/people/${personId}`);
        setName(person.name);
        setRole(person.role ?? '');
        setCompany(person.company ?? '');
        setEmail(person.email ?? '');
        setPhone(person.phone ?? '');
        setLinkedinUrl(person.linkedin_url ?? '');
        setRelationshipType(person.relationship_type);
        setNotes(person.notes ?? '');
        setLocation(person.location ?? '');
      } catch (err) {
        setError(formatApiError(err));
      } finally {
        setLoading(false);
      }
    }
    if (personId) load();
  }, [personId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Name is required.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await api.patch(`/people/${personId}`, {
        name: name.trim(),
        role: role || undefined,
        company: company || undefined,
        email: email || undefined,
        phone: phone || undefined,
        linkedin_url: linkedinUrl || undefined,
        relationship_type: relationshipType,
        notes: notes || undefined,
        location: location || undefined,
      });
      toast({ title: 'Contact updated', description: name.trim() });
      router.push(`/people/${personId}`);
    } catch (err) {
      const msg = formatApiError(err);
      setError(msg);
      toast({ variant: 'destructive', title: 'Update failed', description: msg });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0510] text-[#f7f4ea] p-8 flex items-center justify-center font-mono text-sm">
        Loading...
      </div>
    );
  }

  if (error && !name) {
    return (
      <div className="min-h-screen bg-[#0a0510] p-8">
        <Link href="/people" className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-flex items-center gap-1">
          <ArrowLeft className="h-3.5 w-3.5" /> Back
        </Link>
        <ErrorState title="Could not load contact" message={error} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0510] text-[#f7f4ea] p-4 sm:p-6 md:p-8">
      <Link
        href={`/people/${personId}`}
        className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-flex items-center gap-1"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to profile
      </Link>

      <div
        data-testid="person-edit"
        className="max-w-2xl mx-auto border border-[#301642] bg-[#0e0716] p-6 sm:p-8 rounded-2xl"
      >
        <h1 className="text-xl font-mono font-extrabold uppercase mb-6">Edit Contact</h1>

        {error && (
          <div className="border border-red-500/50 bg-red-950/30 p-3 rounded-xl mb-4 text-xs text-red-300 font-mono">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-[#00ff9d]">Name *</label>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none min-h-[44px]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-muted-foreground">Company</label>
              <input
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none min-h-[44px]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-muted-foreground">Role</label>
              <input
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none min-h-[44px]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-muted-foreground">Category</label>
              <select
                value={relationshipType}
                onChange={(e) => setRelationshipType(e.target.value)}
                className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none font-mono text-xs min-h-[44px]"
              >
                <option value="contact">Contact</option>
                <option value="mentor">Mentor</option>
                <option value="investor">Investor</option>
                <option value="peer">Peer</option>
                <option value="collaborator">Collaborator</option>
                <option value="lead">Lead</option>
                <option value="client">Client</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-muted-foreground">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none min-h-[44px]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-muted-foreground">Phone</label>
              <input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none min-h-[44px]"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono uppercase text-muted-foreground">LinkedIn URL</label>
            <input
              type="url"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none min-h-[44px]"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono uppercase text-muted-foreground">Location</label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2.5 rounded-xl outline-none min-h-[44px]"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono uppercase text-muted-foreground">Notes</label>
            <textarea
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-[#12081d] border border-[#301642] text-[#f7f4ea] p-3 rounded-xl outline-none resize-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-[#301642]">
            <Link
              href={`/people/${personId}`}
              className="px-4 py-2.5 text-xs font-mono text-muted-foreground hover:text-white min-h-[44px] flex items-center"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase disabled:opacity-50 min-h-[44px]"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
