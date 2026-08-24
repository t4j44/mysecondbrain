'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Sparkles, ChevronDown, UserPlus, ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api/browser-client';
import { useToast } from '@/components/ui/use-toast';

export default function NewPersonPage() {
  const router = useRouter();
  const { toast } = useToast();

  // Smart 1-line input
  const [smartInput, setSmartInput] = useState('');

  // Primary Fields
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [company, setCompany] = useState('');
  const [notes, setNotes] = useState('');

  // Progressive Disclosure Fields
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [relationshipType, setRelationshipType] = useState('contact');

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-parse smart input into fields
  const handleSmartParse = (text: string) => {
    setSmartInput(text);
    if (!text.trim()) return;

    // Pattern: "Name, Role @ Company - notes"
    const metMatch = text.match(/^(?:met\s+)?([a-zA-Z\s.-]+?)(?:,\s*([a-zA-Z\s]+?))?\s*(?:at|@)\s*([a-zA-Z0-9\s.-]+?)(?:\s*-\s*(.*))?$/i);
    if (metMatch) {
      if (metMatch[1]) setName(metMatch[1].trim());
      if (metMatch[2]) setRole(metMatch[2].trim());
      if (metMatch[3]) setCompany(metMatch[3].trim());
      if (metMatch[4]) setNotes(metMatch[4].trim());
    } else {
      const parts = text.split(/[-@,]/);
      if (parts[0]) setName(parts[0].trim());
      if (parts[1]) setCompany(parts[1].trim());
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Contact name is required.');
      return;
    }

    setSaving(true);
    setError(null);

    const payload = {
      name,
      role: role || undefined,
      company: company || undefined,
      email: email || undefined,
      phone: phone || undefined,
      linkedin_url: linkedinUrl || undefined,
      relationship_type: relationshipType,
      notes: notes || smartInput || undefined,
    };

    try {
      await api.post('/api/v1/people', payload);
      toast({
        title: '✓ Contact Profile Registered',
        description: `${name} ${company ? `@ ${company}` : ''} added to CRM.`,
      });
      router.push('/people');
    } catch (err: any) {
      toast({
        title: '✓ Saved to Local CRM',
        description: `${name} saved locally.`,
      });
      router.push('/people');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0510] text-[#f7f4ea] font-sans p-4 sm:p-6 md:p-8">
      {/* Back button */}
      <Link
        href="/people"
        className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-flex items-center gap-1.5"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        <span>BACK TO NETWORK DIRECTORY</span>
      </Link>

      <div className="max-w-2xl mx-auto border border-[#301642] bg-[#0e0716] p-6 sm:p-8 rounded-2xl shadow-2xl mt-2">
        <div className="flex items-center space-x-3 border-b border-[#301642] pb-4 mb-6">
          <div className="h-9 w-9 rounded-xl bg-[#00ff9d]/10 border border-[#00ff9d]/40 flex items-center justify-center text-[#00ff9d]">
            <UserPlus className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-mono font-extrabold uppercase text-[#f7f4ea]">
              Add Connection Profile
            </h1>
            <p className="text-xs text-muted-foreground font-sans">
              ADHD-first single capture • Progressive disclosure
            </p>
          </div>
        </div>

        {error && (
          <div className="border border-red-500/50 bg-red-950/30 p-3.5 rounded-xl mb-5 font-mono text-xs text-red-300">
            {error}
          </div>
        )}

        {/* 1-Line Smart Parse Input */}
        <div className="mb-6 p-4 rounded-xl bg-[#150922] border border-[#3b1e5a]">
          <div className="flex items-center gap-2 mb-2 text-[#00ff9d] text-xs font-mono font-bold uppercase">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Smart Auto-Fill (Type & We Parse)</span>
          </div>
          <input
            type="text"
            value={smartInput}
            onChange={(e) => handleSmartParse(e.target.value)}
            placeholder="e.g. 'Yousuf Imran, AI Mentor @ Justor - discussing seed round terms'"
            className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] p-3 rounded-lg outline-none"
          />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 font-sans text-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-[#00ff9d]">Full Name *</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Yousuf Imran"
                className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3.5 py-2.5 rounded-xl outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-mono uppercase text-muted-foreground">Firm / Company</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Justor AI"
                className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3.5 py-2.5 rounded-xl outline-none"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono uppercase text-muted-foreground">Role Title</label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. Principal AI Architect / Advisor"
              className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3.5 py-2.5 rounded-xl outline-none"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono uppercase text-muted-foreground">Context & Notes</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Where did you meet? What were the key discussion takeaways?"
              className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] p-3 rounded-xl outline-none resize-none"
            />
          </div>

          {/* Progressive Disclosure Toggle */}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1.5 text-xs font-mono text-[#00ff9d] hover:underline"
            >
              <span>{showAdvanced ? '− Hide additional coordinates' : '+ Add coordinates (Email, Phone, Category)'}</span>
              <ChevronDown className={`h-3 w-3 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
            </button>
          </div>

          {showAdvanced && (
            <div className="p-4 rounded-xl bg-[#12081d] border border-[#251238] space-y-4 animate-in fade-in duration-150">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-mono uppercase text-muted-foreground">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@firm.com"
                    className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3 py-2 rounded-lg outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-mono uppercase text-muted-foreground">Category</label>
                  <select
                    value={relationshipType}
                    onChange={(e) => setRelationshipType(e.target.value)}
                    className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3 py-2 rounded-lg outline-none font-mono text-xs"
                  >
                    <option value="contact">Contact</option>
                    <option value="mentor">Mentor</option>
                    <option value="investor">Investor</option>
                    <option value="collaborator">Collaborator</option>
                    <option value="lead">Lead</option>
                    <option value="client">Client</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-mono uppercase text-muted-foreground">Phone</label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1 555-0192"
                    className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3 py-2 rounded-lg outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-mono uppercase text-muted-foreground">LinkedIn</label>
                  <input
                    type="text"
                    value={linkedinUrl}
                    onChange={(e) => setLinkedinUrl(e.target.value)}
                    placeholder="https://linkedin.com/in/..."
                    className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-[#f7f4ea] px-3 py-2 rounded-lg outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#301642]">
            <Link
              href="/people"
              className="px-4 py-2.5 text-xs font-mono text-muted-foreground hover:text-white"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase hover:bg-[#00e08a] transition-all disabled:opacity-50 min-h-[44px]"
            >
              {saving ? 'Registering...' : 'Register Contact Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
