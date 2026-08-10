'use client';

import * as React from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface FilterBarProps {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  searchPlaceholder?: string;
  filters?: {
    label: string;
    options: { label: string; value: string }[];
    selectedValue: string;
    onChange: (val: string) => void;
  }[];
  onReset?: () => void;
}

export function FilterBar({
  searchQuery,
  onSearchChange,
  searchPlaceholder = 'Filter records by title or tag...',
  filters = [],
  onReset,
}: FilterBarProps) {
  const hasActiveFilters = searchQuery !== '' || filters.some(f => f.selectedValue !== '' && f.selectedValue !== 'all');

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-lg border border-border bg-[#0e0716] p-4 my-6 shadow-sm">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={searchPlaceholder}
          className="pl-9 h-10 font-sans text-sm bg-[#0a0510]"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center space-x-1 text-xs font-mono text-muted-foreground mr-2">
          <Filter className="h-3.5 w-3.5 text-[#00ff9d]" />
          <span>FILTERS:</span>
        </div>

        {filters.map((filter) => (
          <select
            key={filter.label}
            value={filter.selectedValue}
            onChange={(e) => filter.onChange(e.target.value)}
            className="h-9 rounded-md border border-border bg-[#0a0510] px-3 py-1 text-xs font-mono text-[#f7f4ea] focus:outline-none focus:ring-1 focus:ring-[#00ff9d] capitalize cursor-pointer"
          >
            <option value="all">All {filter.label}</option>
            {filter.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ))}

        {hasActiveFilters && onReset && (
          <Button
            onClick={onReset}
            variant="ghost"
            className="h-9 px-2 text-xs font-mono text-muted-foreground hover:text-red-400"
            title="Reset filters"
          >
            <X className="mr-1 h-3.5 w-3.5" />
            RESET
          </Button>
        )}
      </div>
    </div>
  );
}
