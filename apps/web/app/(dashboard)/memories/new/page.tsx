'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function NewMemoryPage() {
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('reflection');
  const [tagsInput, setTagsInput] = useState('');
  const [linkedPersonId, setLinkedPersonId] = useState('');
  const [linkedVentureId, setLinkedVentureId] = useState('');

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      setError('Title and Content are required fields.');
      return;
    }

    setSaving(true);
    setError(null);

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const payload = {
      title,
      content,
      category: category || undefined,
      tags,
      linked_person_id: linkedPersonId || undefined,
      linked_venture_id: linkedVentureId || undefined,
    };

    try {
      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch('/api/v1/memories', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Failed to register reflective memory entry.');
      }

      router.push('/memories');
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-sans p-6">
      {/* Back button */}
      <Link href="/memories" className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-block">
        &lt;= [ BACK TO LOG ]
      </Link>

      <div className="max-w-2xl border border-[#301642] bg-[#0a0510] p-8 mt-2">
        <h1 className="text-3xl font-mono tracking-tight font-extrabold uppercase mb-8 border-b border-[#301642] pb-4">
          {"//"} Capture Reflection
        </h1>

        {error && (
          <div className="border border-red-500 bg-red-950/20 p-4 mb-6 font-mono text-xs text-red-300">
            SYSTEM CRITICAL ERROR: {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 font-mono text-sm">
          <div className="flex flex-col gap-1">
            <label className="text-[#00ff9d] uppercase text-xs">Reflection Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[#00ff9d] uppercase text-xs">Category Type</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
            >
              <option value="reflection">REFLECTION</option>
              <option value="lesson">FOUNDER LESSON</option>
              <option value="win">MILESTONE WIN</option>
              <option value="failure">ANALYZED FAILURE</option>
              <option value="observation">OBSERVATION</option>
              <option value="decision_context">DECISION CONTEXT</option>
              <option value="quote">QUOTE</option>
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[#00ff9d] uppercase text-xs">Linked Contact (ID)</label>
            <input
              type="text"
              value={linkedPersonId}
              onChange={(e) => setLinkedPersonId(e.target.value)}
              placeholder="e.g. person-uuid-value"
              className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[#00ff9d] uppercase text-xs">Tags (comma separated)</label>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="e.g. Strategy, Pivot"
              className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d]"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[#00ff9d] uppercase text-xs">Reflective Summary / Content *</label>
            <textarea
              rows={6}
              required
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Describe what occurred, what was learned, and how it informs future execution..."
              className="bg-[#12081d] border border-[#301642] text-[#f7f4ea] px-3 py-2 focus:outline-none focus:border-[#00ff9d] resize-none"
            />
          </div>

          <div className="flex justify-end gap-4 border-t border-[#301642] pt-6">
            <Link
              href="/memories"
              className="px-6 py-2.5 border border-[#301642] hover:border-[#00ff9d] text-slate-300 font-bold uppercase text-xs leading-loose"
            >
              [ CANCEL ]
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 bg-[#00ff9d] text-[#12081d] hover:bg-[#00e08a] font-bold uppercase text-xs leading-loose disabled:opacity-50"
            >
              {saving ? '[ DEPLOYING... ]' : '[ REGISTER REFLECTION ]'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
