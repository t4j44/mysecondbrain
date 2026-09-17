'use client';

import { useState, useCallback, useMemo } from 'react';
import { api } from '@/lib/api/browser-client';
import { useToast } from '@/components/ui/use-toast';

export type CaptureType = 'auto' | 'task' | 'memory' | 'person' | 'idea';

export interface ParsedCapture {
  detectedType: 'task' | 'memory' | 'person' | 'idea';
  title: string;
  content?: string;
  priority?: 'urgent' | 'high' | 'medium' | 'low';
  dueDate?: string;
  tags: string[];
  personName?: string;
  company?: string;
  role?: string;
  email?: string;
}

export function parseNaturalLanguage(rawText: string, forcedType: CaptureType = 'auto'): ParsedCapture {
  const text = rawText.trim();
  const lower = text.toLowerCase();

  // Extract tags (e.g. #strategy #urgent)
  const tagMatches = text.match(/#([a-zA-Z0-9_-]+)/g) || [];
  const tags = tagMatches.map(t => t.slice(1));

  // Extract priority
  let priority: 'urgent' | 'high' | 'medium' | 'low' | undefined;
  if (lower.includes('#urgent') || lower.includes('#p0') || lower.includes('!urgent')) {
    priority = 'urgent';
  } else if (lower.includes('#high') || lower.includes('#p1') || lower.includes('!high')) {
    priority = 'high';
  } else if (lower.includes('#low') || lower.includes('#p3')) {
    priority = 'low';
  } else if (lower.includes('#medium') || lower.includes('#p2')) {
    priority = 'medium';
  }

  // Extract email if present
  const emailMatch = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  const email = emailMatch ? emailMatch[0] : undefined;

  // Extract due dates
  let dueDate: string | undefined;
  const now = new Date();
  if (lower.includes('today') || lower.includes('by today')) {
    dueDate = now.toISOString();
  } else if (lower.includes('tomorrow') || lower.includes('by tomorrow')) {
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    dueDate = tomorrow.toISOString();
  } else if (lower.includes('next week')) {
    const nextWeek = new Date(now);
    nextWeek.setDate(nextWeek.getDate() + 7);
    dueDate = nextWeek.toISOString();
  } else if (lower.includes('friday') || lower.includes('by friday')) {
    const d = new Date(now);
    const day = d.getDay();
    const diff = (5 - day + 7) % 7 || 7;
    d.setDate(d.getDate() + diff);
    dueDate = d.toISOString();
  }

  // Clean tags from title
  let cleanedTitle = text
    .replace(/#[a-zA-Z0-9_-]+/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  // Determine Type
  let detectedType: 'task' | 'memory' | 'person' | 'idea' = 'memory';

  if (forcedType !== 'auto') {
    detectedType = forcedType;
  } else {
    // Smart heuristic detection
    const isPerson =
      lower.startsWith('met ') ||
      lower.startsWith('intro to ') ||
      lower.startsWith('contact: ') ||
      lower.startsWith('person: ') ||
      (email !== undefined && !lower.startsWith('email:')) ||
      /\b(cto|ceo|founder|investor|advisor|mentor|director|vp)\s+at\b/i.test(text) ||
      /\b(cto|ceo|founder|investor|advisor|mentor)\s*@/i.test(text);

    const isTask =
      lower.startsWith('todo:') ||
      lower.startsWith('task:') ||
      lower.startsWith('buy ') ||
      lower.startsWith('call ') ||
      lower.startsWith('email ') ||
      lower.startsWith('send ') ||
      lower.startsWith('ship ') ||
      lower.startsWith('finish ') ||
      lower.startsWith('review ') ||
      lower.startsWith('draft ') ||
      lower.startsWith('prep ') ||
      lower.startsWith('follow up ') ||
      lower.includes('due ') ||
      lower.includes('by tomorrow') ||
      lower.includes('by friday') ||
      priority !== undefined;

    const isIdea =
      lower.startsWith('idea:') ||
      lower.startsWith('hypothesis:') ||
      lower.startsWith('what if ') ||
      lower.startsWith('build a ') ||
      lower.startsWith('feature:');

    if (isPerson) detectedType = 'person';
    else if (isIdea) detectedType = 'idea';
    else if (isTask) detectedType = 'task';
    else detectedType = 'memory';
  }

  // Specific parsing for Person
  let personName: string | undefined;
  let company: string | undefined;
  let role: string | undefined;

  if (detectedType === 'person') {
    const metMatch = cleanedTitle.match(/^(?:met|intro to|person:|contact:)?\s*([a-zA-Z\s.-]+?)(?:,\s*([a-zA-Z\s]+?))?\s*(?:at|@)\s*([a-zA-Z0-9\s.-]+?)(?:\s*-\s*(.*))?$/i);
    if (metMatch) {
      personName = metMatch[1]?.trim();
      role = metMatch[2]?.trim();
      company = metMatch[3]?.trim();
    } else {
      const parts = cleanedTitle.split(/[-–—,@]/);
      personName = parts[0]?.replace(/^(?:met|intro to|person:|contact:)\s*/i, '').trim();
      if (parts[1]) company = parts[1].trim();
    }
  }

  return {
    detectedType,
    title: cleanedTitle || text,
    content: text,
    priority: priority || (detectedType === 'task' ? 'medium' : undefined),
    dueDate,
    tags,
    personName,
    company,
    role,
    email,
  };
}

export function useQuickCapture() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [selectedType, setSelectedType] = useState<CaptureType>('auto');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const parsed = useMemo(() => {
    if (!input.trim()) return null;
    return parseNaturalLanguage(input, selectedType);
  }, [input, selectedType]);

  const openCapture = useCallback((initialType: CaptureType = 'auto', initialText: string = '') => {
    setSelectedType(initialType);
    setInput(initialText);
    setIsOpen(true);
  }, []);

  const closeCapture = useCallback(() => {
    setIsOpen(false);
    setInput('');
    setSelectedType('auto');
  }, []);

  const submitCapture = useCallback(async () => {
    if (!input.trim() || !parsed) return false;

    setIsSubmitting(true);
    const targetType = parsed.detectedType;

    try {
      if (targetType === 'task') {
        await api.post('/api/v1/tasks', {
          title: parsed.title,
          description: input,
          priority: parsed.priority || 'medium',
          due_date: parsed.dueDate,
          tags: parsed.tags,
        });
        toast({
          title: 'Task saved',
          description: `"${parsed.title}" (Priority: ${parsed.priority || 'medium'})`,
        });
      } else if (targetType === 'person') {
        const contactName = parsed.personName || parsed.title;
        await api.post('/api/v1/people', {
          name: contactName,
          company: parsed.company,
          role: parsed.role,
          email: parsed.email,
          notes: input,
          tags: parsed.tags,
          relationship_type: 'contact',
        });
        toast({
          title: '✓ Connection Profile Registered',
          description: `${contactName} ${parsed.company ? `@ ${parsed.company}` : ''}`,
        });
      } else if (targetType === 'idea') {
        await api.post('/api/v1/ideas', {
          title: parsed.title,
          summary: input,
          tags: parsed.tags,
        });
        toast({
          title: 'Idea saved',
          description: `"${parsed.title}" added to your ideas`,
        });
      } else {
        // Memory / Reflection
        await api.post('/api/v1/memories', {
          title: parsed.title.slice(0, 80),
          content: input,
          category: 'reflection',
          tags: parsed.tags,
        });
        toast({
          title: 'Note saved',
          description: 'Your note is stored in your private Second Brain.',
        });
      }

      closeCapture();
      return true;
    } catch (err: any) {
      toast({
        title: 'Could not save',
        description: 'Your text is still here. Check your connection and try again.',
        variant: 'destructive',
      });
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [input, parsed, closeCapture, toast]);

  return {
    isOpen,
    input,
    setInput,
    selectedType,
    setSelectedType,
    parsed,
    isSubmitting,
    openCapture,
    closeCapture,
    submitCapture,
  };
}
